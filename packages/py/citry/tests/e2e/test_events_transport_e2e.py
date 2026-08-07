"""
Browser e2e for the events transport, the wire half of the client runtime
shipped as ``citry/ext/events/client/citry-events.js`` (design contract:
docs/design/events.md 4.2/4.5/5.2/5.6/6.1/6.2/7.4). This suite covers what
goes on the wire and how the wire's outcomes settle callers:

- Envelope construction locked against the protocol package's call examples:
  the protocol string, the minted request ID, the capabilities field
  (``morph`` plus the protocol baseline), and per call the component, event,
  instance, args, echoed state token, pending updates, and the send-side
  `sendSequence` increment (design 4.2).
- The fetch transport: ``Content-Type: application/citry-events+json``, the
  ``X-Citry-Events`` floor header, and the CSRF token from the default
  Django cookie or a configured token source (design 6.2, 7.4); the
  per-event URL for a single call versus the batch endpoint for a shared
  envelope (design 3.8).
- Promise settlement: resolution with the ``data`` action's value, an
  undefined resolution for a result with no data action, and structured
  rejection with the error result's exact
  ``{status, code, message, fieldErrors?}``
  envelope; ``$error`` and the ``citry:events:before``/``:after``/``:error``
  lifecycle events around both outcomes (design 5.2).
- The bounded timeout (design 5.6): a hung request rejects at the configured
  timeout with the client-minted ``{status: 0, code: "timeout"}`` shape and
  fires ``citry:events:error``; a response arriving afterwards is dropped
  whole, with the drop event (reason ``timeout``) and a debug log.
- A ``citry:events:before`` listener's ``preventDefault`` stopping the send
  before anything hits the wire (promise rejected, no epoch increment, no
  ``$error``).
- Version-skew surfacing (design 4.5): a ``stale_state`` error result and a
  capabilities-mismatch response both fire ``citry:events:stale`` with
  reason ``version`` (no call promise rides the event), and the default soft
  reload prompt is suppressible by ``preventDefault`` on that event and asks
  at most once per page.
- ``configure`` field by field (design 5.2's table): ``csrf`` (cookie
  rename, header rename, token source), ``timeout``, ``transport``
  (including the pointed error for an unregistered name), and ``url``.
- ``registerTransport`` routing ``send`` through a registered fake, and
  ``Content-Disposition`` responses taking the blob download path with
  filename fallback and sanitization, late-response isolation, and cleanup
  when the browser refuses to start the save.
- One full round trip against a live server: the spec's counter component,
  no interception anywhere.

Uses the live-server harness (conftest ``serve_live``) like the sibling
suites; wire-level tests intercept the events routes with Playwright's
``page.route`` so the request the runtime built is observable byte for byte.
Locked strings and shapes were observed from the real runtime first, then
locked.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events import actions, event

pytestmark = pytest.mark.e2e

SIGNING_KEY = "e2e-secret"

READY = "window.Citry && Citry.events && Citry.events._internal && Citry.events._internal.alpineStarted === true"

TESTS_DIR = Path(__file__).resolve().parents[4] / "protocol" / "events" / "v1" / "tests"

# Registered on every page before anything sends: collects the lifecycle
# events this suite asserts (design 5.2's detail contract).
_SETUP_LOGS = """
() => {
  window.__log = { before: [], after: [], error: [], stale: [] };
  document.addEventListener("citry:events:before", (e) => {
    window.__log.before.push({ instance: e.detail.instance, cls: e.detail.class, event: e.detail.event });
    if (window.__cancelNextSend) {
      window.__cancelNextSend = false;
      e.preventDefault();
    }
  });
  document.addEventListener("citry:events:after", (e) => {
    window.__log.after.push({ event: e.detail.event, ok: e.detail.ok });
  });
  document.addEventListener("citry:events:error", (e) => {
    window.__log.error.push({ event: e.detail.event, error: e.detail.error });
  });
  document.addEventListener("citry:events:stale", (e) => {
    window.__log.stale.push({ instance: e.detail.instance, event: e.detail.event, reason: e.detail.reason });
    if (window.__preventStaleDefault) e.preventDefault();
  });
}
"""


def _collect_console(page: Any) -> list[str]:
    """Start collecting console messages as ``type:text`` strings."""
    messages: list[str] = []
    page.on("console", lambda msg: messages.append(f"{msg.type}:{msg.text}"))
    return messages


def _citry_errors(messages: list[str]) -> list[str]:
    return [m for m in messages if m.startswith("error:")]


def _make_todo_page(*, max_envelope_bytes: int | None = None) -> tuple[Citry, str, type[Component]]:
    """One interactive Todo instance on a document page; returns (citry, html, Todo)."""
    extensions_defaults = {"events": {"_max_envelope_bytes": max_envelope_bytes}} if max_envelope_bytes else None
    c = Citry(secret=SIGNING_KEY, extensions_defaults=extensions_defaults)
    c.set_mounted_prefix("/citry")

    class TodoState:
        query: str = ""
        count: int = 0
        _public = ("query", "count")

    class Todo(Component):
        citry = c
        State = TodoState

        class Events:
            def save(self, state):
                return None

            def find(self, state):
                return None

            def notify(self):
                return None

            @event(methods=("GET",))
            def preview(self):
                return None

            @event(methods=("GET",))
            def peek(self, state):
                return None

        template = """
          <div class="todo">
            <span class="q" x-text="$state.query"></span>
            <span class="busy" x-text="$loading() ? 'busy' : 'idle'"></span>
            <span class="err" x-text="$error() ? $error().code : 'none'"></span>
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>transport e2e</title></head>
            <body>
              <c-todo query="shoes" />
            </body>
          </html>
        """

    return c, str(Page()), Todo


def _goto_todo(page: Any, serve_live: Any) -> tuple[list[str], type[Component]]:
    """Serve the Todo page, open it, wait for the runtime; returns (console log, Todo)."""
    c, html, todo = _make_todo_page()
    messages = _collect_console(page)
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.evaluate(_SETUP_LOGS)
    return messages, todo


def _intercept_events(page: Any, result_envelope: dict | None = None) -> list[dict]:
    """
    Intercept the events wire routes; returns the growing capture list.

    Each captured entry is ``{url, headers, body}`` (headers lowercased by
    Playwright, body parsed as JSON). Every request is answered with
    ``result_envelope`` (a data-only ok result by default) under the batch
    rule ``results[i] answers calls[i]``.
    """
    captured: list[dict] = []

    def handle(route: Any) -> None:
        body = json.loads(route.request.post_data or "null")
        captured.append({"url": route.request.url, "headers": route.request.headers, "body": body})
        if result_envelope is not None:
            envelope = json.loads(json.dumps(result_envelope))
            if envelope.get("requestId") is not None and isinstance(body, dict):
                envelope["requestId"] = body.get("requestId", "r_?")
                for result, call in zip(envelope.get("results", []), body.get("calls", []), strict=False):
                    if isinstance(result, dict) and "sendSequence" in call:
                        result["sendSequence"] = call["sendSequence"]
        else:
            calls = body["calls"] if isinstance(body, dict) else []
            envelope = {
                "protocol": "citry-events/1",
                "requestId": body.get("requestId", "r_?") if isinstance(body, dict) else "r_?",
                "results": [
                    {
                        "ok": True,
                        "sendSequence": call.get("sendSequence"),
                        "actions": [{"action": "data", "value": {"slot": i}}],
                    }
                    for i, call in enumerate(calls)
                ],
            }
        route.fulfill(status=200, content_type="application/json", body=json.dumps(envelope))

    page.route("**/ext/events/e/**", handle)
    page.route("**/ext/events/call", handle)
    return captured


_SEND_AND_WAIT = """
async ([name, args, opts]) => {
  const id = document.querySelector(".todo").getAttribute("data-cid");
  try {
    const value = await Citry.events.send(id, name, args || {}, opts || undefined);
    return ["ok", value === undefined ? "__undefined__" : value];
  } catch (err) {
    return ["err", err && err.code ? err : String((err && err.message) || err)];
  }
}
"""


# ----- envelope construction and endpoint selection -----


def test_declared_get_uses_query_transport_and_preserves_pending_writes(page: Any, serve_live: Any) -> None:
    messages, _todo = _goto_todo(page, serve_live)
    captured: list[dict[str, Any]] = []

    def handle(route: Any) -> None:
        request = route.request
        query = parse_qs(urlparse(request.url).query)
        if request.method == "GET":
            captured.append({"method": request.method, "url": request.url, "headers": request.headers})
            epoch = int(query["_citry_send_sequence"][0])
            correlation_id = query["_citry_request_id"][0]
        else:
            body = json.loads(request.post_data)
            captured.append({"method": request.method, "url": request.url, "headers": request.headers, "body": body})
            epoch = body["calls"][0]["sendSequence"]
            correlation_id = body["requestId"]
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "protocol": "citry-events/1",
                    "requestId": correlation_id,
                    "results": [{"ok": True, "sendSequence": epoch, "actions": []}],
                }
            ),
        )

    page.route("**/ext/events/e/**", handle)
    page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          Citry.events._internal.getAnchor(id).stateProxy.query = "typed";
        }
        """
    )

    get_args = {"term": "hi", "page": 3, "active": True, "tag": ["a", "b"]}
    assert page.evaluate(_SEND_AND_WAIT, ["preview", get_args, None]) == [
        "ok",
        "__undefined__",
    ]
    pending_after_get = page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          return Citry.events._internal.getAnchor(id).pending;
        }
        """
    )
    assert pending_after_get == {"query": "typed"}

    assert page.evaluate(_SEND_AND_WAIT, ["peek", {}, None]) == ["ok", "__undefined__"]
    assert page.evaluate(_SEND_AND_WAIT, ["notify", {}, None]) == ["ok", "__undefined__"]
    get_request, stateful_get_request, post_request = captured
    query = parse_qs(urlparse(get_request["url"]).query)
    assert get_request["method"] == "GET"
    assert query["term"] == ["hi"]
    assert query["page"] == ["3"]
    assert query["active"] == ["true"]
    assert query["tag"] == ["a", "b"]
    assert query["_citry_caller_render_id"]
    assert "_citry_state_token" not in query
    assert query["_citry_send_sequence"] == ["1"]
    assert query["_citry_protocol"] == ["citry-events/1"]
    assert query["_citry_request_id"][0].startswith("r_")
    assert json.loads(query["_citry_capabilities"][0]) == {
        "swaps": ["morph", "replace", "inner", "append", "prepend", "remove", "none"],
        "actions": ["render", "data", "state", "event", "redirect", "url"],
    }
    assert "x-citry-events" not in get_request["headers"]
    assert "content-type" not in get_request["headers"]
    stateful_query = parse_qs(urlparse(stateful_get_request["url"]).query)
    assert stateful_get_request["method"] == "GET"
    assert stateful_query["_citry_state_token"]
    assert stateful_query["_citry_send_sequence"] == ["2"]
    assert post_request["method"] == "POST"
    assert post_request["body"]["calls"][0]["stateToken"].startswith("cev1.")
    assert post_request["body"]["calls"][0]["stateUpdates"] == {"query": "typed"}
    assert not _citry_errors(messages)


def test_live_stateful_get_echoes_the_browser_id_and_negotiates_morph(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ReadState:
        count: int = 0

    class ReadCard(Component):
        citry = c
        State = ReadState

        class Kwargs:
            count: int = 0

        class Events:
            @event(methods=("GET",))
            def refresh(self, state):
                return ReadCard(count=state.count)

        def template_data(self, kwargs, slots):
            return {"count": kwargs.count}

        template = """
          <button class="read-card" @c-click="refresh">
            Count {{ count }}
          </button>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>live GET transport</title></head>
            <body><c-read-card /></body>
          </html>
        """

    messages = _collect_console(page)
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    with page.expect_response(lambda response: f"/e/{ReadCard.class_id}/refresh" in response.url) as response_info:
        page.click(".read-card")
    response = response_info.value
    query = parse_qs(urlparse(response.request.url).query)
    payload = response.json()

    assert response.request.method == "GET"
    assert query["_citry_state_token"]
    assert query["_citry_protocol"] == ["citry-events/1"]
    assert payload["requestId"] == query["_citry_request_id"][0]
    assert payload["results"][0]["actions"][0]["swap"] == "morph"
    page.wait_for_function("document.querySelector('.read-card')?.innerText.includes('Count 0')")
    assert not _citry_errors(messages)


def test_envelope_locked_against_protocol_examples_and_send_sequence(page: Any, serve_live: Any) -> None:
    # The envelope the runtime builds, locked field by field against the
    # protocol package's call examples: same top-level vocabulary, same
    # per-call field vocabulary, the capabilities constant advertising morph
    # plus the baseline, and the send-side sequence increment echoed per call
    # (design 4.2). A queued $state write rides as `stateUpdates` and the second
    # send carries the next sequence without them.
    messages, todo = _goto_todo(page, serve_live)
    captured = _intercept_events(page)

    page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          Citry.events._internal.getAnchor(id).stateProxy.query = "typed";
        }
        """
    )
    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {"extra": 1}, None])
    assert outcome == ["ok", {"slot": 0}]

    live_id = page.evaluate("document.querySelector('.todo').getAttribute('data-cid')")
    sent = captured[0]["body"]
    # The envelope's top-level vocabulary is the examples' (batch_two carries
    # the optional capabilities field; the runtime always advertises).
    fixture_envelope = json.loads((TESTS_DIR / "batch_two.call.json").read_text(encoding="utf-8"))
    assert set(sent) == set(fixture_envelope) == {"protocol", "requestId", "capabilities", "calls"}
    assert sent["protocol"] == fixture_envelope["protocol"] == "citry-events/1"
    assert sent["requestId"].startswith("r_")
    # Morph plus the protocol baseline (the spec's section 5 constant).
    assert sent["capabilities"] == {
        "swaps": ["morph", "replace", "inner", "append", "prepend", "remove", "none"],
        "actions": ["render", "data", "state", "event", "redirect", "url"],
    }
    # The call carries every example call field (the examples' vocabulary is
    # the contract; `stateUpdates` is the design 4.2 example's optional extra).
    fixture_call = fixture_envelope["calls"][0]
    assert set(fixture_call) <= set(sent["calls"][0])
    assert sent["calls"] == [
        {
            "componentClassId": todo.class_id,
            "handlerName": "save",
            "callerRenderId": live_id,
            "args": {"extra": 1},
            "stateToken": sent["calls"][0]["stateToken"],
            "stateUpdates": {"query": "typed"},
            "sendSequence": 1,
        }
    ]
    assert sent["calls"][0]["stateToken"].startswith("cev1.")

    # The second send: the anchor's counter incremented again, and with no
    # pending writes the `stateUpdates` field stays off the wire.
    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert outcome == ["ok", {"slot": 0}]
    second = captured[1]["body"]["calls"][0]
    assert second["sendSequence"] == 2
    assert "stateUpdates" not in second
    anchor_epoch = page.evaluate(
        "Citry.events._internal.getAnchor(document.querySelector('.todo').getAttribute('data-cid')).epoch"
    )
    assert anchor_epoch == 2
    assert _citry_errors(messages) == []


