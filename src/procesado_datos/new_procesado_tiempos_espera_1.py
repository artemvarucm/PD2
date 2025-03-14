import dask.dataframe as dd
from utils import *
from dask.diagnostics import ProgressBar

df = dd.read_csv("202412010000_202412072359.csv", sep=";")
df = df.drop(columns="Unnamed: 2")

df["messageHex"] = df["message"].apply(base64toHEX, meta=str)
df["DL"] = df["messageHex"].apply(getDownlink, meta=int)

filtroDL = df["DL"].isin([11, 17, 18])
#filtroCorrupto = df["messageHex"].map(lambda x: msgIsCorrupted(x) == False, meta=bool)
df = df[filtroDL].reset_index()# & filtroCorrupto].reset_index()


df["ICAO"] = df["messageHex"].apply(getICAO, meta=str)
df["OnGround"] = df["messageHex"].apply(getOnGround, meta=int)
df['timestamp'] = dd.to_datetime(df['ts_kafka'], unit='ms')
df["fecha"] = df["timestamp"].dt.date
df["hora"] = df["timestamp"].dt.hour
df["TC"] = df["messageHex"].apply(getTypeCode, meta=int)

airIdMsg = AircraftIdentificationMessage()
df["AircraftType"] = df["messageHex"].apply(airIdMsg.getAircraftType, meta='str')
df["CA"] = df["messageHex"].apply(airIdMsg.getCA, meta=int)

#df = df.repartition(npartitions=1)
with ProgressBar():
    # !extensión csv!
    df.to_csv('datos_semana.csv', index=False, single_file=True)