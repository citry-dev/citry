# ruff: noqa: E402, T201
"""Measure the literal-DOM and canvas component-field research spikes."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
import mimetypes
import os
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Self, cast
from urllib.parse import parse_qs, unquote, urlsplit

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from components import (
    MAX_CANVAS_PIXELS,
    SUPPORTED_COUNTS,
    Renderer,
    build_scenario,
    component_fixture_sha256,
)
from docs_site._internal.static_deps import export_runtime
from playwright.sync_api import sync_playwright

if TYPE_CHECKING:
    from collections.abc import Sequence

    from playwright.sync_api import Browser, BrowserContext, Page, Playwright

RENDERERS: tuple[Renderer, ...] = ("baseline", "dom", "canvas")
BOOTSTRAP_SEED = 20_260_728
ORDER_SEED = 7_281_605
PROBE_DIR = Path(__file__).resolve().parent
ARRIVAL_WAIT_MS = 2_150
RIPPLE_WAIT_MS = 1_050


@dataclass(frozen=True, slots=True)
class Profile:
    """One reproducible browser viewport and throttling profile."""

    name: Literal["desktop", "mobile"]
    width: int
    height: int
    dpr: float
    cpu_rate: int
    mobile: bool
    touch: bool
    network: dict[str, float] | None
    lcp_budget_ms: float
    blocking_budget_ms: float


PROFILES = {
    "desktop": Profile(
        name="desktop",
        width=1440,
        height=900,
        dpr=1,
        cpu_rate=1,
        mobile=False,
        touch=False,
        network=None,
        lcp_budget_ms=1_500,
        blocking_budget_ms=100,
    ),
    "mobile": Profile(
        name="mobile",
        width=390,
        height=844,
        dpr=2,
        cpu_rate=4,
        mobile=True,
        touch=True,
        network={
            "latency": 150,
            "downloadThroughput": 1_600_000 / 8,
            "uploadThroughput": 750_000 / 8,
        },
        lcp_budget_ms=2_500,
        blocking_budget_ms=200,
    ),
}


def _nearest_percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * percentile) - 1)]


def _summary(values: Sequence[float]) -> dict[str, float | None]:
    if not values:
        return {"median": None, "p75": None, "p95": None, "min": None, "max": None}
    return {
        "median": round(statistics.median(values), 3),
        "p75": round(_nearest_percentile(values, 0.75), 3),
        "p95": round(_nearest_percentile(values, 0.95), 3),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
    }


def _bootstrap_median_interval(values: Sequence[float], resamples: int) -> dict[str, float | None]:
    if not values:
        return {"low": None, "high": None}
    rng = random.Random(BOOTSTRAP_SEED)  # noqa: S311 - deterministic research resampling
    medians = [statistics.median(rng.choices(values, k=len(values))) for _ in range(resamples)]
    return {
        "low": round(_nearest_percentile(medians, 0.025), 3),
        "high": round(_nearest_percentile(medians, 0.975), 3),
    }


def _git_revision() -> str:
    git = shutil.which("git")
    if git is None:
        return "unknown"
    result = subprocess.run(
        [git, "describe", "--always", "--dirty"],
        cwd=PROBE_DIR,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or "unknown"


def _host_memory_bytes() -> int | None:
    try:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render_case(renderer: Renderer, count: int, warmups: int, samples: int) -> dict[str, Any]:
    scenario = build_scenario(renderer, count)
    started = time.perf_counter_ns()
    html, cell_renders = scenario.render()
    first_ms = (time.perf_counter_ns() - started) / 1_000_000
    expected_renders = 0 if renderer == "baseline" else count
    if cell_renders != expected_renders:
        msg = f"{renderer}/{count} rendered {cell_renders} cells, expected {expected_renders}"
        raise RuntimeError(msg)

    for _ in range(warmups):
        scenario.render()
    warm_ms: list[float] = []
    for _ in range(samples):
        started = time.perf_counter_ns()
        _, measured_renders = scenario.render()
        warm_ms.append((time.perf_counter_ns() - started) / 1_000_000)
        if measured_renders != expected_renders:
            msg = f"warm {renderer}/{count} rendered {measured_renders} cells, expected {expected_renders}"
            raise RuntimeError(msg)

    raw = html.encode()
    return {
        "renderer": renderer,
        "count": count,
        "cell_renders": cell_renders,
        "columns": scenario.columns,
        "rows": scenario.rows,
        "descriptor_sha256": scenario.descriptor_sha256,
        "first_render_ms": first_ms,
        "warm_render_ms": warm_ms,
        "html_raw_bytes": len(raw),
        "html_gzip_bytes": len(gzip.compress(raw, mtime=0)),
    }


def _collect_server_metrics(
    counts: list[int],
    processes: int,
    warmups: int,
    samples_per_process: int,
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for renderer in RENDERERS:
        output[renderer] = {}
        for count in counts:
            records: list[dict[str, Any]] = []
            for _ in range(processes):
                command = [
                    sys.executable,
                    __file__,
                    "--_render-case",
                    renderer,
                    str(count),
                    "--server-warmups",
                    str(warmups),
                    "--server-samples",
                    str(samples_per_process),
                ]
                child = subprocess.run(command, check=False, capture_output=True, text=True)
                if child.returncode != 0:
                    detail = child.stderr.strip() or child.stdout.strip() or "no child output"
                    msg = f"server measurement failed for {renderer}/{count}:\n{detail}"
                    raise RuntimeError(msg)
                records.append(json.loads(child.stdout))
            first_values = [float(record["first_render_ms"]) for record in records]
            warm_values = [float(value) for record in records for value in record["warm_render_ms"]]
            first = records[0]
            output[renderer][str(count)] = {
                "cell_renders": first["cell_renders"],
                "columns": first["columns"],
                "rows": first["rows"],
                "descriptor_sha256": first["descriptor_sha256"],
                "html_raw_bytes": first["html_raw_bytes"],
                "html_gzip_bytes": first["html_gzip_bytes"],
                "fresh_process_render": _summary(first_values),
                "warm_render": _summary(warm_values),
                "fresh_process_samples_ms": first_values,
                "warm_samples_ms": warm_values,
            }
    return output


class _ResearchHandler(BaseHTTPRequestHandler):
    root: Path

    def do_GET(self) -> None:
        split = urlsplit(self.path)
        relative = unquote(split.path).lstrip("/") or "index.html"
        candidate = (self.root / relative).resolve()
        if self.root not in candidate.parents and candidate != self.root:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if candidate.is_dir():
            candidate /= "index.html"
        if not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        body = candidate.read_bytes()
        query = parse_qs(split.query)
        fault = query.get("fault", [None])[0]
        if fault in {"corrupt", "mutate"} and b"data-field-descriptors" in body:
            start_marker = b'<script type="application/json" data-field-descriptors>'
            start = body.find(start_marker) + len(start_marker)
            end = body.find(b"</script>", start)
            if fault == "corrupt":
                replacement = b"{invalid"
            else:
                descriptors = json.loads(body[start:end])
                descriptors[0][1] = min(1_000_000, descriptors[0][1] + 1)
                replacement = json.dumps(descriptors, separators=(",", ":")).encode()
            body = body[:start] + replacement + body[end:]

        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        encoded = body
        if "gzip" in self.headers.get("Accept-Encoding", ""):
            encoded = gzip.compress(body, mtime=0)
            content_encoding = "gzip"
        else:
            content_encoding = None

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        if content_encoding:
            self.send_header("Content-Encoding", content_encoding)
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *args: Any) -> None:
        pass


class _StaticServer:
    def __init__(self, root: Path) -> None:
        handler = type("ResearchHandler", (_ResearchHandler,), {"root": root.resolve()})
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def __enter__(self) -> Self:
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.server.shutdown()


def _write_pages(root: Path, counts: list[int]) -> None:
    runtime_exported = False
    for renderer in RENDERERS:
        for count in counts:
            scenario = build_scenario(renderer, count)
            html, cell_renders = scenario.render()
            expected = 0 if renderer == "baseline" else count
            if cell_renders != expected:
                msg = f"generated {renderer}/{count} rendered {cell_renders} cells, expected {expected}"
                raise RuntimeError(msg)
            destination = root / renderer / str(count) / "index.html"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(html, encoding="utf-8")
            if not runtime_exported:
                export_runtime(root, scenario.citry)
                runtime_exported = True


def _page_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(f"console:{message.text}") if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"page:{error}"))
    return errors


def _configure_cdp(context: BrowserContext, page: Page, profile: Profile) -> Any:
    session = context.new_cdp_session(page)
    session.send("Performance.enable")
    if profile.cpu_rate != 1:
        session.send("Emulation.setCPUThrottlingRate", {"rate": profile.cpu_rate})
    if profile.network:
        session.send("Network.enable")
        session.send(
            "Network.emulateNetworkConditions",
            {
                "offline": False,
                "packetLoss": 0,
                "connectionType": "cellular4g",
                **profile.network,
            },
        )
    return session


def _performance_metrics(session: Any) -> dict[str, float]:
    response = session.send("Performance.getMetrics")
    return {entry["name"]: float(entry["value"]) for entry in response["metrics"]}


def _metric_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
    names = (
        "TaskDuration",
        "ScriptDuration",
        "RecalcStyleDuration",
        "LayoutDuration",
        "RecalcStyleCount",
        "LayoutCount",
    )
    return {name: round(after.get(name, 0) - before.get(name, 0), 6) for name in names}


def _new_context(browser: Browser, profile: Profile, *, java_script: bool = True) -> BrowserContext:
    return browser.new_context(
        viewport={"width": profile.width, "height": profile.height},
        device_scale_factor=profile.dpr,
        is_mobile=profile.mobile,
        has_touch=profile.touch,
        java_script_enabled=java_script,
        reduced_motion="no-preference",
        color_scheme="dark",
        locale="en-US",
    )


def _url(base_url: str, renderer: Renderer, count: int, query: str = "") -> str:
    return f"{base_url}/{renderer}/{count}/{query}"


def _wait_ready(page: Page) -> None:
    page.wait_for_function(
        """
        () => window.__fieldResearch
          && document.querySelector('[data-field-root]')?.dataset.fieldReady
        """,
        timeout=20_000,
    )


def _frame_probe_script(duration_ms: int) -> str:
    return f"""
      () => {{
        window.__frameProbe = new Promise((resolve) => {{
          const intervals = [];
          const started = performance.now();
          let previous = started;
          const sample = (now) => {{
            if (now >= previous) intervals.push(now - previous);
            previous = now;
            if (now - started >= {duration_ms}) {{
              resolve(intervals);
            }} else {{
              requestAnimationFrame(sample);
            }}
          }};
          requestAnimationFrame(sample);
        }});
      }}
    """


def _dom_stats(page: Page) -> dict[str, int]:
    return cast(
        "dict[str, int]",
        page.evaluate(
            """
            () => {
              let maxChildren = 0;
              let maxDepth = 0;
              const visit = (node, depth) => {
                maxDepth = Math.max(maxDepth, depth);
                maxChildren = Math.max(maxChildren, node.children?.length || 0);
                for (const child of node.children || []) visit(child, depth + 1);
              };
              visit(document.documentElement, 1);
              return {
                elements: document.querySelectorAll('*').length,
                fieldElements: document.querySelectorAll('[data-field-cell]').length,
                maxChildren,
                maxDepth,
              };
            }
            """
        ),
    )


def _timing_sample(
    browser: Browser,
    base_url: str,
    profile: Profile,
    renderer: Renderer,
    count: int,
    block: int,
    order: int,
) -> dict[str, Any]:
    expected_digest = build_scenario(renderer, count).descriptor_sha256
    context = _new_context(browser, profile)
    page = context.new_page()
    errors = _page_errors(page)
    session = _configure_cdp(context, page, profile)
    before = _performance_metrics(session)
    try:
        page.goto(_url(base_url, renderer, count), wait_until="networkidle", timeout=30_000)
        _wait_ready(page)
        before_arrival_metrics = _performance_metrics(session)
        before_arrival = page.evaluate(
            """
            () => ({
              longTaskCount: window.__fieldVitals.longTasks.length,
              eventCount: window.__fieldVitals.events.length,
            })
            """
        )
        page.evaluate(_frame_probe_script(ARRIVAL_WAIT_MS))
        page.evaluate("() => window.__fieldResearch.runWave()")
        arrival_intervals = page.evaluate("() => window.__frameProbe")
        after_arrival_metrics = _performance_metrics(session)
        after_arrival = page.evaluate(
            """
            () => ({
              longTaskCount: window.__fieldVitals.longTasks.length,
              eventCount: window.__fieldVitals.events.length,
            })
            """
        )

        page.evaluate(_frame_probe_script(RIPPLE_WAIT_MS))
        page.locator("[data-field-trigger]").click()
        if renderer == "baseline":
            page.wait_for_timeout(RIPPLE_WAIT_MS)
        else:
            page.wait_for_function(
                """
                () => {
                  const snapshot = window.__fieldResearch.snapshot();
                  return snapshot.waveRuns >= 2
                    && snapshot.activeAnimationHandles === 0
                    && snapshot.scheduledFrames === 0;
                }
                """,
                timeout=10_000,
            )
        ripple_intervals = page.evaluate("() => window.__frameProbe")
        after_ripple_metrics = _performance_metrics(session)
        payload = page.evaluate(
            """
            () => {
              const navigation = performance.getEntriesByType('navigation')[0];
              const vitals = window.__fieldVitals;
              const snapshot = window.__fieldResearch.snapshot();
              return {
                snapshot,
                navigation: {
                  domContentLoaded: navigation.domContentLoadedEventEnd,
                  load: navigation.loadEventEnd,
                  responseEnd: navigation.responseEnd,
                  encodedBodySize: navigation.encodedBodySize,
                  decodedBodySize: navigation.decodedBodySize,
                },
                vitals,
                focusableInField: document.querySelector('[data-field-surface]')
                  .querySelectorAll('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])').length,
                pointerEvents: getComputedStyle(document.querySelector('[data-field-surface]')).pointerEvents,
                descriptorPayload: (() => {
                  const block = document.querySelector('[data-field-descriptors]');
                  if (block) return JSON.parse(block.textContent);
                  const cells = [...document.querySelectorAll('[data-field-cell]')];
                  if (!cells.length) return null;
                  return cells.map((cell) => [
                    Number(cell.dataset.cellId),
                    Math.round(Number.parseFloat(cell.style.getPropertyValue('--cell-x')) * 1000000),
                    Math.round(Number.parseFloat(cell.style.getPropertyValue('--cell-y')) * 1000000),
                    Number.parseInt(cell.style.getPropertyValue('--cell-phase'), 10),
                    Number(cell.style.getPropertyValue('--cell-tone')),
                  ]);
                })(),
              };
            }
            """
        )
        if errors:
            msg = f"browser errors invalidated {profile.name}/{renderer}/{count}: {' | '.join(errors)}"
            raise RuntimeError(msg)
        snapshot = payload["snapshot"]
        expected_cells = 0 if renderer == "baseline" else count
        if snapshot["cellCount"] != expected_cells:
            msg = f"browser saw {snapshot['cellCount']} cells for {renderer}/{count}, expected {expected_cells}"
            raise RuntimeError(msg)
        actual_digest = None
        if renderer != "baseline":
            descriptor_payload = payload["descriptorPayload"]
            actual_digest = hashlib.sha256(json.dumps(descriptor_payload, separators=(",", ":")).encode()).hexdigest()
            if actual_digest != expected_digest or snapshot["descriptorSha256"] != expected_digest:
                msg = f"browser descriptor digest differed for {renderer}/{count}"
                raise RuntimeError(msg)
        if snapshot["activeAnimationHandles"] != 0 or snapshot["scheduledFrames"] != 0:
            msg = f"{renderer}/{count} retained animation work after the measured wave"
            raise RuntimeError(msg)
        if payload["focusableInField"] != 0 or payload["pointerEvents"] != "none":
            msg = f"decorative field exposed input for {renderer}/{count}"
            raise RuntimeError(msg)
        vitals = payload["vitals"]
        arrival_long_tasks = vitals["longTasks"][before_arrival["longTaskCount"] : after_arrival["longTaskCount"]]
        ripple_long_tasks = vitals["longTasks"][after_arrival["longTaskCount"] :]
        events = vitals["events"][after_arrival["eventCount"] :]
        click_durations = [float(event["duration"]) for event in events if event["name"] == "click"]
        arrival_frames = [float(value) for value in arrival_intervals]
        ripple_frames = [float(value) for value in ripple_intervals]
        if vitals["lcp"] is None:
            raise RuntimeError(f"browser reported no LCP for {profile.name}/{renderer}/{count}")
        if not click_durations:
            raise RuntimeError(f"browser reported no click timing for {profile.name}/{renderer}/{count}")
        if len(arrival_frames) < 2 or len(ripple_frames) < 2:
            raise RuntimeError(f"frame probe returned too little data for {profile.name}/{renderer}/{count}")
        return {
            "schema_version": 1,
            "renderer": renderer,
            "logical_cells": count,
            "profile": profile.name,
            "cohort": "timing",
            "block": block,
            "order": order,
            "valid": True,
            "invalid_reasons": [],
            "navigation": payload["navigation"],
            "lab_metrics": {
                "fcp_ms": next(
                    (
                        float(item["startTime"])
                        for item in vitals["paints"]
                        if item["name"] == "first-contentful-paint"
                    ),
                    None,
                ),
                "lcp_ms": vitals["lcp"],
                "cls": float(vitals["cls"]),
            },
            "dom": _dom_stats(page),
            "main_thread_load": _metric_delta(before, before_arrival_metrics),
            "waves": {
                "arrival": {
                    "front_ms": 1_600,
                    "settle_ms": 350,
                    "main_thread": _metric_delta(before_arrival_metrics, after_arrival_metrics),
                    "long_tasks": arrival_long_tasks,
                    "total_blocking_ms": sum(max(0, float(item["duration"]) - 50) for item in arrival_long_tasks),
                    "frame_diagnostics": {
                        "intervals_ms": arrival_frames,
                        "p95_ms": _nearest_percentile(arrival_frames, 0.95),
                        "max_gap_ms": max(arrival_frames, default=0),
                    },
                },
                "ripple": {
                    "front_ms": 550,
                    "settle_ms": 350,
                    "main_thread": _metric_delta(after_arrival_metrics, after_ripple_metrics),
                    "long_tasks": ripple_long_tasks,
                    "total_blocking_ms": sum(max(0, float(item["duration"]) - 50) for item in ripple_long_tasks),
                    "frame_diagnostics": {
                        "intervals_ms": ripple_frames,
                        "p95_ms": _nearest_percentile(ripple_frames, 0.95),
                        "max_gap_ms": max(ripple_frames, default=0),
                    },
                },
            },
            "interaction_proxy_ms": max(click_durations, default=0),
            "correctness": {
                "descriptor_sha256": snapshot["descriptorSha256"],
                "payload_descriptor_sha256": actual_digest,
                "active_animation_handles": snapshot["activeAnimationHandles"],
                "scheduled_frames": snapshot["scheduledFrames"],
                "focusable_in_field": payload["focusableInField"],
                "pointer_events": payload["pointerEvents"],
                "observer_dropped_entries": vitals["droppedEntries"],
            },
        }
    finally:
        context.close()


def _memory_snapshot(session: Any) -> dict[str, Any]:
    session.send("HeapProfiler.collectGarbage")
    heap = session.send("Runtime.getHeapUsage")
    dom = session.send("Memory.getDOMCounters")
    return {
        "used_heap_bytes": int(heap["usedSize"]),
        "total_heap_bytes": int(heap["totalSize"]),
        "documents": int(dom["documents"]),
        "nodes": int(dom["nodes"]),
        "js_event_listeners": int(dom["jsEventListeners"]),
    }


def _memory_sample(
    browser: Browser,
    base_url: str,
    profile: Profile,
    renderer: Renderer,
    count: int,
    round_index: int,
) -> dict[str, Any]:
    context = _new_context(browser, profile)
    page = context.new_page()
    errors = _page_errors(page)
    session = _configure_cdp(context, page, profile)
    try:
        page.goto(_url(base_url, renderer, count), wait_until="networkidle", timeout=30_000)
        _wait_ready(page)
        before = _memory_snapshot(session)
        page.evaluate("() => window.__fieldResearch.runFiveRipples()")
        after = _memory_snapshot(session)
        snapshot = page.evaluate("() => window.__fieldResearch.snapshot()")
        if errors:
            msg = f"browser errors invalidated memory sample {profile.name}/{renderer}/{count}: {' | '.join(errors)}"
            raise RuntimeError(msg)
        return {
            "renderer": renderer,
            "logical_cells": count,
            "profile": profile.name,
            "cohort": "retained-state",
            "round": round_index,
            "before": before,
            "after": after,
            "delta": {key: after[key] - before[key] for key in before},
            "field_snapshot": snapshot,
        }
    finally:
        context.close()


def _motion_lifecycle_correctness(
    browser: Browser,
    base_url: str,
    count: int,
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    desktop = PROFILES["desktop"]
    for renderer in cast("tuple[Renderer, ...]", ("dom", "canvas")):
        context = _new_context(browser, desktop)
        page = context.new_page()
        errors = _page_errors(page)
        session = _configure_cdp(context, page, desktop)
        try:
            page.goto(_url(base_url, renderer, count), wait_until="networkidle")
            _wait_ready(page)

            page.evaluate(
                """
                () => {
                  window.__pendingFieldWave = window.__fieldResearch.runWave({ frontMs: 550 });
                  return true;
                }
                """
            )
            page.wait_for_function("window.__fieldResearch.snapshot().activeAnimationHandles > 0")
            page.evaluate("window.__fieldResearch.setPaused(true)")
            page.wait_for_timeout(100)
            paused = page.evaluate(
                """
                () => ({
                  snapshot: window.__fieldResearch.snapshot(),
                  runningAnimations: document.getAnimations()
                    .filter((animation) => animation.playState === 'running').length,
                })
                """
            )
            page.evaluate("window.__fieldResearch.setPaused(false)")
            page.evaluate("() => window.__pendingFieldWave")
            page.evaluate("window.__fieldResearch.setPaused(true)")
            page.reload(wait_until="networkidle")
            _wait_ready(page)
            persisted = page.evaluate("() => window.__fieldResearch.snapshot()")
            page.evaluate("window.__fieldResearch.setPaused(false)")

            page.evaluate(
                """
                () => {
                  document.querySelector('.research-proof').style.minHeight = '300vh';
                  window.__pendingFieldWave = window.__fieldResearch.runWave({ frontMs: 550 });
                  return true;
                }
                """
            )
            page.wait_for_function("window.__fieldResearch.snapshot().activeAnimationHandles > 0")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_function("window.__fieldResearch.snapshot().visible === false")
            offscreen = page.evaluate(
                """
                () => ({
                  snapshot: window.__fieldResearch.snapshot(),
                  runningAnimations: document.getAnimations()
                    .filter((animation) => animation.playState === 'running').length,
                })
                """
            )
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_function("window.__fieldResearch.snapshot().visible === true")
            page.evaluate("() => window.__pendingFieldWave")

            page.evaluate(
                """
                () => {
                  window.__testVisibility = 'visible';
                  Object.defineProperty(document, 'visibilityState', {
                    configurable: true,
                    get: () => window.__testVisibility,
                  });
                  window.__pendingFieldWave = window.__fieldResearch.runWave({ frontMs: 550 });
                  return true;
                }
                """
            )
            page.wait_for_function("window.__fieldResearch.snapshot().activeAnimationHandles > 0")
            page.evaluate(
                """
                () => {
                  window.__testVisibility = 'hidden';
                  document.dispatchEvent(new Event('visibilitychange'));
                }
                """
            )
            page.wait_for_timeout(100)
            hidden = page.evaluate(
                """
                () => ({
                  snapshot: window.__fieldResearch.snapshot(),
                  runningAnimations: document.getAnimations()
                    .filter((animation) => animation.playState === 'running').length,
                })
                """
            )
            page.evaluate(
                """
                () => {
                  window.__testVisibility = 'visible';
                  document.dispatchEvent(new Event('visibilitychange'));
                }
                """
            )
            page.evaluate("() => window.__pendingFieldWave")

            before_cleanup = _memory_snapshot(session)
            page.evaluate(
                """
                () => {
                  window.__pendingFieldWave = window.__fieldResearch.runWave({ frontMs: 550 });
                  window.__fieldResearch.destroyForTest();
                  document.querySelector('[data-field-root]').remove();
                  return true;
                }
                """
            )
            page.wait_for_function("window.__fieldResearch === undefined")
            page.evaluate("() => window.__pendingFieldWave")
            after_cleanup = _memory_snapshot(session)
            cleanup = page.evaluate(
                """
                () => ({
                  apiRemoved: window.__fieldResearch === undefined,
                  rootRemoved: !document.querySelector('[data-field-root]'),
                  runningAnimations: document.getAnimations()
                    .filter((animation) => animation.playState === 'running').length,
                })
                """
            )
            cleanup["listenersBefore"] = before_cleanup["js_event_listeners"]
            cleanup["listenersAfter"] = after_cleanup["js_event_listeners"]
            results[renderer] = {
                "paused": paused,
                "pausePersisted": persisted,
                "offscreen": offscreen,
                "hiddenDocumentSimulated": hidden,
                "cleanup": cleanup,
                "errors": errors,
            }
        finally:
            context.close()
    return results


def _structural_correctness(browser: Browser, base_url: str, count: int) -> dict[str, Any]:
    results: dict[str, Any] = {}
    desktop = PROFILES["desktop"]
    for renderer in cast("tuple[Renderer, ...]", ("dom", "canvas")):
        context = _new_context(browser, desktop, java_script=False)
        page = context.new_page()
        try:
            page.goto(_url(base_url, renderer, count), wait_until="load")
            results[f"{renderer}_no_js"] = page.evaluate(
                """
                () => ({
                  heading: document.querySelector('h1')?.textContent.trim(),
                  primaryCta: Boolean(document.querySelector('.component-field__primary')),
                  surface: Boolean(document.querySelector('[data-field-surface]')),
                  domCells: document.querySelectorAll('[data-field-cell]').length,
                  fallback: (() => {
                    const plane = document.querySelector('.component-field__plane--canvas');
                    if (!plane) return null;
                    const style = getComputedStyle(plane, '::before');
                    return {
                      backgroundImage: style.backgroundImage,
                      content: style.content,
                      opacity: Number(style.opacity),
                    };
                  })(),
                })
                """
            )
        finally:
            context.close()

        context = _new_context(browser, desktop)
        page = context.new_page()
        page.emulate_media(reduced_motion="reduce")
        try:
            page.goto(_url(base_url, renderer, count), wait_until="networkidle")
            _wait_ready(page)
            outcome = page.evaluate("() => window.__fieldResearch.runWave()")
            results[f"{renderer}_reduced_motion"] = {
                "outcome": outcome,
                "snapshot": page.evaluate("() => window.__fieldResearch.snapshot()"),
            }
        finally:
            context.close()

        context = _new_context(browser, desktop)
        page = context.new_page()
        page.emulate_media(forced_colors="active")
        try:
            page.goto(_url(base_url, renderer, count), wait_until="networkidle")
            _wait_ready(page)
            results[f"{renderer}_forced_colors"] = page.evaluate(
                """
                () => ({
                  copyVisible: getComputedStyle(document.querySelector('.component-field__copy')).display !== 'none',
                  planeDisplay: getComputedStyle(document.querySelector('[data-field-plane]')).display,
                })
                """
            )
        finally:
            context.close()

        context = _new_context(browser, desktop)
        page = context.new_page()
        try:
            page.goto(_url(base_url, renderer, count), wait_until="networkidle")
            _wait_ready(page)
            page.locator(".component-field__primary").focus()
            page.keyboard.press("Tab")
            trigger_focused = page.locator("[data-field-trigger]").evaluate(
                "element => element === document.activeElement"
            )
            page.keyboard.press("Enter")
            if renderer != "baseline":
                page.wait_for_function("window.__fieldResearch.snapshot().waveRuns >= 1")
            page.set_viewport_size({"width": 320, "height": 700})
            page.evaluate("document.documentElement.style.fontSize = '200%'")
            page.wait_for_timeout(100)
            reflow = page.evaluate(
                """
                () => {
                  const viewportWidth = document.documentElement.clientWidth;
                  const overflowers = [...document.querySelectorAll('body *')]
                    .map((element) => {
                      const bounds = element.getBoundingClientRect();
                      return {
                        tag: element.tagName.toLowerCase(),
                        className: typeof element.className === 'string' ? element.className : '',
                        left: Math.round(bounds.left),
                        right: Math.round(bounds.right),
                        width: Math.round(bounds.width),
                      };
                    })
                    .filter((item) => item.left < -1 || item.right > viewportWidth + 1)
                    .slice(0, 12);
                  const internallyWide = [...document.querySelectorAll('body *')]
                    .filter((element) => element.scrollWidth > element.clientWidth + 1)
                    .map((element) => ({
                      tag: element.tagName.toLowerCase(),
                      className: typeof element.className === 'string' ? element.className : '',
                      clientWidth: element.clientWidth,
                      scrollWidth: element.scrollWidth,
                      overflowX: getComputedStyle(element).overflowX,
                    }))
                    .slice(0, 12);
                  return {
                    noHorizontalOverflow: document.documentElement.scrollWidth <= viewportWidth,
                    viewportWidth,
                    scrollWidth: document.documentElement.scrollWidth,
                    bodyScrollWidth: document.body.scrollWidth,
                    overflowers,
                    internallyWide,
                  };
                }
                """
            )
            results[f"{renderer}_keyboard_reflow"] = {
                "triggerFocused": trigger_focused,
                "headingVisible": page.locator("h1").is_visible(),
                **reflow,
            }
        finally:
            context.close()

    context = _new_context(browser, desktop)
    context.add_init_script("HTMLCanvasElement.prototype.getContext = () => null")
    page = context.new_page()
    try:
        page.goto(_url(base_url, "canvas", count), wait_until="networkidle")
        _wait_ready(page)
        results["canvas_context_failure"] = page.evaluate(
            """
            () => {
              window.__fieldResearch.setPaused(true);
              window.__fieldResearch.setPaused(false);
              return {
                ready: window.__fieldResearch.ready,
                snapshot: window.__fieldResearch.snapshot(),
                rootState: document.querySelector('[data-field-root]').dataset.fieldReady,
                status: document.querySelector('[data-field-status]').textContent.trim(),
                triggerDisabled: document.querySelector('[data-field-trigger]').disabled,
                pauseDisabled: document.querySelector('[data-field-pause]').disabled,
              };
            }
            """
        )
    finally:
        context.close()

    context = _new_context(browser, desktop)
    page = context.new_page()
    try:
        page.goto(_url(base_url, "canvas", count, "?fault=corrupt"), wait_until="networkidle")
        _wait_ready(page)
        results["canvas_corrupt_descriptors"] = page.evaluate(
            """
            () => {
              window.__fieldResearch.setPaused(true);
              window.__fieldResearch.setPaused(false);
              return {
                ready: window.__fieldResearch.ready,
                snapshot: window.__fieldResearch.snapshot(),
                rootState: document.querySelector('[data-field-root]').dataset.fieldReady,
                status: document.querySelector('[data-field-status]').textContent.trim(),
                triggerDisabled: document.querySelector('[data-field-trigger]').disabled,
                pauseDisabled: document.querySelector('[data-field-pause]').disabled,
              };
            }
            """
        )
    finally:
        context.close()

    context = _new_context(browser, desktop)
    page = context.new_page()
    try:
        page.goto(_url(base_url, "canvas", count, "?fault=mutate"), wait_until="networkidle")
        _wait_ready(page)
        results["canvas_mutated_descriptors"] = page.evaluate(
            """
            () => ({
              ready: window.__fieldResearch.ready,
              snapshot: window.__fieldResearch.snapshot(),
              rootState: document.querySelector('[data-field-root]').dataset.fieldReady,
            })
            """
        )
    finally:
        context.close()

    context = browser.new_context(
        viewport={"width": 2400, "height": 1600},
        device_scale_factor=3,
        color_scheme="dark",
    )
    page = context.new_page()
    try:
        page.goto(_url(base_url, "canvas", count), wait_until="networkidle")
        _wait_ready(page)
        before = page.evaluate("() => window.__fieldResearch.snapshot()")
        page.set_viewport_size({"width": 900, "height": 700})
        page.wait_for_timeout(150)
        after = page.evaluate("() => window.__fieldResearch.snapshot()")
        results["canvas_dpr_resize"] = {"before": before, "after": after}
    finally:
        context.close()

    results["motion_lifecycle"] = _motion_lifecycle_correctness(browser, base_url, count)
    return results


def _correctness_gates(results: dict[str, Any], count: int) -> dict[str, dict[str, bool]]:
    gates: dict[str, dict[str, bool]] = {}
    for renderer in cast("tuple[Renderer, ...]", ("dom", "canvas")):
        no_js = results[f"{renderer}_no_js"]
        reduced = results[f"{renderer}_reduced_motion"]["snapshot"]
        forced = results[f"{renderer}_forced_colors"]
        reflow = results[f"{renderer}_keyboard_reflow"]
        motion = results["motion_lifecycle"][renderer]
        renderer_gates = {
            "no_js_content": (
                no_js["heading"] == "Build the frontend in Python." and no_js["primaryCta"] and no_js["surface"]
            ),
            "no_js_field": no_js["domCells"] == count
            if renderer == "dom"
            else bool(
                no_js["fallback"]
                and no_js["fallback"]["backgroundImage"] != "none"
                and no_js["fallback"]["opacity"] > 0
            ),
            "reduced_motion": (
                reduced["cellCount"] == count
                and reduced["reducedMotion"]
                and reduced["activeAnimationHandles"] == 0
                and reduced["scheduledFrames"] == 0
            ),
            "forced_colors": forced["copyVisible"] and forced["planeDisplay"] == "none",
            "keyboard_and_reflow": (
                reflow["triggerFocused"] and reflow["headingVisible"] and reflow["noHorizontalOverflow"]
            ),
            "pause_and_session_persistence": (
                motion["paused"]["snapshot"]["paused"]
                and motion["paused"]["snapshot"]["scheduledFrames"] == 0
                and motion["paused"]["runningAnimations"] == 0
                and motion["pausePersisted"]["paused"]
                and motion["pausePersisted"]["activeAnimationHandles"] == 0
                and motion["pausePersisted"]["scheduledFrames"] == 0
            ),
            "offscreen_suspension": (
                not motion["offscreen"]["snapshot"]["visible"]
                and motion["offscreen"]["snapshot"]["scheduledFrames"] == 0
                and motion["offscreen"]["runningAnimations"] == 0
            ),
            "hidden_document_suspension": (
                motion["hiddenDocumentSimulated"]["snapshot"]["scheduledFrames"] == 0
                and motion["hiddenDocumentSimulated"]["runningAnimations"] == 0
            ),
            "controller_cleanup": (
                motion["cleanup"]["apiRemoved"]
                and motion["cleanup"]["rootRemoved"]
                and motion["cleanup"]["runningAnimations"] == 0
                and motion["cleanup"]["listenersAfter"] <= motion["cleanup"]["listenersBefore"]
                and not motion["errors"]
            ),
        }
        if renderer == "canvas":
            context_failure = results["canvas_context_failure"]
            corrupt = results["canvas_corrupt_descriptors"]
            mutated = results["canvas_mutated_descriptors"]
            resized = results["canvas_dpr_resize"]
            renderer_gates.update(
                {
                    "canvas_context_fallback": (
                        not context_failure["ready"]
                        and context_failure["rootState"] == "fallback"
                        and context_failure["status"] == "Static component field fallback active."
                        and context_failure["triggerDisabled"]
                        and context_failure["pauseDisabled"]
                        and context_failure["snapshot"]["activeAnimationHandles"] == 0
                        and context_failure["snapshot"]["scheduledFrames"] == 0
                    ),
                    "corrupt_descriptor_fallback": (
                        not corrupt["ready"]
                        and corrupt["rootState"] == "fallback"
                        and corrupt["status"] == "Static component field fallback active."
                        and corrupt["triggerDisabled"]
                        and corrupt["pauseDisabled"]
                        and corrupt["snapshot"]["cellCount"] == 0
                        and corrupt["snapshot"]["activeAnimationHandles"] == 0
                        and corrupt["snapshot"]["scheduledFrames"] == 0
                    ),
                    "descriptor_digest_fallback": (
                        not mutated["ready"]
                        and mutated["rootState"] == "fallback"
                        and mutated["snapshot"]["cellCount"] == 0
                        and "digest mismatch" in mutated["snapshot"]["initializationError"]
                    ),
                    "bounded_canvas_allocation": all(
                        snapshot["effectiveDpr"] <= 2 and snapshot["backingPixels"] <= MAX_CANVAS_PIXELS
                        for snapshot in (resized["before"], resized["after"])
                    )
                    and resized["before"]["effectiveDpr"] < 2,
                }
            )
        gates[renderer] = renderer_gates
    return gates


def _cross_browser_smoke(playwright: Playwright, base_url: str, count: int) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for browser_name in ("firefox", "webkit"):
        browser_type = getattr(playwright, browser_name)
        browser = browser_type.launch(headless=True)
        try:
            browser_results: dict[str, Any] = {"version": browser.version, "renderers": {}}
            for renderer in cast("tuple[Renderer, ...]", ("dom", "canvas")):
                context = browser.new_context(viewport={"width": 1280, "height": 800}, color_scheme="dark")
                page = context.new_page()
                errors = _page_errors(page)
                try:
                    page.goto(_url(base_url, renderer, count), wait_until="networkidle")
                    _wait_ready(page)
                    page.evaluate("() => window.__fieldResearch.runWave({ frontMs: 100 })")
                    page.set_viewport_size({"width": 800, "height": 700})
                    page.wait_for_timeout(100)
                    browser_results["renderers"][renderer] = {
                        "errors": errors,
                        "snapshot": page.evaluate("() => window.__fieldResearch.snapshot()"),
                    }
                finally:
                    context.close()
            results[browser_name] = browser_results
        finally:
            browser.close()
    return results


def _summarize(
    samples: list[dict[str, Any]],
    server: dict[str, Any],
    memory: list[dict[str, Any]],
    profiles: list[Profile],
    counts: list[int],
    resamples: int,
    correctness_gates: dict[str, dict[str, bool]],
    expected_rounds: int,
    expected_memory_rounds: int,
) -> dict[str, Any]:
    output: dict[str, Any] = {"profiles": {}, "server": {}, "feasible_frontier": {}}
    for profile in profiles:
        profile_result: dict[str, Any] = {}
        profile_samples = [sample for sample in samples if sample["profile"] == profile.name]
        for count in counts:
            baseline_by_block = {
                sample["block"]: sample
                for sample in profile_samples
                if sample["renderer"] == "baseline" and sample["logical_cells"] == count and sample["valid"]
            }
            count_result: dict[str, Any] = {}
            for renderer in cast("tuple[Renderer, ...]", ("dom", "canvas")):
                all_selected = [
                    sample
                    for sample in profile_samples
                    if sample["renderer"] == renderer and sample["logical_cells"] == count
                ]
                selected = [sample for sample in all_selected if sample["valid"]]
                lcp = [float(sample["lab_metrics"]["lcp_ms"] or 0) for sample in selected]
                cls = [float(sample["lab_metrics"]["cls"]) for sample in selected]
                interaction = [float(sample["interaction_proxy_ms"]) for sample in selected]
                blocking = [
                    max(float(wave["total_blocking_ms"]) for wave in sample["waves"].values()) for sample in selected
                ]
                frame_gap = [
                    max(float(wave["frame_diagnostics"]["max_gap_ms"]) for wave in sample["waves"].values())
                    for sample in selected
                ]
                long_task_max = [
                    max(
                        (float(item["duration"]) for wave in sample["waves"].values() for item in wave["long_tasks"]),
                        default=0,
                    )
                    for sample in selected
                ]
                lcp_deltas = [
                    float(sample["lab_metrics"]["lcp_ms"] or 0)
                    - float(baseline_by_block[sample["block"]]["lab_metrics"]["lcp_ms"] or 0)
                    for sample in selected
                    if sample["block"] in baseline_by_block
                ]
                server_record = server[renderer][str(count)]
                baseline_record = server["baseline"][str(count)]
                raw_delta = int(server_record["html_raw_bytes"]) - int(baseline_record["html_raw_bytes"])
                gzip_delta = int(server_record["html_gzip_bytes"]) - int(baseline_record["html_gzip_bytes"])
                all_memory_selected = [
                    item
                    for item in memory
                    if item["profile"] == profile.name
                    and item["renderer"] == renderer
                    and item["logical_cells"] == count
                ]
                memory_selected = [item for item in all_memory_selected if item["valid"]]
                retained_ok = (
                    all(
                        item["delta"]["nodes"] == 0
                        and item["delta"]["js_event_listeners"] == 0
                        and item["field_snapshot"]["activeAnimationHandles"] == 0
                        and item["field_snapshot"]["scheduledFrames"] == 0
                        for item in memory_selected
                    )
                    and len(memory_selected) == expected_memory_rounds
                )
                gates = {
                    "complete_valid_cohort": (
                        len(selected) == expected_rounds and len(baseline_by_block) == expected_rounds
                    ),
                    "payload_raw": raw_delta <= 300 * 1024,
                    "payload_gzip": gzip_delta <= 32 * 1024,
                    "lab_lcp": _nearest_percentile(lcp, 0.75) <= profile.lcp_budget_ms,
                    "lab_cls": max(cls, default=0) <= 0.01,
                    "interaction_p75": _nearest_percentile(interaction, 0.75) <= 150,
                    "interaction_max": max(interaction, default=0) <= 200,
                    "long_task_max": max(long_task_max, default=0) < 100,
                    "blocking_p75": _nearest_percentile(blocking, 0.75) <= profile.blocking_budget_ms,
                    "frame_gap": max(frame_gap, default=0) < 100,
                    "retained_resources": retained_ok,
                    **correctness_gates[renderer],
                }
                count_result[renderer] = {
                    "metrics": {
                        "lab_lcp_ms": _summary(lcp),
                        "lab_cls": _summary(cls),
                        "interaction_proxy_ms": _summary(interaction),
                        "worst_wave_total_blocking_ms": _summary(blocking),
                        "worst_wave_max_frame_gap_ms": _summary(frame_gap),
                        "worst_wave_max_long_task_ms": _summary(long_task_max),
                        "baseline_relative_lcp_ms": _summary(lcp_deltas),
                        "baseline_relative_lcp_bootstrap_95": _bootstrap_median_interval(lcp_deltas, resamples),
                        "additional_raw_html_bytes": raw_delta,
                        "additional_gzip_html_bytes": gzip_delta,
                        "invalid_samples": [
                            sample["invalid_reasons"] for sample in all_selected if not sample["valid"]
                        ],
                        "invalid_memory_samples": [
                            sample["invalid_reasons"] for sample in all_memory_selected if not sample["valid"]
                        ],
                    },
                    "gates": gates,
                    "passes": all(gates.values()),
                }
            profile_result[str(count)] = count_result
        output["profiles"][profile.name] = profile_result

    for renderer in cast("tuple[Renderer, ...]", ("dom", "canvas")):
        passing = [
            count
            for count in counts
            if all(output["profiles"][profile.name][str(count)][renderer]["passes"] for profile in profiles)
        ]
        output["feasible_frontier"][renderer] = max(passing, default=None)

    for renderer in cast("tuple[Renderer, ...]", ("dom", "canvas")):
        output["server"][renderer] = {}
        for count in counts:
            record = server[renderer][str(count)]
            output["server"][renderer][str(count)] = {
                "fresh_process_render": record["fresh_process_render"],
                "warm_render": record["warm_render"],
                "orientation_targets": {
                    "fresh_median_under_500_ms": float(record["fresh_process_render"]["median"] or 0) <= 500,
                    "warm_median_under_100_ms": float(record["warm_render"]["median"] or 0) <= 100,
                },
            }
    return output


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    counts = list(args.counts)
    profiles = [PROFILES[name] for name in args.profiles]
    server_metrics = _collect_server_metrics(
        counts,
        processes=args.server_processes,
        warmups=args.server_warmups,
        samples_per_process=args.server_samples,
    )
    samples: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    correctness: dict[str, Any] = {}
    correctness_gates: dict[str, dict[str, bool]] = {}
    cross_browser: dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="citry-field-proof-") as temporary:
        site_root = Path(temporary)
        page_counts = sorted({*counts, args.correctness_count})
        _write_pages(site_root, page_counts)
        with _StaticServer(site_root) as server, sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=not args.headful)
            try:
                gpu_info = None
                try:
                    system = browser.new_browser_cdp_session().send("SystemInfo.getInfo")
                    gpu_info = system.get("gpu", {}).get("devices", [])
                except Exception:  # noqa: BLE001
                    gpu_info = None

                for profile in profiles:
                    warm_context = _new_context(browser, profile)
                    warm_page = warm_context.new_page()
                    warm_session = _configure_cdp(warm_context, warm_page, profile)
                    del warm_session
                    try:
                        warm_page.goto(_url(server.base_url, "baseline", counts[0]), wait_until="networkidle")
                        _wait_ready(warm_page)
                    finally:
                        warm_context.close()

                    cases = [(renderer, count) for renderer in RENDERERS for count in counts]
                    for block in range(args.rounds):
                        ordered = list(cases)
                        random.Random(ORDER_SEED + block).shuffle(ordered)  # noqa: S311 - fixed study order
                        for order, (renderer, count) in enumerate(ordered):
                            try:
                                sample = _timing_sample(
                                    browser,
                                    server.base_url,
                                    profile,
                                    renderer,
                                    count,
                                    block,
                                    order,
                                )
                            except Exception as error:  # noqa: BLE001 - invalid samples are retained as evidence
                                print(
                                    f"invalid timing sample {profile.name}/{renderer}/{count}/block-{block}: {error}",
                                    file=sys.stderr,
                                )
                                sample = {
                                    "schema_version": 1,
                                    "renderer": renderer,
                                    "logical_cells": count,
                                    "profile": profile.name,
                                    "cohort": "timing",
                                    "block": block,
                                    "order": order,
                                    "valid": False,
                                    "invalid_reasons": [f"{type(error).__name__}: {error}"],
                                }
                            samples.append(sample)

                    for renderer in cast("tuple[Renderer, ...]", ("dom", "canvas")):
                        for count in counts:
                            for round_index in range(args.memory_rounds):
                                try:
                                    memory_sample = _memory_sample(
                                        browser,
                                        server.base_url,
                                        profile,
                                        renderer,
                                        count,
                                        round_index,
                                    )
                                    memory_sample["valid"] = True
                                    memory_sample["invalid_reasons"] = []
                                except Exception as error:  # noqa: BLE001 - retained as failed evidence
                                    print(
                                        "invalid memory sample "
                                        f"{profile.name}/{renderer}/{count}/round-{round_index}: "
                                        f"{error}",
                                        file=sys.stderr,
                                    )
                                    memory_sample = {
                                        "renderer": renderer,
                                        "logical_cells": count,
                                        "profile": profile.name,
                                        "cohort": "retained-state",
                                        "round": round_index,
                                        "valid": False,
                                        "invalid_reasons": [f"{type(error).__name__}: {error}"],
                                    }
                                retained.append(memory_sample)

                correctness = _structural_correctness(browser, server.base_url, args.correctness_count)
                correctness_gates = _correctness_gates(correctness, args.correctness_count)
            finally:
                browser.close()

            if args.cross_browser:
                cross_browser = _cross_browser_smoke(playwright, server.base_url, args.correctness_count)

    summary = _summarize(
        samples,
        server_metrics,
        retained,
        profiles,
        counts,
        args.bootstrap_resamples,
        correctness_gates,
        args.rounds,
        args.memory_rounds,
    )
    return {
        "schema_version": 1,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "metadata": {
            "git": _git_revision(),
            "fixture_sha256": component_fixture_sha256(),
            "harness_sha256": _file_sha256(Path(__file__).resolve()),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "host_memory_bytes": _host_memory_bytes(),
            "playwright": importlib.metadata.version("playwright"),
            "chromium": samples and args.browser_version,
            "gpu": gpu_info,
            "headful": args.headful,
            "release_build_attested": args.release_build_attested,
            "timing_policy": "one suite warmup; paired deterministic shuffle; retain every valid measured sample",
            "bootstrap_seed": BOOTSTRAP_SEED,
            "order_seed": ORDER_SEED,
            "rounds": args.rounds,
            "memory_rounds": args.memory_rounds,
            "correctness_count": args.correctness_count,
            "effective_arguments": {
                "counts": counts,
                "profiles": [profile.name for profile in profiles],
                "rounds": args.rounds,
                "memory_rounds": args.memory_rounds,
                "server_processes": args.server_processes,
                "server_warmups": args.server_warmups,
                "server_samples": args.server_samples,
                "bootstrap_resamples": args.bootstrap_resamples,
                "correctness_count": args.correctness_count,
                "cross_browser": args.cross_browser,
                "release_build_attested": args.release_build_attested,
                "headful": args.headful,
            },
        },
        "profiles": [asdict(profile) for profile in profiles],
        "server": server_metrics,
        "samples": samples,
        "retained_state": retained,
        "correctness": correctness,
        "correctness_gates": correctness_gates,
        "cross_browser": cross_browser,
        "summary": summary,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", type=int, nargs="+", default=list(SUPPORTED_COUNTS))
    parser.add_argument("--profiles", nargs="+", choices=sorted(PROFILES), default=["desktop", "mobile"])
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--memory-rounds", type=int, default=1)
    parser.add_argument("--server-processes", type=int, default=3)
    parser.add_argument("--server-warmups", type=int, default=5)
    parser.add_argument("--server-samples", type=int, default=5)
    parser.add_argument("--bootstrap-resamples", type=int, default=10_000)
    parser.add_argument("--correctness-count", type=int, choices=SUPPORTED_COUNTS, default=1_024)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--headful", action="store_true")
    parser.add_argument("--cross-browser", action="store_true")
    parser.add_argument("--release-build-attested", action="store_true")
    parser.add_argument("--_render-case", nargs=2, metavar=("RENDERER", "COUNT"), help=argparse.SUPPRESS)
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    if args._render_case:
        renderer_raw, count_raw = args._render_case
        if renderer_raw not in RENDERERS:
            parser.error(f"renderer must be one of {RENDERERS}")
        renderer = cast("Renderer", renderer_raw)
        result = _render_case(renderer, int(count_raw), args.server_warmups, args.server_samples)
        print(json.dumps(result, separators=(",", ":")))
        return
    if args.rounds < 1 or args.memory_rounds < 1 or args.server_processes < 1:
        parser.error("round and process counts must be positive")
    invalid_counts = sorted(set(args.counts) - set(SUPPORTED_COUNTS))
    if invalid_counts:
        parser.error(f"counts must come from {SUPPORTED_COUNTS}, got {invalid_counts}")

    result: dict[str, Any]
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            args.browser_version = browser.version
            browser.close()
        result = run_probe(args)
    except Exception as error:
        print(f"component-field probe failed: {error}", file=sys.stderr)
        raise

    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        destination = args.output if args.output.is_absolute() else PROBE_DIR / args.output
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(encoded + "\n", encoding="utf-8")
        print(destination)
    else:
        print(encoded)


if __name__ == "__main__":
    main()
