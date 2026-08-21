"""
Benchmark Citry's graph-first browser runtime at realistic component counts.

Run from the repository root after installing the e2e dependency group and
Playwright browser binaries:

    uv run --no-sync python benchmarks/client.py --browser chromium --counts 10 100 325 --rounds 9

Timing and heap results are informational. Deterministic payload and
live-resource budgets are enforced by pytest instead.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import shutil
import statistics
import subprocess
import sys
import threading
from dataclasses import asdict
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any, Self
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from client_scenario import build_client_scenario, payload_sizes
from playwright.sync_api import sync_playwright

from citry.contrib.wsgi import wsgi_app

if TYPE_CHECKING:
    from collections.abc import Callable


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass


class _ScenarioServer:
    def __init__(self, count: int) -> None:
        self.scenario = build_client_scenario(count)
        self.document = self.scenario.document()
        self.shell = self.scenario.shell()
        self.fragment = self.scenario.fragment()
        self.morph = self.scenario.morph_fragment()
        self.mounted_document = self.scenario.morph_document()
        citry_app = wsgi_app(self.scenario.citry)
        documents = {
            "/document": self.document,
            "/shell": self.shell,
            "/fragment": self.fragment,
            "/morph": self.morph,
            "/morph-document": self.mounted_document,
        }

        def app(environ: dict[str, Any], start_response: Callable[..., Any]) -> list[bytes]:
            path = environ.get("PATH_INFO", "")
            if path == "/citry" or path.startswith("/citry/"):
                sub = dict(environ)
                sub["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + "/citry"
                sub["PATH_INFO"] = path[len("/citry") :]
                return list(citry_app(sub, start_response))
            content = documents.get(path)
            if content is None:
                start_response("404 Not Found", [("Content-Length", "0")])
                return []
            body = content.encode("utf8")
            start_response(
                "200 OK",
                [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))],
            )
            return [body]

        self.server = make_server(
            "127.0.0.1",
            0,
            app,
            server_class=_ThreadingWSGIServer,
            handler_class=_QuietHandler,
        )
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> Self:
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.server.shutdown()


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "median_ms": round(statistics.median(values), 3),
        "p95_ms": round(_p95(values), 3),
    }


def _collect_page_errors(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    return errors


def _wait_for_workload(page: Any, count: int, *, include_shell: bool = False) -> None:
    expected_instances = count + (2 if include_shell else 1)
    page.wait_for_function(
        """
        ([count, expectedInstances]) => {
          const runtime = window.Citry?.alpine?._debug?.().runtime;
          return window.Citry?.events?._internal?.alpineStarted === true
            && runtime?.liveInstances === expectedInstances
            && runtime.componentBoundaries === count
            && runtime.rootBindings === 2 * count
            && runtime.propsEffects === count
            && runtime.managedEffects === count;
        }
        """,
        arg=[count, expected_instances],
    )


def _snapshot(page: Any) -> dict[str, Any]:
    return page.evaluate(
        """
        () => ({
          alpine: Citry.alpine._debug(),
          events: Citry.events._internal.debug(),
          initCount: window.__citryBenchInits || 0,
          cleanupCount: window.__citryBenchCleanups || 0,
          items: document.querySelectorAll('.bench-item').length,
        })
        """
    )


def _assert_sample(
    snapshot: dict[str, Any],
    count: int,
    errors: list[str],
    *,
    expected_inits: int,
    expected_cleanups: int,
) -> None:
    runtime = snapshot["alpine"]["runtime"]
    if errors:
        msg = "browser errors invalidated the benchmark sample: " + " | ".join(errors)
        raise RuntimeError(msg)
    expected = {
        "items": count,
        "propsEffects": count,
        "managedEffects": count,
        "componentBoundaries": count,
        "rootBindings": count * 2,
        "initCount": expected_inits,
        "cleanupCount": expected_cleanups,
    }
    actual = {
        "items": snapshot["items"],
        "propsEffects": runtime["propsEffects"],
        "managedEffects": runtime["managedEffects"],
        "componentBoundaries": runtime["componentBoundaries"],
        "rootBindings": runtime["rootBindings"],
        "initCount": snapshot["initCount"],
        "cleanupCount": snapshot["cleanupCount"],
    }
    if actual != expected:
        msg = f"invalid benchmark state: expected {expected!r}, got {actual!r}"
        raise RuntimeError(msg)


def _startup_round(browser: Any, server: _ScenarioServer, count: int) -> tuple[float, dict[str, Any]]:
    page = browser.new_page()
    errors = _collect_page_errors(page)
    try:
        page.goto(server.base + "/document", wait_until="domcontentloaded")
        _wait_for_workload(page, count)
        snapshot = _snapshot(page)
        _assert_sample(snapshot, count, errors, expected_inits=count, expected_cleanups=0)
        timing = page.evaluate(
            """
            () => {
              const entry = performance.getEntriesByType('navigation')[0];
              return entry.domContentLoadedEventEnd - entry.responseEnd;
            }
            """
        )
        return float(timing), snapshot
    finally:
        page.close()


def _adoption_round(browser: Any, server: _ScenarioServer, count: int) -> tuple[float, dict[str, Any]]:
    page = browser.new_page()
    errors = _collect_page_errors(page)
    try:
        page.goto(server.base + "/shell", wait_until="domcontentloaded")
        page.wait_for_function("window.Citry?.events?._internal?.alpineStarted === true")
        duration = page.evaluate(
            """
            async ([html, count]) => {
              const started = performance.now();
              const template = document.createElement('template');
              template.innerHTML = html;
              const tag = template.content.querySelector('script[data-citry-graph]');
              const revision = JSON.parse(tag.textContent).revision;
              document.querySelector('#fragment-target').append(template.content);
              await Citry.manager.ownership.whenReady(revision);
              const deadline = performance.now() + 10000;
              while ((window.__citryBenchInits || 0) < count) {
                if (performance.now() > deadline) throw new Error('fragment callbacks did not settle');
                await new Promise((resolve) => setTimeout(resolve, 0));
              }
              return performance.now() - started;
            }
            """,
            [server.fragment, count],
        )
        _wait_for_workload(page, count, include_shell=True)
        snapshot = _snapshot(page)
        _assert_sample(snapshot, count, errors, expected_inits=count, expected_cleanups=0)
        return float(duration), snapshot
    finally:
        page.close()


def _morph_round(browser: Any, server: _ScenarioServer, count: int) -> tuple[dict[str, float], dict[str, Any]]:
    page = browser.new_page()
    errors = _collect_page_errors(page)
    try:
        page.goto(server.base + "/morph-document", wait_until="domcontentloaded")
        _wait_for_workload(page, count)
        timing = page.evaluate(
            """
            async ([html, count]) => {
              const internal = Citry.events._internal;
              const id = document.querySelector('.bench-list').getAttribute('data-cid');
              const anchor = internal.getAnchor(id);
              const targets = document.querySelectorAll('[data-cid-' + id + ']');
              if (targets.length !== 1) {
                throw new Error('morph benchmark expected one exact instance target, found ' + targets.length);
              }
              anchor.epoch = 1;
              const started = performance.now();
              await internal.applyResult(
                {
                  ok: true,
                  epoch: 1,
                  actions: [{ action: 'render', target: 'cid:' + id, swap: 'morph', html }],
                },
                { anchor, instance: id, event: 'choose' },
              );
              const transaction = performance.now() - started;
              // The keyed children keep their physical nodes and lifecycle
              // resources. ``applyResult`` has already awaited graph adoption;
              // the assertions below prove that morph neither recreated nor
              // leaked any component initializer or cleanup.
              await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
              return { transaction, paint: performance.now() - started };
            }
            """,
            [server.morph, count],
        )
        snapshot = _snapshot(page)
        _assert_sample(snapshot, count, errors, expected_inits=count, expected_cleanups=0)
        return {"transaction_ms": float(timing["transaction"]), "paint_ms": float(timing["paint"])}, snapshot
    finally:
        page.close()


def _memory_sample(browser: Any, server: _ScenarioServer, count: int, browser_name: str) -> dict[str, Any] | None:
    if browser_name != "chromium":
        return None
    page = browser.new_page()
    errors = _collect_page_errors(page)
    try:
        page.goto(server.base + "/document", wait_until="domcontentloaded")
        _wait_for_workload(page, count)
        snapshot = _snapshot(page)
        _assert_sample(snapshot, count, errors, expected_inits=count, expected_cleanups=0)
        session = page.context.new_cdp_session(page)
        session.send("HeapProfiler.collectGarbage")
        heap = session.send("Runtime.getHeapUsage")
        dom = session.send("Memory.getDOMCounters")
        return {
            "used_heap_bytes": heap["usedSize"],
            "total_heap_bytes": heap["totalSize"],
            "documents": dom["documents"],
            "nodes": dom["nodes"],
            "js_event_listeners": dom["jsEventListeners"],
            "runtime": snapshot["alpine"]["runtime"],
            "events": snapshot["events"],
        }
    finally:
        page.close()


def _git_revision() -> str:
    git = shutil.which("git")
    if git is None:
        return "unknown"
    result = subprocess.run(
        [git, "describe", "--always", "--dirty"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or "unknown"


def run(browser_name: str, counts: list[int], rounds: int, memory: bool) -> dict[str, Any]:
    output: dict[str, Any] = {
        "metadata": {
            "browser": browser_name,
            "rounds": rounds,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "git": _git_revision(),
            "timing_policy": "discard one cold round; report median and p95",
        },
        "counts": {},
    }
    with sync_playwright() as playwright:
        browser_type = getattr(playwright, browser_name)
        for count in counts:
            browser = browser_type.launch()
            output["metadata"].setdefault("browser_version", browser.version)
            try:
                with _ScenarioServer(count) as server:
                    startup: list[float] = []
                    adoption: list[float] = []
                    morph_transaction: list[float] = []
                    morph_paint: list[float] = []
                    last_snapshot: dict[str, Any] | None = None
                    for index in range(rounds + 1):
                        startup_value, _ = _startup_round(browser, server, count)
                        adoption_value, _ = _adoption_round(browser, server, count)
                        morph_value, last_snapshot = _morph_round(browser, server, count)
                        if index == 0:
                            continue
                        startup.append(startup_value)
                        adoption.append(adoption_value)
                        morph_transaction.append(morph_value["transaction_ms"])
                        morph_paint.append(morph_value["paint_ms"])
                    output["counts"][str(count)] = {
                        "payload": asdict(payload_sizes(server.document)),
                        "startup": _summary(startup),
                        "adoption": _summary(adoption),
                        "morph_transaction": _summary(morph_transaction),
                        "morph_paint": _summary(morph_paint),
                        "resources": last_snapshot,
                        "memory": _memory_sample(browser, server, count, browser_name) if memory else None,
                    }
            finally:
                browser.close()
    return output


def _print_table(result: dict[str, Any]) -> None:
    print(
        f"Citry client benchmark: {result['metadata']['browser']} "
        f"{result['metadata']['browser_version']}, {result['metadata']['rounds']} measured rounds"
    )
    print("count  startup p50/p95  adopt p50/p95    morph p50/p95    graph raw/gzip")
    for count, record in result["counts"].items():
        startup = record["startup"]
        adoption = record["adoption"]
        morph = record["morph_transaction"]
        payload = record["payload"]
        print(
            f"{count:>5}  {startup['median_ms']:>7.1f}/{startup['p95_ms']:<7.1f} "
            f"{adoption['median_ms']:>7.1f}/{adoption['p95_ms']:<7.1f} "
            f"{morph['median_ms']:>7.1f}/{morph['p95_ms']:<7.1f} "
            f"{payload['graph_raw']:>9}/{payload['graph_gzip']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"], default="chromium")
    parser.add_argument("--counts", type=int, nargs="+", default=[10, 100, 325])
    parser.add_argument("--rounds", type=int, default=9)
    parser.add_argument("--memory", action="store_true", help="collect Chromium CDP heap and DOM counters")
    parser.add_argument("--json", action="store_true", help="print JSON instead of the compact table")
    parser.add_argument("--_single", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("--rounds must be positive")
    if len(args.counts) > 1 and not args._single:
        result = {"metadata": {}, "counts": {}}
        for count in args.counts:
            command = [
                sys.executable,
                __file__,
                "--browser",
                args.browser,
                "--counts",
                str(count),
                "--rounds",
                str(args.rounds),
                "--json",
                "--_single",
            ]
            if args.memory:
                command.append("--memory")
            child = subprocess.run(command, check=False, capture_output=True, text=True)
            if child.returncode != 0:
                detail = child.stderr.strip() or child.stdout.strip() or "no child output"
                msg = f"client benchmark failed for count {count}:\n{detail}"
                raise RuntimeError(msg)
            record = json.loads(child.stdout)
            if not result["metadata"]:
                result["metadata"] = record["metadata"]
            result["counts"].update(record["counts"])
    else:
        result = run(args.browser, args.counts, args.rounds, args.memory)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_table(result)


if __name__ == "__main__":
    main()
