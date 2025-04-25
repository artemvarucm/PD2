# modelo_xgb.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import xgboost as xgb
from sklearn.metrics import mean_absolute_error
import joblib

# 1) Carga
df = pd.read_parquet('../../../data/Train/datos_holding_with_runway_and_queue_nuevo_no_parados.parquet')

# 2) Filtrado
#df = df[df['parado'] == True]
df = df[df['tiempo_espera'] <= 500]

# 3) Hora cíclica
df['hora_decimal'] = df['timestamp'].dt.hour + df['timestamp'].dt.minute/60
df['hora_sin']     = np.sin(2*np.pi * df['hora_decimal']/24)
df['hora_cos']     = np.cos(2*np.pi * df['hora_decimal']/24)

# 4) X e y
feature_cols = [
    'tiempo_esperado', 'llegada_lon', 'llegada_lat',
    'hora_sin', 'hora_cos',
    'runway_occupied', 'queue_length', 'time_since_free',
    'aircraft_type', 'holding_point'
]
X = df[feature_cols]
y = df['tiempo_espera']

# 5) Preprocesado
numeric_feats     = ['tiempo_esperado','llegada_lon','llegada_lat','hora_sin','hora_cos','runway_occupied','queue_length','time_since_free']
categorical_feats = ['aircraft_type','holding_point']
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric_feats),
    ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), categorical_feats)
])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train_proc = preprocessor.fit_transform(X_train)
X_test_proc  = preprocessor.transform(X_test)

# 6) Entrena con xgb.train
dtrain = xgb.DMatrix(X_train_proc, label=y_train)
dvalid = xgb.DMatrix(X_test_proc,  label=y_test)
params = {
    'objective':   'reg:squarederror',
    'max_depth':   12,
    'eta':         0.05,
    'seed':        42,
    'eval_metric': 'mae'
}
bst = xgb.train(params, dtrain, num_boost_round=3500, evals=[(dtrain,'train'),(dvalid,'valid')], early_stopping_rounds=20, verbose_eval=True)

joblib.dump(preprocessor, 'preprocessor.joblib')

y_pred = bst.predict(dvalid)
mae = mean_absolute_error(y_test, y_pred)
print(f'Test MAE (XGB + queue): {mae:.2f} s')
bst.save_model('modelo_tiempo_espera_xgb_with_queue.model')

import matplotlib.pyplot as plt
y_train_pred = bst.predict(dtrain)
y_valid_pred = bst.predict(dvalid)

# 2) Scatter “real vs. predicho” en la misma gráfica
plt.figure(figsize=(8,8))
# línea perfecta
min_val = min(y_train.min(), y_test.min())
max_val = max(y_train.max(), y_test.max())
plt.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=1)

# puntos de train
plt.scatter(y_train, y_train_pred,
            alpha=0.3, s=10, label='Train')
# puntos de validación
plt.scatter(y_test, y_valid_pred,
            alpha=0.3, s=10, label='Validación')

plt.xlabel('Tiempo de espera real (s)')
plt.ylabel('Tiempo de espera predicho (s)')
plt.title('Predicciones vs. valores reales')
plt.legend()
plt.axis('equal')      # para que ejes tengan misma escala
plt.tight_layout()
plt.show()
