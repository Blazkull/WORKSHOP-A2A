"""
Herramientas del FlightsAgent.

Cada @tool es una función pura: recibe parámetros, consulta la capa de datos
y devuelve un resultado. No contiene lógica de servidor ni de agente.
Esto permite testearlas de forma aislada.
"""
from strands import tool
from data import get_flights


@tool
def search_flights(origin: str, destination: str, date: str) -> list[dict]:
    """
    Busca vuelos disponibles entre dos ciudades para una fecha específica.

    Parámetros
    ----------
    origin : str
        Código IATA del aeropuerto de origen. Ejemplos: BOG, CTG, MDE, CLO.
    destination : str
        Código IATA del aeropuerto de destino.
    date : str
        Fecha de viaje en formato YYYY-MM-DD. Ejemplo: 2026-09-27.

    Retorna
    -------
    list[dict]
        Lista de vuelos disponibles, cada uno con:
        flight, airline, origin, destination, date, depart, arrive,
        duration_min, cabin, price_usd, stops.

    Ejemplos
    --------
    search_flights("BOG", "CTG", "2026-09-27")
    search_flights("MDE", "BOG", "2026-09-28")
    """
    results = get_flights(origin, destination)
    # Inyectar la fecha en cada resultado
    return [{"date": date, **flight} for flight in results]
