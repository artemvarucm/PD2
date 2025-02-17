import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import time
import pandas as pd
from static_map import StaticMap

app = dash.Dash(__name__)

# De donde sacamos los datos
df = pd.read_csv("data/ex2/preprocess_mapa_mini.csv")
df['ts_kafka'] = pd.to_datetime(df['ts_kafka'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')

# Layout
app.layout = html.Div([
    html.Br(),
    html.Button("Generate & Load HTML", id="generate-btn", n_clicks=0),
    html.Br(), html.Br(),
    html.Iframe(
        id="iframe",
        src="/assets/1.html",  # Pagina por defecto, se puede generar al inicio
        style={"width": "100%", "height": "500px"}
    ),
])

# Callback to generate HTML file and update iframe
@app.callback(
    Output("iframe", "src"),
    Input("generate-btn", "n_clicks"),
    prevent_initial_call=True
)
def generate_and_load(n_clicks):
    file_path = "src/visualization/mapa/assets/generated.html"
    m = StaticMap()
    ## añadir codigo aqui para el filtrado por ts_kafka

    ##
    for _, row in df.iterrows():
        if pd.notna(row["ground"]) and pd.notna(row["lat"]) and pd.notna(row["lon"]) and  row["ground"] is not None and row["lat"] is not None and row["lon"] is not None: #on ground
            m.addAirplane(row["icao"], row["lat"],row["lon"],row["ground"], row["direccion"], row["velocity"], row["ts_kafka"], row["alt_feet"])

    m.saveMap(file_path)
    # Append timestamp to force browser to load fresh file
    return f"/assets/generated.html?t={int(time.time())}"
    
if __name__ == "__main__":
    app.run_server(debug=False)
