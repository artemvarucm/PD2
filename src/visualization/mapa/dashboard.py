import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import time
import pandas as pd
from static_map import StaticMap
from dynamic_map import DynamicMap

app = dash.Dash(__name__)

MAX_HOURS_RANGE = 2 # para evitar problemas de rendimiento

df_static = pd.read_csv("data/ex2/preprocess_mapa_callsign.csv") # cada 5 min, se usa en estático por rendimiento
df_dynamic = pd.read_csv("data/ex2/preprocess_mapa_callsign_1_min.csv") # cada 30 seg, se usa en dinámico para un vuelo más suave

# Ordenamos de pasado a futuro (redundante)
df_static = df_static.sort_values(by='ts_kafka', ascending=True)
df_dynamic = df_dynamic.sort_values(by='ts_kafka', ascending=True)

# Para seleccionar el rango de fechas (desde 00:00 fecha min a fecha max 23:00)
df_static['date'] = pd.to_datetime(df_static['ts_kafka'], unit='ms').dt.strftime('%Y-%m-%d')
date_range = pd.date_range(start=df_static.iloc[0]['date'], end=str(df_static.iloc[-1]['date']) + " 23:00", freq="h")
decodeRangeValues = {i: date for i, date in enumerate(date_range)}

app.layout = html.Div([
    html.H3(
        id="title-dynamic",
        children=f"FILTRADO POR TIEMPO (RANGO MÁXIMO {MAX_HOURS_RANGE} HORAS)",
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
    dcc.RadioItems(
        id='toggle-map-type',
        options=[
            {'label': 'ANIMADO', 'value': 'dynamic'},
            {'label': 'ESTÁTICO', 'value': 'static'}
        ],
        style={
            'display': 'flex', 
            'justify-content': 'center', 
            'align-items': 'center',
        },
        value='dynamic',
        inline=True
    ),
    html.Iframe(
        id="iframe_dynamic_map",
        style={'width': '100%', 'height': '600px'}
    ),
    html.Br(),
    html.Iframe(
        id="iframe_static_map",
        style={'width': '100%', 'height': '600px', 'display': 'none'}
    ),
    html.Img(src="/assets/leyenda.png", style={"width": "30%", "display": "block", "margin": "auto"})
])

@app.callback(
    [Output("slider-output", "children"), Output("validation", "children")],
    [Input("slider-param", "value")]
)
def updateTitle(value_range):
    lowerBound = decodeRangeValues[value_range[0]]
    upperBound = decodeRangeValues[value_range[1]]

    sliderOutput = f"MAPA DE VUELOS DESDE {lowerBound} HASTA {upperBound}"
    validationMsg = ""

    if (value_range[1] - value_range[0] > MAX_HOURS_RANGE):
        validationMsg = f"El rango de horas no puede superar {MAX_HOURS_RANGE} para simplificar la visualización."
    
    return sliderOutput, validationMsg


@app.callback(
    Output("iframe_static_map", "src"),
    [Input("slider-param", "value")]
)
def static_map_draw(value_range):
    if (value_range[1] - value_range[0] > MAX_HOURS_RANGE):
        return ""
    lowerBound = decodeRangeValues[value_range[0]]
    upperBound = decodeRangeValues[value_range[1]]
    lowerBound_ts = pd.Timestamp(lowerBound).timestamp() * 1000
    upperBound_ts = pd.Timestamp(upperBound).timestamp() * 1000
    
    # creamos el mapa estatico
    filter_bounds = (df_static['ts_kafka'] >= lowerBound_ts) & (df_static['ts_kafka'] <= upperBound_ts)
    df_filtered = df_static[filter_bounds]

    stat = StaticMap()
    static_file_path = "src/visualization/mapa/assets/generated_static.html"
    stat.saveMap(df_filtered, static_file_path)
    stat.reset()

    return f"/assets/generated_static.html?t={int(time.time())}"

@app.callback(
    Output("iframe_dynamic_map", "src"),
    [Input("slider-param", "value")],
)
def dynamic_map_draw(value_range):
    if (value_range[1] - value_range[0] > MAX_HOURS_RANGE):
        return ""

    lowerBound = decodeRangeValues[value_range[0]]
    upperBound = decodeRangeValues[value_range[1]]
    lowerBound_ts = pd.Timestamp(lowerBound).timestamp() * 1000
    upperBound_ts = pd.Timestamp(upperBound).timestamp() * 1000

    # para el dinamico usamos otros datos
    dyn = DynamicMap()
    filter_bounds = (df_dynamic['ts_kafka'] >= lowerBound_ts) & (df_dynamic['ts_kafka'] <= upperBound_ts)
    df_filtered = df_dynamic[filter_bounds]
    dynamic_file_path = "src/visualization/mapa/assets/generated_dynamic.html"
    dyn.saveMap(df_filtered, dynamic_file_path)

    return f"/assets/generated_dynamic.html?t={int(time.time())}"

@app.callback(
    [Output('iframe_static_map', 'style'), Output('iframe_dynamic_map', 'style')],
    Input('toggle-map-type', 'value')
)
def toggle_iframes(selected_value):
    if selected_value == 'static':
        return {'width': '100%', 'height': '500px'}, {'width': '100%', 'height': '500px', 'display': 'none'}
    else:
        return {'width': '100%', 'height': '500px', 'display': 'none'}, {'width': '100%', 'height': '500px'}


if __name__ == "__main__":
    app.run_server(debug=False)
