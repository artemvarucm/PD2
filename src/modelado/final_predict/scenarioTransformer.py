import os
import pandas as pd
from shapely.geometry import Point, Polygon
from pyproj import Transformer
import geopandas as gpd
import numpy as np

GS_THR = 80 # limite de velocidad cuando va a despegar

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

# Cargar el geojson de holding points (en CRS WGS84)
holding_points = gpd.read_file("/Users/alewar/Documents/Universidad/Tercero/PD2/PD2/data/geojson/holding_points.geojson")

# Reproyectar a un CRS métrico (por ejemplo, UTM 30N; usa el EPSG adecuado para tu zona)
holding_points_utm = holding_points.to_crs(epsg=32630)

# Crear un buffer de 25 metros alrededor de cada holding point
holding_points_utm['buffer'] = holding_points_utm.buffer(25)

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
    if (pd.isna(lon) or pd.isna(lat) or lon is None or lat is None):
        return None

    point = Point(lon, lat)
    point_utm = transform_point(point)
    for idx, row in holding_points_utm.iterrows():
        if row['buffer'].contains(point_utm):
            return row.get("DESIGNATOR", f"holding_point_{idx}")

    return None


def find_runway(lon, lat):
    point = Point(lon, lat)
    if (pd.isna(lon) or pd.isna(lat)):
        return None

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

"""
Función para sacar runway_occupied, queue_length y time_since_free

Parameters
----------
row : fila del DataFrame
runway_intervals : dicccionario que guarda por cada pista, tiene la lista ordenada de intervalos de tiempo cuando estaba ocupada
runway_despegues : dicccionario que guarda por cada pista, tiene la lista ordenada de los despegues
"""
def get_queue_features(row, runway_intervals, runway_despegues):
    runway = row['runway']
    current_ts       = row['timestamp']
    intervals = runway_intervals.get(runway)
    desps     = runway_despegues.get(runway)

    if intervals is None or desps is None:
        return pd.Series({
            'runway_occupied':  0,
            'queue_length':     0,
            'time_since_free':  np.nan
        })

    contains = intervals.contains(current_ts) # devuelve boolean por cada intervalo, vale True si contiene el número
    # pueden haber varios aviones que están en la pista o han salido de su punto de espera 
    # (por lo de punto de "preespera" y "postespera")
    queue_length    = int(contains.sum())

    idx = desps.searchsorted(current_ts) # devuelve el índice donde tendrías que insertar el elemento
    if idx == 0:
        time_since_free = np.nan # no hay ningún despegue
    else:
        last_departure = desps[idx-1] # el último despegue más cercano a current_ts
        time_since_free = (current_ts - last_departure).total_seconds()

    return pd.Series({
        'runway_occupied':  int(queue_length > 0),
        'queue_length':     queue_length,
        'time_since_free':  time_since_free
    })

"""
Para sacar la variable hold_pt_occupied

Parameters
----------
row : fila del DataFrame
holding_intervals : dicccionario que guarda por cada pista, tiene la lista ordenada de intervalos de tiempo cuando estaba ocupada
"""
def get_hold_pt_occupied(row, holding_intervals):
    runway = row['runway']
    current_ts = row['timestamp']
    runway_to_holding = {
        '14L/32R': ['K1', 'K2', 'K3'],
        '14R/32L': ['L1', 'LA', 'LB', 'LC', 'LE'],
        '18L/36R': ['Y1', 'Y2', 'Y3'],
        '18R/36L': ['Z1', 'Z2', 'Z3', 'Z4', 'Z6']
    }


    count = 0
    for hold_pt in runway_to_holding[runway]:
        if hold_pt != row['holding_point']:
            intervals = holding_intervals.get(hold_pt)
            if intervals is None or intervals.empty:
                continue
            contains = intervals.contains(current_ts) # devuelve boolean por cada intervalo, vale True si contiene el número
            if contains.any():
                count += 1

    return pd.Series({
        'hold_pt_occupied': count,
    })


