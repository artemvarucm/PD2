import folium
import webbrowser
import os
import time
import time
import pandas as pd


class MapVisualization:
    def __init__(self):
        self.mapa = self.createMap()
        self.layerControl = folium.LayerControl(collapsed=False, sortLayers=True)

        self.radares = [{"nombre": "PRINCIPAL", "lat": 40.51, "lon": -3.53}]
        self.pistas = [
            {"nombre": "1", "lat": 40.463, "lon": -3.554},
            {"nombre": "2", "lat": 40.473, "lon": -3.536},
            {"nombre": "3", "lat": 40.507, "lon": -3.574},
            {"nombre": "4", "lat": 40.507, "lon": -3.559},
        ]

        self.layers = {
            'radar': {'capa': folium.FeatureGroup(name="Radares"), 'color': "darkblue"},
            'pistas': {'capa': folium.FeatureGroup(name="Pistas de Aterrizaje"), 'color': "green"},
            'aviones': folium.FeatureGroup(name="Aviones"),
            'rutas': folium.FeatureGroup(name="Rutas")
        }

        self.aviones = dict()
        
        self.initializeMap(all=True)

    def addLayers(self):
        self.layers['radar']['capa'].add_to(self.mapa)
        self.layers['pistas']['capa'].add_to(self.mapa)
        self.layers['aviones'].add_to(self.mapa)
        self.layers['rutas'].add_to(self.mapa)

    def initializeMap(self, all=False):
        if all:
            self.paintRadars()
            self.paintLandingStrips()
        else:
            self.layers['aviones'] = folium.FeatureGroup(name="Aviones")
            self.layers['rutas'] = folium.FeatureGroup(name="Rutas")
        
        self.addLayers()
        self.layerControl.add_to(self.mapa)

    def createMap(self, latitud=40.51, longitud=-3.53):
        mapa = folium.Map(
            location=[latitud, longitud], zoom_start=12
        )
        return mapa
    
    # PAINT RADARES
    def paintRadar(self, nombre_radar, latitud, longitud):
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                f"""
                                            <div style="text-align: center;">
                                            <b>RADAR {nombre_radar}</b><br>
                                            Lat: {latitud}<br>
                                            Lon: {longitud}
                                        """,
                max_width=300,
            ),
            icon=folium.Icon(
                color=self.layers['radar']['color'], icon="fa-solid fa-satellite-dish", prefix="fa"
            ),
        ).add_to(self.layers['radar']['capa'])        
    
    def paintRadars(self):
        for radar in self.radares:
            self.paintRadar(radar['nombre'], radar['lat'], radar['lon'])


    # PAINT PISTAS ATERRIZAJE
    def createDescriptionLandingStrip(self, nombre_pista, latitud, longitud):
        return f"""
                        <div style="text-align: center;">
                        <b>PISTA {nombre_pista}</b><br>
                        Lat: {latitud}<br>
                        Lon: {longitud}
                    """

    def paintLandingStrip(self, nombre_pista, latitud, longitud):
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                self.createDescriptionLandingStrip(nombre_pista, latitud, longitud),
                max_width=300,
            ),
            icon=folium.Icon(
                color=self.layers['pistas']['color'], icon="fa-solid fa-plane-arrival", prefix="fa"
            ),
        ).add_to(self.layers['pistas']['capa'])

        
    def paintLandingStrips(self):
        for pista in self.pistas:
            self.paintLandingStrip(pista['nombre'], pista["lat"], pista["lon"])

    # PINTAR AVIONES
    def createDescriptionAirplane(self, id_avion, latitud, longitud, velocidad=None):
        if not velocidad:
            velocidad="-"
        return f"""
                        <div style="text-align: center;">
                        <b>ID: {id_avion}</b><br>
                        Lat: {round(latitud,2)}<br>
                        Lon: {round(longitud,2)}<br>
                        Velocidad: {velocidad} km/h
                    """

    def airplaneIcon(self, onGroung):
        if onGroung:
            path_icon = "./assets/icons/airplane_ground.png"
        else:
            path_icon = "./assets/icons/airplane_air.png"

        icon = folium.CustomIcon(
            path_icon,
            icon_size=(25, 25),
        )

        return icon
    
    def paintAirplane(self, id_avion, latitud, longitud, on_ground):
        folium.Marker(
            location=[latitud, longitud],
            tooltip=folium.Tooltip(
                self.createDescriptionAirplane(id_avion, latitud, longitud),
                max_width=300,
            ),
            icon=self.airplaneIcon(on_ground),
        ).add_to(self.layers['aviones'])
    
    def paintAirplanes(self):
        for id_avion in self.aviones:
            self.paintAirplane(id_avion, self.aviones[id_avion]['rutas']['ruta_principal'][-1][0], self.aviones[id_avion]['rutas']['ruta_principal'][-1][1], self.aviones[id_avion]['onGround'])
            self.paintRoute(id_avion)
        
        self.layers['aviones'].add_to(self.mapa)
        self.layers['rutas'].add_to(self.mapa)

    def addAirplane(self, id_avion, latitud, longitud, on_ground, velocidad=0):
        if id_avion not in self.aviones:
            self.aviones[id_avion] = {'rutas':{'ruta_principal': [], 'ruta_rapida': [], 'ruta_media': [], 'ruta_lenta':[], 'ultima_velocidad': None}, 'onGround':None}
        
        self.aviones[id_avion]['rutas']['ruta_principal'].append((round(latitud,3), round(longitud,3)))

        nuevoTipoVelocidad = self.getVelocityType(velocidad)
        
        if self.aviones[id_avion]['rutas']['ultima_velocidad'] is None:
            self.aviones[id_avion]['rutas']['ultima_velocidad'] = nuevoTipoVelocidad
            self.aviones[id_avion]['rutas'][nuevoTipoVelocidad].append(len(self.aviones[id_avion]['rutas']['ruta_principal']) - 1)
            self.aviones[id_avion]['rutas'][nuevoTipoVelocidad].append(len(self.aviones[id_avion]['rutas']['ruta_principal']))
        else:
            self.updateTramosVelocidad(id_avion, nuevoTipoVelocidad)

        self.aviones[id_avion]['onGround'] = on_ground

    def updateTramosVelocidad(self, id_avion, nuevoTipoVelocidad):
        if nuevoTipoVelocidad == self.aviones[id_avion]['rutas']['ultima_velocidad']:
            self.aviones[id_avion]['rutas'][nuevoTipoVelocidad][-1] = len(self.aviones[id_avion]['rutas']['ruta_principal'])
        else:
            self.aviones[id_avion]['rutas'][nuevoTipoVelocidad].append(self.aviones[id_avion]['rutas'][self.aviones[id_avion]['rutas']['ultima_velocidad']][-1])
            self.aviones[id_avion]['rutas'][nuevoTipoVelocidad].append(self.aviones[id_avion]['rutas'][self.aviones[id_avion]['rutas']['ultima_velocidad']][-1]+1)
            self.aviones[id_avion]['rutas']['ultima_velocidad'] = nuevoTipoVelocidad
        
    def getVelocityType(self, velocidad):
        if velocidad <= 60:
            return "ruta_lenta"
        elif velocidad <= 80:
            return "ruta_media"
        else:
            return "ruta_rapida"
        

    # PINTAR RUTAS DE AVIONES
    def paintRoute(self, id_avion):
        rutas = ['ruta_lenta', 'ruta_rapida', 'ruta_media']
        colores = {'ruta_rapida': 'red', 'ruta_media': 'orange', 'ruta_lenta':'green'}
        
        for tipo_ruta in rutas:
            for r in range(0, len(self.aviones[id_avion]['rutas'][tipo_ruta]), 2):
                folium.PolyLine(self.aviones[id_avion]['rutas']['ruta_principal'][self.aviones[id_avion]['rutas'][tipo_ruta][r]:self.aviones[id_avion]['rutas'][tipo_ruta][r+1]+1], color=colores[tipo_ruta], weight=2.5, opacity=1).add_to(self.layers['rutas'])
                
            

    def saveMap(self, nombre_mapa):
        self.mapa.save(f"./mapas/{nombre_mapa}.html")

    def showMap(self, nombre_mapa=None):
        self.paintAirplanes()

        if nombre_mapa is None:
            nombre_mapa = time.strftime("%d-%m-%Y_%H-%M-%S")
        
        if not os.path.exists(f"./mapas/{nombre_mapa}.html"):
            self.saveMap(nombre_mapa)
        webbrowser.open(f"file://{os.path.abspath(f"./mapas/{nombre_mapa}.html")}")

        self.reset()

    def reset(self):
        self.mapa = self.createMap()
        self.initializeMap(all=False)


