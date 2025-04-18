import os
from pathlib import Path

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

# Función que procesa todos los tipos de mensajes de una vez
def procesar_mensajes(partition):
    # Crear todas las columnas con valores NaN por defecto
    partition['OnGround'] = np.nan
    partition['TC'] = np.nan
    partition['AircraftType'] = None
    partition['heading'] = np.nan
    partition['vertical_rate'] = np.nan

    # Procesar mensajes tipo 11, 17 y 18
    mask_11_17_18 = partition["DL"].isin([11, 17, 18])
    if mask_11_17_18.any():
        partition.loc[mask_11_17_18, 'OnGround'] = partition.loc[mask_11_17_18, 'messageHex'].apply(getOnGround)
        partition.loc[mask_11_17_18, 'TC'] = partition.loc[mask_11_17_18, 'messageHex'].apply(getTypeCode)
        airIdMsg = AircraftIdentificationMessage()
        partition.loc[mask_11_17_18, 'AircraftType'] = partition.loc[mask_11_17_18, 'messageHex'].apply(
            airIdMsg.getAircraftType)

    # Procesar mensajes tipo 20 y 21
    mask_20_21 = (partition['DL'] == 20) | (partition['DL'] == 21)
    if mask_20_21.any():
        partition.loc[mask_20_21, 'heading'] = partition.loc[mask_20_21, 'messageHex'].apply(
            pyModeS.decoder.bds.bds60.hdg60)
        partition.loc[mask_20_21, 'vertical_rate'] = partition.loc[mask_20_21, 'messageHex'].apply(
            pyModeS.decoder.bds.bds60.vr60ins)

    return partition


import dask.dataframe as dd
import pandas as pd
import time
import pyModeS as pms
import base64

from pyproj import Transformer
from shapely.geometry import Point, Polygon

from dask.diagnostics import ProgressBar
import geopandas as gpd  # para leer el geojson


rwy_polygon_18R_36L = Polygon([
    (-3.582, 40.492383), (-3.5695, 40.492383), (-3.5695, 40.537929), (-3.582, 40.537929)
])

rwy_polygon_18L_36R = Polygon([
    (-3.564441, 40.499172), (-3.549, 40.499172), (-3.549, 40.537472), (-3.564441, 40.537472)
])

rwy_polygon_14L_32R = Polygon([
    (-3.531683, 40.464310), (-3.524645, 40.468620), (-3.556317, 40.498519), (-3.564652, 40.495647)
])

rwy_polygon_14R_32L = Polygon([
    (-3.547648, 40.450661), (-3.539580, 40.454710), (-3.575714, 40.488141), (-3.582924, 40.484224)
])

meta = {
    "ICAO": str,
    "llegada_punto": "datetime64[ns]",
    "salida_punto": "datetime64[ns]",
    "despegue": "datetime64[ns]",
    "tiempo_espera": float,
    "aircraft_type": str,
    "llegada_lon": "float64",
    "llegada_lat": "float64",
    "salida_lon": "float64",
    "salida_lat": "float64",
    "holding_point": str,
    "parado": bool,
    "runway": str
}


# Cargar el geojson de holding points (en CRS WGS84)
holding_points = gpd.read_file("../../data/geojson/holding_points.geojson")

# Reproyectar a un CRS métrico (por ejemplo, UTM 30N; usa el EPSG adecuado para tu zona)
holding_points_utm = holding_points.to_crs(epsg=32630)

# Crear un buffer de 50 metros alrededor de cada holding point
holding_points_utm['buffer'] = holding_points_utm.buffer(50)

# Crear un transformer para convertir puntos de WGS84 (EPSG:4326) a UTM (EPSG:32630)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32630", always_xy=True)


def transform_point(point):
    """Transforma un punto de WGS84 a UTM."""
    x, y = transformer.transform(point.x, point.y)
    return Point(x, y)


