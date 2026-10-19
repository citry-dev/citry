"""Measure stored browser marks and validate the resulting interface afterward."""

import importlib.util
import json
import math
import re
import sys
import urllib.request
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import urlencode, urlsplit

from playwright.sync_api import Browser, Error, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from citry_bench.config import WEB, initial_rendering
from citry_bench.network import Network
from citry_bench.results import append

SCRIPT = Path(__file__).with_name("instrumentation.js").read_text()


def server_render_time(payload: dict, rendering: str, *, initial: bool = True) -> tuple[float | None, str]:
    """Sum explicit HTML-render spans; missing data never becomes zero."""
    if rendering == "browser":
        return None, "not-applicable"
    if rendering == "hybrid" and not initial:
        return None, "not-applicable"
    values = []
    for entry in payload["server_timings"]:
        header = entry.get("header", "")
        metrics = re.findall(r"(?:^|,)\s*render\s*;\s*dur=([^;,\s]+)", header)
        if len(metrics) > 1:
            raise ValueError("Duplicate render timing in a response")
        for metric in metrics:
            value = float(metric)
            if not math.isfinite(value) or value < 0:
                raise ValueError("Render timing must be finite and nonnegative")
            values.append(value)
    return (sum(values), "measured") if values else (None, "missing")


def server_prepare_kind(adapter: dict, *, initial: bool = True) -> str:
    rendering = adapter.get("rendering", "server")
    if rendering in ("server", "hybrid") and initial:
        return "html"
    if rendering == "hybrid":
        return adapter["update_payload"]
    return "delta" if adapter.get("transport", "http") == "websocket" else "json"


def server_prepare_time(
    payload: dict, rendering: str, render_ms: float | None, *, initial: bool = True
) -> tuple[float | None, str, str | None]:
    value = payload["server_prepare_ms"]
    status = payload["server_prepare_status"]
    reason = payload["server_prepare_reason"]
    # The HTML adapters' existing render span already covers construction and
    # serialization of their emitted output.
    if rendering in ("server", "hybrid") and initial and status == "missing" and render_ms is not None:
        return render_ms, "measured", None
    return value, status, reason


PAINT_READ_TIMEOUT_MS = 5000


