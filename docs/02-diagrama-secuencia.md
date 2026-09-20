# Diagrama de Secuencia — Trip Planner A2A

Flujo temporal de una petición completa. Observa el paso de **descubrimiento** (lectura de la agent card) antes de la primera invocación de cada especialista.

```mermaid
sequenceDiagram
    autonumber
    actor U as 👤 Usuario
    participant O as 🧭 Orchestrator (Cliente A2A)
    participant F as ✈️ Flights Agent (Servidor A2A)
    participant W as 🌦️ Weather Agent (Servidor A2A)
    participant H as 🏨 Hotels Agent (Servidor A2A)
    participant B as 🧠 Amazon Bedrock (LLM)

    U->>O: "Vuelos, clima y hoteles Bogotá→Cartagena, este finde"
    O->>B: Razona el plan (¿qué especialistas usar?)
    B-->>O: Plan: consultar vuelos + clima + hoteles

    Note over O,F: Descubrimiento vía agent card
    O->>F: GET /.well-known/agent-card.json
    F-->>O: Skills: search_flights(origen, destino, fecha)
    O->>F: A2A message: buscar vuelos BOG→CTG
    F->>B: Genera respuesta con datos de vuelos
    B-->>F: Vuelos disponibles
    F-->>O: Resultado: 3 vuelos (horarios, precio)

    Note over O,W: Descubrimiento vía agent card
    O->>W: GET /.well-known/agent-card.json
    W-->>O: Skills: get_weather_forecast(ciudad, fecha)
    O->>W: A2A message: clima en Cartagena
    W->>B: Genera pronóstico
    B-->>W: 31°C, soleado
    W-->>O: Resultado: pronóstico Cartagena

    Note over O,H: Descubrimiento vía agent card
    O->>H: GET /.well-known/agent-card.json
    H-->>O: Skills: search_hotels(ciudad, checkin, noches)
    O->>H: A2A message: hoteles en Cartagena, 2 noches
    H->>B: Genera respuesta con datos de hoteles
    B-->>H: Hoteles disponibles
    H-->>O: Resultado: hoteles (estrellas, barrio, precio)

    O->>B: Consolida vuelos + clima + hoteles en una respuesta
    B-->>O: Texto final del itinerario
    O-->>U: Respuesta consolidada (vuelos + clima + hoteles)
```

## Puntos clave del flujo

1. **Descubrimiento dinámico**: el orquestador lee el `agent-card.json` de cada especialista antes de invocarlos. Esto permite conocer sus capacidades sin estar acoplado al código.

2. **Independencia de los especialistas**: `Flights Agent`, `Weather Agent` y `Hotels Agent` no se conocen entre sí. Solo hablan con el orquestador.

3. **LLM compartido**: los cuatro agentes usan Amazon Bedrock como motor de razonamiento, pero cada uno mantiene su propio contexto de conversación.

4. **Respuesta consolidada**: el orquestador es el único punto de contacto con el usuario — recibe los resultados parciales de los tres especialistas y genera una respuesta única y coherente.

## El problema que resuelve

Un usuario escribe una petición en lenguaje natural como:

> *"Quiero viajar de Bogotá a Cartagena el próximo fin de semana. ¿Qué vuelos hay, cómo estará el clima y en qué hotel me quedo?"*

Resolver esto requiere tres competencias distintas — buscar vuelos, consultar el clima y buscar hoteles. En lugar de un único agente monolítico, aplicamos **separación de responsabilidades**: cada competencia vive en su propio agente independiente, y un cuarto agente (el orquestador) los coordina.
