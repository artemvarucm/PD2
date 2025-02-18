import dask.dataframe as dd
import pandas as pd
import time
import pyModeS as pms
import base64
from dask.diagnostics import ProgressBar

vortexDictionary = {
            1: {
                0: "No category information",
                1: "Reserved",
                2: "Reserved",
                3: "Reserved",
                4: "Reserved",
                5: "Reserved",
                6: "Reserved",
                7: "Reserved"
            },
            2: {
                0: "No category information",
                1: "Surface emergency vehicle",
                2: "ERROR",
                3: "Surface service vehicle",
                4: "Ground obstruction",
                5: "Ground obstruction",
                6: "Ground obstruction",
                7: "Ground obstruction"
            },
            3: {
                0: "No category information",
                1: "	Glider, sailplane",
                2: "Lighter-than-air",
                3: "Parachutist, skydiver",
                4: "Ultralight, hang-glider, paraglider",
                5: "Reserved",
                6: "Unmanned aerial vehicle",
                7: "Space or transatmospheric vehicle"
            },
            4: {
                0: "No category information",
                1: "Light (less than 7000 kg)",
                2: "Medium 1 (between 7000 kg and 34000 kg)",
                3: "Medium 2 (between 34000 kg to 136000 kg)",
                4: "High vortex aircraft",
                5: "Heavy (larger than 136000 kg)",
                6: "High performance (>5 g acceleration) and high speed (>400 kt)",
                7: "Rotorcraft"
            }
}

def encodeHex(b64):
    return base64.b64decode(b64).hex()


def getDownlink(hex):
    return pms.df(hex)


def getTypeCode(hex):
    return pms.common.typecode(hex)


def getICAO(hex):
    return (str(pms.common.icao(hex))).upper()

def getCA(hex):
    return pms.bin2int(pms.hex2bin(hex)[5:8])


def msgIsCorrupted(hex):
    return (pms.crc(hex) != 0)

def getOnGround(hex):
    decimal_value =  pms.bin2int(pms.hex2bin(hex)[5:8])
    if decimal_value == 4:
        return 1
    elif decimal_value == 5:
        return 0
    else:
        return None
    
def getAircraftType(hex):
    tc = getTypeCode(hex)  
    ca = getCA(hex)        
    
    if tc in vortexDictionary and ca in vortexDictionary[tc]:
        return vortexDictionary[tc][ca]
    return None

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

def compute_surface_velocity(row):
    if 5 <= row["TC"] <= 8:
        return getSurfaceVelocity(row["messageHex"])
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

    for _, row in grupo.iterrows():
        # Si el mensaje es de superficie y se puede decodificar la velocidad,
        # y esta es exactamente 0, se considera que el avión está parado.
        if ((row["Tc"] > 0) & (row["Tc"] < 5)):
            if ((row["AircraftType"] not in ["No category information", "Reserved", "ERROR"]) | (row["TC"] != 1)):
                aircraftType = row["AircraftType"]

        if pd.notna(row.get("surface_velocity")) and row["surface_velocity"] == 0:
            ultimo_parado = row["timestamp"]

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
                    "aircraft_type": aircraftType
                })
                # Reiniciamos la marca para detectar el siguiente vuelo
                ultimo_parado = None
    return pd.DataFrame(eventos)



i = time.time()

df = dd.read_csv("C:/Universidad/Tercero/PD2/splitCSV/archivos_divididos/archivo_dividido_5.csv", sep=";")
df = df.drop(columns="Unnamed: 2")


df["messageHex"] = df["message"].apply(encodeHex,meta=str)
df["DL"] = df["messageHex"].apply(getDownlink,meta=int)
df = df[(df["DL"] == 17) | (df["DL"] == 18) | (df["DL"] == 11)].reset_index()
df["ICAO"] = df["messageHex"].apply(getICAO,meta=str)
df["CA"] = df["messageHex"].apply(getCA, meta =int)
df["OnGround"] = df["messageHex"].apply(getOnGround,meta =int)
df["AircraftType"] = df["messageHex"].apply(getAircraftType, meta='str')
table = df.dropna(subset=["OnGround"])



df['timestamp'] = dd.to_datetime(df['ts_kafka'], unit='ms')
df["fecha"] = df["timestamp"].dt.date
df["hora"] = df["timestamp"].dt.hour


df["TC"] = df["messageHex"].apply(getTypeCode,meta =int)

df = df.repartition(npartitions=1)

df["surface_velocity"] = df.apply(
    compute_surface_velocity, axis=1, meta=("surface_velocity", float)
)


# Definimos el meta para la función de groupby.apply (para Dask)
meta = {
    "ICAO": str,
    "ultimo_parado": "datetime64[ns]",
    "despegue": "datetime64[ns]",
    "tiempo_espera": float,
    "aircraft_type": str
}

with ProgressBar():
    eventos_espera = df.groupby("ICAO").apply(segmentar_vuelos, meta=meta).compute()

# Una vez obtenidos los eventos, extraemos la hora del despegue para agregarlos
eventos_espera["fecha_despegue"] = eventos_espera["despegue"].dt.date
eventos_espera["hora_despegue"] = eventos_espera["despegue"].dt.hour

# Agrupamos por hora y calculamos estadísticas (por ejemplo, media, mediana y cantidad de eventos)
estadisticas_por_dia_hora = eventos_espera.groupby(
    ["fecha_despegue", "hora_despegue"]
)["tiempo_espera"].agg(["mean", "median", "count"]).reset_index()

print("Estadísticas de tiempo de espera (en segundos) por hora de despegue:")
print(estadisticas_por_dia_hora)

with ProgressBar():
    df.to_csv('eventos_espera_semana', index=False)
