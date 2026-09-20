"""
Datos simulados de vuelos.

Estructura idéntica a la que devuelve la Duffel API (flights-mcp),
sin ninguna dependencia de red. Cambiar esto a una llamada real es
el único cambio necesario para pasar a producción.

Referencia: https://github.com/ravinahp/flights-mcp
"""
from typing import TypedDict


class FlightOffer(TypedDict):
    flight: str
    airline: str
    origin: str
    destination: str
    depart: str
    arrive: str
    duration_min: int
    cabin: str
    price_usd: float
    stops: int


# Catálogo mock indexado por "ORIGIN-DESTINATION"
FLIGHTS: dict[str, list[FlightOffer]] = {
    "BOG-CTG": [
        {"flight": "AV9821", "airline": "Avianca",  "origin": "BOG", "destination": "CTG",
         "depart": "07:15", "arrive": "08:25", "duration_min": 70, "cabin": "economy", "price_usd": 89.0,  "stops": 0},
        {"flight": "LA4410", "airline": "LATAM",    "origin": "BOG", "destination": "CTG",
         "depart": "12:40", "arrive": "13:50", "duration_min": 70, "cabin": "economy", "price_usd": 76.0,  "stops": 0},
        {"flight": "AV9835", "airline": "Avianca",  "origin": "BOG", "destination": "CTG",
         "depart": "18:05", "arrive": "19:15", "duration_min": 70, "cabin": "economy", "price_usd": 102.0, "stops": 0},
    ],
    "CTG-BOG": [
        {"flight": "AV9822", "airline": "Avianca",  "origin": "CTG", "destination": "BOG",
         "depart": "09:00", "arrive": "10:10", "duration_min": 70, "cabin": "economy", "price_usd": 91.0, "stops": 0},
        {"flight": "LA4411", "airline": "LATAM",    "origin": "CTG", "destination": "BOG",
         "depart": "14:30", "arrive": "15:40", "duration_min": 70, "cabin": "economy", "price_usd": 79.0, "stops": 0},
    ],
    "BOG-MDE": [
        {"flight": "AV8001", "airline": "Avianca",  "origin": "BOG", "destination": "MDE",
         "depart": "06:00", "arrive": "06:50", "duration_min": 50, "cabin": "economy", "price_usd": 65.0, "stops": 0},
        {"flight": "LA3200", "airline": "LATAM",    "origin": "BOG", "destination": "MDE",
         "depart": "10:15", "arrive": "11:05", "duration_min": 50, "cabin": "economy", "price_usd": 59.0, "stops": 0},
    ],
    "MDE-BOG": [
        {"flight": "AV8002", "airline": "Avianca",  "origin": "MDE", "destination": "BOG",
         "depart": "08:00", "arrive": "08:50", "duration_min": 50, "cabin": "economy", "price_usd": 67.0, "stops": 0},
    ],
    "BOG-CLO": [
        {"flight": "AV7501", "airline": "Avianca",  "origin": "BOG", "destination": "CLO",
         "depart": "07:30", "arrive": "08:20", "duration_min": 50, "cabin": "economy", "price_usd": 72.0, "stops": 0},
    ],
}

# Respuesta genérica para rutas sin datos en el catálogo mock
FALLBACK_FLIGHT: FlightOffer = {
    "flight":       "XX0001",
    "airline":      "MockAir",
    "origin":       "N/A",
    "destination":  "N/A",
    "depart":       "08:00",
    "arrive":       "10:00",
    "duration_min": 120,
    "cabin":        "economy",
    "price_usd":    99.0,
    "stops":        0,
}


def get_flights(origin: str, destination: str) -> list[FlightOffer]:
    """Devuelve los vuelos disponibles para la ruta dada."""
    key = f"{origin.upper()}-{destination.upper()}"
    return FLIGHTS.get(key, [{**FALLBACK_FLIGHT, "origin": origin, "destination": destination,
                               "note": "Ruta no disponible en catálogo mock"}])
