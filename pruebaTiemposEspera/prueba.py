import dask.dataframe as dd
import pandas as pd
import time
import pyModeS as pms
import base64
from dask.diagnostics import ProgressBar

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



i = time.time()

df = dd.read_csv("E:/UniversidadCoding/Tercero/PD2/Datos/pequeños/archivo_dividido_3.csv", sep=";")
df = df.drop(columns="Unnamed: 2")


df["messageHex"] = df["message"].apply(encodeHex,meta=str)
df["DL"] = df["messageHex"].apply(getDownlink,meta=int)
df = df[(df["DL"] == 17) | (df["DL"] == 18)].reset_index()
df["ICAO"] = df["messageHex"].apply(getICAO,meta=str)
df["CA"] = df["messageHex"].apply(getCA, meta =int)
df["OnGround"] = df["messageHex"].apply(getOnGround,meta =int)
table = df.dropna(subset=["OnGround"])



df['timestamp'] = dd.to_datetime(df['ts_kafka'], unit='ms')
df["fecha"] = df["timestamp"].dt.date
df["hora"] = df["timestamp"].dt.hour


df["TC"] = df["messageHex"].apply(getTypeCode,meta =int)

df = df.repartition(npartitions=1)

with ProgressBar():
    df.to_csv('pruebaCSV3', index=False)
