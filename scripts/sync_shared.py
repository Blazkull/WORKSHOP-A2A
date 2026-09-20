"""
Sincroniza el paquete `app/shared/` dentro de cada agente antes de desplegar.

AgentCore empaqueta solo el `codeLocation` de cada runtime, así que el módulo
`shared` (que vive en app/shared/) no viaja con cada agente. Este script copia
una instantánea de `shared` dentro de cada agente como `shared/`, de modo que
los imports `from shared.config import ...` funcionen tanto en local como en
AgentCore Runtime.

Uso:
    python scripts/sync_shared.py

Ejecútalo cada vez que cambies algo en app/shared/ y antes de `agentcore deploy`.
Las copias sincronizadas se ignoran en git (ver .gitignore).
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
SHARED_SRC = APP / "shared"

AGENTS = ["FlightsAgent", "WeatherAgent", "HotelsAgent", "OrchestratorAgent"]


def sync() -> None:
    if not SHARED_SRC.is_dir():
        raise SystemExit(f"No se encontró {SHARED_SRC}")

    for agent in AGENTS:
        dst = APP / agent / "shared"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(
            SHARED_SRC,
            dst,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        print(f"  shared -> app/{agent}/shared")

    print("Sincronización completada.")


if __name__ == "__main__":
    sync()