def test_per_event_url_for_one_call_and_batch_endpoint_for_several(page: Any, serve_live: Any) -> None:
    # Endpoint selection (design 3.8): a single call POSTs to the per-event
    # route (so host middleware and access logs see the real per-handler
    # URL), while several calls ride one envelope to the batch endpoint, each
    # keeping its own promise settled by its own result slot.
    messages, todo = _goto_todo(page, serve_live)
    captured = _intercept_events(page)

    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert outcome == ["ok", {"slot": 0}]
    assert captured[0]["url"].endswith(f"/citry/ext/events/e/{todo.class_id}/save")
    assert captured[0]["headers"]["content-type"] == "application/citry-events+json"

    outcomes = page.evaluate(
        """
        async () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const promises = Citry.events._internal.sendCalls([
            { target: id, name: "save", args: { a: 1 } },
            { target: id, name: "find", args: { b: 2 } },
          ]);
          return await Promise.all(promises);
        }
        """
    )
    assert outcomes == [{"slot": 0}, {"slot": 1}]
    batch = captured[1]
    assert batch["url"].endswith("/citry/ext/events/call")
    assert [call["handlerName"] for call in batch["body"]["calls"]] == ["save", "find"]
    assert [call["sendSequence"] for call in batch["body"]["calls"]] == [2, 3]
    assert _citry_errors(messages) == []


