"""
Patrón multi-agente (Graph/Swarm) — reto avanzado.

En lugar de las tools manuales ask_flights/ask_weather/ask_hotels, este módulo
integra los A2AAgent remotos directamente como sub-agentes del orquestador
usando el mecanismo nativo de Strands `agent.as_tool()`.

Diferencia clave frente a tools.py:
- tools.py: funciones @tool que llaman invoke_async manualmente.
- swarm.py: los agentes remotos A2A se exponen como herramientas del
  orquestador de forma declarativa. Strands gestiona el ciclo de delegación.

Ambos enfoques cumplen el mismo objetivo A2A (el orquestador delega en
especialistas remotos); este es más idiomático del framework.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strands import Agent
from strands.agent.a2a_agent import A2AAgent

from shared.config import (
    get_model_id,
    get_flights_url,
    get_weather_url,
    get_hotels_url,
)
from shared.logging import get_logger

log = get_logger("OrchestratorAgent.swarm")

_A2A_TIMEOUT = 60

SWARM_SYSTEM_PROMPT = """
Eres un orquestador de viajes. Coordinas tres agentes especialistas remotos
(vuelos, clima y hoteles) para resolver la petición del usuario.

Delega en el especialista adecuado según la intención, combina los resultados
y responde en el idioma del usuario con una propuesta de viaje clara.
Si un especialista no responde, continúa con lo que tengas e infórmalo.
"""


def build_swarm_agent() -> Agent:
    """
    Construye el orquestador integrando los especialistas A2A como sub-agentes.

    Cada A2AAgent remoto se convierte en una herramienta del orquestador con
    `as_tool()`. El LLM del orquestador decide a cuál delegar; Strands maneja
    el ciclo de invocación multi-agente.
    """
    log.info("Construyendo orquestador (patrón Graph/Swarm) con sub-agentes A2A")

    flights = A2AAgent(
        endpoint=get_flights_url(),
        name="flights_specialist",
        description="Busca vuelos disponibles entre ciudades para una fecha.",
        timeout=_A2A_TIMEOUT,
    )
    weather = A2AAgent(
        endpoint=get_weather_url(),
        name="weather_specialist",
        description="Consulta el pronóstico del clima por ciudad y fecha.",
        timeout=_A2A_TIMEOUT,
    )
    hotels = A2AAgent(
        endpoint=get_hotels_url(),
        name="hotels_specialist",
        description="Busca hoteles por ciudad, fecha de entrada y noches.",
        timeout=_A2A_TIMEOUT,
    )

    return Agent(
        model=get_model_id(),
        name="Trip Planner Swarm Orchestrator",
        system_prompt=SWARM_SYSTEM_PROMPT,
        tools=[
            flights.as_tool(name="ask_flights", description="Delegar búsqueda de vuelos."),
            weather.as_tool(name="ask_weather", description="Delegar consulta de clima."),
            hotels.as_tool(name="ask_hotels", description="Delegar búsqueda de hoteles."),
        ],
        callback_handler=None,
    )
