"""
Datos simulados de clima por ciudad.

Indexados por código IATA del aeropuerto principal de cada ciudad.
Cambiar a una llamada real (OpenWeather, etc.) es el único cambio
necesario para pasar a producción.
"""
from typing import TypedDict


class ForecastData(TypedDict):
    city: str
    country: str
    temp_c: float
    temp_min_c: float
    temp_max_c: float
    condition: str
    humidity_pct: int
    wind_kmh: float
    precipitation_mm: float
    uv_index: int
    sunrise: str
    sunset: str


# Catálogo mock indexado por código IATA
FORECASTS: dict[str, ForecastData] = {
    "CTG": {
        "city": "Cartagena", "country": "Colombia",
        "temp_c": 31.0, "temp_min_c": 27.0, "temp_max_c": 34.0,
        "condition": "Soleado", "humidity_pct": 72,
        "wind_kmh": 18.0, "precipitation_mm": 0.0,
        "uv_index": 9, "sunrise": "05:58", "sunset": "18:02",
    },
    "BOG": {
        "city": "Bogotá", "country": "Colombia",
        "temp_c": 15.0, "temp_min_c": 9.0, "temp_max_c": 18.0,
        "condition": "Nublado con lluvia leve", "humidity_pct": 80,
        "wind_kmh": 12.0, "precipitation_mm": 4.0,
        "uv_index": 4, "sunrise": "05:50", "sunset": "17:55",
    },
    "MDE": {
        "city": "Medellín", "country": "Colombia",
        "temp_c": 22.0, "temp_min_c": 16.0, "temp_max_c": 26.0,
        "condition": "Parcialmente nublado", "humidity_pct": 68,
        "wind_kmh": 10.0, "precipitation_mm": 2.0,
        "uv_index": 6, "sunrise": "05:52", "sunset": "17:57",
    },
    "CLO": {
        "city": "Cali", "country": "Colombia",
        "temp_c": 24.0, "temp_min_c": 18.0, "temp_max_c": 28.0,
        "condition": "Soleado con nubosidad", "humidity_pct": 65,
        "wind_kmh": 14.0, "precipitation_mm": 0.0,
        "uv_index": 7, "sunrise": "05:55", "sunset": "17:59",
    },
    "BAQ": {
        "city": "Barranquilla", "country": "Colombia",
        "temp_c": 33.0, "temp_min_c": 28.0, "temp_max_c": 36.0,
        "condition": "Despejado y caluroso", "humidity_pct": 60,
        "wind_kmh": 22.0, "precipitation_mm": 0.0,
        "uv_index": 10, "sunrise": "05:45", "sunset": "18:00",
    },
}

# Alias ciudad → IATA para búsquedas por nombre completo
CITY_ALIASES: dict[str, str] = {
    "cartagena":    "CTG",
    "bogotá":       "BOG",
    "bogota":       "BOG",
    "medellín":     "MDE",
    "medellin":     "MDE",
    "cali":         "CLO",
    "barranquilla": "BAQ",
}

FALLBACK_FORECAST: ForecastData = {
    "city": "Desconocida", "country": "Colombia",
    "temp_c": 20.0, "temp_min_c": 15.0, "temp_max_c": 25.0,
    "condition": "Sin datos (ciudad no en catálogo mock)",
    "humidity_pct": 60, "wind_kmh": 10.0,
    "precipitation_mm": 0.0, "uv_index": 5,
    "sunrise": "06:00", "sunset": "18:00",
}


def get_forecast(city: str) -> ForecastData:
    """
    Devuelve el pronóstico para la ciudad dada.
    Acepta código IATA o nombre de ciudad (español/inglés).
    """
    # Intentar por código IATA directo
    key = city.strip().upper()
    if key in FORECASTS:
        return FORECASTS[key]

    # Intentar por alias de nombre
    alias_key = CITY_ALIASES.get(city.strip().lower())
    if alias_key and alias_key in FORECASTS:
        return FORECASTS[alias_key]

    return {**FALLBACK_FORECAST, "city": city}
