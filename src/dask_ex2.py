import dask.dataframe as dd
import pandas as pd
from dask.diagnostics import ProgressBar
import pyModeS as pms
from utils import *

def getAirbornePosition(hex):
    RAD_LAT = 40.51
    RAD_LON = -3.53
    lat, lon = pms.adsb.airborne_position_with_ref(hex, RAD_LAT, RAD_LON)
    return lat, lon

def getSurfacePosition(hex):
        RAD_LAT = 40.51
        RAD_LON = -3.53
        lat, lon = pms.adsb.position_with_ref(hex, RAD_LAT, RAD_LON)
        return lat, lon

def getSurfaceVelocity(hex):
        binary_message = pms.hex2bin(hex)
        speedValue = int(binary_message[37:44], 2)
        if speedValue == 0:
            return None  # SPEED NOT AVAILABLE
        elif speedValue == 1:
            return 0   # STOPPED (v < 0.125 kt)
        elif 2 <= speedValue < 9:
            return (speedValue - 2) * 0.125 + 0.125
        elif 9 <= speedValue < 13:
            return (speedValue - 9) * 0.25 + 1
        elif 13 <= speedValue < 39:
            return (speedValue - 13) * 0.5 + 2
        elif 39 <= speedValue < 94:
            return (speedValue - 39) * 1 + 15
        elif 94 <= speedValue < 109:
            return (speedValue - 94) * 2 + 70
        elif 109 <= speedValue < 124:
            return (speedValue - 109) * 5 + 100
        elif speedValue == 124:
            return 175  # MAX (v >= 175 kt)
        else:
            return None  # RESERVED

df = dd.read_csv("test.csv", sep=";")

df["messageHex"] = df["message"].apply(base64toHEX, meta=str)
df["DL"] = df["messageHex"].apply(getDownlink, meta=int)

# nos quedamos con las filas necesarias y validas
filtroDL = df["DL"].isin([11, 17, 18])
filtroCorrupto = df["messageHex"].map(lambda x: msgIsCorrupted(x) == False, meta=bool)
df = df[filtroDL & filtroCorrupto].reset_index()

df["ICAO"] = df["messageHex"].apply(getICAO,meta=str)
df["OnGround"] = df["messageHex"].apply(getOnGround,meta =int)
df["TC"] = df["messageHex"].apply(getTypeCode,meta =int)

def segmentar_vuelos(grupo: pd.DataFrame) -> pd.DataFrame:
    """
    Para todos los datos con mismo ICAO (grupo)
    Crea una fila por cada ventana de tiempo, de modo que
    nos quedamos con la última información conocida al final de esa ventana
    Ej. con ventana de 3 segundos
    
    Entrada:
    [t=0, v=10] <- ventana 0
    [t=1, lat=10]
    [t=2, v=20]
    [t=3, v=25] <- ventana 1
    [t=4, lon=41]
    [t=5, v=30]

    Devolveria
    [t=2, v=20, lat=10]
    [t=5, v=30, lon=41]
    """

    grupo = grupo.sort_values("ts_kafka")
    eventos = []
    ultimo_info = {
        'ts_kafka': None,
        'velocity': None,
        'lat': None,
        'lon': None,
        'icao': None,
        'ground': None,
        'direccion': None,
        'surf_vel': None,
        'surf_lat': None,
        'surf_lon': None,
    }
    umbral = 5 * 60 * 1000 # 5 minutos
    
    first = True
    prev_time = None
    airPosClass = AirbornePositionMessage()
    velClass = AirborneVelocity()
    surPosClass = SurfacePositionMessage()
    for _, row in grupo.iterrows():
        try:
            if first:
                first = False
                ultimo_info['ts_kafka'] = row['ts_kafka']

            if (int(row['ts_kafka']) - int(ultimo_info['ts_kafka']) >= umbral):
                # Guardamos último estado de la ventana terminada
                if ultimo_info['ground']:
                    ultimo_info['velocity'] = ultimo_info['surf_vel']
                    ultimo_info['lat'] = ultimo_info['surf_lat']
                    ultimo_info['lon'] = ultimo_info['surf_lon']

                del ultimo_info['surf_vel']
                del ultimo_info['surf_lat']
                del ultimo_info['surf_lon']

                ultimo_info['ts_kafka'] = prev_time
                eventos.append(ultimo_info)

                # Reseteamos estado, nueva ventana
                ultimo_info = {
                    'ts_kafka': row['ts_kafka'],

                    'velocity': None,
                    'lat': None,
                    'lon': None,
                    'icao': None,
                    'ground': None,
                    'direccion': None,
                    'surf_vel': None,
                    'surf_lat': None,
                    'surf_lon': None,
                }
            
            ultimo_info['icao'] = row['ICAO']

            typecode = row["TC"]
            if (airPosClass.match(typecode)):
                ultimo_info["lat"], ultimo_info["lon"] = getAirbornePosition(row["messageHex"])
            if (surPosClass.match(typecode)):
                ultimo_info["surf_vel"] = getSurfaceVelocity(row["messageHex"])
                ultimo_info["surf_lat"], ultimo_info["surf_lon"] = getSurfacePosition(row["messageHex"])
            elif (velClass.match(typecode)):
                ultimo_info["velocity"], _, _, _ = pms.adsb.velocity(row["messageHex"])
            elif (row["DL"] == 11):
                ultimo_info['ground'] = row["OnGround"]

            prev_time = row['ts_kafka']

        except Exception as e:
            with open("errores.log", "a") as archivo:
                archivo.write(f"Error: {str(e)}\n")

    # Añade el último estado (la ventana no termina)
    if (prev_time is not None):
        if ultimo_info['ground']:
            ultimo_info['velocity'] = ultimo_info['surf_vel']
            ultimo_info['lat'] = ultimo_info['surf_lat']
            ultimo_info['lon'] = ultimo_info['surf_lon']

        del ultimo_info['surf_vel']
        del ultimo_info['surf_lat']
        del ultimo_info['surf_lon']
        ultimo_info['ts_kafka'] = prev_time
        eventos.append(ultimo_info)

    return pd.DataFrame(eventos)


# Definimos el meta para la función de groupby.apply (para Dask)
meta = {
    "ts_kafka": int,
    "velocity": float,
    "lat": float,
    "lon": float,
    "icao": str,
    "ground": int,
    "direccion": None,
}


with ProgressBar():
    eventos = df.groupby("ICAO").apply(segmentar_vuelos, meta=meta)
    eventos.to_csv('data/ex2/preprocess_mapa.csv', index=False, single_file=True)