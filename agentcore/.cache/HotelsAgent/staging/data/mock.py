"""
Datos simulados de hoteles por ciudad.

Indexados por código IATA de la ciudad. Los nombres y barrios están basados en
hoteles reales de cada ciudad colombiana (referencia informativa), pero los
precios y disponibilidad son simulados para el workshop. Cambiar a una API real
(Booking, Expedia, Amadeus) es el único cambio necesario para producción.

Ciudades cubiertas: coinciden con las del catálogo de vuelos (BOG, CTG, MDE,
CLO, BAQ) para que el flujo Trip Planner sea coherente entre agentes.
"""
from typing import TypedDict


class HotelOffer(TypedDict):
    hotel: str
    stars: int
    city: str
    neighborhood: str
    price_per_night_usd: float
    rating: float
    breakfast_included: bool
    amenities: list[str]


# Catálogo mock indexado por código IATA de la ciudad
HOTELS: dict[str, list[HotelOffer]] = {
    "CTG": [
        {"hotel": "Hilton Cartagena", "stars": 5, "city": "Cartagena",
         "neighborhood": "Bocagrande", "price_per_night_usd": 190.0, "rating": 4.6,
         "breakfast_included": True, "amenities": ["piscina", "playa", "spa", "wifi", "gimnasio"]},
        {"hotel": "Hyatt Regency Cartagena", "stars": 5, "city": "Cartagena",
         "neighborhood": "Bocagrande", "price_per_night_usd": 175.0, "rating": 4.5,
         "breakfast_included": True, "amenities": ["piscina", "playa", "wifi", "restaurante"]},
        {"hotel": "Hotel Boutique Casa Isabel", "stars": 4, "city": "Cartagena",
         "neighborhood": "Getsemaní", "price_per_night_usd": 120.0, "rating": 4.4,
         "breakfast_included": True, "amenities": ["wifi", "terraza", "bar"]},
        {"hotel": "Hotel Caribe by Faranda", "stars": 4, "city": "Cartagena",
         "neighborhood": "Bocagrande", "price_per_night_usd": 135.0, "rating": 4.3,
         "breakfast_included": True, "amenities": ["piscina", "playa", "wifi"]},
    ],
    "BOG": [
        {"hotel": "Sofitel Bogotá Victoria Regia", "stars": 5, "city": "Bogotá",
         "neighborhood": "Zona T", "price_per_night_usd": 160.0, "rating": 4.6,
         "breakfast_included": True, "amenities": ["wifi", "gimnasio", "restaurante", "spa"]},
        {"hotel": "HAB Hotel Bogotá", "stars": 4, "city": "Bogotá",
         "neighborhood": "Chapinero", "price_per_night_usd": 105.0, "rating": 4.4,
         "breakfast_included": True, "amenities": ["wifi", "gimnasio", "terraza", "restaurante"]},
        {"hotel": "Hotel Maceo Chico", "stars": 3, "city": "Bogotá",
         "neighborhood": "Usaquén", "price_per_night_usd": 70.0, "rating": 4.1,
         "breakfast_included": False, "amenities": ["wifi", "parqueadero"]},
    ],
    "MDE": [
        {"hotel": "The Landmark Hotel", "stars": 5, "city": "Medellín",
         "neighborhood": "El Poblado", "price_per_night_usd": 165.0, "rating": 4.7,
         "breakfast_included": True, "amenities": ["piscina", "rooftop", "wifi", "spa", "gimnasio"]},
        {"hotel": "Lettera Hotel", "stars": 4, "city": "Medellín",
         "neighborhood": "El Poblado", "price_per_night_usd": 100.0, "rating": 4.4,
         "breakfast_included": True, "amenities": ["wifi", "jardín", "restaurante", "terraza"]},
        {"hotel": "Hotel Torre Primavera", "stars": 3, "city": "Medellín",
         "neighborhood": "Laureles", "price_per_night_usd": 60.0, "rating": 4.0,
         "breakfast_included": False, "amenities": ["wifi", "parqueadero"]},
    ],
    "CLO": [
        {"hotel": "Spiwak Chipichape Cali", "stars": 5, "city": "Cali",
         "neighborhood": "Chipichape", "price_per_night_usd": 125.0, "rating": 4.5,
         "breakfast_included": True, "amenities": ["piscina", "wifi", "spa", "gimnasio"]},
        {"hotel": "Hotel Dann Carlton Cali", "stars": 5, "city": "Cali",
         "neighborhood": "Granada", "price_per_night_usd": 110.0, "rating": 4.4,
         "breakfast_included": True, "amenities": ["piscina", "wifi", "restaurante"]},
        {"hotel": "Hotel Boutique San Antonio", "stars": 3, "city": "Cali",
         "neighborhood": "San Antonio", "price_per_night_usd": 55.0, "rating": 4.1,
         "breakfast_included": False, "amenities": ["wifi", "terraza"]},
    ],
    "BAQ": [
        {"hotel": "Hotel El Prado", "stars": 4, "city": "Barranquilla",
         "neighborhood": "El Prado", "price_per_night_usd": 95.0, "rating": 4.3,
         "breakfast_included": True, "amenities": ["piscina", "wifi", "restaurante"]},
        {"hotel": "Barranquilla Plaza", "stars": 4, "city": "Barranquilla",
         "neighborhood": "Alto Prado", "price_per_night_usd": 85.0, "rating": 4.2,
         "breakfast_included": True, "amenities": ["wifi", "gimnasio", "restaurante"]},
    ],
}

FALLBACK_HOTEL: HotelOffer = {
    "hotel": "MockStay Hotel", "stars": 3, "city": "N/A",
    "neighborhood": "Centro", "price_per_night_usd": 80.0, "rating": 4.0,
    "breakfast_included": False, "amenities": ["wifi"],
}


def get_hotels(city: str) -> list[HotelOffer]:
    """Devuelve los hoteles disponibles para la ciudad dada (código IATA)."""
    key = city.strip().upper()
    if key in HOTELS:
        return HOTELS[key]
    return [{**FALLBACK_HOTEL, "city": city, "note": "Ciudad no disponible en catálogo mock"}]
