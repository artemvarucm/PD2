"""
Este script añade 4 columnas extra a los datos sampleados de entrenamiento

1. queue_length: número de aviones, que han salido de su punto de espera 
    (su salida_punto es menor que el timestamp del instante) pero no han despegado 
    (su despegue también es menor que el timestamp del instante).
    En resumen, aquellos aviones que han podido rebasar el punto de espera y están entrando en la pista.

2. runway_occupied: boolean, true si queue_length > 0.

3. time_since_free: tiempo en segundos desde el último despegue.

4. hold_pt_occupied: número de puntos de espera que llevan a la misma pista y que están ocupados en el instante 
    (llegada_punto menor que timestamp y salida_punto mayor que timestamp). No incluye el mismo punto del instante.
"""

import pandas as pd
import numpy as np

"""
Función para sacar runway_occupied, queue_length y time_since_free

Parameters
----------
row : fila del DataFrame
runway_intervals : dicccionario que guarda por cada pista, tiene la lista ordenada de intervalos de tiempo cuando estaba ocupada
runway_despegues : dicccionario que guarda por cada pista, tiene la lista ordenada de los despegues
"""
def get_queue_features(row, runway_intervals, runway_despegues):
    runway = row['runway']
    current_ts       = row['timestamp']
    intervals = runway_intervals.get(runway)
    desps     = runway_despegues.get(runway)

    if intervals is None or desps is None:
        return pd.Series({
            'runway_occupied':  0,
            'queue_length':     0,
            'time_since_free':  np.nan
        })

    contains = intervals.contains(current_ts) # devuelve boolean por cada intervalo, vale True si contiene el número
    # pueden haber varios aviones que están en la pista o han salido de su punto de espera 
    # (por lo de punto de "preespera" y "postespera")
    queue_length    = int(contains.sum())

    idx = desps.searchsorted(current_ts) # devuelve el índice donde tendrías que insertar el elemento
    if idx == 0:
        time_since_free = np.nan # no hay ningún despegue
    else:
        last_departure = desps[idx-1] # el último despegue más cercano a current_ts
        time_since_free = (current_ts - last_departure).total_seconds()

    return pd.Series({
        'runway_occupied':  int(queue_length > 0),
        'queue_length':     queue_length,
        'time_since_free':  time_since_free
    })

"""
Para sacar la variable hold_pt_occupied

Parameters
----------
row : fila del DataFrame
holding_intervals : dicccionario que guarda por cada pista, tiene la lista ordenada de intervalos de tiempo cuando estaba ocupada
"""
def get_hold_pt_occupied(row, holding_intervals):
    runway = row['runway']
    current_ts = row['timestamp']
    runway_to_holding = {
        '14L/32R': ['K1', 'K2', 'K3'],
        '14R/32L': ['L1', 'LA', 'LB', 'LC', 'LE'],
        '18L/36R': ['Y1', 'Y2', 'Y3'],
        '18R/36L': ['Z1', 'Z2', 'Z3', 'Z4', 'Z6']
    }


    count = 0
    for hold_pt in runway_to_holding[runway]:
        if hold_pt != row['holding_point']:
            intervals = holding_intervals.get(hold_pt)
            contains = intervals.contains(current_ts) # devuelve boolean por cada intervalo, vale True si contiene el número
            if contains.any():
                count += 1

    return pd.Series({
        'hold_pt_occupied': count,
    })

# Función que aplica la anterior función al dataframe, previamente calculando los tiempos ocupados de la pista
def compute_runway_occupancy(df_upsampled):
    # ml_3 devuelve datos en los que el avión que está en un punto de espera va a despegar a la pista directamente
    
    # para no usar los datos sampleados 2 veces, ya que las filas salen duplicadas (mejora rendimiento)
    df_int_clean = df_upsampled[['llegada_punto', 'salida_punto', 'despegue', 'runway', 'holding_point']].dropna().drop_duplicates()

    # Diccionarios por pista
    runway_intervals = {}
    runway_despegues = {}
    for runway, group in df_int_clean.groupby('runway'):
        # intervalos de ocupación completos
        runway_intervals[runway] = pd.IntervalIndex.from_arrays(
            group['salida_punto'],
            group['despegue'],
            closed='both'
        )
        # datetimes ordenados de despegue
        runway_despegues[runway] = pd.DatetimeIndex(group['despegue']).sort_values()
    
    # lo mismo, pero para la ocupación de puntos de espera
    holding_intervals = {}
    for hold_pt, group in df_int_clean.groupby('holding_point'):
        holding_intervals[hold_pt] = pd.IntervalIndex.from_arrays(
            group['llegada_punto'],
            group['salida_punto'],
            closed='both'
        )

    df_upsampled[['runway_occupied','queue_length','time_since_free']] = df_upsampled.apply(
        lambda row: get_queue_features(row, runway_intervals, runway_despegues), axis=1)
    
    df_upsampled[['hold_pt_occupied']] = df_upsampled.apply(
        lambda row: get_hold_pt_occupied(row, holding_intervals), axis=1)

    return df_upsampled

def main():
    # cargo tu upsample
    df_upsampled = pd.read_parquet('data/Train/datos_sample_ml_3.parquet')
    # no hace falta
    #df_upsampled = df_upsampled[df_upsampled['parado'] == False]
    #df_upsampled = df_upsampled[df_upsampled['tiempo_espera'] <= 500]
    #df_upsampled = df_upsampled[df_upsampled['tiempo_espera'] >= 25]

    # computa y guarda
    df_final = compute_runway_occupancy(df_upsampled)
    out = "data/Train/datos_final_ml_4.parquet"
    df_final.to_parquet(out, index=False)
    print(f"Guardado en {out}")

if __name__ == '__main__':
    main()
