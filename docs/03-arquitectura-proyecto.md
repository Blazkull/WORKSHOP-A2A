# Arquitectura y estructura del proyecto — Trip Planner A2A

Este documento explica **qué hace cada archivo**, cómo se comparten las
dependencias, y las decisiones de diseño del proyecto. Es la referencia
técnica para entender el código.

---

## 1. Visión general

Un **Trip Planner** multi-agente sobre AWS Bedrock AgentCore que usa el
protocolo **Agent-to-Agent (A2A)** con **Strands Agents**.

- **3 agentes especialistas** (servidores A2A): Flights, Weather, Hotels.
- **1 agente orquestador** (cliente A2A): recibe al usuario, delega y consolida.

El orquestador nunca importa el código de los especialistas: los descubre por
red mediante su `agent-card` y los invoca por el protocolo A2A. Ese
desacoplamiento es la esencia del patrón.

---

## 2. Árbol del proyecto

```
workshop-a2a/
├── .venv/                      # Entorno virtual local (uv). NO se despliega.
├── requirements.txt            # Dependencias compartidas (dev local)
├── .gitignore
├── README.md
│
├── docs/                       # Documentación
│   ├── 01-diagrama-contexto.md
│   ├── 02-diagrama-secuencia.md
│   └── 03-arquitectura-proyecto.md   ← este archivo
│
├── scripts/
│   └── sync_shared.py          # Copia app/shared/ dentro de cada agente
│
├── app/                        # Código de los agentes
│   ├── shared/                 # Utilidades compartidas (fuente única)
│   │   ├── __init__.py
│   │   ├── config.py           # Lectura de variables de entorno
│   │   └── logging.py          # Logger JSON UTF-8
│   │
│   ├── FlightsAgent/           # Servidor A2A — vuelos
│   │   ├── main.py             # Entrypoint: arranca el servidor
│   │   ├── server.py           # Factory del A2AServer + create_agent
│   │   ├── tools.py            # @tool search_flights (función pura)
│   │   ├── agent_card.py       # Skills A2A (AgentSkill)
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   └── mock.py         # Datos simulados de vuelos
│   │   ├── pyproject.toml      # Dependencias del agente (para deploy)
│   │   ├── uv.lock             # Lockfile generado por uv
│   │   ├── requirements.txt    # (referencia; el deploy usa pyproject)
│   │   └── shared/             # COPIA sincronizada de app/shared/ (gitignored)
│   │
│   ├── WeatherAgent/           # Servidor A2A — clima (misma estructura)
│   ├── HotelsAgent/            # Servidor A2A — hoteles (misma estructura)
│   │
│   └── OrchestratorAgent/      # Cliente A2A — punto de entrada del usuario
│       ├── main.py             # Entrypoint BedrockAgentCoreApp (@app.entrypoint)
│       ├── agent.py            # Factory del orquestador (tools manuales)
│       ├── swarm.py            # Variante multi-agente (as_tool) — reto Graph/Swarm
│       ├── tools.py            # ask_flights / ask_weather / ask_hotels
│       ├── a2a_clients.py      # Clientes A2A remotos + SigV4 + failover
│       ├── streaming.py        # Streaming end-to-end (stream_async)
│       ├── invoke-policy.json  # IAM: permiso InvokeAgentRuntime
│       ├── pyproject.toml
│       └── shared/             # COPIA sincronizada (gitignored)
│
└── agentcore/                  # Configuración e infraestructura de despliegue
    ├── agentcore.json          # Declaración de los 4 runtimes (fuente de verdad)
    ├── aws-targets.json        # Cuenta + región de despliegue
    ├── deploy-policy.json      # IAM: política de permisos para desplegar
    ├── SETUP-DEPLOY.md         # Guía de despliegue paso a paso
    ├── .cli/                   # Estado y logs del CLI (gitignored)
    └── cdk/                    # Proyecto CDK (genera el CloudFormation)
        ├── package.json
        ├── cdk.json
        ├── bin/cdk.ts          # Lee agentcore.json y sintetiza el stack
        └── lib/cdk-stack.ts    # Define los recursos AWS (L3 constructs)
```

---

## 3. La capa `shared/` — utilidades compartidas

### `shared/config.py`
Centraliza la lectura de variables de entorno. Ningún otro archivo llama a
`os.environ` directamente.

| Función | Devuelve |
|---|---|
| `get_model_id()` | ID del modelo Bedrock (`us.amazon.nova-lite-v1:0`) |
| `get_port(default)` | Puerto del servidor A2A |
| `get_flights_url()` | URL del FlightsAgent (env `FLIGHTS_AGENT_URL`) |
| `get_weather_url()` | URL del WeatherAgent |
| `get_hotels_url()` | URL del HotelsAgent |
| `get_agent_version()` | Versión semántica para la AgentCard |

