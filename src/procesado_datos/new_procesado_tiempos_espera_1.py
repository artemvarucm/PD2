import dask.dataframe as dd
import pyModeS.decoder.bds.bds60
import pandas as pd
import numpy as np

from utils import *
from dask.diagnostics import ProgressBar

def getSurfaceVelocity(hex_str):
    binary_message = pms.hex2bin(hex_str)
    encoded_speed = int(binary_message[37:44], 2)
    if encoded_speed == 0:
        return None  # SPEED NOT AVAILABLE
    elif encoded_speed == 1:
        return 0.0    # STOPPED (v < 0.125 kt)
    elif 2 <= encoded_speed < 9:
        return (encoded_speed - 2) * 0.125 + 0.125
    elif 9 <= encoded_speed < 13:
        return (encoded_speed - 9) * 0.25 + 1
    elif 13 <= encoded_speed < 39:
        return (encoded_speed - 13) * 0.5 + 2
    elif 39 <= encoded_speed < 94:
        return (encoded_speed - 39) * 1 + 15
    elif 94 <= encoded_speed < 109:
        return (encoded_speed - 94) * 2 + 70
    elif 109 <= encoded_speed < 124:
        return (encoded_speed - 109) * 5 + 100
    elif encoded_speed == 124:
        return 175
    else:
        return None

def getVelocity(hex):
    speed, angle, vertical_rate, speed_type=pms.decoder.adsb.velocity(hex, source=False)
    return speed, angle, vertical_rate, speed_type

def getAltitud(hex):
    altitud = pms.decoder.adsb.altitud(hex)
    return altitud

def getSurfacePosition(hex):
    RAD_LAT = 40.51
    RAD_LON = -3.53
    lat, lon = pms.adsb.position_with_ref(hex, RAD_LAT, RAD_LON)
    return lat, lon


def compute_surface_velocity(row):
    if 5 <= row["TC"] <= 8:
        return getSurfaceVelocity(row["messageHex"])
    else:
        return None

def compute_surface_position(row):
    if 5 <= row["TC"] <= 8:
        return getSurfacePosition(row["messageHex"])
    else:
        return None
    
def filtrar_heading(grupo: pd.DataFrame) -> pd.DataFrame:
    filtro14 = grupo["heading"].between(138,142)
    filtro36 = (grupo["heading"] >= 358) | (grupo["heading"] <= 2)

    aux = grupo[filtro14 | filtro36]

    grupo = grupo.sort_values(by="timestamp")

    if not aux.empty:
        return grupo
    else:
        return grupo.iloc[0:0]


# Función que procesa todos los tipos de mensajes de una vez
def procesar_mensajes(partition):
    # Crear todas las columnas con valores NaN por defecto
    partition['OnGround'] = np.nan
    partition['TC'] = np.nan
    partition['AircraftType'] = None

    # Procesar mensajes tipo 17 y 18
    mask_17_18 = (partition['DL'] == 17) | (partition['DL'] == 18)
    if mask_17_18.any():
        partition.loc[mask_17_18, 'OnGround'] = partition.loc[mask_17_18, 'messageHex'].apply(getOnGround)
        partition.loc[mask_17_18, 'TC'] = partition.loc[mask_17_18, 'messageHex'].apply(getTypeCode)
        airIdMsg = AircraftIdentificationMessage()
        partition.loc[mask_17_18, 'AircraftType'] = partition.loc[mask_17_18, 'messageHex'].apply(
            airIdMsg.getAircraftType)

        # Añadir velocidad y posición en superficie
    partition["surface_velocity"] = partition.apply(
        compute_surface_velocity, axis=1, meta=("surface_velocity", float)
    )

    partition["altitud"] = partition.apply(
        getAltitud, axis=1, meta=("altitud", float)
    )

    partition["surface_position"] = partition.apply(
        compute_surface_position, axis=1, meta=("surface_position", object)
    )

    partition["velocity_data"] = partition.apply(
        getVelocity, axis=1, meta=("velocity_data", object)
    )

    partition["surface_position"] = partition["surface_position"].apply(
        lambda x: (None, None) if x is None else x,
        meta=("surface_position", object)
    )

    partition["lat"] = partition["surface_position"].apply(lambda x: x[0], meta=("lat", "float64"))
    partition["lon"] = partition["surface_position"].apply(lambda x: x[1], meta=("lon", "float64"))

    partition["velocity"] = partition["velocity_data"].apply(lambda x: x[0], meta=("velocity", "float64"))
    partition["heading"] = partition["velocity_data"].apply(lambda x: x[1], meta=("heading", "float64"))
    partition["vertical_rate"] = partition["velocity_data"].apply(lambda x: x[2], meta=("vertical_rate", "float64"))
    partition["speed_type"] = partition["velocity_data"].apply(lambda x: x[3], meta=("speed_type", "float64"))

    return partition


# Cargar y preparar datos
df = dd.read_csv("archivo_dividido_1.csv", sep=";")
df = df.drop(columns="Unnamed: 2")

df["messageHex"] = df["message"].apply(base64toHEX, meta=str)
df["DL"] = df["messageHex"].apply(getDownlink, meta=int)

filtroDL = df["DL"].isin([17, 18])
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
        'surface_velocity': 'float64',
        'lat': 'float64',
        'lon': 'float64',
        'heading': 'float64',
        'vertical_rate': 'float64',
        'altitud': 'float64',
        'speed_type': str,
        'velocity': 'float64'
    }
)

meta2 = {
    'DL': 'int',
    'ICAO': str,
    'timestamp': 'datetime64[ns]',
    'OnGround': 'float64',  
    'TC': 'float64',
    'AircraftType': 'object',
    'surface_velocity': 'float64',
    'lat': 'float64',
    'lon': 'float64',
    'heading': 'float64',
    'vertical_rate': 'float64',
    'altitud': 'float64',
    'speed_type': str,
    'velocity': 'float64'
    
}

with ProgressBar():
    df_headings = df.groupby("ICAO").apply(filtrar_heading, meta = meta2)
    df_headings = df_headings.reset_index(drop=True)

with ProgressBar():
    # Guardar el resultado
    df.to_csv('datos_prueba.csv', index=False, single_file=True)

