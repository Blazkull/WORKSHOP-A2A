# Flujo de una petición — diagramas paso a paso

Qué ocurre exactamente desde que el usuario escribe hasta que recibe la
respuesta consolidada. Incluye el flujo feliz, el flujo con fallo, y el detalle
técnico interno.

---

## 1. Flujo general (alto nivel)

```mermaid
flowchart TD
    A([Usuario escribe petición]) --> B[POST /invocations al Orquestador]
    B --> C[Orquestador razona con Bedrock:<br/>¿qué especialistas necesito?]
    C --> D{¿Qué pide<br/>el usuario?}
    D -->|vuelos| E[ask_flights]
    D -->|clima| F[ask_weather]
    D -->|hoteles| G[ask_hotels]
    E --> H[A2A → FlightsAgent]
    F --> I[A2A → WeatherAgent]
    G --> J[A2A → HotelsAgent]
    H --> K[Cada especialista ejecuta su tool<br/>datos mock + razona con Bedrock]
    I --> K
    J --> K
    K --> L[Orquestador consolida<br/>resultados con Bedrock]
    L --> M[Limpia thinking, streaming]
    M --> N([Respuesta consolidada al usuario])
```

---

## 2. Diagrama de secuencia detallado (flujo feliz)

Escenario: *"Vuelos y clima de Bogotá a Cartagena el 2026-09-27"*.

```mermaid
sequenceDiagram
    autonumber
    actor U as 👤 Usuario
    participant O as 🧭 Orchestrator (8080)
    participant B as 🧠 Bedrock (Nova Lite)
    participant F as ✈️ FlightsAgent (9001/9000)
    participant W as 🌦️ WeatherAgent (9002/9000)

    U->>O: POST /invocations {"prompt":"vuelos y clima BOG→CTG 2026-09-27"}
    activate O
    O->>B: stream_async(prompt) — planifica
    B-->>O: Plan: usar ask_flights + ask_weather

    Note over O,F: --- Delegación a Flights ---
    O->>F: GET /.well-known/agent-card.json (o card pre-inyectada en nube)
    F-->>O: skills: search_flights, url
    O->>F: POST message/send "Vuelos BOG→CTG 2026-09-27"
    activate F
    F->>F: ejecuta tool search_flights (data/mock)
    F->>B: razona la respuesta con los vuelos
    B-->>F: texto con 3 vuelos
    F-->>O: A2A result (AV9821 $89, LA4410 $76, AV9835 $102)
    deactivate F

    Note over O,W: --- Delegación a Weather ---
    O->>W: POST message/send "Clima en CTG 2026-09-27"
    activate W
    W->>W: ejecuta tool get_weather_forecast (data/mock)
    W->>B: razona el pronóstico
    B-->>W: 31°C, Soleado
    W-->>O: A2A result (clima Cartagena)
    deactivate W

    Note over O,B: --- Consolidación ---
    O->>B: consolida vuelos + clima en una respuesta
    B-->>O: texto final consolidado
    O->>O: _clean_output (quita <thinking>)
    O-->>U: "Aquí tienes los vuelos... y el clima..."
    deactivate O
```

---

## 3. Flujo con fallo de un especialista (degradación elegante)

Escenario: el WeatherAgent no responde (cold start / caído).

```mermaid
sequenceDiagram
    autonumber
    actor U as 👤 Usuario
    participant O as 🧭 Orchestrator
    participant F as ✈️ FlightsAgent
    participant W as 🌦️ WeatherAgent (caído)

    U->>O: "vuelos y clima BOG→CTG"
    O->>F: A2A message/send
    F-->>O: OK (3 vuelos)

    O->>W: A2A message/send (intento 1)
    W--xO: ConnectError
    Note over O: espera 2s
    O->>W: intento 2
    W--xO: ConnectError
    Note over O: espera 4s
    O->>W: intento 3
    W--xO: ConnectError
    O->>O: degraded_message("clima")<br/>"NO inventes datos"
    O-->>U: "Aquí están los vuelos [datos reales].<br/>El servicio de clima no está disponible ahora."
```

