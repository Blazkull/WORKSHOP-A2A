"""
Skills del WeatherAgent — conforme con A2A Protocol Spec v1.0 (AgentSkill).

Se pasan a A2AServer(skills=...) en server.py y se publican en
GET /.well-known/agent-card.json para el descubrimiento por el orquestador.
"""
from a2a.types import AgentSkill


def build_skills() -> list[AgentSkill]:
    """Skills descubribles del WeatherAgent."""
    return [
        AgentSkill(
            id="get_weather_forecast",
            name="Pronóstico del clima",
            description=(
                "Consulta el pronóstico meteorológico para una ciudad colombiana "
                "en una fecha específica. Devuelve temperatura mínima/máxima, condición, "
                "humedad, viento, precipitación e índice UV."
            ),
            tags=["weather", "clima", "forecast", "pronóstico", "temperatura"],
            examples=[
                "¿Cómo estará el clima en Cartagena el 27 de septiembre?",
                "Pronóstico del tiempo en CTG para este fin de semana",
                "Temperatura en Bogotá mañana",
            ],
        )
    ]
