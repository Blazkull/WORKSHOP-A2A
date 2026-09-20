# Otorgar permisos de despliegue a agentic-workshop-user

Ejecutar **con un perfil administrador** de la cuenta 707071530981.
Sustituye `admin` por el nombre de tu perfil admin (o quita `--profile admin`
si tu perfil por defecto ya es administrador).

## 1. Adjuntar la política de despliegue (inline)

```bash
aws iam put-user-policy \
  --user-name agentic-workshop-user \
  --policy-name AgentCoreDeployPolicy \
  --policy-document file://deploy-policy.json \
  --profile admin
```

> Ejecutar desde la carpeta `workshop-a2a/agentcore/` (donde está deploy-policy.json).

## 2. Verificar que se adjuntó

```bash
aws iam get-user-policy \
  --user-name agentic-workshop-user \
  --policy-name AgentCoreDeployPolicy \
  --profile admin
```

## 3. Bootstrap de CDK (una sola vez por cuenta+región)

Necesario para que CDK pueda subir assets. Ejecutar con el perfil admin:

```bash
npx cdk bootstrap aws://707071530981/us-east-1 --profile admin
```

## 4. Desplegar (ya con el usuario del workshop)

Volver a la raíz del proyecto y desplegar normalmente:

```bash
cd ..
agentcore deploy
```
