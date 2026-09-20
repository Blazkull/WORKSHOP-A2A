"""
Herramientas del OrchestratorAgent.

Cada @tool envuelve un agente remoto A2A. El LLM del orquestador decide
cuándo llamarlas. Internamente usan invoke_async (bloqueante) porque las
tools de Strands consolidan un resultado antes de devolverlo al LLM.

Manejo de fallos (reto avanzado): si un especialista no responde (timeout,
conexión rechazada, etc.), la tool devuelve un mensaje degradado en lugar de
propagar la excepción, para que el orquestador pueda consolidar con el resto.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strands import tool

from shared.logging import get_logger
from a2a_clients import (
    make_flights_client,
    make_weather_client,
    make_hotels_client,
    invoke_with_retry,
    degraded_message,
)

log = get_logger("OrchestratorAgent.tools")


@tool
async def ask_flights(request: str) -> str:
    """
    Delega en el Flights Agent la búsqueda de vuelos disponibles.

    Úsala cuando el usuario pregunte por vuelos, precios, horarios o
    disponibilidad entre dos ciudades para una fecha.

    Parámetros
    ----------
    request : str
        Petición en lenguaje natural con origen, destino y fecha.
        Ejemplo: "Vuelos de Bogotá (BOG) a Cartagena (CTG) el 2026-09-27"

    Retorna
    -------
    str
        Respuesta del Flights Agent, o un mensaje degradado si no responde.
    """
    log.info(f"Delegando en FlightsAgent: {request!r}")
    try:
        return await invoke_with_retry(make_flights_client, request)
    except Exception as e:  # noqa: BLE001 - degradación elegante
        return degraded_message("vuelos", e)


@tool
async def ask_weather(request: str) -> str:
    """
    Delega en el Weather Agent la consulta del pronóstico del clima.

    Úsala cuando el usuario pregunte por clima, temperatura o condiciones
    meteorológicas de una ciudad para una fecha.

    Parámetros
    ----------
    request : str
        Petición en lenguaje natural con ciudad y fecha.
        Ejemplo: "Clima en Cartagena (CTG) el 2026-09-27"

    Retorna
    -------
    str
        Respuesta del Weather Agent, o un mensaje degradado si no responde.
    """
    log.info(f"Delegando en WeatherAgent: {request!r}")
    try:
        return await invoke_with_retry(make_weather_client, request)
    except Exception as e:  # noqa: BLE001 - degradación elegante
        return degraded_message("clima", e)


@tool
async def ask_hotels(request: str) -> str:
    """
    Delega en el Hotels Agent la búsqueda de alojamiento.

    Úsala cuando el usuario pregunte por hoteles, alojamiento, hospedaje,
    precios de habitación o dónde quedarse en una ciudad.

    Parámetros
    ----------
    request : str
        Petición en lenguaje natural con ciudad, fecha de entrada y noches.
        Ejemplo: "Hoteles en Cartagena (CTG) desde 2026-09-27 por 3 noches"

    Retorna
    -------
    str
        Respuesta del Hotels Agent, o un mensaje degradado si no responde.
    """
    log.info(f"Delegando en HotelsAgent: {request!r}")
    try:
        return await invoke_with_retry(make_hotels_client, request)
    except Exception as e:  # noqa: BLE001 - degradación elegante
        return degraded_message("hoteles", e)
