"""
Inject readiness faults in fresh, untimed browser sessions.

These checks cover HTTP and single-connection WebSocket project boards. Holding
external framework scripts delays actual initialization; it does not establish
the earliest interactive instant or qualify reconnects and concurrent actions.
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from types import ModuleType
from typing import Any
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

from playwright.sync_api import Browser, Page, Route
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from citry_bench.browser import SCRIPT, mark, module
from citry_bench.config import WEB, initial_rendering

SELECT = '[data-bench-action="select-1"]'
STATE = """() => {
  const board = document.querySelector('#board');
  return {revision: Number(board.dataset.revision), session: board.dataset.session,
    operation: board.dataset.operation};
}"""


@contextmanager
def _page(browser: Browser, timeout: int) -> Iterator[Page]:
    context = browser.new_context(service_workers="block")
    context.add_init_script(SCRIPT)
    try:
        page = context.new_page()
        page.set_default_timeout(timeout)
        yield page
    finally:
        context.close()


def _initial(page: Page, base: str, count: int, timeout: int, assertions: ModuleType) -> dict:
    session = uuid4().hex
    expected = assertions.initial_expected(count)
    page.add_init_script("window.__citryBenchExpected = " + json.dumps(assertions.expected_view(expected)) + ";")
    page.goto(base + "/?" + urlencode({"count": count, "session": session}), wait_until="commit")
    result = mark(page, "initial", timeout)
    if result["session"] != session:
        raise AssertionError("Qualification initial signal belongs to another session")
    assertions.assert_view(result["semantic"], expected)
    page.evaluate("value => window.__projectBoardExpected = value", expected)
    return result


def _arm(page: Page, operation: str, *, drop: bool = False, action: str = "select-1") -> None:
    page.evaluate(
        """({operation, drop, action}) => {
          window.__citryBench.arm({operation, event: 'click', action});
          window.addEventListener('click', event => {
            if (event.target.closest('[data-bench-action]')?.dataset.benchAction !== action) return;
            window.__qualificationEvent = {type: event.type, trusted: event.isTrusted};
            if (drop) { event.preventDefault(); event.stopImmediatePropagation(); }
          }, {capture: true, once: true});
        }""",
        {"operation": operation, "drop": drop, "action": action},
    )


def _absent(page: Page, operation: str, timeout: int) -> dict:
    try:
        page.wait_for_function(
            "op => window.__citryBench?.marks.some(mark => mark.operation === op) || "
            "window.__citryBench?.faults.length",
            arg=operation,
            timeout=timeout,
        )
    except PlaywrightTimeoutError:
        state = page.evaluate("() => ({marks: window.__citryBench.marks, faults: window.__citryBench.faults})")
        if state["faults"] or any(item["operation"] == operation for item in state["marks"]):
            raise AssertionError("Fault qualification timed out with contradictory readiness evidence") from None
        return {"observation_timeout_ms": timeout, "ready_accepted": False}
    state = page.evaluate("() => ({marks: window.__citryBench.marks, faults: window.__citryBench.faults})")
    if state["faults"]:
        raise AssertionError(f"Readiness instrumentation faults: {state['faults']}")
    if any(item["operation"] == operation for item in state["marks"]):
        raise AssertionError(f"Injected fault accepted readiness for {operation}")
    raise AssertionError(f"Unexpected readiness wake without a mark or fault for {operation}")


def _action(page: Page, timeout: int, assertions: ModuleType, action: str = "select-1") -> dict:
    before = page.evaluate(STATE)
    previous = page.evaluate("window.__projectBoardExpected")
    if action.startswith("select-"):
        expected = deepcopy(previous)
        selected_id = int(action.removeprefix("select-"))
        for row in expected["rows"]:
            row["selected"] = row["id"] == selected_id
    else:
        expected = assertions.expected_after(previous, action)
    page.evaluate("value => window.__citryBench.expect(value)", assertions.expected_view(expected))
    operation = uuid4().hex
    _arm(page, operation, action=action)
    page.locator(f'[data-bench-action="{action}"]').click()
    result = mark(page, operation, timeout)
    if result["session"] != before["session"] or result["state"]["revision"] != before["revision"] + 1:
        raise AssertionError("Qualification control action did not advance its session revision exactly once")
    if page.evaluate(STATE) != result["state"]:
        raise AssertionError("Qualification control DOM differs from the ready snapshot")
    assertions.assert_view(result["semantic"], expected)
    page.evaluate("value => window.__projectBoardExpected = value", expected)
    return result


def _inserted_control(page: Page, timeout: int, count: int, assertions: ModuleType) -> dict:
    """Check that a server-created row receives a working selection handler."""
    rows_script = """() => Array.from(document.querySelectorAll('#board [data-row-id]'), row => ({
      id: Number(row.dataset.rowId), title: row.querySelector('.row-title').textContent.trim(),
      status: row.querySelector('.row-status').textContent.trim(), selected: row.dataset.selected === 'true',
    }))"""
    before = page.evaluate(rows_script)
    expected = [
        {k: row[k] for k in ("id", "title", "status", "selected")}
        for row in assertions.initial_expected(count)["rows"]
    ]
    if before != expected:
        raise AssertionError("Inserted-control qualification did not start with the expected rows")
    inserted = _action(page, timeout, assertions, "insert")
    row_id = count + 1
    expected.append({"id": row_id, "title": f"New output {row_id:04d}", "status": "open", "selected": False})
    if page.evaluate(rows_script) != expected:
        raise AssertionError("Insert did not append the expected new row and preserve existing rows")
    selected = _action(page, timeout, assertions, f"select-{row_id}")
    expected[-1]["selected"] = True
    if page.evaluate(rows_script) != expected:
        raise AssertionError("Newly inserted control did not select only its own row")
    return {
        "case": "newly-inserted-control",
        "status": "passed",
        "inserted_row_id": row_id,
        "insert": inserted,
        "select": selected,
    }


def _expanded_content(page: Page, count: int) -> dict:
    """Prove canonical disclosure content is rendered and visible outside timing."""
    result = page.evaluate(
        """expectedCount => {
          const visible = element => {
            if (typeof element.checkVisibility === 'function') {
              return element.checkVisibility({
                contentVisibilityAuto: true, opacityProperty: true, visibilityProperty: true,
              });
            }
            for (let current = element; current; current = current.parentElement) {
              const style = getComputedStyle(current);
              if (current.hidden || style.display === 'none' || style.visibility === 'hidden' ||
                  style.visibility === 'collapse' || style.opacity === '0') return false;
            }
            return true;
          };
          const selectors = {
            descriptions: '#outputs [data-row-id] [data-output-description]',
            completions: '#outputs [data-row-id] [data-output-completed]',
            selects: '#outputs [data-row-id] [data-bench-action^="select-"]',
            attachments: '#outputs [data-attachment-id] .attachment-name',
            dependencies: '#outputs [data-dependency-id] .dependency-title',
          };
          const counts = {};
          for (const [name, selector] of Object.entries(selectors)) {
            const elements = Array.from(document.querySelectorAll(selector));
            const hidden = elements.filter(element => !visible(element));
            if (hidden.length) throw new Error(`${name} contains ${hidden.length} hidden canonical elements`);
            counts[name] = elements.length;
          }
          if (counts.descriptions !== expectedCount || counts.completions !== expectedCount ||
              counts.selects !== expectedCount || counts.attachments < 1 || counts.dependencies < 1) {
            throw new Error(`Canonical expanded-content counts are incomplete: ${JSON.stringify(counts)}`);
          }
          return counts;
        }""",
        count,
    )
    return {"case": "expanded-content-visible", "status": "passed", "counts": result}


def _signal_fault(page: Page, case: str, timeout: int) -> dict:
    operation = uuid4().hex
    _arm(page, operation, drop=True)
    if case != "premature-readiness":
        page.locator(SELECT).click()
    page.evaluate(
        """({operation, fault}) => {
          const board = document.querySelector('#board');
          board.dataset.operation = operation;
          if (fault !== 'stale-revision') board.dataset.revision = Number(board.dataset.revision) + 1;
          window.__citryBench.ready({revision: Number(board.dataset.revision),
            session: board.dataset.session, operation, phase: 'update',
            pending: fault === 'pending-readiness' ? 1 : 0});
        }""",
        {"operation": operation, "fault": case},
    )
    try:
        mark(page, operation, timeout)
    except AssertionError as error:
        state = page.evaluate("() => ({marks: window.__citryBench.marks, faults: window.__citryBench.faults})")
        matching_faults = [item for item in state["faults"] if item.get("operation") == operation]
        matching_marks = [item for item in state["marks"] if item.get("operation") == operation]
        if len(matching_faults) != 1 or matching_marks:
            raise AssertionError(f"Injected {case} did not fault before mark publication: {state}") from error
        return {
            "case": case,
            "status": "passed",
            "ready_accepted": False,
            "error": str(error),
            **state,
        }
    raise AssertionError(f"Readiness consumer accepted {case}")


def _semantic_fault(page: Page, case: str) -> dict:
    """Prove a same-revision partial DOM cannot become a valid earlier mark."""
    operation = uuid4().hex
    _arm(page, operation, drop=True)
    page.locator(SELECT).click()
    page.evaluate(
        """({operation, caseName}) => {
          const board = document.querySelector('#board');
          board.dataset.operation = operation;
          board.dataset.revision = Number(board.dataset.revision) + 1;
          const last = Array.from(document.querySelectorAll('#outputs [data-row-id]')).at(-1);
          let restore;
          if (caseName === 'missing-dom-tail') {
            const parent = last.parentNode;
            const next = last.nextSibling;
            last.remove();
            restore = () => { parent.insertBefore(last, next); };
          } else {
            const title = last.querySelector('.row-title');
            const complete = title.textContent;
            title.textContent = 'Delayed DOM tail';
            restore = () => { title.textContent = complete; };
          }
          window.__citryBench.ready({revision: Number(board.dataset.revision), session: board.dataset.session,
            operation, phase: 'update', pending: 0});
          requestAnimationFrame(() => requestAnimationFrame(restore));
        }""",
        {"operation": operation, "caseName": case},
    )
    page.wait_for_function(
        "op => window.__citryBench.marks.some(mark => mark.operation === op) || "
        "window.__citryBench.faults.some(fault => fault.operation === op)",
        arg=operation,
        timeout=1000,
    )
    state = page.evaluate("() => ({marks: window.__citryBench.marks, faults: window.__citryBench.faults})")
    matching_faults = [item for item in state["faults"] if item.get("operation") == operation]
    matching_marks = [item for item in state["marks"] if item.get("operation") == operation]
    if len(matching_faults) != 1 or matching_marks:
        raise AssertionError(f"Injected {case} was accepted before semantic completion")
    completed = page.evaluate("() => window.__citryBench.semanticSnapshot()")
    expected = page.evaluate("window.__citryBenchExpected")
    if completed != expected:
        raise AssertionError(f"Injected {case} did not restore the complete semantic DOM")
    return {"case": case, "status": "passed", "ready_accepted": False, "late_completion": True, **state}


def _semantic_control(page: Page, timeout: int) -> dict:
    """Accept the same synthetic identity when its complete DOM is present."""
    operation = uuid4().hex
    _arm(page, operation, drop=True)
    page.locator(SELECT).click()
    page.evaluate(
        """operation => {
          const board = document.querySelector('#board');
          board.dataset.operation = operation;
          board.dataset.revision = Number(board.dataset.revision) + 1;
          window.__citryBench.ready({revision: Number(board.dataset.revision), session: board.dataset.session,
            operation, phase: 'update', pending: 0});
        }""",
        operation,
    )
    result = mark(page, operation, timeout)
    return {"case": "complete-dom-control", "status": "passed", "ready": result}


def _lost_action(page: Page, case: str, timeout: int) -> dict:
    before = page.evaluate(STATE)
    # Observe the existing sockets too; they were opened before fault injection.
    sent_before = page.evaluate("() => window.__citryBench.connections().map(socket => socket.sent.length)")
    requests = []
    aborted = []
    page.on("request", lambda request: requests.append(request.url) if request.method == "POST" else None)

    def interrupt(route: Route) -> None:
        if route.request.method == "POST":
            aborted.append(route.request.url)
            route.abort("failed")
        else:
            route.continue_()

    if case == "interrupted-transport":
        page.route("**/*", interrupt)
    operation = uuid4().hex
    _arm(page, operation, drop=case == "dropped-handler")
    page.locator(SELECT).click()
    absence = _absent(page, operation, timeout)
    event = page.evaluate("() => window.__qualificationEvent")
    if not event or not event["trusted"]:
        raise AssertionError("Fault injection did not observe a trusted control click")
    after = page.evaluate(STATE)
    if after != before:
        raise AssertionError("Failed action unexpectedly changed the board revision or correlation")
    sent_after = page.evaluate("() => window.__citryBench.connections().map(socket => socket.sent.length)")
    outbound_messages = sum(sent_after) - sum(sent_before)
    if case == "dropped-handler" and outbound_messages:
        raise AssertionError("Dropped handler still sent a WebSocket message")
    if case == "dropped-handler" and requests:
        raise AssertionError("Dropped handler still sent a POST request")
    if case == "interrupted-transport" and not aborted:
        raise AssertionError("Transport interruption did not abort an actual POST request")
    return {
        "case": case,
        "status": "passed",
        "event": event,
        "post_requests": requests,
        "outbound_socket_messages": outbound_messages,
        "aborted": aborted,
        "before": before,
        "after": after,
        **absence,
    }


def _delayed_initialization(
    browser: Browser,
    base: str,
    settings: dict,
    count: int,
    timeout: int,
    transport: str,
    rendering: str = "server",
    assertions: ModuleType | None = None,
) -> dict:
    if assertions is None:
        raise ValueError("Delayed initialization requires the scenario assertions")
    # Hybrid adapters at or above their hydration_min_count already include
    # the board as server HTML in the first document. Browser-only and
    # persistent-socket adapters, and hybrid adapters below that count, start
    # with an empty application root. The adapter's update_payload does not
    # affect this check, which covers only the first page.
    browser_rendered = transport == "websocket" or rendering == "browser"
    held: list[Route] = []
    released = False

    def hold(route: Route) -> None:
        path = urlsplit(route.request.url).path
        if not released and route.request.resource_type == "script" and path != "/assets/readiness.js":
            held.append(route)
        else:
            route.continue_()

    with _page(browser, settings["initial_timeout_ms"]) as page:
        page.route("**/*", hold)
        session = uuid4().hex
        expected = assertions.initial_expected(count)
        page.add_init_script("window.__citryBenchExpected = " + json.dumps(assertions.expected_view(expected)) + ";")
        page.goto(base + "/?" + urlencode({"count": count, "session": session}), wait_until="commit")
        page.locator("body" if browser_rendered else "#board").wait_for(state="attached")
        absence = _absent(page, "initial", timeout)
        if not held:
            raise AssertionError("Initialization delay did not hold the required framework dependency")
        urls = [route.request.url for route in held]
        released = True
        for route in held:
            route.continue_()
        initial = mark(page, "initial", settings["initial_timeout_ms"])
        if initial["session"] != session:
            raise AssertionError("Delayed initial signal belongs to another session")
        page.evaluate("value => window.__projectBoardExpected = value", expected)
        action = _action(page, settings["action_timeout_ms"], assertions)
        return {
            "case": "delayed-initialization",
            "status": "passed",
            "held_scripts": urls,
            "initial_ready_during_hold": False,
            "before_release": absence,
            "initial": initial,
            "control_action": action,
            "scope": "External framework script loading, followed by actual adapter lifecycle readiness",
        }


def _interrupted_socket(
    page: Page, base: str, settings: dict, count: int, timeout: int, assertions: ModuleType
) -> dict:
    interrupted = []
    active = False

    def route_socket(route: Any) -> None:
        server = route.connect_to_server()

        def receive(message: Any) -> None:
            if active:
                interrupted.append(message)
                server.close(code=1011, reason="qualification interruption")
                route.close(code=1011, reason="qualification interruption")
            else:
                server.send(message)

        route.on_message(receive)

    # Routing must be installed before the page creates its persistent connection.
    page.route_web_socket("**/*", route_socket)
    _initial(page, base, count, settings["initial_timeout_ms"], assertions)
    before = page.evaluate(STATE)
    operation = uuid4().hex
    active = True
    _arm(page, operation)
    page.locator(SELECT).click()
    absence = _absent(page, operation, timeout)
    after = page.evaluate(STATE)
    if not interrupted or before != after:
        raise AssertionError("Socket fault did not interrupt a real action without changing the board")
    return {
        "case": "interrupted-transport",
        "status": "passed",
        "messages_interrupted": len(interrupted),
        "before": before,
        "after": after,
        **absence,
    }


def qualify_faults(browser: Browser, base: str, settings: dict, count: int, adapter: dict | None = None) -> list[dict]:
    """
    Require real successful actions and rejection of each injected fault.

    Every case uses a fresh browser context and server session. Fault timeouts are
    bounded observation windows, not benchmark samples; routes are installed only
    here because Playwright routing disables the browser HTTP cache.
    """
    transport = (adapter or {}).get("transport", "http")
    assertions = module(WEB / "scenarios" / settings["scenario"] / "assertions.py")
    evidence = []
    timeout = min(settings["action_timeout_ms"], 500)
    with _page(browser, settings["initial_timeout_ms"]) as page:
        initial = _initial(page, base, count, settings["initial_timeout_ms"], assertions)
        expanded = _expanded_content(page, count)
        duplicate_ids = page.evaluate(
            """() => { const ids = Array.from(document.querySelectorAll('[id]'), el => el.id);
              return ids.filter((id, index) => ids.indexOf(id) !== index); }"""
        )
        if duplicate_ids:
            raise AssertionError(f"Canonical DOM contains duplicate IDs: {duplicate_ids}")
        action = _action(page, settings["action_timeout_ms"], assertions)
        last = _action(page, settings["action_timeout_ms"], assertions, f"select-{count}")
        evidence.append(
            {
                "case": "first-last-controls",
                "status": "passed",
                "initial": initial,
                "expanded_content": expanded,
                "first": action,
                "last": last,
            }
        )
    # These two verification actions run only in a fresh untimed session.
    with _page(browser, settings["initial_timeout_ms"]) as page:
        _initial(page, base, count, settings["initial_timeout_ms"], assertions)
        evidence.append(_inserted_control(page, settings["action_timeout_ms"], count, assertions))
    with _page(browser, settings["initial_timeout_ms"]) as page:
        _initial(page, base, count, settings["initial_timeout_ms"], assertions)
        evidence.append(_semantic_control(page, settings["action_timeout_ms"]))
    for case in ("missing-dom-tail", "delayed-dom-tail"):
        with _page(browser, settings["initial_timeout_ms"]) as page:
            _initial(page, base, count, settings["initial_timeout_ms"], assertions)
            evidence.append(_semantic_fault(page, case))
    for case in (
        "premature-readiness",
        "pending-readiness",
        "stale-revision",
        "dropped-handler",
        "interrupted-transport",
    ):
        with _page(browser, settings["initial_timeout_ms"]) as page:
            if transport == "websocket" and case == "interrupted-transport":
                result = _interrupted_socket(page, base, settings, count, timeout, assertions)
                evidence.append(result)
                continue
            _initial(page, base, count, settings["initial_timeout_ms"], assertions)
            result = (
                _signal_fault(page, case, timeout)
                if case in ("premature-readiness", "pending-readiness", "stale-revision")
                else _lost_action(page, case, timeout)
            )
            evidence.append(result)
    evidence.append(
        _delayed_initialization(
            browser,
            base,
            settings,
            count,
            timeout,
            transport,
            initial_rendering(adapter or {}, count),
            assertions,
        )
    )
    return evidence
