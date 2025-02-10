import dask.dataframe as dd
import time
from utils.general_helpers import *
from dask.diagnostics import ProgressBar
import pandas as pd
"""
columns = [
'time_position', 'airborne_pos_single_antenna_flag', 'airborne_pos_CPR', 'SH',
'airborne_pos_altitude_type', 'IC', 'T', 'position_source', 'last_contact',
'airborne_pos_lon', 'vertical_rate', 'V', 'on_ground', 'ST', 'baro_altitude',
'timestamp', 'H', 'dAlt', 'airborne_pos_time', 'VrSrc', 'Dns', 'SDif', 'HDG',
'squawk', 'IFR', 'VR','VS', 'origin_country', 'icao', 'sensors', 'true_track',
'longitud', 'latitude', 'surface_velocity','ground_track','callsign', 
'Dew', 'VT', 'Svr', 'vrsi', 'airborne_pos_lat', 'spi', 'airborne_pos_surveillance_status', 'NUC', 'Vew',
'geo_altitude', 'vortex'
]
i = time.time()
table = dd.read_csv('visualization/new3.csv', delimiter=',', names=columns, dtype={'callsign': 'object', 'vortex': 'object'})
with ProgressBar():
    table[table['icao'] == '343694'].to_csv('icao_343694.csv', index=False, single_file = True)

f = time.time()
print(f - i)
"""

