import dask.dataframe as dd
import rs1090
from dask.diagnostics import ProgressBar
from utils import base64toHEX

# localización radar
RAD_LAT = 40.51
RAD_LON = -3.53

def decode_message(row):
    newRow = row
    if len(row["messageHex"]) in [14, 28]:
        decoded = rs1090.decode(row["messageHex"], row["ts_kafka"], reference=(RAD_LAT, RAD_LON))
    else:
        decoded = dict()

    newRow["ICAO"] = decoded.get("icao24", None)
    newRow["DL"] = decoded.get("df", None)
    newRow["TC"] = decoded.get("tc", None)
    newRow["capability"] = decoded.get("capability", None)
    newRow["wake_vortex"] = decoded.get("wake_vortex", None)
    newRow["heading"] = decoded["bds60"].get("heading", None) if ("bds60" in decoded and "bds50" not in decoded) else None
    newRow["vertical_rate"] = decoded["bds60"].get("vrate_inertial", None) if ("bds60" in decoded and "bds50" not in decoded) else None
    newRow["lat"] = decoded.get("latitude", None)
    newRow["lon"] = decoded.get("longitude", None)
    newRow["surface_velocity"] = decoded.get("groundspeed", None)

    return newRow

df = dd.read_csv("archivo_dividido_1.csv", sep=";")
df = df.drop(columns="Unnamed: 2")
df["messageHex"] = df["message"].apply(base64toHEX, meta=("message", str))
df['timestamp'] = dd.to_datetime(df['ts_kafka'], unit='ms')

df_decoded = df.apply(decode_message, axis=1, meta={
    'ts_kafka': 'float64',
    'message': 'object',
    'messageHex': 'object',
    'timestamp': 'datetime64[ns]',
    'ICAO': 'object',
    'DL': int,
    'TC': int,
    'capability': 'object',
    'wake_vortex': 'object',
    'heading': 'float64',
    'vertical_rate': int,
    'lat': 'float64',
    'lon': 'float64',
    'surface_velocity': 'float64'
    })
with ProgressBar():
    df_decoded.to_csv('datos_semana.csv', index=False, single_file=True)