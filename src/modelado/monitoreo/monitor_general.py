import wandb
from abc import ABC, abstractmethod

class MonitorGeneral(ABC):
    def __init__(self, modelo, train, test, y, project='pruebaPD2', name="modelo", entity='dacoleto-complutense-university-of-madrid'):
        """
        Inicializa el monitor general para el modelo de machine learning.
        :param modelo: Modelo de machine learning a monitorizar
        :param train: Datos de entrenamiento
        :param test: Datos de prueba
        :param y: Variable objetivo
        :param project: Nombre del proyecto en W&B
        :param name: Nombre del experimento
        :param entity: Nombre de la entidad en W&B
        """
        self.name = name
        self.modelo = modelo
        self.train = train
        self.test = test
        self.y = y

        wandb.init(
            project=project,
            name=name,
            entity=entity
        )

    @abstractmethod
    def evaluate(self, *args):
        """Método abstracto para evaluar el modelo"""
        pass
    
    @abstractmethod
    def visualizeMetrics(self, *args):
        """Método abstracto para visualizar las métricas"""
        pass

    @abstractmethod
    def buildTableMetrics(self, *args):
        """Método abstracto para construir una tabla de métricas"""
        pass

    @abstractmethod
    def buildGraph(self, *args):
        """Método abstracto para construir una gráfica de métricas"""
        pass
            
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
    
    def buildScatter(self, tabla_real_vs_predicciones):
        """
        Construye un gráfico de dispersión comparando los valores reales y las predicciones.
        Con outliers no funciona
        """
        scatter_plot =  wandb.plot_table(
            data_table=tabla_real_vs_predicciones,
            vega_spec_name="dacoleto-complutense-university-of-madrid/dispersion",
            fields={"x": "valor_real", "y": "prediccion"},
            string_fields={"title": "Real vs Predicción"},
        )
        wandb.log({"Real vs Predicción" : scatter_plot})
    
    def buildHistogram(self, real_values, predictions, bins=20):
        """
        Crea un histograma comparando las distribuciones de predicciones y valores reales.
        """
        tabla_reales = wandb.Table(data=[[v] for v in real_values], columns=["valor"])
        tabla_predicciones = wandb.Table(data=[[v] for v in predictions], columns=["valor"])

        # Loguear el histograma con distinción de tipos
        wandb.log({
            "Distribución de valores reales": wandb.plot_table(data_table=tabla_reales, vega_spec_name="dacoleto-complutense-university-of-madrid/histgood", fields=["valor"]),
            "Distribución de predicciones": wandb.plot_table(data_table=tabla_predicciones, vega_spec_name="dacoleto-complutense-university-of-madrid/histgood", fields=["valor"])
        })

    def finish(self):
        """Finaliza la sesión de W&B"""
        wandb.finish()