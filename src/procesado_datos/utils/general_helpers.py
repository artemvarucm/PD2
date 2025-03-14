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

def msgIsCorrupted(hex):
    return (pms.crc(hex) != 0)

def getOnGround(hex):
    decimal_value =  pms.bin2int(pms.hex2bin(hex)[5:8]) 
    if decimal_value == 4:
        return 1
    elif decimal_value == 5:
        return 0
    else:
        return None