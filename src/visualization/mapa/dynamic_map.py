import folium
import folium.plugins
import pandas as pd
import base64
import re
import math

class DynamicMap():
    def __init__(self, latitud=40.51, longitud=-3.53):
        self.map = folium.Map(location=[latitud, longitud], zoom_start=6)
        self.geo_features = []

    def getIcon(self, onGround, svg_air_data, svg_ground_data, angle):
        svg_data = svg_ground_data if onGround else svg_air_data
        svg_content = re.sub(r'(<svg[^>]*>)', r'\1\n  <g transform="rotate({} {} {})">'.format(angle * 180 / math.pi, 288, 256), svg_data)        
        svg_content = re.sub(r'(</svg>)', r'  </g>\n\1', svg_content)
        
        return f"data:image/svg+xml;base64,{base64.b64encode(svg_content.encode()).decode()}"

    def fillMap(self, df):
        filtro = (~df.lat.isna()) & (~df.lon.isna()) & (~df.ground.isna())
        df = df[filtro]
        df['ts_kafka'] = pd.to_datetime(df['ts_kafka'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
        self.fillAirplanes(df)
        self.fillTraces(df)

        t = folium.plugins.TimestampedGeoJson(
            {
                "type": "FeatureCollection",
                "features": self.geo_features,
            },
            duration="PT1M", # los datos que han estado mostrados durante una hora, se eliminan
            period="PT3M",
            auto_play=True,
            add_last_point=False,
        )
        t.add_to(self.map)
    
    def fillTraces(self, df):   
        trail_Size = 10
        for id in df.icao.unique():
            for time_index, time in enumerate(df[df.icao == id]['ts_kafka'].values.tolist()):
                points=df[df.icao == id][['lon', 'lat']].values.tolist()[:time_index+1][-trail_Size:]
                self.geo_features.append({
                    'type': "Feature",
                    'properties':{
                        'name': '',
                        'style': {'color': 'black', 'weight': 2},
                        'times': [time]*len(points)},

                    'geometry':{
                        'type': "LineString",
                        'coordinates': points
                    }
                })

    def fillAirplanes(self, df):
        with open("./assets/icons/airplane_air.svg", "r") as file:
            svg_air_data = file.read()

        with open("./assets/icons/airplane_ground.svg", "r") as file:
            svg_ground_data = file.read()

        for id in df.icao.unique():
            df_current = df[df.icao == id]
            for time in range((df.icao == id).sum()):

                self.geo_features.append({
                    'type': "Feature",
                    'properties': {
                        'icon': 'marker',
                        "iconstyle": {
                            "iconUrl": self.getIcon(df_current['ground'].values.tolist()[time], svg_air_data, svg_ground_data, df_current['direccion'].values.tolist()[time]),
                            "iconSize": [20, 20],
                        },
                        'popup': f"""
                            <b>ID: {id}</b><dd><dd> \
                            Callsign: {df_current['callsign'].values.tolist()[time]}<dd> \
                            Lat: {float(f'{df_current['lat'].values.tolist()[time]:.8g}')}<dd> \
                            Lon: {float(f'{df_current['lon'].values.tolist()[time]:.8g}')}<dd> \
                            Velocidad: {float(f'{float(df_current['velocity'].values.tolist()[time]):.5g}')} nudos<dd> \
                            Timestamp: {df_current['ts_kafka'].values.tolist()[time]}<dd> \
                            """,
                        'name': '',
                        'style': {'color': 'black', 'weight': 2},
                        'times': [df_current['ts_kafka'].values.tolist()[time]]
                        },

                    'geometry':{
                        'type': "MultiPoint",
                        # Lon, Lat order.
                        'coordinates': [df_current[['lon', 'lat']].values.tolist()[time]]
                        }
                })
    
    def saveMap(self, df, path):
        self.fillMap(df)
        self.map.save(path)