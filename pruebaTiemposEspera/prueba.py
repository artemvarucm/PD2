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

with ProgressBar():
    df.to_csv('pruebaCSV5', index=False)
