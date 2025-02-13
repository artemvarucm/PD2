import folium
import webbrowser
import os
import time
import numpy as np


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

        self.layers = {
            'radar': {'capa': folium.FeatureGroup(name="Radares"), 'color': "darkblue"},
            'pistas': {'capa': folium.FeatureGroup(name="Pistas de Aterrizaje"), 'color': "green"},
            'aviones': folium.FeatureGroup(name="Aviones"),
            'rutas': folium.FeatureGroup(name="Rutas")
        }

        self.aviones = dict()
        
        self.initializeMap(all=True)

    def addLayers(self):
        self.layers['radar']['capa'].add_to(self.mapa)
        self.layers['pistas']['capa'].add_to(self.mapa)
        self.layers['aviones'].add_to(self.mapa)
        self.layers['rutas'].add_to(self.mapa)

    def initializeMap(self, all=False):
        if all:
            self.paintRadars()
            self.paintLandingStrips()
        else:
            self.layers['aviones'] = folium.FeatureGroup(name="Aviones")
            self.layers['rutas'] = folium.FeatureGroup(name="Rutas")
        
        self.addLayers()
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
                color=self.layers['radar']['color'], icon="fa-solid fa-satellite-dish", prefix="fa"
            ),
        ).add_to(self.layers['radar']['capa'])        
    
    def paintRadars(self):
        for radar in self.radares:
            self.paintRadar(radar['nombre'], radar['lat'], radar['lon'])


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

    # PINTAR AVIONES
    def createDescriptionAirplane(self, id_avion, latitud, longitud, velocidad=None):
        if not velocidad:
            velocidad="-"
        return f"""
                        <div style="text-align: center;">
                        <b>ID: {id_avion}</b><br>
                        Lat: {round(latitud,2)}<br>
                        Lon: {round(longitud,2)}<br>
                        Velocidad: {velocidad} km/h
                    """

    def airplaneIcon(self, onGroung):
        if onGroung:
            path_icon = "./assets/icons/airplane_ground.png"
        else:
            path_icon = "./assets/icons/airplane_air.png"

        icon = folium.CustomIcon(
            path_icon,
            icon_size=(25, 25),
        )

        return icon
    
    def paintAirplane(self, id_avion, latitud, longitud, on_ground):
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                self.createDescriptionAirplane(id_avion, latitud, longitud),
                max_width=300,
            ),
            icon=self.airplaneIcon(on_ground),
        ).add_to(self.layers['aviones'])
    
    def paintAirplanes(self):
        for id_avion in self.aviones:
            self.paintAirplane(id_avion, self.aviones[id_avion]['ruta'][-1][0], self.aviones[id_avion]['ruta'][-1][1], self.aviones[id_avion]['onGround'])
            self.paintRoute(self.aviones[id_avion]['ruta'])
        
        self.layers['aviones'].add_to(self.mapa)
        self.layers['rutas'].add_to(self.mapa)

    def addAirplane(self, id_avion, latitud, longitud, on_ground, velocidad=0):
        if id_avion not in self.aviones:
            self.aviones[id_avion] = {'ruta':[], 'velocidad': [], 'onGround':None}
        
        self.aviones[id_avion]['ruta'].append((round(latitud,3), round(longitud,3)))
        self.aviones[id_avion]['ruta'].append((round(latitud,3), round(longitud,3)))
        self.aviones[id_avion]['onGround'] = on_ground

    # PINTAR RUTAS DE AVIONES
    def paintRoute(self, ruta):
        folium.PolyLine(ruta, color="blue", weight=2.5, opacity=1).add_to(self.layers['rutas'])
        """
        colors = ["blue", "red", "green", "purple", "orange", "yellow"]
        
        # Recorrer los puntos de la ruta de dos en dos para dibujar los segmentos
        for i in range(len(ruta) - 1):
            color = random.choice(colors)  # Elige un color aleatorio
            folium.PolyLine(
                [ruta[i], ruta[i + 1]], color=color, weight=2.5, opacity=1
            ).add_to(self.layers['rutas'])"""

    def saveMap(self, nombre_mapa):
        self.mapa.save(f"./mapas/{nombre_mapa}.html")

    def showMap(self, nombre_mapa=None):
        self.paintAirplanes()

        if nombre_mapa is None:
            nombre_mapa = time.strftime("%d-%m-%Y_%H-%M-%S")
        
        if not os.path.exists(f"./mapas/{nombre_mapa}.html"):
            self.saveMap(nombre_mapa)
        webbrowser.open(f"file://{os.path.abspath(f"./mapas/{nombre_mapa}.html")}")

        self.reset()

    def reset(self):
        self.mapa = self.createMap()
        self.initializeMap(all=False)


m = MapVisualization()
import random
import time
import pandas as pd

df = pd.read_csv("pruebaCSV5.csv", sep=",")
print(df.shape)
#df = df.loc[:50]
for i, row in df.iterrows():
    print(f"ON GROOUND {row["ground"]}-- LAT -- {row["lat"]} LON -- {row["lon"]}")

    if pd.notna(row["ground"]) and pd.notna(row["lat"]) and pd.notna(row["lon"]): #on ground
        m.addAirplane(row["icao"], row["lat"],row["lon"],row["ground"])
    #elif not ["ground"] and row["airborne_pos_lat"] is not None and row["airborne_pos_lon"] is not None:        
    #    m.addAirplane(row["icao"], row["airborne_pos_lat"],row["airborne_pos_lon"],row["ground"])
    
m.showMap()



