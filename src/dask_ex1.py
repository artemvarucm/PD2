import dask.dataframe as dd
import time
from utils import *
from dask.diagnostics import ProgressBar

i = time.time()
table = dd.read_csv('202412010000_202412072359.csv', delimiter=';')

table['hour'] = dd.to_datetime(table['ts_kafka'], unit='ms').dt.hour
table['day'] = dd.to_datetime(table['ts_kafka'], unit='ms').dt.day

table['hex'] = table['message'].map(base64toHEX, meta=str)
table['icao'] = table['hex'].map(getICAO, meta=str)
#table['typecode'] = table['hex'].map(getTypeCode, meta=int)
table['downlink'] = table['hex'].map(getDownlink, meta=int)

table["on_ground"] = table['hex'].map(getOnGround, meta=int)

table = table[(table['downlink'] == 11) & (~table["on_ground"].isna())]

table = table.groupby(['icao', 'hour', 'day']).agg({'on_ground' : ['min', 'max']}).reset_index()
table.columns = ['_'.join(col).rstrip('_') for col in table.columns.values]
table['ground'] = 1 - table['on_ground_min']
table['flying'] = table['on_ground_max']

#table = table.groupby('hour').agg({'ground' : 'sum', 'flying': 'sum'}).reset_index()

with ProgressBar():
    table.to_csv('data/ex1/preprocessed_ex1.csv', index=False, single_file=True) # tarda 6807 segundos


f = time.time()
print(f - i)

# Convertimos en archivo único
#table = dd.read_csv('ej1.csv/*.part')
#table.to_csv('data/clean/preprocessed_ej1.csv', single_file=True, index=False)

# Para el ejercico 1.b
#table['secs'] = table['ts_kafka'] // 1000
#table['velocity'] = table['tc'].map(lambda x: 100 if x < 10 else None, meta=int)
#table['lat'] = table['tc'].map(lambda x: 76 if x > 10 else None, meta=int)
#table['lon'] = table['tc'].map(lambda x: 22 if x > 10 else None, meta=int)
#icao = table['icao']
#secs = table['secs']
#table = table.groupby(['icao', 'secs']).ffill()
#table['icao'] = icao
#table['secs'] = secs