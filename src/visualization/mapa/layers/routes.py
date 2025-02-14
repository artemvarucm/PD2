import folium

class Routes:
    capa_rutas = folium.FeatureGroup(name="Rutas")
    ruta_aviones = dict()

    @staticmethod
    def paintRoute(id_avion):
        """Pinta la ruta del avión. Tiene en cuenta la velocidad del avión en cada tramo para utilizar un color u otro"""
        rutas = ["ruta_lenta", "ruta_rapida", "ruta_media"]
        colores = {"ruta_rapida": "red", "ruta_media": "orange", "ruta_lenta": "green"}

        for tipo_ruta in rutas:
            for r in range(0, len(Routes.ruta_aviones[id_avion]["rutas"][tipo_ruta]), 2):
                folium.PolyLine(
                    Routes.ruta_aviones[id_avion]["rutas"]["ruta_principal"][
                        Routes.ruta_aviones[id_avion]["rutas"][tipo_ruta][r] : Routes.ruta_aviones[
                            id_avion
                        ]["rutas"][tipo_ruta][r + 1]
                        + 1
                    ],
                    color=colores[tipo_ruta],
                    weight=2.5,
                    opacity=1,
                ).add_to(Routes.capa_rutas)
    
    @staticmethod
    def addLocation(id_avion, latitud, longitud, velocidad=0):
        if (id_avion not in Routes.ruta_aviones):
            Routes.ruta_aviones[id_avion] = {
                "rutas": {
                    "ruta_principal": [],
                    "ruta_rapida": [],
                    "ruta_media": [],
                    "ruta_lenta": [],
                    "ultima_velocidad": None,
                }
            }

        Routes.ruta_aviones[id_avion]["rutas"]["ruta_principal"].append(
            (round(latitud, 3), round(longitud, 3))
        )  # Se añade la ubicación a su ruta
        
        nuevoTipoVelocidad = Routes.getVelocityType(velocidad)

        if Routes.ruta_aviones[id_avion]["rutas"]["ultima_velocidad"] is None:
            Routes.ruta_aviones[id_avion]["rutas"]["ultima_velocidad"] = nuevoTipoVelocidad
            Routes.ruta_aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                len(Routes.ruta_aviones[id_avion]["rutas"]["ruta_principal"]) - 1
            )
            Routes.ruta_aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                len(Routes.ruta_aviones[id_avion]["rutas"]["ruta_principal"])
            )
        else:
            Routes.updateTramosVelocidad(id_avion, nuevoTipoVelocidad)
    
    @staticmethod
    def updateTramosVelocidad(id_avion, nuevoTipoVelocidad):
        """Gestiona el tipo de velocidad de los tramos de la ruta"""
        if nuevoTipoVelocidad == Routes.ruta_aviones[id_avion]["rutas"]["ultima_velocidad"]:
            Routes.ruta_aviones[id_avion]["rutas"][nuevoTipoVelocidad][-1] = len(
                Routes.ruta_aviones[id_avion]["rutas"]["ruta_principal"]
            )
        else:
            Routes.ruta_aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                Routes.ruta_aviones[id_avion]["rutas"][
                    Routes.ruta_aviones[id_avion]["rutas"]["ultima_velocidad"]
                ][-1]
            )
            Routes.ruta_aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                Routes.ruta_aviones[id_avion]["rutas"][
                    Routes.ruta_aviones[id_avion]["rutas"]["ultima_velocidad"]
                ][-1]
                + 1
            )
            Routes.ruta_aviones[id_avion]["rutas"]["ultima_velocidad"] = nuevoTipoVelocidad

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
        if id_avion in Routes.ruta_aviones:
            del Routes.ruta_aviones[id_avion]

