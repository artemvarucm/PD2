import base64
import pyModeS as pms

def base64toHEX(b64):
    return base64.b64decode(b64).hex()

def getDownlink(hex):
    return pms.df(hex)

def getTypeCode(hex):
    return pms.common.typecode(hex)

def getICAO(hex):
    return str(pms.common.icao(hex))