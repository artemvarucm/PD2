import folium
import folium.plugins
import pandas as pd
import math
import base64
from layers.airplanes import RoutesVelocity

m = folium.Map(location=[40.51, -3.53], zoom_start=12)

df = pd.read_csv("data/ex2/preprocess_mapa_mini.csv")
df = df[~df.lat.isna() & ~df.lon.isna()]

df['ts_kafka'] = pd.to_datetime(df['ts_kafka'], unit='ms').dt.strftime('%Y-%m-%dT%H:%M:%S')

# Lon, Lat order.
lines = [
    {
        "coordinates": df[df.icao == icao][['lon', 'lat']].values.tolist(),
        "dates": df[df.icao == icao]['ts_kafka'].values.tolist(),
        "color": df[df.icao == icao].velocity.map(lambda x: RoutesVelocity.get_color_by_speed(x) if x is not None else "green").values.tolist(),
        "popup": f"Avión: {icao}"
    }

    for icao in df.icao.unique()
]

with open("./assets/icons/airplane_air.svg", "r") as file:
    svg_air_data = file.read()

with open("./assets/icons/airplane_ground.svg", "r") as file:
    svg_ground_data = file.read()

def getIcon(onGround, svg_air_data, svg_ground_data):
    svg_data = svg_ground_data if onGround else svg_air_data
    return f"data:image/svg+xml;base64,{base64.b64encode(svg_data.encode()).decode()}"


features = [
    {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": line["coordinates"],
        },
        "properties": {
            "times": line["dates"],
            "icon": "marker",
            "iconstyle": {
                "iconUrl": getIcon(False, svg_air_data, svg_ground_data),
                "iconSize": [20, 20],
            },
            "popup": line["popup"],
            #"style": {
            #    "color": line["color"], # aqui podemos meter el color (velocidad)
            #    "weight": 2,
            #},
        },
    }
    for line in lines
]

t = folium.plugins.TimestampedGeoJson(
    {
        "type": "FeatureCollection",
        "features": features,
    },
    duration="PT1H", # los datos que han estado mostrados durante una hora, se eliminan
    period="PT1M",
    auto_play=True,
    add_last_point=True,
)
t.add_to(m)

m.show_in_browser()