# ----- CSRF attachment -----


def test_csrf_header_from_the_default_cookie_and_from_a_token_source(page: Any, serve_live: Any) -> None:
    # The CSRF autowiring (design 7.4): by default the runtime reads Django's
    # `csrftoken` cookie and sends it as `X-CSRFToken`, alongside the
    # always-on `X-Citry-Events` floor header; a configured `token` source (a
    # zero-arg function here) with a renamed header replaces both sides, and
    # the default header stops being sent.
    messages, _ = _goto_todo(page, serve_live)
    captured = _intercept_events(page)

    page.evaluate("document.cookie = 'csrftoken=cookie-tok-1; path=/'")
    page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    headers = captured[0]["headers"]
    assert headers["x-citry-events"] == "1"
    assert headers["x-csrftoken"] == "cookie-tok-1"

    page.evaluate(
        """
        () => Citry.events.configure({
          csrf: { token: () => "fn-tok-2", header: "X-Custom-CSRF" },
        })
        """
    )
    page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    headers = captured[1]["headers"]
    assert headers["x-custom-csrf"] == "fn-tok-2"
    assert "x-csrftoken" not in headers
    assert headers["x-citry-events"] == "1"
    assert _citry_errors(messages) == []


# ----- promise settlement and the lifecycle surface -----


def test_data_resolves_error_result_rejects_structured_and_lifecycle_fires(page: Any, serve_live: Any) -> None:
    # Settlement (design 5.2): the caller resolves with the data action's
    # value; an error result rejects with the server's exact {status, code,
    # message, fieldErrors} envelope, sets $error, and fires citry:events:error;
    # citry:events:before/:after bracket both outcomes (`ok` says which); the
    # next success for the same handler clears $error.
    messages, _ = _goto_todo(page, serve_live)

    error_envelope = {
        "protocol": "citry-events/1",
        "requestId": "r_x",
        "results": [
            {
                "ok": False,
                "error": {
                    "status": 422,
                    "code": "invalid_args",
                    "message": "Validation failed for 1 field(s).",
                    "fieldErrors": {"text": "Required."},
                },
            }
        ],
    }
    captured = _intercept_events(page)
    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert outcome == ["ok", {"slot": 0}]
    assert page.locator(".err").inner_text() == "none"

    page.unroute("**/ext/events/e/**")
    page.unroute("**/ext/events/call")
    _intercept_events(page, result_envelope=error_envelope)
    outcome = page.evaluate(_SEND_AND_WAIT, ["find", {}, None])
    assert outcome == [
        "err",
        {
            "status": 422,
            "code": "invalid_args",
            "message": "Validation failed for 1 field(s).",
            "fieldErrors": {"text": "Required."},
        },
    ]
    page.wait_for_function("document.querySelector('.err').innerText === 'invalid_args'")

    # The next successful call for `find` clears its retained error.
    page.unroute("**/ext/events/e/**")
    page.unroute("**/ext/events/call")
    _intercept_events(page)
    page.evaluate(_SEND_AND_WAIT, ["find", {}, None])
    page.wait_for_function("document.querySelector('.err').innerText === 'none'")

    log = page.evaluate("window.__log")
    assert [entry["event"] for entry in log["before"]] == ["save", "find", "find"]
    assert log["after"] == [
        {"event": "save", "ok": True},
        {"event": "find", "ok": False},
        {"event": "find", "ok": True},
    ]
    assert log["error"] == [
        {
            "event": "find",
            "error": {
                "status": 422,
                "code": "invalid_args",
                "message": "Validation failed for 1 field(s).",
                "fieldErrors": {"text": "Required."},
            },
        }
    ]
    assert log["stale"] == []
    assert _citry_errors(messages) == []
    assert len(captured) == 1


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("wrong_protocol", "header"),
        ("wrong_id", "correlation"),
        ("missing_result", "header"),
        ("extra_result", "correlation"),
        ("missing_send_sequence", "result 0"),
        ("wrong_send_sequence", "result 0"),
        ("missing_actions", "result 0"),
        ("data_wait_false", "result 0"),
        ("data_wait_true", "result 0"),
        ("malformed_error", "result 0"),
        ("out_of_range_error_status", "result 0"),
        ("empty_error_code", "result 0"),
        ("empty_error_message", "result 0"),
        ("non_string_error_field", "result 0"),
        ("edge_send_sequence", "edge"),
        ("edge_wrong_code", "edge"),
        ("edge_field_errors", "edge"),
    ],
)
def test_result_envelope_preflight_rejects_malformed_responses_atomically(
    page: Any,
    serve_live: Any,
    case: str,
    reason: str,
) -> None:
    messages, _ = _goto_todo(page, serve_live)
    outcome = page.evaluate(
        """
        async (caseName) => {
          Citry.events.registerTransport("malformed", {
            send: (envelope) => {
              const call = envelope.calls[0];
              const response = {
                protocol: envelope.protocol,
                requestId: envelope.requestId,
                results: [{ ok: true, sendSequence: call.sendSequence, actions: [] }],
              };
              if (caseName === "wrong_protocol") response.protocol = "citry-events/2";
              if (caseName === "wrong_id") response.requestId = "r_someone_else";
              if (caseName === "missing_result") response.results = [];
              if (caseName === "extra_result") response.results.push({ ...response.results[0] });
              if (caseName === "missing_send_sequence") delete response.results[0].sendSequence;
              if (caseName === "wrong_send_sequence") response.results[0].sendSequence += 1;
              if (caseName === "missing_actions") delete response.results[0].actions;
              if (caseName === "data_wait_false" || caseName === "data_wait_true") {
                response.results[0].actions = [{
                  action: "data",
                  value: 1,
                  wait: caseName === "data_wait_true",
                }];
              }
              if ([
                "malformed_error",
                "out_of_range_error_status",
                "empty_error_code",
                "empty_error_message",
                "non_string_error_field",
              ].includes(caseName)) {
                response.results[0] = {
                  ok: false,
                  sendSequence: call.sendSequence,
                  error: { status: 422, code: "invalid_args", message: "bad" },
                };
              }
              if (caseName === "malformed_error") response.results[0].error.status = "422";
              if (caseName === "out_of_range_error_status") response.results[0].error.status = 399;
              if (caseName === "empty_error_code") response.results[0].error.code = "";
              if (caseName === "empty_error_message") response.results[0].error.message = "";
              if (caseName === "non_string_error_field") response.results[0].error.fieldErrors = { name: 1 };
              if (caseName === "edge_send_sequence") {
                response.requestId = null;
                response.results[0] = {
                  ok: false,
                  sendSequence: call.sendSequence,
                  error: { status: 400, code: "protocol_mismatch", message: "bad" },
                };
              }
              if (caseName === "edge_wrong_code") {
                response.requestId = null;
                response.results[0] = {
                  ok: false,
                  error: { status: 422, code: "invalid_args", message: "bad" },
                };
              }
              if (caseName === "edge_field_errors") {
                response.requestId = null;
                response.results[0] = {
                  ok: false,
                  error: {
                    status: 400,
                    code: "protocol_mismatch",
                    message: "bad",
                    fieldErrors: { name: "not available before parsing" },
                  },
                };
              }
              return response;
            },
          });
          Citry.events.configure({ transport: "malformed" });
          const id = document.querySelector(".todo").getAttribute("data-cid");
          try {
            await Citry.events.send(id, "save", {});
            return ["ok"];
          } catch (error) {
            const anchor = Citry.events._internal.getAnchor(id);
            return ["err", error, anchor.loading.any, anchor.errorBox.current];
          }
        }
        """,
        case,
    )
    assert outcome[0] == "err"
    assert outcome[1] == {
        "status": 0,
        "code": "transport_error",
        "message": f"invalid event response ({reason}).",
    }
    assert outcome[2] == 0
    assert outcome[3] == outcome[1]
    assert page.evaluate("window.__log.after") == [{"event": "save", "ok": False}]
    assert page.evaluate("window.__log.error[0].error") == outcome[1]
    assert _citry_errors(messages) == []


