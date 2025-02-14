from plugins.geocoder import Geocoder
from plugins.day_and_night import DayAndNight
from plugins.full_screen import Fullscreen
from plugins.locate_user import LocateUser
from plugins.mouse_position import MousePosition

class ExtraFeatures:
    def __init__(self):
        pass
    
    def addGeocoder(self, mapa):
        """Añade el geocoder al mapa"""
        Geocoder(collapsed=True, position="topleft", add_marker=False, zoom=12).add_to(mapa)

    def addDayAndNight(self, mapa):
        """Añade día y noche al mapa"""
        DayAndNight().add_to(mapa)
    
    def addFullScreen(self, mapa):
        """Añade el control de pantalla completa al mapa"""
        Fullscreen(position="bottomright").add_to(mapa)

    def addLocateUser(self, mapa):
        """Añade la opción para que el usuario se localice en el mapa"""
        LocateUser(position="topleft").add_to(mapa)
    
    def addMousePosition(self, mapa):
        """Añade la posición del ratón en el mapa"""
        MousePosition(position="bottomleft", separator=",", num_digits=3).add_to(mapa)

    def addExtraFeatures(self, mapa):
        """Añade todas las funcionalidades extras al mapa"""
        self.addGeocoder(mapa)
        self.addDayAndNight(mapa)
        self.addFullScreen(mapa)
        self.addLocateUser(mapa)
        self.addMousePosition(mapa)

    
