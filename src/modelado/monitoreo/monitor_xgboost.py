import wandb
from monitor_general import MonitorGeneral
import numpy as np
from sklearn.model_selection import train_test_split
from wandb.plot.custom_chart import plot_table
from sklearn.metrics import root_mean_squared_error, mean_squared_error, mean_absolute_error, r2_score, f1_score, accuracy_score
from xgboost import XGBRegressor
import os
import pickle

class MonitorXGBOOST(MonitorGeneral):
    METRICAS_REGRESION = ['rmse', 'mse', 'mae', 'r2']
    METRICAS_CLASIFICACION = ['accuracy', 'f1']

    def __init__(self, modelo, train, test, y, regresion=True, project='xgboost_PD2', name="modelo_xboost", entity='dacoleto-complutense-university-of-madrid'):
        """
        Inicializa el monitor para modelos de scikit-learn.
        :param modelo: Modelo de machine learning a monitorizar
        :param train: Datos de entrenamiento
        :param test: Datos de prueba
        :param y: Variable objetivo
        :param regresion: True si el modelo es de regresión, False si es de clasificación
        :param project: Nombre del proyecto en W&B
        :param name: Nombre del experimento
        :param entity: Nombre de la entidad en W&B
        """
        super().__init__(modelo=modelo, train=train, test=test, y=y, project=project, name=name, entity=entity)
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
        Construye un gráfico para cada métrica y lo registra en W&B.
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

    def buildTable(self, real_values, predictions, name="metricas"):
        """
        Construye una tabla con los valores reales y las predicciones.
        :param real_values: Valores reales
        :param predictions: Predicciones del modelo
        :param name: Nombre de la visualización
        """
        real_values = list(real_values)
        predictions = list(predictions)

        tabla = wandb.Table(columns=["valor_real", "prediccion"])
        for i in range(len(real_values)):
            tabla.add_data(real_values[i], predictions[i])

        wandb.log({name: tabla})
        return tabla

    def evaluate(self, groupby=None, name=None):
        """
        Evalúa el modelo y registra las métricas en W&B.
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        """
        if name is None:
            name = self.name

        X_train = self.train.drop(columns=[self.y])
        y_train = self.train[self.y]

        X_test = self.test.drop(columns=[self.y])  # Cambio aquí
        y_test = self.test[self.y]  # Cambio aquí

        self.modelo.fit(X_train, y_train)

        y_pred = self.modelo.predict(X_test)

        self.visualizeRealvsPrediccion(real_values=y_test, predictions=y_pred, name=name)

        metricas = self.METRICAS_REGRESION if self.regresion else self.METRICAS_CLASIFICACION
        resultados_metricas = self.calculateMetrics(y_true=y_test, y_pred=y_pred, metricas=metricas)

        self.visualizeMetrics(resultados_metricas=resultados_metricas, metricas=metricas, groupby=None, name=name)

        if groupby is not None:
            resultados_metricas = dict()
            grupos = X_test.groupby([groupby], sort=True)
            for valor_agrupar, X_grupo_test in grupos:
                y_g_test = y_test.filter(items=X_grupo_test.index, axis=0)
                y_g_pred = self.modelo.predict(X_grupo_test)
                resultados_metricas[valor_agrupar[0]] = self.calculateMetrics(y_pred=y_g_pred, y_true=y_g_test, metricas=metricas)

            self.visualizeMetrics(resultados_metricas=resultados_metricas, metricas=metricas, groupby=groupby, name=name)

        self.saveModel(path=f"./src/modelado/monitoreo/modelos/modelos_xgboost/{self.name}.pkl")

    def saveModel(self, path):
        """
        Guarda el modelo entrenado en un archivo.
        :param path: Ruta del archivo donde guardar el modelo
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as m:
            pickle.dump(self.modelo, m)
        model_artifact = wandb.Artifact(name=self.name, type="model")
        model_artifact.add_file(path)
        wandb.log_artifact(model_artifact)

    def setModel(self, model):
        """
        Establece un nuevo modelo.
        :param model: Modelo a asignar
        """
        self.modelo = model


import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold, RandomizedSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
import joblib

# 1) Carga y filtrado
df_train = pd.read_parquet(
    './data/Train/train_final.parquet'
)
df_test = pd.read_parquet('./data/Train/test_final.parquet')

df_train = df_train[df_train['tiempo_espera'] <= 500]
df_test = df_test[df_test['tiempo_espera'] <= 500]

# 2) Ingeniería de features
# Hora cíclica
df_train['hora_decimal'] = df_train['timestamp'].dt.hour + df_train['timestamp'].dt.minute / 60
df_train['hora_sin']     = np.sin(2 * np.pi * df_train['hora_decimal'] / 24)
df_train['hora_cos']     = np.cos(2 * np.pi * df_train['hora_decimal'] / 24)


df_test['hora_decimal'] = df_test['timestamp'].dt.hour + df_test['timestamp'].dt.minute/60
df_test['hora_sin']     = np.sin(2*np.pi * df_test['hora_decimal']/24)
df_test['hora_cos']     = np.cos(2*np.pi * df_test['hora_decimal']/24)

# Día de la semana y fin de semana
df_train['weekday'] = df_train['timestamp'].dt.weekday
df_train['is_weekend'] = df_train['weekday'].isin([5, 6]).astype(int)
# Interacción simple
df_train['queue_x_runway'] = df_train['queue_length'] * df_train['runway_occupied']

# Día de la semana y fin de semana
df_test['weekday'] = df_test['timestamp'].dt.weekday
df_test['is_weekend'] = df_test['weekday'].isin([5, 6]).astype(int)
# Interacción simple
df_test['queue_x_runway'] = df_test['queue_length'] * df_test['runway_occupied']

# 3) Definición de X e y (log-transform del target)
feature_cols = [
    'tiempo_esperado', 'llegada_lon', 'llegada_lat',
    'hora_sin', 'hora_cos', 'weekday', 'is_weekend', 'queue_x_runway',
    'runway_occupied', 'queue_length', 'time_since_free',
    'aircraft_type', 'holding_point', 'parado', 'hold_pt_occupied'
]

# renombramos
X_train = df_train[feature_cols]
y_train = df_train['tiempo_espera']
y_train_log = np.log1p(y_train)

# definimos X_test / y_test_log
X_test = df_test[feature_cols]
y_test = df_test['tiempo_espera']
y_test_log = np.log1p(y_test)

# 5) Preprocesado
dnumeric = [c for c in feature_cols if c not in ['aircraft_type', 'holding_point']]
dcat     = ['aircraft_type', 'holding_point']
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), dnumeric),
    ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), dcat)
])

dnumeric = [c for c in feature_cols if c not in ['aircraft_type', 'holding_point']]
dcat     = ['aircraft_type', 'holding_point']
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), dnumeric),
    ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), dcat)
])

final_pipeline = Pipeline([
    ('pre', preprocessor),
    ('xgb', XGBRegressor(objective='reg:squarederror', random_state=42, max_depth=12, eta=0.0, eval_metric='mae'))
])

monitor = MonitorXGBOOST(modelo=final_pipeline, train=df_train, test=df_test, y='tiempo_espera', regresion=True, project='xgboost_PD2', name="modelo_final", entity='dacoleto-complutense-university-of-madrid')
monitor.evaluate()
monitor.finish()