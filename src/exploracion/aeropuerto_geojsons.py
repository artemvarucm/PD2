# Cargar el GeoJSON de holding points
# Asegúrate de que "holding_points.geojson" esté en el path o especifica la ruta correcta
import geopandas as gpd  # para leer el geojso

import matplotlib.pyplot as plt

# Cargar los archivos GeoJSON
holding_points = gpd.read_file("../../data/geojson/holding_points.geojson")
taxiways = gpd.read_file("../../data/geojson/taxiways.geojson")
runways = gpd.read_file("../../data/geojson/runways.geojson")

# Crear la figura y los ejes
fig, ax = plt.subplots(figsize=(10, 10))

# Graficar cada capa con un color diferente
runways.plot(ax=ax, color="gray", edgecolor="black", linewidth=2, label="Runways")
taxiways.plot(ax=ax, color="orange", edgecolor="black", alpha=0.7, label="Taxiways")
holding_points.plot(ax=ax, color="red", markersize=50, alpha=0.9, label="Holding Points")

# Añadir título y leyenda
plt.title("Mapa del Aeropuerto: Holding Points, Taxiways y Runways")
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.legend()

# Mostrar el mapa
plt.show()

