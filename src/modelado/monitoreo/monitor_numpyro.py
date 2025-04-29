import wandb
from monitor_general import MonitorGeneral
import numpy as np
from sklearn.model_selection import train_test_split
import jax.numpy as jnp
from jax import random
from numpyro.infer import MCMC, NUTS, Predictive

class MonitorNumpyro(MonitorGeneral):
    def __init__(self, modelo_numpyro, train, test, y, num_samples=1000, num_warmup=500, project='numpyro_project', name='modelo_numpyro', entity='tu_entidad'):
        """
        Inicializa el monitor para un modelo NumPyro.
        :param modelo_numpyro: función que define el modelo en NumPyro
        :param train: DataFrame de entrenamiento
        :param test: DataFrame de test
        :param y: Variable objetivo
        :param num_samples: Número de muestras para MCMC
        :param num_warmup: Número de pasos de calentamiento
        """
        self.modelo_numpyro = modelo_numpyro
        self.num_samples = num_samples
        self.num_warmup = num_warmup
        super().__init__(modelo=None, train=train, test=test, y=y, project=project, name=name, entity=entity)

    def visualizeMetrics(self, resultados_metricas, metricas, groupby=None, name="metricas"):
        """
        Visualiza las métricas en W&B.
        :param resultados_metricas: Resultados de las métricas
        :param metricas: Métricas a visualizar  
        :param train: True si la tabla es para métricas de entrenamiento, False si es para métricas de test
        :param groupby: Columna por la que agrupar los resultados (None si no se quiere agrupar)
        :param name: Nombre de la visualización de métricas
        """                   
        tabla_metricas = self.buildTableMetrics(resultados_metricas, metricas=metricas, groupby=groupby, name=name)
        
        if groupby is not None: 
            self.buildGraph(tabla_metricas=tabla_metricas, groupby=groupby, metricas=metricas, name=name)

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

    def evaluate(self, groupby=None, name=None):
        """
        Ejecuta MCMC y evalúa el modelo.
        """
        if name is None:
            name = self.name

        X_train = self.train.drop(columns=[self.y]).values
        y_train = self.train[self.y].values

        rng_key = random.PRNGKey(0)
        kernel = NUTS(self.modelo_numpyro)
        mcmc = MCMC(kernel, num_warmup=self.num_warmup, num_samples=self.num_samples)
        mcmc.run(rng_key, X=X_train, y=y_train)
        mcmc.print_summary()

        self.samples = mcmc.get_samples()

        X_test = self.test.drop(columns=[self.y]).values
        y_test = self.test[self.y].values

        predictive = Predictive(self.modelo_numpyro, posterior_samples=self.samples)
        predictions = predictive(random.PRNGKey(1), X=X_test)['y'].mean(axis=0)

        self.visualizeRealvsPrediccion(real_values=y_test, predictions=predictions, name=name)

        mae = np.mean(np.abs(y_test - predictions))
        mse = np.mean((y_test - predictions)**2)

        resultados_test = {'mae': mae, 'mse': mse}
        self.visualizeMetrics(resultados_metricas=resultados_test, metricas=['mae', 'mse'], groupby=None, name=name)

        if groupby is not None:
            X_test_df = self.test.drop(columns=[self.y])
            grupos = X_test_df.groupby(groupby)
            resultados_por_grupo = {}
            for valor, df_grupo in grupos:
                idx = df_grupo.index
                pred_grupo = predictions[idx]
                real_grupo = y_test[idx]
                resultados_por_grupo[valor] = {
                    'mae': np.mean(np.abs(real_grupo - pred_grupo)),
                    'mse': np.mean((real_grupo - pred_grupo)**2)
                }
            self.visualizeMetrics(resultados_metricas=resultados_por_grupo, metricas=['mae', 'mse'], groupby=groupby, name=name)



#import dask.dataframe as dd
import pandas as pd
from sklearn.preprocessing import StandardScaler,OneHotEncoder
df = pd.read_parquet("./data/Train/train_final.parquet")
# df = pd.read_parquet("../../../data/Train/datos_holding_with_runway.parquet")

df

import pandas as pd
import numpy as np

import pandas as pd
import numpy as np

def procesar_datos(df):
    df = df.copy()

    # --- Timestamps ---
    df["fecha_despegue"] = pd.to_datetime(df["fecha_despegue"], errors="coerce")

    # # Hora en segundos desde medianoche
    # df["segundos_llegada"] = df["timestamp"].dt.hour * 3600 + df["timestamp"].dt.minute * 60 + df["timestamp"].dt.second

    # Día de la semana (0=lunes, 6=domingo)
    df["dia_semana"] = df["fecha_despegue"].dt.weekday

    # Codificar si es fin de semana
    #df["es_finde"] = df["dia_semana"] >= 5

    # --- Categóricas como one-hot ---
    df = pd.get_dummies(df, columns=["aircraft_type", "holding_point"], drop_first=True)

    # --- Booleanas ---
    #df["parado"] = df["parado"].astype(int)
    #df["es_finde"] = df["es_finde"].astype(int)

    # --- Variables finales ---
    columnas_finales = ["tiempo_esperado", "dia_semana", "hora_despegue"] + \
                       [col for col in df.columns if col.startswith("aircraft_type_") or col.startswith("holding_point_")]

    x = df[columnas_finales].values.astype(np.float32)
    y = df["tiempo_espera"].values.astype(np.float32)

    umbral = 1000  # segundos
    mask = y < umbral

    x = x[mask]
    y = y[mask]

    mask = y > 0
    x = x[mask]
    y = y[mask]

    return x, y, columnas_finales

x, y, columnas_finales = procesar_datos(df)
from sklearn.model_selection import train_test_split

x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42
)

print(x_train.shape)
print(len(columnas_finales))

x_train = pd.DataFrame(x_train, columns=columnas_finales)
x_test = pd.DataFrame(x_test, columns=columnas_finales)

x_train["tiempo_espera"] = y_train
x_test["tiempo_espera"] = y_test

import numpyro
import numpyro.distributions as dist
import jax
import jax.numpy as jnp

def modelo_regresion(x, y=None):
    n_features = x.shape[1]

    # Priores para los coeficientes y bias
    beta = numpyro.sample("beta", dist.Normal(0, 1).expand([n_features]))
    intercept = numpyro.sample("intercept", dist.Normal(0, 5))
    sigma = numpyro.sample("sigma", dist.Exponential(1.0))  # escala del LogNormal

    # Predicción media (log del tiempo esperado)
    mu = intercept + jnp.dot(x, beta)

    # Tiempo de espera ~ LogNormal(mu, sigma)
    numpyro.sample("obs", dist.LogNormal(mu, sigma), obs=y)


monitor_numpyro = MonitorNumpyro(modelo_numpyro=modelo_regresion, train=pd.DataFrame(x_train, columnas_finales),test=pd.DataFrame(x_test, columns=["tiempo_espera"]),
    y="tiempo_espera",
    num_samples=1000,
    num_warmup=500,
    project='numpyro_project',
    name='modelo_numpyro',
    entity='tu_entidad'
)
monitor_numpyro.evaluate(name="modelo_1")
monitor_numpyro.finish()