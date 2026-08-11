"""
Browser e2e for the event queue, the dependency-DAG half of the client
runtime shipped as ``citry/ext/events/client/citry-events.js`` (design
contract: docs/design/events.md 5.6, with 3.5's ``@event`` knobs, 4.2's
``calls[]`` batching, and 5.2's ``cancelled``/``superseded`` drop rows).

What this suite locks, mapped to the design:

- Containment edges: a child send waits behind a slow in-flight parent send
  and fires only after the parent's render applied, carrying the fresh state
  token and the fresh instance id that render delivered (settled means
  applied); two sibling widgets share no edge and never wait on each other;
  an event enqueued under two overlapping unsettled scopes (an ancestor and
  a descendant of its own anchor) holds one edge to each and dispatches only
  after both settle.
- Every settle path releases dependents: a network-failed send and a
  timed-out send both free the events queued behind them.
- Dequeue re-verification: a queued send whose dispatching instance left the
  DOM cancels early (never sent, promise rejected with code ``cancelled``,
  the drop event with reason ``cancelled``, a debug line).
- Eligible-together batching: sends released together ride one ``calls[]``
  envelope to the batch endpoint, each with its own promise and result slot;
  ``@event(bundle=False)`` sends alone; ``@event(latest_wins=True)`` drops a
  queued predecessor (never sent) and abandons an in-flight one (rejected at
  supersession time; its late response's application drops on arrival), both
  rejecting with code ``superseded``.
- ``wait: false`` joins no graph: it fires immediately despite an in-flight
  overlap, holds nothing, and its late render is epoch-dropped (the applier's
  comparison; promise still resolves).
- Busy from the gesture: ``data-citry-busy`` and ``$loading`` start at
  enqueue and span queue, flight, and apply, clearing on settle.
- The tick-skip rule: a recurring send (the bindings runtime's private key,
  entry) whose previous call is still outstanding is skipped with a debug
  breadcrumb and no promise.

Uses the live-server harness (conftest ``serve_live``) like the sibling
suites. Timing is made deterministic by holding real requests at intercepted
routes (the route object is stashed and ``continue_()``d later, so released
calls still hit the real WSGI routes and produce real tokens and renders).
Locked strings and shapes were observed from the real runtime first, then
locked.
"""

from __future__ import annotations

import json
import time
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events import event

pytestmark = pytest.mark.e2e

SIGNING_KEY = "e2e-secret"

READY = "window.Citry && Citry.events && Citry.events._internal && Citry.events._internal.alpineStarted === true"

# Registered on every page before anything sends: collects the lifecycle
# events this suite asserts (design 5.2's detail contract).
_SETUP_LOGS = """
() => {
  window.__log = { before: [], after: [], error: [], stale: [] };
  document.addEventListener("citry:events:before", (e) => {
    window.__log.before.push({ instance: e.detail.instance, event: e.detail.event });
  });
  document.addEventListener("citry:events:after", (e) => {
    window.__log.after.push({ event: e.detail.event, ok: e.detail.ok });
  });
  document.addEventListener("citry:events:error", (e) => {
    window.__log.error.push({ event: e.detail.event, code: e.detail.error && e.detail.error.code });
  });
  document.addEventListener("citry:events:stale", (e) => {
    window.__log.stale.push({ instance: e.detail.instance, event: e.detail.event, reason: e.detail.reason });
  });
}
"""

# Store a send's outcome under window.__o[key] so the test can poll it
# without blocking the Python thread (held routes are released from Python,
# so awaiting inside evaluate would deadlock).
_TRACK = """
([target, name, args, opts, key]) => {
  window.__o = window.__o || {};
  Citry.events.send(target, name, args || {}, opts || undefined).then(
    (v) => { window.__o[key] = ["ok", v === undefined ? "__undefined__" : v]; },
    (e) => {
      window.__o[key] = ["err", e && e.code ? { status: e.status, code: e.code, message: e.message } : String(e)];
    },
  );
}
"""


def _collect_console(page: Any) -> list[str]:
    """Start collecting console messages as ``type:text`` strings."""
    messages: list[str] = []
    page.on("console", lambda msg: messages.append(f"{msg.type}:{msg.text}"))
    return messages


def _citry_errors(messages: list[str]) -> list[str]:
    return [m for m in messages if m.startswith("error:")]


def _collect_event_requests(page: Any) -> list[dict]:
    """Capture every events-route request as ``{url, body}`` in wire order."""
    captured: list[dict] = []

    def record(request: Any) -> None:
        if "/ext/events/" not in request.url or "/runtime.js" in request.url:
            return
        body = None
        try:
            body = json.loads(request.post_data or "null")
        except ValueError:
            body = None
        captured.append({"url": request.url, "body": body})

    page.on("request", record)
    return captured


def _hold_route(page: Any, url_pattern: str) -> list[Any]:
    """
    Stash every request to ``url_pattern`` unanswered; the test releases one
    later with ``held[i].continue_()`` (on to the real server) so its timing
    is fully test-controlled while the response stays real.
    """
    held: list[Any] = []
    page.route(url_pattern, lambda route: held.append(route))
    return held


def _wait_held(page: Any, held: list[Any], count: int, timeout_ms: int = 5000) -> None:
    """
    Wait until ``count`` requests sit at a held route. The in-page dispatch is
    synchronous but the request reaches the route handler asynchronously, so
    a held-count read needs this pump (``wait_for_timeout`` keeps the driver
    loop running the route callbacks).
    """
    deadline = time.monotonic() + timeout_ms / 1000
    while len(held) < count:
        if time.monotonic() > deadline:
            msg = f"expected {count} held request(s), saw {len(held)}"
            raise AssertionError(msg)
        page.wait_for_timeout(25)


