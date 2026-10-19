"""Reject configuration drift from inherited Reflex settings in fresh processes."""

# Runtime options are read during import, so each mode needs its own interpreter.
# ruff: noqa: PT009
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class ConfigurationTests(unittest.TestCase):
    def test_processing_task_activates_board_and_state_preparation(self) -> None:
        with TemporaryDirectory() as directory:
            code = """
import asyncio
import app
from audit import run_event_scope
from board_app import board_app
from model import reset
from reflex_base.event.processor.base_state_processor import BaseStateEventProcessor
from render_timing import current_pending_preparation

assert BaseStateEventProcessor._execute_event.__wrapped__.__module__ == (
    "reflex_base.event.processor.base_state_processor"
)
reset("timing-proof", 14)

async def construct():
    board_app.snapshot("timing-proof")
    board_app.Board(_reflex_internal_init=True).get_delta()
    timing = current_pending_preparation()
    assert timing is not None and timing.count == 2 and timing.duration >= 0
    return timing

async def check():
    timing = await asyncio.create_task(run_event_scope(construct))
    assert timing.count == 2
    assert current_pending_preparation() is None

asyncio.run(check())
"""
            result = subprocess.run(
                [sys.executable, "-c", code],
                cwd=Path(__file__).parent,
                env={**os.environ, "CITRY_BENCH_RUNTIME_DIR": directory},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_build_and_runtime_ignore_hostile_parent_settings(self) -> None:
        with TemporaryDirectory() as directory:
            dotenv = Path(directory) / "parent.env"
            dotenv.write_text("REFLEX_STATE_MANAGER_MODE=disk\nCITRY_BENCH_DOTENV_LOADED=yes\n")
            environment = {
                **os.environ,
                "REFLEX_API_URL": "https://other.example",
                "REFLEX_DEPLOY_URL": "https://other.example",
                "REFLEX_STATE_MANAGER_MODE": "disk",
                "REFLEX_FROZEN_LOCKFILE": "false",
                "REFLEX_USE_SYSTEM_BUN": "true",
                "REFLEX_BUN_PATH": str(Path(directory) / "missing-bun"),
                "REFLEX_WEB_WORKDIR": str(Path(directory) / "external-web"),
                "REFLEX_ENV_FILE": str(dotenv),
                "REFLEX_TELEMETRY_ENABLED": "true",
                "__REFLEX_SKIP_COMPILE": "false",
                "CITRY_BENCH_RUNTIME_DIR": directory,
            }
            for compile_frontend in (False, True):
                with self.subTest(compile_frontend=compile_frontend):
                    setup = (
                        "from configuration import configure_environment; configure_environment(compile_frontend=True)"
                        if compile_frontend
                        else "import app"
                    )
                    code = f"""
{setup}
import json, os
from configuration import validate_configuration
from reflex.config import get_config
from reflex.environment import environment
from reflex.utils.path_ops import get_bun_path, get_node_path
validate_configuration(get_config(), get_node_path(), get_bun_path())
print(json.dumps({{
    "skip_compile": environment.REFLEX_SKIP_COMPILE.get(),
    "mode": environment.REFLEX_ENV_MODE.get(),
    "states": str(environment.REFLEX_STATES_WORKDIR.get()),
    "dotenv_loaded": os.environ.get("CITRY_BENCH_DOTENV_LOADED"),
}}))
"""
                    result = subprocess.run(
                        [sys.executable, "-c", code],
                        cwd=Path(__file__).parent,
                        env=environment,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    observed = json.loads(result.stdout.strip().splitlines()[-1])
                    self.assertEqual(observed["skip_compile"], not compile_frontend)
                    self.assertEqual(observed["mode"], "prod")
                    self.assertEqual(Path(observed["states"]), Path(directory) / ".states")
                    self.assertIsNone(observed["dotenv_loaded"])


if __name__ == "__main__":
    unittest.main()
