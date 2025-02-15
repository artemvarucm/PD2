import folium
from .routes import Routes
from datetime import datetime


class RoutesVelocity(Routes):
    capa_rutas = folium.FeatureGroup(name="Rutas Velocidad")
    ruta_aviones = dict()

    @staticmethod
    def paintRoute(id_avion):
        """Pinta la ruta del avión. Tiene en cuenta la velocidad del avión en cada tramo para utilizar un color u otro"""
        rutas = ["ruta_lenta", "ruta_rapida", "ruta_media"]
        colores = {"ruta_rapida": "red", "ruta_media": "orange", "ruta_lenta": "green"}

        for tipo_ruta in rutas:
            for r in range(
                0, len(RoutesVelocity.ruta_aviones[id_avion]["rutas"][tipo_ruta]), 2
            ):
                folium.PolyLine(
                    RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"][
                        RoutesVelocity.ruta_aviones[id_avion]["rutas"][tipo_ruta][
                            r
                        ] : RoutesVelocity.ruta_aviones[id_avion]["rutas"][tipo_ruta][
                            r + 1
                        ]
                        + 1
                    ],
                    color=colores[tipo_ruta],
                    weight=2.5,
                    opacity=1,
                ).add_to(RoutesVelocity.capa_rutas)

    @staticmethod
    def sameRoute(id_avion, timestamp):
        new_timestamp = datetime.strptime(timestamp, Routes.formato_fechas)
        last_timestamp = datetime.strptime(
            RoutesVelocity.ruta_aviones[id_avion]["last_timestamp"],
            Routes.formato_fechas,
        )

        diferencia_tiempo = new_timestamp - last_timestamp

        if (
            (diferencia_tiempo.total_seconds() >= 1800)
            and RoutesVelocity.ruta_aviones[id_avion]["onGround"]
            and RoutesVelocity.ruta_aviones[id_avion]["been_on_air"]
        ):
            return False
        return True

    @staticmethod
    def addLocation(id_avion, latitud, longitud, **kwargs):
        timestamp, velocidad, onGround = (
            kwargs.get("timestamp"),
            kwargs.get("velocidad", 0),
            kwargs.get("onGround"),
        )

        if (id_avion not in RoutesVelocity.ruta_aviones) or (
            not RoutesVelocity.sameRoute(id_avion, timestamp)
        ):
            RoutesVelocity.ruta_aviones[id_avion] = {
                "rutas": {
                    "ruta_principal": [],
                    "ruta_rapida": [],
                    "ruta_media": [],
                    "ruta_lenta": [],
                    "ultima_velocidad": None,
                },
                "last_timestamp": None,
                "onGround": False,
                "been_on_air": False,
            }

        RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"].append(
            (round(latitud, 3), round(longitud, 3))
        )  # Se añade la ubicación a su ruta
        RoutesVelocity.ruta_aviones[id_avion]["last_timestamp"] = timestamp
        RoutesVelocity.ruta_aviones[id_avion]["onGround"] = onGround
        if not RoutesVelocity.ruta_aviones[id_avion]["been_on_air"]:
            RoutesVelocity.ruta_aviones[id_avion]["been_on_air"] = not onGround

        nuevoTipoVelocidad = RoutesVelocity.getVelocityType(velocidad)

        if RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ultima_velocidad"] is None:
            RoutesVelocity.ruta_aviones[id_avion]["rutas"][
                "ultima_velocidad"
            ] = nuevoTipoVelocidad
            RoutesVelocity.ruta_aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                len(RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"])
                - 1
            )
            RoutesVelocity.ruta_aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                len(RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"])
            )
        else:
            RoutesVelocity.updateTramosVelocidad(id_avion, nuevoTipoVelocidad)

    @staticmethod
    def updateTramosVelocidad(id_avion, nuevoTipoVelocidad):
        """Gestiona el tipo de velocidad de los tramos de la ruta"""
        if (
            nuevoTipoVelocidad
            == RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ultima_velocidad"]
        ):
            RoutesVelocity.ruta_aviones[id_avion]["rutas"][nuevoTipoVelocidad][-1] = (
                len(RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"])
            )
        else:
            RoutesVelocity.ruta_aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                RoutesVelocity.ruta_aviones[id_avion]["rutas"][
                    RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ultima_velocidad"]
                ][-1]
            )
            RoutesVelocity.ruta_aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                RoutesVelocity.ruta_aviones[id_avion]["rutas"][
                    RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ultima_velocidad"]
                ][-1]
                + 1
            )
            RoutesVelocity.ruta_aviones[id_avion]["rutas"][
                "ultima_velocidad"
            ] = nuevoTipoVelocidad

    @staticmethod
    def getVelocityType(velocidad):
        """Devuelve el tipo de velocidad según la velocidad del avión"""
        if velocidad <= 60:
            return "ruta_lenta"
        elif velocidad <= 80:
            return "ruta_media"
        else:
            return "ruta_rapida"

    @staticmethod
    def deleteAirplane(id_avion):
        """Borra el avión"""
        if id_avion in RoutesVelocity.ruta_aviones:
            del RoutesVelocity.ruta_aviones[id_avion]

    @staticmethod
    def reset():
        RoutesVelocity.ruta_aviones = dict()
        RoutesVelocity.capa_rutas = folium.FeatureGroup(name="Rutas Velocidad")
