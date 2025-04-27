import pandas as pd
from sklearn.model_selection import train_test_split

"""
Este archivo separa los datos en train(80%) test(20%), 
manteniendo la misma proporción de holding point (usando stratify)
"""
df = pd.read_parquet("data/Train/datos_final_ml_4.parquet")

train_df, test_df = train_test_split(
    df,
    test_size=0.2,
    stratify=df["holding_point"],
    random_state=777
)
print("DISTRIBUCIÓN POR PUNTO DE ESPERA")
print(pd.DataFrame({"TRAIN": (train_df.holding_point.value_counts() / train_df.shape[0]), 
              "TEST": (test_df.holding_point.value_counts() / test_df.shape[0])
              }).sort_index())

# guardamos en .parquet
train_df.to_parquet('data/Train/train_final.parquet', index=False)
test_df.to_parquet('data/Train/test_final.parquet', index=False)