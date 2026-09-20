"""
OrchestratorAgent — Punto de entrada (cliente A2A sobre AgentCore Runtime).

Es la única puerta de entrada del usuario. Recibe una petición en lenguaje
natural, delega en los especialistas vía A2A y devuelve una respuesta
consolidada por streaming.

Modos de operación (según payload):
  - Por defecto: el LLM orquesta usando las tools ask_flights / ask_weather /
    ask_hotels y transmite su respuesta consolidada token a token.
  - mode="swarm": usa el patrón multi-agente de Strands (swarm.py), integrando
    los A2AAgent remotos como sub-agentes del orquestador.
  - stream_direct=True: reto avanzado — reenvía directamente el streaming de un
    especialista al usuario sin pasar por el ciclo tool-use del LLM.

Payload:
  {
    "prompt": "Vuelos, clima y hoteles de Bogotá a Cartagena este fin de semana",
    "mode": "default" | "swarm",              # opcional
    "stream_direct": false,                    # opcional
    "specialist": "flights|weather|hotels"     # requerido si stream_direct=true
  }

Variables de entorno:
  MODEL_ID           Modelo Bedrock (default: us.amazon.nova-lite-v1:0)
  FLIGHTS_AGENT_URL  URL del FlightsAgent  (inyectada tras deploy)
  WEATHER_AGENT_URL  URL del WeatherAgent  (inyectada tras deploy)
  HOTELS_AGENT_URL   URL del HotelsAgent   (inyectada tras deploy)
  PORT               Puerto local (default: 8080)
"""
import sys
import os

# Fuerza UTF-8 en stdout/stderr para que los textos en español (tildes, ñ, ¿¡)
# se emitan correctamente en cualquier consola.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from shared.logging import get_logger
from shared.config import get_flights_url, get_weather_url, get_hotels_url
from agent import build_agent
from swarm import build_swarm_agent
from streaming import stream_flights, stream_weather, stream_hotels

import re

log = get_logger("OrchestratorAgent")

app = BedrockAgentCoreApp()

_STREAM_MAP = {
    "flights": stream_flights,
    "weather": stream_weather,
    "hotels": stream_hotels,
}

_THINKING_RE = re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE)


def _clean_output(text: str) -> str:
    """Elimina bloques <thinking>...</thinking> y espacios sobrantes."""
    cleaned = _THINKING_RE.sub("", text)
    return cleaned.strip()


@app.entrypoint
async def invoke(payload: dict, context):
    """
    Entrypoint invocado por AgentCore Runtime en cada petición.

    Valida el payload (prompts como string) y transmite la respuesta por streaming.
    """
    prompt = payload.get("prompt", "")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("`prompt` debe ser un string no vacío.")

    # ── Modo avanzado: streaming directo desde un especialista ─────────
    if bool(payload.get("stream_direct", False)):
        specialist = str(payload.get("specialist", "")).lower()
        streamer = _STREAM_MAP.get(specialist)
        if streamer is None:
            raise ValueError(
                "stream_direct=true requiere specialist='flights', 'weather' o 'hotels'."
            )
        async for delta in streamer(prompt):
            yield delta
        return

    # ── Selección de orquestador: default (tools) o swarm (multi-agente) ─
    mode = str(payload.get("mode", "default")).lower()
    agent = build_swarm_agent() if mode == "swarm" else build_agent()

    # Acumular solo los deltas de texto del modelo (ignorar eventos crudos:
    # tool_use, AgentResult, metadata — eso duplicaba y ensuciaba la salida).
    # Al final se limpian los bloques <thinking>...</thinking> que Nova Lite
    # a veces emite, y se entrega una única respuesta limpia.
    chunks: list[str] = []
    async for event in agent.stream_async(prompt):
        if isinstance(event, dict) and "data" in event:
            chunks.append(event["data"])

    yield _clean_output("".join(chunks))


if __name__ == "__main__":
    from shared.config import get_port

    port = get_port(default=8080)
    log.info(f"OrchestratorAgent iniciando en puerto {port}")
    log.info(f"  FLIGHTS_AGENT_URL = {get_flights_url()}")
    log.info(f"  WEATHER_AGENT_URL = {get_weather_url()}")
    log.info(f"  HOTELS_AGENT_URL  = {get_hotels_url()}")
    app.run()
