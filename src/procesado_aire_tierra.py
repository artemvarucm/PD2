import dask.dataframe as dd
import time
from dask.diagnostics import ProgressBar
from utils import *

i = time.time()
table = dd.read_csv("202412010000_202412072359.csv", delimiter=';')

table = table.drop(columns="Unnamed: 2")


## Transforming the message to hex
table["messageHex"] = table["message"].apply(base64toHEX,meta=str)
table["DL"] = table["messageHex"].apply(getDownlink,meta=int)

## Filtering messages by downlink format ==11 and removing corrupted messages
#table = table[table["DL"] == 11].reset_index()
filtroDL = table["DL"] == 11
filtroCorrupto = table["messageHex"].apply(msgIsCorrupted, meta=bool)
table = table[filtroDL & ~filtroCorrupto].reset_index()

## getting the icao
table["ICAO"] = table["messageHex"].apply(getICAO,meta=str)

 
## Decripting onground messages 
table["OnGround"] = table["messageHex"].apply(getOnGround,meta =int)
table = table.dropna(subset=["OnGround"])

##timestamp


table['timestamp'] = dd.to_datetime(table['ts_kafka'], unit='ms')
table['formatted_date'] = table['timestamp'].dt.strftime('%d/%m/%Y %H:%M')
table["day"] = table['timestamp'].dt.strftime('%d/%m/%Y')
table["hour"] = table['timestamp'].dt.hour


##with ProgressBar():
  ##  table.to_csv('data/ex1/preprocessed_df_11.csv', index=False, single_file=True) 

## groupby by day,hour,ICAO and getting the values of onground for further analysis


with ProgressBar():
    df = table.compute()

df = df.groupby(["day","hour","ICAO"])["OnGround"].unique().explode().reset_index()




with ProgressBar():
    df.to_csv('data/ex1/parte1.csv', index=False) 


    
