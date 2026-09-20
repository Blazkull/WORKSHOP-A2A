"""
Skills del FlightsAgent — conforme con A2A Protocol Spec v1.0 (AgentSkill).

Referencia: https://a2a-protocol.org/latest/specification/#445-agentskill

Strands A2AServer construye la AgentCard automáticamente (name, description,
capabilities, url) a partir del Agent. Aquí definimos explícitamente las
`skills` para enriquecerlas con tags, descripción en español y ejemplos —
en lugar de dejar que Strands las derive solo del nombre de la tool.

Estas skills se pasan a A2AServer(skills=...) en server.py y se publican en
GET /.well-known/agent-card.json para el descubrimiento por el orquestador.
"""
from a2a.types import AgentSkill


def build_skills() -> list[AgentSkill]:
    """Skills descubribles del FlightsAgent."""
    return [
        AgentSkill(
            id="search_flights",
            name="Búsqueda de vuelos",
            description=(
                "Busca vuelos disponibles entre dos aeropuertos colombianos "
                "para una fecha específica. Devuelve vuelo, aerolínea, horarios, "
                "duración, clase y precio en USD."
            ),
            tags=["flights", "vuelos", "travel", "viajes", "aviation"],
            examples=[
                "Busca vuelos de Bogotá a Cartagena para el 27 de septiembre de 2026",
                "¿Qué vuelos hay de BOG a CTG el próximo sábado?",
                "Vuelos disponibles de Medellín a Bogotá mañana",
            ],
        )
    ]
