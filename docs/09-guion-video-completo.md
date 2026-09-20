# Guion completo para el video — Trip Planner A2A

Guion detallado para grabar el video explicativo al profesor. Cubre:
explicación del código de cada componente, el despliegue en AWS, y una demo
del agente en el Playground de AgentCore.

**Duración total sugerida: 12-15 min.** Cada sección indica qué mostrar en
pantalla y qué decir (texto guía, no leer literal).

---

## SECCIÓN 0 · Introducción (1 min)

**Mostrar:** el diagrama de contexto (`docs/01-diagrama-contexto.md`).

**Decir:**
> "Construí un **Trip Planner** con el patrón **Agent-to-Agent (A2A)** sobre
> AWS Bedrock AgentCore. Un **orquestador** recibe la petición del usuario y
> delega en **tres especialistas independientes**: vuelos, clima y hoteles.
> Cada uno es un servicio separado que se descubre y se invoca por red, sin
> compartir código ni memoria. El orquestador consolida todo en una respuesta."

**Punto clave a resaltar:** el desacoplamiento — el orquestador solo conoce las
URLs de los especialistas, nunca su código.

---

## SECCIÓN 1 · Estructura del proyecto (1.5 min)

**Mostrar:** el árbol de `app/` en el explorador y `docs/03-arquitectura-proyecto.md`.

**Decir:**
> "El proyecto tiene 4 agentes en `app/`. Cada especialista sigue la misma
> estructura en capas: `data/mock.py` con los datos, `tools.py` con la
> herramienta, `agent_card.py` con las skills que publica, `server.py` que
> monta el servidor A2A, y `main.py` que lo arranca. Hay un módulo `shared/`
> con configuración y logging, que se comparte entre todos."

**Mostrar rápido:** `app/shared/config.py` y `scripts/sync_shared.py`.

> "Como AgentCore empaqueta cada agente por separado, uso `sync_shared.py`
> para copiar `shared` dentro de cada uno antes de desplegar."

---

## SECCIÓN 2 · Explicación del código — un especialista (2.5 min)

Usa **FlightsAgent** como ejemplo (los otros son idénticos en estructura).

### 2.1. La capa de datos — `app/FlightsAgent/data/mock.py`
**Decir:**
> "Aquí están los datos simulados de vuelos, aislados. Si quisiera pasar a
> producción con la API de Duffel, solo cambiaría este archivo; el resto del
> agente no se toca."

**Mostrar:** el diccionario `FLIGHTS` y la función `get_flights()`.

### 2.2. La herramienta — `app/FlightsAgent/tools.py`
**Decir:**
> "La herramienta `search_flights` es una función pura decorada con `@tool` de
> Strands. El docstring es lo que el modelo lee para saber cuándo usarla y qué
> parámetros pasar."

**Mostrar:** la función `search_flights` con su docstring.

### 2.3. La agent-card — `app/FlightsAgent/agent_card.py`
**Decir:**
> "`build_skills` define las capacidades que este agente publica en su
> agent-card: id, nombre, descripción, tags y ejemplos. Es lo que el
> orquestador lee para descubrir qué sabe hacer."

### 2.4. El servidor A2A — `app/FlightsAgent/server.py`
**Decir:**
> "`create_agent` construye el agente Strands con el modelo y la herramienta.
> `build_server` monta el `A2AServer`, que automáticamente publica la
> agent-card en `/.well-known/agent-card.json` y expone el endpoint para
> recibir mensajes A2A. En local uso `PUBLIC_URL` para que anuncie 127.0.0.1."

### 2.5. El entrypoint — `app/FlightsAgent/main.py`
**Decir:**
> "`main.py` solo arranca el servidor. Es el archivo que AgentCore ejecuta.
> Escucha en el puerto 9000 en la nube."

---

## SECCIÓN 3 · Explicación del código — el orquestador (3 min)

### 3.1. Los clientes A2A — `app/OrchestratorAgent/a2a_clients.py`
**Decir:**
> "Aquí está el corazón de la comunicación. `_make_client` decide cómo hablar
> con un especialista según el entorno:
> - En **local**, un cliente A2A simple que lee la agent-card normalmente.
> - En la **nube**, firma cada petición con **AWS SigV4** (porque los agentes
>   usan autenticación AWS_IAM) y pre-inyecta la agent-card, porque en AgentCore
>   el GET del agent-card da 403; así va directo al POST firmado que sí funciona."

