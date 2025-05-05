import pandas as pd
from pathlib import Path
from scenarioTransformer import get_preprocessed_scenario

scenariosPath = './data/final_scenarios/'
df_casos = pd.read_csv(Path(scenariosPath, 'answers_empty.csv'))

#modelo = ...

for idx, row in df_casos.iterrows():
    processed = get_preprocessed_scenario(Path(scenariosPath, row['scenario_name']), row)
    if processed is None:
        df_casos.loc[idx, 'time_to_takeoff_s'] = -1
    else:
        df_casos.loc[idx, 'time_to_takeoff_s'] = 10 #modelo.predict(processed)

df_casos.to_csv('resultados_sin_nombre.csv', index=False)