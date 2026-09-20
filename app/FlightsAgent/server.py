"""
Factory del servidor A2A para FlightsAgent.

Separa la creación del agente Strands (lógica) de la configuración
del servidor A2A (infraestructura). Ambas piezas son independientes
y testeables por separado.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strands import Agent
from strands.multiagent.a2a import A2AServer

from shared.config import get_model_id, get_port, get_agent_version
from shared.logging import get_logger
from tools import search_flights
from agent_card import build_skills

log = get_logger("FlightsAgent.server")


def create_agent(context_id: str) -> Agent:
    """
    Factory llamada por A2AServer en cada nueva sesión/contexto.

    A2A spec §3.4: cada contextId representa una conversación aislada.
    Strands crea un agente nuevo por contexto para mantener el historial
    de mensajes separado entre sesiones concurrentes.

    Parámetros
    ----------
    context_id : str
        Identificador de contexto A2A (UUID). Permite al servidor
        mantener conversaciones aisladas.
    """
    log.info(f"Creando agente para context_id={context_id}")
    return Agent(
        model=get_model_id(),
        name="Flights Agent",
        description=(
            "Servidor A2A que busca vuelos entre ciudades colombianas. "
            "Herramienta disponible: search_flights(origin, destination, date)."
        ),
        tools=[search_flights],
        callback_handler=None,
    )


def build_server() -> A2AServer:
    """
    Construye y devuelve el servidor A2A listo para servir.

    Endpoints que publica automáticamente Strands A2AServer:
      GET  /.well-known/agent-card.json  → descubrimiento (A2A spec §8)
      POST /                              → send message   (A2A spec §3.1.1)
      POST /message:send                 → send message   (HTTP+JSON binding §11.3.1)
      POST /message:stream               → streaming SSE  (HTTP+JSON binding §11.3.1)
    """
    port = get_port(default=9000)
    log.info(f"Construyendo A2AServer en 0.0.0.0:{port}")
    kwargs = dict(
        agent_factory=create_agent,
        host="0.0.0.0",
        port=port,
        version=get_agent_version(),
        skills=build_skills(),  # skills enriquecidas (tags, ejemplos, español)
    )
    # En local, forzar que la agent-card anuncie una URL conectable (127.0.0.1),
    # no 0.0.0.0, para que el cliente A2A pueda enviar el POST message/send.
    public_url = os.environ.get("PUBLIC_URL")
    if public_url:
        kwargs["http_url"] = public_url
    return A2AServer(**kwargs)
