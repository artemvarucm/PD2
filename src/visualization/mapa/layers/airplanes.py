import folium, branca, plotly.express as px, numpy as np
from .routes_velocity import RoutesVelocity
from .routes_history import RoutesHistory


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
        x = np.arange(len(Airplanes.aviones[id_avion]["alturas"]))
        y = Airplanes.aviones[id_avion]["alturas"]
        fig = px.line(x=x, y=y, width=600, height=400, markers=True)
        fig.update_layout(
            # margin=dict(l=100, r=100, t=100, b=100),
            title_text="Alturas del avión con el paso del tiempo",
            title_x=0.5,
            yaxis_title="Altura",
            yaxis=dict(showgrid=False),
            xaxis_title="Nº Mensaje",
            xaxis=dict(tickmode="array", tickvals=x, ticktext=x, showgrid=False),
            font=dict(size=12, color="black"),
        )

        html = fig.to_html(full_html=False, include_plotlyjs="cdn")

        iframe = branca.element.IFrame(html=html, width=620, height=420)
        popup = folium.Popup(iframe)
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
            icao=id_avion,
            popup=Airplanes.generateImageHeights(id_avion),
            icon=Airplanes.airplaneIcon(on_ground),
        ).add_to(Airplanes.capa_aviones)

    @staticmethod
    def paintAirplanes(mapa):
        """Pinta todos los aviones en el mapa. Además, también pinta sus rutas"""
        for id_avion in Airplanes.aviones:
            Airplanes.paintAirplane(
                id_avion,
                RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"][-1][0],
                RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"][-1][1],
                Airplanes.aviones[id_avion]["onGround"],
            )
            RoutesVelocity.paintRoute(id_avion)
            RoutesHistory.paintRoute(id_avion)

        Airplanes.capa_aviones.add_to(mapa)
        RoutesHistory.capa_rutas.add_to(mapa)
        RoutesVelocity.capa_rutas.add_to(mapa)

    # GESTIÓN DE LOS AVIONES QUE SE VAN A VISUALIZAR
    @staticmethod
    def addAirplane(
        id_avion, latitud, longitud, on_ground, velocidad, timestamp, altura=None
    ):
        """Añade el avión para que pueda ser pintado en el mapa"""
        if id_avion not in Airplanes.aviones:
            Airplanes.aviones[id_avion] = {
                "alturas": [],
                "onGround": None,
            }
        Airplanes.aviones[id_avion]["onGround"] = on_ground
        if altura is not None:
            Airplanes.aviones[id_avion]["alturas"].append(altura)

        RoutesVelocity.addLocation(
            id_avion=id_avion,
            latitud=latitud,
            longitud=longitud,
            timestamp=timestamp,
            onGround=on_ground,
            velocidad=velocidad,
        )
        RoutesHistory.addLocation(
            id_avion=id_avion,
            latitud=latitud,
            longitud=longitud,
            timestamp=timestamp,
            onGround=on_ground,
        )

    @staticmethod
    def deleteAirplane(id_avion):
        """Borra el avión"""
        if id_avion in Airplanes.aviones:
            del Airplanes.aviones[id_avion]
        RoutesVelocity.deleteAirplane(id_avion)
        RoutesHistory.deleteAirplane(id_avion)

    @staticmethod
    def reset():
        Airplanes.aviones = dict()
        Airplanes.capa_aviones = folium.FeatureGroup(name="Aviones")
        RoutesVelocity.reset()
        RoutesHistory.reset()
