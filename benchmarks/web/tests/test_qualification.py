"""Exercise fault rejection with real Chromium events and a small HTTP fixture."""

import json
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import parse_qs, urlsplit

import pytest
from citry_bench.browser import SCRIPT, mark, module
from citry_bench.config import CACHE, WEB
from citry_bench.qualification import (
    _absent,
    _delayed_initialization,
    _inserted_control,
    _lost_action,
    _signal_fault,
    qualify_faults,
)
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

SETTINGS = {"scenario": "project_board", "initial_timeout_ms": 5000, "action_timeout_ms": 1000}
COUNT = 14
ASSERTIONS = module(WEB / "scenarios/project_board/assertions.py")
FRAMEWORK = """
const board = document.querySelector('#board');
const signal = phase => window.__citryBench.ready({phase, pending: 0,
  revision: Number(board.dataset.revision), session: board.dataset.session,
  operation: board.dataset.operation});
const row = id => `<article id="row-${id}" data-row-id="${id}" data-output-expanded="true"
  data-selected="false"><span data-output-badge="open">In progress</span><details open>
  <summary><span class="row-title">New output ${String(id).padStart(4, '0')}</span>
  <span class="row-status">open</span></summary><section aria-label="Dependencies"></section>
  <textarea data-output-description></textarea><input type="checkbox" data-output-completed>
  <button data-bench-action="select-${id}">Select</button></details></article>`;
board.addEventListener('click', async event => {
  const action = event.target.closest('[data-bench-action]')?.dataset.benchAction;
  if (!action || (window.__fixtureDropInserted && action === 'select-15')) return;
  try {
    await fetch('/action', {method: 'POST', body: action});
    if (action === 'insert') {
      const finalGroup = board.querySelector('#outputs [data-phase-id]:last-of-type > details > div');
      finalGroup.insertAdjacentHTML('beforeend', row(15));
      board.dataset.visibleCount = '15';
      board.dataset.totalCount = '15';
    } else {
      const selected = window.__fixtureWrongSelection ? 1 : Number(action.split('-')[1]);
      board.querySelectorAll('[data-row-id]').forEach(row => {
        row.dataset.selected = String(Number(row.dataset.rowId) === selected);
      });
    }
    board.dataset.revision = Number(board.dataset.revision) + 1;
    board.dataset.operation = document.querySelector('input[name="operation"]').value;
    signal('update');
  } catch { /* An interrupted request must not report a completed update. */ }
});
signal('initial');
"""


def _text(value: object) -> str:
    return escape(str(value), quote=True)


def _row(value: dict) -> str:
    source = "" if value["source_id"] is None else f' data-source-id="{value["source_id"]}"'
    checked = " checked" if value["completed"] else ""
    attachments = "".join(
        f'<article data-attachment-id="{item["id"]}" data-attachment-name="{_text(item["name"])}">'
        f'<a class="attachment-name" href="{_text(item["url"])}">{_text(item["name"])}</a>'
        + "".join(f'<span data-attachment-tag="{_text(tag)}">{_text(tag)}</span>' for tag in item["tags"])
        + "</article>"
        for item in value["attachments"]
    )
    dependencies = "".join(
        f'<article data-dependency-id="{item["id"]}" data-dependency-title="{_text(item["title"])}" '
        f'data-dependency-completed="{str(item["completed"]).lower()}">'
        f'<span class="dependency-title">{_text(item["title"])}</span></article>'
        for item in value["dependencies"]
    )
    return (
        f'<article id="row-{value["id"]}" data-row-id="{value["id"]}"{source} '
        f'data-output-expanded="true" data-selected="{str(value["selected"]).lower()}">'
        f'<span data-output-badge="{value["status"]}">{value["status"]}</span><details open><summary>'
        f'<span class="row-title">{_text(value["title"])}</span>'
        f'<span class="row-status">{value["status"]}</span></summary>'
        f'<section aria-label="Dependencies">{dependencies}</section>'
        f"<textarea data-output-description>{_text(value['description'])}</textarea>"
        f'<input type="checkbox" data-output-completed{checked}>'
        f'<section>{attachments}</section><button data-bench-action="select-{value["id"]}">Select</button>'
        "</details></article>"
    )


