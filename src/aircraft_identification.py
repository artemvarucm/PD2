import pyModeS as pms
from message_type import MessageType


"""
TC: ENTRE 1 y 4

DEVUELVE (EN ORDEN):
CALLSIGN
VORTEX_TYPE
"""


class AircraftIdentificationMessage(MessageType):

    def __init__(self, tc):
        # DICCIONARIO DE COMBINACIONES PARA VARIABLE VORTEX,PRIMER NIVEL CAT, SEGUNDO NIVEL TC
        self.vortexDictionary = {
            1: {
                0: "No category information",
                1: "Reserved",
                2: "Reserved",
                3: "Reserved",
                4: "Reserved",
                5: "Reserved",
                6: "Reserved",
                7: "Reserved"
            },
            2: {
                0: "No category information",
                1: "Surface emergency vehicle",
                2: "ERROR",
                3: "Surface service vehicle",
                4: "Ground obstruction",
                5: "Ground obstruction",
                6: "Ground obstruction",
                7: "Ground obstruction"
            },
            3: {
                0: "No category information",
                1: "	Glider, sailplane",
                2: "Lighter-than-air",
                3: "Parachutist, skydiver",
                4: "Ultralight, hang-glider, paraglider",
                5: "Reserved",
                6: "Unmanned aerial vehicle",
                7: "Space or transatmospheric vehicle"
            },
            4: {
                0: "No category information",
                1: "Light (less than 7000 kg)",
                2: "Medium 1 (between 7000 kg and 34000 kg)",
                3: "Medium 2 (between 34000 kg to 136000 kg)",
                4: "High vortex aircraft",
                5: "Heavy (larger than 136000 kg)",
                6: "High performance (>5 g acceleration) and high speed (>400 kt)",
                7: "Rotorcraft"
            }
        }

    def match(self, typecode):
        return typecode >= 1 and typecode <= 4