# Setup completo para desplegar el Workshop A2A (cuenta nueva)

Guía paso a paso desde una cuenta AWS nueva (con acceso root) hasta el
despliegue del Trip Planner en AgentCore.

---

## PASO 1 — Habilitar el modelo en Amazon Bedrock

En la cuenta nueva, los modelos NO vienen habilitados por defecto.

1. Inicia sesión en la [Consola AWS](https://console.aws.amazon.com/) como **root**.
2. Arriba a la derecha, selecciona la región **US East (N. Virginia) us-east-1**.
3. Busca el servicio **Amazon Bedrock**.
4. Menú izquierdo → **Model access** (Acceso a modelos).
5. Botón **Enable specific models** (o "Manage model access").
6. Marca **Amazon Nova Lite** (`amazon.nova-lite-v1:0`).
   - Los modelos **Amazon Nova** se activan al instante.
   - Evita Anthropic Claude: exige un formulario de caso de uso y aprobación.
7. **Save changes**.

---

## PASO 2 — Crear un usuario IAM para desplegar

No uses root para el día a día. Crea un usuario programático con permisos de
despliegue.

1. Consola AWS → servicio **IAM** → **Users** → **Create user**.
2. Nombre: `agentcore-deployer`.
3. NO marques acceso a consola (solo programático).
4. **Create user** (los permisos se adjuntan en el PASO 3).

---

## PASO 3 — Adjuntar permisos de despliegue

El despliegue toca varios servicios: CloudFormation, CDK (S3/SSM/ECR),
IAM (crea roles de ejecución), CodeBuild, Bedrock AgentCore y observabilidad
(CloudWatch/X-Ray). Elige UNA de las dos opciones.

### Opción A — Rápida (recomendada para el workshop)

Adjunta dos políticas gestionadas de AWS al usuario `agentcore-deployer`:

1. IAM → Users → `agentcore-deployer` → **Add permissions** →
   **Attach policies directly**.
2. Marca:
   - **`AdministratorAccess`**  ← cubre todo el despliegue sin sorpresas
3. **Add permissions**.

> Alternativa a AdministratorAccess (menos amplia pero suficiente):
> **`PowerUserAccess`** + **`IAMFullAccess`** (IAM es necesario porque
> AgentCore crea roles de ejecución para los runtimes).

### Opción B — Mínimo privilegio (política a medida)

Adjunta la política del archivo `deploy-policy.json` (en esta carpeta), que
combina los permisos oficiales del CLI de AgentCore
([docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html))
con los que necesita CDK/CloudFormation:

1. IAM → Users → `agentcore-deployer` → **Add permissions** →
   **Create inline policy** → pestaña **JSON**.
2. Pega el contenido de `deploy-policy.json`.
3. Nombre: `AgentCoreDeployPolicy` → **Create policy**.

Cubre: `cloudformation:*`, S3/SSM (CDK), IAM (roles), CodeBuild, `ecr:*`,
`bedrock:*`, `bedrock-agentcore:*`, `logs/xray/cloudwatch`.

---

## PASO 4 — Generar credenciales del usuario

1. IAM → Users → `agentcore-deployer` → pestaña **Security credentials**.
2. **Access keys** → **Create access key** → caso de uso
   **Command Line Interface (CLI)** → **Create**.
3. **Copia** el `Access Key ID` y el `Secret Access Key`.
   (El secret solo se muestra UNA vez.)

---

## PASO 5 — Configurar el perfil en AWS CLI

> Seguridad: configura las claves TÚ mismo. No las pegues en el chat.

```bash
aws configure --profile agentcore-deployer
```

Rellena:
- **AWS Access Key ID**: (pega el Access Key)
- **AWS Secret Access Key**: (pega el Secret)
- **Default region name**: `us-east-1`
- **Default output format**: `json`

---

## PASO 6 — Verificar identidad (confirmar la cuenta nueva)

```bash
aws sts get-caller-identity --profile agentcore-deployer
```

Comparte SOLO la salida de este comando (Account / UserId / Arn — no son
secretos). Con el `Account` se actualiza el target del proyecto.

---

## PASO 7 — Bootstrap de CDK (una sola vez por cuenta+región)

Sustituye `NUEVO_ACCOUNT_ID` por el número del PASO 6:

```bash
npx cdk bootstrap aws://NUEVO_ACCOUNT_ID/us-east-1 --profile agentcore-deployer
```

---

## PASO 8 — Actualizar el target del proyecto

El archivo `agentcore/aws-targets.json` debe tener el `account` de la cuenta
nueva. (Kiro lo actualiza; solo hace falta el número del PASO 6.)

---

## PASO 9 — Desplegar (Fase 1: especialistas)

```bash
$env:AWS_PROFILE = "agentcore-deployer"   # PowerShell
agentcore deploy
agentcore status                          # muestra las URLs de los runtimes
```

---

## PASO 10 — Cablear URLs y redesplegar (Fase 2: orquestador)

1. Copia las URLs de FlightsAgent, WeatherAgent y HotelsAgent que dio
   `agentcore status`.
2. Ponlas en las `envVars` del OrchestratorAgent en `agentcore.json`
   (reemplazan los placeholders `PENDING_AFTER_..._DEPLOY`).
3. Redesplega:

```bash
agentcore deploy
```

---

## PASO 11 — Verificar

```bash
agentcore invoke --runtime OrchestratorAgent ^
  --payload "{\"prompt\": \"Vuelos, clima y hoteles de Bogota a Cartagena este fin de semana\"}"
```

**Criterio de éxito:** una respuesta que combina vuelos, clima y hoteles, con
invocaciones A2A salientes visibles en `agentcore logs --runtime OrchestratorAgent`.

---

## Notas

- **Costos:** el despliegue provisiona infraestructura facturable (runtimes,
  ECR, CodeBuild, S3). Para limpiar todo al terminar:
  ```bash
  agentcore remove all
  agentcore deploy
  ```
- **Seguridad:** `AdministratorAccess` y la política amplia son adecuadas para
  un workshop de práctica. En producción, restringe al mínimo privilegio
  (Opción B, acotando recursos por ARN).
