import pyModeS as pms
from message_type import MessageType

"""
TC: ENTRE 5 y 8

DEVUELVE (EN ORDEN):
LATITUD
LONGITUD
SURFACE_VELOCITY - velocidad de la aeronave mientras está en la superficie
GROUND_STATUS - Indica si la aeronave está en movimiento o detenida en la superficie del aeropuerto.
GROUND_TRACK - dirección o ángulo de trayectoria sobre la tierra en grados desde el norte verdadero, indicando hacia dónde se dirige la aeronave mientras se mueve en la superficie.

"""


class SurfacePositionMessage(MessageType):
    def __init__(self):
        # CONSTANTES DE DONDE SE SITUA EL RADAR
        self.RAD_LAT = 40.51
        self.RAD_LON = -3.53

    def match(self, typecode):
        return typecode >= 5 and typecode <= 8
            
    def updateRowFromHex(self, row, hex):
        lat, lon = self.getSurfacePosition(hex)
        binary_message = pms.hex2bin(hex)
        encoded_speed = int(binary_message[37:44], 2)
        encoded_track = int(binary_message[45:52], 2)
        row["latitude"] = lat
        row["longitude"] = lon
        row["surface_velocity"] = self.getMovement(encoded_speed)
        row["ground_track"] = self.decode_ground_track(encoded_track, binary_message[44])

    def getSurfacePosition(self, hex):
        lat, lon = pms.adsb.position_with_ref(hex, self.RAD_LAT, self.RAD_LON)
        return lat, lon
    
    def getMovement(self, speedValue):
        if speedValue == 0:
            return 'SPEED NOT AVAILABLE'
        elif speedValue == 1:
            return 'STOPPED (v < 0.125 kt)'
        elif speedValue < 9:
            return (speedValue - 2)* 0.125 + 0.125
        elif speedValue < 13:
            return (speedValue - 9)* 0.25 + 1
        elif speedValue < 39:
            return (speedValue - 13)* 0.5 + 2
        elif speedValue < 94:
            return (speedValue - 39)* 1 + 15
        elif speedValue < 109:
            return (speedValue - 94)* 2 + 70
        elif speedValue == 124:
            return 'MAX (v >= 175 kt)'
        else:
            return 'RESERVED'
        
    def decode_ground_track(self, encoded_track, status_bit):
        if status_bit == '0':
            ground_track = (encoded_track / 128) * 360
            return ground_track
        else:
            return "invalid"