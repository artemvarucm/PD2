import dask.dataframe as dd
import pandas as pd
import time
import pyModeS as pms
import base64
from shapely.geometry import Point, Polygon

from dask.array import result_type
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
    eventos = []
    ultimo_parado = None
    aircraftType = None
    ultimaLat = None
    ultimaLon = None

    for _, row in grupo.iterrows():
        # Si el mensaje es de superficie y se puede decodificar la velocidad,
        # y esta es exactamente 0, se considera que el avión está parado.
        if ((row["TC"] > 0) & (row["TC"] < 5)):
            if ((row["AircraftType"] not in ["No category information", "Reserved", "ERROR"]) | (row["TC"] != 1)):
                aircraftType = row["AircraftType"]

        if pd.notna(row.get("surface_velocity")) and row["surface_velocity"] == 0:
            ultimo_parado = row["timestamp"]

        if(pd.notna(row.get("lat")) and pd.notna(row.get("lon"))):
            ultimaLat = row["lat"]
            ultimaLon = row["lon"]

        # Cuando se detecta que el avión ya está en aire (OnGround == 0)
        if ((row["OnGround"] == 0) & (row["DL"] == 11)):
            if ultimo_parado is not None:
                tiempo_despegue = row["timestamp"]
                tiempo_espera = (tiempo_despegue - ultimo_parado).total_seconds()
                eventos.append({
                    "ICAO": row["ICAO"],
                    "ultimo_parado": ultimo_parado,
                    "despegue": tiempo_despegue,
                    "tiempo_espera": tiempo_espera,
                    "aircraft_type": aircraftType,
                    "lat": ultimaLat,
                    "lon": ultimaLon,
                })
                # Reiniciamos la marca para detectar el siguiente vuelo
                ultimo_parado = None
    return pd.DataFrame(eventos)


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



df = dd.read_csv("E:/UniversidadCoding/Tercero/PD2/PD2/src/datos_semana/0.part", sep=",", parse_dates=["timestamp"])  # o el patrón que hayas definido
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

meta = {
    "ICAO": str,
    "ultimo_parado": "datetime64[ns]",
    "despegue": "datetime64[ns]",
    "tiempo_espera": float,
    "aircraft_type": str,
    "lat": "float64",
    "lon": "float64"
}

with ProgressBar():
    eventos_espera = df.groupby("ICAO").apply(segmentar_vuelos, meta=meta).compute()

eventos_espera["fecha_despegue"] = eventos_espera["despegue"].dt.date
eventos_espera["hora_despegue"] = eventos_espera["despegue"].dt.hour

eventos_espera["runway"] = eventos_espera.apply(
    lambda row: find_runway(row["lon"], row["lat"]),
    axis=1
)


estadisticas_por_dia_hora = eventos_espera.groupby(
    ["fecha_despegue", "hora_despegue"]
)["tiempo_espera"].agg(["mean", "median", "count"]).reset_index()

print("Estadísticas de tiempo de espera (en segundos) por hora de despegue:")
print(estadisticas_por_dia_hora)

with ProgressBar():
    eventos_espera.to_csv('eventos_espera_semana_nuevo', index=False)