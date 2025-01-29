import pyModeS as pms

"""
TC: ENTRE 5 y 8
TRK (Trayectoria terrestre)
MOV (VELOCIDAD EN TIERRA)
"""
def getSurfacePosition(hex):
    speed, trk, vertical_speed, tag = pms.adsb.velocity(hex)