def test_preflight_rejects_a_two_call_envelope_before_the_first_slot_applies(page: Any, serve_live: Any) -> None:
    messages, _ = _goto_todo(page, serve_live)
    outcome = page.evaluate(
        """
        async () => {
          history.replaceState({ kept: true }, "", "/before-preflight");
          Citry.events.registerTransport("bad-second-slot", {
            send: (envelope) => ({
              protocol: envelope.protocol,
              requestId: envelope.requestId,
              results: [
                {
                  ok: true,
                  sendSequence: envelope.calls[0].sendSequence,
                  actions: [
                    { action: "url", url: "/must-not-apply", mode: "push" },
                    { action: "data", value: "first-must-not-resolve" },
                  ],
                },
                { ok: true, sendSequence: envelope.calls[1].sendSequence },
              ],
            }),
          });
          Citry.events.configure({ transport: "bad-second-slot" });
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const promises = Citry.events._internal.sendCalls([
            { target: id, name: "save", args: {} },
            { target: id, name: "find", args: {} },
          ]);
          const settled = await Promise.all(promises.map((promise) => promise.then(
            (value) => ["ok", value],
            (error) => ["err", error],
          )));
          const anchor = Citry.events._internal.getAnchor(id);
          return { settled, path: location.pathname, loading: anchor.loading.any };
        }
        """
    )
    assert [entry[0] for entry in outcome["settled"]] == ["err", "err"]
    assert [entry[1]["code"] for entry in outcome["settled"]] == ["transport_error", "transport_error"]
    assert [entry[1]["message"] for entry in outcome["settled"]] == ["invalid event response (result 1)."] * 2
    assert outcome["path"] == "/before-preflight"
    assert outcome["loading"] == 0
    assert page.evaluate("window.__log.after") == [
        {"event": "save", "ok": False},
        {"event": "find", "ok": False},
    ]
    assert _citry_errors(messages) == []


def test_transport_edge_sentinel_fans_one_structured_error_across_the_batch(page: Any, serve_live: Any) -> None:
    c, html, _todo = _make_todo_page(max_envelope_bytes=512)
    messages = _collect_console(page)
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.evaluate(_SETUP_LOGS)
    outcome = page.evaluate(
        """
        async () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          Citry.events._internal.getAnchor(id).stateProxy.query = "retry-me";
          const promises = Citry.events._internal.sendCalls([
            { target: id, name: "save", args: { large: "x".repeat(2000) } },
            { target: id, name: "find", args: {} },
          ]);
          const settled = await Promise.all(promises.map((promise) => promise.then(
            () => ["ok"],
            (reason) => ["err", reason],
          )));
          const anchor = Citry.events._internal.getAnchor(id);
          return { settled, pending: anchor.pending, loading: anchor.loading.any };
        }
        """,
    )
    first_error = outcome["settled"][0][1]
    assert outcome["settled"] == [["err", first_error], ["err", first_error]]
    assert first_error["status"] == 413
    assert first_error["code"] == "payload_too_large"
    assert "the cap is 512" in first_error["message"]
    assert outcome["pending"] == {"query": "retry-me"}
    assert outcome["loading"] == 0
    assert page.evaluate("window.__log.error.map((entry) => entry.error)") == [first_error, first_error]
    assert _citry_errors(messages) == []


def test_non_2xx_response_with_unknown_protocol_fields_is_rejected_strictly(page: Any, serve_live: Any) -> None:
    messages, _ = _goto_todo(page, serve_live)
    server_error = {
        "status": 429,
        "code": "error",
        "message": "Try this event again shortly.",
        "fieldErrors": {"future": "kept"},
    }

    def handle(route: Any) -> None:
        request_envelope = json.loads(route.request.post_data)
        route.fulfill(
            status=429,
            content_type="text/plain",
            body=json.dumps(
                {
                    "protocol": "citry-events/1",
                    "requestId": request_envelope["requestId"],
                    "results": [
                        {
                            "ok": False,
                            "sendSequence": request_envelope["calls"][0]["sendSequence"],
                            "error": server_error,
                            "future_result_field": True,
                        }
                    ],
                    "future_envelope_field": True,
                }
            ),
        )

    page.route("**/ext/events/e/**", handle)
    expected = {
        "status": 0,
        "code": "transport_error",
        "message": "invalid event response (header).",
    }
    assert page.evaluate(_SEND_AND_WAIT, ["save", {}, None]) == ["err", expected]
    assert page.evaluate("window.__log.after") == [{"event": "save", "ok": False}]
    assert page.evaluate("window.__log.error[0].error") == expected
    browser_errors = _citry_errors(messages)
    assert all("responded with a status of 429" in message for message in browser_errors)


