import wandb
from monitor_general import MonitorGeneral
import numpy as np
from sklearn.model_selection import train_test_split
from wandb.plot.custom_chart import plot_table
from sklearn.metrics import root_mean_squared_error, mean_squared_error, mean_absolute_error, r2_score, f1_score, accuracy_score
from xgboost import XGBRegressor

class MonitorXGBOOST(MonitorGeneral):
    METRICAS_REGRESION = ['mae']
    METRICAS_CLASIFICACION = ['accuracy', 'f1']

    def __init__(self, params, train, val, test, y,  modelo=None, regresion=True, num_boost_round=2500, early_stopping_rounds=20, project='xgboost_PD2', name="modelo_xboost", entity='dacoleto-complutense-university-of-madrid'):
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
        :param params: Parámetros del modelo
        :param num_boost_round: Número de rondas de boosting

        """
        super().__init__(modelo=modelo, train=train, test=test, y=y, project=project, name=name, entity=entity)
        self.val = val
        self.regresion = regresion
        self.params = params
        self.num_boost_round = num_boost_round
        self.early_stopping_rounds = early_stopping_rounds

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
        self.buildPlotBar(resultados_metricas=resultados_metricas, metricas=metricas)
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
        
        X_val   = self.val.drop(columns=[self.y])
        y_val   = self.val[self.y]
       
        X_test  = self.test.drop(columns=[self.y])
        y_test  = self.test[self.y]

        numeric_feats     = ['tiempo_esperado','llegada_lon','llegada_lat','hora_sin','hora_cos','runway_occupied','queue_length','time_since_free', 'hold_pt_occupied']
        categorical_feats = ['aircraft_type','holding_point']
        preprocessor = ColumnTransformer([
            ('num', StandardScaler(), numeric_feats),
            ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), categorical_feats)
        ])

        X_train_proc = preprocessor.fit_transform(X_train)
        X_val_proc   = preprocessor.transform(X_val)
        X_test_proc  = preprocessor.transform(X_test)

        dtrain = xgb.DMatrix(X_train_proc, label=y_train)
        dval   = xgb.DMatrix(X_val_proc,   label=y_val)
        dtest  = xgb.DMatrix(X_test_proc,  label=y_test)
        
        self.modelo = xgb.train(self.params, dtrain, num_boost_round=self.num_boost_round, evals=[(dtrain,'train'),(dval,'valid')], early_stopping_rounds=self.early_stopping_rounds, verbose_eval=True)

        y_pred = self.modelo.predict(dtest)

        self.visualizeRealvsPrediccion(real_values=y_test, predictions=y_pred, name=name)

        metricas = self.METRICAS_REGRESION if self.regresion else self.METRICAS_CLASIFICACION
        resultados_metricas = self.calculateMetrics(y_true=y_test, y_pred=y_pred, metricas=metricas)

        self.visualizeMetrics(resultados_metricas=resultados_metricas, metricas=metricas, groupby=None, name=name)

        if groupby is not None:
            resultados_metricas = dict()
            grupos = self.test.groupby([groupby], sort=True)
            for valor_agrupar, X_grupo_test in grupos:
                y_g_test = y_test.filter(items=X_grupo_test.index, axis=0)
                y_g_pred = self.modelo.predict(X_grupo_test)
                resultados_metricas[valor_agrupar[0]] = self.calculateMetrics(y_pred=y_g_pred, y_true=y_g_test, metricas=metricas)

            self.visualizeMetrics(resultados_metricas=resultados_metricas, metricas=metricas, groupby=groupby, name=name)

        self.saveData(path=f"./src/modelado/monitoreo/datasets/xgboost/{self.name}", train=self.train, test=self.test)
        self.saveModel(path=f"./src/modelado/monitoreo/modelos/xgboost/{self.name}.pkl")



import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, KFold, RandomizedSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error
import xgboost as xgb


df_train = pd.read_parquet('./data/Train/train_final.parquet')
df_test = pd.read_parquet('./data/Train/test_final.parquet')

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

df_train, df_val = train_test_split(
    df_train,
    test_size=0.2,
    random_state=42
)

params = {
    'objective':   'reg:squarederror',
    'max_depth':   12,
    'eta':         0.05,
    'seed':        42,
    'eval_metric': 'mae'
}

monitor = MonitorXGBOOST(params=params, train=df_train, val=df_val, test=df_test, y='tiempo_espera', modelo=None, regresion=True, num_boost_round=2500, early_stopping_rounds=20, project='xgboost_PD2', name="modelo_xboost", entity='dacoleto-complutense-university-of-madrid')
monitor.evaluate()
monitor.finish()