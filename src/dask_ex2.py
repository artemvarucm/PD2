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

df = dd.read_csv("202412010000_202412072359.csv", sep=";")

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
    ultimo_info = {'ts_kafka': None, 'velocity': None, 'lat': None, 'lon': None, 'icao': None, 'ground': None}
    umbral = 5 * 60 * 1000 # 5 minutos
    
    first = True
    prev_time = None
    for _, row in grupo.iterrows():
        try:
            if first:
                first = False
                ultimo_info['ts_kafka'] = row['ts_kafka']

            if (row['ts_kafka'] - ultimo_info['ts_kafka'] >= umbral):
                # Guardamos último estado de la ventana terminada
                ultimo_info['ts_kafka'] = prev_time
                eventos.append(ultimo_info)

                # Reseteamos estado, nueva ventana
                ts = ultimo_info['ts_kafka']
                ultimo_info = {'ts_kafka': ts, 'velocity': None, 'lat': None, 'lon': None, 'icao': None, 'ground': None}        
            
            ultimo_info['icao'] = row['ICAO']

            typecode = row["TC"]
            if ((typecode >= 9 and typecode <= 18) or (typecode >= 20 and typecode <= 22)):
                ultimo_info["lat"], ultimo_info["lon"] = getAirbornePosition(row["messageHex"])
            elif (typecode == 19):
                ultimo_info["velocity"], _, _, _ = pms.adsb.velocity(row["messageHex"])
            elif (row["DL"] == 11):
                ultimo_info['ground'] = row["OnGround"]

        except Exception as e:
            with open("errores.log", "a") as archivo:
                archivo.write(f"Error: {str(e)}\n")

    # Añade el último estado (la ventana no termina)
    if (prev_time is not None):
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
    "ground": int
}


with ProgressBar():
    eventos = df.groupby("ICAO").apply(segmentar_vuelos, meta=meta)
    eventos.to_csv('data/ex2/preprocess_mapa.csv', index=False, single_file=True)