"""
WeatherAgent — Punto de entrada.

Responsabilidad única: arrancar el servidor A2A.

Variables de entorno:
    PORT       Puerto del servidor (default: 9002)
    MODEL_ID   Modelo Bedrock      (default: us.amazon.nova-lite-v1:0)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.logging import get_logger
from shared.config import get_port
from server import build_server

log = get_logger("WeatherAgent")


if __name__ == "__main__":
    port = get_port(default=9000)
    log.info(f"WeatherAgent iniciando en puerto {port}")
    log.info("Endpoints disponibles:")
    log.info(f"  GET  http://0.0.0.0:{port}/.well-known/agent-card.json")
    log.info(f"  POST http://0.0.0.0:{port}/message:send")
    log.info(f"  POST http://0.0.0.0:{port}/message:stream")

    server = build_server()
    server.serve()