@pytest.mark.parametrize(
    ("status", "content_type", "body"),
    [
        (502, "text/plain", ""),
        (503, "text/html", "<h1>upstream unavailable</h1>"),
        (504, "application/json", "{}"),
    ],
)
def test_invalid_http_responses_reject_with_status_and_balance_lifecycle(
    page: Any,
    serve_live: Any,
    status: int,
    content_type: str,
    body: str,
) -> None:
    _messages, _ = _goto_todo(page, serve_live)
    page.route(
        "**/ext/events/e/**",
        lambda route: route.fulfill(status=status, content_type=content_type, body=body),
    )
    expected = {
        "status": status,
        "code": "transport_error",
        "message": f"the events endpoint answered {status} without a result envelope.",
    }
    assert page.evaluate(_SEND_AND_WAIT, ["save", {}, None]) == ["err", expected]
    state = page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          return { loading: anchor.loading.any, error: anchor.errorBox.current };
        }
        """
    )
    assert state == {"loading": 0, "error": expected}
    assert page.evaluate("window.__log.after") == [{"event": "save", "ok": False}]
    assert page.evaluate("window.__log.error[0].error") == expected


def test_client_minted_transport_error_omits_fields_everywhere(page: Any, serve_live: Any) -> None:
    messages, _ = _goto_todo(page, serve_live)
    outcome = page.evaluate(
        """async () => {
          Citry.events.registerTransport('offline', {
            send: () => Promise.reject(new Error('offline now')),
          });
          Citry.events.configure({ transport: 'offline' });
          const id = document.querySelector('.todo').getAttribute('data-cid');
          try {
            await Citry.events.send(id, 'save', {});
          } catch (error) {
            const anchor = Citry.events._internal.getAnchor(id);
            return {
              rejection: error,
              stored: anchor.errorBox.current,
              lifecycle: window.__log.error[0].error,
            };
          }
        }"""
    )
    expected = {"status": 0, "code": "transport_error", "message": "offline now"}
    assert outcome == {"rejection": expected, "stored": expected, "lifecycle": expected}
    assert _citry_errors(messages) == []


def test_get_encoding_rejects_unrepresentable_values_without_a_request(page: Any, serve_live: Any) -> None:
    messages, _ = _goto_todo(page, serve_live)
    captured = _intercept_events(page)
    outcome = page.evaluate(
        """
        async () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          anchor.stateProxy.query = "still-pending";
          const cases = [
            ["nested", { nested: { value: 1 } }],
            ["null", { value: null }],
            ["empty", { values: [] }],
            ["nonfinite", { value: Number.POSITIVE_INFINITY }],
          ];
          const settled = [];
          for (const [name, args] of cases) {
            try {
              await Citry.events.send(id, "preview", args);
              settled.push([name, "ok"]);
            } catch (error) {
              settled.push([name, "err", {
                status: typeof error?.status === "number" ? error.status : null,
                code: typeof error?.code === "string" ? error.code : null,
                message: String(error && (error.message || error)),
              }]);
            }
          }
          return {
            settled,
            pending: anchor.pending,
            loading: anchor.loading.any,
            handlerLoading: anchor.loading.handlers.preview || 0,
          };
        }
        """
    )
    assert [entry[:2] for entry in outcome["settled"]] == [
        ["nested", "err"],
        ["null", "err"],
        ["empty", "err"],
        ["nonfinite", "err"],
    ]
    errors = [entry[2] for entry in outcome["settled"]]
    assert all(error["status"] == 0 and error["code"] == "transport_error" for error in errors[:3])
    assert errors[3]["status"] is None
    assert errors[3]["code"] is None
    assert "field 'nested' is not representable" in errors[0]["message"]
    assert "field 'value' is not representable" in errors[1]["message"]
    assert "cannot represent an empty array" in errors[2]["message"]
    assert "must be a strict JSON object" in errors[3]["message"]
    assert captured == []
    assert outcome["pending"] == {"query": "still-pending"}
    assert outcome["loading"] == 0
    assert outcome["handlerLoading"] == 0
    assert page.evaluate("window.__log.after") == [
        {"event": "preview", "ok": False},
        {"event": "preview", "ok": False},
        {"event": "preview", "ok": False},
    ]
    assert page.evaluate("window.__log.error.map((entry) => entry.error.code)") == ["transport_error"] * 3
    assert _citry_errors(messages) == []


def test_custom_transport_sync_throw_and_structured_async_rejection_balance_lifecycle(
    page: Any,
    serve_live: Any,
) -> None:
    messages, _ = _goto_todo(page, serve_live)
    expected_structured = {
        "status": 451,
        "code": "policy_blocked",
        "message": "The custom transport blocked this call.",
        "fieldErrors": {"reason": "local policy"},
    }
    outcome = page.evaluate(
        """
        async (structured) => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          Citry.events.registerTransport("sync-throw", {
            send: () => { throw new Error("sync transport failed"); },
          });
          Citry.events.registerTransport("async-structured", {
            send: () => Promise.reject(structured),
          });
          const settled = [];
          for (const name of ["sync-throw", "async-structured"]) {
            Citry.events.configure({ transport: name });
            try {
              await Citry.events.send(id, "save", {});
              settled.push(["ok"]);
            } catch (error) {
              settled.push(["err", error]);
            }
          }
          const anchor = Citry.events._internal.getAnchor(id);
          return { settled, loading: anchor.loading.any, stored: anchor.errorBox.current };
        }
        """,
        expected_structured,
    )
    expected_sync = {"status": 0, "code": "transport_error", "message": "sync transport failed"}
    assert outcome == {
        "settled": [["err", expected_sync], ["err", expected_structured]],
        "loading": 0,
        "stored": expected_structured,
    }
    assert page.evaluate("window.__log.after") == [
        {"event": "save", "ok": False},
        {"event": "save", "ok": False},
    ]
    assert page.evaluate("window.__log.error.map((entry) => entry.error)") == [expected_sync, expected_structured]
    assert _citry_errors(messages) == []


def test_before_preventdefault_stops_the_send_before_the_wire(page: Any, serve_live: Any) -> None:
    # citry:events:before is cancellable (design 5.2): preventDefault stops
    # the send (nothing hits the wire, the anchor's epoch counter never
    # moves) and rejects the caller's promise with the client-minted
    # `cancelled` shape. The cancel is the page's own act, so no $error, no
    # error event, no drop event; :after still fires so before/after pairs
    # stay balanced for progress indicators.
    messages, _ = _goto_todo(page, serve_live)
    captured = _intercept_events(page)

    page.evaluate("window.__cancelNextSend = true")
    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert outcome == [
        "err",
        {"status": 0, "code": "cancelled", "message": "a citry:events:before listener stopped the send of 'save'."},
    ]
    assert captured == []
    state = page.evaluate(
        """
        () => {
          const anchor = Citry.events._internal.getAnchor(document.querySelector('.todo').getAttribute('data-cid'));
          return { sendSequence: anchor.epoch, error: anchor.errorBox.current, loading: anchor.loading.any };
        }
        """
    )
    assert state == {"sendSequence": 0, "error": None, "loading": 0}
    log = page.evaluate("window.__log")
    assert log["after"] == [{"event": "save", "ok": False}]
    assert log["error"] == []
    assert log["stale"] == []
    assert _citry_errors(messages) == []


# ----- the bounded timeout -----


def test_timeout_rejects_then_a_late_response_drops(page: Any, serve_live: Any) -> None:
    # The bounded timeout (design 5.6): a hung request rejects the caller at
    # the per-call timeout with the client-minted timeout error and fires
    # citry:events:error; the response arriving afterwards is dropped whole,
    # with the drop event (reason `timeout`) and a debug log, because the
    # caller was already told it failed. The hang and the late delivery are
    # driven through a registered transport whose resolver the test holds,
    # which pins the timing deterministically.
    messages, _ = _goto_todo(page, serve_live)

    page.evaluate(
        """
        () => {
          history.replaceState({ router: "kept" }, "", "/before-timeout");
          window.__historyBefore = {
            path: location.pathname,
            length: history.length,
            state: history.state,
          };
          window.__deliver = null;
          Citry.events.registerTransport("held", {
            send: (envelope) => new Promise((resolve) => {
              window.__sentEnvelope = envelope;
              window.__deliver = resolve;
            }),
          });
          Citry.events.configure({ transport: "held" });
        }
        """
    )
    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, {"timeout": 250}])
    assert outcome == [
        "err",
        {
            "status": 0,
            "code": "timeout",
            "message": "'save' timed out after 250 ms; raise it per call (sendEvent opts)"
            " or page-wide (Citry.events.configure({timeout})).",
        },
    ]
    page.wait_for_function("document.querySelector('.err').innerText === 'timeout'")
    log = page.evaluate("window.__log")
    assert log["after"] == [{"event": "save", "ok": False}]
    assert [entry["error"]["code"] for entry in log["error"]] == ["timeout"]
    assert log["stale"] == []

    # Deliver the response late: its whole application drops (the DOM query
    # span never updates), the drop event fires with reason `timeout`, and
    # the debug log names the drop.
    page.evaluate(
        """
        () => window.__deliver({
          protocol: "citry-events/1",
          requestId: window.__sentEnvelope.requestId,
          results: [{
            ok: true,
            sendSequence: window.__sentEnvelope.calls[0].sendSequence,
            actions: [
              {
                action: "state",
                targetRenderId: window.__sentEnvelope.calls[0].callerRenderId,
                stateToken: "cev1.late",
              },
              { action: "url", url: "/late-history", mode: "push" },
              { action: "data", value: { late: true } },
            ],
          }],
        })
        """
    )
    page.wait_for_function("window.__log.stale.length === 1")
    live_id = page.evaluate("document.querySelector('.todo').getAttribute('data-cid')")
    assert page.evaluate("window.__log.stale") == [{"instance": live_id, "event": "save", "reason": "timeout"}]
    drops = [m for m in messages if m.startswith("debug:") and "timed out" in m]
    assert drops == ["debug:[Citry] events: dropped the response of 'save': it arrived after the call timed out."]
    # The late token refresh did not land (the anchor still holds a
    # real minted value, not the late response's marker), and the caller
    # settled exactly once: no second :after rides the dropped response.
    late_token_landed = page.evaluate(
        "Citry.events._internal.getAnchor(document.querySelector('.todo').getAttribute('data-cid')).token"
        " === 'cev1.late'"
    )
    assert late_token_landed is False
    assert page.evaluate(
        """() => ({
          path: location.pathname,
          length: history.length,
          state: history.state,
        })"""
    ) == page.evaluate("window.__historyBefore")
    assert page.evaluate("window.__log.after") == [{"event": "save", "ok": False}]
    assert _citry_errors(messages) == []


def test_timeout_stops_at_response_arrival_while_blocking_actions_keep_the_call_pending(
    page: Any,
    serve_live: Any,
) -> None:
    messages, _ = _goto_todo(page, serve_live)
    page.evaluate(
        """
        () => {
          Citry.events.registerTransport("slow-application", {
            send: (envelope) => ({
              protocol: envelope.protocol,
              requestId: envelope.requestId,
              results: [{
                ok: true,
                sendSequence: envelope.calls[0].sendSequence,
                actions: [{ action: "data", value: { applied: true }, delay: 0.2 }],
              }],
            }),
          });
          Citry.events.configure({ transport: "slow-application" });
          const id = document.querySelector(".todo").getAttribute("data-cid");
          window.__slowApplication = { settled: false, outcome: null };
          Citry.events.send(id, "save", {}, { timeout: 50 }).then(
            (value) => {
              window.__slowApplication.settled = true;
              window.__slowApplication.outcome = ["ok", value];
            },
            (error) => {
              window.__slowApplication.settled = true;
              window.__slowApplication.outcome = ["err", error];
            },
          );
        }
        """
    )
    page.wait_for_timeout(100)
    during = page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          return {
            settled: window.__slowApplication.settled,
            loading: anchor.loading.any,
            after: window.__log.after,
            errors: window.__log.error,
          };
        }
        """
    )
    assert during == {"settled": False, "loading": 1, "after": [], "errors": []}

    page.wait_for_function("window.__slowApplication.settled === true")
    assert page.evaluate("window.__slowApplication.outcome") == ["ok", {"applied": True}]
    assert page.evaluate("window.__log.after") == [{"event": "save", "ok": True}]
    assert page.evaluate("window.__log.error") == []
    assert (
        page.evaluate(
            "Citry.events._internal.getAnchor(document.querySelector('.todo').getAttribute('data-cid')).loading.any"
        )
        == 0
    )
    assert _citry_errors(messages) == []


