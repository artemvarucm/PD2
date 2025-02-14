import folium

class Radars:
    radares = [{"nombre": "PRINCIPAL", "lat": 40.51, "lon": -3.53}]
    capa = folium.FeatureGroup(name="Radares")
    color = "darkblue"

    @staticmethod
    def createDescriptionRadar(nombre_radar, latitud, longitud):
        """Crea el tooltip del radar"""
        return f"""
                        <div style="text-align: center;">
                        <b>RADAR {nombre_radar}</b><br>
                        Lat: {latitud}<br>
                        Lon: {longitud}
                    """
    
    @staticmethod
    def paintRadar(nombre_radar, latitud, longitud):
        """Pinta el radar en el mapa"""
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                Radars.createDescriptionRadar(nombre_radar, latitud, longitud),
                max_width=300,
            ),
            icon=folium.Icon(
                color=Radars.color,
                icon="fa-solid fa-satellite-dish",
                prefix="fa",
            ),
        ).add_to(Radars.capa)

    @staticmethod
    def addRadarsLayer(mapa):
        """Pinta todos los radares en el mapa"""
        for radar in Radars.radares:
            Radars.paintRadar(radar["nombre"], radar["lat"], radar["lon"])
        Radars.capa.add_to(mapa)