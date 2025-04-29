# modelo_xgb_mejorado_corregido.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold, RandomizedSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
import joblib

# 1) Carga y filtrado
df_train = pd.read_parquet(
    '/data/Train/train_final.parquet'
)
df_test = pd.read_parquet('/data/Train/test_final.parquet')


df_train = df_train[df_train['tiempo_espera'] <= 500]
df_test = df_test[df_test['tiempo_espera'] <= 500]

# 2) Ingeniería de features
# Hora cíclica
df_train['hora_decimal'] = df_train['timestamp'].dt.hour + df_train['timestamp'].dt.minute / 60
df_train['hora_sin']     = np.sin(2 * np.pi * df_train['hora_decimal'] / 24)
df_train['hora_cos']     = np.cos(2 * np.pi * df_train['hora_decimal'] / 24)


df_test['hora_decimal'] = df_test['timestamp'].dt.hour + df_test['timestamp'].dt.minute/60
df_test['hora_sin']     = np.sin(2*np.pi * df_test['hora_decimal']/24)
df_test['hora_cos']     = np.cos(2*np.pi * df_test['hora_decimal']/24)

# Día de la semana y fin de semana
df_train['weekday'] = df_train['timestamp'].dt.weekday
df_train['is_weekend'] = df_train['weekday'].isin([5, 6]).astype(int)
# Interacción simple
df_train['queue_x_runway'] = df_train['queue_length'] * df_train['runway_occupied']

# Día de la semana y fin de semana
df_test['weekday'] = df_test['timestamp'].dt.weekday
df_test['is_weekend'] = df_test['weekday'].isin([5, 6]).astype(int)
# Interacción simple
df_test['queue_x_runway'] = df_test['queue_length'] * df_test['runway_occupied']

# 3) Definición de X e y (log-transform del target)
feature_cols = [
    'tiempo_esperado', 'llegada_lon', 'llegada_lat',
    'hora_sin', 'hora_cos', 'weekday', 'is_weekend', 'queue_x_runway',
    'runway_occupied', 'queue_length', 'time_since_free',
    'aircraft_type', 'holding_point', 'parado', 'hold_pt_occupied'
]
# renombramos
X_train = df_train[feature_cols]
y_train = df_train['tiempo_espera']
y_train_log = np.log1p(y_train)

# definimos X_test / y_test_log
X_test = df_test[feature_cols]
y_test = df_test['tiempo_espera']
y_test_log = np.log1p(y_test)

# 5) Preprocesado
dnumeric = [c for c in feature_cols if c not in ['aircraft_type', 'holding_point']]
dcat     = ['aircraft_type', 'holding_point']
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), dnumeric),
    ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), dcat)
])

# 6) Pipeline base
pipeline = Pipeline([
    ('pre', preprocessor),
    ('xgb', XGBRegressor(
        objective='reg:squarederror',
        random_state=42,
        verbosity=0
    ))
])

# 7) Validación cruzada inicial sobre TRAIN
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(
    pipeline, X_train, y_train_log, cv=kf, scoring='neg_mean_absolute_error'
)
print(f"MAE CV 5-fold (log-target): {np.mean(-cv_scores):.4f} ± {np.std(-cv_scores):.4f}")

# 8) Búsqueda de hiperparámetros (Randomized Search)
param_dist = {
    'xgb__max_depth': [6, 8, 10, 12],
    'xgb__learning_rate': [0.01, 0.03, 0.05, 0.1],
    'xgb__subsample': [0.6, 0.8, 1.0],
    'xgb__colsample_bytree': [0.6, 0.8, 1.0],
    'xgb__gamma': [0, 1, 5],
    'xgb__reg_alpha': [0, 0.1, 1],
    'xgb__reg_lambda': [1, 5, 10],
    'xgb__n_estimators': [500, 1000, 1500, 2000]
}
search = RandomizedSearchCV(
    pipeline, param_dist, n_iter=30, cv=3,
    scoring='neg_mean_absolute_error',
    random_state=42, n_jobs=-1, verbose=1,
    error_score='raise'
)
# Ejecuta búsqueda y guarda resultados detallados
search.fit(X_train, y_train_log)
df_results = pd.DataFrame(search.cv_results_)
df_results.to_csv('random_search_results_final.csv', index=False)
print("Resultados de RandomizedSearch guardados en 'random_search_results.csv'")

print("Mejores parámetros:", search.best_params_)
print(f"Mejor MAE (log-target) en CV: {-search.best_score_:.4f}")

