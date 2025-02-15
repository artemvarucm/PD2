import pandas as pd
import folium
import json
import webbrowser
import os
import time
import math

class MapV:
    def __init__(self):
        self.mapa = self.createMap()
        self.layerControl = folium.LayerControl()
        self.aviones = dict()
        self.num_aviones = 0
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

        self.initializeMap(all=True)
        self.script = None


    def addAirplane(self, id_avion, latitud, longitud, on_ground, rotacion, velocidad, altura):
        if id_avion not in self.aviones:
            self.aviones[id_avion] = {"id":self.num_aviones,"lat": None, "lon": None, "ground":None, "rotacion": None, "altura": None, "trayectoria": []}
            self.num_aviones = self.num_aviones + 1

        self.aviones[id_avion]["trayectoria"].insert(0,(latitud,longitud, velocidad))
        self.aviones[id_avion]["lat"] = latitud
        self.aviones[id_avion]["lon"] = longitud
        self.aviones[id_avion]["ground"] = on_ground
        self.aviones[id_avion]["rotacion"] = rotacion
        self.aviones[id_avion]["altura"] = altura

    def createMap(self, latitud=40.51, longitud=-3.53):
        mapa = folium.Map(
            location=[latitud, longitud], zoom_start=6.5
        )
        return mapa
    
    def addLayers(self):
        self.layers['radar']['capa'].add_to(self.mapa)
        self.layers['pistas']['capa'].add_to(self.mapa)
        self.layers['aviones'].add_to(self.mapa)
        self.layers['rutas'].add_to(self.mapa)
    
    # Función para determinar el color según la velocidad
    def get_color_by_speed(self,velocity):
        if velocity < 300:
            return "red"
        elif velocity < 450:
            return "yellow"
        else:
            return "green"

    def initializeMap(self, all=False):
        if all:
            self.paintRadars()
            self.paintLandingStrips()

        self.addLayers()
        self.layerControl.add_to(self.mapa)






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
                max_width=150,
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
                max_width=150,
            ),
            icon=folium.Icon(
                color=self.layers['pistas']['color'], icon="fa-solid fa-plane-arrival", prefix="fa"
            ),
        ).add_to(self.layers['pistas']['capa'])

        
    def paintLandingStrips(self):
        for pista in self.pistas:
            self.paintLandingStrip(pista['nombre'], pista["lat"], pista["lon"])




    def paintAirplanes(self):
            # Crear grupos de capas
        # capa_aviones = folium.FeatureGroup(name="Aviones")
        # capa_trayectorias = folium.FeatureGroup(name="Trayectorias")

        with open("assets/icons/airplane_air.svg", "r") as file:
            svg_data_air = file.read()

        with open("assets/icons/airplane_ground.svg", "r") as file:
            svg_data_ground = file.read()


        # Agregar trayectorias y marcadores
        for avion in self.aviones.keys():
            #print(len(self.aviones[avion]["trayectoria"]))
            # if len(self.aviones[avion]["trayectoria"]) > 1:
            altura = None
            for i in range(1, len(self.aviones[avion]["trayectoria"])):
                lat1, lon1, vel1 = self.aviones[avion]["trayectoria"][i-1]
                lat2, lon2, vel2 = self.aviones[avion]["trayectoria"][i]
                color = self.get_color_by_speed(vel1)
                altura = self.aviones[avion]["altura"]
                # Agregar una clase única para cada trayectoria
                polyline = folium.PolyLine(
                    [(lat1, lon1), (lat2, lon2)],
                    color=color,
                    weight=2,
                    opacity=0.8,
                    tooltip=f"Trayectoria Avión {avion}",
                    popup=f"Velocidad: {vel1} nudos -- Altura {altura}",
                    class_name=f"trayectoria trayectoria-{avion}"
                )
                self.layers['rutas'].add_child(polyline)  # Añadir la trayectoria a su capa

            if self.aviones[avion]["ground"]:
                svg_data = svg_data_ground
            else:
                svg_data = svg_data_air

            icon = folium.DivIcon(html=f"<div style='width:16px;height:16px; transform: rotate({self.aviones[avion]['rotacion'] * 180 / math.pi}deg);'>{svg_data}</div>")

            try:
            # Crear marcador para el avión
                marker = folium.Marker(
                    location=[self.aviones[avion]["lat"], self.aviones[avion]["lon"]],
                    icon=icon,
                    popup=f"Avión {avion} -- Altura: {altura} pies",
                    tooltip=f"Avión {avion}"
                )
            except Exception as e:
                print(self.aviones[avion]["lat"], self.aviones[avion]["lon"])
            self.layers['aviones'].add_child(marker)  # Añadir el marcador a su capa

    # Agregar las capas al mapa
        # self.mapa.add_child(capa_aviones)
        # self.mapa.add_child(capa_trayectorias)
        # self.mapa.add_child(capa_aviones)
        # self.mapa.add_child(capa_trayectorias)




    def generate_script(self):
    # Script JavaScript (funcionalidad de selección y ocultación de elementos)
        return """ 
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        let trayectoriasLengths = """ + json.dumps([len(avion["trayectoria"]) - 1 for avion in self.aviones.values()]) + """;
        console.log("TRAAAAA ",trayectoriasLengths)
        let selectedAvionId = null;

        function assignIdsToPaths() {
            let polylines = document.querySelectorAll('path.leaflet-interactive');
            let avionIndex = 0;
            let segmentCounter = 0;
            let ii = 0;
            polylines.forEach((path) => {
                console.log("ii=",ii)
                
                if (segmentCounter >= trayectoriasLengths[avionIndex]) {
                    avionIndex++;
                    segmentCounter = 0;
                    while (trayectoriasLengths[avionIndex] === 0){
                        avionIndex++;
                    }
                }
                let avionId = avionIndex;
                path.setAttribute('data-avion-id', avionId);
                console.log("PA ", avionId)
                segmentCounter++;
                
                ii = ii+ 1;
            });
        }

        function hideOthers(selectedId) {
            selectedAvionId = selectedId;

            document.querySelectorAll('.leaflet-marker-icon').forEach((marker, idx) => {
                marker.style.display = (idx === selectedId) ? 'block' : 'none';
            });

            document.querySelectorAll('path.leaflet-interactive').forEach(path => {
                let avionId = Number(path.getAttribute('data-avion-id'));
                path.style.display = (avionId === selectedId) ? 'block' : 'none';
            });
        }

        function resetAll() {
            document.querySelectorAll('.leaflet-marker-icon').forEach(marker => marker.style.display = 'block');
            document.querySelectorAll('path.leaflet-interactive').forEach(line => line.style.display = 'block');

            assignIdsToPaths();
            assignEventListeners();

            if (selectedAvionId !== null) {
                setTimeout(() => hideOthers(selectedAvionId), 100);
            }
        }

        function assignEventListeners() {
            document.querySelectorAll('.leaflet-marker-icon').forEach((el, idx) => {
                console.log("PATTTTTTTTTHH ", idx)
                el.addEventListener('click', () => hideOthers(idx));
            });
        }

        function activateAllLayers() {
            document.querySelectorAll('.leaflet-control-layers-selector').forEach(checkbox => {
                if (!checkbox.checked) {
                    checkbox.click(); // Activa las capas que estaban desactivadas
                }
            });

            setTimeout(() => resetAll(), 500); // Esperamos un poco para que se activen antes de resetear
        }

        const observer = new MutationObserver(() => {
            resetAll();
        });

        observer.observe(document.querySelector('.leaflet-control-layers'), { childList: true, subtree: true });

        resetAll();

        var button = document.createElement('button');
        button.innerText = 'Mostrar todos los aviones';
        button.style.position = 'absolute';
        button.style.top = '10px';
        button.style.right = '10px';
        button.style.zIndex = '1000';
        button.style.background = 'white';
        button.style.border = '1px solid black';
        button.style.padding = '5px';
        button.style.cursor = 'pointer';
        button.addEventListener('click', function() {
            selectedAvionId = null;
            activateAllLayers();
        });
        document.body.appendChild(button);
    });
    </script>
    """





    def saveMap(self, nombre_mapa):
            self.mapa.save(f"./mapas/{nombre_mapa}.html")

    def showMap(self, nombre_mapa=None):

        self.paintAirplanes()

        # self.mapa.add_child(folium.LayerControl())

        self.script = self.generate_script()

        self.mapa.get_root().html.add_child(folium.Element(self.script))

        if nombre_mapa is None:
            nombre_mapa = time.strftime("%d-%m-%Y_%H-%M-%S")
        
        if not os.path.exists(f"./mapas/{nombre_mapa}.html"):
            self.saveMap(nombre_mapa)
        webbrowser.open(f"file://{os.path.abspath(f"./mapas/{nombre_mapa}.html")}")

        #self.reset()

    def reset(self):
        self.mapa = self.createMap()
        self.initializeMap(all=False)
    # Agregar control de capas


    

m = MapV()

df = pd.read_csv("preprocess_mapa (2).csv")  #NO ES EL CONJUNTOD DE DATOS GRANDE
df["alt_feet"] = 0
# df = df.loc[:150]
for _, row in df.iterrows():
    # print(f"ON GROOUND {row["ground"]}-- LAT -- {row["lat"]} LON -- {row["lon"]}")
    if pd.notna(row["ground"]) and pd.notna(row["lat"]) and pd.notna(row["lon"]) and  row["ground"] is not None and row["lat"] is not None and row["lon"] is not None: #on ground
        print(f"ICAO -- {row["icao"]} , LAT -- {row["lat"]}, LON -- {row["lon"]}, VELOCITY -- {row["velocity"]}, DIRECCION -- {row["direccion"]}")
        m.addAirplane(row["icao"], row["lat"],row["lon"],row["ground"], row["direccion"], row["velocity"], row["alt_feet"])


m.showMap()
