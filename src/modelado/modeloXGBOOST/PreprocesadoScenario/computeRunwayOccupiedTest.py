#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_features_for_icao.py

Este script carga el CSV de eventos preprocesados (escenario1), filtra por un ICAO dado,
y calcula exactamente las características que el modelo espera:

numeric_feats     = ['tiempo_esperado','llegada_lon','llegada_lat',
                     'hora_sin','hora_cos',
                     'runway_occupied','queue_length','time_since_free']

categorical_feats = ['aircraft_type','holding_point']

Uso:
  Ajusta INPUT_CSV y ICAO_TARGET, luego:
    python compute_features_for_icao.py

Salida:
  Imprime un DataFrame con una fila y las columnas en el orden de entrenamiento.
"""
import pandas as pd
import numpy as np
# Parámetros\# ----------------------------
INPUT_CSV   = "outputs/scenario1preprocessed.csv"
ICAO_TARGET = "34324e"

# Estas son las columnas que pide el modelo
numeric_feats = [
    'tiempo_esperado', 'llegada_lon', 'llegada_lat',
    'hora_sin', 'hora_cos',
    'runway_occupied', 'queue_length', 'time_since_free'
]
categorical_feats = ['aircraft_type', 'holding_point']
all_feats = numeric_feats + categorical_feats

# ----------------------------
# 1) Leer eventos preprocesados
# ----------------------------
df = pd.read_csv(INPUT_CSV, sep=';', parse_dates=[
    'llegada_punto', 'salida_punto', 'despegue', 'timestamp'
])

# ----------------------------
# 2) Filtrar el evento de interés
# ----------------------------
df_target = df[df['ICAO'] == ICAO_TARGET]
if df_target.empty:
    raise ValueError(f"No se encontró ICAO={ICAO_TARGET} en el CSV de eventos")
row = df_target.iloc[0]

# ----------------------------
# 3) Calcular hora_sin y hora_cos a partir de llegada_punto
# ----------------------------
hour = row['llegada_punto'].hour
hora_sin = np.sin(2 * np.pi * hour / 24)
hora_cos = np.cos(2 * np.pi * hour / 24)

# ----------------------------
# 4) Preparar despegues anteriores por pista
# ----------------------------
EMPTY_DTS = np.array([], dtype='datetime64[ns]')

dep_times = {
    rwy: np.sort(grp['despegue'].dropna().values.astype('datetime64[ns]'))
    for rwy, grp in df.groupby('runway')
}

def compute_runway_queue(r0, df_events, dep_times):
    """
    Cuenta aviones en cola y pista ocupada para el evento r0.
    """
    rwy = r0['runway']
    t0  = r0['llegada_punto']
    mask = (
        (df_events['runway'] == rwy) &
        (df_events['ICAO'] != r0['ICAO']) &
        (df_events['salida_punto'].notna()) &
        (df_events['salida_punto'] <= t0) &
        ((df_events['despegue'].isna()) | (df_events['despegue'] > t0))
    )
    queue_len = int(mask.sum())
    runway_occ = int(queue_len > 0)
    # 1) Usamos nuestro array vacio tipado si no hay key
    times = dep_times.get(rwy, EMPTY_DTS)

    # 2) Convertimos el pandas.Timestamp a numpy.datetime64
    t0_np = np.datetime64(t0)

    # 3) Hacemos searchsorted ya sin mezcla de tipos
    idx = np.searchsorted(times, t0_np)

    if idx == 0:
        tsf = 0.0
    else:
        last_dep = times[idx - 1].astype('datetime64[ns]')
        # Volvemos a pandas.Timestamp para restar
        tsf = (t0 - pd.to_datetime(last_dep)).total_seconds()

    return runway_occ, queue_len, tsf

# ----------------------------
# 5) Ejecutar cálculo de runway_occupied, queue_length, time_since_free
# ----------------------------
runway_occupied, queue_length, time_since_free = compute_runway_queue(
    row, df, dep_times
)

# ----------------------------
# 6) Crear el diccionario final de features
# ----------------------------
features = {
    'tiempo_esperado':  row['tiempo_esperado'],
    'llegada_lon':      row['llegada_lon'],
    'llegada_lat':      row['llegada_lat'],
    'hora_sin':         hora_sin,
    'hora_cos':         hora_cos,
    'runway_occupied':  runway_occupied,
    'queue_length':     queue_length,
    'time_since_free':  time_since_free,
    'aircraft_type':    row['aircraft_type'],
    'holding_point':    row['holding_point']
}
X_test = pd.DataFrame([features], columns=all_feats)

pd.set_option('display.max_columns', None)

# al final de tu script, justo antes del print:
OUTPUT_CSV = f"outputs/features_ICAO_{ICAO_TARGET}.csv"
X_test.to_csv(OUTPUT_CSV, index=False)
print(f"Features guardados en {OUTPUT_CSV}")


