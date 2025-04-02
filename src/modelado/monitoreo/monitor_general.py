import wandb
from abc import ABC, abstractmethod

class MonitorGeneral(ABC):
    def __init__(self, modelo, data, y, regression, project='pruebaPD2', name="modelo_spark", entity='dacoleto-complutense-university-of-madrid'):
        """
        Inicializa el monitor general para el modelo de machine learning.
        :param modelo: Modelo de machine learning a monitorizar
        :param data: Conjunto de datos a evaluar
        :param y: Variable objetivo
        :param regression: True si es regresion, False si es clasificacion
        :param project: Nombre del proyecto en W&B
        :param name: Nombre del experimento
        :param entity: Nombre de la entidad en W&B
        """
        self.modelo = modelo
        self.modelo.setFeaturesCol("X_scaled")
        self.data = data
        self.y = y
        self.regression = regression

        wandb.init(
            project=project,
            name=name,
            entity=entity, 
        )

    @abstractmethod
    def evaluate(self, *args):
        """Método abstracto para evaluar el modelo"""
        pass
    
    @abstractmethod
    def calculateMetrics(self, *args):
        """Método abstracto para calcular métricas"""
        pass

    @abstractmethod
    def buildTable(self, *args):
        """Método abstracto para construir una tabla de métricas"""
        pass

    @abstractmethod
    def buildGraph(self, *args):
        """Método abstracto para construir un gráfico de métricas"""
        pass
    
    def finish(self):
        """Finaliza la sesión de W&B"""
        wandb.finish()