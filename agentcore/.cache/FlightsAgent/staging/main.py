"""
FlightsAgent — Punto de entrada.

Responsabilidad única: arrancar el servidor A2A.
Toda la lógica vive en server.py, tools.py y data/.

Uso local:
    python main.py

Uso con agentcore dev / agentcore deploy:
    Declarado en agentcore.json como entrypoint "main.py"

Variables de entorno:
    PORT       Puerto del servidor (default: 9001)
    MODEL_ID   Modelo Bedrock      (default: us.amazon.nova-lite-v1:0)
"""
import sys
import os

# Permite resolver 'shared' cuando agentcore ejecuta desde app/FlightsAgent/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.logging import get_logger
from shared.config import get_port
from server import build_server

log = get_logger("FlightsAgent")


if __name__ == "__main__":
    port = get_port(default=9000)
    log.info(f"FlightsAgent iniciando en puerto {port}")
    log.info("Endpoints disponibles:")
    log.info(f"  GET  http://0.0.0.0:{port}/.well-known/agent-card.json")
    log.info(f"  POST http://0.0.0.0:{port}/message:send")
    log.info(f"  POST http://0.0.0.0:{port}/message:stream")

    server = build_server()
    server.serve()
