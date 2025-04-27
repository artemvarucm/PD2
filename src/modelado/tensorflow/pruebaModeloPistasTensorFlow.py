# modelo_tensorflow.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import joblib
import matplotlib.pyplot as plt

# 1) Carga
df = pd.read_parquet('../../../data/Train/datos_holding_with_runway_and_queue_nuevo_no_parados.parquet')


df = df.dropna().reset_index(drop=True)
print(df.columns)

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

# Get feature names after fitting
feature_names_out = preprocessor.get_feature_names_out()
X_test_proc_df = pd.DataFrame(X_test_proc, index=X_test.index, columns=feature_names_out)

# 6) Entrenar con TensorFlow
# Early stopping
early_stopping = tf.keras.callbacks.EarlyStopping(
    monitor='val_loss',
    patience=20,
    restore_best_weights=True
)

lr_schedule = tf.keras.callbacks.ReduceLROnPlateau(
    monitor='val_loss', factor=0.5, patience=5, min_lr=0.0001
)

# Construcción del modelo
model = keras.Sequential([
    layers.Dense(256, activation='relu', input_shape=(X_train_proc.shape[1],)),
    layers.BatchNormalization(),
    layers.Dense(128, activation='relu'),
    layers.BatchNormalization(),
    layers.Dense(64, activation='relu'),
    layers.BatchNormalization(),
    layers.Dense(32, activation='relu'),
    layers.BatchNormalization(),
    layers.Dense(16, activation='relu'),
    layers.BatchNormalization(),
    layers.Dense(1)
])

# Compilación
optimizer = tf.keras.optimizers.Adam(learning_rate=0.0002) 
model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])

# Entrenamiento con early stopping
history = model.fit(
    X_train_proc, 
    y_train, 
    epochs=1500,
    batch_size=128,
    validation_data=(X_test_proc, y_test),
    callbacks=[early_stopping, lr_schedule],
    verbose=1
)

# Guardar el modelo y preprocessor
joblib.dump(preprocessor, 'preprocessor_tensorflow.joblib')
model.save('modelo_tiempo_espera_tensorflow_with_queue.keras')

# Evaluacións
y_pred = model.predict(X_test_proc).flatten()
mae = mean_absolute_error(y_test, y_pred)
print(f'Test MAE (TensorFlow + queue): {mae:.2f} s')

# 7) Crear DataFrame final para el test set
df_test_original = df.loc[X_test.index].copy()
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
df_final_test['tiempo_esperado'] = df_test_original['time_since_free']

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

df_final_test.to_csv('../../../src/evaluacion/predicciones_tensorflow_with_queue.csv', index=False)

# Visualización
plt.figure(figsize=(8,8))
# línea perfecta
min_val = min(y_train.min(), y_test.min())
max_val = max(y_train.max(), y_test.max())
plt.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=1)

# puntos de train
y_train_pred = model.predict(X_train_proc).flatten()
plt.scatter(y_train, y_train_pred,
            alpha=0.3, s=10, label='Train')
# puntos de validación
plt.scatter(y_test, y_pred,
            alpha=0.3, s=10, label='Validación')

plt.xlabel('Tiempo de espera real (s)')
plt.ylabel('Tiempo de espera predicho (s)')
plt.title('Predicciones vs. valores reales (TensorFlow)')
plt.legend()
plt.axis('equal')      # para que ejes tengan misma escala
plt.tight_layout()
plt.show()

# Gráfica de pérdida durante el entrenamiento
plt.figure(figsize=(10, 6))
plt.plot(history.history['loss'], label='Entrenamiento')
plt.plot(history.history['val_loss'], label='Validación')
plt.xlabel('Epoch')
plt.ylabel('Pérdida (MSE)')
plt.title('Evolución de la pérdida durante el entrenamiento')
plt.legend()
plt.grid(True)
plt.show()

# Gráfica de MAE durante el entrenamiento
plt.figure(figsize=(10, 6))
plt.plot(history.history['mae'], label='Entrenamiento')
plt.plot(history.history['val_mae'], label='Validación')
plt.xlabel('Epoch')
plt.ylabel('MAE')
plt.title('Evolución del MAE durante el entrenamiento')
plt.legend()
plt.grid(True)
plt.show() 