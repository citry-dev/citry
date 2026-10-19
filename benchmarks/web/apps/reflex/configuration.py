"""Select the same owned Reflex configuration for preparation and production."""

import os
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
NODE = HERE / ".toolchain/node-v22.22.0-darwin-arm64/bin/node"
BUN = HERE / ".reflex/bun/bin/bun"


def configure_environment(*, compile_frontend: bool) -> None:
    """Set options before Reflex imports can read environment or dotenv files."""
    for key in list(os.environ):
        if key.startswith(("REFLEX_", "__REFLEX_")):
            del os.environ[key]
    os.environ.update(
        {
            "REFLEX_DIR": str(HERE / ".reflex"),
            "REFLEX_WEB_WORKDIR": str(HERE / ".web"),
            "REFLEX_STATES_WORKDIR": str(Path(os.environ.get("CITRY_BENCH_RUNTIME_DIR", HERE)) / ".states"),
            "REFLEX_BUN_PATH": str(BUN),
            "REFLEX_USE_SYSTEM_BUN": "false",
            "REFLEX_ENV_MODE": "prod",
            # The installed release prefixes internal environment options with two underscores.
            "__REFLEX_SKIP_COMPILE": "false" if compile_frontend else "true",
            "PATH": str(NODE.parent) + os.pathsep + os.environ.get("PATH", ""),
        }
    )


def validate_configuration(config: Any, node: Path | None, bun: Path | None) -> None:
    """Reject effective settings or selected tools outside this adapter's contract."""
    expected = {
        "app_name": "board_app",
        "api_url": "http://127.0.0.1:8917",
        "deploy_url": "http://127.0.0.1:8917",
        "backend_port": 8917,
        "telemetry_enabled": False,
        "frozen_lockfile": True,
        "transport": "websocket",
        "state_manager_mode": "memory",
        "cors_allowed_origins": ["http://127.0.0.1:8917"],
    }
    for name, value in expected.items():
        if getattr(config, name) != value:
            raise RuntimeError(f"Unexpected effective Reflex setting: {name}")
    if node is None or node.resolve() != NODE.resolve():
        raise RuntimeError("Reflex selected a Node executable outside the pinned toolchain")
    if bun is None or bun.resolve() != BUN.resolve():
        raise RuntimeError("Reflex selected a Bun executable outside the pinned toolchain")
