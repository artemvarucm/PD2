import pandas as pd

df_casos = pd.read_csv('./data/final_scenarios/answers_empty.csv')

modelo = ...

for idx, row in df_casos.iterrows():
    despegues_sampleados = 0
    despegue_predecir = despegues_sampleados[
        (despegues_sampleados.ICAO == row["icao"]) &
        (despegues_sampleados.holding_point == row["holding_point"]) &
        (despegues_sampleados.runway == row["runway"])
        ]
    if despegue_predecir.empty:
        df_casos.loc[idx, 'time_to_takeoff_s'] = -1
    else:
        # selectamos el del último timestamp
        despegue = despegue_predecir.sort_values(by="timestamp", ascending=False).reset_index(drop=True).iloc[:1]
        df_casos.loc[idx, 'time_to_takeoff_s'] = modelo.predict(despegue)

df_casos.to_csv('resultados_sin_nombre.csv', index=False)