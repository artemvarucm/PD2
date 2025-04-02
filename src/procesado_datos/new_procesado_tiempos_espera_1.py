import dask.dataframe as dd
import pyModeS.decoder.bds.bds60
import pandas as pd
import numpy as np

from utils import *
from dask.diagnostics import ProgressBar

# Función que procesa todos los tipos de mensajes de una vez
def procesar_mensajes(partition):
    # Crear todas las columnas con valores NaN por defecto
    partition['OnGround'] = np.nan
    partition['TC'] = np.nan
    partition['AircraftType'] = None
    partition['heading'] = np.nan
    partition['vertical_rate'] = np.nan

    # Procesar mensajes tipo 17 y 18
    mask_17_18 = (partition['DL'] == 17) | (partition['DL'] == 18)
    if mask_17_18.any():
        partition.loc[mask_17_18, 'OnGround'] = partition.loc[mask_17_18, 'messageHex'].apply(getOnGround)
        partition.loc[mask_17_18, 'TC'] = partition.loc[mask_17_18, 'messageHex'].apply(getTypeCode)
        airIdMsg = AircraftIdentificationMessage()
        partition.loc[mask_17_18, 'AircraftType'] = partition.loc[mask_17_18, 'messageHex'].apply(
            airIdMsg.getAircraftType)

    # Procesar mensajes tipo 20 y 21
    mask_20_21 = (partition['DL'] == 20) | (partition['DL'] == 21)
    if mask_20_21.any():
        partition.loc[mask_20_21, 'heading'] = partition.loc[mask_20_21, 'messageHex'].apply(
            pyModeS.decoder.bds.bds60.hdg60)
        partition.loc[mask_20_21, 'vertical_rate'] = partition.loc[mask_20_21, 'messageHex'].apply(
            pyModeS.decoder.bds.bds60.vr60ins)

    return partition


# Cargar y preparar datos
df = dd.read_csv("archivo_dividido_1.csv", sep=";")
df = df.drop(columns="Unnamed: 2")

df["messageHex"] = df["message"].apply(base64toHEX, meta=str)
df["DL"] = df["messageHex"].apply(getDownlink, meta=int)

filtroDL = df["DL"].isin([17, 18, 20, 21])
df = df[filtroDL].reset_index()

df["ICAO"] = df["messageHex"].apply(getICAO, meta=str)
df['timestamp'] = dd.to_datetime(df['ts_kafka'], unit='ms')

# Aplicar la función de procesamiento con los metadatos adecuados
df = df.map_partitions(
    procesar_mensajes,
    meta={
        **df._meta.dtypes.to_dict(),
        'OnGround': 'float64',  # Usamos float64 para poder tener NaN
        'TC': 'float64',
        'AircraftType': 'object',
        'heading': 'float64',
        'vertical_rate': 'float64'
    }
)

with ProgressBar():
    # Guardar el resultado
    df.to_csv('datos_prueba.csv', index=False, single_file=True)

