import folium
from .routes import Routes
from datetime import datetime


class RoutesVelocity(Routes):
    capa_rutas = folium.FeatureGroup(name="Rutas Velocidad")
    ruta_aviones = dict()

    @staticmethod
    def paintRoute(id_avion):
        """Pinta la ruta del avión. Tiene en cuenta la velocidad del avión en cada tramo para utilizar un color u otro"""
        #rutas = ["ruta_lenta", "ruta_rapida", "ruta_media"]
        #colores = {"ruta_rapida": "red", "ruta_media": "orange", "ruta_lenta": "green"}

        for i in range(1, len(RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"])):
            lat1, lon1, vel1, callsign1 = RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"][i-1]
            lat2, lon2, vel2, callsign2 = RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"][i]
            color = RoutesVelocity.get_color_by_speed(vel1)
            folium.PolyLine(
                [(lat1, lon1), (lat2, lon2)],
                color=color,
                weight=2,
                opacity=0.8,
                tooltip=f"Trayectoria Avión {id_avion}. Callsign: {callsign1}",
                #class_name=f"trayectoria trayectoria-{id_avion}",
                #popup=f"Velocidad: {vel1} nudos -- Altura {altura}",
            ).add_to(RoutesVelocity.capa_rutas)

    @staticmethod
    def sameRoute(id_avion, callsign):
        return RoutesVelocity.ruta_aviones[id_avion]['last_callsign'] == callsign

    @staticmethod
    def addLocation(id_avion, latitud, longitud, **kwargs):
        timestamp, velocidad, onGround, callsign = (
            kwargs.get("timestamp"),
            kwargs.get("velocidad", 0),
            kwargs.get("onGround"),
            kwargs.get("callsign"),
        )

        if (id_avion not in RoutesVelocity.ruta_aviones) or (
            not RoutesVelocity.sameRoute(id_avion, timestamp)
        ):
            RoutesVelocity.ruta_aviones[id_avion] = {
                "rutas": {
                    "ruta_principal": [],
                    #"ruta_rapida": [],
                    #"ruta_media": [],
                    #"ruta_lenta": [],
                    "ultima_velocidad": None,
                },
                "last_callsign": None
            }

        RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"].append(
            (round(latitud, 3), round(longitud, 3), velocidad, callsign)
        )  # Se añade la ubicación a su ruta
        RoutesVelocity.ruta_aviones[id_avion]['last_callsign'] = callsign


    @staticmethod
    def get_color_by_speed(velocity):
        if velocity < 300:
            return "red"
        elif velocity < 450:
            return "yellow"
        else:
            return "green"

    @staticmethod
    def deleteAirplane(id_avion):
        """Borra el avión"""
        if id_avion in RoutesVelocity.ruta_aviones:
            del RoutesVelocity.ruta_aviones[id_avion]

    @staticmethod
    def reset():
        RoutesVelocity.ruta_aviones = dict()
        RoutesVelocity.capa_rutas = folium.FeatureGroup(name="Rutas Velocidad")