def _paint_time(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and value >= 0 else None


def paint_fields(raw: object, *, read_error: str | None = None) -> dict:
    """Turn the browser's finalized paint record into additive sample fields.

    Every time is milliseconds since navigation start, the zero of
    `ready_elapsed_ms` and `layout_inclusive_elapsed_ms` for an initial load.
    A value the browser did not report stays None with a reason; it never
    becomes zero.
    """

    def unavailable(reason: str) -> dict:
        return {
            "fcp_ms": None,
            "fcp_status": "unavailable",
            "fcp_reason": reason,
            "lcp_ms": None,
            "lcp_status": "unavailable",
            "lcp_reason": reason,
            "paint_timing": None,
        }

    if read_error is not None:
        return unavailable(f"paint timing read failed: {read_error}")
    if not isinstance(raw, dict) or raw.get("time_origin") != "navigation-start":
        return unavailable("paint timing record is missing or malformed")
    supported = raw.get("supported") if isinstance(raw.get("supported"), dict) else {}
    errors = [str(error) for error in raw.get("errors") or []]
    finalized = _paint_time(raw.get("finalized_ms"))
    first_input = raw.get("first_input") if isinstance(raw.get("first_input"), dict) else None
    lcp = raw.get("lcp") if isinstance(raw.get("lcp"), dict) else None
    result = {
        "paint_timing": {
            "time_origin": "navigation-start",
            "finalized_ms": finalized,
            "request_start_ms": _paint_time(raw.get("request_start_ms")),
            "lcp_candidates": raw.get("lcp_candidates"),
            "lcp_size": lcp.get("size") if lcp else None,
            "lcp_element": lcp.get("element") if lcp else None,
            "first_input": first_input,
            "errors": errors,
        }
    }

    def measure(name: str, entry_type: str, value: object, missing: str) -> None:
        reason = None
        if finalized is None:
            reason = "paint timing was not finalized"
        elif not supported.get(entry_type):
            reason = f"browser does not support {entry_type} entries"
        elif any(error.startswith(f"{entry_type}:") for error in errors):
            reason = f"{entry_type} observer failed"
        elif value is None:
            reason = missing
        elif _paint_time(value) is None:
            reason = f"{name.upper()} value is not a finite nonnegative time"
        # The paint happened before finalization by construction; a later time
        # means the record is inconsistent.
        elif _paint_time(value) > finalized:
            reason = f"{name.upper()} is later than finalization"
        result[f"{name}_ms"] = None if reason else _paint_time(value)
        result[f"{name}_status"] = "unavailable" if reason else "measured"
        result[f"{name}_reason"] = reason

    measure("fcp", "paint", raw.get("fcp_ms"), "no first-contentful-paint entry before finalization")
    measure(
        "lcp",
        "largest-contentful-paint",
        lcp.get("start_ms") if lcp else None,
        "no largest-contentful-paint candidate before finalization",
    )
    # Chromium stops LCP at the first input, so a candidate seen before an
    # earlier input may not be the page's largest paint.
    if first_input is not None and result["lcp_status"] == "measured":
        result["lcp_ms"] = None
        result["lcp_status"] = "unavailable"
        result["lcp_reason"] = f"{first_input.get('type', 'input')} before finalization stopped LCP reporting"
    return result


def read_paint_timing(page: Page) -> dict:
    """Finalize the page's paint observers and return the sample fields.

    Call this before anything clicks, types or scrolls in the page: Chromium
    stops reporting LCP candidates at the first input.
    """
    try:
        raw = page.evaluate(
            """timeout => Promise.race([
              window.__citryBench.paintTimings(),
              new Promise((_, reject) => setTimeout(
                () => reject(new Error('paint timing finalization timed out')), timeout)),
            ])""",
            PAINT_READ_TIMEOUT_MS,
        )
    except Error as error:
        return paint_fields(None, read_error=str(error).splitlines()[0])
    return paint_fields(raw)


def module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load scenario module: {path}")
    result = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(result)
    finally:
        sys.path.pop(0)
    return result


def mark(page: Page, operation: str, timeout: int) -> dict:
    page.wait_for_function(
        "op => window.__citryBench?.marks.some(mark => mark.operation === op) || window.__citryBench?.faults.length",
        arg=operation,
        timeout=timeout,
    )
    state = page.evaluate("() => ({marks: window.__citryBench.marks, faults: window.__citryBench.faults})")
    if state["faults"]:
        raise AssertionError(f"Readiness instrumentation faults: {state['faults']}")
    result = next(m for m in state["marks"] if m["operation"] == operation)
    if result["end"] < result["start"]:
        raise AssertionError("Readiness precedes the triggering event")
    if not isinstance(result.get("layout_end"), (int, float)) or result["layout_end"] < result["end"]:
        raise AssertionError("Layout opportunity endpoint is missing or precedes readiness")
    if not math.isclose(result.get("layout_extra_ms", -1), result["layout_end"] - result["end"], abs_tol=1e-6):
        raise AssertionError("Stored extra layout wait does not match the ready/layout boundaries")
    geometry = result.get("layout_geometry")
    if (
        not isinstance(geometry, dict)
        or not isinstance(geometry.get("board"), dict)
        or not isinstance(geometry.get("last_row"), dict)
        or not geometry.get("row_count")
    ):
        raise AssertionError("Layout opportunity geometry evidence is incomplete")
    if operation != "initial" and not result["event"]["trusted"]:
        raise AssertionError("Measured UI event was not trusted")
    return result


def capture(page: Page, ready: dict) -> dict:
    # Capture bytes only after the endpoint, before correctness probes mutate state.
    result = page.evaluate("""() => {
      const board = document.querySelector('#board');
      const type = document.doctype;
      const doctype = type ? new XMLSerializer().serializeToString(type) : '';
      return {
        html: doctype + document.documentElement.outerHTML,
        revision: Number(board?.dataset.revision),
        operation: board?.dataset.operation,
        resources: performance.getEntriesByType('resource').map(e => e.toJSON()),
        navigation: performance.getEntriesByType('navigation').map(e => e.toJSON()),
        transport: window.__citryBench.connections(),
        marks: window.__citryBench.marks,
        shadowRoots: Array.from(document.querySelectorAll('*')).filter(e => e.shadowRoot).length,
      };
    }""")
    if result["revision"] != ready["state"]["revision"] or result["operation"] != ready["operation"]:
        raise AssertionError("DOM revision changed between readiness and HTML capture")
    result["final_html_bytes"] = len(result["html"].encode("utf-8"))
    return result


def write_diagnostic_capture(
    directory: Path,
    session: str,
    index: int,
    operation: str,
    status: str,
    page_errors: list[str],
    network: Network,
) -> None:
    """Retain network details only for an operation that did not complete correctly."""
    if status == "ok":
        return
    captures = directory / "captures"
    captures.mkdir(exist_ok=True)
    (captures / f"{session}-{index}-failure.json").write_text(
        json.dumps(
            {
                "errors": page_errors,
                "http": [entry for entry in network.raw if entry["operation"] == operation],
                "sockets": [entry for entry in network.sockets if entry["operation"] == operation],
            },
            indent=2,
        )
    )


def stored_sample(row: dict) -> dict:
    """Remove the in-memory semantic oracle from a successful sample."""
    result = dict(row)
    if result["status"] == "ok" and isinstance(result.get("ready"), dict):
        result["ready"] = {key: value for key, value in result["ready"].items() if key != "semantic"}
    return result


def session_sequence(settings: dict, actions: ModuleType, *, initial_only: bool = False) -> list[dict]:
    """Build one page load's fixed operation order."""
    sequence = [{"name": "initial"}]
    if initial_only:
        return sequence
    for cycle in range(settings["warmups"] + settings["cycles"]):
        sequence.extend(
            {**action, "cycle": cycle, "warmup": cycle < settings["warmups"]} for action in actions.ACTIONS
        )
    return sequence


def record_not_run_session(settings: dict, directory: Path, info: dict, *, reason: str) -> None:
    """Retain the operations omitted after a failed first page load."""
    actions = module(WEB / "scenarios" / settings["scenario"] / "actions.py")
    for action in session_sequence(settings, actions):
        append(
            directory / "samples.jsonl",
            {
                **info,
                "action": action["name"],
                "cycle": action.get("cycle"),
                "warmup": action.get("warmup", False),
                "status": "not-run",
                "reason": reason,
                "elapsed_ms": None,
            },
        )


def collect_network_then_heap_after_gc(
    network: Network,
    memory_observer: Any,
    page: Page,
    operation: str,
    ready: dict,
    snapshot: dict,
    audit: dict | None,
    *,
    read_heap_after_gc: bool,
) -> dict:
    """Read the observation's network accounting, then take the after-GC heap reading.

    Forced garbage collection makes Chromium drop some script bodies it has
    already received, so network accounting must read the response bodies
    first. Only a page's last observation takes the after-GC reading.
    """
    payload = network.collect(operation, ready, snapshot, audit)
    if memory_observer is not None and read_heap_after_gc:
        memory_observer.read_heap_after_gc(operation, page)
    return payload


def run_session(
    browser: Browser,
    base: str,
    settings: dict,
    directory: Path,
    info: dict,
    *,
    adapter: dict | None = None,
    initial_only: bool = False,
    memory_observer: object | None = None,
) -> bool:
    scenario = WEB / "scenarios" / settings["scenario"]
    actions = module(scenario / "actions.py")
    assertions = module(scenario / "assertions.py")
    initial_expected = assertions.initial_expected(info["count"])
    session = info["session"]
    page_errors = []
    context = browser.new_context(
        viewport={"width": 1440, "height": 1000},
        device_scale_factor=1,
        locale="en-US",
        timezone_id="UTC",
        reduced_motion="reduce",
        service_workers="block",
    )
    context.add_init_script(SCRIPT)
    page = context.new_page()
    # Initial readiness can fire during navigation, so install its independent
    # expected state before any application code runs.
    page.add_init_script(
        "window.__citryBenchExpected = " + json.dumps(assertions.expected_view(initial_expected)) + ";"
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on("console", lambda message: page_errors.append(message.text) if message.type == "error" else None)
    network = Network(page)
    network.origin = urlsplit(base).netloc
    network.transport = (adapter or {}).get("transport", "http")
    page.set_default_timeout(settings["action_timeout_ms"])
    outcome = True
    previous_revision = -1
    sequence = session_sequence(settings, actions, initial_only=initial_only)
    try:
        for index, action in enumerate(sequence):
            initial = action["name"] == "initial"
            operation = "initial" if initial else f"{session}-{index}-{action['name']}"
            network.operation = operation
            row = {
                **info,
                "operation": operation,
                "action": action["name"],
                "cycle": action.get("cycle"),
                "warmup": action.get("warmup", False),
                "status": "error",
                "elapsed_ms": None,
            }
            ready = None
            snapshot = None
            payload = None
            timeout = settings["initial_timeout_ms"] if initial else settings["action_timeout_ms"]
            # Forced collection changes every later heap reading, so only the
            # page's last observation takes it.
            final = index == len(sequence) - 1
            try:
                if memory_observer is not None:
                    memory_observer.begin(
                        operation,
                        page,
                        action["name"],
                        action.get("warmup", False),
                        action.get("cycle"),
                        read_heap_after_gc=final,
                    )
                if initial:
                    page.goto(
                        base + "/?" + urlencode({"count": info["count"], "session": session}),
                        wait_until="commit",
                        timeout=timeout,
                    )
                else:
                    # Keep the before-state check outside form preparation and timing.
                    page.evaluate("value => window.__projectBoardBefore = value", assertions.capture_view(page))
                    previous = page.evaluate("window.__projectBoardExpected")
                    expected = assertions.expected_after(previous, action["name"])
                    page.evaluate("value => window.__citryBench.expect(value)", assertions.expected_view(expected))
                    # Form preparation is outside the measured event interval.
                    if hasattr(actions, "prepare"):
                        actions.prepare(page, action)
                    page.evaluate(
                        "value => window.__citryBench.arm(value)",
                        {
                            "operation": operation,
                            "event": action.get("event", "click"),
                            "action": page.locator(action["selector"]).get_attribute("data-bench-action"),
                        },
                    )
                    actions.perform(page, action)
                ready = mark(page, operation, timeout)
                if memory_observer is not None:
                    # Host/CDP sampling starts only after the layout timestamp
                    # has been captured and cannot extend the measured interval.
                    memory_observer.at_layout(operation, page, ready)
                if ready["session"] != session:
                    raise AssertionError("Ready signal belongs to a different session")
                row["ready_elapsed_ms"] = ready["end"] - ready["start"]
                row["layout_extra_wait_ms"] = ready["layout_end"] - ready["end"]
                row["layout_inclusive_elapsed_ms"] = ready["layout_end"] - ready["start"]
                row["layout_endpoint"] = "second-rAF-layout-opportunity-v1"
                # Keep the pre-existing field as the ready-only diagnostic for
                # archived consumers; the shared endpoint has an explicit field.
                row["elapsed_ms"] = row["ready_elapsed_ms"]
                row["ready"] = ready
                row["observer_ms"] = ready.get("observer_ms")
                row["semantic_observer_ms"] = ready["semantic_observer_ms"]
                if row["layout_inclusive_elapsed_ms"] > timeout:
                    raise PlaywrightTimeoutError("Layout-inclusive browser interval exceeded the profile deadline")
                snapshot = capture(page, ready)
                audit = None
                if network.transport == "websocket":
                    with urllib.request.urlopen(  # noqa: S310 - adapter audit is validated as same-origin HTTP
                        base + adapter["audit"] + "?" + urlencode({"session": session}), timeout=10
                    ) as response:
                        audit = json.load(response)
                payload = collect_network_then_heap_after_gc(
                    network,
                    memory_observer,
                    page,
                    operation,
                    ready,
                    snapshot,
                    audit,
                    read_heap_after_gc=final,
                )
                if initial:
                    # The local-behavior assertions below click tabs, and a
                    # click ends Chromium's LCP reporting, so finalize paint
                    # timing first. The values are browser paint timestamps;
                    # reading them late does not change them.
                    row.update(read_paint_timing(page))
                # A hybrid adapter may mount small boards in the browser; its
                # initial page then carries browser-rendering labels.
                declared = adapter or {}
                rendering = (
                    initial_rendering(declared, info["count"]) if initial else declared.get("rendering", "server")
                )
                row["server_render_ms"], row["server_render_status"] = server_render_time(
                    payload, rendering, initial=initial
                )
                (
                    row["server_prepare_ms"],
                    row["server_prepare_status"],
                    row["server_prepare_reason"],
                ) = server_prepare_time(payload, rendering, row["server_render_ms"], initial=initial)
                row["latency_phase"] = payload["latency_phase"]
                row["server_prepare_kind"] = server_prepare_kind({**declared, "rendering": rendering}, initial=initial)
                row["server_timing_boundary"] = (adapter or {}).get("timing_boundary", "complete")
                for server in payload["server_timings"]:
                    append(directory / "server-timings.jsonl", {**info, **server})
                if payload["errors"]:
                    raise AssertionError(str(payload["errors"]))
                if page_errors:
                    raise AssertionError(f"Browser errors: {page_errors}")
                if initial:
                    assertions.assert_initial(page, info["count"], ready)
                    assertions.assert_local_behavior(page)
                else:
                    if ready["state"]["revision"] <= previous_revision:
                        raise AssertionError("Server revision did not advance")
                    if not payload["server_exchange_count"]:
                        raise AssertionError("Server action produced no request or socket message")
                    assertions.assert_action(page, action, info["count"], previous_revision, ready)
                previous_revision = ready["state"]["revision"]
                row["status"] = "ok"
            except (Error, AssertionError, ValueError, StopIteration) as error:
                row["status"] = "timeout" if isinstance(error, PlaywrightTimeoutError) else "error"
                row["error"] = str(error)
                row["deadline_ms"] = timeout
                outcome = False
            finally:
                if memory_observer is not None:
                    memory_observer.finish(operation, row["status"], row.get("error"))
                write_diagnostic_capture(
                    directory,
                    session,
                    index,
                    operation,
                    row["status"],
                    page_errors,
                    network,
                )
                # One record per operation keeps failures from duplicating byte totals.
                append(
                    directory / "sizes.jsonl",
                    {
                        **info,
                        "operation": operation,
                        "action": action["name"],
                        "cycle": row["cycle"],
                        "warmup": row["warmup"],
                        "final_html_bytes": snapshot["final_html_bytes"] if snapshot else None,
                        **(
                            {
                                k: v
                                for k, v in payload.items()
                                if k
                                not in (
                                    "cdp",
                                    "sockets",
                                    "server_timings",
                                    "server_prepare_ms",
                                    "server_prepare_status",
                                    "server_prepare_reason",
                                    "latency_phase",
                                )
                            }
                            if payload
                            else {"decoded_response_bytes": None, "encoded_response_body_bytes": None}
                        ),
                        "status": row["status"],
                        "error": row.get("error"),
                    },
                )
                append(directory / "samples.jsonl", stored_sample(row))
            if row["status"] != "ok":
                # Dependent actions cannot be meaningfully timed on invalid state.
                for skipped in sequence[index + 1 :]:
                    append(
                        directory / "samples.jsonl",
                        {
                            **info,
                            "action": skipped["name"],
                            "warmup": skipped.get("warmup", False),
                            "status": "not-run",
                            "reason": "session prerequisite failed",
                            "elapsed_ms": None,
                        },
                    )
                break
    finally:
        context.close()
    return outcome
