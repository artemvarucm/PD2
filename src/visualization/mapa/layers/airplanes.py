import folium, branca, plotly.express as px, numpy as np
from .routes_velocity import RoutesVelocity
from .routes_history import RoutesHistory
import math
import json
import pandas as pd

class Airplanes:
    capa_aviones = folium.FeatureGroup(name="Aviones")
    aviones = dict()

    @staticmethod
    def createDescriptionAirplane(id_avion, latitud, longitud, timestamp, velocidad=None):
        """Crea el tooltip del avión"""
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
    def airplaneIcon(onGround, rotation):
        """Devuelve el icono correspondiente según el avión esté en el aire o en tierra"""
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
        avion = Airplanes.aviones[id_avion]
        x = np.arange(len(avion["alturas"]))
        y = avion["alturas"]
        rutas=RoutesVelocity.ruta_aviones[id_avion]["rutas"]["ruta_principal"]


        latitudes = []
        longitudes = []
        alturas_ruta = []
        aviones_id = []

        # Iteramos sobre los índices de la altura para rellenar los datos de hover
        for i in range(len(x)):
            if i < len(rutas):  # Si hay datos de ruta disponibles en ese índice
                lat, lon, alt, avion_id = rutas[i]
            else:  # Si no hay datos suficientes en la ruta, asignamos valores por defecto
                lat, lon, alt, avion_id = None, None, None, None
            
            latitudes.append(lat)
            longitudes.append(lon)
            alturas_ruta.append(alt)
            aviones_id.append(avion_id)

        # Convertimos los datos a un DataFrame de Pandas para manejar mejor las columnas
        df = pd.DataFrame({
            "Nº Mensaje": x,
            "Altura": y,
            "Latitud": latitudes,
            "Longitud": longitudes,
            "Altitud Ruta": alturas_ruta,
            "Avión ID": aviones_id
        })

        # Crear la gráfica con hover_data correctamente estructurado
        fig = px.line(
            df,
            x="Nº Mensaje",
            y="Altura",
            width=600,
            height=400,
            markers=True,
            hover_data={"Latitud": True, "Longitud": True}  # Agregar datos extra al hover
        )

        # Configuración del layout del gráfico
        fig.update_layout(
            title_text="Alturas del avión con el paso del tiempo",
            title_x=0.5,
            yaxis_title="Altura",
            yaxis=dict(showgrid=False),
            xaxis_title="Nº Mensaje",
            xaxis=dict(tickmode="array", tickvals=x, ticktext=x, showgrid=False),
            font=dict(size=12, color="black"),
        )




        html = fig.to_html(full_html=False, include_plotlyjs="cdn")


        custom_js = """
        <script>
        function setupPlotlyEvents() {
            var plot = document.querySelector('div.js-plotly-plot'); // Buscar el gráfico

            if (!plot) {
                console.log("Esperando a que se cargue Plotly...");
                setTimeout(setupPlotlyEvents, 500); // Reintentar si aún no está listo
                return;
            }

            console.log("Gráfico Plotly detectado en el popup!");

            plot.on('plotly_hover', function(event) {
                if (event.points && event.points.length > 0) {
                    var pointData = event.points[0];
                    var msg = {
                        type: 'mouse_on_point',
                        x: pointData.x,
                        y: pointData.y,
                        hoverData: pointData.customdata  // Extraer latitud y longitud
                    };
                    window.parent.postMessage(msg, '*');
                }
            });

            plot.on('plotly_unhover', function(event) {
                window.parent.postMessage('mouse_off_point', '*');
            });
        }

        document.addEventListener("DOMContentLoaded", setupPlotlyEvents);
        </script>
        """

        # Insertar el JS en el HTML del gráfico
        html_with_js = html + custom_js

        iframe = branca.element.IFrame(html=html_with_js, width=620, height=420)
        popup = folium.Popup(iframe)
        return popup

    @staticmethod
    def paintAirplane(id_avion, latitud, longitud, on_ground, rotation, timestamp, velocidad):
        """Pinta el avión en el mapa"""

        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                Airplanes.createDescriptionAirplane(id_avion, latitud, longitud, timestamp, velocidad),
                max_width=300,
            ),
            icao=id_avion,
            popup=Airplanes.generateImageHeights(id_avion),
            icon=Airplanes.airplaneIcon(on_ground, rotation),
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
                Airplanes.aviones[id_avion]["rotacion"],
                Airplanes.aviones[id_avion]["timestamp"], 
                Airplanes.aviones[id_avion]["velocidad"]
            )
            RoutesVelocity.paintRoute(id_avion)
            RoutesHistory.paintRoute(id_avion)

        Airplanes.capa_aviones.add_to(mapa)
        RoutesVelocity.capa_rutas.add_to(mapa)
        RoutesHistory.capa_rutas.add_to(mapa)

    # GESTIÓN DE LOS AVIONES QUE SE VAN A VISUALIZAR
    @staticmethod
    def addAirplane(id_avion, latitud, longitud, on_ground, rotacion, velocidad, timestamp, altura, callsign):
        """Añade el avión para que pueda ser pintado en el mapa"""
        if id_avion not in Airplanes.aviones:
            Airplanes.aviones[id_avion] = {
                "alturas": [],
                "onGround": None,
                "rotacion": None,
                "timestamp": timestamp,
                "velocidad": None,
            }
        Airplanes.aviones[id_avion]["onGround"] = on_ground
        Airplanes.aviones[id_avion]["rotacion"] = rotacion
        Airplanes.aviones[id_avion]["timestamp"] = timestamp
        Airplanes.aviones[id_avion]["velocidad"] = velocidad

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

    @staticmethod
    def script_show_one_route_on_click():
        """Script JavaScript (funcionalidad de selección y ocultación de elementos)"""
        scriptContent = None
        
        with open("./assets/js/plane_click.js", "r") as file:
            scriptContent = file.read()

        scriptContent = scriptContent.replace('{{trayectoriasLengths}}', json.dumps([len(avion["rutas"]["ruta_principal"]) - 1 for avion in RoutesVelocity.ruta_aviones.values()]))

        return f"<script>{scriptContent}</script>"