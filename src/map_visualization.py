import folium
import webbrowser
import os
import time


class MapVisualization:
    def __init__(self):
        self.mapa = self.createMap()
        self.layerControl = folium.LayerControl(collapsed=False, sortLayers=True)

        self.radares = [{"nombre": "PRINCIPAL", "lat": 40.51, "lon": -3.53}]
        self.pistas = [
            {"nombre": "1", "lat": 40.463, "lon": -3.554},
            {"nombre": "2", "lat": 40.473, "lon": -3.536},
            {"nombre": "3", "lat": 40.507, "lon": -3.574},
            {"nombre": "4", "lat": 40.507, "lon": -3.559},
        ]

        self.aviones = set()
        self.layers = {
            "radares": {'capa': folium.FeatureGroup(name="Radares"), 'color': "darkblue"},
            "pistas": {'capa': folium.FeatureGroup(name="Pistas de Aterrizaje"), 'color': "green"},
            "aviones": {'capa': folium.FeatureGroup(name="Aviones"), 'color': "lightgray", 'añadida': False},
        }
        
        self.initializeMap()

    def initializeMap(self):
        self.paintRadars()
        self.paintLandingStrips()
        self.layers['aviones']['capa'].add_to(self.mapa)
        self.layerControl.add_to(self.mapa)

    def createMap(self, latitud=40.51, longitud=-3.53):
        mapa = folium.Map(
            location=[latitud, longitud], zoom_start=12
        )
        return mapa
    
    # PAINT RADARES
    def paintRadar(self, nombre_radar, latitud, longitud):
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                f"""
                                            <div style="text-align: center;">
                                            <b>RADAR {nombre_radar}</b><br>
                                            Lat: {latitud}<br>
                                            Lon: {longitud}
                                        """,
                max_width=300,
            ),
            icon=folium.Icon(
                color=self.layers['radares']['color'], icon="fa-solid fa-satellite-dish", prefix="fa"
            ),
        ).add_to(self.layers['radares']['capa'])        
    
    def paintRadars(self):
        for radar in self.radares:
            self.paintRadar(radar['nombre'], radar['lat'], radar['lon'])
        
        self.layers['radares']['capa'].add_to(self.mapa)


    # PAINT PISTAS ATERRIZAJE
    def createDescriptionLandingStrip(self, nombre_pista, latitud, longitud):
        return f"""
                        <div style="text-align: center;">
                        <b>PISTA {nombre_pista}</b><br>
                        Lat: {latitud}<br>
                        Lon: {longitud}
                    """

    def paintLandingStrip(self, nombre_pista, latitud, longitud):
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                self.createDescriptionLandingStrip(nombre_pista, latitud, longitud),
                max_width=300,
            ),
            icon=folium.Icon(
                color=self.layers['pistas']['color'], icon="fa-solid fa-plane-arrival", prefix="fa"
            ),
        ).add_to(self.layers['pistas']['capa'])

        
    def paintLandingStrips(self):
        for pista in self.pistas:
            self.paintLandingStrip(pista['nombre'], pista["lat"], pista["lon"])
        
        self.layers['pistas']['capa'].add_to(self.mapa)


    # PINTAR AVIONES
    def createDescriptionAirplane(self, id_avion, latitud, longitud):
        return f"""
                        <div style="text-align: center;">
                        <b>ID {id_avion}</b><br>
                        Lat: {latitud}<br>
                        Lon: {longitud}
                    """

    def paintAirplane(self, id_avion, latitud, longitud):
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                self.createDescriptionAirplane(id_avion, latitud, longitud),
                max_width=300,
            ),
            icon=folium.Icon(color=self.layers['aviones']['color'], icon="fa-solid fa-plane", prefix="fa"),
        ).add_to(self.layers['aviones']['capa'])

    def saveMap(self, nombre_mapa):
        self.mapa.save(f"./mapas/{nombre_mapa}.html")

    def showMap(self, nombre_mapa=None):
        if nombre_mapa is None:
            nombre_mapa = time.strftime("%d-%m-%Y_%H-%M-%S")
        
        if not os.path.exists(f"./mapas/{nombre_mapa}.html"):
            self.saveMap(nombre_mapa)
        webbrowser.open(f"file://{os.path.abspath(f"./mapas/{nombre_mapa}.html")}")


"""
m = MapVisualization()
m.showMap()
time.sleep(1)
m.paintAirplane("34", 40.53, -3.56)
m.showMap()
time.sleep(1)
m.paintAirplane("34", 40.59, -3.70)
m.showMap()
time.sleep(1)
m.paintAirplane("34", 40.57, -3.70)
m.showMap()"""

