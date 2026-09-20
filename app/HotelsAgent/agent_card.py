"""
Skills del HotelsAgent — conforme con A2A Protocol Spec v1.0 (AgentSkill).

Se pasan a A2AServer(skills=...) en server.py y se publican en
GET /.well-known/agent-card.json para el descubrimiento por el orquestador.
"""
from a2a.types import AgentSkill


def build_skills() -> list[AgentSkill]:
    """Skills descubribles del HotelsAgent."""
    return [
        AgentSkill(
            id="search_hotels",
            name="Búsqueda de hoteles",
            description=(
                "Busca hoteles disponibles en una ciudad colombiana para una fecha "
                "de entrada y número de noches. Devuelve hotel, categoría (estrellas), "
                "barrio, precio por noche, precio total, calificación y amenidades."
            ),
            tags=["hotels", "hoteles", "lodging", "alojamiento", "hospedaje", "travel"],
            examples=[
                "Busca hoteles en Cartagena para el 27 de septiembre, 3 noches",
                "¿Qué hoteles hay en Bogotá cerca de la Zona T?",
                "Alojamiento en Medellín para este fin de semana",
            ],
        )
    ]
