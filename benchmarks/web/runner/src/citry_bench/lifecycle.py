"""Start production application processes and clean up only those we own."""

import os
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from citry_bench.config import CACHE, adapter
from citry_bench.prepare import environment


@contextmanager
def application(directory: Path, log: Path):
    declaration = adapter(directory)
    # The nonce identifies our server if another process takes the candidate port.
    with socket.socket() as listener:
        # Sequential runs can reuse a port whose previous connections are closing.
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", declaration.get("port", 0)))
        port = listener.getsockname()[1]
    substitutions = {
        "python": str(directory / ".venv/bin/python"),
        "node": str(directory / declaration["node"]) if "node" in declaration else "",
        "port": port,
    }
    command = [part.format(**substitutions) for part in declaration["launch"]]
    log.parent.mkdir(parents=True, exist_ok=True)
    nonce = uuid4().hex
    (CACHE / "runtime").mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="app-", dir=CACHE / "runtime") as runtime, log.open("w") as output:
        env = {**environment(), "CITRY_BENCH_SERVER_NONCE": nonce, "CITRY_BENCH_RUNTIME_DIR": runtime}
        child = subprocess.Popen(
            command, cwd=directory, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True
        )
        base = f"http://127.0.0.1:{port}"
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if child.poll() is not None:
                    raise RuntimeError(f"Server exited with {child.returncode}; inspect {log}")
                try:
                    with urllib.request.urlopen(base + declaration["health"], timeout=0.5) as response:
                        if response.status == 200 and response.read().decode() == nonce:
                            break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(0.05)
            else:
                raise TimeoutError(f"Server health deadline exceeded; inspect {log}")
            yield {"url": base, "pid": child.pid, "command": command, "adapter": declaration}
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=5)
