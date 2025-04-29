import wandb
from monitor_general import MonitorGeneral
import numpy as np
from sklearn.model_selection import train_test_split
from wandb.plot.custom_chart import plot_table
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_absolute_error
import joblib

class MonitorXGBoost(MonitorGeneral):
    def __init__(self, modelo, train, test, y, project='xgb_PD2', name="modelo_xgb", entity='dacoleto-complutense-university-of-madrid'):
        """
        Inicializa el monitor para el modelo de machine learning.
        :param modelo: Modelo de machine learning a monitorizar
        :param train: DataFrame de entrenamiento
        :param test: DataFrame de test
        :param y: Variable objetivo
        :param num_epochs: Número de épocas para el entrenamiento (si aplica)
        :param project: Nombre del proyecto en W&B
        :param name: Nombre del experimento
        :param entity: Nombre de la entidad en W&B
        """
        super().__init__(modelo=modelo, train=train, test=test, y=y, project=project, name=name, entity=entity)
    
    