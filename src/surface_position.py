rad_lat = 40.51
rad_lon = -3.53
import pyModeS as pms

"""
TC: ENTRE 5 y 8
TRK (Trayectoria terrestre)
MOV (VELOCIDAD EN TIERRA)
"""
def getSurfacePosition(hex):
    speed, trk, vertical_speed, tag = pms.adsb.velocity(hex)



"""
Devuelve LA LATITUD Y LONGITUD DEL AVIÓN EN FUNCIÓN DEL RADAR
"""

def getSurfacePos(msg, ref_lat, ref_lon):
    lat, lon = pms.adsb.position_with_ref(msg, ref_lat, ref_lon)
    return lat, lon

