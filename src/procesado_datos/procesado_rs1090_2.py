import dask.dataframe as dd
import pandas as pd
import time
import pyModeS as pms
import base64

from pyproj import Transformer
from shapely.geometry import Point, Polygon

from dask.diagnostics import ProgressBar
import geopandas as gpd  # para leer el geojson


# Cargar el geojson de holding points (en CRS WGS84)
holding_points = gpd.read_file("data/geojson/holding_points.geojson")

# Reproyectar a un CRS métrico (por ejemplo, UTM 30N; usa el EPSG adecuado para tu zona)
holding_points_utm = holding_points.to_crs(epsg=32630)

# Crear un buffer de 50 metros alrededor de cada holding point
holding_points_utm['buffer'] = holding_points_utm.buffer(50)

# Crear un transformer para convertir puntos de WGS84 (EPSG:4326) a UTM (EPSG:32630)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32630", always_xy=True)

def transform_point(point):
    """Transforma un punto de WGS84 a UTM."""
    x, y = transformer.transform(point.x, point.y)
    return Point(x, y)

def find_holding_point_with_buffer(lon, lat):
    """
    Dado un par de coordenadas (en WGS84), transforma el punto a UTM y verifica
    si se encuentra dentro de alguno de los buffers de los holding points.
    Devuelve el DESIGNATOR (u otro identificador) si coincide o None.
    """
    if (lon is None or lat is None):
        return None

    point = Point(lon, lat)
    point_utm = transform_point(point)
    for idx, row in holding_points_utm.iterrows():
        if row['buffer'].contains(point_utm):
            return row.get("DESIGNATOR", f"holding_point_{idx}")

    return None


def find_runway(lon, lat):
    point = Point(lon, lat)
    if rwy_polygon_18R_36L.contains(point):
        return "18R/36L"
    elif rwy_polygon_18L_36R.contains(point):
        return "18L/36R"
    elif rwy_polygon_14L_32R.contains(point):
        return "14L/32R"
    elif rwy_polygon_14R_32L.contains(point):
        return "14R/32L"
    else:
        return None



# 3. Función para segmentar vuelos por grupo (por cada ICAO)
def segmentar_vuelos(grupo: pd.DataFrame) -> pd.DataFrame:
    """
    Para un grupo de mensajes (un mismo ICAO) ordenados cronológicamente,
    se detecta la transición: se guarda el último instante en que el avión está en tierra
    (OnGround == 1) y, en cuanto se detecta el primer mensaje con OnGround == 0, se calcula el tiempo
    de espera (diferencia de timestamps).
    Se reinicia la marca de tierra para detectar ciclos sucesivos.
    """
    grupo = grupo.sort_values("timestamp")

    eventos = [] # tiene los puntos de espera de TODOS los despegues
    eventos_provisional = [] # tiene los puntos de espera de 1 despegue
    visited_hp = set()

    # Variables para seguimiento de estado
    ultimaLat, ultimaLon = None, None
    aircraftType = None

    for _, row in grupo.iterrows():
        # Si el mensaje es de superficie y se puede decodificar la velocidad,
        # y esta es exactamente 0, se considera que el avión está parado.
        if (aircraftType is None and 
            pd.notna(row["AircraftType"]) and 
            row["AircraftType"] not in ["No category information", "Reserved", "ERROR"]
            ):
            # se queda con el primer tipo emitido por el avion (si emite un mensaje con otro tipo se descarta)
            aircraftType = row["AircraftType"]

        if pd.notna(row.get("surface_velocity")):
            parado = row["surface_velocity"] == 0
            hp = find_holding_point_with_buffer(row["lon"], row["lat"])
            if (hp is not None and hp not in visited_hp):
                # si es la primera vez que pasa por este punto
                visited_hp.add(hp)
                eventos_provisional.append({
                    "ICAO": row["ICAO"],
                    "llegada_punto": row["timestamp"],
                    "salida_punto": None,
                    "despegue": None,
                    "tiempo_espera": None,
                    "aircraft_type": aircraftType,
                    "llegada_lon": row["lon"],
                    "llegada_lat": row["lat"],
                    "salida_lon": None,
                    "salida_lat": None,
                    "holding_point": hp,
                    "parado": parado
                })
            if len(eventos_provisional) > 0:
                if (
                    (hp is None or hp != eventos_provisional[-1]["holding_point"])
                    and eventos_provisional[-1]["salida_punto"] is None
                    ):
                    # si se ha movido a otro punto o se ha salido de este
                    eventos_provisional[-1]["salida_punto"] = row["timestamp"]
                    eventos_provisional[-1]["salida_lon"] = row["lon"]
                    eventos_provisional[-1]["salida_lat"] = row["lat"]
                elif (hp == eventos_provisional[-1]["holding_point"]):
                    # se ha parado en el punto de espera
                    eventos_provisional[-1]["parado"] = True if (parado or eventos_provisional[-1]["parado"]) else False

        if (pd.notna(row.get("lat")) and pd.notna(row.get("lon"))):
            ultimaLat = row["lat"]
            ultimaLon = row["lon"]

        # Cuando se detecta que el avión ya está en aire (OnGround == 0)
        if (row["OnGround"] == 0 and row["DL"] == 11):
            if bool(visited_hp): # si ha visitado algun punto
                tiempo_despegue = row["timestamp"]
                
                # posicion final al despegar
                if eventos_provisional[-1]["salida_punto"] is None:
                    eventos_provisional[-1]["salida_punto"] = row["timestamp"]
                
                if eventos_provisional[-1]["salida_lat"] is None or eventos_provisional[-1]["salida_lon"] is None:
                    eventos_provisional[-1]["salida_lat"] = ultimaLat
                    eventos_provisional[-1]["salida_lon"] = ultimaLon

                runway = find_runway(ultimaLon, ultimaLat) # pista de despegue
                for evento in eventos_provisional:
                    evento["despegue"] = tiempo_despegue
                    evento["tiempo_espera"] = (tiempo_despegue - evento["llegada_punto"]).total_seconds()
                    evento["runway"] = runway
                    #evento["lat"] = ultimaLat
                    #evento["lon"] = ultimaLon
                    eventos.append(evento)

                # puede tener varios despegues, seguimos
                ultimaLat, ultimaLon = None, None
                aircraftType = None
                visited_hp.clear()
                eventos_provisional.clear()

    return pd.DataFrame(eventos)


