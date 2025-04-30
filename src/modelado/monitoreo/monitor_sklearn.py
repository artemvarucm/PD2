from monitor_general import MonitorGeneral
import pandas as pd
import wandb
from sklearn.metrics import root_mean_squared_error, mean_squared_error, mean_absolute_error, r2_score, f1_score, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression


class MonitorSklearn(MonitorGeneral):
    METRICAS_REGRESION = ['rmse', 'mse', 'mae', 'r2']
    METRICAS_CLASIFICACION = ['accuracy', 'f1']

    def __init__(self, modelo, train, test, y, regresion=True, project='sklearn_PD2', name="modelo_sklearn", entity='dacoleto-complutense-university-of-madrid'):
        """
        Inicializa el monitor para modelos de scikit-learn
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

        wandb.log({"metricas": tabla_metricas})
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

        X = self.train.drop(columns=[self.y])
        y = self.train[self.y]

        X_test = self.test.drop(columns=[self.y])
        y_test = self.test[self.y]

        self.modelo.fit(X, y)

        y_pred = self.modelo.predict(X_test)

        self.visualizeRealvsPrediccion(real_values=y_test, predictions=y_pred, name=name)
        
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
        
        self.saveData(path=f"./src/modelado/monitoreo/datasets/sklearn/{self.name}", train=self.train, test=self.test)
        self.saveModel(path=f"./src/modelado/monitoreo/modelos/sklearn/{self.name}.pkl")

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor

# Cargar datos
df = pd.read_parquet("data/Train/train_final.parquet")
df_meteo = pd.read_csv("./data/datos_meteorologicos.csv", delimiter=",")

# Conversión de fechas y tiempos
df["llegada_punto"]  = pd.to_datetime(df["llegada_punto"])
df["salida_punto"]   = pd.to_datetime(df["salida_punto"])
df["despegue"]       = pd.to_datetime(df["despegue"])
df["timestamp"]      = pd.to_datetime(df["timestamp"])
df["fecha_despegue"] = pd.to_datetime(df["fecha_despegue"])
df["Fecha"] = df["timestamp"].dt.date
df["Hora"] = df["timestamp"].dt.hour

# Conversión de columnas numéricas del meteo
cols_numericas = [
    "Precipitación", "Temperatura", "Humedad", "Viento", "Viento máximo",
    "Temperatura mínima", "Temperatura máxima"
]
for col in cols_numericas:
    df_meteo[col] = df_meteo[col].str.replace(",", ".").astype(float)

df_meteo["Fecha"] = pd.to_datetime(df_meteo["Fecha"]).dt.date
df_meteo["Hora"] = pd.to_datetime(df_meteo["Hora"], format="%H:%M").dt.hour

# Merge de meteorología
df_merged = df.merge(df_meteo, how="left", on=["Fecha", "Hora"])
df_filtrado = df_merged[df_merged["tiempo_espera"] <= 500].copy()

print(f"Registros antes de filtrar: {len(df_merged)}")
print(f"Registros después de filtrar: {len(df_filtrado)}")

# Features
df_modelo = df_filtrado.drop(columns=[
    "ICAO", "llegada_punto", "salida_punto", "salida_lon", "salida_lat", "despegue",
    "runway", "fecha_despegue", "hora_despegue", "timestamp", "holding_point"
])
X = df_modelo.drop(columns=["tiempo_espera"])
y = df_modelo["tiempo_espera"]

# Columnas
num_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
cat_cols = X.select_dtypes(include=["object", "bool"]).columns.tolist()

# Preprocesamiento manual
preprocessor = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
])

X_t = preprocessor.fit_transform(X)
cat_feats = preprocessor.named_transformers_["cat"].get_feature_names_out(cat_cols).tolist()
all_feats = num_cols + cat_feats

df_preprocesado = pd.DataFrame(X_t, columns=all_feats, index=X.index)
df_preprocesado["tiempo_espera"] = y



# 1) Cargo test_final
df_test = pd.read_parquet("./data/Train/test_final.parquet")

# 3) Creo Fecha y Hora para el merge con meteorología
df["Fecha"] = df["timestamp"].dt.date
df["Hora"]  = df["timestamp"].dt.hour

# 4) Merge con df_meteo (ya procesado antes)
df_test_merged = df.merge(df_meteo, on=["Fecha","Hora"], how="left")

# 5) Filtrar outliers igual que en train
df_test_filtrado = df_test_merged[df_test_merged["tiempo_espera"] <= 500].copy()

# 6) Preparo X_test_final e y_test_final
drop_cols = [
    "ICAO","llegada_punto","salida_punto","despegue",
    "runway","fecha_despegue","hora_despegue",
    "timestamp","holding_point"
]
X_test_final = df_test_filtrado.drop(columns=drop_cols + ["tiempo_espera"])
y_test_final = df_test_filtrado["tiempo_espera"]

# 7) Predicción y MAE
from sklearn.metrics import mean_absolute_error

# 7a) Transformar X_test_final con el preprocessor entrenado
X_test_t = preprocessor.transform(X_test_final)

df_preprocesado_test = pd.DataFrame(X_test_t, columns=all_feats, index=X_test_final.index)
df_preprocesado_test["tiempo_espera"] = y_test_final

rf = RandomForestRegressor(n_estimators=3, random_state=42)

monitor_sk = MonitorSklearn(modelo=rf,train=df_preprocesado,test=df_preprocesado_test, y="tiempo_espera",regresion=True,project='sklearn_PD2',name="modelo_3_sin_out",entity='dacoleto-complutense-university-of-madrid')

monitor_sk.evaluate()
monitor_sk.finish()