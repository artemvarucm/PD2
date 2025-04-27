import wandb
from monitor_general import MonitorGeneral
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from wandb.integration.keras import WandbMetricsLogger
from wandb.integration.keras import WandbModelCheckpoint
import numpy as np
from wandb.plot.custom_chart import plot_table

class MonitorTensorflow(MonitorGeneral):
    def __init__(self, modelo, data, y, num_epochs, project='tf_PD2', name="modelo_tf", entity='dacoleto-complutense-university-of-madrid'):
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

        X = self.data.drop(columns=[self.y])
        y = self.data[self.y]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=42)

        # Entrenar el modelo
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


import tensorflow as tf

# Función para la métrica personalizada
def custom_metric_lolaso(y_true, y_pred):
    return tf.reduce_mean(tf.abs(y_true - y_pred)-tf.abs(y_true - y_pred))

model = tf.keras.Sequential([
    layers.Dense(64, activation='relu', input_shape=[len(df.drop(columns=["tiempo_espera"]).keys())]),
    layers.Dense(1)
])
model.compile(optimizer='adam',
              loss='mse',
              metrics=["mae", "mse", "msle", "cosine_similarity", custom_metric_lolaso])

"""
monitor_tf = MonitorTensorflow(modelo=model, data=df, y="tiempo_espera", num_epochs=5, project='tf_PD2', name="modelo_tf", entity='dacoleto-complutense-university-of-madrid')
monitor_tf.evaluate(groupby="hora_despegue")
"""
monitor_tf = MonitorTensorflow(modelo=model, data=df, y="tiempo_espera", num_epochs=2, project='tf_PD2', name="modelo_general5", entity='dacoleto-complutense-university-of-madrid')
monitor_tf.evaluate()

monitor_tf.finish()
