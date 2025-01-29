"""
TC: ENTRE 5 y 8
"""
def getSurfacePosition(hex):
    pass


"""
Devuelve la TRK (Trayectoria terrestre)
"""
def getGroundTrack(status, grdValue):
    if status == 0:
        return "INVALID"
    else:
        return grdValue * 360 / 128


"""
Devuelve la MOV (VELOCIDAD EN TIERRA)
"""
def getMovement(speedValue):
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