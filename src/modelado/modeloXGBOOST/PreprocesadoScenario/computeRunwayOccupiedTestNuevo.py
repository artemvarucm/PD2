#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_features_for_icao_updated.py

Este script carga el CSV de eventos preprocesados (escenario1), filtra por un ICAO dado,
y calcula exactamente las características que el modelo espera, incluyendo todas las
features de ingeniería: hora cíclica, día de semana, fin de semana, interacción.

Uso:
  Ajusta INPUT_CSV y ICAO_TARGET, luego:
    python compute_features_for_icao_updated.py

Salida:
  Genera un CSV con una fila y las columnas en el orden de entrenamiento.
"""
import pandas as pd
import numpy as np
# Parámetros --------------------------------------------------
INPUT_CSV   = "outputs/scenario1preprocessed.csv"
ICAO_TARGET = "34324e"

# Columnas esperadas por el modelo
numeric_feats = [
    'tiempo_esperado', 'llegada_lon', 'llegada_lat',
    'hora_sin', 'hora_cos', 'weekday', 'is_weekend', 'queue_x_runway',
    'runway_occupied', 'queue_length', 'time_since_free'
]
categorical_feats = ['aircraft_type', 'holding_point']
all_feats = numeric_feats + categorical_feats

# 1) Leer eventos preprocesados
# ---------------------------------
df = pd.read_csv(
    INPUT_CSV, sep=';',
    parse_dates=['llegada_punto', 'salida_punto', 'despegue', 'timestamp']
)

# 2) Filtrar el evento de interés
# ---------------------------------
df_target = df[df['ICAO'] == ICAO_TARGET]
if df_target.empty:
    raise ValueError(f"No se encontró ICAO={ICAO_TARGET} en el CSV de eventos")
row = df_target.iloc[0]

# 3) Calcular hora cíclica con minutos
# ------------------------------------
t0 = row['llegada_punto']
hora_decimal = t0.hour + t0.minute / 60
hora_sin = np.sin(2 * np.pi * hora_decimal / 24)
hora_cos = np.cos(2 * np.pi * hora_decimal / 24)

# 4) Preparar despegues anteriores por pista
# -------------------------------------------
EMPTY_DTS = np.array([], dtype='datetime64[ns]')
dep_times = {
    rwy: np.sort(grp['despegue'].dropna()
                .values.astype('datetime64[ns]'))
    for rwy, grp in df.groupby('runway')
}

def compute_runway_queue(r0, df_events, dep_times):
    """
    Cuenta aviones en cola y pista ocupada para el evento r0.
    Devuelve (runway_occupied, queue_length, time_since_free).
    """
    rwy = r0['runway']
    t0  = r0['llegada_punto']
    # Cola vs pista ocupada
    mask = (
        (df_events['runway'] == rwy) &
        (df_events['ICAO'] != r0['ICAO']) &
        (df_events['salida_punto'].notna()) &
        (df_events['salida_punto'] <= t0) &
        ((df_events['despegue'].isna()) | (df_events['despegue'] > t0))
    )
    queue_len = int(mask.sum())
    runway_occ = int(queue_len > 0)

    # Calcular time_since_free
    times = dep_times.get(rwy, EMPTY_DTS)
    t0_np = np.datetime64(t0)
    idx = np.searchsorted(times, t0_np)
    if idx == 0:
        tsf = 0.0
    else:
        last_dep = times[idx - 1].astype('datetime64[ns]')
        tsf = (t0 - pd.to_datetime(last_dep)).total_seconds()
    return runway_occ, queue_len, tsf

# 5) Calcular runway_occupied, queue_length, time_since_free
# ---------------------------------------------------------
runway_occupied, queue_length, time_since_free = compute_runway_queue(
    row, df, dep_times
)

# 6) Calcular weekday, is_weekend, interacción
# -------------------------------------------
weekday = t0.weekday()
is_weekend = int(weekday in [5, 6])
queue_x_runway = runway_occupied * queue_length

# 7) Crear diccionario final de features
# --------------------------------------
features = {
    'tiempo_esperado':   row['tiempo_esperado'],
    'llegada_lon':       row['llegada_lon'],
    'llegada_lat':       row['llegada_lat'],
    'hora_sin':          hora_sin,
    'hora_cos':          hora_cos,
    'weekday':           weekday,
    'is_weekend':        is_weekend,
    'queue_x_runway':    queue_x_runway,
    'runway_occupied':   runway_occupied,
    'queue_length':      queue_length,
    'time_since_free':   time_since_free,
    'aircraft_type':     row['aircraft_type'],
    'holding_point':     row['holding_point']
}
X_test = pd.DataFrame([features], columns=all_feats)

# 8) Guardar CSV de features
# ---------------------------
OUTPUT_CSV = f"outputs/features_ICAO_{ICAO_TARGET}.csv"
X_test.to_csv(OUTPUT_CSV, index=False)
print(f"Features guardados en {OUTPUT_CSV}")
