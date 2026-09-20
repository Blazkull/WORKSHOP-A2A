# Workshop A2A — Trip Planner

Planificador de viajes **multi-agente** sobre **AWS Bedrock AgentCore Runtime**,
usando el protocolo **Agent-to-Agent (A2A)** con **Strands Agents** (Python).

Un usuario escribe una petición en lenguaje natural:

> *"Quiero viajar de Bogotá a Cartagena el próximo fin de semana. ¿Qué vuelos
> hay, cómo estará el clima y en qué hotel me quedo?"*

El **Orchestrator** descubre y delega en **tres especialistas independientes**
(**Flights**, **Weather** y **Hotels**) vía A2A, y consolida una única respuesta.

---

## Estado del proyecto

- ✅ **Desplegado en AWS**: los 4 runtimes están `READY` en AWS Bedrock
  AgentCore (cuenta `113410693163`, región `us-east-1`, proyecto `TripPlannerA2A`).
- ✅ **Funciona en local**: los 4 agentes corren como procesos Python y
  colaboran vía A2A.
- ✅ **Retos avanzados implementados**: tercer especialista, streaming
  end-to-end, patrón Graph/Swarm y manejo de fallos.

| Runtime en AWS | Rol | Estado |
|---|---|---|
| `TripPlannerA2A_OrchestratorAgent` | Cliente A2A (entrada del usuario) | READY |
| `TripPlannerA2A_FlightsAgent` | Servidor A2A (vuelos) | READY |
| `TripPlannerA2A_WeatherAgent` | Servidor A2A (clima) | READY |
| `TripPlannerA2A_HotelsAgent` | Servidor A2A (hoteles) | READY |

---

## Arquitectura

```
Usuario ──▶ OrchestratorAgent (Cliente A2A · HTTP · puerto 8080)
                 │
                 ├──A2A──▶ FlightsAgent  (Servidor A2A · 9000/9001) ──▶ Bedrock
                 ├──A2A──▶ WeatherAgent  (Servidor A2A · 9000/9002) ──▶ Bedrock
                 └──A2A──▶ HotelsAgent   (Servidor A2A · 9000/9003) ──▶ Bedrock
```

- **Modelo LLM:** Amazon Nova Lite (`us.amazon.nova-lite-v1:0`).
- **Puertos:** en AWS los especialistas usan 9000; en local 9001/9002/9003.
- **Descubrimiento:** cada especialista publica su `agent-card`; el orquestador
  la lee antes de invocarlo.

---

## Tecnologías

| Componente | Elección | Motivo |
|---|---|---|
| Framework de agentes | Strands Agents (Python) | Soporte nativo de A2A (servidor y cliente). |
| Plataforma de despliegue | AWS Bedrock AgentCore Runtime | Runtime serverless; requisito del workshop. |
| Protocolo entre agentes | A2A (JSON-RPC) | Foco pedagógico: descubrimiento + delegación. |
| Modelo | Amazon Nova Lite | Se habilita al instante (Anthropic exige formulario). |
| Infraestructura | CDK → CloudFormation | Declarado en `agentcore.json`, materializado por el CLI. |
| Datos | Simulados (mock) | Sin credenciales externas; cambio a producción = 1 archivo. |

---

## Documentación

La documentación está organizada de lo conceptual a lo operativo:

| # | Documento | Contenido |
|---|---|---|
| 01 | [`docs/01-diagrama-contexto.md`](docs/01-diagrama-contexto.md) | Diagrama de contexto (los 4 agentes) y restricciones. |
| 02 | [`docs/02-diagrama-secuencia.md`](docs/02-diagrama-secuencia.md) | Flujo temporal de una petición completa. |
| 03 | [`docs/03-arquitectura-proyecto.md`](docs/03-arquitectura-proyecto.md) | Estructura, qué hace cada archivo/función, dependencias. |
| 04 | [`docs/04-validacion-y-operacion.md`](docs/04-validacion-y-operacion.md) | Validar en Bedrock, operar, observabilidad. |
| 05 | [`docs/05-ejecucion-local-y-video.md`](docs/05-ejecucion-local-y-video.md) | Puertos, levantar los 4 agentes en local, guion del video. |
| 06 | [`docs/06-documento-arquitectonico.md`](docs/06-documento-arquitectonico.md) | Documento arquitectónico: estilo, principios, capas, ADRs. |
| 07 | [`docs/07-servicios-y-comunicacion.md`](docs/07-servicios-y-comunicacion.md) | Cada servicio en detalle y cómo se comunican (A2A). |
| 08 | [`docs/08-flujo-de-peticion.md`](docs/08-flujo-de-peticion.md) | Diagramas de flujo de petición (feliz y con fallo). |
| 09 | [`docs/09-guion-video-completo.md`](docs/09-guion-video-completo.md) | Guion del video: código, despliegue en AWS, demo en Playground. |
| — | [`agentcore/SETUP-DEPLOY.md`](agentcore/SETUP-DEPLOY.md) | Setup de cuenta AWS y despliegue paso a paso. |

