import folium, branca, plotly.express as px, numpy as np
from .routes_velocity import RoutesVelocity
from .routes_history import RoutesHistory
import math
import json

class Airplanes:
    capa_aviones = folium.FeatureGroup(name="Aviones")
    aviones = dict()

    @staticmethod
    def createDescriptionVehicle(id_avion, latitud, longitud, timestamp, velocidad=None):
        """Crea el tooltip del vehiculo"""
        if not velocidad:
            velocidad = "-"
        return f"""
                        <div style="text-align: center;">
                        <b>ID: {id_avion}</b><br>
                        Lat: {round(latitud,2)}<br>
                        Lon: {round(longitud,2)}<br>
                        Velocidad: {velocidad} nudos<br>
                        Timestamp: {timestamp}
                    """

    @staticmethod
    def vehicleIcon(onGround, rotation, vehicle_type=None):
        """Devuelve el icono correspondiente según el vehiculo esté en el aire o en tierra"""
        if vehicle_type == "Rotorcraft":
             if onGround:
                path_icon = "./assets/icons/helicopter_ground.svg"
             else:
                path_icon = "./assets/icons/helicopter_air.svg"
        else:  
            if onGround:
                path_icon = "./assets/icons/airplane_ground.svg"
            else:
                path_icon = "./assets/icons/airplane_air.svg"
       
        with open(path_icon, "r") as file:
            svg_data = file.read()

        icon = folium.DivIcon(html=f"<div style='width:16px;height:16px; transform: rotate({rotation * 180 / math.pi}deg);'>{svg_data}</div>")


        return icon

    @staticmethod
    def generateImageHeights(id_avion):
        """Genera la gráfica de alturas del vehiculo"""
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
    def paintVehicle(id_avion, latitud, longitud, on_ground, rotation, timestamp, velocidad, vehicle_type):
        """Pinta el vehiculo en el mapa"""

        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                Airplanes.createDescriptionVehicle(id_avion, latitud, longitud, timestamp, velocidad),
                max_width=300,
            ),
            icao=id_avion,
            popup=Airplanes.generateImageHeights(id_avion),
            icon=Airplanes.vehicleIcon(on_ground, rotation, vehicle_type),
        ).add_to(Airplanes.capa_aviones)

    @staticmethod
    def paintVehicles(mapa):
        """Pinta todos los vehiculos en el mapa. Además, también pinta sus rutas"""
        for id_avion in Airplanes.aviones:
            Airplanes.paintVehicle(
                id_avion,
                RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"][-1][0],
                RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"][-1][1],
                Airplanes.aviones[id_avion]["onGround"],
                Airplanes.aviones[id_avion]["rotacion"],
                Airplanes.aviones[id_avion]["timestamp"], 
                Airplanes.aviones[id_avion]["velocidad"],
                Airplanes.aviones[id_avion]["vehicle_type"]
            )
            RoutesVelocity.paintRoute(id_avion)
            RoutesHistory.paintRoute(id_avion)

        Airplanes.capa_aviones.add_to(mapa)
        RoutesHistory.capa_rutas.add_to(mapa)
        RoutesVelocity.capa_rutas.add_to(mapa)

    # GESTIÓN DE LOS AVIONES QUE SE VAN A VISUALIZAR
    @staticmethod
    def addVehicle(id_avion, latitud, longitud, on_ground, rotacion, velocidad, timestamp, altura, callsign, vehicle_type):
        """Añade el vehiculo para que pueda ser pintado en el mapa"""
        if id_avion not in Airplanes.aviones:
            Airplanes.aviones[id_avion] = {
                "alturas": [],
                "onGround": None,
                "rotacion": None,
                "timestamp": None,
                "velocidad": None,
                "vehicle_type": None
            }
        Airplanes.aviones[id_avion]["onGround"] = on_ground
        Airplanes.aviones[id_avion]["rotacion"] = rotacion
        Airplanes.aviones[id_avion]["timestamp"] = timestamp
        Airplanes.aviones[id_avion]["velocidad"] = velocidad
        Airplanes.aviones[id_avion]["vehicle_type"] = vehicle_type

        if altura is not None:
            Airplanes.aviones[id_avion]["alturas"].append(altura)

        RoutesVelocity.addLocation(
            id_avion=id_avion,
            latitud=latitud,
            longitud=longitud,
            timestamp=timestamp,
            onGround=on_ground,
            velocidad=velocidad,
            callsign=callsign
        )
        RoutesHistory.addLocation(
            id_avion=id_avion,
            latitud=latitud,
            longitud=longitud,
            timestamp=timestamp,
            onGround=on_ground,
            callsign=callsign
        )

    @staticmethod
    def deleteVehicle(id_avion):
        """Borra el vehiculo"""
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

    @staticmethod
    def script_show_one_route_on_click():
        """Script JavaScript (funcionalidad de selección y ocultación de elementos)"""
        scriptContent = None
        
        with open("./assets/js/plane_click.js", "r") as file:
            scriptContent = file.read()

        scriptContent = scriptContent.replace('{{trayectoriasLengths}}', json.dumps([len(avion["rutas"]["ruta_principal"]) - 1 for avion in RoutesVelocity.ruta_aviones.values()]))

        return f"<script>{scriptContent}</script>"