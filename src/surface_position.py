import pyModeS as pms
from message_type import MessageType

"""
TC: ENTRE 5 y 8

DEVUELVE (EN ORDEN):
VELOCIDAD EN TIERRA - velocidad a la que la aeronave se mueve a lo largo de la superficie de la Tierra
TRAYECTORIA TERRESTRE - dirección hacia la cual se dirige la aeronave en grados desde el norte verdadero
VELOCIDAD VERTICAL - tasa a la que la aeronave está ascendiendo o descendiendo
VERTICAL RATE SOURCE INDICATOR - indicador que muestra si la velocidad vertical es basada en una medición barométrica o geométrica.
LATITUD
LONGITUD
"""


class SurfacePositionMessage(MessageType):
    def __init__(self):
        # CONSTANTES DE DONDE SE SITUA EL RADAR
        self.RAD_LAT = 40.51
        self.RAD_LON = -3.53

    def match(self, typecode):
        return typecode >= 5 and typecode <= 8

    def updateRowFromHex(self, row, hex):
        speed, trk, vertical_speed, tag = pms.adsb.velocity(hex)
        lat, lon = self.getSurfacePosition(hex)
        row["latitude"] = lat
        row["longitude"] = lon
        row["velocity"] = speed
        row["true_track"] = trk
        row["vertical_rate"] = vertical_speed
        row["vrsi"] = tag

    def getSurfacePosition(self, hex):
        lat, lon = pms.adsb.position_with_ref(hex, self.RAD_LAT, self.RAD_LON)
        return lat, lon