# 9) Entrenamiento final sin early stopping
# Usamos el número óptimo de estimators ya buscado
best_params = {k.replace('xgb__', ''): v for k, v in search.best_params_.items()}
final_pipeline = Pipeline([
    ('pre', preprocessor),
    ('xgb', XGBRegressor(
        objective='reg:squarederror',
        random_state=42,
        verbosity=0,
        **best_params
    ))
])
final_pipeline.fit(X_train, y_train_log)

y_pred_log = final_pipeline.predict(X_test)
y_pred     = np.expm1(y_pred_log)

# 1) Preparamos el DataFrame de test original
df_test_original = df_test.copy()  # como X_test usa el mismo índice que df_test

# 2) Obtenemos la matriz preprocesada y los nombres de columna
pre = final_pipeline.named_steps['pre']
X_test_proc = pre.transform(X_test)
feature_names = pre.get_feature_names_out()  # escalar__col1, cat__tipo_A, etc.
X_test_proc_df = pd.DataFrame(X_test_proc, index=X_test.index, columns=feature_names)

# 3) Creamos el df_final_test e incorporamos las columnas originales
df_final_test = pd.DataFrame(index=X_test.index)
original_cols_to_keep = [
    'ICAO', 'llegada_punto', 'salida_punto', 'despegue', 'aircraft_type',
    'llegada_lon', 'llegada_lat', 'salida_lon', 'salida_lat',
    'holding_point', 'parado', 'fecha_despegue', 'hora_despegue'
]
for col in original_cols_to_keep:
    df_final_test[col] = df_test_original[col]

# 4) Añadimos target real, predicción y tiempo_esperado
df_final_test['tiempo_espera']    = y_test
df_final_test['pred']             = y_pred
df_final_test['tiempo_esperado']  = df_test_original['tiempo_esperado']

# 5) Extraemos sólo las columnas One-Hot (prefijo 'cat__') y renombramos
ohe_cols = [c for c in feature_names if c.startswith('holding_point_') or c.startswith('aircraft_type_')]
df_final_test = df_final_test.join(
    X_test_proc_df[ohe_cols]
)

# 6) Aseguramos que existan todas las categorías (rellenamos con 0 si faltan)
target_cols = original_cols_to_keep + [
    'tiempo_espera', 'pred', 'tiempo_esperado'
] + ohe_cols

for col in target_cols:
    if col not in df_final_test.columns:
        df_final_test[col] = 0

# 7) Reordenamos y volcamos a CSV
df_final_test = df_final_test[target_cols]
df_final_test.reset_index(drop=True, inplace=True)

df_final_test.to_csv(
    '../../../src/evaluacion/predicciones_xgb_with_queue_final.csv',
    index=False
)
print("Predicciones de test guardadas en 'predicciones_xgb_with_queue_gridSearch.csv'")

# 10) Evaluación sobre TEST
y_true = np.expm1(y_test_log)
mae = mean_absolute_error(y_true, y_pred)
print(f"Test MAE (XGB mejorado): {mae:.4f} s")


# 11) Importancia de variables

# 11.1) Recuperar nombres reales de las features tras el preprocesado
pre = final_pipeline.named_steps['pre']
# Obtiene algo como ['num__tiempo_esperado', 'num__llegada_lon', ..., 'cat__aircraft_type_Heavy', ...]
raw_feature_names = pre.get_feature_names_out()
# Limpia el prefijo para que quede sólo el nombre original
feature_names = [f.replace('num__','')
                   .replace('cat__','')
                   for f in raw_feature_names]

# 11.2) Extraer el booster entrenado
bst = final_pipeline.named_steps['xgb'].get_booster()

# 11.3) Obtener el diccionario de importancias (por “weight”)
imp_dict = bst.get_score(importance_type='weight')
# imp_dict tiene claves 'f0', 'f1', …; las mapeamos a nombres reales
imp_mapped = { feature_names[int(k[1:])] : v
               for k,v in imp_dict.items() }

# 11.4) Ordenar de mayor a menor e imprimir por consola
imp_sorted = sorted(imp_mapped.items(), key=lambda x: x[1], reverse=True)
print("\nFeature importance (weight):")
for feat, score in imp_sorted:
    print(f"\t{feat}: {score}")

# 11.5) (Opcional) Gráfico de barras horizontal
import matplotlib.pyplot as plt

names, scores = zip(*imp_sorted)
plt.figure(figsize=(8,10))
plt.barh(names, scores)
plt.gca().invert_yaxis()               # invertir para que la más importante quede arriba
plt.xlabel('Weight')
plt.title('Importancia de variables (XGB)')
plt.tight_layout()
plt.show()

# 12) Guardar pipeline completo (el mejor modelo)
joblib.dump(final_pipeline, 'pipeline_xgb.joblib')
print("Pipeline final (mejor modelo) guardado en 'pipeline_xgb_mejorado_final.joblib'")