"""
Factory del servidor A2A para WeatherAgent.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strands import Agent
from strands.multiagent.a2a import A2AServer

from shared.config import get_model_id, get_port, get_agent_version
from shared.logging import get_logger
from tools import get_weather_forecast
from agent_card import build_skills

log = get_logger("WeatherAgent.server")


def create_agent(context_id: str) -> Agent:
    """
    Factory llamada por A2AServer en cada nueva sesión/contexto (A2A spec §3.4).
    """
    log.info(f"Creando agente para context_id={context_id}")
    return Agent(
        model=get_model_id(),
        name="Weather Agent",
        description=(
            "Servidor A2A que consulta el pronóstico del clima por ciudad. "
            "Herramienta disponible: get_weather_forecast(city, date)."
        ),
        tools=[get_weather_forecast],
        callback_handler=None,
    )


def build_server() -> A2AServer:
    """
    Construye el servidor A2A con soporte de streaming.

    Endpoints publicados por Strands A2AServer:
      GET  /.well-known/agent-card.json  → descubrimiento (A2A spec §8)
      POST /message:send                 → send message   (A2A spec §3.1.1)
      POST /message:stream               → streaming SSE  (A2A spec §3.1.2)
    """
    port = get_port(default=9000)
    log.info(f"Construyendo A2AServer en 0.0.0.0:{port}")
    kwargs = dict(
        agent_factory=create_agent,
        host="0.0.0.0",
        port=port,
        version=get_agent_version(),
        skills=build_skills(),
    )
    public_url = os.environ.get("PUBLIC_URL")
    if public_url:
        kwargs["http_url"] = public_url
    return A2AServer(**kwargs)
