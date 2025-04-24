# computeRunwayOccupied.py

import pandas as pd
import numpy as np

def compute_runway_occupancy(df_upsampled, df_int):
    # 1) Limpia nulos
    df_int_clean = df_int.dropna(subset=['salida_punto', 'despegue'])

    # 2) Prepara por pista:
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

    # 3) Función para extraer los 3 features
    def get_queue_features(row):
        runway = row['runway']
        T       = row['timestamp']
        intervals = runway_intervals.get(runway)
        desps     = runway_despegues.get(runway)

        if intervals is None or desps is None:
            return pd.Series({
                'runway_occupied':  0,
                'queue_length':     0,
                'time_since_free':  np.nan
            })

        contains = intervals.contains(T)
        runway_occupied = int(contains.any())
        queue_length    = int(contains.sum())

        # searchsorted sobre DatetimeIndex
        idx = desps.searchsorted(T)
        if idx == 0:
            tsf = np.nan
        else:
            last_departure = desps[idx-1]
            tsf = (T - last_departure).total_seconds()

        return pd.Series({
            'runway_occupied':  runway_occupied,
            'queue_length':     queue_length,
            'time_since_free':  tsf
        })

    # 4) Aplica sobre el upsample seteado
    df = df_upsampled.copy()
    df[['runway_occupied','queue_length','time_since_free']] = \
        df.apply(get_queue_features, axis=1)
    return df

def main():
    # cargo tu upsample y el histórico
    df_upsampled = pd.read_parquet('/Users/alewar/Documents/Universidad/Tercero/PD2/PD2/data/Train/datos_holding_upsampled.parquet')
    df_int       = pd.read_csv(
        '/Users/alewar/Documents/Universidad/Tercero/PD2/PD2/data/Train/train.csv',
        sep=';',
        parse_dates=['salida_punto','despegue']
    )

    # mismo filtrado que en tus modelos
    df_upsampled = df_upsampled[df_upsampled['parado'] == True]
    df_upsampled = df_upsampled[df_upsampled['tiempo_espera'] <= 500]

    # computa y guarda
    df_final = compute_runway_occupancy(df_upsampled, df_int)
    df_final.to_parquet('datos_holding_with_runway_and_queue.parquet', index=False)
    print("✅ Guardado en 'datos_holding_with_runway_and_queue.parquet'")

if __name__ == '__main__':
    main()
