from pathlib import Path
import pandas as pd
import joblib
from scenarioTransformer import get_preprocessed_scenario
import numpy as np

# Ruta al escenario
scenariosPath = '../../../data/final_scenarios/'
df_casos = pd.read_csv(Path(scenariosPath, 'answers_empty.csv'))

# Cargar meteorología y procesar como en train
df_meteo = pd.read_csv("../../../data/datos_meteorologicos.csv", delimiter=",")
df_meteo["Fecha"] = pd.to_datetime(df_meteo["Fecha"]).dt.date
df_meteo["Hora"] = pd.to_datetime(df_meteo["Hora"], format="%H:%M").dt.hour
cols_numericas = ["Precipitación", "Temperatura", "Humedad", "Viento", "Viento máximo", "Temperatura mínima", "Temperatura máxima"]
for col in cols_numericas:
    df_meteo[col] = df_meteo[col].str.replace(",", ".").astype(float)

# Cargar modelo sklearn (pipeline)
modelo = joblib.load("../sklearn/modelo_sklearn.pkl")
expected_cols = set(modelo.feature_names_in_)

for idx, row in df_casos.iterrows():
    processed = get_preprocessed_scenario(Path(scenariosPath, row['scenario_name']), row)

    if processed is None:
        df_casos.loc[idx, 'time_to_takeoff_s'] = -1
    else:
        try:
            # Añadir variables temporales
            processed["Fecha"] = processed["timestamp"].dt.date
            processed["Hora"] = processed["timestamp"].dt.hour

            # Merge con meteorología
            processed = processed.merge(df_meteo, how="left", on=["Fecha", "Hora"])

            # Validar columnas requeridas por el modelo
            cols_present = set(processed.columns)
            missing = expected_cols - cols_present
            if missing:
                print(f"Error en predicción del escenario {row['scenario_name']}: faltan columnas {missing}")
                df_casos.loc[idx, 'time_to_takeoff_s'] = -1
                continue

            # Predecir
            pred = modelo.predict(processed[list(modelo.feature_names_in_)])[0]
            df_casos.loc[idx, 'time_to_takeoff_s'] = pred

        except Exception as e:
            print(f"Error en predicción del escenario {row['scenario_name']}: {e}")
            df_casos.loc[idx, 'time_to_takeoff_s'] = -1

# Guardar resultado
df_casos.to_csv('resultados_sklearn.csv', index=False)
print("Archivo generado: resultados_sklearn.csv")