def segmentar_vuelos(grupo: pd.DataFrame) -> pd.DataFrame:
    """
    Para un grupo de mensajes (un mismo ICAO) ordenados cronológicamente,
    se detecta la transición: se guarda el último instante en que el avión está en tierra
    (OnGround == 1) y, en cuanto se detecta el primer mensaje con OnGround == 0, se calcula el tiempo
    de espera (diferencia de timestamps).
    Se reinicia la marca de tierra para detectar ciclos sucesivos.
    """
    grupo = grupo.sort_values("timestamp")

    eventos = []  # tiene los puntos de espera de TODOS los despegues
    eventos_provisional = []  # tiene los puntos de espera de 1 despegue
    visited_hp = set()

    # Variables para seguimiento de estado
    ultimaLat, ultimaLon = None, None
    aircraftType = None

    for _, row in grupo.iterrows():
        # Si el mensaje es de superficie y se puede decodificar la velocidad,
        # y esta es exactamente 0, se considera que el avión está parado.
        if (aircraftType is None and
                pd.notna(row["aircraft_type"]) and
                row["aircraft_type"] not in ["No category information", "Reserved", "ERROR"]
        ):
            # se queda con el primer tipo emitido por el avion (si emite un mensaje con otro tipo se descarta)
            aircraftType = row["aircraft_type"]

        if pd.notna(row.get("groundspeed")):
            parado = row["groundspeed"] == 0
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

        # Cuando se detecta que el avión ya está en aire
        if pd.notna(row.get("groundspeed")) and (row["groundspeed"] > GS_THR):
            if bool(visited_hp):  # si ha visitado algun punto
                tiempo_despegue = row["timestamp"]

                # posicion final al despegar
                if eventos_provisional[-1]["salida_punto"] is None:
                    eventos_provisional[-1]["salida_punto"] = row["timestamp"]

                if eventos_provisional[-1]["salida_lat"] is None or eventos_provisional[-1]["salida_lon"] is None:
                    eventos_provisional[-1]["salida_lat"] = ultimaLat
                    eventos_provisional[-1]["salida_lon"] = ultimaLon

                runway = find_runway(ultimaLon, ultimaLat)  # pista de despegue
                for evento in eventos_provisional:
                    evento["despegue"] = tiempo_despegue
                    evento["tiempo_espera"] = (tiempo_despegue - evento["llegada_punto"]).total_seconds()
                    evento["runway"] = runway
                    # evento["lat"] = ultimaLat
                    # evento["lon"] = ultimaLon
                    eventos.append(evento)

                # puede tener varios despegues, seguimos
                ultimaLat, ultimaLon = None, None
                aircraftType = None
                visited_hp.clear()
                eventos_provisional.clear()

    ### NUEVO ###
    if bool(visited_hp): # para meter justo aviones que no han despegado (incluyendo el avion a predecir)
        runway = find_runway(ultimaLon, ultimaLat)  # pista de despegue
        for evento in eventos_provisional:
            evento["runway"] = runway
            eventos.append(evento)

    return pd.DataFrame(eventos)

def get_preprocessed_scenario(inputPath, avion_a_predecir):
    df = pd.read_parquet(inputPath)
    # Renombrar columnas
    df = df.rename(columns={
        'icao24':        'ICAO',
        'groundspeed':   'groundspeed',
        'altitude':      'altitude',
        'vertical_rate': 'vertical_rate',
        'lat_deg':       'lat',
        'lon_deg':       'lon',
        'wake_vortex':   'aircraft_type',
        'ts': 'ts_kafka'
    })
    df['timestamp'] = pd.to_datetime(df['ts_kafka'], unit='ms')

    CURRENT_TS = df['timestamp'].max() # será el tiempo actual, se asume que el avion a predecir está parado todavía
    
    eventos_espera = df.groupby("ICAO").apply(segmentar_vuelos)

    eventos_espera["despegue"] = pd.to_datetime(eventos_espera["despegue"])

    eventos_espera["fecha_despegue"] = eventos_espera["despegue"].dt.date
    eventos_espera["hora_despegue"] = eventos_espera["despegue"].dt.hour

    ### 2da parte, variables adicionales
    despegue_predecir = eventos_espera[
        (eventos_espera.ICAO == avion_a_predecir["icao"]) &
        (eventos_espera.holding_point == avion_a_predecir["holding_point"]) &
        (eventos_espera.runway == avion_a_predecir["runway"])
    ]

    if despegue_predecir.empty:
        return None
        
    despegue_predecir["timestamp"] = CURRENT_TS
    despegue_predecir["tiempo_esperado"] = (CURRENT_TS - despegue_predecir["llegada_punto"].values[0]).total_seconds()

    # Diccionarios por pista
    runway_intervals = {}
    runway_despegues = {}
    for runway, group in eventos_espera.groupby('runway'):
        # intervalos de ocupación completos
        runway_intervals[runway] = pd.IntervalIndex.from_arrays(
            group['salida_punto'],
            group['despegue'],
            closed='both'
        )
        # datetimes ordenados de despegue
        runway_despegues[runway] = pd.DatetimeIndex(group['despegue'].dropna()).sort_values()

    # lo mismo, pero para la ocupación de puntos de espera
    holding_intervals = {}
    for hold_pt, group in eventos_espera.groupby('holding_point'):
        holding_intervals[hold_pt] = pd.IntervalIndex.from_arrays(
            group['llegada_punto'],
            group['salida_punto'].fillna(CURRENT_TS),
            closed='both'
        )

    despegue_predecir[['runway_occupied','queue_length','time_since_free']] = despegue_predecir.apply(
        lambda row: get_queue_features(row, runway_intervals, runway_despegues), axis=1)
    
    despegue_predecir[['hold_pt_occupied']] = despegue_predecir.apply(
        lambda row: get_hold_pt_occupied(row, holding_intervals), axis=1)
    
    return despegue_predecir.reset_index(drop=True)
    
