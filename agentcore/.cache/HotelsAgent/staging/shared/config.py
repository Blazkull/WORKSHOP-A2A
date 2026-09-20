"""
Configuración central desde variables de entorno.
Todos los agentes importan de aquí — nunca leen os.environ directamente.
"""
import os


def get_model_id() -> str:
    """ID del modelo Bedrock a usar en todos los agentes."""
    return os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")


def get_port(default: int = 9000) -> int:
    """Puerto en el que escucha el servidor A2A."""
    return int(os.environ.get("PORT", str(default)))


# 127.0.0.1 explícito (no "localhost") para evitar que httpx intente IPv6 (::1)
# en Windows mientras uvicorn escucha en IPv4 → ConnectError.
def get_flights_url() -> str:
    """URL base del FlightsAgent (inyectada tras el primer deploy)."""
    return os.environ.get("FLIGHTS_AGENT_URL", "http://127.0.0.1:9001")


def get_weather_url() -> str:
    """URL base del WeatherAgent (inyectada tras el primer deploy)."""
    return os.environ.get("WEATHER_AGENT_URL", "http://127.0.0.1:9002")


def get_hotels_url() -> str:
    """URL base del HotelsAgent (inyectada tras el primer deploy)."""
    return os.environ.get("HOTELS_AGENT_URL", "http://127.0.0.1:9003")


def get_agent_version() -> str:
    """Versión semántica de los agentes (A2A spec: AgentCard.version)."""
    return os.environ.get("AGENT_VERSION", "1.0.0")
