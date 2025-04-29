#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
predict_tiempo_espera.py

Carga un CSV de features, aplica el preprocesador y el modelo XGBoost
entrenado, y guarda/imprime la predicción.
"""
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pandas as pd
import xgboost as xgb
import joblib
import numpy as np

# 1) Parámetros
FEATURES_CSV      = ("/Users/alewar/Documents/Universidad/Tercero/PD2/PD2/data/Train/test_final_no_parados.parquet")
PREPROCESSOR_PKL  = "preprocessor5.joblib"
MODEL_FILE        = "modelo_tiempo_espera_xgb_with_queue5.model"
OUTPUT_CSV = 'predicciones_xgb.csv'

df_feat = pd.read_parquet(FEATURES_CSV)

df_feat = df_feat[df_feat['tiempo_espera'] <= 500]

y_true = df_feat['tiempo_espera'].values

df_feat['hora_decimal'] = df_feat['timestamp'].dt.hour + df_feat['timestamp'].dt.minute/60
df_feat['hora_sin']     = np.sin(2*np.pi * df_feat['hora_decimal']/24)
df_feat['hora_cos']     = np.cos(2*np.pi * df_feat['hora_decimal']/24)

preprocessor = joblib.load(PREPROCESSOR_PKL)
scaler  = preprocessor.named_transformers_['num']
ohe     = preprocessor.named_transformers_['cat']

numeric_feats     = scaler.feature_names_in_
categorical_feats = ohe.feature_names_in_

# 1) Transformación numérica
X_num = scaler.transform(df_feat[numeric_feats])

# 2) Codificación manual de categorías
cat_arrays = []
for feat, cats in zip(categorical_feats, ohe.categories_):
    vals = df_feat[feat].fillna('').astype(str).values
    # crea un array (n_samples, n_cats) con 1 donde coincida, 0 el resto
    arr = (vals[:, None] == np.array(cats)[None, :]).astype(int)
    cat_arrays.append(arr)

X_cat = np.hstack(cat_arrays)

# 3) Combinar y predecir
X_proc = np.hstack([X_num, X_cat])
bst    = xgb.Booster()
bst.load_model(MODEL_FILE)

dtest = xgb.DMatrix(X_proc)
y_pred = bst.predict(dtest)

# 1) Asume que ya has cargado y_true, y_pred es tu array de predicciones
mae   = mean_absolute_error(y_true, y_pred)
r2    = r2_score(y_true, y_pred)

print(f"MAE  : {mae:.3f}")
print(f"R²   : {r2:.3f}")

import matplotlib.pyplot as plt

plt.figure(figsize=(6,6))
plt.scatter(y_true, y_pred, alpha=0.3)
plt.plot([y_true.min(), y_true.max()],
         [y_true.min(), y_true.max()],
         'k--', lw=2)
plt.xlabel("Real")
plt.ylabel("Predicho")
plt.title("Predicciones vs Valores Reales")
plt.show()


df_feat['predicted_tiempo_espera'] = y_pred
print(df_feat[['predicted_tiempo_espera']])
