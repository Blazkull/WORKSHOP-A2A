"""
Herramientas del HotelsAgent.

Función pura: recibe parámetros, consulta la capa de datos, devuelve resultado.
"""
from strands import tool
from data import get_hotels


@tool
def search_hotels(city: str, checkin: str, nights: int = 1) -> list[dict]:
    """
    Busca hoteles disponibles en una ciudad para una fecha de entrada.

    Parámetros
    ----------
    city : str
        Código IATA de la ciudad. Ejemplos: BOG, CTG, MDE, CLO.
    checkin : str
        Fecha de entrada en formato YYYY-MM-DD. Ejemplo: 2026-09-27.
    nights : int
        Número de noches de estadía. Por defecto 1.

    Retorna
    -------
    list[dict]
        Lista de hoteles con: hotel, stars, city, neighborhood, checkin,
        nights, price_per_night_usd, total_usd, rating, breakfast_included, amenities.

    Ejemplos
    --------
    search_hotels("CTG", "2026-09-27", 2)
    search_hotels("BOG", "2026-09-28")
    """
    results = get_hotels(city)
    enriched = []
    for h in results:
        price = h["price_per_night_usd"]
        enriched.append({
            "checkin": checkin,
            "nights": nights,
            "total_usd": round(price * nights, 2),
            **h,
        })
    return enriched
