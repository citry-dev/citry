"""
Harness for the docs-site browser e2e tests.

Builds the real static site once (the same artifact a deploy ships: minified,
with the Pagefind search index) and serves it over a background HTTP server that
Playwright can point a real browser at. This is the integration layer the unit
tests miss: it exercises the whole rendered site (chrome, TOC, nav, search,
assets) in a browser, so a dropped markup hook, a broken asset URL, or an empty
table of contents fails a test instead of shipping.

Playwright comes from the optional ``e2e`` dependency group plus the ``docs``
extra; each test module ``importorskip``s it, so the suite is skipped anywhere
Playwright is not installed (the default dev env).
"""

from __future__ import annotations

import functools
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from docs_site._internal.build import build_site
from docs_site._internal.pipeline import render_page

if TYPE_CHECKING:
    from collections.abc import Iterator


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: browser end-to-end test (needs Playwright and a browser binary)")


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:  # keep test output quiet
        pass


@pytest.fixture(scope="session")
def docs_site_url() -> Iterator[str]:
    """Build the static docs site once, serve it, and yield its base URL."""
    tmp = Path(tempfile.mkdtemp(prefix="citry-docs-e2e-"))
    site = tmp / "site"
    # Social cards off (they need a browser and are unit-tested elsewhere); search
    # and minify stay on so the served site matches the deployed artifact.
    build_site(output_dir=site, social_cards=False)
    # A product-neutral fixture proves coordination across multiple authored
    # blocks without adding duplicate examples to the public navigation.
    synthetic = render_page(
        """---
title: Multiple live examples
---

<c-live-code path="docs_site/live_snippets/welcome.py" title="First example" full_height />

<c-live-code path="docs_site/live_snippets/welcome.py" title="Second example" />
""",
        current_path="__tests__/live-code-multiple/",
    ).html
    synthetic_path = site / "__tests__" / "live-code-multiple" / "index.html"
    synthetic_path.parent.mkdir(parents=True)
    synthetic_path.write_text(synthetic, encoding="utf-8")

    incomplete = render_page(
        """---
title: Incomplete live example
---

<c-live-code path="docs_site/tests/fixtures/live_code_incomplete.py" title="Incomplete card" />
""",
        current_path="__tests__/live-code-incomplete/",
    ).html
    incomplete_path = site / "__tests__" / "live-code-incomplete" / "index.html"
    incomplete_path.parent.mkdir(parents=True)
    incomplete_path.write_text(incomplete, encoding="utf-8")

    toc_history = render_page(
        """---
title: TOC history fixture
---

# TOC history fixture

## First target

<div style="height: 50rem"></div>

## Second target

### Third target
""",
        current_path="__tests__/toc-history/",
    ).html
    toc_history_path = site / "__tests__" / "toc-history" / "index.html"
    toc_history_path.parent.mkdir(parents=True)
    toc_history_path.write_text(toc_history, encoding="utf-8")

    handler = functools.partial(_QuietHandler, directory=str(site))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="session")
def workspace_static_url() -> Iterator[str]:
    """Serve the workspace so focused browser tests can load source static assets."""
    workspace = Path(__file__).resolve().parents[3]
    handler = functools.partial(_QuietHandler, directory=str(workspace))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()


@pytest.fixture(scope="session")
def local_docs_site_url() -> Iterator[str]:
    """Run the local-wheel authoring server for Citry UI browser coverage."""
    workspace = Path(__file__).resolve().parents[3]
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "docs_site._internal.serve:create_local_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            pytest.fail(f"Local docs server exited during startup:\n{output}")
        try:
            with urllib.request.urlopen(f"{url}/playground/", timeout=0.5) as response:  # noqa: S310
                if response.status == 200:
                    break
        except OSError:
            time.sleep(0.05)
    else:
        process.terminate()
        pytest.fail("Local docs server did not start within 30 seconds")

    try:
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture(scope="session")
def getting_started_app_url() -> Iterator[str]:
    """Run the finished FastAPI tutorial app through a real ASGI server."""
    app_dir = Path(__file__).resolve().parents[2] / "snippets" / "getting_started"
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    env = os.environ.copy()
    env["CITRY_SECRET"] = secrets.token_urlsafe(32)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=app_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            pytest.fail(f"Getting started app exited during startup:\n{output}")
        try:
            with urllib.request.urlopen(f"{url}/", timeout=0.5) as response:  # noqa: S310
                if response.status == 200:
                    break
        except OSError:
            time.sleep(0.05)
    else:
        process.terminate()
        pytest.fail("Getting started app did not start within 15 seconds")

    try:
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
