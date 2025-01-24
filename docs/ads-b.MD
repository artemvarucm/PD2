### ADS-B (Automatic Dependent Surveillance-Broadcast)
Es una tecnología de vigilancia diseñada para permitir que las aeronaves transmitan su estado de vuelo periódicamente sin necesidad de **interrogarlas**.
- [Downlink format](#downlink-format)
- [Estructura del mensaje](#estructura-del-mensaje)
- [Message types](#message-types)
- [Versiones](#versiones)


#### Downlink format

Permite especificar como se organizan los bits del mensaje para el Modo S (protocolo que se utiliza para la comunicación entre aircrafts aéreos, sin necesidad de enviar interrogación a todos los aviones).

Para el ADS-B se utilizan 2 formatos:

<span style="color:red">Importante! Probablemente el formato 18 no se necesita para la solución del problema</span>.
1. **DF 17**: 112 bits
2. **DF 18**: 112 bits, el mensaje proviene de un equipo que NO puede ser interrogado.

#### Estructura del mensaje
```
+----------+----------+-------------+------------------------+-----------+
|  DF (5)  |  CA (3)  |  ICAO (24)  |         ME (56)        |  PI (24)  |
+----------+----------+-------------+------------------------+-----------+
```

+ 1–5: 	Downlink Format (DF): numero que identifica la organización de los bits.
+ 6–8: Transponder capability (CA): nos dice que información el avión puede transmitir.
+ 9–32: ICAO aircraft address (ICAO): es un identificador del avion concreto para que se pueda identificar sin ambigüedad.
+ 33–88: Message, extended squitter (ME)
    + (33–37): (Type code): nos dice que información está codificada en el mensaje, ver más alante.
+ 89–112: Parity/Interrogator ID (PI): Son bits de paridad para asegurar que el contenido no ha sido alterado. (validación de datos)

<span style="color:red">Importante! Hay que ver si el procesamiento de un mensaje depende de transponder capability (en principio no deberia)</span>.


#### Message types

1–4: Aircraft identification

5–8: Surface position

9–18: Airborne position (w/Baro Altitude)

19: Airborne velocities

20–22: Airborne position (w/GNSS Height)

23–27: Reserved

28: Aircraft status

29: Target state and status information

31: Aircraft operation status

#### Versiones
Existen **tres** versiones (0, 1, 2).


La **Versión 1** se diferencia de la 0 principalmente en el **cambiar el control de la integridad de datos** y en **añadir nuevos tipos de mensajes (28 y 31)**.

La **Versión 2** se diferencia de la 1 principalmente en el **dos bits adicionales de suplemento NIC** con el NIC y en el **cambio de estructura y contenido de los tipos de mensajes 28 y 31**.


**Para identificar la versión**

1. Verifique si una aeronave está transmitiendo mensajes ADS-B con TC=31. Si nunca se informa de un mensaje, se puede asumir de manera segura que la versión es la versión 0.

2. Si se reciben mensajes con TC=31, verifique los números de versión ubicados en los bits 41–43 en ME (o los bits 73–75 en el mensaje).

<span style="color:red">Importante! Esto nos será importante para decodificar mensajes 28 (Aircraft status) y 31 (Aircraft operation status)</span>.