---

## Estructura del proyecto

```
workshop-a2a/
├── app/
│   ├── shared/                 # Utilidades compartidas (fuente única)
│   │   ├── config.py           #   lectura de variables de entorno
│   │   └── logging.py          #   logger JSON UTF-8
│   │
│   ├── FlightsAgent/           # Servidor A2A — búsqueda de vuelos
│   │   ├── data/mock.py        #   datos simulados (aislados)
│   │   ├── tools.py            #   @tool search_flights (función pura)
│   │   ├── agent_card.py       #   skills A2A (AgentSkill)
│   │   ├── server.py           #   factory A2AServer + create_agent
│   │   ├── main.py             #   entrypoint (arranca el servidor)
│   │   └── pyproject.toml      #   dependencias del agente (deploy)
│   │
│   ├── WeatherAgent/           # Servidor A2A — clima (misma estructura)
│   ├── HotelsAgent/            # Servidor A2A — hoteles (misma estructura)
│   │
│   └── OrchestratorAgent/      # Cliente A2A — punto de entrada del usuario
│       ├── a2a_clients.py      #   clientes A2A remotos + SigV4 + failover
│       ├── tools.py            #   ask_flights / ask_weather / ask_hotels
│       ├── agent.py            #   factory del orquestador + system prompt
│       ├── swarm.py            #   variante multi-agente (reto Graph/Swarm)
│       ├── streaming.py        #   streaming end-to-end (reto avanzado)
│       ├── invoke-policy.json  #   IAM: permiso InvokeAgentRuntime
│       └── main.py             #   entrypoint BedrockAgentCoreApp
│
├── agentcore/
│   ├── agentcore.json          # 4 runtimes: 3 A2A + 1 HTTP (fuente de verdad)
│   ├── aws-targets.json        # cuenta + región de despliegue
│   ├── deploy-policy.json      # política IAM para desplegar
│   ├── SETUP-DEPLOY.md         # guía de despliegue
│   └── cdk/                    # proyecto CDK (genera CloudFormation)
│
├── scripts/
│   └── sync_shared.py          # copia app/shared/ dentro de cada agente
│
├── docs/                       # documentación (9 documentos + diagramas)
├── requirements.txt            # dependencias compartidas (dev local)
└── .venv/                      # entorno virtual (uv)
```

---

## Cómo se construyó (resumen del proceso)

