rad_lat = 40.51
rad_lon = -3.53
import pyModeS as pms

"""
TC: ENTRE 5 y 8
TRK (Trayectoria terrestre)
MOV (VELOCIDAD EN TIERRA)
LATITUD
LONGITUD
"""
def getSurfacePosition(hex, ref_lat, ref_lon):
    speed, trk, vertical_speed, tag = pms.adsb.velocity(hex)
    lat, lon = pms.adsb.position_with_ref(hex, ref_lat, ref_lon)
    return speed, trk, vertical_speed, tag, lat, lon





