import folium
import pandas as pd
import webbrowser
import os


class MapVisualization:
    def __init__(self):
        self.radar = {"lat": 40.51, "lon": -3.53}
        self.pistas = [
            {"lat": 40.463, "lon": -3.554},
            {"lat": 40.473, "lon": -3.536},
            {"lat": 40.507, "lon": -3.574},
            {"lat": 40.507, "lon": -3.559},
        ]
        self.mapa = self.createMap()
        self.addRadar()
        self.addLandingStrips()

    def createMap(self):
        mapa = folium.Map(
            location=[self.radar["lat"], self.radar["lon"]], zoom_start=12
        )
        return mapa

    def addRadar(self):
        folium.Marker(
            location=[self.radar["lat"], self.radar["lon"]],
            tooltip=folium.Tooltip(
                f"""
                                            <div style="text-align: center;">
                                            <b>RADAR</b><br>
                                            Lat: {self.radar['lat']}<br>
                                            Lon: {self.radar['lon']}
                                        """,
                max_width=300,
            ),
            icon=folium.Icon(
                color="darkblue", icon="fa-solid fa-satellite-dish", prefix="fa"
            ),
        ).add_to(self.mapa)

    def createDescriptionLandingStrip(self, nombre_pista, latitud, longitud):
        return f"""
                        <div style="text-align: center;">
                        <b>PISTA {nombre_pista + 1}</b><br>
                        Lat: {latitud}<br>
                        Lon: {longitud}
                    """

    def addLandingStrip(self, nombre_pista, latitud, longitud):
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                self.createDescriptionLandingStrip(nombre_pista, latitud, longitud),
                max_width=300,
            ),
            icon=folium.Icon(
                color="green", icon="fa-solid fa-plane-arrival", prefix="fa"
            ),
        ).add_to(self.mapa)

    def addLandingStrips(self):
        for n_pista, pista in enumerate(self.pistas):
            self.addLandingStrip(n_pista, pista["lat"], pista["lon"])


    def createDescriptionAirplane(self, id_avion, latitud, longitud):
        return f"""
                        <div style="text-align: center;">
                        <b>ID {id_avion}</b><br>
                        Lat: {latitud}<br>
                        Lon: {longitud}
                    """
    def addAirplane(self, id_avion, latitud, longitud):
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                self.createDescriptionAirplane(id_avion, latitud, longitud),
                max_width=300,
            ),
            icon=folium.Icon(
                color="lightgray", icon="fa-solid fa-plane", prefix="fa"
            ),
        ).add_to(self.mapa)

    def saveMap(self, nombre_mapa):
        self.mapa.save(f"./mapas/{nombre_mapa}.html")

    def showMap(self, nombre_mapa):
        ruta = f"./mapas/{nombre_mapa}.html"
    
        if os.path.exists(ruta):
            webbrowser.open(f"file://{os.path.abspath(ruta)}")

        else:
            print("El mapa no existe")
        
