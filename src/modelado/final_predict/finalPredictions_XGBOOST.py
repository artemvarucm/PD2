import sys

import joblib
import pandas as pd
from pathlib import Path
from scenarioTransformer import get_preprocessed_scenario
import numpy as np
from numpy import expm1


PIPELINE_JOBLIB = "../modeloXGBOOST/TrainModel/pipeline_xgb.joblib"
OUTPUT_CSV      = "predictions_manual.csv"
scenariosPath = '/Users/alewar/Documents/Universidad/Tercero/PD2/PD2/data/final_scenarios'
df_casos = pd.read_csv(Path(scenariosPath, 'answers_empty.csv'))


for idx, row in df_casos.iterrows():
    processed = get_preprocessed_scenario(Path(scenariosPath, row['scenario_name']), row)

    if processed is None:
        df_casos.loc[idx, 'time_to_takeoff_s'] = -1
    else:

        # Hora cíclica
        processed['hora_decimal'] = processed['timestamp'].dt.hour + processed['timestamp'].dt.minute / 60
        processed['hora_sin'] = np.sin(2 * np.pi * processed['hora_decimal'] / 24)
        processed['hora_cos'] = np.cos(2 * np.pi * processed['hora_decimal'] / 24)

        # Día de la semana y fin de semana
        processed['weekday'] = processed['timestamp'].dt.weekday
        processed['is_weekend'] = processed['weekday'].isin([5, 6]).astype(int)
        # Interacción simple
        processed['queue_x_runway'] = processed['queue_length'] * processed['runway_occupied']

        # 3) Cargar pipeline y extraer preprocesador + modelo
        try:
            pipeline = joblib.load(PIPELINE_JOBLIB)
            preprocessor = pipeline.named_steps['pre']
            model = pipeline.named_steps['xgb']
        except Exception as e:
            print(f"ERROR: No se pudo cargar pipeline {PIPELINE_JOBLIB}: {e}", file=sys.stderr)
            sys.exit(1)

        # 4) Extraer scaler y OHE del preprocesador
        scaler = preprocessor.named_transformers_['num']
        ohe = preprocessor.named_transformers_['cat']
        numeric_feats = list(scaler.feature_names_in_)
        categorical_feats = ohe.feature_names_in_

        # 5) Transformación numérica
        try:
            X_num = scaler.transform(processed[numeric_feats])
        except Exception as e:
            print(f"ERROR en escalado numérico: {e}", file=sys.stderr)
            sys.exit(1)

        # 6) Codificación manual de categorías
        cat_arrays = []
        for feat, cats in zip(categorical_feats, ohe.categories_):
            vals = processed[feat].fillna('').astype(str).values
            arr = (vals[:, None] == np.array(cats)[None, :]).astype(int)
            cat_arrays.append(arr)
        X_cat = np.hstack(cat_arrays) if cat_arrays else np.empty((len(processed), 0))

        # 7) Combinar num + cat
        X_proc = np.hstack([X_num, X_cat])

        # 8) Predicción (el modelo devuelve log1p(y))
        y_log_pred = model.predict(X_proc)
        y_pred = expm1(y_log_pred)

        # 9) Anexar predicción e imprimir
        processed['predicted_tiempo_espera'] = y_pred
        print(processed[['predicted_tiempo_espera']])

        # 10) Guardar a CSV
        try:
            processed.to_csv(OUTPUT_CSV, index=False)
            print(f"Predicciones guardadas en '{OUTPUT_CSV}'")
        except Exception as e:
            print(f"WARNING: No se pudo guardar {OUTPUT_CSV}: {e}", file=sys.stderr)

        df_casos.loc[idx, 'time_to_takeoff_s'] = y_pred[0]

df_casos.to_csv('resultados_sin_nombre.csv', index=False)