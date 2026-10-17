"""Check that parent settings cannot change the measured ReactPy configuration."""

# Run in fresh interpreters because ReactPy reads these options during import.
# ruff: noqa: PT009
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class ConfigurationTests(unittest.TestCase):
    def test_failed_socket_send_does_not_retain_a_stale_preparation(self) -> None:
        with TemporaryDirectory() as directory:
            code = """
import asyncio
import app
from audit import CONNECTION_SCOPE_KEY, preparations
from reactpy.backend import starlette
from render_timing import current_pending_preparation, pending_preparation, preparation_scope, preparation_span

class Socket:
    scope = {CONNECTION_SCOPE_KEY: "failed-connection"}

    async def send_text(self, _text):
        raise RuntimeError("send failed")

    async def receive_text(self):
        raise AssertionError("receive is not used")

async def check():
    timing = pending_preparation()
    with preparation_scope(timing), preparation_span():
        pass
    send, _receive = starlette._make_send_recv_callbacks(Socket())
    try:
        await send({"type": "layout-update"})
    except RuntimeError as error:
        assert str(error) == "send failed"
    else:
        raise AssertionError("failed send returned")
    assert preparations == {}
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

    def test_parent_options_and_module_directory_are_overridden(self) -> None:
        flags = (
            "REACTPY_DEBUG_MODE",
            "REACTPY_ASYNC_RENDERING",
            "REACTPY_CHECK_VDOM_SPEC",
            "REACTPY_CHECK_JSON_ATTRS",
        )
        with TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime"
            inherited = Path(directory) / "inherited"
            runtime.mkdir()
            inherited.mkdir()
            sentinel = inherited / "board-disclosure.js"
            sentinel.write_text("Parent-owned module")
            environment = {
                **os.environ,
                **dict.fromkeys(flags, "true"),
                "CITRY_BENCH_RUNTIME_DIR": str(runtime),
                "REACTPY_WEB_MODULES_DIR": str(inherited),
            }
            code = f"""
import json
import app
from reactpy import config
directory = config.REACTPY_WEB_MODULES_DIR.current
print(json.dumps({{
    "flags": {{name: getattr(config, name).current for name in {flags!r}}},
    "directory": str(directory),
    "module_matches": (directory / "board-disclosure.js").read_bytes()
        == (app.HERE / "assets/disclosure.js").read_bytes(),
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
            self.assertEqual(observed["flags"], dict.fromkeys(flags, False))
            module_directory = Path(observed["directory"])
            self.assertEqual(module_directory.parent.resolve(), runtime.resolve())
            self.assertTrue(observed["module_matches"])
            self.assertFalse(module_directory.exists())
            self.assertEqual(sentinel.read_text(), "Parent-owned module")


if __name__ == "__main__":
    unittest.main()
