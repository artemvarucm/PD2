import os
from pathlib import Path
import pandas as pd
from datetime import datetime
"""
Este archivo concatena todos los archivos procesados en un csv
"""


base_processed_path = "./data/Preprocessed"
base_output_path = "./data/Train/"

old_files = list(Path(base_output_path).glob("train_*.csv"))
if old_files:
    print(f"Existen archivos de train: {old_files}")
    delPrev = input("Eliminar archivos previos? y/n: ")
    if delPrev.lower() == "y":
        for file in old_files:
            os.remove(file)

all_dfs = []
for month in [11, 12, 1]:
    for day in range(1, 32):
        path = Path(base_processed_path,f"{month:02d}",f"{day:02d}")
        print(f"Revisando: {path}")

        if os.path.exists(path):
            archivos = list(path.glob("*"))
            print(f"Archivos encontrados: {[f.name for f in archivos]}")
            if archivos:
                df = pd.read_parquet(archivos)
                all_dfs.append(df)

df = pd.concat(all_dfs)
df = df.sort_values(by="despegue", ascending=True)
print(df.info())
print(f"Shape: {df.shape}")
filename = datetime.now().strftime("train_%d_%m_%Y_%H-%M.csv")
out_path = Path(base_output_path, filename)
df.to_csv(out_path, index=False)
print(f"Guardado en {out_path}")