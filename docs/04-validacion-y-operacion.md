# Validación y operación — Trip Planner A2A

Cómo confirmar que los agentes están en AWS Bedrock AgentCore, cómo levantar el
servicio localmente, y cómo invocarlos ya desplegados.

Todos los comandos asumen el perfil AWS `agentcore-deployer` y la región
`us-east-1`. En PowerShell, fija el perfil para la sesión:

```powershell
$env:AWS_PROFILE = "agentcore-deployer"
$env:AWS_REGION  = "us-east-1"
```

---

## 1. Estado actual del despliegue

- **Cuenta AWS:** `113410693163`
- **Región:** `us-east-1`
- **Proyecto:** `TripPlannerA2A` (target `dev`)

| Runtime | ID | Estado |
|---|---|---|
| FlightsAgent | `TripPlannerA2A_FlightsAgent-qIJreU42fo` | READY |
| WeatherAgent | `TripPlannerA2A_WeatherAgent-Q0CfsR6BE3` | READY |
| HotelsAgent | `TripPlannerA2A_HotelsAgent-LbMU6mAJfA` | READY |
| OrchestratorAgent | `TripPlannerA2A_OrchestratorAgent-wpdUPo2jiQ` | READY |

---

## 2. Validar que los agentes están en Bedrock AgentCore

### Opción A — Consola AWS (visual)

