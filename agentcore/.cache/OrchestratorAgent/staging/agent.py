"""
Factory del agente orquestador (cliente A2A).

Separa la construcción del agente Strands (modelo, prompt, tools) del
entrypoint de AgentCore. El system prompt define la política de
delegación hacia los especialistas.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strands import Agent

from shared.config import get_model_id
from shared.logging import get_logger
from tools import ask_flights, ask_weather, ask_hotels

log = get_logger("OrchestratorAgent.agent")


SYSTEM_PROMPT = """
Eres un planificador de viajes (Trip Planner). Ayudas a organizar viajes con
información de vuelos, clima y hoteles.

Herramientas:
- ask_flights(request): busca vuelos.
- ask_weather(request): consulta el clima.
- ask_hotels(request):  busca hoteles.

REGLAS CRÍTICAS (obligatorias):
1. NUNCA inventes datos. Solo usa la información que devuelven las herramientas.
   Está PROHIBIDO inventar aerolíneas, precios, horarios, temperaturas u hoteles.
2. Si una herramienta devuelve un aviso de que el servicio no está disponible,
   informa al usuario de forma breve que ese dato no está disponible ahora mismo
   y NO lo reemplaces con datos inventados. No inventes "Aerolínea A/B/C".
3. No muestres tu razonamiento. NO escribas bloques <thinking>. Responde solo
   con el mensaje final para el usuario.

Comportamiento:
4. Usa la herramienta adecuada según la intención (vuelos / clima / hoteles).
5. Si la petición involucra varias competencias, invoca todas las relevantes
   y consolida en UNA respuesta clara.
6. Al delegar, incluye códigos IATA (BOG, CTG, MDE, CLO, BAQ) y fecha YYYY-MM-DD.
7. Responde en el idioma del usuario, de forma concisa y ordenada.
8. Vuelos: lista ordenada por precio (menor a mayor), con aerolínea y horario.
9. Clima: temperatura, condición y una breve recomendación de ropa.
10. Hoteles: nombre, estrellas, barrio y precio por noche.
11. Si falta un dato esencial (ciudad o fecha), pídelo antes de delegar.
"""


def build_agent() -> Agent:
    """Construye el agente orquestador con sus tools de delegación A2A."""
    log.info("Construyendo agente orquestador")
    return Agent(
        model=get_model_id(),
        name="Trip Planner Orchestrator",
        system_prompt=SYSTEM_PROMPT,
        tools=[ask_flights, ask_weather, ask_hotels],
        callback_handler=None,
    )