**Mostrar:** `_make_client`, `_SigV4Auth`, `_prebuilt_card`.

**Decir sobre tolerancia a fallos:**
> "`invoke_with_retry` reintenta 3 veces con backoff, porque los runtimes tienen
> cold start. Si aun así falla, `degraded_message` devuelve una instrucción
> explícita al modelo de NO inventar datos."

### 3.2. Las tools de delegación — `app/OrchestratorAgent/tools.py`
**Decir:**
> "`ask_flights`, `ask_weather` y `ask_hotels` envuelven a cada especialista
> remoto. El modelo decide cuál llamar. Cada una tiene manejo de fallos."

### 3.3. El agente y su prompt — `app/OrchestratorAgent/agent.py`
**Decir:**
> "`build_agent` crea el orquestador con el system prompt. Las reglas incluyen:
> usa la tool adecuada, consolida en una respuesta, y — muy importante — NUNCA
> inventes datos ni muestres el razonamiento interno."

**Mostrar:** las reglas críticas del `SYSTEM_PROMPT`.

### 3.4. El entrypoint — `app/OrchestratorAgent/main.py`
**Decir:**
> "El entrypoint valida el prompt, ejecuta el orquestador, acumula solo el texto
> de la respuesta y limpia los bloques `<thinking>` antes de entregarla. Soporta
> tres modos: normal, swarm (multi-agente), y streaming directo."

---

## SECCIÓN 4 · Configuración de despliegue (1.5 min)

**Mostrar:** `agentcore/agentcore.json`.

**Decir:**
> "Aquí declaro los 4 runtimes. Los especialistas usan `protocol: A2A`, el
> orquestador `HTTP`. El orquestador tiene las URLs de los especialistas como
> variables de entorno y un `invoke-policy.json` que le da permiso para
> invocarlos. La cuenta y región están en `aws-targets.json`."

**Mostrar:** `agentcore/aws-targets.json` y `app/OrchestratorAgent/invoke-policy.json`.

---

## SECCIÓN 5 · Despliegue en AWS (2.5 min)

**Mostrar:** una terminal en la raíz del proyecto.

### 5.1. Prerrequisitos
**Decir:**
> "Necesito: modelo Nova Lite habilitado en Bedrock, un usuario IAM con permisos
> (AdministratorAccess para el workshop) y el perfil AWS configurado."

**Ejecutar:**
```powershell
$env:AWS_PROFILE='agentcore-deployer'; $env:AWS_REGION='us-east-1'
aws sts get-caller-identity --profile agentcore-deployer
```
> "Confirmo que estoy en la cuenta correcta."

### 5.2. Validar y desplegar
**Ejecutar:**
```powershell
python scripts/sync_shared.py      # sincroniza shared
agentcore validate                 # valida la config
agentcore deploy                   # despliega los 4 runtimes
```

**Decir mientras despliega:**
> "AgentCore valida el proyecto, construye el CDK, sintetiza CloudFormation,
> hace el bootstrap automáticamente, sube los artefactos a S3 y crea los 4
> runtimes. La primera vez toma unos minutos."

### 5.3. Verificar el despliegue
**Ejecutar:**
```powershell
agentcore status
```
> "Los 4 runtimes aparecen en estado READY, cada uno con su ARN y URL."

**Mostrar la consola de AWS:**
```
https://us-east-1.console.aws.amazon.com/bedrock-agentcore/runtimes?region=us-east-1
```
> "En la consola de Bedrock AgentCore veo los 4 runtimes desplegados."

### 5.4. Cablear URLs (fase 2)
**Decir:**
> "Las URLs de los especialistas solo existen tras desplegarlos. Las copio de
> `agentcore status`, las pongo en las envVars del orquestador en
> `agentcore.json`, y vuelvo a desplegar con `agentcore deploy`."

---

## SECCIÓN 6 · Demo en el Playground de AgentCore (2 min)

El **Playground** (o Sandbox) es la UI de AWS para probar un runtime desplegado.

