import dask.dataframe as dd
import pandas as pd
from dask.diagnostics import ProgressBar
import pyModeS as pms


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

df = dd.read_csv("E:/UniversidadCoding/Tercero/PD2/PD2/pruebaTiemposEspera/pruebaCSV3/0.part", sep=",", parse_dates=["timestamp"])  # o el patrón que hayas definido

df["surface_velocity"] = df.apply(
    compute_surface_velocity, axis=1, meta=("surface_velocity", float)
)

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

    for _, row in grupo.iterrows():
        # Si el mensaje es de superficie y se puede decodificar la velocidad,
        # y esta es exactamente 0, se considera que el avión está parado.
        if pd.notna(row.get("surface_velocity")) and row["surface_velocity"] == 0:
            ultimo_parado = row["timestamp"]
        # Cuando se detecta que el avión ya está en aire (OnGround == 0)
        if row["OnGround"] == 0:
            if ultimo_parado is not None:
                tiempo_despegue = row["timestamp"]
                tiempo_espera = (tiempo_despegue - ultimo_parado).total_seconds()
                eventos.append({
                    "ICAO": row["ICAO"],
                    "ultimo_parado": ultimo_parado,
                    "despegue": tiempo_despegue,
                    "tiempo_espera": tiempo_espera
                })
                # Reiniciamos la marca para detectar el siguiente vuelo
                ultimo_parado = None
    return pd.DataFrame(eventos)


# Definimos el meta para la función de groupby.apply (para Dask)
meta = {
    "ICAO": str,
    "ultimo_parado": "datetime64[ns]",
    "despegue": "datetime64[ns]",
    "tiempo_espera": float
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
