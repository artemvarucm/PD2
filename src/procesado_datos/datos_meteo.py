import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import numpy as np
import time
import pandas as pd
import random

"""
Extrae datos para una fecha determinada (utiliza estrategia para evitar detección de bots cambiando de user_agent)
"""
def extraer_datos_meteorologicos(fecha):

    url = f"https://x-y.es/aemet/est-3129-madrid-barajas?fecha={fecha}"

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.184 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chromium/121.0.6167.85 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.78 Safari/537.36"
    ]

    headers = {
        "User-Agent": random.choice(user_agents)
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error al acceder a la página: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")
    
    if not table:
        print(f"No se encontró una tabla de datos para la fecha {fecha}")
        return None
    
    rows = table.find_all("tr")[1:]
    data = []
    for row in rows:
        columns = row.find_all("td")
        values = [col.text.strip() if col.text.strip() != "-" else np.nan for col in columns]
        data.append(values)

    df = pd.DataFrame(data, columns=["Hora", "Precipitación", "Temperatura", "Humedad",
                                     "Viento", "Dirección", "Viento máximo",
                                     "Dirección viento máximo", "Temperatura mínima",
                                     "Temperatura máxima"])
    
    return df

"""
Extrae datos en un rango de [fecha_inicio, fecha_fin]
"""
def extraer_datos_rango(fecha_inicio, fecha_fin):
    start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    end_date = datetime.strptime(fecha_fin, "%Y-%m-%d")

    all_data = []
    current_date = start_date
    
    while current_date <= end_date:
        fecha_str = current_date.strftime("%Y-%m-%d")
        print(f"Extrayendo datos para {fecha_str}...")

        df_dia = extraer_datos_meteorologicos(fecha_str)
        if df_dia is not None:
            df_dia["Fecha"] = fecha_str
            all_data.append(df_dia)

        # Pausa para evitar bloqueos (ajusta el tiempo si sigue bloqueando)
        time.sleep(random.uniform(3, 6))  # Espera x segundos entre cada solicitud

        current_date += timedelta(days=1)

    if all_data:
        df_total = pd.concat(all_data, ignore_index=True)
        return df_total
    else:
        print("No se encontraron datos en el rango especificado.")
        return None


fecha_inicio = "2024-11-07"
fecha_fin = "2025-01-06"

df_1 = extraer_datos_rango(fecha_inicio, fecha_fin)

time.sleep(5 * 60) # para esperar y confundir que no es bot

fecha_inicio = "2025-01-07"
fecha_fin = "2025-01-31"

df_2 = extraer_datos_rango(fecha_inicio, fecha_fin)

# Eliminar duplicados si existen
df_final = pd.concat([df_1, df_2]).drop_duplicates(subset=["Fecha", "Hora"], keep="first")

# Ordenar por fecha y hora
df_final = df_final.sort_values(by=["Fecha", "Hora"]).reset_index(drop=True)

# Mostrar los primeros valores
print(df_final.head())

ruta_guardado = "datos_meteorologicos.csv"  
df_final.to_csv(ruta_guardado, index=False)