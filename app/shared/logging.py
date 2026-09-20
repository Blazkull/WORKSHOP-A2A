"""
Logging estructurado compartido.
Emite JSON para que AgentCore / CloudWatch lo indexe correctamente.
"""
import json
import logging
import sys
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    """Formatea cada log como una línea JSON — compatible con CloudWatch Logs Insights."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """
    Devuelve un logger con formato JSON (UTF-8) que escribe a stdout.

    Fuerza codificación UTF-8 en el stream para que los textos en español
    (tildes, ñ, ¿¡) se emitan correctamente en cualquier consola.

    Uso:
        from shared.logging import get_logger
        log = get_logger(__name__)
        log.info("FlightsAgent iniciado")
    """
    # Reconfigura stdout a UTF-8 una sola vez (Windows por defecto usa cp1252).
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