def find_holding_point_with_buffer(lon, lat):
    """
    Dado un par de coordenadas (en WGS84), transforma el punto a UTM y verifica
    si se encuentra dentro de alguno de los buffers de los holding points.
    Devuelve el DESIGNATOR (u otro identificador) si coincide o None.
    """
    if (lon is None or lat is None):
        return None

    point = Point(lon, lat)
    point_utm = transform_point(point)
    for idx, row in holding_points_utm.iterrows():
        if row['buffer'].contains(point_utm):
            return row.get("DESIGNATOR", f"holding_point_{idx}")

    return None


def find_runway(lon, lat):
    point = Point(lon, lat)
    if rwy_polygon_18R_36L.contains(point):
        return "18R/36L"
    elif rwy_polygon_18L_36R.contains(point):
        return "18L/36R"
    elif rwy_polygon_14L_32R.contains(point):
        return "14L/32R"
    elif rwy_polygon_14R_32L.contains(point):
        return "14R/32L"
    else:
        return None


# 3. Función para segmentar vuelos por grupo (por cada ICAO)
def segmentar_vuelos(grupo: pd.DataFrame) -> pd.DataFrame:
    """
    Para un grupo de mensajes (un mismo ICAO) ordenados cronológicamente,
    se detecta la transición: se guarda el último instante en que el avión está en tierra
    (OnGround == 1) y, en cuanto se detecta el primer mensaje con OnGround == 0, se calcula el tiempo
    de espera (diferencia de timestamps).
    Se reinicia la marca de tierra para detectar ciclos sucesivos.
    """
    grupo = grupo.sort_values("timestamp")

    eventos = []  # tiene los puntos de espera de TODOS los despegues
    eventos_provisional = []  # tiene los puntos de espera de 1 despegue
    visited_hp = set()

    # Variables para seguimiento de estado
    ultimaLat, ultimaLon = None, None
    aircraftType = None

    for _, row in grupo.iterrows():
        # Si el mensaje es de superficie y se puede decodificar la velocidad,
        # y esta es exactamente 0, se considera que el avión está parado.
        if (aircraftType is None and
                pd.notna(row["AircraftType"]) and
                row["AircraftType"] not in ["No category information", "Reserved", "ERROR"]
        ):
            # se queda con el primer tipo emitido por el avion (si emite un mensaje con otro tipo se descarta)
            aircraftType = row["AircraftType"]

        if pd.notna(row.get("surface_velocity")):
            parado = row["surface_velocity"] == 0
            hp = find_holding_point_with_buffer(row["lon"], row["lat"])
            if (hp is not None and hp not in visited_hp):
                # si es la primera vez que pasa por este punto
                visited_hp.add(hp)
                eventos_provisional.append({
                    "ICAO": row["ICAO"],
                    "llegada_punto": row["timestamp"],
                    "salida_punto": None,
                    "despegue": None,
                    "tiempo_espera": None,
                    "aircraft_type": aircraftType,
                    "llegada_lon": row["lon"],
                    "llegada_lat": row["lat"],
                    "salida_lon": None,
                    "salida_lat": None,
                    "holding_point": hp,
                    "parado": parado
                })
            if len(eventos_provisional) > 0:
                if (
                        (hp is None or hp != eventos_provisional[-1]["holding_point"])
                        and eventos_provisional[-1]["salida_punto"] is None
                ):
                    # si se ha movido a otro punto o se ha salido de este
                    eventos_provisional[-1]["salida_punto"] = row["timestamp"]
                    eventos_provisional[-1]["salida_lon"] = row["lon"]
                    eventos_provisional[-1]["salida_lat"] = row["lat"]
                elif (hp == eventos_provisional[-1]["holding_point"]):
                    # se ha parado en el punto de espera
                    eventos_provisional[-1]["parado"] = True if (parado or eventos_provisional[-1]["parado"]) else False

        if (pd.notna(row.get("lat")) and pd.notna(row.get("lon"))):
            ultimaLat = row["lat"]
            ultimaLon = row["lon"]

        # Cuando se detecta que el avión ya está en aire (OnGround == 0)
        if (row["OnGround"] == 0 and row["DL"] == 11):
            if bool(visited_hp):  # si ha visitado algun punto
                tiempo_despegue = row["timestamp"]

                # posicion final al despegar
                if eventos_provisional[-1]["salida_punto"] is None:
                    eventos_provisional[-1]["salida_punto"] = row["timestamp"]

                if eventos_provisional[-1]["salida_lat"] is None or eventos_provisional[-1]["salida_lon"] is None:
                    eventos_provisional[-1]["salida_lat"] = ultimaLat
                    eventos_provisional[-1]["salida_lon"] = ultimaLon

                runway = find_runway(ultimaLon, ultimaLat)  # pista de despegue
                for evento in eventos_provisional:
                    evento["despegue"] = tiempo_despegue
                    evento["tiempo_espera"] = (tiempo_despegue - evento["llegada_punto"]).total_seconds()
                    evento["runway"] = runway
                    # evento["lat"] = ultimaLat
                    # evento["lon"] = ultimaLon
                    eventos.append(evento)

                # puede tener varios despegues, seguimos
                ultimaLat, ultimaLon = None, None
                aircraftType = None
                visited_hp.clear()
                eventos_provisional.clear()

    return pd.DataFrame(eventos)