1. **Diseño A2A**: se definió el patrón orquestador + especialistas siguiendo
   la [spec oficial A2A](https://a2a-protocol.org/latest/specification/).
2. **Agentes especialistas**: cada uno con capas separadas (datos → tool →
   agent-card → server → entrypoint) usando `A2AServer` de Strands.
3. **Orquestador**: cliente A2A con `A2AAgent`, con tools de delegación y
   `BedrockAgentCoreApp` como entrypoint.
4. **Módulo compartido**: `shared/` (config + logging) sincronizado en cada
   agente con `scripts/sync_shared.py` antes de desplegar.
5. **Despliegue**: declarado en `agentcore.json` → CDK → CloudFormation →
   4 runtimes en AWS Bedrock AgentCore.
6. **Comunicación A2A en la nube**: resuelta con firma **SigV4** (auth AWS_IAM),
   permiso `InvokeAgentRuntime` y agent-card pre-inyectada.
7. **Retos avanzados**: tercer especialista, streaming, swarm y manejo de fallos.

---

## Principios de diseño (A2A)

| Principio | Cómo se aplica |
|---|---|
| **Desacoplamiento** | El orquestador solo conoce URLs de los especialistas, nunca su código. |
| **Descubrimiento** | Cada especialista publica su `agent-card` en `/.well-known/agent-card.json`. |
| **Responsabilidad única** | Cada agente resuelve una competencia (vuelos, clima u hoteles). |
| **Modularidad** | Capas separadas: datos → tools → agent → server → entrypoint. |
| **Interoperabilidad** | Contrato estándar A2A (JSON-RPC). |
| **Tolerancia a fallos** | Reintentos con backoff + degradación elegante sin inventar datos. |

---

## Prerrequisitos

- Cuenta AWS con Amazon Bedrock y el modelo `us.amazon.nova-lite-v1:0` habilitado.
- Perfil AWS configurado (`aws configure --profile agentcore-deployer`).
- CLI `agentcore` instalada (`npm install -g @aws/agentcore`).
- Python 3.10+ y `uv`.

Setup completo en [`agentcore/SETUP-DEPLOY.md`](agentcore/SETUP-DEPLOY.md).

---

## Ejecución local (los 4 agentes)

Abre 4 terminales (una por agente). En cada una limpia el token viejo y fija
el perfil. **Los especialistas usan `PUBLIC_URL` para anunciar una URL
conectable** (evita `ConnectError`).

```powershell
# Terminal 1 — FlightsAgent (9001)
cd workshop-a2a/app/FlightsAgent
$env:AWS_BEARER_TOKEN_BEDROCK=$null; $env:AWS_PROFILE='agentcore-deployer'; $env:AWS_REGION='us-east-1'
$env:PORT='9001'; $env:PUBLIC_URL='http://127.0.0.1:9001'
../../.venv/Scripts/python.exe main.py

# Terminal 2 — WeatherAgent (9002)  → PORT=9002, PUBLIC_URL=http://127.0.0.1:9002
# Terminal 3 — HotelsAgent (9003)   → PORT=9003, PUBLIC_URL=http://127.0.0.1:9003
# Terminal 4 — OrchestratorAgent (8080)  → PORT=8080 (sin PUBLIC_URL)
```

Probar (Terminal 5):
```powershell
$body = '{"prompt":"Busca vuelos de BOG a CTG el 2026-09-27, clima y hoteles en CTG para 2 noches. Hazlo ya."}'
Invoke-WebRequest -Uri "http://127.0.0.1:8080/invocations" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing | Select -Expand Content
```

Detalle completo en [`docs/05-ejecucion-local-y-video.md`](docs/05-ejecucion-local-y-video.md).

---

## Despliegue en AWS

Ejecutar desde la raíz del proyecto (`workshop-a2a/`):

```powershell
$env:AWS_BEARER_TOKEN_BEDROCK=$null
$env:AWS_PROFILE='agentcore-deployer'; $env:AWS_REGION='us-east-1'

# 1. Sincronizar el módulo shared en cada agente (OBLIGATORIO antes de desplegar)
.venv\Scripts\python.exe scripts\sync_shared.py

# 2. Validar la configuración
agentcore validate

# 3. Desplegar los 4 runtimes
agentcore deploy

# 4. Verificar estado
agentcore status
```

El flujo es en 2 fases: se despliegan primero los runtimes, se obtienen sus
URLs con `agentcore status`, se cablean en las `envVars` del orquestador en
`agentcore.json`, y se redesplega. Detalle en
[`agentcore/SETUP-DEPLOY.md`](agentcore/SETUP-DEPLOY.md).

---

## Verificación y demo

### En la nube (Playground de AgentCore)
Consola AWS → **Bedrock AgentCore** → **Versión ejecutable** (Agent Runtime) →
selecciona `TripPlannerA2A_OrchestratorAgent` → **Probar** → payload:
```json
{ "prompt": "Busca vuelos de BOG a CTG el 2026-09-27, el clima en Cartagena y hoteles para 2 noches. Hazlo ya." }
```

### Por CLI
```powershell
agentcore invoke --runtime OrchestratorAgent --target dev `
  "Busca vuelos de BOG a CTG el 2026-09-27, clima y hoteles en CTG. Hazlo ya."
```

**Criterio de éxito:** una única respuesta que combina vuelos, clima y hoteles
con datos reales de los especialistas (no inventados), y las invocaciones A2A
visibles en los logs.

---

## Retos avanzados implementados

| Reto | Dónde | Cómo activar |
|---|---|---|
| Tercer especialista (Hotels) | `app/HotelsAgent/` | Automático (el LLM decide) |
| Streaming end-to-end | `OrchestratorAgent/streaming.py` | `{"stream_direct": true, "specialist": "flights"}` |
| Patrón Graph/Swarm | `OrchestratorAgent/swarm.py` | `{"mode": "swarm"}` |
| Manejo de fallos | `OrchestratorAgent/a2a_clients.py` | Automático ante error (reintentos + degradación) |

---

## Endpoints A2A (publicados por cada especialista)

Strands `A2AServer` publica automáticamente:

| Método | Endpoint | Propósito |
|---|---|---|
| `GET`  | `/.well-known/agent-card.json` | Descubrimiento |
| `POST` | `/` y `/message:send` | Enviar mensaje A2A (JSON-RPC) |
| `POST` | `/message:stream` | Streaming (SSE) |

El **Orchestrator** (HTTP) expone `/invocations`, invocable con `agentcore invoke`.
