"""
Streaming end-to-end desde los especialistas al usuario.

Reto avanzado del workshop: en lugar de esperar la respuesta completa de
cada especialista (invoke_async, bloqueante), usamos A2AAgent.stream_async
para reenviar los tokens del especialista al usuario a medida que llegan.

Estas funciones son async generators: producen fragmentos de texto (str)
que el entrypoint de AgentCore vuelve a emitir hacia el cliente.

Manejo de fallos: si el especialista no responde, cede un mensaje degradado
en vez de romper el stream.
"""
import sys
import os
from typing import AsyncIterator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.logging import get_logger
from a2a_clients import (
    make_flights_client,
    make_weather_client,
    make_hotels_client,
    extract_text,
    degraded_message,
)

log = get_logger("OrchestratorAgent.streaming")


async def _stream_specialist(client, request: str, label: str) -> AsyncIterator[str]:
    """
    Reenvía token a token la respuesta de un especialista.

    A2AAgent.stream_async emite eventos:
      {"type": "a2a_stream", "event": <A2A object>}  → texto incremental
      {"result": AgentResult}                        → resultado final
    Extraemos el texto de cada evento a2a_stream y cedemos solo la parte nueva.

    Si el especialista falla, cedemos un mensaje degradado (graceful degradation).
    """
    prev = ""
    try:
        async for event in client.stream_async(request):
            if event.get("type") == "a2a_stream":
                text = extract_text(event.get("event"))
                if not text:
                    continue
                if text.startswith(prev):
                    delta = text[len(prev):]
                    prev = text
                else:
                    delta = text
                    prev = prev + text
                if delta:
                    yield delta
    except Exception as e:  # noqa: BLE001 - degradación elegante
        yield degraded_message(label, e)


async def stream_flights(request: str) -> AsyncIterator[str]:
    """Streaming de la respuesta del FlightsAgent."""
    log.info(f"Streaming FlightsAgent: {request!r}")
    async for delta in _stream_specialist(make_flights_client(), request, "vuelos"):
        yield delta


async def stream_weather(request: str) -> AsyncIterator[str]:
    """Streaming de la respuesta del WeatherAgent."""
    log.info(f"Streaming WeatherAgent: {request!r}")
    async for delta in _stream_specialist(make_weather_client(), request, "clima"):
        yield delta


async def stream_hotels(request: str) -> AsyncIterator[str]:
    """Streaming de la respuesta del HotelsAgent."""
    log.info(f"Streaming HotelsAgent: {request!r}")
    async for delta in _stream_specialist(make_hotels_client(), request, "hoteles"):
        yield delta
