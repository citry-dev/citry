from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import importlib.metadata
import json
import platform
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar
from http import HTTPStatus
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from playwright.sync_api import sync_playwright

from citry import Citry, Component
from citry.contrib.wsgi import wsgi_app

if TYPE_CHECKING:
    from collections.abc import Iterator


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CANDIDATE = HERE / "browser" / "candidate.js"
PROBE = HERE / "browser" / "probe.js"
CLIENT_RUNTIME = REPO / "packages/py/citry/citry/ext/dependencies/client/citry.js"
PROVIDE_SOURCE = REPO / "packages/py/citry/citry/provide.py"
PROVIDE_COMPONENT = REPO / "packages/py/citry/citry/components/provide.py"
AMBIENT_TESTS = REPO / "packages/py/citry/tests/e2e/test_alpine_ambient_context_e2e.py"
BROWSER_NAMES = ("chromium", "firefox", "webkit")
SIGNING_KEY = "i18n-provider-phase0"
SERVER_BINDING: ContextVar[dict[str, str] | None] = ContextVar("citry_i18n_phase0_binding", default=None)

CONTEXTS = {
    "ar-EG": {"direction": "rtl", "locale": "ar-EG", "timeZone": "UTC"},
    "cs-CZ": {"direction": "ltr", "locale": "cs-CZ", "timeZone": "UTC"},
    "en-US": {"direction": "ltr", "locale": "en-US", "timeZone": "UTC"},
    "ja-JP": {"direction": "ltr", "locale": "ja-JP", "timeZone": "UTC"},
    "pl-PL": {"direction": "ltr", "locale": "pl-PL", "timeZone": "UTC"},
}
CATALOGS = {
    "ar-EG": {"label": "مرحبا"},
    "cs-CZ": {"label": "Ahoj"},
    "en-US": {"label": "Hello"},
    "ja-JP": {"label": "こんにちは"},
    "pl-PL": {"label": "Cześć"},
}
MANIFEST = {
    "aliases": {locale: locale for locale in CONTEXTS},
    "catalogs": CATALOGS,
    "clientMessages": ["label"],
    "contexts": CONTEXTS,
    "revision": "7" * 64,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_always_on_checks() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    require(
        not [node for node in ast.walk(tree) if isinstance(node, ast.Assert)],
        "the evidence harness must not use optimization-sensitive assert statements",
    )
    for script in (CANDIDATE, PROBE):
        require("console.assert" not in script.read_text(encoding="utf-8"), f"{script.name} uses console.assert")


@contextmanager
def bind_request(locale: str, time_zone: str) -> Iterator[None]:
    token = SERVER_BINDING.set({"locale": locale, "time_zone": time_zone})
    try:
        yield
    finally:
        SERVER_BINDING.reset(token)


def run_server_binding_checks() -> dict[str, bool]:
    def one_thread(index: int) -> tuple[str, str]:
        locale = f"x-thread-{index}"
        zone = f"Etc/GMT+{index % 12}"
        with bind_request(locale, zone):
            threading.Event().wait(0.001)
            current = SERVER_BINDING.get()
            require(current is not None, "a thread lost its request binding")
            return current["locale"], current["time_zone"]

    with ThreadPoolExecutor(max_workers=8) as executor:
        threaded = list(executor.map(one_thread, range(24)))
    expected_threads = [(f"x-thread-{index}", f"Etc/GMT+{index % 12}") for index in range(24)]
    require(threaded == expected_threads, "thread binding leaked")

    async def one_task(index: int) -> str:
        with bind_request(f"x-task-{index}", "UTC"):
            await asyncio.sleep(0)
            current = SERVER_BINDING.get()
            require(current is not None, "an async task lost its request binding")
            return current["locale"]

    async def task_matrix() -> list[str]:
        return list(await asyncio.gather(*(one_task(index) for index in range(24))))

    task_values = asyncio.run(task_matrix())
    require(task_values == [f"x-task-{index}" for index in range(24)], "async binding leaked")
    try:
        with bind_request("x-error", "UTC"):
            raise LookupError("expected")
    except LookupError:
        pass
    require(SERVER_BINDING.get() is None, "an exception did not restore the prior request binding")
    return {
        "async_tasks_isolated": True,
        "exception_restored_binding": True,
        "threads_isolated": True,
    }


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass


@contextmanager
def serve_page(citry: Citry, html: str) -> Iterator[str]:
    citry.set_mounted_prefix("/citry")
    citry_wsgi = wsgi_app(citry)
    body = html.encode()

    def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
        path = environ.get("PATH_INFO", "")
        if path == "/citry" or path.startswith("/citry/"):
            sub = dict(environ)
            sub["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + "/citry"
            sub["PATH_INFO"] = path[len("/citry") :]
            return list(citry_wsgi(sub, start_response))
        start_response(
            f"{HTTPStatus.OK.value} {HTTPStatus.OK.phrase}",
            [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))],
        )
        return [body]

    server = make_server(
        "127.0.0.1",
        0,
        app,
        server_class=_ThreadingWSGIServer,
        handler_class=_QuietHandler,
    )
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()


