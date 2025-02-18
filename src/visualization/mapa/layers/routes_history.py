import folium
from datetime import datetime
from .routes import Routes


class RoutesHistory(Routes):
    capa_rutas = folium.FeatureGroup(name="Rutas Historial", show=False)
    rutas_avion = dict()
    factor_opacidad = 0.45

    @staticmethod
    def paintRoute(id_avion):
        opacity = 1
        for vuelo in RoutesHistory.rutas_avion[id_avion]:
            folium.PolyLine(
                vuelo["ruta"],
                color="blue",
                weight=2.5,
                opacity=opacity,
            ).add_to(RoutesHistory.capa_rutas)
            opacity = opacity - RoutesHistory.factor_opacidad

    @staticmethod
    def addLocation(id_avion, latitud, longitud, **kwargs):
        timestamp, onGround = kwargs.get("timestamp"), kwargs.get("onGround")
        if id_avion not in RoutesHistory.rutas_avion:
            RoutesHistory.rutas_avion[id_avion] = [
                {
                    "ruta": [],
                    "last_timestamp": None,
                    "onGround": False,
                    "been_on_air": False,
                }
            ]
        elif not RoutesHistory.sameRoute(id_avion, timestamp):
            RoutesHistory.rutas_avion[id_avion].insert(
                0,
                {
                    "ruta": [],
                    "last_timestamp": None,
                    "onGround": False,
                    "been_on_air": False,
                },
            )

        RoutesHistory.rutas_avion[id_avion][0]["ruta"].append(
            (round(latitud, 3), round(longitud, 3))
        )  # Se añade la ubicación a su ruta

        RoutesHistory.rutas_avion[id_avion][0]["last_timestamp"] = timestamp
        RoutesHistory.rutas_avion[id_avion][0]["onGround"] = onGround
        if not RoutesHistory.rutas_avion[id_avion][0]["been_on_air"]:
            RoutesHistory.rutas_avion[id_avion][0]["been_on_air"] = not onGround

    @staticmethod
    def sameRoute(id_avion, timestamp):
        new_timestamp = datetime.strptime(timestamp, Routes.formato_fechas)
        last_timestamp = datetime.strptime(
            RoutesHistory.rutas_avion[id_avion][0]["last_timestamp"],
            Routes.formato_fechas,
        )

        diferencia_tiempo = new_timestamp - last_timestamp

        if (
            (diferencia_tiempo.total_seconds() >= 1800)
            and RoutesHistory.rutas_avion[id_avion][0]["onGround"]
            and RoutesHistory.rutas_avion[id_avion][0]["been_on_air"]
        ):
            return False
        return True

    @staticmethod
    def deleteAirplane(id_avion):
        """Borra el avión"""
        if id_avion in RoutesHistory.rutas_avion:
            del RoutesHistory.rutas_avion[id_avion]

    @staticmethod
    def reset():
        RoutesHistory.rutas_avion = dict()
        RoutesHistory.capa_rutas = folium.FeatureGroup(name="Rutas Historial")
