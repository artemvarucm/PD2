#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
predict_tiempo_espera.py

Carga un CSV de features, aplica el preprocesador y el modelo XGBoost
entrenado, y guarda/imprime la predicción.
"""

import pandas as pd
import xgboost as xgb
import joblib
import numpy as np

# 1) Parámetros
FEATURES_CSV      = "outputs/features_ICAO_34324e.csv"               # ajusta si cambias nombre
PREPROCESSOR_PKL  = "preprocessor.joblib"
MODEL_FILE        = "modelo_tiempo_espera_xgb_with_queue.model"

df_feat = pd.read_csv(FEATURES_CSV)
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

df_feat['predicted_tiempo_espera'] = y_pred
print(df_feat[['predicted_tiempo_espera']])

