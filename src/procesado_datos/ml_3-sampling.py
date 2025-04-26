"""
Este archivo añade filas nuevas al df utilizando sampling.
Además, se eliminan filas con la pista de despegue inusual para el punto
"""
import pandas as pd

# 1. Carga los datos desde tu CSV (ajusta la ruta y nombres de columna si es necesario)
df = pd.read_csv(
    'data/Train/train_enero_hasta_17(incluido).csv',
    sep=',',
    parse_dates=['llegada_punto', 'salida_punto', 'despegue']
)

# Quitamos outliers muy claros
noOutliersMask = (df['tiempo_espera'] <= 1200) & (df['tiempo_espera'] > 10)
print("-> Outliers eliminados:", df.shape[0] - noOutliersMask.sum(), "de", df.shape[0])
df = df[noOutliersMask]
# Se asume que al salir del punto de espera, se entra a la pista.
# Descartamos datos que digan lo contrario (son relativamente pocos)
holding_to_runway = {
    'K1':'14L/32R','K2':'14L/32R','K3':'14L/32R',
    'L1':'14L/32L','LA':'14R/32L','LB':'14R/32L','LC':'14R/32L','LE':'14R/32L',
    'Y1':'18L/36R','Y2':'18L/36R','Y3':'18L/36R',
    'Z1':'18R/36L','Z2':'18R/36L','Z3':'18R/36L','Z4':'18R/36L','Z6':'18R/36L'
}
df = df.dropna(subset=['salida_punto', 'despegue'])

correct_runway = df['holding_point'].map(holding_to_runway)
df['runway'] = df['runway'].fillna(correct_runway)
print('-> Despegues con pistas inusuales:', (df['runway'] != correct_runway).sum(), "de", df.shape[0])
df = df[df['runway'] == correct_runway]

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
            'timestamp': ts, # tiempo actual
            'tiempo_esperado': tiempo_esperado, # tiempo que lleva en el punto
            'tiempo_espera': tiempo_espera_remain # tiempo que falta para despegar
        })
        records.append(rec)

# 3. Ensambla el DataFrame resultante
df_upsampled = pd.DataFrame.from_records(records)

#df_upsampled.to_csv('datos_holding_upsampled_nuevo.csv', index=False, sep=';')


out_path = 'data/Train/datos_sample_ml_3.parquet'
df_upsampled.to_parquet(
    out_path,
    engine='pyarrow',
    index=False
)


print(f"Guardado  en {out_path}.")

