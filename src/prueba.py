import numpy as np
import wandb
import tensorflow as tf
import tensorflow as tf
from tensorflow.keras import layers
import pandas as pd
import datetime
from sklearn.model_selection import train_test_split
from pyspark.sql import SparkSession
from pyspark.ml.regression import LinearRegression
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml import Pipeline
from pyspark.sql.functions import col
import pyspark

df = pd.read_csv("data/ex1/eventos_espera_semana_nuevo.csv")


spark = SparkSession.builder.appName("SparkWandBExample").getOrCreate()

wandb.init(
    project='pruebaPD2',
    name="modelo_2",
    entity='marbaldo-complutense-university-of-madrid', 
    config={
        'learning_rate': 10,
        'batch_size': 64,
        'epochs': 10
    }
)


# Configura el callback de W&B

"""

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

X = df.drop(columns=["ICAO", "tiempo_espera", "lat", "lon"])
y = df["tiempo_espera"]



X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)




model = tf.keras.Sequential([
    layers.Dense(64, activation='relu', input_shape=[len(X_train.keys())]),
    layers.Dense(1)
])

# Compilación del modelo
model.compile(optimizer='adam',
              loss='mse',
              metrics=['mae', 'mse'])

from wandb.integration.keras import WandbMetricsLogger
from wandb.integration.keras import WandbModelCheckpoint

wandb_metrics_logger = WandbMetricsLogger()
wandb_model_checkpoint = WandbModelCheckpoint("model2.keras")
# Entrenamiento del modelo
# Utiliza el callback de W&B durante el entrenamiento
model.fit(X_train, y_train, epochs=10, callbacks=[wandb_metrics_logger, wandb_model_checkpoint])

wandb.finish() 

"""










from pyspark.sql.functions import unix_timestamp

data = spark.read.csv("data/ex1/eventos_espera_semana_nuevo.csv", header=True, inferSchema=True)

wandb.init(
    project='pruebaPD2',
    name="modelo_spark",
    entity='marbaldo-complutense-university-of-madrid', 
    config={
        'learning_rate': 10,
        'batch_size': 64,
        'epochs': 10
    }
)
data = data.drop("ICAO", "tiempo_espera", "lat", "lon")
data = data.withColumn("fecha_despegue", unix_timestamp("fecha_despegue").cast("double"))
data = data.withColumn("ultimo_parado", unix_timestamp("ultimo_parado").cast("double"))
data = data.withColumn("despegue", unix_timestamp("despegue").cast("double"))

# Convertir columnas de tipo string a índices numéricos
indexer_aircraft_type = StringIndexer(inputCol="aircraft_type", outputCol="aircraft_type")
indexer_holding_point = StringIndexer(inputCol="holding_point", outputCol="holding_point")
indexer_runway = StringIndexer(inputCol="runway", outputCol="runway")

assembler = VectorAssembler(inputCols=data.columns, outputCol='X')
data = assembler.transform(data)

train_data, test_data = data.randomSplit([0.8, 0.2], seed=7)

# Definir el modelo de regresión lineal
lr = LinearRegression(featuresCol='X', labelCol='tiempo_espera', maxIter=wandb.config.max_iter, regParam=wandb.config.reg_param)

# Entrenar el modelo
lr_model = lr.fit(train_data)

# Evaluar el modelo en el conjunto de prueba
test_results = lr_model.evaluate(test_data)

# Registrar los resultados y las métricas en W&B
wandb.log({
    'rmse': test_results.rootMeanSquaredError,
    'r2': test_results.r2
})

# También podemos guardar el modelo entrenado si lo necesitamos
model_path = '/model_spark'
lr_model.save(model_path)

# Finalizar el experimento en W&B
wandb.finish()

# Mostrar resultados en consola
print(f"RMSE: {test_results.rootMeanSquaredError}")
print(f"R2: {test_results.r2}")