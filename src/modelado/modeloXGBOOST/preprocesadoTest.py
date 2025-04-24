#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preprocess_test_full.py

Preprocesa datos ADS-B de test (Parquet) y extrae eventos de espera/despegue,
asignando runway incluso cuando aún no ha despegado, basándose en el holding_point.
Produce un CSV con columnas:
ICAO;llegada_punto;salida_punto;despegue;tiempo_espera;aircraft_type;
llegada_lon;llegada_lat;salida_lon;salida_lat;holding_point;
parado;runway;fecha_despegue;hora_despegue;timestamp;tiempo_esperado

- runway se rellena de eventuales nulls usando un mapeo de holding_point → runway.
- tiempo_espera: diferencia real despegue–llegada
- tiempo_esperado: si no despegado, diferencia entre timestamp de corte y llegada
"""
import os
import pandas as pd
from shapely.geometry import Point, Polygon
from pyproj import Transformer
import geopandas as gpd

# -------------------------------
# Parámetros de entrada/salida
# -------------------------------
INPUT_PATH  = "../../../data/scenarios/scenario_001.parquet"
OUTPUT_PATH = "outputs/scenario1preprocessed.csv"

# ----------------------------
# 1) CARGA Y PREPARACIÓN DEL DF
# ----------------------------
df = pd.read_parquet(INPUT_PATH)
# Renombrar columnas
df = df.rename(columns={
    'icao24':        'ICAO',
    'ts':            'ts_kafka',
    'groundspeed':   'groundspeed',
    'altitude':      'altitude',
    'vertical_rate': 'vertical_rate',
    'lat_deg':       'lat',
    'lon_deg':       'lon',
    'wake_vortex':   'aircraft_type'
})
# Timestamp de cada mensaje
df['llegada_punto'] = pd.to_datetime(df['ts_kafka'], unit='ms')
# Timestamp de corte
timestamp_cutoff = df['llegada_punto'].max()
# Asegurar aircraft_type
if 'aircraft_type' not in df.columns:
    df['aircraft_type'] = None

# ----------------------------
# 2) GEOLOCALIZACIÓN: holding y pistas
# ----------------------------
# Polígonos de pista (Madrid Barajas)
rwy18R36L = Polygon([(-3.582,40.492383),(-3.5695,40.492383),(-3.5695,40.537929),(-3.582,40.537929)])
rwy18L36R = Polygon([(-3.564441,40.499172),(-3.549,40.499172),(-3.549,40.537472),(-3.564441,40.537472)])
rwy14L32R = Polygon([(-3.531683,40.464310),(-3.524645,40.468620),(-3.556317,40.498519),(-3.564652,40.495647)])
rwy14R32L = Polygon([(-3.547648,40.450661),(-3.539580,40.454710),(-3.575714,40.488141),(-3.582924,40.484224)])
# Leer holding points + buffer
holding = gpd.read_file("../../../data/geojson/holding_points.geojson")
hp_utm = holding.to_crs(epsg=32630)
hp_utm['buffer50m'] = hp_utm.buffer(50)
# Transformador coord
transformer = Transformer.from_crs("EPSG:4326","EPSG:32630",always_xy=True)

def find_holding_point_with_buffer(lon, lat):
    if pd.isna(lon) or pd.isna(lat): return None
    x, y = transformer.transform(lon, lat)
    pt = Point(x,y)
    for _, row in hp_utm.iterrows():
        if row['buffer50m'].contains(pt):
            return row.get('DESIGNATOR')
    return None

def find_runway(lon, lat):
    pt = Point(lon,lat)
    if rwy18R36L.contains(pt): return '18R/36L'
    if rwy18L36R.contains(pt): return '18L/36R'
    if rwy14L32R.contains(pt): return '14L/32R'
    if rwy14R32L.contains(pt): return '14R/32L'
    return None

# ----------------------------
# 3) DETECCIÓN DE DESPEGUE
# ----------------------------
GS_THR, ALT_THR = 80, 2400
def mark_in_air(df):
    df = df.sort_values(['ICAO','llegada_punto'])
    df['in_air'] = df['groundspeed'].fillna(0) > GS_THR
    df['prev_in_air'] = df.groupby('ICAO')['in_air'].shift(fill_value=False)
    df['takeoff_event'] = (~df['prev_in_air']) & df['in_air']
    return df
df = mark_in_air(df)

# ----------------------------
# 4) SEGMENTACIÓN DE EVENTOS
# ----------------------------
def segmentar_eventos(grp):
    grp = grp.sort_values('llegada_punto')
    visited, provis, evs = set(), [], []
    for _, r in grp.iterrows():
        hp = find_holding_point_with_buffer(r['lon'], r['lat'])
        if hp and hp not in visited:
            visited.add(hp)
            provis.append({
                'ICAO':          r['ICAO'],
                'llegada_punto': r['llegada_punto'],
                'salida_punto':  None,
                'despegue':      None,
                'tiempo_espera': None,
                'aircraft_type': r['aircraft_type'],
                'llegada_lon':   r['lon'],
                'llegada_lat':   r['lat'],
                'salida_lon':    None,
                'salida_lat':    None,
                'holding_point': hp,
                'parado':        r['groundspeed']==0,
                'runway':        None
            })
        if provis:
            last = provis[-1]
            cur_hp = find_holding_point_with_buffer(r['lon'], r['lat'])
            if last['salida_punto'] is None and cur_hp != last['holding_point']:
                last['salida_punto'] = r['llegada_punto']
                last['salida_lon']   = r['lon']
                last['salida_lat']   = r['lat']
        if r['takeoff_event']:
            for e in provis:
                e['despegue']       = r['llegada_punto']
                e['tiempo_espera']  = (e['despegue'] - e['llegada_punto']).total_seconds()
                e['runway']         = find_runway(r['lon'], r['lat'])
                evs.append(e)
            provis.clear(); visited.clear()
    evs.extend(provis)
    return pd.DataFrame(evs)

frames = [segmentar_eventos(g) for _,g in df.groupby('ICAO')]
out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

# ----------------------------
# 5) Asignar runway a nulls usando holding_point → runway
# ----------------------------
holding_to_runway = {
    'K1':'14L/32R','K2':'14L/32R','K3':'14L/32R','L1':'14L/32R',
    'LA':'14R/32R','LB':'14R/32R','LC':'14R/32R','LE':'14R/32R',
    'Y1':'18L/36R','Y2':'18L/36R','Y3':'18L/36R',
    'Z1':'18R/36L','Z2':'18R/36L','Z3':'18R/36L','Z4':'18R/36L','Z6':'18R/36L'
}
out['runway'] = out['runway'].fillna(out['holding_point'].map(holding_to_runway))

# ----------------------------
# 6) Rellenar tiempos
# ----------------------------
out['tiempo_esperado'] = out['tiempo_espera']
mask = out['tiempo_espera'].isna()
out.loc[mask,'tiempo_esperado'] = (timestamp_cutoff - out.loc[mask,'llegada_punto']).dt.total_seconds()
# timestamp
out['timestamp'] = timestamp_cutoff

# ----------------------------
# 7) Ajustes de tipos y columnas finales
# ----------------------------
out['salida_punto']   = pd.to_datetime(out['salida_punto'])
out['despegue']       = pd.to_datetime(out['despegue'])
out['fecha_despegue'] = out['despegue'].dt.date
out['hora_despegue']  = out['despegue'].dt.hour
cols = [
    'ICAO','llegada_punto','salida_punto','despegue','tiempo_espera',
    'aircraft_type','llegada_lon','llegada_lat','salida_lon','salida_lat',
    'holding_point','parado','runway','fecha_despegue','hora_despegue',
    'timestamp','tiempo_esperado'
]
out = out[cols]

# ----------------------------
# 8) Guardar CSV
# ----------------------------
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
out.to_csv(OUTPUT_PATH, sep=';', index=False)
print(f"Output generado con {len(out)} eventos → {OUTPUT_PATH}")