def document(session: str) -> str:
    view = ASSERTIONS.expected_view(ASSERTIONS.initial_expected(COUNT))
    tab_labels = [
        ("project-info", "Project Info"),
        *((group["id"], group["title"]) for group in view["note_tabs"]),
        ("outputs", "Outputs"),
    ]
    buttons = "".join(f'<button data-tab-target="{tab}">{_text(label)}</button>' for tab, label in tab_labels)
    notes = ""
    for group in view["note_tabs"]:
        content = "".join(
            f'<article data-note-id="{note["id"]}"><p class="note-text">{_text(note["text"])}</p>'
            + "".join(
                f'<article data-comment-id="{comment["id"]}"><p class="comment-text">'
                f'{_text(comment["text"])}</p><span class="comment-author">{_text(comment["author"])}</span></article>'
                for comment in note["comments"]
            )
            + "</article>"
            for note in group["notes"]
        )
        notes += f'<section hidden id="{group["id"]}" data-tab-panel="{group["id"]}">{content}</section>'
    phases = "".join(
        f'<section data-phase-id="{phase["id"]}" data-phase-expanded="true"><details open>'
        f'<summary class="phase-title">{_text(phase["title"])}</summary><div>'
        + "".join(_row(row) for row in phase["outputs"])
        + "</div></details></section>"
        for phase in view["phase_groups"]
    )
    roles = "".join(
        f'<span data-role-id="{role["id"]}"><span class="role-name">{_text(role["name"])}</span>'
        f'<span class="user-name">{_text(role["user_name"])}</span></span>'
        for role in view["roles"]
    )
    bookmarks = "".join(
        f'<a data-bookmark-id="{item["id"]}" data-bookmark-name="{_text(item["text"])}" '
        f'href="{_text(item["url"])}"><span class="bookmark-name">{_text(item["text"])}</span></a>'
        for item in view["bookmarks"]
    )
    project = view["project"]
    return f"""<!doctype html><html><head><script defer src="/assets/framework.js"></script></head><body>
<aside id="local-disclosure"><button data-bench-action="disclosure">Details</button>
<p id="disclosure-content">Open</p><input id="preserved-input" value="Unchanged draft"></aside>
<section id="board" data-project-id="{project["id"]}" data-session="{_text(session)}" data-operation="initial"
 data-revision="0" data-visible-count="14" data-total-count="14">
<nav id="project-navbar"></nav><aside id="project-sidebar">{bookmarks}</aside>
<h1 id="board-title">{_text(view["title"])}</h1><span id="project-status">{_text(project["status"])}</span>
<span id="project-start-date">{_text(project["start_date"])}</span>
<span id="project-end-date">{_text(project["end_date"])}</span>
<span id="project-organization">{_text(project["organization"])}</span>
<input id="title-input" value="{_text(view["title_input"])}"><input id="query" value="">
<span id="form-error"></span><span id="form-notice"></span><input name="operation">
<button data-bench-action="insert">Insert</button><section id="project-tabs">{buttons}
<section hidden id="project-info" data-tab-panel="project-info">{roles}<div data-project-contacts></div>
<div data-project-status-updates></div><div data-project-tags></div></section>{notes}
<section id="outputs" data-tab-panel="outputs">{phases}</section></section></section></body></html>"""


@pytest.fixture(scope="module")
def browser():
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(CACHE / "browsers"))
        with sync_playwright() as playwright:
            instance = playwright.chromium.launch()
            try:
                yield instance
            finally:
                instance.close()


