from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import threading
from contextlib import contextmanager
from http import HTTPStatus
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from playwright.sync_api import sync_playwright

from citry import Citry, Component
from citry.citry_render import PhysicalRegionPart, PhysicalRegionRender
from citry.contrib.wsgi import wsgi_app

if TYPE_CHECKING:
    from collections.abc import Iterator


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CANDIDATE = HERE / "browser" / "candidate.js"
PROBE = HERE / "browser" / "probe.js"
CLIENT_RUNTIME = REPO / "packages/py/citry/citry/ext/dependencies/client/citry.js"
OWNERSHIP_SOURCE = REPO / "packages/py/citry/citry/ownership.py"
COMPONENT_RENDER_SOURCE = REPO / "packages/py/citry/citry/component_render.py"
GRAPH_SPEC = REPO / "packages/protocol/client_graph/v1/spec.md"
ROOT_SHAPES_TEST = REPO / "packages/py/citry/tests/e2e/test_alpine_root_shapes_e2e.py"
SLOT_SCOPE_TEST = REPO / "packages/py/citry/tests/e2e/test_alpine_slot_scope_e2e.py"
BROWSER_NAMES = ("chromium", "firefox", "webkit")
READY = (
    "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true "
    "&& window.__richRelocation?.registrations?.length === 1 "
    "&& document.querySelectorAll('.term-owner').length === 2 "
    "&& Array.from(document.querySelectorAll('.term-owner')).every((element) => "
    "element.textContent.startsWith('caller:')) "
    "&& document.querySelector('.help-slot')?.textContent === 'help:0'"
)
SIGNING_KEY = "i18n-rich-client-relocation-phase0"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=REPO,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout.strip()


def ensure_always_on_checks() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    require(
        not [node for node in ast.walk(tree) if isinstance(node, ast.Assert)],
        "the evidence harness must not use optimization-sensitive assert statements",
    )
    for script in (CANDIDATE, PROBE):
        require("console.assert" not in script.read_text(encoding="utf-8"), f"{script.name} uses console.assert")


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


def build_fixture() -> tuple[Citry, str]:
    engine = Citry(secret=SIGNING_KEY)
    engine.set_mounted_prefix("/citry")

    class StatefulSlot(Component):
        citry = engine

        def template_data(self, kwargs: Any, _slots: Any) -> dict[str, str]:
            return {"occurrence": kwargs["occurrence"]}

        def js_data(self, kwargs: Any, _slots: Any) -> dict[str, str]:
            return {"occurrence": kwargs["occurrence"]}

        js = """
          $component(({ data, scope }) => {
            const runtime = window.__richRelocation;
            scope.identity = scope.identity || Symbol(data.occurrence);
            runtime.inits.push(data.occurrence);
            runtime.scopes[data.occurrence] = scope;
            return () => runtime.cleanups.push(data.occurrence);
          });
        """
        template = """
          <label class="terms-slot" c-data-occurrence="occurrence">
            <input class="terms-input" c-data-occurrence="occurrence">
          </label>
        """

    class Rich(Component):
        citry = engine

        def template_data(self, _kwargs: Any, slots: dict[str, Any]) -> dict[str, Any]:
            layout = [
                ("text", "Before <unsafe> "),
                ("slot", "terms_link", 0),
                ("text", ", again "),
                ("slot", "terms_link", 1),
                ("text", ", and finally "),
                ("slot", "help_link", 0),
                ("text", "."),
            ]
            items: list[dict[str, Any]] = []
            occurrences: list[dict[str, Any]] = []
            for item in layout:
                if item[0] == "text":
                    items.append({"kind": "text", "part": "", "text": item[1]})
                    continue
                slot_name, index = item[1], item[2]
                key = f"message:{slot_name}:{index}"
                part = slots[slot_name]({"occurrence": key})
                if not isinstance(part, (PhysicalRegionPart, PhysicalRegionRender)):
                    raise TypeError(f"Slot occurrence {key!r} did not produce an ownership region.")
                occurrences.append({"key": key, "regionId": int(part.region_id), "slot": slot_name})
                items.append({"key": key, "kind": "slot", "part": part, "text": ""})
            self._rich_occurrences = occurrences
            return {"items": items}

        def js_data(self, _kwargs: Any, _slots: Any) -> dict[str, Any]:
            return {"occurrences": self._rich_occurrences}

        js = """
          $component((context) => {
            window.__richRelocation.registrations.push(context);
          });
        """
        template = """
          <span class="rich-relocation-output">
            <c-for each="item in items">
              <c-if cond="item['kind'] == 'text'">{{ item['text'] }}</c-if>
              <c-else>
                <bdi
                  class="rich-slot-boundary"
                  dir="auto"
                  c-data-occurrence="item['key']"
                >{{ item['part'] }}</bdi>
              </c-else>
            </c-for>
          </span>
        """

    class Foreign(Component):
        citry = engine
        template = '<aside class="foreign-slot"><c-slot /></aside>'

    class Harness(Component):
        citry = engine
        template = """
          <section
            class="i18n-relocation-provider"
            lang="en-US"
            dir="ltr"
            tabindex="-1"
            x-data="{ owner: 'caller', clicks: 0 }"
          >
            <output class="caller-clicks" x-text="clicks"></output>
            <c-rich>
              <c-fill name="terms_link" data="slot_data">
                <button
                  class="term-owner"
                  c-data-occurrence="slot_data.occurrence"
                  lang="en"
                  x-text="owner + ':' + $el.dataset.occurrence"
                  @click="clicks += 1"
                ></button>
                <span class="hostile-slot-text" lang="en">English &#x2069;&#x202E;override&#x202C;</span>
                <c-stateful-slot
                  #c-key="'inner:' + slot_data.occurrence"
                  c-occurrence="slot_data.occurrence"
                />
              </c-fill>
              <c-fill name="help_link" data="slot_data">
                <template x-teleport="#portal">
                  <button
                    class="help-slot"
                    c-data-occurrence="slot_data.occurrence"
                    dir="auto"
                    lang="en"
                    x-data="{ localClicks: 0 }"
                    x-text="'help:' + localClicks"
                    @click="localClicks += 1"
                  ></button>
                </template>
              </c-fill>
            </c-rich>
            <c-foreign><span class="foreign-content" x-text="'foreign'"></span></c-foreign>
          </section>
        """

    class Page(Component):
        citry = engine
        template = """
          <html><body>
            <script>
              window.__richRelocation = {
                cleanups: [], inits: [], registrations: [], scopes: {}
              };
            </script>
            <div id="portal"></div>
            <c-harness />
          </body></html>
        """

    return engine, str(Page())


