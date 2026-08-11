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
from citry.contrib.wsgi import wsgi_app

if TYPE_CHECKING:
    from collections.abc import Iterator


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BROWSER = HERE / "browser" / "probe.js"
CLIENT_RUNTIME = REPO / "packages/py/citry/citry/ext/dependencies/client/citry.js"
EVENTS_RUNTIME = REPO / "packages/js/citry-client/src/citry-events.ts"
STRUCTURAL_TEST = REPO / "packages/py/citry/tests/e2e/test_alpine_structural_e2e.py"
SLOT_SCOPE_TEST = REPO / "packages/py/citry/tests/e2e/test_alpine_slot_scope_e2e.py"
BROWSER_NAMES = ("chromium", "firefox", "webkit")
READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"
FIXTURE_READY = (
    "Citry.manager.ownership.revisions().length === 1 "
    "&& document.querySelectorAll('.terms-input').length === 2 "
    "&& document.querySelector('.help-slot')?.textContent === 'help:0'"
)
SIGNING_KEY = "i18n-rich-client-runtime-phase0"


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
    require("console.assert" not in BROWSER.read_text(encoding="utf-8"), "browser probe uses console.assert")


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


def build_fixture() -> tuple[Citry, str, str, str, dict[str, str]]:
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
            const runtime = window.__richRuntime;
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

    class Occurrence(Component):
        citry = engine

        def template_data(self, kwargs: Any, _slots: Any) -> dict[str, Any]:
            return {"content": kwargs["content"], "identity": kwargs["identity"]}

        template = "{{ content({'occurrence': identity}) }}"

    class Rich(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: dict[str, Any]) -> dict[str, Any]:
            locale = kwargs["locale"]
            if locale == "ar":
                layout = [
                    ("text", "أولًا "),
                    ("slot", "help_link", 0),
                    ("text", " ثم "),
                    ("slot", "terms_link", 0),
                    ("text", " وبعدها "),
                    ("slot", "terms_link", 1),
                    ("text", " وأخيرًا "),
                    ("slot", "terms_link", 2),
                    ("text", "."),
                ]
            else:
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
            for item in layout:
                if item[0] == "text":
                    items.append({"kind": "text", "text": item[1]})
                else:
                    name, occurrence = item[1], item[2]
                    identity = f"rich:{name}:{occurrence}"
                    items.append({"content": slots[name], "identity": identity, "kind": "slot", "text": ""})
            return {"items": items}

        template = """
          <span class="rich-output">
            <c-for each="item in items">
              <c-if cond="item['kind'] == 'text'">{{ item['text'] }}</c-if>
              <c-else>
                <c-occurrence
                  #c-key="item['identity']"
                  c-content="item['content']"
                  c-identity="item['identity']"
                >
                </c-occurrence>
              </c-else>
            </c-for>
          </span>
        """

    class Harness(Component):
        citry = engine

        class Events:
            def refresh(self) -> None:
                pass

        def template_data(self, kwargs: Any, _slots: Any) -> dict[str, str]:
            locale = kwargs["locale"]
            return {"direction": "rtl" if locale == "ar" else "ltr", "locale": locale}

        template = """
          <section
            class="i18n-runtime-provider"
            c-lang="locale"
            c-dir="direction"
            tabindex="-1"
            x-data="{ owner: 'caller', clicks: 0 }"
          >
            <output class="click-count" x-text="clicks"></output>
            <c-rich #c-key="'rich'" c-locale="locale">
              <c-fill name="terms_link" data="slot_data">
                <span
                  class="term-owner"
                  c-data-occurrence="slot_data.occurrence"
                  x-text="typeof owner === 'undefined' ? 'missing' : owner"
                >caller-owned</span>
                <c-stateful-slot
                  #c-key="'inner'"
                  #c-ignore
                  c-occurrence="slot_data.occurrence"
                />
              </c-fill>
              <c-fill name="help_link" data="slot_data">
                <template x-teleport="#portal">
                  <button
                    class="help-slot"
                    c-data-occurrence="slot_data.occurrence"
                    x-data="{ localClicks: 0 }"
                    x-text="'help:' + localClicks"
                    @click="localClicks += 1"
                  ></button>
                </template>
              </c-fill>
            </c-rich>
          </section>
        """

    class Page(Component):
        citry = engine
        template = """
          <html><body>
            <script>window.__richRuntime = { inits: [], cleanups: [], scopes: {} };</script>
            <div id="portal"></div>
            <c-harness locale="en-US" />
          </body></html>
        """

    document = str(Page())
    growth = Harness(locale="ar").render().serialize(deps_strategy="fragment")
    back = Harness(locale="en-US").render().serialize(deps_strategy="fragment")
    return engine, document, growth, back, {"occurrence": Occurrence.class_id}


