from google import genai
from google.genai.types import GenerateContentConfig

# Clave API: https://aistudio.google.com/apikey
GOOGLE_API_KEY = "YOUR_KEY"

client = genai.Client(api_key=GOOGLE_API_KEY)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="""
    Tell me when (exact time and date) the flight with icao 777777 will take off given it is a plane icao given this airport state:
    -------------------------------------------------------------------- 
    |  icao  |   last_stopped   |     taken_off    | aircraft_category |
    -------------------------------------------------------------------- 
    | 777777 | 01/12/2024 10:00 |      NULL        |   HEAVY AIRCRAFT  |
    -------------------------------------------------------------------- 
    | 722777 | 01/12/2024 10:17 | 01/12/2024 10:20 |   LIGHT AIRCRAFT  |
    -------------------------------------------------------------------- 
    | 712777 | 01/12/2024 10:18 | 01/12/2024 10:23 |   HEAVY AIRCRAFT  |
    --------------------------------------------------------------------  
    """,
    config=GenerateContentConfig(
        system_instruction=[
            "Current datetime is 01/12/2024 10:25",
            "You are a flight dispatcher at Aeropuerto Madrid-Barajas in charge of managing the take-offs.",
            "Your mission is to help users know when a plane will take off using the available info of the planes based on historical data I provide you next.",
            "plane_data...",
            "The plane take off should be after the last takeoff time from all planes."
            "Return the results in a csv table with the icao and the take off time, without any comments."
        ]
    ),
)
print(response.text)

#chat = model.start_chat()
#response = chat.send_message("message")

