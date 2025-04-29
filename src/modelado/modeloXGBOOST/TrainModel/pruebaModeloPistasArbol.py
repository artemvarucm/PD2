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
df_train = pd.read_parquet('/data/Train/train_final.parquet')
df_test = pd.read_parquet('/data/Train/test_final.parquet')

print(df_train.columns)

# 2) Filtrado
#df = df[df['parado'] == True]
df_train = df_train[df_train['tiempo_espera'] <= 500]
df_test = df_test[df_test['tiempo_espera'] <= 500]

# 3) Hora cíclica
df_train['hora_decimal'] = df_train['timestamp'].dt.hour + df_train['timestamp'].dt.minute/60
df_train['hora_sin']     = np.sin(2*np.pi * df_train['hora_decimal']/24)
df_train['hora_cos']     = np.cos(2*np.pi * df_train['hora_decimal']/24)

df_test['hora_decimal'] = df_test['timestamp'].dt.hour + df_test['timestamp'].dt.minute/60
df_test['hora_sin']     = np.sin(2*np.pi * df_test['hora_decimal']/24)
df_test['hora_cos']     = np.cos(2*np.pi * df_test['hora_decimal']/24)

df_train_main, df_val = train_test_split(
    df_train,
    test_size=0.2,
    random_state=42
)

# 4) X e y
feature_cols = [
    'tiempo_esperado', 'llegada_lon', 'llegada_lat',
    'hora_sin', 'hora_cos',
    'runway_occupied', 'queue_length', 'time_since_free',
    'aircraft_type', 'holding_point', 'hold_pt_occupied'
]
X_train = df_train_main[feature_cols]
y_train = df_train_main['tiempo_espera']

X_val   = df_val[feature_cols]
y_val   = df_val['tiempo_espera']

X_test = df_test[feature_cols]
y_test = df_test['tiempo_espera']

# 5) Preprocesado
numeric_feats     = ['tiempo_esperado','llegada_lon','llegada_lat','hora_sin','hora_cos','runway_occupied','queue_length','time_since_free', 'hold_pt_occupied']
categorical_feats = ['aircraft_type','holding_point']
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric_feats),
    ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), categorical_feats)
])

X_train_proc = preprocessor.fit_transform(X_train)
X_val_proc   = preprocessor.transform(X_val)
X_test_proc  = preprocessor.transform(X_test)

# Get feature names after fitting
feature_names_out = preprocessor.get_feature_names_out()
X_test_proc_df = pd.DataFrame(X_test_proc, index=X_test.index, columns=feature_names_out)


# 6) Entrena con xgb.train
dtrain = xgb.DMatrix(X_train_proc, label=y_train)
dval   = xgb.DMatrix(X_val_proc,   label=y_val)
dtest  = xgb.DMatrix(X_test_proc,  label=y_test)
params = {
    'objective':   'reg:squarederror',
    'max_depth':   12,
    'eta':         0.05,
    'seed':        42,
    'eval_metric': 'mae'
}
bst = xgb.train(params, dtrain, num_boost_round=2500, evals=[(dtrain,'train'),(dval,'valid')], early_stopping_rounds=20, verbose_eval=True)

joblib.dump(preprocessor, 'preprocessor5.joblib')

y_pred = bst.predict(dtest)
mae = mean_absolute_error(y_test, y_pred)
print(f'Test MAE (XGB + queue): {mae:.2f} s')
bst.save_model('modelo_tiempo_espera_xgb_with_queue5.model')

# 7) Crear DataFrame final para el test set
df_test_original = df_test.loc[X_test.index].copy()
df_final_test = pd.DataFrame(index=X_test.index)

# Columnas originales necesarias
original_cols_to_keep = ['ICAO', 'llegada_punto', 'salida_punto', 'despegue', 'aircraft_type',
                         'llegada_lon', 'llegada_lat', 'salida_lon', 'salida_lat',
                         'holding_point', 'parado', 'fecha_despegue', 'hora_despegue']
for col in original_cols_to_keep:
    df_final_test[col] = df_test_original[col]

# Target real, predicción y tiempo_esperando
df_final_test['tiempo_espera'] = y_test
df_final_test['pred'] = y_pred
df_final_test['tiempo_esperado'] = df_test_original['tiempo_esperado']

# Columnas One-Hot Encoded (quitando prefijo 'cat__')
ohe_cols = [col for col in feature_names_out if col.startswith('cat__')]
rename_dict = {col: col.replace('cat__', '') for col in ohe_cols}
df_final_test = df_final_test.join(X_test_proc_df[ohe_cols].rename(columns=rename_dict))

# Añadir índice como columna y reordenar según CSV de ejemplo
df_final_test.reset_index(inplace=True)

target_cols = ['index', 'ICAO', 'llegada_punto', 'salida_punto', 'despegue', 'tiempo_espera', 'aircraft_type', 'llegada_lon', 'llegada_lat', 'salida_lon', 'salida_lat', 'holding_point', 'parado', 'fecha_despegue', 'hora_despegue', 'aircraft_type_Heavy (larger than 136000 kg)', 'aircraft_type_High vortex aircraft', 'aircraft_type_Light (less than 7000 kg)', 'aircraft_type_Medium 1 (between 7000 kg and 34000 kg)', 'aircraft_type_Medium 2 (between 34000 kg to 136000 kg)', 'holding_point_K1', 'holding_point_K2', 'holding_point_K3', 'holding_point_KA6', 'holding_point_KA8', 'holding_point_L1', 'holding_point_LA', 'holding_point_LB', 'holding_point_LC', 'holding_point_LD', 'holding_point_LE', 'holding_point_LF', 'holding_point_Y1', 'holding_point_Y2', 'holding_point_Y3', 'holding_point_Z1', 'holding_point_Z2', 'holding_point_Z3', 'holding_point_Z4', 'holding_point_Z6', 'tiempo_esperando', 'pred']

# Asegurar que todas las columnas existan (rellenar con 0/False si faltan OHE)
for col in target_cols:
    if col not in df_final_test.columns:
        # Podría pasar si alguna categoría OHE no está en el test set
        df_final_test[col] = 0 # O False, dependiendo del tipo esperado

df_final_test = df_final_test[target_cols]

print("\nDataFrame final para test:")
print(df_final_test.head())
print(df_final_test.info())


df_final_test.to_csv('../../../src/evaluacion/predicciones_xgb_with_queue_entero.csv', index=False)

# Visualización (código existente)
import matplotlib.pyplot as plt
y_train_pred = bst.predict(dtrain)
y_valid_pred = bst.predict(dtest)

# 2) Scatter "real vs. predicho" en la misma gráfica
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
