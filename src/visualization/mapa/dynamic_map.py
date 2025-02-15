import folium
import folium.plugins
import pandas as pd
m = folium.Map(location=[40.51, -3.53], zoom_start=12)

df = pd.read_csv("data/ex2/preprocess_mapa_mini.csv")
df = df[~df.lat.isna() & ~df.lon.isna()]

df['ts_kafka'] = pd.to_datetime(df['ts_kafka'], unit='ms').dt.strftime('%Y-%m-%dT%H:%M:%S')

# Lon, Lat order.
lines = [
    {
        "coordinates": df[df.icao == icao][['lon', 'lat']].values.tolist(),
        "dates": df[df.icao == icao]['ts_kafka'].values.tolist(),
        "color": "red",
    }

    for icao in df.icao.unique()
]

features = [
    {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": line["coordinates"],
        },
        "properties": {
            "times": line["dates"],
            "icon": "plane",
            "style": {
                "color": line["color"],
                "weight": line["weight"] if "weight" in line else 5,
            },
        },
    }
    for line in lines
]

folium.plugins.TimestampedGeoJson(
    {
        "type": "FeatureCollection",
        "features": features,
    },
    period="PT1M",
    auto_play=True,
    add_last_point=True,
).add_to(m)

m.show_in_browser()