"""
Clientes A2A hacia los agentes especialistas desplegados en AgentCore Runtime.

Invocar un runtime A2A de AgentCore NO es una llamada HTTP plana: requiere
autenticación AWS SigV4 (firma con las credenciales del rol de ejecución) y un
header de sesión. Aquí construimos un cliente httpx que firma cada petición con
SigV4 contra el servicio `bedrock-agentcore`, y se lo pasamos al A2AAgent de
Strands vía ClientConfig.

Referencias:
- A2A entre runtimes AgentCore: docs runtime-a2a (SigV4 / OAuth, header de sesión)
- Endpoint: .../runtimes/<arn-encoded>/invocations/  (barra final)
- Agent card: <endpoint>/.well-known/agent-card.json
"""
import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from strands.agent.a2a_agent import A2AAgent

try:
    from a2a.client import ClientConfig
    from a2a.types import (
        AgentCard,
        AgentCapabilities,
        AgentSkill,
    )
except Exception:  # pragma: no cover - defensivo
    ClientConfig = None  # type: ignore
    AgentCard = None  # type: ignore

from shared.config import get_flights_url, get_weather_url, get_hotels_url
from shared.logging import get_logger

log = get_logger("OrchestratorAgent.a2a_clients")

_A2A_TIMEOUT = 120
_REGION = os.environ.get("AWS_REGION", "us-east-1")
_SERVICE = "bedrock-agentcore"


class _SigV4Auth(httpx.Auth):
    """
    Auth de httpx que firma cada petición con AWS SigV4 (servicio bedrock-agentcore).

    Firma solo con los headers estables (host + content-type) para evitar que
    httpx añada headers después de la firma e invalide el cálculo → 403.
    """

    def __init__(self, region: str, service: str):
        self._region = region
        self._service = service
        self._session = boto3.Session()

    def auth_flow(self, request: httpx.Request):
        credentials = self._session.get_credentials()
        if credentials is not None:
            body = request.content or b""
            frozen = credentials.get_frozen_credentials()

            # Firmar con SigV4 usando el método estándar de botocore. Este
            # cálculo (probado contra el endpoint /invocations) autentica
            # correctamente tanto GET (agent-card) como POST (message/send).
            aws_req = AWSRequest(method=request.method, url=str(request.url), data=body)
            SigV4Auth(frozen, self._service, self._region).add_auth(aws_req)

            # Copiar los headers de firma calculados de vuelta al request httpx.
            for key in ("Authorization", "X-Amz-Date", "X-Amz-Security-Token", "X-Amz-Content-SHA256"):
                if key in aws_req.headers:
                    request.headers[key] = aws_req.headers[key]

        yield request


def _prebuilt_card(endpoint: str, name: str) -> "AgentCard | None":
    """
    Construye una AgentCard mínima localmente para el endpoint dado.

    En AgentCore, el GET a /.well-known/agent-card.json responde 403 (el
    proxy A2A solo acepta el POST JSON-RPC message/send). Al pre-inyectar la
    card en el A2AAgent, Strands se salta ese GET y va directo al POST, que
    sí funciona con la firma SigV4.

    La `url` de la card DEBE apuntar al endpoint de invocación para que el
    cliente A2A envíe ahí los mensajes.
    """
    if AgentCard is None:
        return None
    return AgentCard(
        name=name,
        description=f"Especialista A2A remoto: {name}",
        version="1.0.0",
        url=endpoint,
        preferred_transport="JSONRPC",
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[
            AgentSkill(
                id=name,
                name=name,
                description=f"Capacidad del especialista {name}",
                tags=[name],
            )
        ],
    )


def _is_local(endpoint: str) -> bool:
    """True si el endpoint apunta a un servidor local (localhost / 127.0.0.1)."""
    return "localhost" in endpoint or "127.0.0.1" in endpoint