# ----- version skew -----


def test_stale_state_error_fires_version_skew_and_the_prompt_is_configurable(page: Any, serve_live: Any) -> None:
    # The version-skew flow (design 4.5): a stale_state error result fires
    # citry:events:stale with reason `version` through the dispatch helper,
    # while the call itself settles through its own error result (no promise
    # rides the skew event). The default handling is a soft reload prompt
    # (window.confirm), asked at most once per page; preventDefault on the
    # stale event replaces the default and suppresses the prompt.
    stale_fixture = json.loads((TESTS_DIR / "error_stale_state.result.json").read_text(encoding="utf-8"))
    stale_error = stale_fixture["results"][0]["error"]

    # Page one: default handling. The confirm dialog appears once, and a
    # second stale_state response does not re-ask.
    messages, _ = _goto_todo(page, serve_live)
    dialogs: list[str] = []
    page.on("dialog", lambda dialog: (dialogs.append(f"{dialog.type}:{dialog.message}"), dialog.dismiss()))
    _intercept_events(page, result_envelope=stale_fixture)

    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert outcome == ["err", stale_error]
    page.wait_for_function("window.__log.stale.length === 1")
    assert page.evaluate("window.__log.stale[0].reason") == "version"
    assert dialogs == [
        "confirm:This page and the server are running different versions of the app. Reload to get back in sync?"
    ]

    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert outcome == ["err", stale_error]
    page.wait_for_function("window.__log.stale.length === 2")
    assert len(dialogs) == 1  # once per page, never nagging
    assert _citry_errors(messages) == []


def test_stale_default_is_replaceable_and_unknown_actions_are_rejected_strictly(page: Any, serve_live: Any) -> None:
    # A page can replace the stale-state prompt with preventDefault. Unknown
    # action kinds are protocol errors in v1: the whole response rejects
    # before a later valid action can apply.
    messages, _ = _goto_todo(page, serve_live)
    dialogs: list[str] = []
    page.on("dialog", lambda dialog: (dialogs.append(f"{dialog.type}:{dialog.message}"), dialog.dismiss()))
    page.evaluate("window.__preventStaleDefault = true")

    stale_fixture = json.loads((TESTS_DIR / "error_stale_state.result.json").read_text(encoding="utf-8"))
    _intercept_events(page, result_envelope=stale_fixture)
    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert outcome == ["err", stale_fixture["results"][0]["error"]]
    page.wait_for_function("window.__log.stale.length === 1")
    assert page.evaluate("window.__log.stale[0]") == {
        "instance": page.evaluate("document.querySelector('.todo').getAttribute('data-cid')"),
        "event": "save",
        "reason": "version",
    }
    assert dialogs == []  # preventDefault replaced the soft reload prompt

    outcome = page.evaluate(
        """
        async () => {
          Citry.events.registerTransport("unknown-action", {
            send: (envelope) => ({
              protocol: envelope.protocol,
              requestId: envelope.requestId,
              results: [{
                ok: true,
                sendSequence: envelope.calls[0].sendSequence,
                actions: [
                  { action: "teleport", target: "body" },
                  { action: "data", value: { mustNotResolve: true } },
                ],
              }],
            }),
          });
          Citry.events.configure({ transport: "unknown-action" });
          const id = document.querySelector(".todo").getAttribute("data-cid");
          try {
            await Citry.events.send(id, "save", {});
            return ["ok"];
          } catch (error) {
            return ["err", error];
          }
        }
        """
    )
    assert outcome == [
        "err",
        {"status": 0, "code": "transport_error", "message": "invalid event response (result 0)."},
    ]
    assert page.evaluate("window.__log.stale.length") == 1
    assert _citry_errors(messages) == []


# ----- configure, field by field -----


