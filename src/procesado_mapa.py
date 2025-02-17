import dask.dataframe as dd
import pandas as pd
from dask.diagnostics import ProgressBar
import pyModeS as pms
from utils import *
import math
import logging

def getAirbornePosition(hex):
    """Devuelve latitud y longitud (usar cuando está en AIRE)"""
    RAD_LAT = 40.51
    RAD_LON = -3.53
    lat, lon = pms.adsb.airborne_position_with_ref(hex, RAD_LAT, RAD_LON)
    return lat, lon

def getAirborneAltitude(hex):
    """Devuelve la altura en pies"""
    return pms.adsb.altitude(hex)

def getSurfacePosition(hex):
        """Devuelve latitud y longitud (usar cuando está en TIERRA)"""
        RAD_LAT = 40.51
        RAD_LON = -3.53
        lat, lon = pms.adsb.position_with_ref(hex, RAD_LAT, RAD_LON)
        return lat, lon

def getSurfaceVelocity(hex):
        """Devuelve la velocidad en nudos, cuando está en TIERRA"""
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

def dotproduct(v1, v2):
  return sum((a*b) for a, b in zip(v1, v2))

def length(v):
  return math.sqrt(dotproduct(v, v))

def angle(v1, v2):
  return math.acos(dotproduct(v1, v2) / (10e-6 + (length(v1) * length(v2))))

def calcularDireccion(lat1, lon1, lat2, lon2):
    """Angulo con el vector que representa el ESTE (en radianes)"""
    if lat1 is None or lat2 is None or lon1 is None or lon2 is None:
        return None

    vectorCentrado = [lon2 - lon1, lat2 - lat1]
    vectorEste = [1, 0]
    return angle(vectorCentrado, vectorEste)


df = dd.read_csv("202412010000_202412072359.csv", sep=";")

df["messageHex"] = df["message"].apply(base64toHEX, meta=str)
df["DL"] = df["messageHex"].apply(getDownlink, meta=int)

# nos quedamos con las filas necesarias y validas
filtroDL = df["DL"].isin([11, 17, 18])
filtroCorrupto = df["messageHex"].map(lambda x: msgIsCorrupted(x) == False, meta=bool)
df = df[filtroDL & filtroCorrupto].reset_index()


df["ICAO"] = df["messageHex"].apply(getICAO,meta=str)
df["TC"] = df["messageHex"].apply(getTypeCode,meta =int)

def clean_row(full_row: dict, eventos: list):
    """Prepara la fila para insertar en el dataframe limpio"""
    if full_row['ground']:
        # CUANDO ESTA EN TIERRA PUEDE NO EMITIR EL MENSAJE SURFACE POSITION,
        # QUE ES EXACTAMENTE LO QUE PASA Y NOS SALEN MUY POCAS FILAS CON GROUND = 1
        if full_row['surf_vel'] is not None:
            full_row['velocity'] = full_row['surf_vel']
        if full_row['surf_lat'] is not None and full_row['surf_lon'] is not None:
            full_row['lat'] = full_row['surf_lat']
            full_row['lon'] = full_row['surf_lon']

    del full_row['surf_vel']
    del full_row['surf_lat']
    del full_row['surf_lon']

    if len(eventos) > 0:
        direccion = calcularDireccion(eventos[-1]['lat'], eventos[-1]['lon'], full_row['lat'], full_row['lon'])
        if len(eventos) > 1: # para mayor precision
            # hacemos la media de la direccion respecto penúltimo y dirección respecto el antepenúltimo
            direccion_antepenultimo = calcularDireccion(eventos[-2]['lat'], eventos[-2]['lon'], full_row['lat'], full_row['lon'])
            if direccion is None:
                direccion = direccion_antepenultimo
            elif direccion_antepenultimo is not None:
                direccion = (direccion_antepenultimo + direccion) / 2
        
        full_row['direccion'] = direccion

    return full_row


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
        'alt_feet': None,
        'callsign': None,
        'vortex': None,
    }
    umbral = 5 * 60 * 1000 # 5 minutos
    
    first = True
    prev_time = None
    airPosClass = AirbornePositionMessage()
    velClass = AirborneVelocity()
    surPosClass = SurfacePositionMessage()
    identifyClass = AircraftIdentificationMessage()
    logging.basicConfig(filename='errores.log', encoding='utf-8')
    for _, row in grupo.iterrows():
        try:
            if first:
                first = False
                ultimo_info['ts_kafka'] = row['ts_kafka']

            if (int(row['ts_kafka']) - int(ultimo_info['ts_kafka']) >= umbral):
                # Guardamos último estado de la ventana terminada
                ultimo_info = clean_row(ultimo_info, eventos)
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
                    'alt_feet': None,
                    'callsign': None,
                    'vortex': None,
                }
            
            ultimo_info['icao'] = row['ICAO']

            typecode = row["TC"]
            if (airPosClass.match(typecode)):
                ultimo_info["lat"], ultimo_info["lon"] = getAirbornePosition(row["messageHex"])
                ultimo_info["alt_feet"] = getAirborneAltitude(row["messageHex"])
            if (surPosClass.match(typecode)):
                ultimo_info["surf_vel"] = getSurfaceVelocity(row["messageHex"])
                ultimo_info["surf_lat"], ultimo_info["surf_lon"] = getSurfacePosition(row["messageHex"])
            elif (identifyClass.match(typecode)):
                identifyClass.updateRowFromHex(ultimo_info, row["messageHex"])
            elif (velClass.match(typecode)):
                ultimo_info["velocity"], _, _, _ = pms.adsb.velocity(row["messageHex"])
            elif (row["DL"] == 11 and ultimo_info['ground'] != 1):
                # HEMOS VISTO QUE NO HAY CASI NINGUN MENSAJE DE QUE ESTÁ EN TIERRA EL AVIÓN
                # VAMOS A PRIORIZAR A LOS AVIONES EN TIERRA POR TANTO
                # SI APARECE UN MENSAJE CON GROUND = 1, NO LO SOBREESCRIBIMOS SI APARECE UN GROUND = 0 MAS TARDE
                ultimo_info['ground'] = getOnGround(row["messageHex"])

            prev_time = row['ts_kafka']
        except Exception as e:
            logging.error(f'ERROR_DATOS\n{row}')
            logging.exception(e)

    # Añade el último estado (la ventana no termina)
    if (prev_time is not None):
        ultimo_info = clean_row(ultimo_info, eventos)
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
    "direccion": float,
    'alt_feet': float,
    'callsign': str,
    'vortex': str,
}


with ProgressBar():
    eventos = df.groupby("ICAO").apply(segmentar_vuelos, meta=meta)
    eventos.to_csv('data/ex2/preprocess_mapa.csv', index=False, single_file=True)