def inherited_policy(*, locale: str | None = None, time_zone: str | None | object = ...) -> dict[str, Any]:
    locale_policy = {"mode": "inherit"} if locale is None else {"mode": "explicit", "value": locale}
    if time_zone is ...:
        time_zone_policy: dict[str, Any] = {"mode": "inherit"}
    elif time_zone is None:
        time_zone_policy = {"mode": "clear"}
    else:
        time_zone_policy = {"mode": "explicit", "value": time_zone}
    return {
        "direction": {"mode": "inherit"},
        "locale": locale_policy,
        "timeZone": time_zone_policy,
    }


def build_fixture(*, benchmark_readers: int = 0) -> tuple[Citry, str, dict[str, bool]]:
    require(benchmark_readers >= 0, "benchmark_readers cannot be negative")
    engine = Citry(secret=SIGNING_KEY)
    engine.set_mounted_prefix("/citry")

    class ClientProvider(Component):
        citry = engine

        def template_data(self, kwargs: Any, _slots: Any) -> dict[str, Any]:
            resolved = kwargs["resolved"]
            self.provide("i18n_server", **resolved)
            return {"direction": resolved["direction"], "locale": resolved["locale"], "name": kwargs["name"]}

        def js_data(self, kwargs: Any, _slots: Any) -> dict[str, Any]:
            return {"name": kwargs["name"], "policy": kwargs["policy"], "resolved": kwargs["resolved"]}

        js = """
          $component((context) => CitryI18nProviderCandidate.mount(context));
        """
        template = """
          <section
            class="client-provider"
            c-data-provider="name"
            c-dir="direction"
            c-lang="locale"
          >
            <c-slot />
          </section>
        """

    class ServerBarrier(Component):
        citry = engine

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, Any]:
            self.unprovide("i18n_server")
            return {}

        template = """
          <section
            class="server-barrier"
            x-init="$unprovide('citry_i18n')"
          >
            <c-slot />
          </section>
        """

    class Reader(Component):
        citry = engine

        def template_data(self, kwargs: Any, _slots: Any) -> dict[str, str]:
            server = self.inject("i18n_server", None)
            return {"name": kwargs["name"], "server_locale": "blocked" if server is None else server.locale}

        def js_data(self, kwargs: Any, _slots: Any) -> dict[str, str]:
            return {"name": kwargs["name"]}

        js = """
          $component(({ data, els, inject }) => {
            const service = inject("citry_i18n", null);
            window.__providerProbe.readers[data.name] = { service };
            if (service === null) {
              els[0].textContent = "blocked";
              return;
            }
            const binding = service.bindMessage("label", els[0]);
            return () => binding.dispose();
          });
        """
        template = """
          <output
            c-data-reader="name"
            c-data-server-locale="server_locale"
          ></output>
        """

    class ServerOnlyProvider(Component):
        citry = engine
        transparent = True

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, Any]:
            self.provide("i18n_server", locale="cs-CZ")
            return {}

        template = """
          <c-slot />
        """

    class ServerOnlyLeaf(Component):
        citry = engine

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, str]:
            return {"locale": self.inject("i18n_server").locale}

        template = """
          <output class="server-only-leaf">{{ locale }}</output>
        """

    class ServerOnlyPage(Component):
        citry = engine
        template = """
          <html><body>
            <c-server-only-provider><c-server-only-leaf /></c-server-only-provider>
          </body></html>
        """

    outer = CONTEXTS["en-US"]
    inherited = {**CONTEXTS["en-US"], "timeZone": "Europe/Prague"}
    explicit = {**CONTEXTS["cs-CZ"], "timeZone": None}
    independent = {**CONTEXTS["ja-JP"], "timeZone": None}
    benchmark_markup = "\n".join(f'<c-reader name="benchmark_reader_{index}" />' for index in range(benchmark_readers))

    class Page(Component):
        citry = engine

        def template_data(self, _kwargs: Any, _slots: Any) -> dict[str, Any]:
            return {
                "explicit": explicit,
                "explicit_policy": inherited_policy(locale="cs-CZ", time_zone=None),
                "independent": independent,
                "independent_policy": inherited_policy(locale="ja-JP", time_zone=None),
                "inherited": inherited,
                "inherited_policy": inherited_policy(time_zone="Europe/Prague"),
                "outer": outer,
                "outer_policy": inherited_policy(locale="en-US", time_zone="UTC"),
            }

        template = f"""
          <html><body>
            <script>
              window.__providerProbe = {{
                corrupt: new Set(), delays: new Map(), failures: new Set(),
                loads: [], readers: {{}}, services: {{}}
              }};
              CitryI18nProviderCandidate.configure({{
                publicServices: window.__providerProbe.services,
                manifest: {json.dumps(MANIFEST, ensure_ascii=False)},
                load(locale, generation) {{
                  window.__providerProbe.loads.push({{ generation, locale }});
                  const delay = window.__providerProbe.delays.get(locale) || 0;
                  return new Promise((resolve, reject) => setTimeout(() => {{
                    if (window.__providerProbe.failures.has(locale)) {{
                      const error = new Error(`failed ${{locale}}`);
                      error.code = "I18N_PROVIDER_CHUNK_FAILED";
                      reject(error);
                      return;
                    }}
                    resolve({{
                      catalogs: {json.dumps(CATALOGS, ensure_ascii=False)}, locale,
                      revision: window.__providerProbe.corrupt.has(locale)
                        ? "0".repeat(64)
                        : {json.dumps(MANIFEST["revision"])}
                    }});
                  }}, delay));
                }}
              }});
            </script>
            <c-client-provider
              name="outer"
              c-policy="outer_policy"
              c-resolved="outer"
            >
              <c-reader name="outer_reader" />
              {benchmark_markup}
              <c-client-provider
                name="inherited"
                c-policy="inherited_policy"
                c-resolved="inherited"
              >
                <c-reader name="inherited_reader" />
              </c-client-provider>
              <c-client-provider
                name="explicit"
                c-policy="explicit_policy"
                c-resolved="explicit"
              >
                <c-reader name="explicit_reader" />
              </c-client-provider>
              <c-server-barrier>
                <c-reader name="blocked_reader" />
                <c-client-provider
                  name="independent"
                  c-policy="independent_policy"
                  c-resolved="independent"
                >
                  <c-reader name="independent_reader" />
                </c-client-provider>
              </c-server-barrier>
            </c-client-provider>
          </body></html>
        """

    server_only_html = str(ServerOnlyPage())
    server_gates = {
        "component_provide_reached_descendant": "cs-CZ" in server_only_html,
        "server_only_provider_has_no_i18n_browser_payload": "citry_i18n" not in server_only_html,
        "server_only_provider_has_no_own_wrapper": "server-only-provider" not in server_only_html,
    }
    require(all(server_gates.values()), f"server-only provider gates failed: {server_gates!r}")
    return engine, str(Page()), server_gates