### `shared/logging.py`
`get_logger(name)` devuelve un logger que emite **JSON por línea** (indexable
en CloudWatch) y **fuerza UTF-8** en stdout para que las tildes y la ñ salgan
correctas.

---

## 4. Anatomía de un agente especialista (FlightsAgent)

Todos los especialistas siguen la misma separación en capas. Ejemplo con Flights:

### `data/mock.py` — capa de datos
Datos simulados aislados. `get_flights(origin, destination)` devuelve la lista
de vuelos. Para pasar a producción, solo se cambia este archivo por una llamada
real (p.ej. Duffel API). El resto del agente no se toca.

### `tools.py` — capa de herramientas
```python
@tool
def search_flights(origin, destination, date) -> list[dict]:
    ...
```
Función **pura** decorada con `@tool` de Strands. Recibe parámetros, consulta
la capa de datos, devuelve el resultado. El docstring es lo que el LLM lee para
decidir cuándo usar la herramienta.

### `agent_card.py` — capa de descubrimiento
`build_skills()` devuelve una lista de `AgentSkill` (objetos del SDK A2A) con
id, nombre, descripción en español, tags y ejemplos. Strands publica esto en
`/.well-known/agent-card.json` para que el orquestador descubra qué sabe hacer
el agente.

### `server.py` — capa de servidor A2A
- `create_agent(context_id)`: factory que Strands llama por cada sesión A2A
  (aísla conversaciones concurrentes, A2A spec §3.4). Crea un `Agent` con el
  modelo, la descripción y la tool.
- `build_server()`: construye el `A2AServer` (host, puerto, versión, skills).

### `main.py` — entrypoint
Responsabilidad única: `build_server().serve()`. Es el archivo que AgentCore
ejecuta (`entrypoint: main.py`). Escucha en el puerto **9000** (requisito A2A
de AgentCore).

**Puertos de cada especialista (local):** Flights 9001, Weather 9002, Hotels 9003.
En AgentCore Runtime todos corren en 9000 (cada uno en su microVM aislado).

---

## 5. Anatomía del orquestador (OrchestratorAgent)

Es un **cliente A2A** y el único punto de entrada del usuario. Protocolo HTTP
(puerto 8080), no A2A.

### `a2a_clients.py` — clientes hacia los especialistas
- `make_flights_client()` / `make_weather_client()` / `make_hotels_client()`:
  crean un `A2AAgent` apuntando a la URL del especialista, con un cliente httpx
  que **firma cada petición con AWS SigV4** (`_SigV4Auth`) — necesario porque
  invocar un runtime de AgentCore requiere autenticación AWS — y añade el header
  `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id`.
- `degraded_message(specialist, error)`: **manejo de fallos**. Si un
  especialista no responde, devuelve un aviso legible en vez de romper la
  respuesta (degradación elegante).
- `extract_text(a2a_event)`: extrae el texto de los eventos A2A crudos.

### `tools.py` — herramientas de delegación
`ask_flights`, `ask_weather`, `ask_hotels`: cada una envuelve un `A2AAgent`
remoto con `invoke_async`. Envueltas en `try/except` que devuelve el mensaje
degradado si el especialista falla. El LLM del orquestador decide cuál llamar.

### `agent.py` — factory del orquestador (modo por defecto)
`build_agent()` crea el `Agent` con el system prompt (política de delegación) y
las 3 tools. El system prompt define las reglas: cuándo usar cada tool, cómo
consolidar, degradación elegante, pedir datos faltantes.

### `swarm.py` — variante multi-agente (reto Graph/Swarm)
`build_swarm_agent()` integra los `A2AAgent` remotos como **sub-agentes** del
orquestador usando `agent.as_tool()` de Strands, en vez de las tools manuales.
Es más idiomático del framework. Se activa con `{"mode": "swarm"}`.

### `streaming.py` — streaming end-to-end (reto avanzado)
`stream_flights` / `stream_weather` / `stream_hotels` usan
`A2AAgent.stream_async` para reenviar tokens del especialista al usuario a
medida que llegan. Se activa con `{"stream_direct": true, "specialist": "..."}`.

### `main.py` — entrypoint AgentCore
`@app.entrypoint async def invoke(payload, context)`: valida el prompt y decide
el modo:
- **default**: orquestación por LLM con `agent.stream_async`.
- **swarm**: patrón multi-agente.
- **stream_direct**: streaming directo de un especialista.
Fuerza UTF-8 en stdout/stderr.

