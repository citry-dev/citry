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
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from scripts.verify_playground_release import PlaygroundReleaseError, validate_published_runtime

from docs_site._internal.build import build_site
from docs_site._internal.pipeline import render_page
from docs_site._internal.static_server import StaticSiteHandler

if TYPE_CHECKING:
    from collections.abc import Iterator


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: browser end-to-end test (needs Playwright and a browser binary)")


class _QuietHandler(StaticSiteHandler):
    def log_message(self, *args: Any) -> None:  # keep test output quiet
        pass


def _stop_process(process: subprocess.Popen[str]) -> str:
    """Stop a fixture server and return its captured startup diagnostics."""
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    return process.stdout.read() if process.stdout else ""


def _unique_runtime_packages(packages: object, *, label: str) -> dict[str, dict[str, Any]]:
    """Return runtime packages by normalized name, rejecting hidden duplicates."""
    if not isinstance(packages, list):
        pytest.fail(f"{label} has no package list.")
    found: dict[str, dict[str, Any]] = {}
    for package in packages:
        if (
            not isinstance(package, dict)
            or not isinstance(package.get("name"), str)
            or not package["name"]
            or not isinstance(package.get("version"), str)
            or not package["version"]
        ):
            pytest.fail(f"{label} contains a package without a name and version.")
        name = re.sub(r"[-_.]+", "-", package["name"]).casefold()
        if name in found:
            pytest.fail(f"{label} contains duplicate package entries for {name!r}.")
        found[name] = package
    return found


def _assert_published_runtime(site: Path) -> None:
    """Ensure the static fixture still exercises the committed runtime tuple."""
    runtime_path = site / "static" / "playground" / "runtime.json"
    try:
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        pytest.fail(f"Static docs site has no readable playground runtime: {error}")
    if not isinstance(runtime, dict) or runtime.get("source") != "published":
        pytest.fail("Static docs E2E must serve runtime.json with source: 'published'.")
    try:
        validate_published_runtime(runtime)
    except PlaygroundReleaseError as error:
        pytest.fail(f"Static docs E2E runtime is not a valid published runtime: {error}")
    required = {"citry-core", "citry", "citry-ui"}
    found = _unique_runtime_packages(runtime["packages"], label="Static docs E2E runtime")
    missing = sorted(required - found.keys())
    if missing:
        pytest.fail("Static docs E2E runtime is missing published packages: " + ", ".join(missing))
    mixed = sorted(name for name in required if found[name].get("source") != "pypi")
    if mixed:
        pytest.fail("Static docs E2E runtime mixes in non-published packages: " + ", ".join(mixed))


