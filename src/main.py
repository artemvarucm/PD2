import pandas as pd
import base64
import pyModeS as pms
import time
from surface_position import SurfacePositionMessage

"""
Recorre fila por fila el dataFrame para devolver un df
nuevo con información que conocemos en cada instante

path: Ruta al csv que tiene 2 columnas, "ts_kafka" y "message"
new_path: Ruta al csv en la salida

"""
def merge(path, new_path):
    # columnas del dataframe resultante
    columns = [
        "timestamp",
        "icao",
        "callsign",
        "origin_country",
        "time_position",
        "last_contact",
        "longitude",
        "latitude",
        "baro_altitude",
        "on_ground",
        "velocity",
        "true_track",
        "vertical_rate",
        "sensors",
        "geo_altitude",
        "squawk",
        "spi",
        "position_source",
    ]

    # IMPORTANTE: Contiene la lista con todos los tipos de mensajes, para poder comprobar
    # si el mensaje pertenece a ese tipo y ejecutar la logica correspondiente
    messagesTypes = [SurfacePositionMessage()]

    # Guarda el ultimo estado de atributos avion
    # (la clave seria ICAO, el valor seria otro diccionario con los valores para todas las columnas)
    plane_last_states = {}

    i = 0
    chunksize = 10**6
    for chunk in pd.read_csv(path, sep=";", chunksize=chunksize):
        # Guarda cada chunk procesado
        processed_rows = []

        print(f"[INFO] Reading CHUNK {i}.")
        start = time.time()

        for index, row in chunk.iterrows():
            # PARTE 1: Comprobamos el downlink format
            T = row["ts_kafka"]
            msgHex = encodeHex(row["message"])
            DL = getDownlink(msgHex)

            if DL in [17, 18]:  # segun documentacion ads-b.MD
                # PARTE 2: Sacamos atributos que conocemos de antes a partir del ICAO del avion
                ICAO = getICAO(msgHex)

                if ICAO in plane_last_states:
                    # este avion ya se ha procesado antes (los atributos se mantienen)
                    newRow = plane_last_states[ICAO].copy()
                else:
                    # este avion no se ha procesado antes
                    newRow = {col: None for col in columns}
                    newRow["icao"] = ICAO
                    plane_last_states[ICAO] = newRow

                newRow["timestamp"] = T

                # PARTE 3: Logica de procesamiento de campos segun cada mensaje
                TC = getTypeCode(msgHex)
                for mType in messagesTypes:
                    if mType.match(TC):
                        mType.updateRowFromHex(newRow, msgHex)
                        plane_last_states[ICAO] = newRow
                        processed_rows.append(newRow)
                        break  # solo puede ser de un tipo el mensaje

        

        if processed_rows:
            dfProcessed = pd.DataFrame(processed_rows, columns=columns)
            if i == 0:
                # Escribe header en la primera escritura y sobreescribe el contenido
                dfProcessed.to_csv(new_path, index=False)
            else:
                # añade los datos (mode = "a") al final del archivo
                dfProcessed.to_csv(new_path, mode="a", header=False, index=False)

        end = time.time()
        print(f"[INFO] Finished reading CHUNK {i} in {end - start}")
        i += 1


def encodeHex(b64):
    return base64.b64decode(b64).hex()


def getDownlink(hex):
    return pms.df(hex)


def getTypeCode(hex):
    return pms.common.typecode(hex)


def getICAO(hex):
    return str(pms.common.icao(hex))


# PRUEBA
merge("202412010000_202412072359.csv", "new.csv")
