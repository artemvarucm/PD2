import base64
import pandas as pd
import pyModeS as pms
from message_type import MessageType



class AirborneVelocity(MessageType):
    
    def match(self,typecode):
        return typecode == 19
    
    def updateRowFromHex(self,row,hex):
        row["V"],row["H"],row["VR"],row["VT"] = pms.adsb.velocity(hex) ## speed,track angle (heading), vertical speed,speed type
        row["ST"] = self.get_subtype(hex)
        row["IC"] = self.get_intent_change_flag(hex)
        row["IFR"] = self.get_ifr_capability_flag(hex)
        row["NUC"] = self.get_navigation_uncertainty_category(hex)
        row["VrSrc"]= self.get_source_bit_vertical_rate(hex)
        row["Svr"]= self.get_sign_bit_for_vertical_rate(hex)
        row["SDif"] = self.get_sign_gnss_baro_difference(hex)
        row["dAlt"] = self.get_difference_gnss_baro_altitudes(hex,row["SDif"])
        ##row["VR"] = self.get_vertical_rate(hex,row["Svr"])
        if row["ST"] == 1 or row["ST"] == 2:
            row["Dew"] = self.get_direction_east_west(hex)
            row["Vew"] = self.get_east_west_velocity(hex,row["ST"])
            row["Dns"] = self.direction_north_south(hex)
            row["Vns"] = self.get_north_south_velocity(hex,row["ST"])
        elif row["ST"] == 3 or row["ST"] == 4:
            row["SH"]= self.get_status_bit_for_magnetic_heading(hex)
            row["HDG"] = self.get_magnetic_heading(hex)
            row["T"] = self.get_airspeed_type(hex)
      

    
    ## Auxiliar functions
    def get_subtype(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[37:40])
    
    def get_intent_change_flag(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[40])

    ## Instrument Flight Rules Capability Flag 
    def get_ifr_capability_flag(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[41])

    ## Navigation Uncertainty Category for velocity
    
    def get_navigation_uncertainty_category(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[42:45])
        
    ## Vertical Rate


    def get_source_bit_vertical_rate(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[37])

    def get_sign_bit_for_vertical_rate(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[68])

    def get_vertical_rate(self,hex,svr):
        decimal_value = pms.bin2int(pms.hex2bin(hex)[69:78])
        return 64 * (decimal_value - 1) if svr == 0 else -64 * (decimal_value - 1)
    

    ## GNSS Baro Difference

    def get_sign_gnss_baro_difference(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[80])
    
    def get_difference_gnss_baro_altitudes(self,hex,sign_bit):
        return sign_bit * (pms.bin2int(pms.hex2bin(hex)[81:88]) - 1)
    

    ## Function for subtype 1 and 2
    def get_direction_east_west(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[45])  
    
    def get_east_west_velocity(self,hex,subtype):
        return pms.bin2int(pms.hex2bin(hex)[46:56]) -1 if subtype ==1 else 4* (pms.bin2int(pms.hex2bin(hex)[46:56]) -1)
    
    def direction_north_south(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[56])
    
    def get_north_south_velocity(self,hex,subtype):
        return pms.bin2int(pms.hex2bin(hex)[57:67]) -1 if subtype ==1 else 4* (pms.bin2int(pms.hex2bin(hex)[57:67]) -1)

    ## Function for subtype 3 and 4

    def get_status_bit_for_magnetic_heading(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[45])
    
    def get_magnetic_heading(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[46:56])
    
    ## Airspeed type	
    def get_airspeed_type(self,hex):
        return pms.bin2int(pms.hex2bin(hex)[56])
    

     ##   def get_airspeed(hex, subtipe):
   ##     return pms.bin2int(pms.hex2bin(hex)[57:67])

