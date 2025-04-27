from monitor_general import MonitorGeneral
from pyspark.ml.feature import VectorAssembler, StandardScaler,  StringIndexer
from sklearn.model_selection import train_test_split
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator, MulticlassClassificationEvaluator
import wandb
import os

class MonitorSpark(MonitorGeneral):
    METRICAS_REGRESION = ['rmse', 'mse', 'mae']
    METRICAS_CLASIFICACION = ['accuracy', 'f1']

    def __init__(self, modelo, data, y, spark_session, regresion, project='spark_PD2', name="modelo_spark", entity='dacoleto-complutense-university-of-madrid'):
        """
        Inicializa el monitor para el modelo de machine learning.
        :param modelo: Modelo de machine learning a monitorizar
        :param data: Conjunto de datos a evaluar
        :param y: Variable objetivo
        :param regresion: True si el modelo es de regresión, False si es de clasificación
        :param spark_session: Sesión de Spark
        :param project: Nombre del proyecto en W&B
        :param name: Nombre del experimento
        :param entity: Nombre de la entidad en W&B
        """
        super().__init__(modelo=modelo, data=data, y=y, project=project, name=name, entity=entity)
        self.spark_session = spark_session
        self.regression = regresion
        self.modelo.setFeaturesCol("X_scaled")
        self.pipeline = self.buildPipeline()
        
    def buildPipeline(self):
        X = self.data.columns.copy()
        X.remove(self.y)
        assembler = VectorAssembler( inputCols = X, outputCol ='X')
        scaler = StandardScaler(inputCol='X', outputCol='X_scaled')
        
        return Pipeline(stages=[assembler, scaler, self.modelo])

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
        :return: Tabla de métricas
        """
        if groupby is not None:
            tabla_metricas = wandb.Table(columns=[groupby] + metricas)
            for g, metricas in resultados_metricas.items():
                fila = [g] + [metricas[m] for m in metricas]
                tabla_metricas.add_data(*fila)
        else:
            tabla_metricas = wandb.Table(columns=metricas)
            fila = [resultados_metricas[m] for m in resultados_metricas]
            tabla_metricas.add_data(*fila)
        
        wandb.log({name: tabla_metricas})

        if groupby is not None:
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
    
    def calculateMetrics(self, test_results, metricas):
        """
        Calcula las métricas de regresión y las registra en W&B.
        :param test_results: Predicciones del modelo
        :param metricas: Métricas a calcular
        """
        resultados_metricas = dict()
        for m in metricas:
            evaluador = RegressionEvaluator(labelCol=self.y, predictionCol="prediction", metricName=m)
            resultado = evaluador.evaluate(test_results)         
            resultados_metricas[m] = resultado
        
        return resultados_metricas
        
    def evaluate(self, groupby=None, name=None):
        """
        Evalua el modelo y registra las métricas en W&B.
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        """
        if name is None:
            name = self.name

        # Dividir los datos en entrenamiento y prueba
        train_data, test_data = self.data.randomSplit([0.8, 0.2], seed=7)

        # Entrenar el modelo
        self.pipeline_model = self.pipeline.fit(train_data)
        
        metricas = self.METRICAS_REGRESION if self.regression else self.METRICAS_CLASIFICACION

        test_results = self.pipeline_model.transform(test_data)
        
        real_values = test_results.select(self.y).collect()
        predictions = test_results.select("prediction").collect()
        self.buildScatter(real_values=real_values, predictions=predictions)

        resultados_metricas = self.calculateMetrics(test_results=test_results, metricas=metricas)
        self.visualizeMetrics(resultados_metricas=resultados_metricas, metricas=metricas, groupby=None, name=name)

        if groupby is not None:
            resultados_metricas = dict()
            valores_agrupar = test_data.select(groupby).distinct().orderBy(groupby).collect()
            for valor in valores_agrupar:
                valor = valor[0]
                test_data_grouped = test_data.filter(test_data[groupby] == valor)
                test_results = self.pipeline_model.transform(test_data_grouped)
                resultados_metricas[valor] = self.calculateMetrics(test_results=test_results, metricas=metricas)
        
            self.visualizeMetrics(resultados_metricas=resultados_metricas, metricas=metricas, groupby=groupby, name=name)

        #Guardar el modelo
        #self.saveModel(path=f"./src/modelado/monitoreo/modelos/modelos_spark/{name}")

    def saveModel(self, path):
        self.pipeline_model.write().overwrite().save(path)
        model_artifact = wandb.Artifact(name=self.name, type="model")
        model_artifact.add_dir(path)
        wandb.log_artifact(model_artifact)

    def setModel(self, model):
        self.model = model
        


from pyspark.sql.functions import unix_timestamp, hour
from pyspark.ml.regression import LinearRegression
from pyspark.sql import SparkSession
import pandas as pd

spark = SparkSession.builder.appName("SparkWandBExample").getOrCreate()
data = spark.read.csv("data/ex1/eventos_espera_semana_nuevo.csv", header=True, inferSchema=True)


data = data.drop("ICAO", "lat", "lon")
data = data.withColumn("fecha_despegue", unix_timestamp("fecha_despegue").cast("double"))
data = data.withColumn("ultimo_parado", unix_timestamp("ultimo_parado").cast("double"))
data = data.withColumn("despegue", unix_timestamp("despegue").cast("double"))

data = data.dropna()

# Convertir columnas de tipo string a índices numéricos
indexer_aircraft_type = StringIndexer(inputCol="aircraft_type", outputCol="aircraft_type_ind")

indexer_aircraft_type_model = indexer_aircraft_type.fit(data)
data = indexer_aircraft_type_model.transform(data)
indexer_holding_point = StringIndexer(inputCol="holding_point", outputCol="holding_point_ind")
indexer_holding_point_model = indexer_holding_point.fit(data)
data = indexer_holding_point_model.transform(data)
indexer_runway = StringIndexer(inputCol="runway", outputCol="runway_ind")
indexer_runway_model = indexer_runway.fit(data)
data = indexer_runway_model.transform(data) 

data = data.drop("aircraft_type", "holding_point", "runway")

# Definir el modelo de regresión lineal
lr = LinearRegression(featuresCol='lol', labelCol='tiempo_espera', maxIter=100, regParam=0.1)

monitor_spark = MonitorSpark(modelo=lr, data=data, y='tiempo_espera', spark_session=spark, regresion=True, name="metricas_por_hora")
monitor_spark.evaluate(groupby="hora_despegue")
"""
monitor_spark = MonitorSpark(modelo=lr, data=data, y='tiempo_espera', spark_session=spark, regresion=True, name="metricas_sin_agrupar")
monitor_spark.evaluate()
"""
monitor_spark.finish()