def test_configure_csrf_renames_timeout_transport_and_url(page: Any, serve_live: Any) -> None:
    # Every configure field of design 5.2's table observably takes effect:
    # `csrf` renames the cookie read and the carrier header (and a string
    # token source wins over the cookie); `url` moves the POST to the
    # configured base (with the missing trailing slash supplied); `transport`
    # selects a registered name and an unregistered one is the pointed
    # error naming the registered set; `timeout` sets the page-wide default.
    messages, todo = _goto_todo(page, serve_live)
    captured = _intercept_events(page)

    # csrf.cookie: read a renamed cookie, carried under the default header.
    page.evaluate("document.cookie = 'csrftoken=default-tok; path=/'")
    page.evaluate("document.cookie = 'renamed_csrf=renamed-tok; path=/'")
    page.evaluate("Citry.events.configure({ csrf: { cookie: 'renamed_csrf' } })")
    page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert captured[0]["headers"]["x-csrftoken"] == "renamed-tok"

    # csrf.header + a string token source.
    page.evaluate("Citry.events.configure({ csrf: { header: 'X-Renamed', token: 'string-tok' } })")
    page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert captured[1]["headers"]["x-renamed"] == "string-tok"
    assert "x-csrftoken" not in captured[1]["headers"]

    # url: the POST moves to the configured base; the missing trailing slash
    # is supplied, and the per-event path shape stays.
    moved: list[str] = []

    def moved_route(route: Any) -> None:
        envelope = json.loads(route.request.post_data)
        moved.append(route.request.url)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "protocol": "citry-events/1",
                    "requestId": envelope["requestId"],
                    "results": [
                        {
                            "ok": True,
                            "sendSequence": envelope["calls"][0]["sendSequence"],
                            "actions": [],
                        }
                    ],
                }
            ),
        )

    page.route(
        "**/custom-events-base/**",
        moved_route,
    )
    page.evaluate("Citry.events.configure({ url: '/custom-events-base' })")
    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert outcome == ["ok", "__undefined__"]
    assert len(moved) == 1
    assert moved[0].endswith(f"/custom-events-base/e/{todo.class_id}/save")

    # transport: an unregistered name rejects with the pointed error naming
    # the registered set (nothing goes on the wire).
    page.evaluate("Citry.events.configure({ transport: 'missing' })")
    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert outcome[0] == "err"
    assert "no events transport is registered under 'missing'" in outcome[1]
    assert "registered: fetch" in outcome[1]

    # timeout: the page-wide default applies when opts carry none.
    page.evaluate(
        """
        () => {
          Citry.events.registerTransport("held", { send: () => new Promise(() => {}) });
          Citry.events.configure({ transport: "held", timeout: 150 });
        }
        """
    )
    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert outcome[0] == "err"
    assert outcome[1]["code"] == "timeout"
    assert "'save' timed out after 150 ms" in outcome[1]["message"]
    assert _citry_errors(messages) == []


def test_register_transport_routes_send_through_a_registered_fake(page: Any, serve_live: Any) -> None:
    # registerTransport (design 5.2/6.1): a registered `{send}` impl receives
    # the whole call envelope and its resolved result envelope settles the
    # caller through the same path as the built-in fetch; selection is
    # configure({transport}).
    messages, _ = _goto_todo(page, serve_live)

    outcome = page.evaluate(
        """
        async () => {
          window.__fakeSeen = [];
          Citry.events.registerTransport("fake", {
            send: (envelope) => {
              window.__fakeSeen.push(envelope);
              return Promise.resolve({
                protocol: envelope.protocol,
                requestId: envelope.requestId,
                results: envelope.calls.map((call) => ({
                  ok: true,
                  sendSequence: call.sendSequence,
                  actions: [{ action: "data", value: { via: "fake" } }],
                })),
              });
            },
          });
          Citry.events.configure({ transport: "fake" });
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const value = await Citry.events.send(id, "save", {});
          return [value, window.__fakeSeen.length, window.__fakeSeen[0].calls[0].handlerName];
        }
        """
    )
    assert outcome == [{"via": "fake"}, 1, "save"]
    assert _citry_errors(messages) == []


# ----- the download escape hatch -----


def test_content_disposition_response_takes_the_blob_download_path(page: Any, serve_live: Any) -> None:
    # The escape-hatch consumer (design 6.2): a response carrying
    # Content-Disposition is a file answer, not an envelope; the transport
    # saves it as a blob download and the caller's promise still settles
    # (resolved with undefined), so nothing hangs on a download.
    messages, _ = _goto_todo(page, serve_live)

    def download_route(route: Any) -> None:
        route.fulfill(
            status=200,
            content_type="text/plain",
            headers={
                "Content-Disposition": (
                    "Attachment; filename=\"fallback;name.txt\"; filename*=UTF-8'en'p%C5%99ehled%3B2026.txt"
                )
            },
            body="file-bytes",
        )

    page.route("**/ext/events/e/**", download_route)
    with page.expect_download() as download_info:
        outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    download = download_info.value
    # WebKit may expose the platform's decomposed Unicode spelling even when
    # the download attribute used the equivalent composed spelling.
    assert unicodedata.normalize("NFC", download.suggested_filename) == "přehled;2026.txt"
    assert Path(download.path()).read_text(encoding="utf-8") == "file-bytes"
    assert outcome == ["ok", "__undefined__"]
    log = page.evaluate("window.__log")
    assert log["after"] == [{"event": "save", "ok": True}]
    assert log["error"] == []
    assert _citry_errors(messages) == []


def test_download_filename_fallbacks_are_sanitized_and_settle_successfully(page: Any, serve_live: Any) -> None:
    messages, _ = _goto_todo(page, serve_live)
    dispositions = iter(
        [
            "attachment; filename=\"dir\\\\report/name.txt\"; filename*=UTF-8''bad%ZZ",
            "attachment",
        ]
    )

    def download_route(route: Any) -> None:
        route.fulfill(
            status=200,
            content_type="application/octet-stream",
            headers={"Content-Disposition": next(dispositions)},
            body="file-bytes",
        )

    page.route("**/ext/events/e/**", download_route)
    outcomes: list[Any] = []
    suggested_filenames: list[str] = []
    for event_name in ("save", "find"):
        with page.expect_download() as download_info:
            outcomes.append(page.evaluate(_SEND_AND_WAIT, [event_name, {}, None]))
        suggested_filenames.append(download_info.value.suggested_filename)

    assert outcomes == [["ok", "__undefined__"], ["ok", "__undefined__"]]
    assert suggested_filenames == ["dir_report_name.txt", "download"]
    log = page.evaluate("window.__log")
    assert log["after"] == [{"event": "save", "ok": True}, {"event": "find", "ok": True}]
    assert log["error"] == []
    decode_warnings = [message for message in messages if "could not decode the download filename" in message]
    assert len(decode_warnings) == 1
    assert _citry_errors(messages) == []