### 6.1. Abrir el Playground
**Mostrar en la consola AWS:**
1. Bedrock AgentCore → **Agent Runtime** → clic en `TripPlannerA2A_OrchestratorAgent`.
2. En la pestaña de endpoints, seleccionar el endpoint **DEFAULT**.
3. Clic en **Test** / **Invoke** (abre el Playground/Sandbox).

**Decir:**
> "Este es el Playground de AgentCore. Aquí puedo invocar el orquestador
> directamente desde la consola, sin escribir código."

### 6.2. Ejemplo de invocación en el Playground
**En el campo de payload, escribir:**
```json
{ "prompt": "Busca vuelos de BOG a CTG el 2026-09-27, el clima en Cartagena y hoteles para 2 noches. Hazlo ya." }
```
Clic en **Invoke**.

**Mostrar la respuesta y decir:**
> "El orquestador razona, delega en los tres especialistas vía A2A, y devuelve
> una respuesta consolidada con los vuelos reales (Avianca AV9821 $89, LATAM
> LA4410 $76...), el clima de Cartagena (31°C, soleado) y los hoteles (Hilton,
> Hyatt Regency...). Todo obtenido de los especialistas, no inventado."

### 6.3. Alternativa por CLI (si el Playground no está disponible)
```powershell
agentcore invoke --runtime OrchestratorAgent --target dev `
  "Busca vuelos de BOG a CTG el 2026-09-27, clima y hoteles en CTG. Hazlo ya."
```

---

## SECCIÓN 7 · Demo local — evidencia de la colaboración A2A (2 min)

**Mostrar:** las 4 terminales con los agentes corriendo (o levantarlas en vivo).

**Decir:**
> "También corre en local. Levanto los 3 especialistas en los puertos
> 9001/9002/9003 y el orquestador en 8080."

**Ejecutar la petición (terminal 5):**
```powershell
$body = '{"prompt":"Busca vuelos de BOG a CTG el 2026-09-27, clima y hoteles en CTG para 2 noches. Hazlo ya."}'
Invoke-WebRequest -Uri "http://127.0.0.1:8080/invocations" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing | Select -Expand Content
```

**Mostrar la consola del FlightsAgent y decir:**
> "En la consola del especialista veo llegar el POST `message/send`: es la
> evidencia de que el orquestador lo invocó por A2A. Esa es la colaboración
> entre agentes en acción."

---

## SECCIÓN 8 · Retos avanzados (1 min)

**Decir:**
> "Implementé los cuatro retos avanzados del workshop:
> 1. **Tercer especialista** (HotelsAgent) que el orquestador decide cuándo usar.
> 2. **Streaming end-to-end** con `stream_async` (`streaming.py`).
> 3. **Patrón Graph/Swarm** que integra los A2AAgent como sub-agentes (`swarm.py`).
> 4. **Manejo de fallos**: timeouts, reintentos con backoff y degradación
>    elegante que no inventa datos."

---

## SECCIÓN 9 · Cierre y reflexión (1 min)

**Decir:**
> "Recapitulando: A2A estandariza cómo agentes independientes se descubren y
> colaboran. El patrón orquestador + especialistas permite escalar y desplegar
> cada competencia por separado. Strands me dio el framework, AgentCore el
> runtime serverless, y todo quedó desplegado en AWS y funcionando también en
> local."

**Reflexión (diferencia programa tradicional vs agente):**
> "La mayor diferencia es el cambio de paradigma: en un programa tradicional yo
> codifico cada rama del flujo con condicionales. Aquí expongo herramientas a un
> motor semántico (el LLM) y **delego la orquestación**: el agente decide en
> tiempo real qué especialistas consultar y cómo combinar los resultados. Pasé
> de programar el 'cómo' a declarar el 'qué'."

---

## Checklist de grabación

- [ ] Modelo Nova Lite habilitado en Bedrock.
- [ ] Perfil `agentcore-deployer` configurado.
- [ ] Los 4 runtimes en READY (`agentcore status`).
- [ ] Los 4 agentes locales corriendo (para la demo local).
- [ ] Diagramas abiertos en el editor (docs 01, 06, 07, 08).
- [ ] Terminal limpia y con fuente legible.
- [ ] Payload de ejemplo copiado y listo para pegar.
