import folium, webbrowser, os, time, pandas as pd
from plugins.extra_features import ExtraFeatures
from layers.radars import Radars
from layers.landing_strips import LandingStrips
from layers.airplanes import Airplanes


class StaticMap:
    def __init__(self):
        self.mapa = self.createMap()
        self.layerControl = folium.LayerControl(collapsed=False, sortLayers=True)

        self.initializeMap(all=True)

    # INICIALIZACION MAPA
    def createMap(self, latitud=40.51, longitud=-3.53):
        """Crea un mapa. Al abrirse hace zoom en la localizacion indicada"""
        mapa = folium.Map(
            location=[latitud, longitud], zoom_start=12, zoom_control=False
        )
        return mapa

    def initializeMap(self, all=False):
        """Inicializa el mapa base. En caso de all=True inicializa el mapa desde 0, pintando las pistas de aterrizaje y el radar.
        En caso contrario, simplemente restaura las capas que varian con el tiempo (aviones y rutas)
        """
        if not all:
            Airplanes.reset()

        self.addAllLayers()
        self.layerControl.add_to(self.mapa)

    def addAllLayers(self):
        """Añade todas las capas del mapa"""
        self.paintRadars()
        self.paintLandingStrips()
        self.paintAirplanes()

    # PAINT RADARES
    def paintRadars(self):
        Radars.addRadarsLayer(self.mapa)

    # PAINT PISTAS ATERRIZAJE
    def paintLandingStrips(self):
        LandingStrips.addLandingStripsLayers(self.mapa)

    # PAINT AVIONES Y SUS RUTAS
    def paintAirplanes(self):
        Airplanes.paintAirplanes(self.mapa)

    # GESTIÓN DE LOS AVIONES QUE SE VAN A VISUALIZAR
    def addAirplane(self, id_avion, latitud, longitud, on_ground, rotacion, velocidad, timestamp, altura):
        """Añade el avión para que pueda ser pintado en el mapa. Además, también servirá para pintar su ruta"""
        Airplanes.addAirplane(id_avion, latitud, longitud, on_ground, rotacion, velocidad, timestamp, altura)

    def deleteAirplane(self, id_avion):
        """Borra el avión"""
        Airplanes.deleteAirplane(id_avion)

    # FUNCIONALIDADES EXTRAS EN EL MAPA
    def addExtraFeatures(self):
        """Añade funcionalidades extras al mapa"""
        ExtraFeatures().addExtraFeatures(self.mapa, Airplanes.capa_aviones)

    # GESTIÓN DEL MAPA RESULTANTE
    def saveMap(self, nombre_mapa):
        """Guarda el mapa con el nombre indicado, añadiéndole la extensión html"""
        self.mapa.save(f"./mapas/{nombre_mapa}.html")

    def showMap(self, nombre_mapa=None):
        """Muestra el mapa. En caso de no especificar el nombre, este será la fecha en la que se ha ejecutado la función"""

        self.addExtraFeatures()
        self.paintAirplanes()

        script = Airplanes.script_show_one_route_on_click()

        self.mapa.get_root().html.add_child(folium.Element(script))

        if nombre_mapa is None:
            nombre_mapa = time.strftime("%d-%m-%Y_%H-%M-%S")

        if not os.path.exists(
            f"./mapas/{nombre_mapa}.html"
        ):  # En caso de que el mapa no haya sido guardado previamente, se guarda primero
            self.saveMap(nombre_mapa)
        webbrowser.open(
            f"file://{os.path.abspath(f"./mapas/{nombre_mapa}.html")}"
        )  # Abre el mapa en el navegador

        self.reset()

    def reset(self):
        """Borra las capas que varían con el tiempo (aviones y rutas)"""
        self.mapa = self.createMap()
        self.initializeMap(all=False)


m = StaticMap()
"""
timestamp_str1 = "2025-02-15 14:06:22"
timestamp_str2 = "2025-02-15 14:06:25"
timestamp_str3 = "2025-02-15 14:06:28"
timestamp_str4 = "2025-02-15 20:06:22"
timestamp_str5 = "2025-02-15 20:06:24"
timestamp_str6 = "2025-02-15 20:06:29"
m.addAirplane("jnsfu", 40.52, -3.53, True, 10, timestamp_str1, 1)
m.addAirplane("jnsfu", 40.55, -3.55, False, 70, timestamp_str2, 2)
m.addAirplane("jnsfu", 40.56, -3.56, True, 70, timestamp_str3, 3)
m.addAirplane("jnsfu", 40.52, -3.53, True, 90, timestamp_str4, 4)
m.addAirplane("jnsfu", 40.70, -3.80, False, 90, timestamp_str5, 3)
m.addAirplane("jnsfu", 40.71, -3.82, False, 10, timestamp_str6, 2)
"""

df = pd.read_csv("data/ex2/preprocess_mapa_mini.csv")

df['ts_kafka'] = "2025-02-15 14:06:22"
for _, row in df.iterrows():
    if pd.notna(row["ground"]) and pd.notna(row["lat"]) and pd.notna(row["lon"]) and  row["ground"] is not None and row["lat"] is not None and row["lon"] is not None: #on ground
        print(f"ICAO -- {row["icao"]} , LAT -- {row["lat"]}, LON -- {row["lon"]}, VELOCITY -- {row["velocity"]}, DIRECCION -- {row["direccion"]}")
        m.addAirplane(row["icao"], row["lat"],row["lon"],row["ground"], row["direccion"], row["velocity"], row["ts_kafka"], row["alt_feet"])


m.showMap()
