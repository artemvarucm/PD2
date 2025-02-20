import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import time
import pandas as pd
from static_map import StaticMap

app = dash.Dash(__name__)

MAX_HOURS_RANGE = 5 # para evitar problemas de rendimiento

# Eliminamos filas sin latitud, longitud y ground
df = pd.read_csv("data/ex2/preprocess_mapa_callsign.csv")
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
    html.H3(
        id="title-dynamic",
        children="ANIMACIÓN DEL MAPA",
        style={
            'display': 'flex', 
            'justify-content': 'center', 
            'align-items': 'center',
        }
    ),
    html.Iframe(
        id="iframe_dyn_map",
        src="/assets/mapa_dinamico.html",
        style={"width": "100%", "height": "400px"}
    ),
    html.H3(
        id="title-dynamic",
        children=f"FILTRAR MOMENTOS DEL MAPA (RANGO MÁXIMO {MAX_HOURS_RANGE} HORAS)",
        style={
            'display': 'flex', 
            'justify-content': 'center', 
            'align-items': 'center',
        }
    ),
    html.Br(),
    dcc.RangeSlider(
        id="slider-param",
        tooltip = {
            "always_visible": True,
            "placement": "top",
            "transform": "modulo24"
        },
        min=0,
        max=len(date_range) - 1,
        step=1,
        marks={i: {"label": date.strftime("%m-%d %H:%M"), "style": {"font-size": "16px"}} for i, date in enumerate(date_range) if date.hour == 0},
        value=[0, MAX_HOURS_RANGE]
    ),
    html.Br(),
    html.H3(
        id="slider-output",
        style={
            'display': 'flex', 
            'justify-content': 'center', 
            'align-items': 'center',
        }
    ),
    html.H3(
        id="validation",
        style={'color': 'red'}
    ),
    html.Br(),
    html.Iframe(
        id="iframe_map",
        #src="/assets/intro.html",  # Default page
        style={"width": "100%", "height": "700px"}
    ),
])

# Callback to generate and update the map
@app.callback(
    [Output("iframe_map", "src"), Output("slider-output", "children"), Output("validation", "children")],
    [Input("slider-param", "value")],
    #prevent_initial_call=True
)
def generate_and_load(value_range):
    lowerBound = decodeRangeValues[value_range[0]]
    upperBound = decodeRangeValues[value_range[1]]

    lowerBound_ts = pd.Timestamp(lowerBound).timestamp() * 1000
    upperBound_ts = pd.Timestamp(upperBound).timestamp() * 1000

    if (value_range[1] - value_range[0] > MAX_HOURS_RANGE):
        return f"", f"MAPA DE VUELOS DESDE {lowerBound} HASTA {upperBound}", f"El rango de horas no puede superar {MAX_HOURS_RANGE} para simplificar la visualización."

    # Filtramos dataframe
    print('FILTERING')
    filter_bounds = (df['ts_kafka'] >= lowerBound_ts) & (df['ts_kafka'] <= upperBound_ts)
    df_filtered = df[filter_bounds]
    print(f'FILTERED {filter_bounds.sum()} ROWS')
    # Creamos el mapa
    file_path = "src/visualization/mapa/assets/generated.html"

    m = StaticMap()
    print('ADDING AIRPLANES')

    print('SAVING')
    m.saveMap(df_filtered, file_path)
    m.reset()
    print('FINISHED')
    # Append timestamp to force browser to load fresh file
    return f"/assets/generated.html?t={int(time.time())}", f"MAPA DE VUELOS DESDE {lowerBound} HASTA {upperBound}", ""

if __name__ == "__main__":
    app.run_server(debug=False)
