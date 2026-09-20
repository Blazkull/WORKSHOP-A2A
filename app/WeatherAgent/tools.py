"""
Herramientas del WeatherAgent.

Función pura: recibe parámetros, consulta la capa de datos, devuelve resultado.
"""
from strands import tool
from data import get_forecast


@tool
def get_weather_forecast(city: str, date: str) -> dict:
    """
    Devuelve el pronóstico del clima para una ciudad y fecha específica.

    Parámetros
    ----------
    city : str
        Nombre de la ciudad o código IATA del aeropuerto principal.
        Ejemplos: "Cartagena", "CTG", "Bogotá", "BOG", "Medellín", "MDE".
    date : str
        Fecha del pronóstico en formato YYYY-MM-DD. Ejemplo: 2026-09-27.

    Retorna
    -------
    dict
        Pronóstico con campos: city, country, date, temp_c, temp_min_c,
        temp_max_c, condition, humidity_pct, wind_kmh, precipitation_mm,
        uv_index, sunrise, sunset.

    Ejemplos
    --------
    get_weather_forecast("CTG", "2026-09-27")
    get_weather_forecast("Cartagena", "2026-09-28")
    get_weather_forecast("BOG", "2026-09-27")
    """
    forecast = get_forecast(city)
    return {"date": date, **forecast}
