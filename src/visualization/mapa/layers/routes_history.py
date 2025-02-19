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
        callsign = kwargs.get("callsign")
        if id_avion not in RoutesHistory.rutas_avion:
            RoutesHistory.rutas_avion[id_avion] = [
                {
                    "ruta": [],
                    'last_callsign': None
                }
            ]
        elif not RoutesHistory.sameRoute(id_avion, callsign):
            RoutesHistory.rutas_avion[id_avion].insert(
                0,
                {
                    "ruta": [],
                    'last_callsign': None
                },
            )

        RoutesHistory.rutas_avion[id_avion][0]["ruta"].append(
            (round(latitud, 3), round(longitud, 3))
        )  # Se añade la ubicación a su ruta
        RoutesHistory.rutas_avion[id_avion][0]['last_callsign'] = callsign

    @staticmethod
    def sameRoute(id_avion, callsign):
        return RoutesHistory.rutas_avion[id_avion][0]['last_callsign'] == callsign

    @staticmethod
    def deleteAirplane(id_avion):
        """Borra el avión"""
        if id_avion in RoutesHistory.rutas_avion:
            del RoutesHistory.rutas_avion[id_avion]

    @staticmethod
    def reset():
        RoutesHistory.rutas_avion = dict()
        RoutesHistory.capa_rutas = folium.FeatureGroup(name="Rutas Historial")