def run_browser_matrix() -> tuple[dict[str, Any], dict[str, str]]:
    engine, document = build_fixture()
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
                page_errors: list[str] = []
                console_errors: list[str] = []
                page.on("pageerror", lambda error, target=page_errors: target.append(str(error)))
                page.on(
                    "console",
                    lambda message, target=console_errors: (
                        target.append(message.text) if message.type == "error" else None
                    ),
                )
                page.goto(url)
                page.wait_for_function(READY)
                page.add_script_tag(content=candidate)
                page.add_script_tag(content=probe)
                results[name] = page.evaluate("CitryRichRelocationProbe.runProbe()")
                require(not page_errors, f"{name} page errors: {page_errors!r}")
                require(not console_errors, f"{name} console errors: {console_errors!r}")
            finally:
                browser.close()
    canonical = results[BROWSER_NAMES[0]]
    require(
        all(results[name] == canonical for name in BROWSER_NAMES[1:]),
        f"browser semantic results differ: {results!r}",
    )
    return results, versions


def run_runtime_baselines() -> None:
    run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            (
                "packages/py/citry/tests/e2e/test_alpine_root_shapes_e2e.py::"
                "test_same_task_range_move_survives_but_later_detach_is_terminal"
            ),
            (
                "packages/py/citry/tests/e2e/test_alpine_slot_scope_e2e.py::"
                "test_supplied_fill_uses_caller_scope_before_fill_local_data"
            ),
            (
                "packages/py/citry/tests/e2e/test_alpine_slot_scope_e2e.py::"
                "test_teleported_fill_keeps_source_scope_and_native_physical_event_path"
            ),
            (
                "packages/py/citry/tests/e2e/test_alpine_slot_scope_e2e.py::"
                "test_multi_root_mirrors_keep_one_source_when_the_first_copy_is_removed"
            ),
            "--browser",
            "chromium",
            "--browser",
            "firefox",
            "--browser",
            "webkit",
        ]
    )


def build_evidence() -> dict[str, Any]:
    ensure_always_on_checks()
    run_runtime_baselines()
    results, versions = run_browser_matrix()
    canonical = results[BROWSER_NAMES[0]]
    require(all(canonical["initial_gates"].values()), "an initial ownership gate failed")
    require(all(canonical["move_gates"].values()), "a relocation gate failed")
    require(all(canonical["round_trip_gates"].values()), "a round-trip gate failed")
    require(all(failure["atomic"] for failure in canonical["failures"].values()), "a failure mutated the page")
    return {
        "artifacts": {
            "candidate": sha256(CANDIDATE),
            "client_runtime": sha256(CLIENT_RUNTIME),
            "component_render_source": sha256(COMPONENT_RENDER_SOURCE),
            "graph_spec": sha256(GRAPH_SPEC),
            "harness": sha256(Path(__file__)),
            "ownership_source": sha256(OWNERSHIP_SOURCE),
            "probe": sha256(PROBE),
            "root_shapes_tests": sha256(ROOT_SHAPES_TEST),
            "slot_scope_tests": sha256(SLOT_SCOPE_TEST),
            "uv_lock": sha256(REPO / "uv.lock"),
        },
        "bounded_limits": [
            "the candidate is research JavaScript loaded after Citry rather than a shipped runtime API",
            "the client switch keeps the same occurrence keys and counts",
            "each tested Slot region has one physical placement",
            "browser creation, provider inheritance, stale generations, and chunk loading remain separate",
        ],
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
        "existing_slot_region_is_sufficient_for_source_aware_occurrence": True,
        "new_client_graph_record_required": False,
        "result": "PASS_BOUNDED",
        "semantic_result": canonical,
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