1. Inicia sesión en la [Consola AWS](https://console.aws.amazon.com/).
2. Región arriba a la derecha: **US East (N. Virginia) us-east-1**.
3. Busca el servicio **Amazon Bedrock AgentCore** (o "Bedrock AgentCore").
4. Menú izquierdo → **Agent Runtime** (Runtimes de agente).
5. Verás los 4 runtimes `TripPlannerA2A_*` con estado **READY**.
6. Clic en cualquiera para ver su ARN, versión, endpoint y configuración.

Ruta directa (pega en el navegador, ya con sesión iniciada):
```
https://us-east-1.console.aws.amazon.com/bedrock-agentcore/runtimes?region=us-east-1
```

### Opción B — CLI de agentcore (rápida)

Desde la **raíz del proyecto** (`workshop-a2a/`):

```powershell
agentcore status
```

Muestra los 4 agentes, su estado READY, ARN y URL de invocación.

### Opción C — AWS CLI (API de control, sin agentcore)

```powershell
aws bedrock-agentcore-control list-agent-runtimes `
  --region us-east-1 `
  --query "agentRuntimes[].{Name:agentRuntimeName,Status:status,Id:agentRuntimeId}" `
  --output table
```

### Opción D — CloudFormation (el stack que creó todo)

```powershell
aws cloudformation describe-stacks `
  --stack-name AgentCore-TripPlannerA2A-dev `
  --region us-east-1 `
  --query "Stacks[0].StackStatus" --output text
```
Debe devolver `CREATE_COMPLETE` o `UPDATE_COMPLETE`.

---

## 3. Levantar el servicio LOCALMENTE (agentcore dev)

`agentcore dev` levanta un runtime local con hot-reload y una **UI de chat web**.
Como hay varios runtimes, se elige uno con `-r`.

> Ejecutar SIEMPRE desde la raíz del proyecto (`workshop-a2a/`), no desde
> `agentcore/`.

### Levantar el orquestador (punto de entrada del usuario)

```powershell
agentcore dev -r OrchestratorAgent
```

Salida esperada:
```
Chat UI: http://localhost:8081
```
Abre esa URL en el navegador para chatear con el agente.

> Nota: `agentcore dev` crea un `.venv` propio dentro de `app/<Agente>/`. Si
> falla con `ModuleNotFoundError: bedrock_agentcore`, instala las dependencias
> en ese venv:
> ```powershell
> uv pip install -r requirements.txt --python app/OrchestratorAgent/.venv/Scripts/python.exe
> ```

### Levantar un especialista (para probar su A2A aislado)

```powershell
agentcore dev -r FlightsAgent
```

### Probar el flujo A2A completo en local

Para que el orquestador delegue en los especialistas en local, los 4 deben
correr a la vez. Abre 4 terminales (una por agente), o levanta cada especialista
directamente con Python:

```powershell
# Terminal 1
$env:PORT=9001; python app/FlightsAgent/main.py
# Terminal 2
$env:PORT=9002; python app/WeatherAgent/main.py
# Terminal 3
$env:PORT=9003; python app/HotelsAgent/main.py
# Terminal 4 (UI de chat)
agentcore dev -r OrchestratorAgent
```

En local el orquestador usa `http://localhost:9001..9003` (sin SigV4).

---

## 4. Invocar los agentes YA DESPLEGADOS en AWS

### Invocar el orquestador

```powershell
agentcore invoke --runtime OrchestratorAgent --target dev `
  "Busca vuelos de Bogota (BOG) a Cartagena (CTG) el 2026-09-27"
```

Modos especiales (payload JSON con `--prompt-file` o prompt directo):
- Patrón swarm: incluir `"mode": "swarm"` en el payload.
- Streaming directo: `"stream_direct": true, "specialist": "flights"`.

### Invocar un especialista directamente (JSON-RPC A2A)

Los especialistas hablan A2A (JSON-RPC). Se invocan con su ARN:

```powershell
agentcore invoke --runtime FlightsAgent --target dev `
  "Vuelos de BOG a CTG el 2026-09-27"
```

### Ver la agent card de un especialista (descubrimiento A2A)

La card se publica en `/.well-known/agent-card.json`. En AgentCore requiere
autenticación; localmente (con el agente corriendo) es directa:

```powershell
curl http://localhost:9001/.well-known/agent-card.json
```

---

## 5. Observabilidad (logs y trazas)

### Log group de cada runtime (CloudWatch)

```
/aws/bedrock-agentcore/runtimes/<RuntimeId>-DEFAULT
```

Ejemplo, ver los últimos errores del orquestador:

```powershell
aws logs filter-log-events `
  --log-group-name "/aws/bedrock-agentcore/runtimes/TripPlannerA2A_OrchestratorAgent-wpdUPo2jiQ-DEFAULT" `
  --filter-pattern "Error" --max-items 10 `
  --region us-east-1 --query "events[].message" --output text
```

### Vía CLI de agentcore

```powershell
agentcore logs --runtime OrchestratorAgent
agentcore traces list
```

---

## 6. Ciclo de actualización y limpieza

### Redesplegar tras cambiar código

```powershell
python scripts/sync_shared.py    # 1. sincroniza shared en cada agente
agentcore validate               # 2. valida la config
agentcore deploy                 # 3. despliega los cambios
```

### Detener sesiones activas (ahorro de costos)

Las sesiones de runtime se apagan solas tras el idle timeout (15 min por
defecto). No hay comando directo en la CLI; se usa la API `StopRuntimeSession`
si se necesita cortar antes.

### Eliminar TODO (teardown)

```powershell
agentcore remove all
agentcore deploy                 # aplica el teardown en AWS
```

---

## 7. Consideraciones importantes de despliegue

1. **Ruta sin espacios recomendada:** versiones viejas del CLI de agentcore
   fallaban con rutas que tienen espacios (`PROGRAMACION AGENTICA`). Se corrigió
   en la CLI 0.30.0. Si aparece un error de "pyproject.toml no reconocido",
   actualiza: `npm install -g @aws/agentcore@latest`.

2. **`npx cdk` se cuelga en Windows:** usar el binario local en su lugar:
   `node agentcore/cdk/node_modules/aws-cdk/bin/cdk ...`. El bootstrap de CDK
   lo hace `agentcore deploy` automáticamente, no hace falta correrlo a mano.

3. **`pyproject.toml` + `uv.lock` obligatorios** para runtimes Python CodeZip.
   Si faltan, el deploy falla en la síntesis. Generar con `uv lock` en cada
   agente.

4. **El módulo `shared` debe sincronizarse** (`sync_shared.py`) antes de cada
   deploy, o los agentes fallarán al importar en la nube.

5. **Modelo Bedrock habilitado:** en cuenta nueva, habilitar **Amazon Nova
   Lite** en Bedrock → Model access. Los modelos Nova se activan al instante;
   Anthropic Claude requiere un formulario de caso de uso.

6. **Comunicación A2A entre runtimes (RESUELTO):** invocar un runtime A2A
   desde otro en AgentCore requiere tres cosas, todas implementadas en
   `OrchestratorAgent/a2a_clients.py`:
   - **Autenticación SigV4**: el orquestador firma cada petición HTTP con las
     credenciales de su rol de ejecución (clase `_SigV4Auth`). Los agentes usan
     `authorizerType: AWS_IAM` (default), por eso es SigV4, no Bearer/Cognito.
   - **Permiso IAM** `bedrock-agentcore:InvokeAgentRuntime` sobre los
     especialistas (`OrchestratorAgent/invoke-policy.json`, referenciado en
     `additionalPolicies`).
   - **Saltar el GET del agent-card**: en AgentCore el GET a
     `/.well-known/agent-card.json` responde 403 (el proxy A2A solo acepta el
     POST JSON-RPC `message/send`). Se resuelve **pre-inyectando** una
     `AgentCard` construida localmente en el `A2AAgent` (`_prebuilt_card`), para
     que Strands no haga ese GET y vaya directo al POST firmado.
   - **Puerto 9000**: los servidores A2A en AgentCore DEBEN escuchar en el
     puerto 9000 (no 9001/9002/9003). Por eso los especialistas NO llevan la
     envVar `PORT` en `agentcore.json` (usan el default 9000).

7. **Costos:** cada runtime, ECR, CodeBuild y S3 son facturables. Usar
   `agentcore remove all` al terminar para no dejar recursos corriendo.