@pytest.fixture
def page(browser):
    context = browser.new_context()
    try:
        result = context.new_page()
        result.set_content(document("fixture").replace('<script defer src="/assets/framework.js"></script>', ""))
        result.evaluate(SCRIPT)
        expected = ASSERTIONS.initial_expected(COUNT)
        result.evaluate("value => window.__citryBench.expect(value)", ASSERTIONS.expected_view(expected))
        result.evaluate("value => window.__projectBoardExpected = value", expected)
        result.evaluate("""() => window.__citryBench.ready({phase: 'initial', pending: 0,
          revision: 0, session: 'fixture', operation: 'initial'})""")
        mark(result, "initial", 1000)
        yield result
    finally:
        context.close()


def pending_initial_page(browser, session="pending-fixture"):
    context = browser.new_context()
    page = context.new_page()
    page.set_content(document(session).replace('<script defer src="/assets/framework.js"></script>', ""))
    page.evaluate(SCRIPT)
    expected = ASSERTIONS.initial_expected(COUNT)
    page.evaluate("value => window.__citryBench.expect(value)", ASSERTIONS.expected_view(expected))
    return context, page


def test_initial_ready_reserves_before_allowing_an_action_arm(browser):
    context, result = pending_initial_page(browser)
    try:
        state = result.evaluate("""() => {
          const board = document.querySelector('#board');
          window.__citryBench.ready({phase: 'initial', pending: 0, revision: 0,
            session: board.dataset.session, operation: board.dataset.operation});
          let message = '';
          try { window.__citryBench.arm({operation: 'too-early', event: 'click', action: 'insert'}); }
          catch (error) { message = error.message; }
          return {message, pending: window.__citryBench.pendingMarks.length};
        }""")
        assert state["message"] == "Previous operation has not completed"
        assert state["pending"] == 1
        ready = mark(result, "initial", 1000)
        assert ready["layout_end"] >= ready["end"]
    finally:
        context.close()


def test_duplicate_ready_is_rejected_while_layout_mark_is_pending(browser):
    context, result = pending_initial_page(browser, "duplicate-fixture")
    try:
        result.evaluate("""() => {
          const board = document.querySelector('#board');
          const value = {phase: 'initial', pending: 0, revision: 0,
            session: board.dataset.session, operation: board.dataset.operation};
          window.__citryBench.ready(value);
          window.__citryBench.ready(value);
        }""")
        with pytest.raises(AssertionError, match="prior layout mark was pending"):
            mark(result, "initial", 1000)
    finally:
        context.close()


def test_semantic_comparison_starts_after_second_frame_layout_timestamp(browser):
    context, result = pending_initial_page(browser, "semantic-layout-fixture")
    try:
        result.evaluate("""() => {
          const original = window.__citryBench.semanticSnapshot;
          window.__citryBench.semanticSnapshot = () => {
            const reservation = window.__citryBench.pendingMarks[0];
            window.__semanticTiming = {
              layoutEnd: reservation?.layout_end,
              semanticStart: reservation?.semantic_start,
            };
            return original();
          };
          const board = document.querySelector('#board');
          window.__citryBench.ready({phase: 'initial', pending: 0, revision: 0,
            session: board.dataset.session, operation: board.dataset.operation});
        }""")
        ready = mark(result, "initial", 1000)
        order = result.evaluate("() => window.__semanticTiming")
        assert order["layoutEnd"] is not None
        assert order["semanticStart"] >= order["layoutEnd"]
        assert ready["layout_geometry"]["row_count"] == COUNT
    finally:
        context.close()


@pytest.fixture
def server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/assets/framework.js":
                body = FRAMEWORK
                content_type = "text/javascript"
            else:
                session = parse_qs(url.query)["session"][0]
                body = document(session)
                content_type = "text/html"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body.encode())))
            self.end_headers()
            self.wfile.write(body.encode())

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response(204)
            self.end_headers()

        def log_message(self, *_args):
            pass

    instance = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{instance.server_port}"
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join()


