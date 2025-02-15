from abc import ABC, abstractmethod
class Routes(ABC):
    formato_fechas = "%Y-%m-%d %H:%M:%S"

    @abstractmethod
    def paintRoute(id_avion):
        pass
    
    @abstractmethod
    def addLocation(id_avion, latitud, longitud, **kwargs):
        pass

    @abstractmethod
    def sameRoute(id_avion, timestamp):
        pass
    
    @abstractmethod
    def deleteAirplane(id_avion):
        pass
    
    @abstractmethod
    def reset():
        pass
        