def build_forwarded_failure_fixture() -> tuple[Citry, str]:
    engine = Citry(secret=SIGNING_KEY)
    engine.set_mounted_prefix("/citry")

    class ForwardOccurrence(Component):
        citry = engine
        template = "<c-slot />"

    class ForwardReceiver(Component):
        citry = engine

        def template_data(self, _kwargs: Any, slots: dict[str, Any]) -> dict[str, Any]:
            return {"content": slots["content"]}

        template = """
          <section>
            <c-forward-occurrence #c-key="'forwarded'">
              {{ content({'occurrence': 'forwarded'}) }}
            </c-forward-occurrence>
          </section>
        """

    class ForwardPage(Component):
        citry = engine
        template = """
          <html><body><main x-data="{ owner: 'caller' }">
            <c-forward-receiver>
              <c-fill name="content" data="slot_data">
                <span class="forwarded-owner" x-text="owner"></span>
              </c-fill>
            </c-forward-receiver>
          </main></body></html>
        """

    return engine, str(ForwardPage())


def run_browser_matrix() -> tuple[dict[str, Any], dict[str, str]]:
    citry, document, growth, back, class_ids = build_fixture()
    failed_citry, failed_document = build_forwarded_failure_fixture()
    helper = BROWSER.read_text(encoding="utf-8")
    results: dict[str, Any] = {}
    versions: dict[str, str] = {}
    with (
        serve_page(citry, document) as url,
        serve_page(failed_citry, failed_document) as failed_url,
        sync_playwright() as playwright,
    ):
        for name in BROWSER_NAMES:
            browser = getattr(playwright, name).launch(headless=True)
            try:
                versions[name] = browser.version
                page = browser.new_page()
                errors: list[str] = []

                def record_page_error(error: Any, target: list[str] = errors) -> None:
                    target.append(str(error))

                page.on("pageerror", record_page_error)
                page.goto(url)
                page.wait_for_function(READY)
                page.wait_for_function(FIXTURE_READY)
                page.add_script_tag(content=helper)
                server_result = page.evaluate(
                    "([growth, back, ids]) => CitryRichRuntimeProbe.runServerBackedProbe(growth, back, ids)",
                    [growth, back, class_ids],
                )
                require(not errors, f"{name} server-backed page errors: {errors!r}")

                errors.clear()
                page.goto(url)
                page.wait_for_function(READY)
                page.wait_for_function(FIXTURE_READY)
                page.add_script_tag(content=helper)
                client_result = page.evaluate(
                    "ids => CitryRichRuntimeProbe.runClientOnlyProbe(ids)",
                    class_ids,
                )
                require(not errors, f"{name} client-only page errors: {errors!r}")

                forwarded_logs: list[str] = []
                failed_page = browser.new_page()

                def record_forwarded_log(message: Any, target: list[str] = forwarded_logs) -> None:
                    target.append(f"{message.type}:{message.text}")

                failed_page.on("console", record_forwarded_log)
                failed_page.goto(failed_url)
                failed_page.wait_for_timeout(300)
                forwarded_result = {
                    "manifest_rejected": failed_page.evaluate("Citry.manager.ownership.revisions().length === 0"),
                    "owner_text_rendered_before_rejection": failed_page.locator(".forwarded-owner").inner_text()
                    == "caller",
                    "pointed_owner_mismatch": any(
                        "slot region ownership does not match its fill" in message for message in forwarded_logs
                    ),
                }
                require(
                    all(forwarded_result.values()),
                    f"{name} forwarded-slot failure changed: {forwarded_result!r}; {forwarded_logs!r}",
                )
                results[name] = {
                    "client_only": client_result,
                    "forwarded_slot_failure": forwarded_result,
                    "server_backed": server_result,
                }
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
                "packages/py/citry/tests/e2e/test_alpine_structural_e2e.py::"
                "test_native_structural_clone_of_server_component_fails_before_graph_activation"
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
    client_surface = canonical["client_only"]["ownership_surface"]
    client_findings = canonical["client_only"]["integration_findings"]
    server_findings = canonical["server_backed"]["integration_findings"]
    growth = canonical["server_backed"]["growth_observations"]
    final = canonical["server_backed"]["final_observations"]
    require(client_surface["has_browser_slot_instantiation"] is False, "unexpected instantiation API appeared")
    require(client_surface["has_range_relocation"] is False, "unexpected relocation API appeared")
    require(all(canonical["client_only"]["gates"].values()), "an existing-range move gate failed")
    require(
        client_findings["repeated_slot_source_projection_missing"]
        and server_findings["repeated_slot_source_projection_missing"],
        "the direct keyed Slot unexpectedly inherited its caller's Alpine scope",
    )
    require(all(canonical["forwarded_slot_failure"].values()), "the forwarded-slot failure changed")
    require(
        growth["existing_component_ranges_kept_logical_identity"]
        and not growth["existing_inputs_kept_dom_identity"]
        and not growth["focus_and_selection_survived"]
        and not growth["retained_inner_ranges_were_not_recreated"]
        and not growth["teleport_dom_identity_survived"]
        and not growth["teleport_kept_local_state"],
        "the server-backed lifecycle result changed",
    )
    require(
        final["existing_ranges_survived_round_trip"]
        and not final["added_occurrence_cleaned_once"]
        and not final["revisions_pruned"]
        and not final["surviving_state_remained"],
        "the server-backed return result changed",
    )
    return {
        "artifacts": {
            "browser_probe": sha256(BROWSER),
            "client_runtime": sha256(CLIENT_RUNTIME),
            "events_runtime_source": sha256(EVENTS_RUNTIME),
            "harness": sha256(Path(__file__)),
            "native_clone_test": sha256(STRUCTURAL_TEST),
            "slot_scope_tests": sha256(SLOT_SCOPE_TEST),
            "uv_lock": sha256(REPO / "uv.lock"),
        },
        "browser_results_equal": True,
        "browser_versions": versions,
        "bounded_limits": [
            "the server-backed count change uses an Events fragment rather than a catalog-only browser switch",
            "the client-only path calls current private graph records because no checked relocation API exists",
            "the client-only path can move only occurrences that the server already rendered",
            "the direct keyed Slot path cannot see the caller's Alpine scope",
            "the normal slot-forwarding path renders caller scope but the ownership manifest rejects it",
            "the server-backed path recreates surviving supplied content and fails the rich-switch lifecycle contract",
            "provider inheritance, stale generations, chunk loading, and cache variation are separate Phase 0 work",
        ],
        "dependencies": {
            "playwright": importlib.metadata.version("playwright"),
            "pytest_playwright": importlib.metadata.version("pytest-playwright"),
        },
        "environment": {
            "machine": platform.machine(),
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "native_component_clone_rejected_in_all_browsers": True,
        "normal_supplied_slot_and_teleport_baselines_passed": True,
        "current_runtime_can_move_only_existing_keyed_occurrences_without_lifecycle_loss": True,
        "current_runtime_cannot_combine_keyed_occurrences_with_caller_slot_scope": True,
        "server_fragment_count_change_recreated_surviving_slot_content": True,
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