Clave: el orquestador **NO inventa** el clima; informa la indisponibilidad y
entrega lo que sí obtuvo (los vuelos). Esto es la degradación elegante.

---

## 4. Detalle técnico: qué hace el código en cada paso

| # | Paso | Archivo / función |
|---|---|---|
| 1 | Recibe `POST /invocations` | `main.py` → `@app.entrypoint invoke()` |
| 2 | Valida que `prompt` es string | `main.py` |
| 3 | Construye el agente | `agent.py` → `build_agent()` |
| 4 | El LLM decide qué tool usar | Strands + system prompt |
| 5 | Ejecuta la tool de delegación | `tools.py` → `ask_flights/weather/hotels` |
| 6 | Crea el cliente A2A (local o SigV4) | `a2a_clients.py` → `_make_client()` |
| 7 | Reintenta si falla (cold start) | `a2a_clients.py` → `invoke_with_retry()` |
| 8 | Descubre y envía mensaje A2A | Strands `A2AAgent.invoke_async()` |
| 9 | El especialista ejecuta su tool | (FlightsAgent) `tools.py` → `search_flights` |
| 10 | El especialista consulta datos | `data/mock.py` → `get_flights()` |
| 11 | Si falla, mensaje degradado | `a2a_clients.py` → `degraded_message()` |
| 12 | Consolida y limpia la salida | `main.py` → `_clean_output()` |
| 13 | Transmite al usuario | `main.py` → `yield` |

---

## 5. Formato de la petición y la respuesta

### Petición del usuario al orquestador (HTTP)
```json
POST http://127.0.0.1:8080/invocations
{ "prompt": "Vuelos de BOG a CTG el 2026-09-27, clima y hoteles en CTG" }
```

Payload opcional para modos avanzados:
```json
{ "prompt": "...", "mode": "swarm" }                          // patrón multi-agente
{ "prompt": "...", "stream_direct": true, "specialist": "flights" }  // streaming directo
```

### Mensaje A2A del orquestador al especialista (JSON-RPC)
```json
POST {endpoint}/
{
  "jsonrpc": "2.0", "id": "req-001", "method": "message/send",
  "params": { "message": {
    "role": "user",
    "parts": [{ "kind": "text", "text": "Vuelos de BOG a CTG el 2026-09-27" }],
    "messageId": "uuid"
  }}
}
```

### Respuesta consolidada al usuario (streaming SSE)
```
data: "Aquí tienes los vuelos de Bogotá a Cartagena:
1. Avianca AV9821 — 07:15/08:25 — $89.00
2. LATAM LA4410 — 12:40/13:50 — $76.00
3. Avianca AV9835 — 18:05/19:15 — $102.00

Clima en Cartagena: 31°C, Soleado. Lleva ropa ligera.

Hoteles (2 noches): Hilton Cartagena (Bocagrande) $380 total, ..."
```

---

## 6. Puntos de decisión del orquestador (LLM)

```mermaid
flowchart TD
    P[Petición del usuario] --> Q{¿Tiene ciudad<br/>y fecha?}
    Q -->|No| Ask[Pide los datos faltantes]
    Q -->|Sí| Intent{¿Qué competencias<br/>menciona?}
    Intent -->|solo vuelos| V[ask_flights]
    Intent -->|solo clima| C[ask_weather]
    Intent -->|solo hoteles| H[ask_hotels]
    Intent -->|varias| All[invoca todas<br/>las relevantes]
    V & C & H & All --> Cons[Consolida en<br/>UNA respuesta]
    Cons --> Rule{¿Algún servicio<br/>falló?}
    Rule -->|Sí| Inform[Informa indisponibilidad<br/>NO inventa datos]
    Rule -->|No| Final[Respuesta completa]
```

Estas decisiones las toma el LLM guiado por el **system prompt** de `agent.py`,
que incluye las reglas anti-alucinación y de consolidación.
