import wandb
from monitor_general import MonitorGeneral

class MonitorTensorflow(MonitorGeneral):
    METRICAS_REGRESION = ['rmse', 'mse', 'mae']
    METRICAS_CLASIFICACION = ['accuracy', 'f1']

    def __init__(self, modelo, data, y, spark_session, regresion, project='spark_PD2', name="modelo_spark", entity='dacoleto-complutense-university-of-madrid'):
        """
        Inicializa el monitor para el modelo de machine learning.
        :param modelo: Modelo de machine learning a monitorizar
        :param data: Conjunto de datos a evaluar
        :param y: Variable objetivo
        :param spark_session: Sesión de Spark
        :param project: Nombre del proyecto en W&B
        :param name: Nombre del experimento
        :param entity: Nombre de la entidad en W&B
        """
        super().__init__(modelo=modelo, data=data, y=y, regression=regresion, project=project, name=name, entity=entity)
        self.spark_session = spark_session
        self.pipeline = self.buildPipeline()
        

    def visualizeMetrics(self, resultados_metricas, metricas, groupby=None, name="metricas"):
        """
        Visualiza las métricas en W&B.
        :param resultados_metricas: Resultados de las métricas
        :param metricas: Métricas a visualizar  
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        """
                                
        tabla_metricas = self.buildTable(resultados_metricas, metricas=metricas, groupby=groupby, name=name)
        
        if groupby is not None: 
            self.buildGraph(tabla_metricas=tabla_metricas, groupby=groupby, metricas=metricas, name=name)

    def buildTable(self, resultados_metricas, metricas, groupby=None, name="metricas"):
        """
        Construye una tabla de métricas para registrar en W&B.
        :param resultados_metricas: Resultados de las métricas
        :return: Tabla de métricas
        """
        if groupby is not None:
            tabla_metricas = wandb.Table(columns=[groupby] + metricas)
            for g, metricas in resultados_metricas.items():
                fila = [g] + [metricas[m] for m in metricas]
                tabla_metricas.add_data(*fila)
            #self.buildGraph(tabla_metricas=tabla_metricas, groupby=groupby, metricas=metricas, name=name)            
        else:
            tabla_metricas = wandb.Table(columns=metricas)
            fila = [resultados_metricas[m] for m in resultados_metricas]
            tabla_metricas.add_data(*fila)
        
        wandb.log({name: tabla_metricas})

        return tabla_metricas

    def buildGraph(self, tabla_metricas, groupby, metricas, name="metricas"):
        """
        Construye una tabla de métricas para registrar en W&B.
        :param resultados_metricas: Resultados de las métricas
        :return: Tabla de métricas
        """
        for metrica in metricas:
                wandb.log({
                    f"{name}_{metrica}": wandb.plot.line(
                        tabla_metricas, groupby, metrica, title=metrica
                    )
                })

    def calculateMetrics(self, test_results, metricas):
        """
        Calcula las métricas de regresión y las registra en W&B.
        :param test_results: Resultados de la evaluación del modelo
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param kwargs: Otros parámetros
        """
        resultados_metricas = dict()
        for m in metricas:
            evaluador = RegressionEvaluator(labelCol=self.y, predictionCol="prediction", metricName=m)
            resultado = evaluador.evaluate(test_results)         
            resultados_metricas[m] = resultado
        
        return resultados_metricas
        
    def evaluate(self, groupby=None, name="metricas"):
        """
        Evalua el modelo registra las métricas en W&B.
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        """
        # Dividir los datos en entrenamiento y prueba
        train_data, test_data = self.data.randomSplit([0.8, 0.2], seed=7)

        # Entrenar el modelo
        self.pipeline_model = self.pipeline.fit(train_data)
        
        metricas = self.METRICAS_REGRESION if self.regression else self.METRICAS_CLASIFICACION
        resultados_metricas = dict()
        
        if groupby is not None:
            valores_agrupar = test_data.select(groupby).distinct().orderBy(groupby).collect()
            for valor in valores_agrupar:
                valor = valor[0]
                test_data_grouped = test_data.filter(test_data[groupby] == valor)
                test_results = self.pipeline_model.transform(test_data_grouped)
                resultados_metricas[valor] = self.calculateMetrics(test_results=test_results, metricas=metricas)
            
        else:
            test_results = self.pipeline_model.transform(test_data)
            resultados_metricas = self.calculateMetrics(test_results=test_results, metricas=metricas)
        
        self.visualizeMetrics(resultados_metricas=resultados_metricas, metricas=metricas, groupby=groupby, name=name)
        