def _make_client(endpoint: str, label: str) -> A2AAgent:
    """
    Crea un A2AAgent adaptado al entorno:

    - LOCAL (localhost): cliente A2A simple, sin SigV4. El servidor local
      publica su agent-card normalmente, así que Strands la descubre solo.
    - AGENTCORE (nube): firma con SigV4, añade el header de sesión, y usa una
      AgentCard pre-construida (salta el GET a /.well-known/agent-card.json,
      que en AgentCore responde 403).
    """
    # ── Entorno local: A2A plano sin autenticación ─────────────────────
    if _is_local(endpoint):
        return A2AAgent(endpoint=endpoint, timeout=_A2A_TIMEOUT, name=label)

    # ── Entorno AgentCore: SigV4 + card pre-inyectada ──────────────────
    session_id = uuid4().hex + uuid4().hex  # >= 33 chars (requisito de AgentCore)
    httpx_client = httpx.AsyncClient(
        timeout=_A2A_TIMEOUT,
        auth=_SigV4Auth(_REGION, _SERVICE),
        headers={"X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id},
    )

    if ClientConfig is not None:
        config = ClientConfig(httpx_client=httpx_client, streaming=True)
        agent = A2AAgent(endpoint=endpoint, timeout=_A2A_TIMEOUT, client_config=config, name=label)
        card = _prebuilt_card(endpoint, label)
        if card is not None:
            agent._agent_card = card
        return agent

    return A2AAgent(endpoint=endpoint, timeout=_A2A_TIMEOUT, name=label)


def make_flights_client() -> A2AAgent:
    return _make_client(get_flights_url(), "flights_specialist")


def make_weather_client() -> A2AAgent:
    return _make_client(get_weather_url(), "weather_specialist")


def make_hotels_client() -> A2AAgent:
    return _make_client(get_hotels_url(), "hotels_specialist")


async def invoke_with_retry(make_client, request: str, attempts: int = 3) -> str:
    """
    Invoca un especialista A2A con reintentos.

    Los runtimes de AgentCore tienen cold start: la primera invocación tras un
    periodo inactivo puede fallar o tardar. Reintentamos con una espera breve
    antes de rendirnos y devolver el mensaje degradado.
    """
    import asyncio

    last_error: Exception | None = None
    for i in range(attempts):
        try:
            client = make_client()
            result = await client.invoke_async(request)
            return str(result.message)
        except Exception as e:  # noqa: BLE001
            last_error = e
            log.warning(f"Intento {i + 1}/{attempts} falló: {type(e).__name__}")
            if i < attempts - 1:
                await asyncio.sleep(2 * (i + 1))  # backoff: 2s, 4s
    # Se agotaron los reintentos
    raise last_error if last_error else RuntimeError("Fallo desconocido")


# ── Manejo de fallos (reto avanzado) ──────────────────────────────────

def degraded_message(specialist: str, error: Exception) -> str:
    """
    Respuesta degradada cuando un especialista no responde (graceful degradation).
    En vez de romper toda la respuesta, devolvemos un aviso para que el orquestador
    consolide con lo que sí tiene.
    """
    log.warning(f"Especialista '{specialist}' no disponible: {error!r}")
    return (
        f"ERROR_SERVICIO: El servicio de {specialist} no está disponible en este momento. "
        f"NO tengo datos de {specialist}. INSTRUCCIÓN OBLIGATORIA: informa al usuario que el "
        f"servicio de {specialist} no está disponible ahora mismo y NO inventes ni supongas "
        f"ningún dato de {specialist} (ni nombres, ni precios, ni horarios). Continúa solo con "
        f"la información de otros servicios que sí hayas obtenido."
    )


# ── Extracción de texto de eventos A2A crudos ─────────────────────────

def extract_text(a2a_event: object) -> str:
    """Extrae texto plano de un evento A2A crudo emitido por stream_async."""
    if isinstance(a2a_event, tuple) and len(a2a_event) == 2:
        _, update = a2a_event
        artifact = getattr(update, "artifact", None)
        if artifact is not None:
            return _text_from_parts(getattr(artifact, "parts", []))
        status = getattr(update, "status", None)
        if status is not None and getattr(status, "message", None) is not None:
            return _text_from_parts(getattr(status.message, "parts", []))
        return ""

    parts = getattr(a2a_event, "parts", None)
    if parts is not None:
        return _text_from_parts(parts)
    return ""


def _text_from_parts(parts: list) -> str:
    chunks: list[str] = []
    for part in parts or []:
        root = getattr(part, "root", part)
        text = getattr(root, "text", None)
        if text:
            chunks.append(text)
    return "".join(chunks)
