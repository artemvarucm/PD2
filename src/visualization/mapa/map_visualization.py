import folium, webbrowser, os, time, pandas as pd
from plugins.extra_features import ExtraFeatures
from layers.radars import Radars
from layers.landing_strips import LandingStrips
from layers.airplanes import Airplanes

class MapVisualization:
    def __init__(self):
        self.mapa = self.createMap()
        self.layerControl = folium.LayerControl(collapsed=False, sortLayers=True)

        self.initializeMap(all=True)

    # INICIALIZACION MAPA
    def createMap(self, latitud=40.51, longitud=-3.53):
        """Crea un mapa. Al abrirse hace zoom en la localizacion indicada"""
        mapa = folium.Map(location=[latitud, longitud], zoom_start=12, zoom_control=False)
        return mapa

    def initializeMap(self, all=False):
        """Inicializa el mapa base. En caso de all=True inicializa el mapa desde 0, pintando las pistas de aterrizaje y el radar.
        En caso contrario, simplemente restaura las capas que varian con el tiempo (aviones y rutas)
        """
        if all:
            self.paintRadars()
            self.paintLandingStrips()
        else:
            Airplanes.reset()

        self.addLayers()
        self.layerControl.add_to(self.mapa)

    def addLayers(self):
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
    def addAirplane(self, id_avion, latitud, longitud, on_ground, velocidad):
        """Añade el avión para que pueda ser pintado en el mapa. Además, también servirá para pintar su ruta"""
        Airplanes.addAirplane(id_avion, latitud, longitud, on_ground, velocidad)

    def deleteAirplane(self, id_avion):
        """Borra el avión"""
        Airplanes.deleteAirplane(id_avion)


     # FUNCIONALIDADES EXTRAS EN EL MAPA
    def addExtraFeatures(self):
        """Añade funcionalidades extras al mapa"""
        ExtraFeatures().addExtraFeatures(self.mapa)

    # GESTIÓN DEL MAPA RESULTANTE
    def saveMap(self, nombre_mapa):
        """Guarda el mapa con el nombre indicado, añadiéndole la extensión html"""
        self.mapa.save(f"./mapas/{nombre_mapa}.html")

    def showMap(self, nombre_mapa=None):
        """Muestra el mapa. En caso de no especificar el nombre, este será la fecha en la que se ha ejecutado la función"""

        self.addExtraFeatures()
        self.paintAirplanes()
        
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

m = MapVisualization()
"""
df = pd.read_csv("data/ex1/icao_343694.csv")
df["velocidad"] = 10
df.loc[3000:15000, "velocidad"] = 70
df.loc[15000:23000, "velocidad"] = 100
df["on_ground"] = True
i = 0
# df = df.loc[:50]
for _, row in df.iterrows():
    row["longitud"] = -3.53 + i
   # print(f"ON GROOUND {row["on_ground"]}-- LAT -- {row["latitude"]} LON -- {row["longitud"]}")
    if (
        pd.notna(row["on_ground"])
        and pd.notna(row["latitude"])
        and pd.notna(row["longitud"])
    ):  # on ground
        m.addAirplane(
            row["icao"],
            row["latitude"] + i,
            row["longitud"],
            row["on_ground"],
            row["velocidad"],
        )
        i = i + 0.01
"""
m.addAirplane("jnsfu", 40.52, -3.53, True, 10)
m.addAirplane("jnsfu", 40.55, -3.55, False, 70)
m.addAirplane("jnsfu", 40.56, -3.56, False, 70)
m.addAirplane("la", 40.52, -3.53, False, 90)
m.addAirplane("la", 40.70, -3.80, True, 90)
m.addAirplane("la", 40.71, -3.82, False, 10)
m.addAirplane("la", 40.74, -3.82, False, 10)

m.showMap()

