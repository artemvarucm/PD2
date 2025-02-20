import dask.dataframe as dd
import pandas as pd
import time
import pyModeS as pms
from utils import *
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


def getCA(hex):
    return pms.bin2int(pms.hex2bin(hex)[5:8])

def getAircraftType(hex):
    tc = getTypeCode(hex)
    ca = getCA(hex)

    if tc in vortexDictionary and ca in vortexDictionary[tc]:
        return vortexDictionary[tc][ca]
    return None


i = time.time()
df = dd.read_csv("E:/UniversidadCoding/Tercero/PD2/datos/semana/datosSemana.csv", sep=";")
df = df.drop(columns="Unnamed: 2")
df["messageHex"] = df["message"].apply(base64toHEX, meta=str)
df["DL"] = df["messageHex"].apply(getDownlink, meta=int)



filtroDL = df["DL"].isin([11, 17, 18])
filtroCorrupto = df["messageHex"].map(lambda x: msgIsCorrupted(x) == False, meta=bool)
df = df[filtroDL & filtroCorrupto].reset_index()


df["ICAO"] = df["messageHex"].apply(getICAO, meta=str)
df["CA"] = df["messageHex"].apply(getCA, meta=int)
df["OnGround"] = df["messageHex"].apply(getOnGround, meta=int)
df["AircraftType"] = df["messageHex"].apply(getAircraftType, meta='str')
df['timestamp'] = dd.to_datetime(df['ts_kafka'], unit='ms')
df["fecha"] = df["timestamp"].dt.date
df["hora"] = df["timestamp"].dt.hour
df["TC"] = df["messageHex"].apply(getTypeCode, meta=int)
df = df.repartition(npartitions=1)
with ProgressBar():
    df.to_csv('datos_semana', index=False, single_file=True)
