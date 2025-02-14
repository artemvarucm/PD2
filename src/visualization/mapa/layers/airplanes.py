import folium

class Airplanes:
    capa_aviones = folium.FeatureGroup(name="Aviones")
    capa_rutas = folium.FeatureGroup(name="Rutas")

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
    def paintAirplane(id_avion, latitud, longitud, on_ground):
        """Pinta el avión en el mapa"""
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                Airplanes.createDescriptionAirplane(id_avion, latitud, longitud),
                max_width=300,
            ),
            icon=Airplanes.airplaneIcon(on_ground),
        ).add_to(Airplanes.capa_aviones)

    @staticmethod
    def paintAirplanes(mapa):
        """Pinta todos los aviones en el mapa. Además, también pinta sus rutas"""
        for id_avion in Airplanes.aviones:
            Airplanes.paintAirplane(
                id_avion,
                Airplanes.aviones[id_avion]["rutas"]["ruta_principal"][-1][0],
                Airplanes.aviones[id_avion]["rutas"]["ruta_principal"][-1][1],
                Airplanes.aviones[id_avion]["onGround"],
            )
            Airplanes.paintRoute(id_avion)

        Airplanes.capa_aviones.add_to(mapa)
        Airplanes.capa_rutas.add_to(mapa)

    # PINTAR RUTAS DE AVIONES
    @staticmethod
    def paintRoute(id_avion):
        """Pinta la ruta del avión. Tiene en cuenta la velocidad del avión en cada tramo para utilizar un color u otro"""
        rutas = ["ruta_lenta", "ruta_rapida", "ruta_media"]
        colores = {"ruta_rapida": "red", "ruta_media": "orange", "ruta_lenta": "green"}

        for tipo_ruta in rutas:
            for r in range(0, len(Airplanes.aviones[id_avion]["rutas"][tipo_ruta]), 2):
                folium.PolyLine(
                    Airplanes.aviones[id_avion]["rutas"]["ruta_principal"][
                        Airplanes.aviones[id_avion]["rutas"][tipo_ruta][r] : Airplanes.aviones[
                            id_avion
                        ]["rutas"][tipo_ruta][r + 1]
                        + 1
                    ],
                    color=colores[tipo_ruta],
                    weight=2.5,
                    opacity=1,
                ).add_to(Airplanes.capa_rutas)

    # GESTIÓN DE LOS AVIONES QUE SE VAN A VISUALIZAR
    @staticmethod
    def addAirplane(id_avion, latitud, longitud, on_ground, velocidad=0):
        """Añade el avión para que pueda ser pintado en el mapa.
        De cada avión se guarda:
                                ruta_principal: La ruta que ha seguido el avión hasta el momento
                                ruta_rapida: Guarda los índices de la ruta_principal donde el avión haya ido rápido
                                ruta_media: Guarda los índices de la ruta_principal donde el avión haya ido a una velocidad media
                                ruta_lenta: Guarda los índices de la ruta_principal donde el avión haya ido lento
                                ultima_velocidad: Nos ayuda gestionar las rutas que guardan información sobre la velocidad del avión en los distintos tramos de la ruta principal
                                onGround: Inidca si el avión está en tierra o en aire"""

        if (
            id_avion not in Airplanes.aviones
        ):  # Si el avion no ha aparecido anteriormente, se le crea una estructura para guardar sus datos
            Airplanes.aviones[id_avion] = {
                "rutas": {
                    "ruta_principal": [],
                    "ruta_rapida": [],
                    "ruta_media": [],
                    "ruta_lenta": [],
                    "ultima_velocidad": None,
                },
                "onGround": None,
            }

        Airplanes.aviones[id_avion]["rutas"]["ruta_principal"].append(
            (round(latitud, 3), round(longitud, 3))
        )  # Se añade la ubicación a su ruta

        nuevoTipoVelocidad = Airplanes.getVelocityType(velocidad)

        if Airplanes.aviones[id_avion]["rutas"]["ultima_velocidad"] is None:
            Airplanes.aviones[id_avion]["rutas"]["ultima_velocidad"] = nuevoTipoVelocidad
            Airplanes.aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                len(Airplanes.aviones[id_avion]["rutas"]["ruta_principal"]) - 1
            )
            Airplanes.aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                len(Airplanes.aviones[id_avion]["rutas"]["ruta_principal"])
            )
        else:
            Airplanes.updateTramosVelocidad(id_avion, nuevoTipoVelocidad)

        Airplanes.aviones[id_avion]["onGround"] = on_ground

    @staticmethod
    def deleteAirplane(id_avion):
        """Borra el avión"""
        if id_avion in Airplanes.aviones:
            del Airplanes.aviones[id_avion]

    @staticmethod
    def updateTramosVelocidad(id_avion, nuevoTipoVelocidad):
        """Gestiona el tipo de velocidad de los tramos de la ruta"""
        if nuevoTipoVelocidad == Airplanes.aviones[id_avion]["rutas"]["ultima_velocidad"]:
            Airplanes.aviones[id_avion]["rutas"][nuevoTipoVelocidad][-1] = len(
                Airplanes.aviones[id_avion]["rutas"]["ruta_principal"]
            )
        else:
            Airplanes.aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                Airplanes.aviones[id_avion]["rutas"][
                    Airplanes.aviones[id_avion]["rutas"]["ultima_velocidad"]
                ][-1]
            )
            Airplanes.aviones[id_avion]["rutas"][nuevoTipoVelocidad].append(
                Airplanes.aviones[id_avion]["rutas"][
                    Airplanes.aviones[id_avion]["rutas"]["ultima_velocidad"]
                ][-1]
                + 1
            )
            Airplanes.aviones[id_avion]["rutas"]["ultima_velocidad"] = nuevoTipoVelocidad

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
    def reset():
        Airplanes.capa_aviones = folium.FeatureGroup(name="Aviones")
        Airplanes.capa_rutas = folium.FeatureGroup(name="Rutas")
        Airplanes.aviones = dict()