#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
predict_tiempo_espera_with_pipeline_manual.py

Carga un CSV con las features ya calculadas, extrae el preprocesador y el modelo
XGBRegressor de un pipeline joblib, realiza manualmente la transformación
y predice el tiempo de espera.
"""
import sys
import pandas as pd
import numpy as np
import joblib
from numpy import expm1

# ----------------------------
# 1) Ajusta rutas según tu entorno
# ----------------------------
FEATURES_CSV    = "../outputs/features_ICAO_34324e.csv"       # CSV con features precomputadas
PIPELINE_JOBLIB = "../TrainModel/pipeline_xgb.joblib"          # pipeline joblib (preprocessor + XGBRegressor)
OUTPUT_CSV      = "predictions_manual.csv"                # CSV de salida con predicción
# ----------------------------

# 2) Carga de features
try:
    df = pd.read_csv(FEATURES_CSV)
except Exception as e:
    print(f"ERROR: No se pudo leer {FEATURES_CSV}: {e}", file=sys.stderr)
    sys.exit(1)

# 3) Cargar pipeline y extraer preprocesador + modelo
try:
    pipeline = joblib.load(PIPELINE_JOBLIB)
    preprocessor = pipeline.named_steps['pre']
    model        = pipeline.named_steps['xgb']
except Exception as e:
    print(f"ERROR: No se pudo cargar pipeline {PIPELINE_JOBLIB}: {e}", file=sys.stderr)
    sys.exit(1)

# 4) Extraer scaler y OHE del preprocesador
scaler = preprocessor.named_transformers_['num']
ohe    = preprocessor.named_transformers_['cat']
numeric_feats     = list(scaler.feature_names_in_)
categorical_feats = ohe.feature_names_in_

# 5) Transformación numérica
try:
    X_num = scaler.transform(df[numeric_feats])
except Exception as e:
    print(f"ERROR en escalado numérico: {e}", file=sys.stderr)
    sys.exit(1)

# 6) Codificación manual de categorías
cat_arrays = []
for feat, cats in zip(categorical_feats, ohe.categories_):
    vals = df[feat].fillna('').astype(str).values
    arr  = (vals[:, None] == np.array(cats)[None, :]).astype(int)
    cat_arrays.append(arr)
X_cat = np.hstack(cat_arrays) if cat_arrays else np.empty((len(df), 0))

# 7) Combinar num + cat
X_proc = np.hstack([X_num, X_cat])

# 8) Predicción (el modelo devuelve log1p(y))
y_log_pred = model.predict(X_proc)
y_pred     = expm1(y_log_pred)

# 9) Anexar predicción e imprimir
df['predicted_tiempo_espera'] = y_pred
print(df[['predicted_tiempo_espera']])

# 10) Guardar a CSV
try:
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Predicciones guardadas en '{OUTPUT_CSV}'")
except Exception as e:
    print(f"WARNING: No se pudo guardar {OUTPUT_CSV}: {e}", file=sys.stderr)