m = MapVisualization()
df = pd.read_csv("data/ex1/icao_343694.csv")
df["velocidad"] = 10
df.loc[3000:15000, "velocidad"] = 70
df.loc[15000:23000, "velocidad"] = 100
df["on_ground"] = True
i = 0
#df = df.loc[:50]
for _, row in df.iterrows():
    row["longitud"] = -3.53 + i
    print(f"ON GROOUND {row["on_ground"]}-- LAT -- {row["latitude"]} LON -- {row["longitud"]}")
    if pd.notna(row["on_ground"]) and pd.notna(row["latitude"]) and pd.notna(row["longitud"]): #on ground
        m.addAirplane(row["icao"], row["latitude"]+i,row["longitud"],row["on_ground"], row["velocidad"])
        i=i+0.01
"""
m.addAirplane("jnsfu", 40.52, -3.53, True, 10)
m.addAirplane("jnsfu", 40.55, -3.55, False, 70)
m.addAirplane("jnsfu", 40.56, -3.56, False, 70)
m.addAirplane("jnsfu", 40.57, -3.57, False, 90)
m.addAirplane("jnsfu", 40.70, -3.80, True, 90)
m.addAirplane("jnsfu", 40.71, -3.82, False, 10)
m.addAirplane("jnsfu", 40.74, -3.82, False, 10)

print(m.aviones["jnsfu"]['rutas'])
"""
m.showMap()



