"""
Este archivo añade filas nuevas al df utilizando sampling
"""
import pandas as pd

# 1. Carga los datos desde tu CSV (ajusta la ruta y nombres de columna si es necesario)
df = pd.read_csv(
    '/Users/alewar/Documents/Universidad/Tercero/PD2/PD2/data/Train/train.csv',
    sep=';',
    parse_dates=['llegada_punto', 'salida_punto', 'despegue']
)

df = df[df['tiempo_espera'] <= 500]
df = df[df['tiempo_espera'] > 50]
df = df.dropna(subset=['salida_punto', 'despegue'])

# 2. Genera filas cada 5 segundos y calcula nuevas columnas
records = []
for _, row in df.iterrows():
    # rango de timestamps cada 5 segundos desde llegada hasta despegue
    timestamps = pd.date_range(start=row['llegada_punto'], end=row['salida_punto'], freq='5s')
    for ts in timestamps:
        tiempo_esperado = (ts - row['llegada_punto']).total_seconds()
        tiempo_espera_remain = row['tiempo_espera'] - tiempo_esperado
        rec = row.to_dict()
        rec.update({
            'timestamp': ts,
            'tiempo_esperado': tiempo_esperado,
            'tiempo_espera': tiempo_espera_remain
        })
        records.append(rec)

# 3. Ensambla el DataFrame resultante
df_upsampled = pd.DataFrame.from_records(records)
"""
df_upsampled.to_csv('datos_holding_upsampled_nuevo.csv', index=False, sep=';')
"""


df_upsampled.to_parquet(
    'datos_holding_upsampled_nuevo.parquet',
    engine='pyarrow',
    index=False
)


print("Guardado  en 'datos_holding_upsampled.parquet'.")

