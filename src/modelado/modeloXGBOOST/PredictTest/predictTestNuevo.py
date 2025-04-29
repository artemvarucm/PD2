#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
predict_tiempo_espera_pipeline.py

Carga un Parquet de test, aplica el pipeline (preprocessor + XGB)
entrenado, y evalúa MAE y R². También grafica real vs predicho.
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt

# 1) Parámetros de entrada
TEST_PARQUET      = "/Users/alewar/Documents/Universidad/Tercero/PD2/PD2/data/Train/test_final_no_parados.parquet"
PIPELINE_FILE     = "pipeline_xgb_mejorado.joblib"

# 2) Carga del pipeline
pipeline = joblib.load(PIPELINE_FILE)

# 3) Carga y filtrado de datos
df = pd.read_parquet(TEST_PARQUET)
df = df[df['tiempo_espera'] <= 1200]


# 4) Ingeniería de features (idéntica a la del entrenamiento)
df['hora_decimal']    = df['timestamp'].dt.hour + df['timestamp'].dt.minute/60
df['hora_sin']        = np.sin(2*np.pi * df['hora_decimal']/24)
df['hora_cos']        = np.cos(2*np.pi * df['hora_decimal']/24)
df['weekday']         = df['timestamp'].dt.weekday
df['is_weekend']      = df['weekday'].isin([5,6]).astype(int)
df['queue_x_runway']  = df['queue_length'] * df['runway_occupied']

feature_cols = [
    'tiempo_esperado','llegada_lon','llegada_lat',
    'hora_sin','hora_cos','weekday','is_weekend','queue_x_runway',
    'runway_occupied','queue_length','time_since_free',
    'aircraft_type','holding_point'
]

# 5) Entradas y etiquetas reales
X_test  = df[feature_cols]
y_true  = df['tiempo_espera'].values

# 6) Predicción (pipeline ya incluye log-transform)
y_pred_log = pipeline.predict(X_test)
y_pred     = np.expm1(y_pred_log)  # inversa de log1p

# 7) Métricas
mae = mean_absolute_error(y_true, y_pred)
r2  = r2_score(y_true, y_pred)
print(f"MAE : {mae:.3f} s")
print(f"R²  : {r2:.3f}")

# 8) Gráfica Real vs Predicho
plt.figure(figsize=(6,6))
plt.scatter(y_true, y_pred, alpha=0.3)
m = max(y_true.max(), y_pred.max())
plt.plot([0, m],[0, m],'k--',lw=1)
plt.xlabel("Tiempo espera real (s)")
plt.ylabel("Tiempo espera predicho (s)")
plt.title("Real vs. Predicho")
plt.axis('equal')
plt.tight_layout()
plt.show()

# 9) Guardar predicciones en el DataFrame
df['predicted_tiempo_espera'] = y_pred
print(df[['predicted_tiempo_espera']].head())