def _goto(page: Any, serve_live: Any, citry: Citry, html: str) -> list[str]:
    """Serve the page, open it, wait for the runtime, register the log listeners."""
    messages = _collect_console(page)
    base = serve_live(citry, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.evaluate(_SETUP_LOGS)
    return messages


def _event_url(component: type[Component], name: str) -> str:
    """The per-event route pattern for one handler (design 3.8)."""
    return f"**/ext/events/e/{component.class_id}/{name}"


_SNAPSHOT = "Citry.events._internal.queue.snapshot()"


# ----- containment edges: parent-child, siblings, overlapping scopes -----


def _make_parent_child_app() -> tuple[Citry, str, type[Component], type[Component]]:
    """A parent whose self-render carries a keyed child (the anchor survives the parent's render)."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ChildState:
        note: str = "n0"
        _public = ("note",)

    class Child(Component):
        citry = c
        State = ChildState

        class Events:
            def ping(self, state):
                return None

        template = """
          <div class="child">
            <span class="c-busy" x-text="$loading() ? 'busy' : 'idle'"></span>
            <button class="go">go</button>
          </div>
        """

    class ParentState:
        tick: int = 0
        _public = ("tick",)

        def render(self):
            return Parent(tick=self.tick)

    class Parent(Component):
        citry = c
        State = ParentState

        class Events:
            def slow(self, state):
                state.tick += 1
                return state.render()

            def idle(self, state):
                return None

        # The child's `note` kwarg derives from the parent's tick, so the
        # parent's render provably rotates the child's state token (the
        # child-waits test reads that rotation).
        template = """
          <div class="parent">
            <span class="tick" x-text="$state.tick">{{ tick }}</span>
            <c-child
              #c-key="'k1'"
              c-note="child_note"
            />
          </div>
        """

        def template_data(self, kwargs, slots):
            tick = kwargs.get("tick", 0)
            return {"tick": tick, "child_note": f"n{tick}"}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>queue e2e</title></head>
            <body>
              <c-parent />
            </body>
          </html>
        """

    return c, str(Page()), Parent, Child


def test_child_send_waits_behind_slow_parent_and_observes_the_applied_render(page: Any, serve_live: Any) -> None:
    # The DAG's core rule (design 5.6): a child send enqueued while its
    # parent's send is in flight gains one containment edge and holds until
    # the parent's render has APPLIED, then fires carrying the world that
    # render produced: the fresh state token and the fresh instance id (the
    # keyed link carried the anchor across, design 5.5).
    c, html, parent, child = _make_parent_child_app()
    messages = _goto(page, serve_live, c, html)
    requests = _collect_event_requests(page)
    held_slow = _hold_route(page, _event_url(parent, "slow"))
    held_ping = _hold_route(page, _event_url(child, "ping"))

    before = page.evaluate(
        """
        () => {
          const childId = document.querySelector(".child").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(childId);
          return { childId, anchorId: anchor.anchorId, token: anchor.token };
        }
        """
    )

    parent_id = page.evaluate("document.querySelector('.parent').getAttribute('data-cid')")
    page.evaluate(_TRACK, [parent_id, "slow", None, None, "slow"])
    page.evaluate(_TRACK, [before["childId"], "ping", None, None, "ping"])

    # The parent went to the wire; the child holds exactly one edge to it.
    page.wait_for_function("window.__log.before.length === 1")
    snapshot = page.evaluate(_SNAPSHOT)
    assert [entry["event"] for entry in snapshot] == ["slow", "ping"]
    assert snapshot[0]["dispatched"] is True
    assert snapshot[0]["waitsOn"] == []
    assert snapshot[1]["dispatched"] is False
    assert snapshot[1]["waitsOn"] == [snapshot[0]["seq"]]
    _wait_held(page, held_slow, 1)
    assert len(held_ping) == 0
    assert [r["url"].rsplit("/", 1)[-1] for r in requests] == ["slow"]

    # Release the parent: its render applies (fresh DOM), the edge settles,
    # and only then does the child's call go on the wire.
    held_slow[0].continue_()
    page.wait_for_function("document.querySelector('.tick').innerText === '1'")
    page.wait_for_function("window.__o.slow !== undefined")
    page.wait_for_function(f"{_SNAPSHOT}.some((n) => n.event === 'ping' && n.dispatched)")
    _wait_held(page, held_ping, 1)

    # The child's call carries the applied world: the parent-derived fresh
    # token and the fresh (re-minted) instance id, on the surviving anchor.
    after = page.evaluate(
        """
        () => {
          const childId = document.querySelector(".child").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(childId);
          return { childId, anchorId: anchor.anchorId, token: anchor.token };
        }
        """
    )
    ping_call = requests[-1]["body"]["calls"][0]
    assert [r["url"].rsplit("/", 1)[-1] for r in requests] == ["slow", "ping"]
    assert after["anchorId"] == before["anchorId"]  # the keyed link carried the anchor
    assert after["childId"] != before["childId"]  # the render re-minted the id
    assert ping_call["callerRenderId"] == after["childId"]
    assert ping_call["stateToken"] == after["token"]
    assert ping_call["stateToken"] != before["token"]

    held_ping[0].continue_()
    page.wait_for_function("window.__o.ping !== undefined")
    assert page.evaluate("window.__o.ping") == ["ok", "__undefined__"]
    assert page.evaluate("window.__o.slow") == ["ok", "__undefined__"]
    assert page.evaluate("window.__log.stale") == []
    assert _citry_errors(messages) == []


def _make_siblings_app() -> tuple[Citry, str, type[Component]]:
    """Two sibling widget instances under a non-interactive page (no shared anchor above them)."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class WidgetState:
        label: str = ""
        _public = ("label",)

    class Widget(Component):
        citry = c
        State = WidgetState

        class Events:
            def save(self, state):
                return {"who": state.label}

            def toggle(self, state):
                return {"who": state.label}

        template = """
          <div class="widget">
            <span x-text="$state.label"></span>
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>siblings</title></head>
            <body>
              <c-widget label="a" />
              <c-widget label="b" />
            </body>
          </html>
        """

    return c, str(Page()), Widget


def test_sibling_widgets_never_wait_on_each_other(page: Any, serve_live: Any) -> None:
    # Independent branches run in parallel (design 5.6): a slow save on one
    # widget shares no edge with its sibling, whose toggle fires immediately
    # and resolves while the save is still in flight.
    c, html, widget = _make_siblings_app()
    messages = _goto(page, serve_live, c, html)
    requests = _collect_event_requests(page)
    held_save = _hold_route(page, _event_url(widget, "save"))

    ids = page.evaluate("Array.from(document.querySelectorAll('.widget')).map((el) => el.getAttribute('data-cid'))")
    page.evaluate(_TRACK, [ids[0], "save", None, None, "save"])
    page.evaluate(_TRACK, [ids[1], "toggle", None, None, "toggle"])

    # The toggle resolved while the save's request is still held open.
    page.wait_for_function("window.__o.toggle !== undefined")
    assert page.evaluate("window.__o.toggle") == ["ok", {"who": "b"}]
    assert page.evaluate("window.__o.save") is None
    _wait_held(page, held_save, 1)
    snapshot = page.evaluate(_SNAPSHOT)
    assert [(entry["event"], entry["dispatched"], entry["waitsOn"]) for entry in snapshot] == [("save", True, [])]
    assert [r["url"].rsplit("/", 1)[-1] for r in requests] == ["save", "toggle"]

    held_save[0].continue_()
    page.wait_for_function("window.__o.save !== undefined")
    assert page.evaluate("window.__o.save") == ["ok", {"who": "a"}]
    assert page.evaluate("window.__log.stale") == []
    assert _citry_errors(messages) == []


def _make_nested_app() -> tuple[Citry, str, type[Component], type[Component], type[Component]]:
    """Three nested interactive components (outer > mid > inner), all with data-only handlers."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class InnerState:
        note: str = "i"
        _public = ("note",)

    class Inner(Component):
        citry = c
        State = InnerState

        class Events:
            def poke(self, state):
                return None

        template = """
          <div class="inner">inner</div>
        """

    class MidState:
        note: str = "m"
        _public = ("note",)

    class Mid(Component):
        citry = c
        State = MidState

        class Events:
            def poke(self, state):
                return None

        template = """
          <div class="mid">
            <c-inner />
          </div>
        """

    class OuterState:
        note: str = "o"
        _public = ("note",)

    class Outer(Component):
        citry = c
        State = OuterState

        class Events:
            def poke(self, state):
                return None

        template = """
          <div class="outer">
            <c-mid />
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>nested</title></head>
            <body>
              <c-outer />
            </body>
          </html>
        """

    return c, str(Page()), Outer, Mid, Inner


def test_event_under_two_overlapping_scopes_holds_one_edge_to_each(page: Any, serve_live: Any) -> None:
    # An event dispatched from an anchor sitting inside two overlapping
    # unsettled scopes holds one edge to each (design 5.6): here the mid
    # component's send waits on its ancestor (outer, in flight) AND its
    # descendant (inner, queued behind outer), and dispatches only after
    # both settle.
    c, html, outer, mid, inner = _make_nested_app()
    messages = _goto(page, serve_live, c, html)
    requests = _collect_event_requests(page)
    held_outer = _hold_route(page, _event_url(outer, "poke"))
    held_inner = _hold_route(page, _event_url(inner, "poke"))

    ids = page.evaluate(
        """
        () => ({
          outer: document.querySelector(".outer").getAttribute("data-cid").split(/\\s+/)[0],
          mid: document.querySelector(".mid").getAttribute("data-cid").split(/\\s+/)[0],
          inner: document.querySelector(".inner").getAttribute("data-cid").split(/\\s+/)[0],
        })
        """
    )
    page.evaluate(_TRACK, [ids["outer"], "poke", None, None, "outer"])
    page.evaluate(_TRACK, [ids["inner"], "poke", None, None, "inner"])
    page.evaluate(_TRACK, [ids["mid"], "poke", None, None, "mid"])

    # Outer is in flight; inner waits on outer (its ancestor); mid holds one
    # edge to EACH of the two unsettled overlapping scopes.
    snapshot = page.evaluate(_SNAPSHOT)
    assert len(snapshot) == 3
    outer_node = snapshot[0]
    inner_node = snapshot[1]
    mid_node = snapshot[2]
    assert outer_node["dispatched"] is True
    assert outer_node["waitsOn"] == []
    assert inner_node["dispatched"] is False
    assert inner_node["waitsOn"] == [outer_node["seq"]]
    assert mid_node["dispatched"] is False
    assert mid_node["waitsOn"] == [outer_node["seq"], inner_node["seq"]]

    # Outer settles: inner dispatches; mid still holds its edge to inner.
    held_outer[0].continue_()
    page.wait_for_function("window.__o.outer !== undefined")
    page.wait_for_function(f"{_SNAPSHOT}.some((n) => n.dispatched)")
    snapshot = page.evaluate(_SNAPSHOT)
    assert [(entry["dispatched"], entry["waitsOn"]) for entry in snapshot] == [
        (True, []),
        (False, [inner_node["seq"]]),
    ]
    assert page.evaluate("window.__o.mid") is None
    _wait_held(page, held_inner, 1)

    # Inner settles too: mid finally dispatches and resolves.
    held_inner[0].continue_()
    page.wait_for_function("window.__o.mid !== undefined")
    assert page.evaluate("window.__o.mid") == ["ok", "__undefined__"]
    assert [r["url"].rsplit("/", 2)[-2] for r in requests] == [
        outer.class_id,
        inner.class_id,
        mid.class_id,
    ]
    assert page.evaluate("window.__log.stale") == []
    assert _citry_errors(messages) == []


# ----- every settle path releases dependents -----


def test_failed_and_timed_out_sends_release_their_dependents(page: Any, serve_live: Any) -> None:
    # Failure settles too (design 5.6): a network-failed parent send and a
    # timed-out parent send each reject their caller AND release the child
    # queued behind them; a hung request must never freeze a subtree.
    c, html, parent, _child = _make_parent_child_app()
    messages = _goto(page, serve_live, c, html)

    # Phase one: a deterministic transport failure. The fake holds its first
    # call until the exact parent/child edge is visible, then rejects it; its
    # later calls resolve normally so the released child proves progress.
    page.evaluate(
        """() => {
          window.__fakeCalls = 0;
          window.__rejectParent = null;
          Citry.events.registerTransport("failure-gate", {
            send: (envelope) => {
              window.__fakeCalls += 1;
              if (window.__fakeCalls === 1) {
                return new Promise((_resolve, reject) => { window.__rejectParent = reject; });
              }
              return Promise.resolve({
                protocol: envelope.protocol,
                requestId: envelope.requestId,
                results: envelope.calls.map((call) => ({ ok: true, sendSequence: call.sendSequence, actions: [] })),
              });
            },
          });
          Citry.events.configure({ transport: "failure-gate" });
        }"""
    )
    ids = page.evaluate(
        """
        () => ({
          parent: document.querySelector(".parent").getAttribute("data-cid"),
          child: document.querySelector(".child").getAttribute("data-cid"),
        })
        """
    )
    page.evaluate(_TRACK, [ids["parent"], "idle", None, None, "failed"])
    page.evaluate(_TRACK, [ids["child"], "ping", None, None, "after_fail"])
    snapshot = page.evaluate(_SNAPSHOT)
    assert [(node["event"], node["dispatched"], node["waitsOn"]) for node in snapshot] == [
        ("idle", True, []),
        ("ping", False, [snapshot[0]["seq"]]),
    ]
    page.evaluate("window.__rejectParent({ status: 0, code: 'transport_error', message: 'offline' })")
    page.wait_for_function("window.__o.failed !== undefined && window.__o.after_fail !== undefined")
    assert page.evaluate("window.__o.failed[0]") == "err"
    assert page.evaluate("window.__o.failed[1].code") == "transport_error"
    assert page.evaluate("window.__o.after_fail") == ["ok", "__undefined__"]
    page.evaluate("Citry.events.configure({ transport: 'fetch' })")

    # Phase two: the bounded timeout. The parent's request is held past its
    # 250 ms budget; the rejection releases the child, which then resolves
    # while the parent's request is still hanging.
    held_idle = _hold_route(page, _event_url(parent, "idle"))
    page.evaluate(_TRACK, [ids["parent"], "idle", None, {"timeout": 250}, "timed_out"])
    page.evaluate(_TRACK, [ids["child"], "ping", None, None, "after_timeout"])
    timeout_snapshot = page.evaluate(_SNAPSHOT)
    assert [(node["event"], node["dispatched"], node["waitsOn"]) for node in timeout_snapshot] == [
        ("idle", True, []),
        ("ping", False, [timeout_snapshot[0]["seq"]]),
    ]
    page.wait_for_function("window.__o.timed_out !== undefined && window.__o.after_timeout !== undefined")
    assert page.evaluate("window.__o.timed_out[0]") == "err"
    assert page.evaluate("window.__o.timed_out[1].code") == "timeout"
    assert page.evaluate("window.__o.after_timeout") == ["ok", "__undefined__"]
    assert len(held_idle) == 1  # the parent's request is still held: only the client stopped waiting

    # Deliver the parent's response late: it drops (reason timeout, landed
    # transport behavior), releasing nothing twice.
    held_idle[0].continue_()
    page.wait_for_function("window.__log.stale.length === 1")
    assert page.evaluate("window.__log.stale[0].reason") == "timeout"
    assert _citry_errors(messages) == []


# ----- dequeue-time early cancel -----


def _make_removing_parent_app() -> tuple[Citry, str, type[Component], type[Component]]:
    """A parent whose slow render removes its (unkeyed) child from the tree."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ChildState:
        note: str = "srv"
        _public = ("note",)

    class Child(Component):
        citry = c
        State = ChildState

        js = """
          $component({
            props: { value: { type: Number, required: true } },
            init: ({ props, effect, els }) => {
              effect(() => { els[0].dataset.boundaryValue = String(props.value); });
            },
          });
        """

        class Events:
            def ping(self, state):
                return None

        template = """
          <div class="child">child</div>
        """

    class ParentState:
        keep: int = 1
        _public = ("keep",)

        def render(self):
            return Parent(keep=self.keep)

    class Parent(Component):
        citry = c
        State = ParentState

        class Events:
            def drop_child(self, state):
                state.keep = 0
                return state.render()

        template = """
          <div class="parent">
            <span class="keep" x-text="$state.keep">{{ keep }}</span>
            <c-for each="i in items">
              <c-child $c-props="{ value: $state.keep }" />
            </c-for>
          </div>
        """

        def template_data(self, kwargs, slots):
            return {"keep": kwargs.get("keep", 1), "items": list(range(kwargs.get("keep", 1)))}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>cancel</title></head>
            <body>
              <c-parent />
            </body>
          </html>
        """

    return c, str(Page()), Parent, Child


def test_dead_dispatcher_cancels_early_at_dequeue(page: Any, serve_live: Any) -> None:
    # Dequeue re-verifies against the live DOM (design 5.6): the parent's
    # render removed the child region while the child's send waited, so the
    # send is never sent; its promise rejects with the named `cancelled`
    # reason, the drop event fires, and a debug line records it. A queued
    # click on a replaced region must not fire a ghost call.
    c, html, parent, _child = _make_removing_parent_app()
    messages = _goto(page, serve_live, c, html)
    page.wait_for_function("document.querySelector('.child')?.dataset.boundaryValue === '1'")
    requests = _collect_event_requests(page)
    held_drop = _hold_route(page, _event_url(parent, "drop_child"))

    ids = page.evaluate(
        """
        () => ({
          parent: document.querySelector(".parent").getAttribute("data-cid"),
          child: document.querySelector(".child").getAttribute("data-cid"),
        })
        """
    )
    page.evaluate(_TRACK, [ids["parent"], "drop_child", None, None, "drop"])
    page.evaluate(_TRACK, [ids["child"], "ping", None, None, "ping"])
    assert page.evaluate(f"{_SNAPSHOT}.length") == 2

    held_drop[0].continue_()
    page.wait_for_function("window.__o.drop !== undefined && window.__o.ping !== undefined")
    assert page.evaluate("document.querySelector('.child')") is None
    assert page.evaluate("window.__o.drop") == ["ok", "__undefined__"]
    assert page.evaluate("window.__o.ping") == [
        "err",
        {
            "status": 0,
            "code": "cancelled",
            "message": "'ping' was cancelled: its dispatching element or component instance left the DOM"
            " while the call was queued (design 5.6).",
        },
    ]
    # Never sent: the only wire traffic is the parent's own call.
    assert [r["url"].rsplit("/", 1)[-1] for r in requests] == ["drop_child"]
    stale = page.evaluate("window.__log.stale")
    assert [(entry["event"], entry["reason"]) for entry in stale] == [("ping", "cancelled")]
    drops = [m for m in messages if m.startswith("debug:") and "cancelled queued" in m]
    assert drops == [
        "debug:[Citry] events: cancelled queued 'ping': its dispatching element or instance is gone; never sent."
    ]
    # A routine queue outcome: no $error, no error event (design 5.2).
    assert page.evaluate("window.__log.error") == []
    assert _citry_errors(messages) == []


def test_dead_dispatching_elements_cover_removed_and_ownerless_dequeue_branches(page: Any, serve_live: Any) -> None:
    c, html, parent, _child = _make_parent_child_app()
    messages = _goto(page, serve_live, c, html)
    requests = _collect_event_requests(page)
    held_idle = _hold_route(page, _event_url(parent, "idle"))

    parent_id = page.evaluate("document.querySelector('.parent').getAttribute('data-cid')")
    page.evaluate(_TRACK, [parent_id, "idle", None, None, "idle"])
    page.evaluate(
        """() => {
          const host = document.querySelector('.child');
          window.__removedTrigger = host.querySelector('.go').cloneNode(true);
          window.__ownerlessTrigger = host.querySelector('.go').cloneNode(true);
          host.append(window.__removedTrigger, window.__ownerlessTrigger);
          window.__removedOutcome = null;
          window.__ownerlessOutcome = null;
          Citry.events.send(window.__removedTrigger, 'ping', {}).then(
            () => { window.__removedOutcome = 'ok'; },
            (e) => { window.__removedOutcome = e.code; },
          );
          Citry.events.send(window.__ownerlessTrigger, 'ping', {}).then(
            () => { window.__ownerlessOutcome = 'ok'; },
            (e) => { window.__ownerlessOutcome = e.code; },
          );
          window.__removedTrigger.remove();
          document.body.append(window.__ownerlessTrigger);
        }"""
    )
    snapshot = page.evaluate(_SNAPSHOT)
    assert [(node["event"], node["dispatched"]) for node in snapshot] == [
        ("idle", True),
        ("ping", False),
        ("ping", False),
    ]

    held_idle[0].continue_()
    page.wait_for_function("window.__removedOutcome && window.__ownerlessOutcome")
    assert page.evaluate("[window.__removedOutcome, window.__ownerlessOutcome]") == ["cancelled", "cancelled"]
    assert page.evaluate(
        """() => ({
          removedBusy: window.__removedTrigger.hasAttribute('data-citry-busy'),
          ownerlessBusy: window.__ownerlessTrigger.hasAttribute('data-citry-busy'),
          rootBusy: document.querySelector('.child')?.hasAttribute('data-citry-busy') || false,
        })"""
    ) == {"removedBusy": False, "ownerlessBusy": False, "rootBusy": False}
    assert [request["url"].rsplit("/", 1)[-1] for request in requests] == ["idle"]
    assert [(entry["event"], entry["reason"]) for entry in page.evaluate("window.__log.stale")] == [
        ("ping", "cancelled"),
        ("ping", "cancelled"),
    ]
    assert _citry_errors(messages) == []


# ----- eligible-together batching and the @event knobs -----


def _make_bundle_app() -> tuple[Citry, str, type[Component], type[Component], type[Component]]:
    """A slow data-only parent over three widgets: two bundleable, one @event(bundle=False)."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class WidgetState:
        label: str = ""
        _public = ("label",)

    class Widget(Component):
        citry = c
        State = WidgetState

        class Events:
            def ping(self, state):
                return {"who": state.label}

        template = """
          <div class="widget" x-text="$state.label"></div>
        """

    class AloneState:
        label: str = ""
        _public = ("label",)

    class Alone(Component):
        citry = c
        State = AloneState

        class Events:
            @event(bundle=False)
            def ping(self, state):
                return {"who": state.label}

        template = """
          <div class="alone" x-text="$state.label"></div>
        """

    class HubState:
        note: str = "hub"
        _public = ("note",)

    class Hub(Component):
        citry = c
        State = HubState

        class Events:
            def slow(self, state):
                return None

        template = """
          <div class="hub">
            <c-widget label="a" />
            <c-alone label="b" />
            <c-widget label="c" />
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>bundle</title></head>
            <body>
              <c-hub />
            </body>
          </html>
        """

    return c, str(Page()), Hub, Widget, Alone


def test_co_eligible_sends_bundle_and_bundle_false_sends_alone(page: Any, serve_live: Any) -> None:
    # Eligible-together batching (design 5.6): three sends queued behind one
    # slow ancestor become dispatchable together when it settles. The two
    # bundleable ones ride ONE envelope to the batch endpoint, each keeping
    # its own promise and result slot; the @event(bundle=False) one sends
    # alone on its per-event route.
    c, html, hub, _widget, alone = _make_bundle_app()
    messages = _goto(page, serve_live, c, html)
    requests = _collect_event_requests(page)
    held_slow = _hold_route(page, _event_url(hub, "slow"))

    ids = page.evaluate(
        """
        () => ({
          hub: document.querySelector(".hub").getAttribute("data-cid"),
          a: document.querySelectorAll(".widget")[0].getAttribute("data-cid"),
          b: document.querySelector(".alone").getAttribute("data-cid"),
          c: document.querySelectorAll(".widget")[1].getAttribute("data-cid"),
        })
        """
    )
    page.evaluate(_TRACK, [ids["hub"], "slow", None, None, "slow"])
    page.evaluate(_TRACK, [ids["a"], "ping", None, None, "a"])
    page.evaluate(_TRACK, [ids["b"], "ping", None, None, "b"])
    page.evaluate(_TRACK, [ids["c"], "ping", None, None, "c"])
    snapshot = page.evaluate(_SNAPSHOT)
    hub_seq = snapshot[0]["seq"]
    assert [(entry["dispatched"], entry["waitsOn"]) for entry in snapshot] == [
        (True, []),
        (False, [hub_seq]),
        (False, [hub_seq]),
        (False, [hub_seq]),
    ]
    assert [r["url"].rsplit("/", 1)[-1] for r in requests] == ["slow"]

    held_slow[0].continue_()
    page.wait_for_function("window.__o.a !== undefined && window.__o.b !== undefined && window.__o.c !== undefined")

    # One shared envelope for the two bundleable calls (their own promises,
    # their own result slots), one solo envelope for the bundle=False call.
    wire = [
        (r["url"].rsplit("/", 1)[-1], [call["handlerName"] for call in (r["body"] or {}).get("calls", [])])
        for r in requests[1:]
    ]
    assert wire == [("call", ["ping", "ping"]), ("ping", ["ping"])]
    batch_body = requests[1]["body"]
    assert [call["callerRenderId"] for call in batch_body["calls"]] == [ids["a"], ids["c"]]
    solo_body = requests[2]["body"]
    assert requests[2]["url"].endswith(f"/e/{alone.class_id}/ping")
    assert [call["callerRenderId"] for call in solo_body["calls"]] == [ids["b"]]
    assert page.evaluate("window.__o.a") == ["ok", {"who": "a"}]
    assert page.evaluate("window.__o.b") == ["ok", {"who": "b"}]
    assert page.evaluate("window.__o.c") == ["ok", {"who": "c"}]
    assert page.evaluate("window.__log.stale") == []
    assert _citry_errors(messages) == []


class SaveIn:
    """The latest_wins save handler's args schema (module level so the annotation resolves)."""

    n: int = 0


def _make_latest_wins_app() -> tuple[Citry, str, type[Component], type[Component]]:
    """A slow data-only parent over one widget whose save handler opted into latest_wins."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class DraftState:
        text: str = ""
        _public = ("text",)

    class Draft(Component):
        citry = c
        State = DraftState

        class Events:
            @event(latest_wins=True, bundle=False)
            def save(self, data: SaveIn, state):
                return {"saved": data.n}

        template = """
          <div class="draft">draft</div>
        """

    class HubState:
        note: str = "hub"
        _public = ("note",)

    class Hub(Component):
        citry = c
        State = HubState

        class Events:
            def slow(self, state):
                return None

        template = """
          <div class="hub">
            <c-draft />
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>latest wins</title></head>
            <body>
              <c-hub />
            </body>
          </html>
        """

    return c, str(Page()), Hub, Draft


def test_latest_wins_drops_the_queued_predecessor(page: Any, serve_live: Any) -> None:
    # @event(latest_wins=True), the queued half (design 3.5): a newer call
    # enqueued from the same anchor drops a queued-not-sent predecessor
    # before sending; the predecessor's promise rejects with code
    # `superseded`, the drop event fires, and it is never sent.
    c, html, hub, _draft = _make_latest_wins_app()
    messages = _goto(page, serve_live, c, html)
    requests = _collect_event_requests(page)
    held_slow = _hold_route(page, _event_url(hub, "slow"))

    ids = page.evaluate(
        """
        () => ({
          hub: document.querySelector(".hub").getAttribute("data-cid"),
          draft: document.querySelector(".draft").getAttribute("data-cid"),
        })
        """
    )
    page.evaluate(_TRACK, [ids["hub"], "slow", None, None, "slow"])
    page.evaluate(_TRACK, [ids["draft"], "save", {"n": 1}, None, "first"])
    page.evaluate(_TRACK, [ids["draft"], "save", {"n": 2}, None, "second"])

    # The first save was dropped at the second's enqueue: rejected, drop
    # event fired, and it no longer sits in the queue.
    page.wait_for_function("window.__o.first !== undefined")
    assert page.evaluate("window.__o.first") == [
        "err",
        {
            "status": 0,
            "code": "superseded",
            "message": "'save' was superseded by a newer call to the same handler"
            " (@event(latest_wins=True), design 3.5).",
        },
    ]
    snapshot = page.evaluate(_SNAPSHOT)
    assert [entry["event"] for entry in snapshot] == ["slow", "save"]
    stale = page.evaluate("window.__log.stale")
    assert [(entry["event"], entry["reason"]) for entry in stale] == [("save", "superseded")]
    drops = [m for m in messages if m.startswith("debug:") and "superseded" in m]
    assert drops == [
        "debug:[Citry] events: dropped queued 'save': a newer call superseded it (latest_wins); never sent."
    ]

    # The surviving save fires after the hub settles; the server saw exactly
    # one save call, the newer one.
    held_slow[0].continue_()
    page.wait_for_function("window.__o.second !== undefined")
    assert page.evaluate("window.__o.second") == ["ok", {"saved": 2}]
    save_calls = [r for r in requests if r["url"].endswith("/save")]
    assert len(save_calls) == 1
    assert save_calls[0]["body"]["calls"][0]["args"] == {"n": 2}
    # A routine queue outcome: no $error, no error event (design 5.2).
    assert page.evaluate("window.__log.error") == []
    assert _citry_errors(messages) == []


def test_latest_wins_abandons_the_in_flight_predecessor(page: Any, serve_live: Any) -> None:
    # @event(latest_wins=True), the in-flight half (design 3.5): the newer
    # call abandons an in-flight predecessor, rejecting it with `superseded`
    # NOW and sending without waiting for the abandoned response; when that
    # response finally arrives, its application drops whole (the drop event
    # with reason `superseded` and a debug line).
    c, html, _hub, draft = _make_latest_wins_app()
    messages = _goto(page, serve_live, c, html)
    downloads: list[Any] = []
    page.on("download", lambda download: downloads.append(download))

    # Hold only the FIRST save request; later saves pass through to the
    # live server.
    held_first: list[Any] = []

    def gate(route: Any) -> None:
        if held_first:
            route.continue_()
        else:
            held_first.append(route)

    page.route(_event_url(draft, "save"), gate)

    draft_id = page.evaluate("document.querySelector('.draft').getAttribute('data-cid')")
    page.evaluate(_TRACK, [draft_id, "save", {"n": 1}, None, "first"])
    # The first request must be the one the gate stashes, so it must reach
    # the route before the second send fires.
    _wait_held(page, held_first, 1)
    page.evaluate(_TRACK, [draft_id, "save", {"n": 2}, None, "second"])

    # The first rejected at supersession time, while its request is still
    # held open; the second fired immediately (no edge to the abandoned
    # call).
    page.wait_for_function("window.__o.first !== undefined && window.__o.second !== undefined")
    assert page.evaluate("window.__o.first[0]") == "err"
    assert page.evaluate("window.__o.first[1].code") == "superseded"
    assert page.evaluate("window.__o.second") == ["ok", {"saved": 2}]
    assert len(held_first) == 1
    abandoned = [m for m in messages if m.startswith("debug:") and "abandoned the in-flight" in m]
    assert abandoned == [
        "debug:[Citry] events: abandoned the in-flight 'save': a newer call superseded it (latest_wins)."
    ]

    # Deliver an attachment as the abandoned response: it is buffered by the
    # fetch transport, then dropped at settlement before a browser save can
    # start.
    held_first[0].fulfill(
        status=200,
        content_type="text/plain",
        headers={"Content-Disposition": 'attachment; filename="stale.txt"'},
        body="stale",
    )
    page.wait_for_function("window.__log.stale.length === 1")
    page.wait_for_timeout(100)
    stale = page.evaluate("window.__log.stale")
    assert [(entry["event"], entry["reason"]) for entry in stale] == [("save", "superseded")]
    late_drops = [m for m in messages if m.startswith("debug:") and "dropped the response" in m]
    assert late_drops == [
        "debug:[Citry] events: dropped the response of 'save': a newer call superseded it (latest_wins)."
    ]
    assert downloads == []
    assert page.evaluate("window.__log.error") == []
    assert _citry_errors(messages) == []


# ----- wait: false joins no graph -----


def _make_racer_app() -> tuple[Citry, str, type[Component]]:
    """One widget with two render handlers, for racing a wait:false send against a queued one."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class RacerState:
        shown: str = "start"
        _public = ("shown",)

        def render(self):
            return Racer(shown=self.shown)

    class Racer(Component):
        citry = c
        State = RacerState

        class Events:
            def slow_render(self, state):
                state.shown = "slow"
                return state.render()

            def fast_render(self, state):
                state.shown = "fast"
                return state.render()

        template = """
          <div class="racer">
            <span class="shown" x-text="$state.shown">{{ shown }}</span>
          </div>
        """

        def template_data(self, kwargs, slots):
            return {"shown": kwargs.get("shown", "start")}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>wait false</title></head>
            <body>
              <c-racer />
            </body>
          </html>
        """

    return c, str(Page()), Racer


def test_wait_false_fires_immediately_holds_nothing_and_late_render_epoch_drops(page: Any, serve_live: Any) -> None:
    # A wait:false send joins no graph (design 5.6): it fires immediately,
    # gains no edges, no later event gains an edge to it (the later send from
    # the SAME anchor fires while it is still in flight), and its late
    # render is exactly what the per-anchor epoch guard nets: dropped with
    # reason `epoch` while its promise still resolves.
    c, html, racer = _make_racer_app()
    messages = _goto(page, serve_live, c, html)
    requests = _collect_event_requests(page)
    held_slow = _hold_route(page, _event_url(racer, "slow_render"))
    held_fast = _hold_route(page, _event_url(racer, "fast_render"))

    racer_id = page.evaluate("document.querySelector('.racer').getAttribute('data-cid')")
    page.evaluate(_TRACK, [racer_id, "slow_render", None, {"wait": False}, "slow"])
    page.evaluate(_TRACK, [racer_id, "fast_render", None, None, "fast"])

    # Both went to the wire despite sharing the anchor: the wait:false send
    # sits in no graph (the snapshot shows only the queued fast send), so
    # the fast send gained no edge to it.
    _wait_held(page, held_slow, 1)
    _wait_held(page, held_fast, 1)
    snapshot = page.evaluate(_SNAPSHOT)
    assert [(entry["event"], entry["dispatched"], entry["waitsOn"]) for entry in snapshot] == [
        ("fast_render", True, [])
    ]

    # The fast response applies first (epoch 2 lands).
    held_fast[0].continue_()
    page.wait_for_function("document.querySelector('.shown').innerText === 'fast'")
    page.wait_for_function("window.__o.fast !== undefined")

    # The slow response arrives late: its instance-mutating render is
    # epoch-dropped (the applier's comparison), its promise still resolves,
    # and the DOM keeps the fast render.
    held_slow[0].continue_()
    page.wait_for_function("window.__o.slow !== undefined")
    page.wait_for_function("window.__log.stale.length === 1")
    assert page.evaluate("window.__o.slow") == ["ok", "__undefined__"]
    stale = page.evaluate("window.__log.stale")
    assert [(entry["event"], entry["reason"]) for entry in stale] == [("slow_render", "epoch")]
    assert page.evaluate("document.querySelector('.shown').innerText") == "fast"
    assert [r["url"].rsplit("/", 1)[-1] for r in requests] == ["slow_render", "fast_render"]
    assert _citry_errors(messages) == []


def test_two_wait_false_sends_share_a_trigger_busy_refcount(page: Any, serve_live: Any) -> None:
    c, html, _parent, _child = _make_parent_child_app()
    messages = _goto(page, serve_live, c, html)
    page.evaluate(
        """() => {
          window.__bypassDeliveries = [];
          Citry.events.registerTransport('bypass-held', {
            send: (envelope) => new Promise((resolve) => {
              window.__bypassDeliveries.push(() => resolve({
                protocol: envelope.protocol,
                requestId: envelope.requestId,
                results: envelope.calls.map((call) => ({ ok: true, sendSequence: call.sendSequence, actions: [] })),
              }));
            }),
          });
          Citry.events.configure({ transport: 'bypass-held' });
          const trigger = document.querySelector('.child .go');
          window.__bypassDone = 0;
          Citry.events.send(trigger, 'ping', {}, { wait: false }).finally(() => { window.__bypassDone += 1; });
          Citry.events.send(trigger, 'ping', {}, { wait: false }).finally(() => { window.__bypassDone += 1; });
        }"""
    )
    page.wait_for_function("window.__bypassDeliveries.length === 2")
    assert page.locator(".child .go").get_attribute("data-citry-busy") == ""

    page.evaluate("window.__bypassDeliveries[0]()")
    page.wait_for_function("window.__bypassDone === 1")
    assert page.locator(".child .go").get_attribute("data-citry-busy") == ""

    page.evaluate("window.__bypassDeliveries[1]()")
    page.wait_for_function("window.__bypassDone === 2")
    assert page.locator(".child .go").get_attribute("data-citry-busy") is None
    assert _citry_errors(messages) == []


# ----- busy from the gesture -----


def test_busy_spans_the_queue_from_the_gesture(page: Any, serve_live: Any) -> None:
    # Busy state spans the queue (design 5.6): the gesture, not the send,
    # starts the pending UI. A child send queued behind its in-flight parent
    # stamps data-citry-busy on the child's root and on the triggering
    # element and counts in $loading from enqueue, stays busy through queue
    # and flight, and clears on settle.
    c, html, parent, child = _make_parent_child_app()
    messages = _goto(page, serve_live, c, html)
    held_slow = _hold_route(page, _event_url(parent, "slow"))
    held_ping = _hold_route(page, _event_url(child, "ping"))

    parent_id = page.evaluate("document.querySelector('.parent').getAttribute('data-cid')")
    page.evaluate(_TRACK, [parent_id, "slow", None, None, "slow"])
    # The child send dispatches from its trigger element (the queue's busy
    # stamp lands on it, design 5.5/5.6).
    page.evaluate(
        """
        () => {
          window.__o = window.__o || {};
          Citry.events.send(document.querySelector(".child .go"), "ping", {}).then(
            (v) => { window.__o.ping = ["ok", v === undefined ? "__undefined__" : v]; },
            (e) => { window.__o.ping = ["err", String((e && e.message) || e)]; },
          );
        }
        """
    )

    # Queued, not sent, and already busy: the root, the trigger, and both
    # $loading forms show the gesture.
    busy_queued = page.evaluate(
        """
        () => ({
          rootBusy: document.querySelector(".child").hasAttribute("data-citry-busy"),
          triggerBusy: document.querySelector(".child .go").hasAttribute("data-citry-busy"),
          parentBusy: document.querySelector(".parent").hasAttribute("data-citry-busy"),
          text: document.querySelector(".c-busy").innerText,
          queued: Citry.events._internal.queue.snapshot().length,
        })
        """
    )
    assert busy_queued == {"rootBusy": True, "triggerBusy": True, "parentBusy": True, "text": "busy", "queued": 2}
    assert len(held_ping) == 0

    # Through flight: the parent settles, the child's call goes to the wire,
    # and the busy surface never blinked (the applier re-stamped the linked
    # anchor's fresh roots and the surviving trigger).
    held_slow[0].continue_()
    page.wait_for_function(f"{_SNAPSHOT}.some((n) => n.event === 'ping' && n.dispatched)")
    _wait_held(page, held_ping, 1)
    busy_flight = page.evaluate(
        """
        () => ({
          rootBusy: document.querySelector(".child").hasAttribute("data-citry-busy"),
          triggerBusy: document.querySelector(".child .go").hasAttribute("data-citry-busy"),
          text: document.querySelector(".c-busy").innerText,
        })
        """
    )
    assert busy_flight == {"rootBusy": True, "triggerBusy": True, "text": "busy"}

    # Settle clears it.
    held_ping[0].continue_()
    page.wait_for_function("window.__o.ping !== undefined")
    page.wait_for_function("document.querySelector('.c-busy').innerText === 'idle'")
    busy_settled = page.evaluate(
        """
        () => ({
          rootBusy: document.querySelector(".child").hasAttribute("data-citry-busy"),
          triggerBusy: document.querySelector(".child .go").hasAttribute("data-citry-busy"),
        })
        """
    )
    assert busy_settled == {"rootBusy": False, "triggerBusy": False}
    assert _citry_errors(messages) == []


# ----- the tick-skip rule -----


def test_recurring_tick_skips_while_the_previous_call_is_outstanding(page: Any, serve_live: Any) -> None:
    # The tick-skip rule (design 5.6): a recurring send (the bindings entry's
    # private key) whose previous call is still queued or in flight is
    # skipped with a debug breadcrumb and no promise, never enqueued behind
    # it; once the call settles, the next tick sends again.
    c, html, _parent, child = _make_parent_child_app()
    messages = _goto(page, serve_live, c, html)
    held_ping = _hold_route(page, _event_url(child, "ping"))

    first = page.evaluate(
        """
        () => {
          const el = document.querySelector(".child");
          window.__tick = Citry.events._internal.sendFromElement(el, "ping", {}, undefined, "poll:1");
          window.__tick.then(() => { window.__tickDone = true; });
          return window.__tick !== null;
        }
        """
    )
    assert first is True
    skipped = page.evaluate(
        """
        () => Citry.events._internal.sendFromElement(
          document.querySelector(".child"), "ping", {}, undefined, "poll:1",
        ) === null
        """
    )
    assert skipped is True
    breadcrumbs = [m for m in messages if m.startswith("debug:") and "skipped a recurring" in m]
    assert breadcrumbs == [
        "debug:[Citry] events: skipped a recurring 'ping' tick: its previous call is still queued or in flight."
    ]
    _wait_held(page, held_ping, 1)
    assert len(held_ping) == 1  # the skipped tick sent nothing

    held_ping[0].continue_()
    page.wait_for_function("window.__tickDone === true")
    next_tick = page.evaluate(
        """
        () => Citry.events._internal.sendFromElement(
          document.querySelector(".child"), "ping", {}, undefined, "poll:1",
        ) !== null
        """
    )
    assert next_tick is True
    page.wait_for_function("Citry.events._internal.queue.snapshot().length === 1")
    _wait_held(page, held_ping, 2)
    held_ping[1].continue_()
    page.wait_for_function("Citry.events._internal.queue.snapshot().length === 0")
    assert _citry_errors(messages) == []


def test_public_recurring_option_is_ordinary_data_and_send_always_returns_a_promise(
    page: Any, serve_live: Any
) -> None:
    c, html, _parent, child = _make_parent_child_app()
    messages = _goto(page, serve_live, c, html)
    held_ping = _hold_route(page, _event_url(child, "ping"))
    outcome = page.evaluate(
        """() => {
          const id = document.querySelector('.child').getAttribute('data-cid');
          const first = Citry.events.send(id, 'ping', {}, { recurring: 'user-value' });
          const second = Citry.events.send(id, 'ping', {}, { recurring: 'user-value' });
          window.__publicRecurring = false;
          Promise.all([first, second]).then(() => { window.__publicRecurring = true; });
          return [first instanceof Promise, second instanceof Promise];
        }"""
    )
    assert outcome == [True, True]
    _wait_held(page, held_ping, 1)
    held_ping[0].continue_()
    _wait_held(page, held_ping, 2)
    held_ping[1].continue_()
    page.wait_for_function("window.__publicRecurring === true")
    assert _citry_errors(messages) == []
