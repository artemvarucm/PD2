import folium, branca, plotly.express as px
from .routes import Routes

class Airplanes:
    capa_aviones = folium.FeatureGroup(name="Aviones")
    aviones = dict()

    @staticmethod
    def createDescriptionAirplane(id_avion, latitud, longitud, velocidad=None):
        """Crea el tooltip del avión"""
        if not velocidad:
            velocidad = "-"
        return f"""
                        <div style="text-align: center;">
                        <b>ID: {id_avion}</b><br>
                        Lat: {round(latitud,2)}<br>
                        Lon: {round(longitud,2)}<br>
                        Velocidad: {velocidad} km/h
                    """
    
    @staticmethod
    def airplaneIcon(onGroung):
        """Devuelve el icono correspondiente según el avión esté en el aire o en tierra"""
        if onGroung:
            path_icon = "./assets/icons/airplane_ground.png"
        else:
            path_icon = "./assets/icons/airplane_air.png"

        icon = folium.CustomIcon(
            path_icon,
            icon_size=(25, 25),
        )

        return icon

    @staticmethod
    def generateImageHeights(id_avion):
        fig = px.line(x=range(len(Airplanes.aviones[id_avion]["alturas"])), y=Airplanes.aviones[id_avion]["alturas"], title='Alturas del avión con el paso del tiempo')

        html = fig.to_html(full_html=False, include_plotlyjs='cdn')

        iframe = branca.element.IFrame(html=html, width=500, height=300)
        popup = folium.Popup(iframe, max_width=500)
        return popup

    @staticmethod
    def paintAirplane(id_avion, latitud, longitud, on_ground):
        """Pinta el avión en el mapa"""

        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                Airplanes.createDescriptionAirplane(id_avion, latitud, longitud),
                max_width=300,
            ),
            popup=Airplanes.generateImageHeights(id_avion),
            icon=Airplanes.airplaneIcon(on_ground),
        ).add_to(Airplanes.capa_aviones)

    @staticmethod
    def paintAirplanes(mapa):
        """Pinta todos los aviones en el mapa. Además, también pinta sus rutas"""
        for id_avion in Airplanes.aviones:
            Airplanes.paintAirplane(
                id_avion,
                Routes.ruta_aviones[id_avion]["rutas"]["ruta_principal"][-1][0],
                Routes.ruta_aviones[id_avion]["rutas"]["ruta_principal"][-1][1],
                Airplanes.aviones[id_avion]["onGround"],
            )
            Routes.paintRoute(id_avion)

        Airplanes.capa_aviones.add_to(mapa)
        Routes.capa_rutas.add_to(mapa)
   
    # GESTIÓN DE LOS AVIONES QUE SE VAN A VISUALIZAR
    @staticmethod
    def addAirplane(id_avion, latitud, longitud, on_ground, velocidad, altura=None):
        """Añade el avión para que pueda ser pintado en el mapa"""

        if (id_avion not in Airplanes.aviones):  
            Airplanes.aviones[id_avion] = {
                "alturas": [],
                "onGround": None,
            }
        Airplanes.aviones[id_avion]["onGround"] = on_ground
        if altura is not None:
            Airplanes.aviones[id_avion]["alturas"].append(altura)
        
        Routes.addLocation(id_avion, latitud, longitud, velocidad)

    @staticmethod
    def deleteAirplane(id_avion):
        """Borra el avión"""
        if id_avion in Airplanes.aviones:
            del Airplanes.aviones[id_avion]
        Routes.deleteAirplane(id_avion)
        
    
    @staticmethod
    def reset():
        Airplanes.aviones = dict()
        Airplanes.capa_aviones = folium.FeatureGroup(name="Aviones")
        Routes.reset()
        