def run_browser_matrix() -> tuple[dict[str, Any], dict[str, str], dict[str, bool]]:
    engine, document, server_gates = build_fixture()
    candidate = CANDIDATE.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")
    results: dict[str, Any] = {}
    versions: dict[str, str] = {}
    with serve_page(engine, document) as url, sync_playwright() as playwright:
        for name in BROWSER_NAMES:
            browser = getattr(playwright, name).launch(headless=True)
            try:
                versions[name] = browser.version
                page = browser.new_page()
                errors: list[str] = []
                page.on("pageerror", lambda error, target=errors: target.append(str(error)))
                page.add_init_script(script=candidate)
                page.goto(url)
                page.wait_for_function(
                    "Object.keys(window.__providerProbe?.readers || {}).length === 5 "
                    "&& Object.keys(window.__providerProbe?.services || {}).length === 4"
                )
                page.add_script_tag(content=probe)
                results[name] = page.evaluate("CitryI18nProviderProbe.runProviderProbe()")
                require(not errors, f"{name} page errors: {errors!r}")
            finally:
                browser.close()
    canonical = results[BROWSER_NAMES[0]]
    require(all(results[name] == canonical for name in BROWSER_NAMES[1:]), f"browser results differ: {results!r}")
    return results, versions, server_gates


def build_evidence() -> dict[str, Any]:
    ensure_always_on_checks()
    binding_gates = run_server_binding_checks()
    results, versions, server_gates = run_browser_matrix()
    return {
        "artifacts": {
            "ambient_tests": sha256(AMBIENT_TESTS),
            "candidate": sha256(CANDIDATE),
            "client_runtime": sha256(CLIENT_RUNTIME),
            "harness": sha256(Path(__file__)),
            "probe": sha256(PROBE),
            "provide_component": sha256(PROVIDE_COMPONENT),
            "provide_source": sha256(PROVIDE_SOURCE),
            "uv_lock": sha256(REPO / "uv.lock"),
        },
        "browser_results_equal": True,
        "browser_versions": versions,
        "dependencies": {
            "playwright": importlib.metadata.version("playwright"),
            "pytest_playwright": importlib.metadata.version("pytest-playwright"),
        },
        "environment": {
            "machine": platform.machine(),
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "result": "PASS_BOUNDED",
        "semantic_result": results[BROWSER_NAMES[0]],
        "server_binding_gates": binding_gates,
        "server_provider_gates": server_gates,
        "tested_browsers": list(BROWSER_NAMES),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "evidence.json")
    arguments = parser.parse_args()
    evidence = build_evidence()
    arguments.output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    sys.stdout.write(f"PASS_BOUNDED\nevidence={arguments.output}\n")


if __name__ == "__main__":
    main()
