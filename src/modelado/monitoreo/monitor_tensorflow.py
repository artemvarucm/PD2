import wandb
from monitor_general import MonitorGeneral
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from wandb.integration.keras import WandbMetricsLogger
from wandb.integration.keras import WandbModelCheckpoint
import numpy as np
from wandb.plot.custom_chart import plot_table

class MonitorTensorflow(MonitorGeneral):
    def __init__(self, modelo, train, test, y, num_epochs, project='tf_PD2', name="modelo_tf", entity='dacoleto-complutense-university-of-madrid'):
        """
        Inicializa el monitor para el modelo de machine learning.
        :param modelo: Modelo de machine learning a monitorizar
        :param train: DataFrame de entrenamiento
        :param test: DataFrame de test
        :param y: Variable objetivo
        :param num_epochs: Número de épocas para el entrenamiento
        :param project: Nombre del proyecto en W&B
        :param name: Nombre del experimento
        :param entity: Nombre de la entidad en W&B
        """
        self.num_epochs = num_epochs
        super().__init__(modelo=modelo, train=train, test=test, y=y, project=project, name=name, entity=entity)
    
    def visualizeMetrics(self, resultados_metricas, metricas, train=False, groupby=None, name="metricas"):
        """
        Visualiza las métricas en W&B.
        :param resultados_metricas: Resultados de las métricas
        :param metricas: Métricas a visualizar  
        :param train: True si la tabla es para metricas de entrenamiento, False si es para métricas de test
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        """                  
        tabla_metricas = self.buildTableMetrics(resultados_metricas, metricas=metricas, train=train, groupby=groupby, name=name)
        
        if groupby is not None: 
            self.buildGraph(tabla_metricas=tabla_metricas, groupby=groupby, metricas=metricas, name=name)

    def buildGraph(self, tabla_metricas, groupby, metricas, name="metricas"):
        """
        Construye un grafico para cada métricay lo registra en W&B.
        :param tabla_metricas: Tabla de métricas
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param metricas: Métricas a visualizar
        :param name: Nombre de la visualización de métricas
        """
        for metrica in metricas:
            wandb.log({
                f"{name}_{metrica}": wandb.plot.bar(
                    tabla_metricas, groupby, metrica, title=metrica
                )
            })
    
    def buildTableMetrics(self, resultados_metricas, metricas, train=False, groupby=None, name="metricas"):
        """
        Construye una tabla de métricas para registrar en W&B.
        :param resultados_metricas: Resultados de las métricas
        :param metricas: Métricas a visualizar
        :param train: True si la tabla es para metricas de entrenamiento, False si es para métricas de test
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        :return: Tabla de métricas
        """
        if train:
            name = f"{name}_entrenamiento"
            columns = ["epoch"] + metricas
            tabla_metricas = wandb.Table(columns=columns)
            for epoch in range(self.num_epochs):
                    fila = [epoch] + [resultados_metricas[metrica][epoch] for metrica in metricas]
                    tabla_metricas.add_data(*fila)
        else:
            name = f"{name}_test" if groupby is None else f"{name}_test_{groupby}"
            columns =  [groupby] + metricas if groupby is not None else metricas  
            tabla_metricas = wandb.Table(columns=columns)       
            
            if groupby is not None:
                for valor_agrupar in resultados_metricas.keys():
                    fila = [valor_agrupar] + [resultados_metricas[valor_agrupar][m] for m in metricas]
                    tabla_metricas.add_data(*fila)
            else:
                fila = [resultados_metricas[metrica] for metrica in metricas]
                tabla_metricas.add_data(*fila)
        
            wandb.log({name: tabla_metricas})
            if groupby is not None and not train:
                return tabla_metricas

    def buildTable(self, real_values, predictions, name="metricas"):
        real_values = list(real_values)
        predictions = list(predictions)
        """
        ind = real_values.index(43909.516)
        real_values.pop(ind)
        predictions.pop(ind)
        """
        tabla = wandb.Table(columns = ["valor_real", "prediccion"])
        for i in range(len(real_values)):
            tabla.add_data(real_values[i], predictions[i])
        
        wandb.log({name: tabla})
        return tabla

    def evaluate(self, groupby=None, name=None):
        """
        Evalua el modelo y registra las métricas en W&B.
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        """
        if name is None:
            name = self.name

        wandb_metrics_logger = WandbMetricsLogger()
        wandb_model_checkpoint = WandbModelCheckpoint(f"./src/modelado/monitoreo/modelos/modelos_tensorflow/{name}/"+"{epoch:02d}.keras", monitor='val_loss')

        X = self.train.drop(columns=[self.y])
        y = self.train[self.y]

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.25, random_state=42)

        X_test = self.test.drop(columns=[self.y])
        y_test = self.test[self.y]

        self.modelo.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=self.num_epochs, callbacks=[wandb_metrics_logger, wandb_model_checkpoint])


        predicciones = self.modelo.predict(X_test).flatten()
        self.visualizeRealvsPrediccion(real_values=y_test, predictions=predicciones, name=name)

        self.visualizeMetrics(resultados_metricas=self.modelo.history.history, metricas=list(self.modelo.history.history.keys()), train=True, groupby=None, name=name)    

        test_results = self.modelo.evaluate(X_test, y_test, return_dict=True)
        self.visualizeMetrics(resultados_metricas=test_results, metricas=[m for m in list(self.modelo.history.history.keys()) if "val" not in m], groupby=None, name=name)
        
        if groupby is not None:
            test_results = dict()
            grupos = X_test.groupby([groupby], sort=True)
            for valor_agrupar, X_grupo_test in grupos:
                y_g_test = y_test.filter(items = X_grupo_test.index, axis=0)
                test_results[valor_agrupar[0]] = self.modelo.evaluate(X_grupo_test, y_g_test, return_dict=True)
            
            self.visualizeMetrics(resultados_metricas=test_results, metricas=[m for m in list(self.modelo.history.history.keys()) if "val" not in m], groupby=groupby, name=name)    


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
df_train = pd.read_parquet('./data/Train/train_final.parquet')
df_test = pd.read_parquet('./data/Train/test_final.parquet')
df_train = df_train.dropna().reset_index(drop=True)
df_test = df_test.dropna().reset_index(drop=True)
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

