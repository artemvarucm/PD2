from plugins.geocoder import Geocoder
from plugins.day_and_night import DayAndNight
from plugins.full_screen import Fullscreen
from plugins.locate_user import LocateUser
from plugins.mouse_position import MousePosition
from plugins.search_bar import SearchBar


class ExtraFeatures:
    def __init__(self):
        pass
    
    @staticmethod
    def addGeocoder(mapa):
        """Añade el geocoder al mapa"""
        Geocoder(collapsed=True, position="topleft", add_marker=False, zoom=12).add_to(mapa)

    @staticmethod
    def addDayAndNight(mapa):
        """Añade día y noche al mapa"""
        DayAndNight().add_to(mapa)
    
    @staticmethod
    def addFullScreen(mapa):
        """Añade el control de pantalla completa al mapa"""
        Fullscreen(position="bottomright").add_to(mapa)

    @staticmethod
    def addLocateUser(mapa):
        """Añade la opción para que el usuario se localice en el mapa"""
        LocateUser(position="topleft").add_to(mapa)
    
    @staticmethod
    def addMousePosition(mapa):
        """Añade la posición del ratón en el mapa"""
        MousePosition(position="bottomleft", separator=",", num_digits=3).add_to(mapa)
    
    """
    @staticmethod
    def addSearchBar(mapa, capa):
        SearchBar(
            layer=capa,
            geom_type="Polygon",
            placeholder="Search for a US State",
            collapsed=False,
            search_label="icao",
            weight=3,
        ).add_to(mapa)"""

    @staticmethod
    def addExtraFeatures(mapa):
        """Añade todas las funcionalidades extras al mapa"""
        ExtraFeatures.addGeocoder(mapa)
        ExtraFeatures.addDayAndNight(mapa)
        ExtraFeatures.addFullScreen(mapa)
        ExtraFeatures.addLocateUser(mapa)
        ExtraFeatures.addMousePosition(mapa)

    
