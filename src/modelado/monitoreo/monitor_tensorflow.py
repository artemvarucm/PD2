import wandb
from monitor_general import MonitorGeneral
from sklearn.model_selection import train_test_split
from wandb.integration.keras import WandbMetricsLogger
from wandb.integration.keras import WandbModelCheckpoint

class MonitorTensorflow(MonitorGeneral):
    def __init__(self, modelo, data, y, num_epochs, project='spark_PD2', name="modelo_spark", entity='dacoleto-complutense-university-of-madrid'):
        """
        Inicializa el monitor para el modelo de machine learning.
        :param modelo: Modelo de machine learning a monitorizar
        :param data: Conjunto de datos a evaluar
        :param y: Variable objetivo
        :param num_epochs: Número de épocas para el entrenamiento
        :param project: Nombre del proyecto en W&B
        :param name: Nombre del experimento
        :param entity: Nombre de la entidad en W&B
        """
        self.num_epochs = num_epochs
        super().__init__(modelo=modelo, data=data, y=y, project=project, name=name, entity=entity)
        
    
    def buildTable(self, resultados_metricas, metricas, groupby=None, name="metricas", train=False):
        """
        Construye una tabla de métricas para registrar en W&B.
        :param resultados_metricas: Resultados de las métricas
        :return: Tabla de métricas
        """
        name = f"{name}_entrenamiento" if train else f"{name}_test"
        columns = ["epoch"] + metricas if train  else metricas

        if groupby is not None:
            tabla_metricas = wandb.Table(columns=[groupby] + columns)
            for g, metricas in resultados_metricas.items():
                fila = [g] + [metricas[m] for m in metricas]
                tabla_metricas.add_data(*fila)
        else:
            tabla_metricas = wandb.Table(columns=columns)
            if train:
                for epoch in range(self.num_epochs):
                    fila = [epoch] + [resultados_metricas[metrica][epoch] for metrica in metricas]
                    tabla_metricas.add_data(*fila)
            else:
                fila = [resultados_metricas[metrica] for metrica in metricas]
                tabla_metricas.add_data(*fila)
                        
        wandb.log({name: tabla_metricas})

        #return tabla_metricas
    
    def evaluate(self, groupby=None, name="metricas"):
        """
        Evalua el modelo registra las métricas en W&B.
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        """

        wandb_metrics_logger = WandbMetricsLogger()
        wandb_model_checkpoint = WandbModelCheckpoint(name+"-{epoch:02d}.keras", monitor='val_loss')
        # Dividir los datos en entrenamiento y prueba
        X = self.data.drop(columns=[self.y])
        y = self.data[self.y]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=42)

        # Entrenar el modelo
        self.modelo.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=self.num_epochs, callbacks=[wandb_metrics_logger, wandb_model_checkpoint])

        self.buildTable(resultados_metricas=self.modelo.history.history, metricas=list(self.modelo.history.history.keys()), groupby=None, name="metricas", train=True)
        
        test_results = self.modelo.evaluate(X_test, y_test, return_dict=True)
    
        self.buildTable(resultados_metricas=test_results, metricas=list(test_results.keys()), groupby=None, name="metricas", train=False)
    
        
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers

df = pd.read_csv("data/ex1/eventos_espera_semana_nuevo.csv")
df = pd.get_dummies(df, columns=["aircraft_type", "runway", "holding_point"])
import datetime

# Asegúrate de que las columnas están en formato datetime
df["fecha_despegue"] = pd.to_datetime(df["fecha_despegue"])
df["ultimo_parado"] = pd.to_datetime(df["ultimo_parado"])
df["despegue"] = pd.to_datetime(df["despegue"])

# Convertir las fechas a segundos desde el 1 de enero de 1970
df["fecha_despegue"] = (df["fecha_despegue"] - datetime.datetime(1970, 1, 1)).dt.total_seconds()
df["ultimo_parado"] = (df["ultimo_parado"] - datetime.datetime(1970, 1, 1)).dt.total_seconds()
df["despegue"] = (df["despegue"] - datetime.datetime(1970, 1, 1)).dt.total_seconds()

df = df.drop(columns=["ICAO", "lat", "lon"])

model = tf.keras.Sequential([
    layers.Dense(64, activation='relu', input_shape=[len(df.drop(columns=["tiempo_espera"]).keys())]),
    layers.Dense(1)
])

import tensorflow as tf

# Función para la métrica personalizada
def custom_metric_lolaso(y_true, y_pred):
    return tf.reduce_mean(tf.abs(y_true - y_pred)-tf.abs(y_true - y_pred))


# Compilación del modelo
model.compile(optimizer='adam',
              loss='mse',
              metrics=["mae", "mse", "msle", "cosine_similarity", custom_metric_lolaso])

monitor_tf = MonitorTensorflow(modelo=model, data=df, y="tiempo_espera", num_epochs=5, project='tf_PD2', name="modelo_tf", entity='dacoleto-complutense-university-of-madrid')
monitor_tf.evaluate(groupby=None, name="modelo1")
monitor_tf.finish()
