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
import importlib.metadata
import json
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
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from docs_site._internal.build import build_site
from docs_site._internal.local_playground_runtime import (
    CORE_WHEEL_ENV,
    build_local_playground_runtime,
    playground_core_wheel_from_environment,
)
from docs_site._internal.pipeline import render_page
from docs_site._internal.static_deps import StaticSiteRequestHandler

if TYPE_CHECKING:
    from collections.abc import Iterator


# The release docs workflow sets this after it pins the release it just
# published, when this checkout and the pinned wheels hold the same Citry.
PINS_MATCH_CHECKOUT_ENV = "CITRY_PLAYGROUND_PINS_MATCH_CHECKOUT"

# Shown for every skipped test, so a skipped run says which variable brings
# the test back rather than reading as a pass.
WORKSPACE_CITRY_SKIP_REASON = (
    "This test runs this checkout's example code or Citry UI in the browser playground, but the "
    "playground installs the published release pinned in docs_site/static/playground/runtime.json, "
    f"which may not support it until the next release. Set {CORE_WHEEL_ENV} to a Pyodide build of this "
    "checkout's Citry Core to run it against this checkout's Citry (see docs_site/static/playground/README.md)."
)


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: browser end-to-end test (needs Playwright and a browser binary)")
    config.addinivalue_line(
        "markers",
        "workspace_citry: playground test that needs this checkout's Citry, so it is skipped with a reason "
        f"unless {CORE_WHEEL_ENV} or {PINS_MATCH_CHECKOUT_ENV} is set",
    )


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip, with a visible reason, the playground tests the pinned runtime cannot run."""
    # With the workspace wheels swapped in, or with pins that match this
    # checkout, the page runs the Citry these tests describe.
    if os.environ.get(CORE_WHEEL_ENV, "").strip() or os.environ.get(PINS_MATCH_CHECKOUT_ENV, "").strip():
        return
    skip = pytest.mark.skip(reason=WORKSPACE_CITRY_SKIP_REASON)
    for item in items:
        if item.get_closest_marker("workspace_citry") is not None:
            item.add_marker(skip)


# The deployed host sends CORS headers, which sandboxed UI previews need.
class _QuietHandler(StaticSiteRequestHandler):
    def log_message(self, *args: Any) -> None:  # keep test output quiet
        pass


def _install_workspace_playground_runtime(site: Path, scratch: Path) -> None:
    """Point the built site's playground at this checkout's wheels when a developer asks for it."""
    core_wheel = playground_core_wheel_from_environment()
    # Without a Pyodide build of the workspace Citry Core, the site keeps the
    # committed runtime, which is what CI and the deployed docs run.
    if core_wheel is None:
        return
    # Reuse the authoring server's builder so the static site and the local
    # server assemble the same runtime.json and wheel set.
    runtime = build_local_playground_runtime(
        repo_root=Path(__file__).resolve().parents[3],
        output_dir=scratch,
        core_wheel=core_wheel,
    )
    playground = site / "static" / "playground"
    shutil.copyfile(runtime.manifest_path, playground / "runtime.json")
    # The manifest refers to "./local/<wheel>", resolved next to worker.js.
    shutil.copytree(runtime.directory / "local", playground / "local", dirs_exist_ok=True)


@pytest.fixture(scope="session")
def docs_site_url() -> Iterator[str]:
    """Build the static docs site once, serve it, and yield its base URL."""
    tmp = Path(tempfile.mkdtemp(prefix="citry-docs-e2e-"))
    site = tmp / "site"
    # Social cards off (they need a browser and are unit-tested elsewhere); search
    # and minify stay on so the served site matches the deployed artifact.
    build_site(output_dir=site, social_cards=False)
    _install_workspace_playground_runtime(site, tmp / "playground-runtime")
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
    # The page is written with its assets, so drop the generated class from the
    # shared Citry instance; unit tests in this process run the same source.
    default_citry.unregister(tabs_namespace["LandingComposition"])

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
def playground_runtime(docs_site_url: str) -> dict[str, Any]:
    """Return the runtime.json the built site serves, committed or workspace."""
    # Tests compare version labels against this rather than the committed
    # file, because CITRY_PLAYGROUND_CORE_WHEEL swaps in workspace versions.
    with urllib.request.urlopen(f"{docs_site_url}/static/playground/runtime.json", timeout=5) as response:  # noqa: S310
        served = json.loads(response.read())
    # Prove the site serves the runtime the developer selected, so a test
    # named for the published runtime cannot quietly run workspace wheels,
    # and a workspace run cannot quietly fall back to the published ones.
    if playground_core_wheel_from_environment() is None:
        committed = Path(__file__).resolve().parents[2] / "static" / "playground" / "runtime.json"
        assert served == json.loads(committed.read_text(encoding="utf-8"))
    else:
        assert served["citry"]["version"] == importlib.metadata.version("citry")
        assert served["citry"]["ui_version"] == importlib.metadata.version("citry-ui")
    return served


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


def _stop_process(process: subprocess.Popen[str]) -> str:
    """Stop a fixture server and return its captured startup output for the failure message."""
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    return process.stdout.read() if process.stdout else ""


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

    # These tests specifically exercise the workspace wheel. The committed
    # runtime also includes Citry UI now, so identify the local wheel by URL
    # rather than by the shared ui_version field.
    local_ui_version = None
    try:
        with urllib.request.urlopen(f"{url}/static/playground/runtime.json", timeout=5) as response:  # noqa: S310
            runtime = json.loads(response.read())
        if isinstance(runtime, dict) and isinstance(runtime.get("packages"), list):
            for package in runtime["packages"]:
                if (
                    isinstance(package, dict)
                    and package.get("name") == "citry-ui"
                    and str(package.get("url", "")).startswith("./local/")
                ):
                    local_ui_version = package.get("version")
    except (OSError, ValueError) as error:
        output = _stop_process(process)
        pytest.fail(f"Local docs server did not serve a playground runtime: {error}\n{output}")
    if not local_ui_version:
        output = _stop_process(process)
        pytest.fail(
            "Local docs server is serving the committed playground runtime without the workspace "
            "Citry UI wheel. Its startup output below reports why the local wheel was rejected.\n" + output
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