rwy_polygon_18R_36L = Polygon([
    (-3.582, 40.492383), (-3.5695, 40.492383), (-3.5695, 40.537929), (-3.582, 40.537929)
])

rwy_polygon_18L_36R = Polygon([
    (-3.564441, 40.499172), (-3.549, 40.499172), (-3.549, 40.537472), (-3.564441, 40.537472)
])

rwy_polygon_14L_32R = Polygon([
    (-3.531683, 40.464310), (-3.524645, 40.468620), (-3.556317, 40.498519), (-3.564652, 40.495647)
])

rwy_polygon_14R_32L = Polygon([
    (-3.547648, 40.450661), (-3.539580, 40.454710), (-3.575714, 40.488141), (-3.582924, 40.484224)
])

meta = {
    "ICAO": str,
    "llegada_punto": "datetime64[ns]",
    "salida_punto": "datetime64[ns]",
    "despegue": "datetime64[ns]",
    "tiempo_espera": float,
    "aircraft_type": str,
    "llegada_lon": "float64",
    "llegada_lat": "float64",
    "salida_lon": "float64",
    "salida_lat": "float64",
    "holding_point": str,
    "parado": bool,
    "runway": str
}



df = dd.read_csv("datos_prueba.csv", sep=",", parse_dates=["timestamp"], dtype={'AircraftType': 'object'})

# elimina tipos de aviones raros (no info, emergency vehicles...)

#filtro1 = df["wake_vortex"].isna()
#filtro2 = df["wake_vortex"].isin(["<7000kg", "<34,000kg", "<136,000kg", "High vortex", "Heavy", "High performance", "Rotorcraft"])
#df = df[filtro1 | filtro2]
eventos_espera = df.groupby("ICAO").apply(segmentar_vuelos, meta=meta)

eventos_espera["fecha_despegue"] = eventos_espera["despegue"].dt.date
eventos_espera["hora_despegue"] = eventos_espera["despegue"].dt.hour

with ProgressBar():
    eventos_espera = eventos_espera.compute()
    
    estadisticas_por_dia_hora = eventos_espera.groupby(
        ["fecha_despegue", "hora_despegue"]
    )["tiempo_espera"].agg(["mean", "median", "count"]).reset_index()

    print("Estadísticas de tiempo de espera (en segundos) por hora de despegue:")
    print(estadisticas_por_dia_hora)

    eventos_espera.to_csv('eventos_espera_semana_hp.csv', index=False)