@pytest.mark.parametrize("case", ["premature-readiness", "pending-readiness", "stale-revision"])
def test_signal_faults_fail_before_async_mark_publication(page, case):
    result = _signal_fault(page, case, 1000)
    assert result["status"] == "passed"
    assert result["ready_accepted"] is False
    assert len(result["faults"]) == 1
    assert [item["operation"] for item in result["marks"]] == ["initial"]


def test_absence_does_not_accept_an_existing_mark(page):
    with pytest.raises(AssertionError, match="Injected fault accepted readiness"):
        _absent(page, "initial", 100)


def test_absence_does_not_swallow_instrumentation_fault(page):
    page.evaluate("() => window.__citryBench.faults.push({message: 'fixture fault'})")
    with pytest.raises(AssertionError, match="fixture fault"):
        _absent(page, "missing-operation", 100)


def test_absence_does_not_accept_a_late_mark(page):
    page.evaluate("""() => setTimeout(() => window.__citryBench.marks.push({
      operation: 'late', start: 0, end: performance.now(), event: {trusted: true}}), 25)""")
    with pytest.raises(AssertionError, match="Injected fault accepted readiness"):
        _absent(page, "late", 1000)


def test_all_faults_and_recovery_use_actual_browser_events(browser, server):
    evidence = qualify_faults(browser, server, SETTINGS, COUNT)
    assert [item["case"] for item in evidence] == [
        "first-last-controls",
        "newly-inserted-control",
        "complete-dom-control",
        "missing-dom-tail",
        "delayed-dom-tail",
        "premature-readiness",
        "pending-readiness",
        "stale-revision",
        "dropped-handler",
        "interrupted-transport",
        "delayed-initialization",
    ]
    assert all(item["status"] == "passed" for item in evidence)
    assert evidence[0]["first"]["event"]["trusted"] is True
    assert evidence[8]["post_requests"] == []
    assert evidence[9]["aborted"] == [server + "/action"]
    assert evidence[10]["held_scripts"] == [server + "/assets/framework.js"]
    assert evidence[10]["before_release"]["ready_accepted"] is False
    assert evidence[10]["control_action"]["state"]["revision"] == 1


@pytest.mark.parametrize("fault", ["__fixtureDropInserted", "__fixtureWrongSelection"])
def test_inserted_control_rejects_missing_handler_and_wrong_selection(page, fault):
    # This fixture has already emitted initial readiness; install only its handlers.
    page.evaluate(
        FRAMEWORK.replace("signal('initial');", "").replace("fetch('/action'", "fetch('http://fixture.test/action'")
    )
    page.route("**/action", lambda route: route.fulfill(status=204))
    page.evaluate("name => window[name] = true", fault)
    error = PlaywrightTimeoutError if fault == "__fixtureDropInserted" else AssertionError
    match = "Timeout" if fault == "__fixtureDropInserted" else "Readiness instrumentation faults"
    with pytest.raises(error, match=match):
        _inserted_control(page, 100, COUNT, ASSERTIONS)
    inserted_mark = page.evaluate("window.__citryBench.marks[1]")
    assert inserted_mark["event"]["action"] == "insert"
    assert inserted_mark["revision"] == 1


