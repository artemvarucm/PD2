import pyModeS as pms
from message_type import MessageType

class AirbornePositionMessage(MessageType):
    def __init__(self):
        # CONSTANTES DE DONDE SE SITUA EL RADAR
        self.RAD_LAT = 40.51
        self.RAD_LON = -3.53

        # DECODERS 
        self.surveillance_status_decoder = {0: "no_condition", 1: "permanent_alert", 2: "temporary_alert", 3: "SPI_condition"}
        self.CPR_decoder = {0: "even_frame", 1: "odd_frame"}


    def match(self, typecode):
        return (typecode >= 9 and typecode <= 18) or (typecode >= 20 and typecode <= 22)

    def get_typecode(self, msg):
        return pms.common.typecode(msg)

    def hex2bin(self, msg):
        return pms.common.hex2bin(msg)

    def bin2int(self, msg):
        return pms.common.bin2int(msg)

    def extractAltitudeType(self, msg):
        if 9 <= msg <= 18:
            return "airborne_barometric_alt"
        elif 20 <= msg <= 22:
            return "airborne_gnss_alt"
        else:
            return None
    
    def getSingleAntennaFlag(self, msg_bin):
        bit_single_antenna_flag = 7
        msg_antenan_bin = msg_bin[bit_single_antenna_flag]
        return msg_antenan_bin

    def getTime(self, msg_bin):
        bit_time = 20
        msg_time_bin = msg_bin[bit_time]
        return msg_time_bin

    def getCPRFormat(self, msg_bin):
        bit_time = 21
        msg_CPR_bin = msg_bin[bit_time]
        msg_CPR = self.bin2int(msg_CPR_bin)
        return self.CPR_decoder[msg_CPR]

    def getSurveillanceStatus(self, msg_bin):
        msg_status_bin = msg_bin[5:7]
        msg_status_int = self.bin2int(msg_status_bin)
        return self.surveillance_status_decoder[msg_status_int]
    
    def getAirbornePosition(self, hex):
        lat, lon = pms.adsb.airborne_position_with_ref(hex, self.RAD_LAT, self.RAD_LON)
        return lat, lon
    
    def updateRowFromHex(self, row, hex):
        row["airborne_pos_single_antenna_flag"] = self.getSingleAntennaFlag(self.hex2bin(hex))
        row["airborne_pos_surveillance_status"] = self.getSurveillanceStatus(self.hex2bin(hex))
        row["airborne_pos_time"] = self.getTime(self.hex2bin(hex))
        row["airborne_pos_CPR"] = self.getCPRFormat(self.hex2bin(hex))
        row["airborne_pos_altitude_type"] = self.extractAltitudeType(self.get_typecode(hex))
        
        lat, lon = self.getAirbornePosition(hex)
        row["airborne_pos_lat"] = lat
        row["airborne_pos_lon"] = lon