# 4) X e y
feature_cols = [
    'tiempo_esperado', 'llegada_lon', 'llegada_lat',
    'hora_sin', 'hora_cos',
    'runway_occupied', 'queue_length', 'time_since_free',
    'aircraft_type', 'holding_point'
]
X_train = df_train[feature_cols]
y_train = df_train['tiempo_espera']
X_test = df_test[feature_cols]
y_test = df_test['tiempo_espera']

# 5) Preprocesado
numeric_feats     = ['tiempo_esperado','llegada_lon','llegada_lat','hora_sin','hora_cos','runway_occupied','queue_length','time_since_free']
categorical_feats = ['aircraft_type','holding_point']
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric_feats),
    ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), categorical_feats)
])


X_train_proc = preprocessor.fit_transform(X_train)
X_test_proc  = preprocessor.transform(X_test)

# Get feature names after fitting
feature_names_out = preprocessor.get_feature_names_out()
X_train_proc_df = pd.DataFrame(X_train_proc, index=X_train.index, columns=feature_names_out)
X_test_proc_df = pd.DataFrame(X_test_proc, index=X_test.index, columns=feature_names_out)

df_train_proc = X_train_proc_df.copy()
df_train_proc["tiempo_espera"] = y_train.values
df_test_proc = X_test_proc_df.copy()
df_test_proc["tiempo_espera"] = y_test.values

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
monitor_tf = MonitorTensorflow(modelo=model, train=df_train_proc, test=df_test_proc, y="tiempo_espera", num_epochs=1500, project='tf_PD2', name="tensorflow_modelo_final", entity='dacoleto-complutense-university-of-madrid')
monitor_tf.evaluate()

monitor_tf.finish()
