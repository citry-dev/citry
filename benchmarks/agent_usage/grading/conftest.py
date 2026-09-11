# ruff: noqa: S101
"""Run submitted apps and inspect their public HTML in the grading container."""

import os
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import Browser, Page, sync_playwright


@pytest.fixture(scope="session", autouse=True)
def submission_import_path() -> Iterator[None]:
    # Collection imports the trusted grader dependencies before exposing app files.
    workspace = str(Path(os.environ.get("SUBMISSION_DIR", "/workspace")))
    sys.path.insert(0, workspace)
    yield
    sys.path.remove(workspace)


@pytest.fixture(scope="session")
def server_url() -> Iterator[str]:
    workspace = Path(os.environ.get("SUBMISSION_DIR", "/workspace"))
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    # Keep app output out of the score stream while retaining startup failures.
    with tempfile.TemporaryFile(mode="w+") as output:
        process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-m",
                "uvicorn",
                "app:app",
                "--app-dir",
                str(workspace),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=workspace,
            stdout=output,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 20
            with httpx.Client(trust_env=False, timeout=1) as client:
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        break
                    try:
                        if client.get(url).status_code == 200:
                            yield url
                            return
                    except httpx.TransportError:
                        pass
                    time.sleep(0.1)
            output.seek(0)
            pytest.fail(f"Application did not serve GET / within 20 seconds:\n{output.read()[-8000:]}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser, server_url: str) -> Iterator[Page]:
    context = browser.new_context()
    # Browser traffic has the same offline constraint as the grading container.
    context.route(
        "**/*", lambda route: route.continue_() if route.request.url.startswith(server_url + "/") else route.abort()
    )
    errors: list[str] = []
    # Isolation checks open several pages; every page contributes runtime errors.
    context.on("page", lambda opened: opened.on("pageerror", lambda error: errors.append(str(error))))
    page = context.new_page()
    page.set_default_timeout(5000)
    page.goto(server_url, wait_until="networkidle")
    yield page
    context.close()
    assert not errors, f"Uncaught browser errors: {errors}"
