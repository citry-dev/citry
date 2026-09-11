"""Regression tests that drive hot reload through real development servers."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import textwrap
import time
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path
    from typing import BinaryIO

_RELOAD_TIMEOUT = 10.0
_RELOADER_BASELINE_DELAY = 0.6


@dataclass(frozen=True)
class _Response:
    status: int
    body: str
    pid: int | None


class _SourceEditor:
    """Write each edit with a later whole-second mtime so Python rejects stale bytecode."""

    def __init__(self, paths: tuple[Path, ...], staging_dir: Path) -> None:
        latest_mtime = max(path.stat().st_mtime for path in paths)
        self._mtime = max(int(latest_mtime), int(time.time())) + 1
        self._staging_file = staging_dir / ".citry-reload-edit"

    def write(self, path: Path, source: str) -> None:
        # Stage outside the watched root so a scan can observe only the old or
        # complete new source, never a partially written Python module.
        self._staging_file.write_text(source, encoding="utf-8")
        self._mtime += 1
        os.utime(self._staging_file, (self._mtime, self._mtime))
        self._staging_file.replace(path)


class _ServerProcess:
    def __init__(
        self,
        process: subprocess.Popen[bytes],
        base_url: str,
        log_file: Path,
        log_handle: BinaryIO,
    ) -> None:
        self.process = process
        self.base_url = base_url
        self.log_file = log_file
        self._log_handle = log_handle

    def logs(self) -> str:
        self._log_handle.flush()
        return self.log_file.read_text(encoding="utf-8", errors="replace")

    def stop(self) -> None:
        # The reloader supervisor owns worker descendants, so terminate its
        # complete process tree even when a worker is between restarts.
        if sys.platform == "win32":
            with suppress(subprocess.TimeoutExpired):
                subprocess.run(
                    ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],  # noqa: S607
                    check=False,
                    capture_output=True,
                    timeout=3,
                )
        else:
            with suppress(ProcessLookupError):
                os.killpg(self.process.pid, signal.SIGTERM)

        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            if sys.platform != "win32":
                with suppress(ProcessLookupError):
                    os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=3)
        finally:
            self._log_handle.close()


def _component_source(message: str, *, raises: bool = False) -> str:
    statement = f'raise ValueError("{message}")' if raises else f'return {{"message": "{message}"}}'
    return textwrap.dedent(
        f"""\
        from pathlib import Path

        from citry import Citry, Component

        BASE_DIR = Path(__file__).resolve().parent
        engine = Citry(dirs=[BASE_DIR])


        class Page(Component):
            citry = engine

            def template_data(self, kwargs, slots):
                {statement}

            template_file = "page.html"
        """,
    )


def _django_app_source() -> str:
    return textwrap.dedent(
        """\
        import os
        from pathlib import Path

        from django.http import HttpResponse
        from django.urls import path
        from django.utils import autoreload

        from citry.contrib.django import enable_hot_reload
        from component import Page, engine

        BASE_DIR = Path(__file__).resolve().parent
        SECRET_KEY = "test-only-key"
        DEBUG = False
        ALLOWED_HOSTS = ["127.0.0.1"]
        ROOT_URLCONF = __name__
        INSTALLED_APPS = []
        MIDDLEWARE = []
        TEMPLATES = [
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [BASE_DIR],
                "APP_DIRS": True,
                "OPTIONS": {},
            },
        ]

        # Keep the test independent of optional Watchman installations and
        # shorten Django's default one-second polling interval so the test stays fast.
        autoreload.get_reloader = autoreload.StatReloader
        autoreload.StatReloader.SLEEP_TIME = 0.05

        engine.initialize()
        enable_hot_reload(engine)


        def page(_request):
            headers = {"X-Serving-PID": str(os.getpid())}
            try:
                body = Page().render().serialize(deps_strategy="ignore")
            except ValueError as exc:
                return HttpResponse(f"render-error: {exc}", status=500, headers=headers)
            return HttpResponse(body, headers=headers)


        urlpatterns = [path("", page)]
        """,
    )


def _uvicorn_app_source() -> str:
    return textwrap.dedent(
        """\
        import os
        from contextlib import asynccontextmanager
        from pathlib import Path

        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse

        from citry.contrib.asgi import reload_lifespan
        from citry.reload import PollingWatcher
        from component import Page, engine

        BASE_DIR = Path(__file__).resolve().parent
        watch_lifespan = reload_lifespan(
            engine,
            roots=[BASE_DIR],
            watcher=PollingWatcher(interval=0.05),
        )


        @asynccontextmanager
        async def lifespan(app):
            engine.initialize()
            async with watch_lifespan(app):
                yield


        app = FastAPI(lifespan=lifespan)


        @app.get("/")
        async def page():
            headers = {"X-Serving-PID": str(os.getpid())}
            try:
                body = Page().render().serialize(deps_strategy="ignore")
            except ValueError as exc:
                return HTMLResponse(f"render-error: {exc}", status_code=500, headers=headers)
            return HTMLResponse(body, headers=headers)
        """,
    )


def _unused_loopback_port() -> int:
    # Ask the kernel for an unused loopback port, then start the server promptly
    # to keep the reuse window short.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@contextmanager
def _development_server(host: str, app_root: Path, log_file: Path) -> Iterator[_ServerProcess]:
    port = _unused_loopback_port()
    environment = os.environ.copy()
    if host == "django":
        pytest.importorskip("django", reason="the Django reload regression needs Django")
        environment["DJANGO_SETTINGS_MODULE"] = "server_app"
        # Keep requests on the server thread so this reload test does not depend
        # on per-request thread scheduling. The real WSGI handler and autoreloader
        # supervisor still run, including worker restarts.
        command = [
            sys.executable,
            "-m",
            "django",
            "runserver",
            f"127.0.0.1:{port}",
            "--skip-checks",
            "--nothreading",
        ]
    else:
        pytest.importorskip("fastapi", reason="the Uvicorn reload regression needs FastAPI")
        pytest.importorskip("uvicorn", reason="the Uvicorn reload regression needs Uvicorn")
        command = [
            sys.executable,
            "-m",
            "uvicorn",
            "server_app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--reload",
            "--reload-dir",
            str(app_root),
            "--reload-delay",
            "0.05",
        ]

    log_handle = log_file.open("wb")
    try:
        if sys.platform == "win32":
            process = subprocess.Popen(
                command,
                cwd=app_root,
                env=environment,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            process = subprocess.Popen(
                command,
                cwd=app_root,
                env=environment,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except BaseException:
        log_handle.close()
        raise
    server = _ServerProcess(process, f"http://127.0.0.1:{port}", log_file, log_handle)
    try:
        yield server
    finally:
        server.stop()


def _request(base_url: str, *, timeout: float) -> _Response:
    opener = build_opener(ProxyHandler({}))
    try:
        response = opener.open(base_url, timeout=timeout)
    except HTTPError as exc:
        response = exc
    with response:
        pid_header = response.headers.get("X-Serving-PID")
        return _Response(
            status=response.status,
            body=response.read().decode("utf-8", errors="replace"),
            pid=int(pid_header) if pid_header is not None else None,
        )


def _wait_for_response(
    server: _ServerProcess,
    predicate: Callable[[_Response], bool],
    description: str,
) -> _Response:
    deadline = time.monotonic() + _RELOAD_TIMEOUT
    last_observation = "no response"
    while (remaining := deadline - time.monotonic()) > 0:
        if server.process.poll() is not None:
            break
        try:
            # A server that has accepted the request may still be completing
            # its first render. Give that request the remaining operation
            # budget so polling cannot pile concurrent renders onto it.
            response = _request(server.base_url, timeout=remaining)
        except (ConnectionError, OSError, URLError) as exc:
            last_observation = f"{type(exc).__name__}: {exc}"
        else:
            last_observation = repr(response)
            if predicate(response):
                return response
        time.sleep(0.05)
    msg = f"Timed out waiting for {description}; last observation: {last_observation}\nServer log:\n{server.logs()}"
    raise AssertionError(msg)


def test_response_wait_uses_the_remaining_deadline_after_a_refused_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = _Response(status=200, body="ready", pid=123)
    process = MagicMock()
    process.poll.return_value = None
    server = _ServerProcess(process, "http://127.0.0.1:8000", MagicMock(), MagicMock())
    clock = [100.0]
    timeouts: list[float] = []

    def request(base_url: str, *, timeout: float) -> _Response:
        assert base_url == server.base_url
        timeouts.append(timeout)
        if len(timeouts) == 1:
            raise URLError(ConnectionRefusedError())
        return expected

    monkeypatch.setattr(sys.modules[__name__], "_request", request)
    monkeypatch.setattr(time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(time, "sleep", lambda _delay: clock.__setitem__(0, clock[0] + 2))

    assert _wait_for_response(server, lambda response: response == expected, "readiness") is expected
    assert timeouts == pytest.approx([_RELOAD_TIMEOUT, _RELOAD_TIMEOUT - 2])
    assert process.poll.call_count == 2


@pytest.mark.parametrize("host", ["django", "uvicorn"])
def test_development_server_hot_reloads_assets_and_restarts_python(host: str, tmp_path: Path) -> None:
    app_root = tmp_path / "app"
    app_root.mkdir()
    template_file = app_root / "page.html"
    component_file = app_root / "component.py"
    server_file = app_root / "server_app.py"
    template_file.write_text("<main>template-v1: {{ message }}</main>", encoding="utf-8")
    component_file.write_text(_component_source("python-v1"), encoding="utf-8")
    app_source = _django_app_source() if host == "django" else _uvicorn_app_source()
    server_file.write_text(app_source, encoding="utf-8")
    editor = _SourceEditor((template_file, component_file, server_file), tmp_path)

    with _development_server(host, app_root, tmp_path / f"{host}.log") as server:
        initial = _wait_for_response(
            server,
            lambda response: (
                response.status == 200 and response.pid is not None and "template-v1: python-v1" in response.body
            ),
            "the initial page",
        )
        # HTTP readiness loads the template. This short bound gives both the
        # host reloader and Citry's poller time to record their first snapshot.
        time.sleep(_RELOADER_BASELINE_DELAY)

        editor.write(template_file, "<main>template-v2: {{ message }}</main>")
        hot = _wait_for_response(
            server,
            lambda response: (
                response.status == 200 and response.pid == initial.pid and "template-v2: python-v1" in response.body
            ),
            "the hot-reloaded template in the original worker",
        )
        assert hot.pid == initial.pid

        editor.write(component_file, _component_source("broken-v2", raises=True))
        broken = _wait_for_response(
            server,
            lambda response: (
                response.status == 500
                and response.pid is not None
                and response.pid != initial.pid
                and "render-error:" in response.body
                and "broken-v2" in response.body
            ),
            "the Python failure from a restarted worker",
        )
        # Django's restarted child creates a new StatReloader, while Uvicorn's
        # polling fallback clears its mtimes, so let either rebuild its baseline.
        time.sleep(_RELOADER_BASELINE_DELAY)

        editor.write(component_file, _component_source("python-v3"))
        fixed = _wait_for_response(
            server,
            lambda response: (
                response.status == 200
                and response.pid is not None
                and response.pid not in {initial.pid, broken.pid}
                and "template-v2: python-v3" in response.body
            ),
            "the fixed component from another restarted worker",
        )
        assert fixed.pid not in {initial.pid, broken.pid}