---

## 6. Cómo se comparten las dependencias (punto clave)

Hay **dos niveles** de dependencias:

### a) Paquetes Python (strands, bedrock-agentcore)
Cada agente declara sus dependencias en su **`pyproject.toml`**. Al desplegar,
AgentCore lee ese archivo, resuelve con `uv` (usando `uv.lock`) y empaqueta las
librerías dentro del ZIP del agente. En local, el `.venv` de la raíz tiene todo
instalado para desarrollo.

### b) El módulo `shared/`
Problema: AgentCore empaqueta **solo el `codeLocation` de cada agente**
(`app/FlightsAgent/`), así que `app/shared/` (que está fuera) **no viajaría**
con el agente y los `from shared.config import ...` fallarían en la nube.

Solución: **`scripts/sync_shared.py`** copia una instantánea de `app/shared/`
dentro de cada agente (`app/FlightsAgent/shared/`, etc.) **antes de desplegar**.
Estas copias están en `.gitignore` (no se versionan; se regeneran).

**Regla de oro:** edita siempre `app/shared/` (la fuente). Ejecuta
`python scripts/sync_shared.py` tras cada cambio y antes de `agentcore deploy`.

### Imports: absolutos, no relativos
Como AgentCore ejecuta `main.py` como script suelto (no como paquete), los
imports entre módulos del mismo agente son **absolutos**: `from tools import ...`,
`from server import ...`, `from data import ...` — no `from .tools import`.
Cada `main.py` hace `sys.path.insert(0, "..")` para resolver `shared` en local;
tras `sync_shared.py`, `shared` también está en el propio directorio.

---

## 7. La carpeta `agentcore/` — configuración de despliegue

### `agentcore.json` (fuente de verdad)
Declara los 4 runtimes. Campos por runtime:
- `name`: determina el Logical ID en CloudFormation (renombrar = recrear).
- `entrypoint`: `main.py`.
- `codeLocation`: carpeta que se empaqueta.
- `runtimeVersion`: `PYTHON_3_13`.
- `protocol`: `A2A` para especialistas, `HTTP` para el orquestador.
- `envVars`: variables inyectadas (MODEL_ID, PORT, URLs de especialistas).
- `additionalPolicies`: (orquestador) `invoke-policy.json` para poder invocar
  los otros runtimes.

### `aws-targets.json`
Define a dónde se despliega: `account` + `region`. En este proyecto:
cuenta `113410693163`, región `us-east-1`, target `dev`.

### `deploy-policy.json`
Política IAM de mínimo privilegio para el usuario que despliega (CloudFormation,
CDK/S3/SSM, IAM, CodeBuild, ECR, Bedrock AgentCore, observabilidad).

### `invoke-policy.json` (en OrchestratorAgent)
Concede al rol de ejecución del orquestador `bedrock-agentcore:InvokeAgentRuntime`
sobre los 3 especialistas, para que pueda invocarlos vía A2A.

### `cdk/`
Proyecto CDK genérico que **lee `agentcore.json`** y sintetiza el stack
CloudFormation. `bin/cdk.ts` es el punto de entrada; `lib/cdk-stack.ts` define
los recursos con los L3 constructs `@aws/agentcore-cdk`. No se edita a mano:
la fuente de verdad son los JSON.

---

## 8. Flujo de una petición (runtime)

1. Usuario → `OrchestratorAgent` (HTTP) con `{"prompt": "..."}`.
2. El orquestador razona con Nova Lite (Bedrock) y decide qué tools usar.
3. Por cada tool (`ask_flights`, ...), crea un `A2AAgent` firmado con SigV4.
4. Lee el `agent-card` del especialista (descubrimiento) y le envía el mensaje.
5. El especialista razona con su LLM, ejecuta su tool (datos mock) y responde.
6. Si un especialista falla, el orquestador degrada elegantemente.
7. El orquestador consolida todo en una respuesta y la transmite al usuario.

---

## 9. Retos avanzados implementados

| Reto | Dónde | Cómo activar |
|---|---|---|
| Tercer especialista (Hotels) | `app/HotelsAgent/` | Automático (el LLM decide) |
| Streaming end-to-end | `streaming.py` | `{"stream_direct": true, "specialist": "flights"}` |
| Patrón Graph/Swarm | `swarm.py` | `{"mode": "swarm"}` |
| Manejo de fallos | `a2a_clients.py` (`degraded_message`) + try/except | Automático ante error |
