"""
Clase abstracta para el patrón de diseño Command,
que permitirá actualizar la fila del dataframe según el tipo del mensaje
"""
class MessageType:
    """
    Devuelve True si el mensaje devuelto es del tipo necesario
    """

    def match(self, typecode):
        pass

    """
    Actualiza el objeto de tipo Series que se pasa a partir del nuevo mensaje
    """

    def updateRowFromHex(self, row, hex):
        pass
