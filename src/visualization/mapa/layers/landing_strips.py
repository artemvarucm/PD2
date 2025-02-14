import folium

class LandingStrips:
    pistas = [
            {"nombre": "1", "lat": 40.463, "lon": -3.554},
            {"nombre": "2", "lat": 40.473, "lon": -3.536},
            {"nombre": "3", "lat": 40.507, "lon": -3.574},
            {"nombre": "4", "lat": 40.507, "lon": -3.559},
        ]
    capa = folium.FeatureGroup(name="Pistas de Aterrizaje")
    color = "green"

    @staticmethod
    def createDescriptionLandingStrip(nombre_pista, latitud, longitud):
        """Crea el tooltip de la pista de aterrizaje"""
        return f"""
                        <div style="text-align: center;">
                        <b>PISTA {nombre_pista}</b><br>
                        Lat: {latitud}<br>
                        Lon: {longitud}
                    """
    
    @staticmethod
    def paintLandingStrip(nombre_pista, latitud, longitud):
        """Pinta la pista de aterrizaje en el mapa"""
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                LandingStrips.createDescriptionLandingStrip(nombre_pista, latitud, longitud),
                max_width=300,
            ),
            icon=folium.Icon(
                color=LandingStrips.color,
                icon="fa-solid fa-plane-arrival",
                prefix="fa",
            ),
        ).add_to(LandingStrips.capa)

    @staticmethod
    def addLandingStripsLayers(mapa):
        """Pinta las pistas de aterrizaje en el mapa"""
        for pista in LandingStrips.pistas:
            LandingStrips.paintLandingStrip(pista["nombre"], pista["lat"], pista["lon"])
        LandingStrips.capa.add_to(mapa)