# Sube desde preprocesadoJunto.py hasta "Universidad/"
universidad_path = Path(__file__).resolve().parents[5]
salida_path = Path(__file__).resolve().parents[2]

# Llega a "datapd2/Raw"
base_raw_path = universidad_path / "datapd2" / "Raw"
base_output_path = salida_path / "data" / "Preprocessed"

for month in [1]:
    for day in range(1, 32):
        dfs_del_dia = []

        for hour in range(24):
            path = base_raw_path / f"{month:02d}" / f"{day:02d}" / f"{hour:02d}"
            print(f"Revisando: {path}")

            if os.path.exists(path):
                # Cargar todos los CSVs del directorio
                archivos = list(path.glob("*.csv"))
                print(f"  Archivos encontrados: {[f.name for f in archivos]}")
                if archivos:
                    df = dd.read_csv(archivos, sep=";")
                    dfs_del_dia.append(df)

        if dfs_del_dia:
            df = dd.concat(dfs_del_dia)
            df = df.drop(columns="Unnamed: 2", errors="ignore")

            df["messageHex"] = df["message"].apply(base64toHEX, meta=str)
            df["DL"] = df["messageHex"].apply(getDownlink, meta=int)

            filtroDL = df["DL"].isin([11, 17, 18, 20, 21])
            df = df[filtroDL].reset_index()

            df["ICAO"] = df["messageHex"].apply(getICAO, meta=str)
            df['timestamp'] = dd.to_datetime(df['ts_kafka'], unit='ms')

            df = df.map_partitions(
                procesar_mensajes,
                meta={
                    **df._meta.dtypes.to_dict(),
                    'OnGround': 'float64',
                    'TC': 'float64',
                    'AircraftType': 'object',
                    'heading': 'float64',
                    'vertical_rate': 'float64'
                }
            )

            df["surface_velocity"] = df.apply(
                compute_surface_velocity, axis=1, meta=("surface_velocity", float)
            )
            df["surface_position"] = df.apply(
                compute_surface_position,
                axis=1,
                meta=("surface_position", object)
            )

            df["surface_position"] = df["surface_position"].apply(
                lambda x: (None, None) if x is None else x,
                meta=("surface_position", object)
            )

            df["lat"] = df["surface_position"].apply(lambda x: x[0], meta=("lat", "float64"))
            df["lon"] = df["surface_position"].apply(lambda x: x[1], meta=("lon", "float64"))

            if df is not None:
                eventos_espera = df.groupby("ICAO").apply(segmentar_vuelos, meta=meta)

                eventos_espera["fecha_despegue"] = eventos_espera["despegue"].dt.date
                eventos_espera["hora_despegue"] = eventos_espera["despegue"].dt.hour

                with ProgressBar():
                    eventos_espera = eventos_espera.compute()

                pathFinal = base_output_path / f"{month:02d}" / f"{day:02d}"
                os.makedirs(pathFinal, exist_ok=True)

                nombre_archivo = f"{day}-{month}"

                eventos_espera.to_parquet(pathFinal / nombre_archivo)