def test_browser_save_failure_rejects_and_cleans_up(page: Any, serve_live: Any) -> None:
    messages, _ = _goto_todo(page, serve_live)
    downloads: list[Any] = []
    page.on("download", lambda download: downloads.append(download))
    page.route(
        "**/ext/events/e/**",
        lambda route: route.fulfill(
            status=200,
            content_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="blocked.txt"'},
            body="file-bytes",
        ),
    )
    page.evaluate(
        """
        () => {
          const realCreateObjectURL = URL.createObjectURL.bind(URL);
          const realRevokeObjectURL = URL.revokeObjectURL.bind(URL);
          const realSetTimeout = window.setTimeout.bind(window);
          window.__saveProbe = { created: [], revoked: [], clicks: 0 };
          URL.createObjectURL = (blob) => {
            const url = realCreateObjectURL(blob);
            window.__saveProbe.created.push(url);
            return url;
          };
          URL.revokeObjectURL = (url) => {
            window.__saveProbe.revoked.push(url);
            realRevokeObjectURL(url);
          };
          window.setTimeout = (callback, delay, ...args) => {
            if (delay === 10000) {
              callback(...args);
              return 0;
            }
            return realSetTimeout(callback, delay, ...args);
          };
          HTMLAnchorElement.prototype.click = function () {
            window.__saveProbe.clicks += 1;
            throw new Error("blocked save");
          };
        }
        """
    )

    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    expected_error = {"status": 0, "code": "transport_error", "message": "blocked save"}
    assert outcome == ["err", expected_error]
    state = page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          return {
            loading: anchor.loading.any,
            handlerLoading: anchor.loading.handlers.save || 0,
            error: anchor.errorBox.current,
            temporaryLinks: document.querySelectorAll("a[download]").length,
            probe: window.__saveProbe,
          };
        }
        """
    )
    probe = state.pop("probe")
    assert state == {
        "loading": 0,
        "handlerLoading": 0,
        "error": expected_error,
        "temporaryLinks": 0,
    }
    assert probe["clicks"] == 1
    assert len(probe["created"]) == 1
    assert probe["revoked"] == probe["created"]
    log = page.evaluate("window.__log")
    assert log["after"] == [{"event": "save", "ok": False}]
    assert log["error"] == [{"event": "save", "error": expected_error}]
    assert downloads == []
    browser_errors = _citry_errors(messages)
    assert len(browser_errors) == 1
    assert "saving the download from 'save' failed" in browser_errors[0]
    assert "blocked save" in browser_errors[0]


def test_timed_out_attachment_never_starts_a_browser_download(page: Any, serve_live: Any) -> None:
    messages, _ = _goto_todo(page, serve_live)
    held: list[Any] = []
    downloads: list[Any] = []
    page.on("download", lambda download: downloads.append(download))
    page.route("**/ext/events/e/**", lambda route: held.append(route))

    outcome = page.evaluate(_SEND_AND_WAIT, ["save", {}, {"timeout": 150}])
    assert outcome[0] == "err"
    assert outcome[1]["code"] == "timeout"
    assert len(held) == 1

    held[0].fulfill(
        status=200,
        content_type="text/plain",
        headers={"Content-Disposition": 'attachment; filename="late.txt"'},
        body="too-late",
    )
    page.wait_for_function("window.__log.stale.length === 1")
    page.wait_for_timeout(100)
    assert downloads == []
    assert page.evaluate("window.__log.stale[0].reason") == "timeout"
    assert _citry_errors(messages) == []


def test_failed_and_batched_attachments_reject_without_a_browser_download(page: Any, serve_live: Any) -> None:
    messages, _ = _goto_todo(page, serve_live)
    downloads: list[Any] = []
    page.on("download", lambda download: downloads.append(download))

    page.route(
        "**/ext/events/e/**",
        lambda route: route.fulfill(
            status=500,
            content_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="error.txt"'},
            body="not-a-file",
        ),
    )
    failed = page.evaluate(_SEND_AND_WAIT, ["save", {}, None])
    assert failed == [
        "err",
        {"status": 500, "code": "transport_error", "message": "the download endpoint answered 500."},
    ]

    page.unroute("**/ext/events/e/**")
    page.route(
        "**/ext/events/call",
        lambda route: route.fulfill(
            status=200,
            content_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="batch.txt"'},
            body="ambiguous",
        ),
    )
    batched = page.evaluate(
        """async () => {
          const id = document.querySelector('.todo').getAttribute('data-cid');
          const promises = Citry.events._internal.sendCalls([
            { target: id, name: 'save', args: {} },
            { target: id, name: 'find', args: {} },
          ]);
          return Promise.all(promises.map((promise) => promise.then(
            () => ['ok'],
            (error) => ['err', error],
          )));
        }"""
    )
    expected = {
        "status": 0,
        "code": "transport_error",
        "message": "a download response can answer exactly one event call.",
    }
    assert batched == [["err", expected], ["err", expected]]
    page.wait_for_timeout(100)
    assert downloads == []
    browser_errors = _citry_errors(messages)
    # Chromium reports the intercepted HTTP 500 as a console error; Firefox
    # and WebKit are allowed to omit that browser-owned network diagnostic.
    assert len(browser_errors) <= 1
    if browser_errors:
        assert "responded with a status of 500" in browser_errors[0]


def test_download_action_round_trips_through_the_real_server(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Export(Component):
        citry = c

        class Events:
            @event(bundle=False)
            def report(self):
                return actions.Download("name\nAda", "přehled.csv", "text/csv; charset=utf-8")

        template = """
          <div class="export">export</div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>download</title></head>
            <body><c-export /></body>
          </html>
        """

    messages = _collect_console(page)
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    with page.expect_download() as download_info:
        result = page.evaluate(
            """async () => {
              const id = document.querySelector('.export').getAttribute('data-cid');
              const value = await Citry.events.send(id, 'report', {});
              return value === undefined ? '__undefined__' : value;
            }"""
        )
    download = download_info.value
    assert result == "__undefined__"
    assert unicodedata.normalize("NFC", download.suggested_filename) == "přehled.csv"
    assert Path(download.path()).read_text(encoding="utf-8") == "name\nAda"
    assert _citry_errors(messages) == []


# ----- the full round trip -----


def test_full_round_trip_against_a_live_server_increments_the_counter(page: Any, serve_live: Any) -> None:
    # The whole pipeline with zero interception: the spec's counter component
    # on a real page, one Citry.events.send("increment"), the real fetch POST
    # through the real WSGI routes (CSRF floor included), the dispatcher
    # running the handler, and the render action morphing the new count into
    # the DOM. The epoch echo lands on the anchor (send-side increment here,
    # apply-side comparison in the applier), the token rotates with the
    # re-render, and the anchor's identity survives while the component id
    # changes.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class CounterState:
        count: int = 0
        name: str = "Counter"
        _public = ("count", "name")

        def render(self):
            return Counter(count=self.count, name=self.name)

    class Counter(Component):
        citry = c
        State = CounterState

        class Events:
            def increment(self, state):
                state.count += 1
                return state.render()

        template = """
          <div class="counter">
            <h2 x-text="$state.name">Counter</h2>
            <button class="n" x-text="'Clicked ' + $state.count + ' times'">Clicked 0 times</button>
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>round trip</title></head>
            <body>
              <c-counter />
            </body>
          </html>
        """

    messages = _collect_console(page)
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.evaluate(_SETUP_LOGS)
    assert page.locator(".n").inner_text() == "Clicked 0 times"

    before = page.evaluate(
        """
        () => {
          const id = document.querySelector(".counter").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          return { id, anchorId: anchor.anchorId, token: anchor.token };
        }
        """
    )
    outcome = page.evaluate(
        """
        async () => {
          const id = document.querySelector(".counter").getAttribute("data-cid");
          const value = await Citry.events.send(id, "increment", {});
          return value === undefined ? "__undefined__" : value;
        }
        """
    )
    assert outcome == "__undefined__"  # a render-only result carries no data action
    page.wait_for_function("document.querySelector('.n').innerText === 'Clicked 1 times'")

    after = page.evaluate(
        """
        () => {
          const id = document.querySelector(".counter").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          return {
            id,
            anchorId: anchor.anchorId,
            token: anchor.token,
            sendSequence: anchor.epoch,
            highestApplied: anchor.highestApplied,
            count: anchor.values.count,
          };
        }
        """
    )
    # The faithful component id changed with the render; the anchor (and its
    # epoch bookkeeping) is the same client-side identity.
    assert after["anchorId"] == before["anchorId"]
    assert after["id"] != before["id"]
    assert after["token"].startswith("cev1.")
    assert after["token"] != before["token"]
    assert after["sendSequence"] == 1
    assert after["highestApplied"] == 1
    assert after["count"] == 1

    log = page.evaluate("window.__log")
    assert log["before"] == [{"instance": before["id"], "cls": Counter.class_id, "event": "increment"}]
    assert log["after"] == [{"event": "increment", "ok": True}]
    assert log["error"] == []
    assert log["stale"] == []
    assert _citry_errors(messages) == []
