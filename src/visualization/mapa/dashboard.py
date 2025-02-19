import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import time
import pandas as pd
from static_map import StaticMap

app = dash.Dash(__name__)

# Eliminamos filas sin latitud, longitud y ground
df = pd.read_csv("data/ex2/preprocess_mapa_16_02.csv")
df = df.dropna(subset=['lat', 'lon', 'ground'])
df = df[(df.lat != None) & (df.lon != None) & (df.ground != None)]
# Ordenamos de pasado a futuro
df = df.sort_values(by='ts_kafka', ascending=True)

df['date'] = pd.to_datetime(df['ts_kafka'], unit='ms').dt.strftime('%Y-%m-%d')
df['datetime'] = pd.to_datetime(df['ts_kafka'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')

# Para seleccionar el rango de fechas (desde 00:00 fecha min a fecha max 23:00)
date_range = pd.date_range(start=df.iloc[0]['date'], end=str(df.iloc[-1]['date']) + " 23:00", freq="h")
decodeRangeValues = {i: date for i, date in enumerate(date_range)}

app.layout = html.Div([
    html.Br(),
    dcc.RangeSlider(
        id="slider-param",
        min=0,
        max=len(date_range) - 1,
        step=1,
        marks={i: {"label": date.strftime("%m-%d %H:%M"), "style": {"font-size": "16px"}} for i, date in enumerate(date_range) if date.hour == 0},
        value=[0, len(date_range) - 1]
    ),
    html.Br(),
    html.Br(),
    html.Iframe(
        id="iframe_map",
        src="/assets/intro.html",  # Default page
        style={"width": "100%", "height": "700px"}
    ),
])

# Callback to generate and update the map
@app.callback(
    Output("iframe_map", "src"),
    [Input("slider-param", "value")],
    prevent_initial_call=True
)
def generate_and_load(value_range):
    lowerBound = decodeRangeValues[value_range[0]]
    upperBound = decodeRangeValues[value_range[1]]

    lowerBound_ts = pd.Timestamp(lowerBound).timestamp() * 1000
    upperBound_ts = pd.Timestamp(upperBound).timestamp() * 1000

    # Filtramos dataframe
    print('FILTERING')
    filter_bounds = (df['ts_kafka'] >= lowerBound_ts) & (df['ts_kafka'] <= upperBound_ts)
    df_filtered = df[filter_bounds]
    print(f'FILTERED {filter_bounds.sum()} ROWS')
    # Creamos el mapa
    file_path = "src/visualization/mapa/assets/generated.html"

    m = StaticMap()
    print('ADDING AIRPLANES')
    """
    # Manual para probar, esto SI va
    timestamp_str1 = "2025-02-15 14:06:22"
    timestamp_str2 = "2025-02-15 14:06:25"
    timestamp_str3 = "2025-02-15 14:06:28"
    timestamp_str4 = "2025-02-15 20:06:22"
    timestamp_str5 = "2025-02-15 20:06:24"
    timestamp_str6 = "2025-02-15 20:06:29"

    m.addAirplane("jnsfu", 40.52, -3.53, True, 0, 10, timestamp_str1, 1)
    m.addAirplane("jnsfu", 40.55, -3.55, False, 0, 70, timestamp_str2, 2)
    m.addAirplane("jnsfu", 40.56, -3.56, True, 0, 70, timestamp_str3, 3)
    m.addAirplane("jnsfu", 40.52, -3.53, True, 0, 90, timestamp_str4, 4)
    m.addAirplane("jnsfu", 40.70, -3.80, False, 0, 90, timestamp_str5, 3)
    m.addAirplane("jnsfu", 40.71, -3.82, False, 0, 10, timestamp_str6, 2)
    """
    for _, row in df_filtered.iterrows():
        m.addAirplane(row["icao"], row["lat"], row["lon"], row["ground"], row["direccion"], row["velocity"], row["datetime"], row["alt_feet"])

    print('SAVING')
    m.saveMap(file_path)
    m.reset()
    print('FINISHED')
    # Append timestamp to force browser to load fresh file
    return f"/assets/generated.html?t={int(time.time())}"

if __name__ == "__main__":
    app.run_server(debug=False)
