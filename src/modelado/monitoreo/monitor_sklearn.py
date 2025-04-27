from monitor_general import MonitorGeneral
import pandas as pd
import wandb
from sklearn.metrics import root_mean_squared_error, mean_squared_error, mean_absolute_error, r2_score, f1_score, accuracy_score
from sklearn.model_selection import train_test_split
import pickle
from sklearn.linear_model import LinearRegression
import os


class MonitorSklearn(MonitorGeneral):
    METRICAS_REGRESION = ['rmse', 'mse', 'mae', 'r2']
    METRICAS_CLASIFICACION = ['accuracy', 'f1']

    def __init__(self, modelo, data, y, regresion=True, project='sklearn_PD2', name="modelo_sklearn", entity='dacoleto-complutense-university-of-madrid'):
        """
        Inicializa el monitor para modelos de scikit-learn
        :param modelo: Modelo de machine learning a monitorizar
        :param data: Conjunto de datos a evaluar
        :param y: Variable objetivo
        :param regresion: True si el modelo es de regresión, False si es de clasificación
        :param project: Nombre del proyecto en W&B
        :param name: Nombre del experimento
        :param entity: Nombre de la entidad en W&B
        """
        super().__init__(modelo=modelo, data=data, y=y, project=project, name=name, entity=entity)
        self.regresion = regresion

    def calculateMetrics(self, y_true, y_pred, metricas):
        """
        Calcula las métricas de regresión y las registra en W&B.
        :param y_true: Valores reales
        :param y_pred: Valores predichos
        :param metricas: Métricas a calcular
        """
        resultados = dict()
        for m in metricas:
            if self.regresion:
                if m == 'rmse':
                    resultados[m] = root_mean_squared_error(y_true, y_pred)
                elif m == 'mse':
                    resultados[m] = mean_squared_error(y_true, y_pred)
                elif m == 'mae':
                    resultados[m] = mean_absolute_error(y_true, y_pred)
                elif m == 'r2':
                    resultados[m] = r2_score(y_true, y_pred)
            else:
                if m == 'accuracy':
                    resultados[m] = accuracy_score(y_true, y_pred)
                elif m == 'f1':
                    resultados[m] = f1_score(y_true, y_pred)
        return resultados

    def visualizeMetrics(self, resultados_metricas, metricas, groupby=None, name="metricas"):
        """
        Visualiza las métricas en W&B.
        :param resultados_metricas: Resultados de las métricas
        :param metricas: Métricas a visualizar  
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        """
        tabla_metricas = self.buildTableMetrics(resultados_metricas, metricas=metricas, groupby=groupby, name=name)
        if groupby is not None:
            self.buildGraph(tabla_metricas=tabla_metricas, groupby=groupby, metricas=metricas, name=name)

    def buildTableMetrics(self, resultados_metricas, metricas, groupby=None, name="metricas"):
        """
        Construye una tabla de métricas para registrar en W&B.
        :param resultados_metricas: Resultados de las métricas
        :param metricas: Métricas a visualizar
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        :return: Tabla de métricas
        """
        if groupby is not None:
            tabla_metricas = wandb.Table(columns=[groupby] + metricas)
            for g, valores in resultados_metricas.items():
                fila = [g] + [valores[m] for m in metricas]
                tabla_metricas.add_data(*fila)
        else:
            tabla_metricas = wandb.Table(columns=metricas)
            fila = [resultados_metricas[m] for m in metricas]
            tabla_metricas.add_data(*fila)

        wandb.log({name: tabla_metricas})
        return tabla_metricas

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
    
    def visualizeRealvsPrediccion(self, real_values, predictions, name="Real vs Predicción"):
        """
        Visualiza la comparación entre los valores reales y las predicciones.
        :param real_values: Valores reales
        :param predictions: Predicciones del modelo
        :param name: Nombre de la visualización
        """
        tabla = self.buildTable(real_values=real_values, predictions=predictions, name=name)
        self.buildScatter(tabla_real_vs_predicciones=tabla)
        self.buildHistogram(real_values=real_values, predictions=predictions)

    def buildScatter(self, real_values, predictions, name=f"Real vs Predicción"):
        """
        Con outliers no funciona
        """
        table = self.buildTable(real_values=real_values, predictions=predictions, name=name)
        scatter_plot = wandb.plot.scatter(table, x="valor_real", y="prediccion", title=name)
        wandb.log({name : scatter_plot})


    def buildTable(self, real_values, predictions,groupby=None, name="metricas"):
        real_values = list(real_values)
        predictions = list(predictions)
        """
        ind = real_values.index(43909.516)
        real_values.pop(ind)
        predictions.pop(ind)"""

        table = wandb.Table(columns = ["valor_real", "prediccion"])
        for i in range(len(real_values)):
            table.add_data(real_values[i], predictions[i])
        
        return table
    
    def visualizeRealvsPrediccion(self, real_values, predictions, name="Real vs Predicción"):
        """
        Visualiza la comparación entre los valores reales y las predicciones.
        :param real_values: Valores reales
        :param predictions: Predicciones del modelo
        :param name: Nombre de la visualización
        """
        tabla = self.buildTable(real_values=real_values, predictions=predictions, name=name)
        self.buildScatter(tabla_real_vs_predicciones=tabla)
        self.buildHistogram(real_values=real_values, predictions=predictions)
    
    def buildHistogram(self, real_values, predictions, bins=20):
        """
        Crea un histograma comparando las distribuciones de predicciones y valores reales.
        """
        # Crear la tabla con una columna de valores y otra de tipo (real o predicción)
        tabla_reales = wandb.Table(data=[[v] for v in real_values], columns=["valor"])
        tabla_predicciones = wandb.Table(data=[[v] for v in predictions], columns=["valor"])
        # Loguear el histograma con distinción de tipos
        wandb.log({
            "Distribución de valores reales": wandb.plot_table(data_table=tabla_reales, vega_spec_name="dacoleto-complutense-university-of-madrid/histgood", fields=["valor"]),
            "Distribución de predicciones": wandb.plot_table(data_table=tabla_predicciones, vega_spec_name="dacoleto-complutense-university-of-madrid/histgood", fields=["valor"])
        })

    def evaluate(self, groupby=None, name=None):
        """
        Evalua el modelo y registra las métricas en W&B.
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        """
        if name is None:
            name = self.name

        X = self.data.drop(columns=[self.y])
        y = self.data[self.y]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.modelo.fit(X_train, y_train)
        y_pred = self.modelo.predict(X_test)

        self.buildScatter(real_values=y_test, predictions=y_pred)

        metricas = self.METRICAS_REGRESION if self.regresion else self.METRICAS_CLASIFICACION
        resultados_metricas = self.calculateMetrics(y_true=y_test, y_pred=y_pred, metricas=metricas)

        self.visualizeMetrics(resultados_metricas=resultados_metricas, metricas=metricas, groupby=None, name=name)

        if groupby is not None:
            resultados_metricas = dict()
            grupos = X_test.groupby([groupby], sort=True)
            for valor_agrupar, X_grupo_test in grupos:
                y_g_test = y_test.filter(items = X_grupo_test.index, axis=0)
                y_g_pred = self.modelo.predict(X_grupo_test)
                resultados_metricas[valor_agrupar[0]] = self.calculateMetrics(y_pred=y_g_pred, y_true=y_g_test, metricas=metricas)


            self.visualizeMetrics(resultados_metricas=resultados_metricas, metricas=metricas, groupby=groupby, name=name)
        
        #self.saveModel(path=f"./src/modelado/monitoreo/modelos/modelos_sklearn/{self.name}.pkl")

    def saveModel(self, path):
        with open(path, "wb") as m:
            pickle.dump(self.modelo, m)
        model_artifact = wandb.Artifact(name=self.name, type="model")
        model_artifact.add_file(path)
        wandb.log_artifact(model_artifact)

    def setModel(self, model):
        self.modelo = model

import pandas as pd

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

model = LinearRegression()
"""
monitor_sk = MonitorSklearn(modelo=model, data=df, y="tiempo_espera", regresion=True, project='sklearn_PD2', name="modelo_agrupado", entity='dacoleto-complutense-university-of-madrid')
monitor_sk.evaluate(groupby="hora_despegue")
"""
monitor_sk = MonitorSklearn(modelo=model, data=df, y="tiempo_espera", regresion=True, project='sklearn_PD2', name="modelo_general", entity='dacoleto-complutense-university-of-madrid')
monitor_sk.evaluate()

monitor_sk.finish()