@pytest.fixture(scope="session")
def docs_site_url() -> Iterator[str]:
    """Build the static docs site once, serve it, and yield its base URL."""
    tmp = Path(tempfile.mkdtemp(prefix="citry-docs-e2e-"))
    site = tmp / "site"
    # Social cards off (they need a browser and are unit-tested elsewhere); search
    # and minify stay on so the served site matches the deployed artifact.
    build_site(output_dir=site, social_cards=False)
    _assert_published_runtime(site)
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

    from citry import Component, Slot
    from citry import citry as default_citry
    from citry.citry_render import CitryRender
    from docs_site._internal.components.landing_composer import (
        _RECIPES,
        _initial_state,
        _instantiate,
        _serialize_source,
    )
    from docs_site._internal.static_deps import export_prepared_page_assets

    tabs_state = _initial_state()
    tabs_state["root"]["slots"]["default"] = []
    tabs_recipe = next(recipe for recipe in _RECIPES if recipe["id"] == "tabs")
    tabs_node, tabs_state["nextId"] = _instantiate(tabs_recipe["node"], start=tabs_state["nextId"])
    tabs_state["root"]["slots"]["default"].append(tabs_node)
    tabs_source = _serialize_source(tabs_state).replace(
        "            Overview",
        '            <span v-text="label">fallback tab</span>',
    )
    tabs_source = tabs_source.replace(
        "                Components can be nested inside each panel.",
        '                <b v-text="detail">fallback panel</b>',
    )
    tabs_source = tabs_source.replace(
        "\n\npreview = LandingComposition()",
        "\n\n    def js_data(self, kwargs, slots):\n"
        "        return {'label': 'Lexical tab', 'detail': 'Lexical panel'}\n\n"
        "preview = LandingComposition()",
    )
    tabs_namespace: dict[str, object] = {}
    exec(compile(tabs_source, "<tabs-lexical>", "exec"), tabs_namespace)  # noqa: S102
    tabs_lexical = str(tabs_namespace["preview"])
    tabs_lexical_path = site / "__tests__" / "tabs-lexical" / "index.html"
    tabs_lexical_path.parent.mkdir(parents=True)
    export_prepared_page_assets(tabs_lexical, site, default_citry)
    tabs_lexical_path.write_text(tabs_lexical, encoding="utf-8")

    declarations: list[Slot] = []

    class DeferredRunDeclaration(Component):
        template = """
          <c-slot />
        """

        def template_data(self, kwargs, slots):
            declarations.append(slots["default"])
            return {}

        def on_render(self):
            result, error = yield
            if error is not None:
                raise error
            return CitryRender(parts=[], context=result.context)

    class DeferredRunReceiver(Component):
        template = """
          <section class="deferred-run-receiver">{{ content }}</section>
        """

        def template_data(self, kwargs, slots):
            declaration = declarations[{"a": 0, "b": 1}[kwargs["key"]]]
            return {"content": Slot(lambda _: declaration())}

    class DeferredRunRoot(Component):
        template = """
          <c-DeferredRunDeclaration><b v-text="label">first</b></c-DeferredRunDeclaration>
          <c-DeferredRunDeclaration><i v-text="label">second</i></c-DeferredRunDeclaration>
          <c-for each="key in keys">
            <c-DeferredRunReceiver #c-key="key" c-key="key" />
          </c-for>
        """

        def template_data(self, kwargs, slots):
            return {"keys": ["a", "b"]}

        def js_data(self, kwargs, slots):
            return {"label": "lexical"}

    deferred_run = str(DeferredRunRoot())
    deferred_run_path = site / "__tests__" / "deferred-run" / "index.html"
    deferred_run_path.parent.mkdir(parents=True)
    export_prepared_page_assets(deferred_run, site, default_citry)
    deferred_run_path.write_text(deferred_run, encoding="utf-8")

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
    threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.01},
        daemon=True,
    ).start()
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
    threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.01},
        daemon=True,
    ).start()
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
        output = _stop_process(process)
        pytest.fail(f"Local docs server did not start within 30 seconds:\n{output}")

    # These tests specifically exercise the complete workspace tuple. A
    # published fallback is useful for ordinary authoring, but must never be
    # mistaken for this fixture's workspace coverage.
    try:
        with urllib.request.urlopen(f"{url}/static/playground/runtime.json", timeout=5) as response:  # noqa: S310
            runtime = json.loads(response.read())
    except (OSError, ValueError) as error:
        output = _stop_process(process)
        pytest.fail(f"Local docs server did not serve a playground runtime: {error}")
    if not isinstance(runtime, dict) or runtime.get("source") != "workspace":
        output = _stop_process(process)
        pytest.fail(
            "Local docs server is serving the published runtime instead of the workspace tuple.\n"
            + output
        )
    workspace_packages = _unique_runtime_packages(runtime.get("packages"), label="Local docs server workspace runtime")
    missing = sorted({"citry-core", "citry", "citry-ui"} - workspace_packages.keys())
    local_missing = sorted(
        name
        for name in ("citry-core", "citry", "citry-ui")
        if workspace_packages.get(name, {}).get("source") != "url"
        or not str(workspace_packages.get(name, {}).get("url", "")).startswith("./local/")
    )
    if missing or local_missing:
        output = _stop_process(process)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if local_missing:
            details.append("not local: " + ", ".join(local_missing))
        pytest.fail(
            "Local docs server did not provide a complete workspace tuple ("
            + "; ".join(details)
            + ").\n"
            + output
        )

    try:
        yield url
    finally:
        _stop_process(process)


@pytest.fixture(scope="session")
def getting_started_app_url() -> Iterator[str]:
    """Run the finished FastAPI tutorial app through a real ASGI server."""
    repo_dir = Path(__file__).resolve().parents[3]
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
            "docs_site.tests.e2e.getting_started_app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=repo_dir,
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
