import os
import pandas as pd
from io import StringIO
from google import genai
from google.genai import types

# Simulación del contenido CSV. En la práctica, podrías leer de un archivo.
csv_data = """ICAO,ultimo_parado,despegue,tiempo_espera,aircraft_type,lat,lon,holding_point,fecha_despegue,hora_despegue,runway
3420ca,2024-12-03 15:21:22.843,2024-12-03 15:23:03.503,100.66,"Medium 2 (between 34000 kg to 136000 kg)",40.50596237182617,-3.559234619140625,Y2,2024-12-03,15,18L/36R
3420ca,2024-12-04 09:24:55.891,2024-12-04 09:26:36.177,100.286,"Medium 2 (between 34000 kg to 136000 kg)",40.504462031994834,-3.5592113841663706,Y1,2024-12-04,9,18L/36R
3420ca,2024-12-04 16:16:10.860,2024-12-04 16:17:46.200,95.34,"Medium 2 (between 34000 kg to 136000 kg)",40.49863815307617,-3.57464599609375,Z4,2024-12-04,16,18R/36L
3420ca,2024-12-07 20:14:55.509,2024-12-07 20:16:48.101,112.592,"Medium 2 (between 34000 kg to 136000 kg)",40.50461332676774,-3.5592113841663706,Y1,2024-12-07,20,18L/36R
3444c3,2024-12-02 14:42:10.407,2024-12-02 14:43:51.726,101.319,"Medium 2 (between 34000 kg to 136000 kg)",40.505823684951004,-3.5592269897460938,Y1,2024-12-02,14,18L/36R
"""

# Cargamos los datos en un DataFrame
df = pd.read_csv(StringIO(csv_data))

def consultar_icao(icao: str, campo: str):
    """
    Realiza una consulta en el DataFrame para un ICAO y devuelve los valores del campo solicitado.
    """
    df_icao = df[df['ICAO'] == icao]
    if df_icao.empty:
        return f"No se encontraron registros para el ICAO '{icao}'."
    if campo not in df_icao.columns:
        return f"El campo '{campo}' no existe en la base de datos."
    # Se devuelven los valores encontrados. Puedes adaptar la respuesta, por ejemplo, mostrando el primer valor o un resumen.
    valores = df_icao[campo].tolist()
    return valores

# Declaración de la función para la API
query_icao_function = {
    "name": "query_icao",
    "description": "Consulta datos de un ICAO específico para un campo determinado usando pandas.",
    "parameters": {
        "type": "object",
        "properties": {
            "icao": {
                "type": "string",
                "description": "Código ICAO para consultar (por ejemplo, '3420ca').",
            },
            "campo": {
                "type": "string",
                "description": "Nombre del campo a consultar (por ejemplo, 'ultimo_parado', 'despegue', etc.).",
            },
        },
        "required": ["icao", "campo"],
    },
}

# Configuración del cliente y herramientas para la API
client = genai.Client(api_key="PON-TU-CLAVE")
tools = types.Tool(function_declarations=[query_icao_function])
config = types.GenerateContentConfig(tools=[tools])

# Ejemplo de consulta: Se solicita obtener el valor del campo "ultimo_parado" para el ICAO "3420ca"
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Consulta el campo 'ultimo_parado' para el ICAO 3444c3.",
    config=config,
)

# Verificamos si se realizó una llamada a función
if response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    # Se asume que los argumentos ya se han extraído como un diccionario.
    # En un escenario real podrías necesitar convertir el string de argumentos a un diccionario.
    args = function_call.args  # Se espera que sea un dict con claves "icao" y "campo"
    resultado = consultar_icao(args.get("icao"), args.get("campo"))
    # Después de obtener el resultado de la función

    # Enviar el resultado de vuelta al modelo para que lo procese
    response_final = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"El resultado de la consulta para el ICAO {args.get('icao')} y el campo {args.get('campo')} es: {resultado}. Por favor, redacta una respuesta clara para el usuario.",
        config=config,
    )
    print( response_final.text)
else:
    print("No se encontró llamada a función en la respuesta.")
    print(response.text)