@pytest.mark.parametrize("leak", [False, True])
def test_dropped_handler_checks_existing_socket_outbound_messages(browser, server, leak):
    context = browser.new_context()
    try:
        page = context.new_page()
        received = []

        def route_socket(route):
            def receive(message):
                received.append(message)

            route.on_message(receive)

        page.route_web_socket("ws://fixture.test/socket", route_socket)
        # Install routing before navigation so instrumentation wraps the routed constructor.
        context.add_init_script(SCRIPT)
        context.add_init_script(
            "window.__citryBenchExpected = "
            + json.dumps(ASSERTIONS.expected_view(ASSERTIONS.initial_expected(COUNT)))
            + ";"
        )
        page.goto(server + "/?session=socket-fixture")
        mark(page, "initial", 1000)
        page.evaluate("() => { window.__fixtureSocket = new WebSocket('ws://fixture.test/socket'); }")
        page.wait_for_function("window.__fixtureSocket.readyState === WebSocket.OPEN", timeout=1000)
        if leak:
            # An earlier capture handler can send even when the later drop prevents the action.
            page.evaluate("""() => window.addEventListener('click', () => {
              window.__fixtureSocket.send('unexpected message');
            }, {capture: true, once: true})""")
            with pytest.raises(AssertionError, match="Dropped handler still sent a WebSocket message"):
                _lost_action(page, "dropped-handler", 100)
            assert received == ["unexpected message"]
        else:
            result = _lost_action(page, "dropped-handler", 100)
            assert result["outbound_socket_messages"] == 0
            assert received == []
    finally:
        context.close()


def test_delayed_initialization_supports_browser_rendered_http(browser, server, monkeypatch):
    # The board cannot exist while the framework script that creates it is held.
    body = document("DYNAMIC_SESSION").split("<body>")[1].split("</body>")[0]
    setup = (
        "document.body.innerHTML = "
        + json.dumps(body)
        + ".replaceAll('DYNAMIC_SESSION', new URLSearchParams(location.search).get('session'));"
    )
    monkeypatch.setitem(globals(), "FRAMEWORK", setup + FRAMEWORK)
    monkeypatch.setitem(
        globals(),
        "document",
        lambda _session: '<html><head><script defer src="/assets/framework.js"></script></head><body></body></html>',
    )
    result = _delayed_initialization(browser, server, SETTINGS, COUNT, 100, "http", "browser", ASSERTIONS)
    assert result["initial_ready_during_hold"] is False
    assert result["control_action"]["state"]["revision"] == 1


def test_arm_writes_the_operation_only_into_the_submitting_form(browser):
    # Each repeated row owns a form with its own operation field. Setting
    # `.value` on a hidden input rewrites its `value` attribute, so writing
    # every row would put the id into the final HTML of each row.
    context = browser.new_context()
    try:
        page = context.new_page()
        page.set_content("""<!doctype html><html><body>
<form><input type="hidden" name="operation" value="manual"><button data-bench-action="select-1">Select</button></form>
<form><input type="hidden" name="operation" value="manual"><button data-bench-action="select-2">Select</button></form>
<button data-bench-action="loose">Loose</button><input name="operation" value="manual">
</body></html>""")
        page.evaluate(SCRIPT)
        values = "() => Array.from(document.querySelectorAll('input[name=operation]'), input => input.value)"
        page.evaluate("window.__citryBench.arm({operation: 'op-1', event: 'click', action: 'select-2'})")
        assert page.evaluate(values) == ["manual", "op-1", "manual"]
        assert page.evaluate("document.body.outerHTML.split('op-1').length - 1") == 1
    finally:
        context.close()


@pytest.mark.parametrize("action", ["loose", "formless-field"])
def test_arm_without_an_operation_field_in_the_form_writes_every_operation_input(browser, action):
    # Unicorn reads the id from a board field outside the action forms, and a
    # control can also sit outside any form.
    context = browser.new_context()
    try:
        page = context.new_page()
        page.set_content("""<!doctype html><html><body>
<button data-bench-action="loose">Loose</button><input name="operation" value="manual">
<form><input name="operation" value="manual"></form>
<form><button data-bench-action="formless-field">Go</button></form>
</body></html>""")
        page.evaluate(SCRIPT)
        page.evaluate("action => window.__citryBench.arm({operation: 'op-2', event: 'click', action})", action)
        values = "() => Array.from(document.querySelectorAll('input[name=operation]'), input => input.value)"
        assert page.evaluate(values) == ["op-2", "op-2"]
    finally:
        context.close()
