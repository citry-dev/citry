"""
Browser e2e for the client forms runtime, the state-binding half of
``citry/ext/events/client/citry-events.js`` (design contract:
docs/design/events.md 5.1's update-event table and form-collection rule,
5.5's preservation block and one-way rebind rule, 5.6's piggyback rule, and
4.2's ``updates`` field; the compiled ``data-cev-bind`` contract is the one
published in ``citry/ext/events/bindings.py``).

What this suite locks, mapped to the design:

- Two-way bindings: the control's update event drives one call carrying the
  ``$state`` write (the wire ``updates`` field) together with the named
  handler; ``.lazy`` moves a text control to its committed-value event;
  ``.on:<event>`` overrides the update event outright (with the key filter
  honored); a checkbox updates on ``change`` with a boolean value; a number
  input's update is a JSON number (a State field declared ``int`` takes
  numbers, and the server checks types without coercing, design 7.2); a
  debounced binding collapses a burst into one call carrying the final
  value; a throttled binding sends the burst's leading trigger immediately
  and captures the rest into one trailing flush carrying the final value,
  so the rate stays at one send per window and the last input still lands.
- The updates piggyback (design 4.2): a draft whose debounce timer is still
  pending rides any earlier call from the instance, its draft mark clears
  the moment that call goes to the wire, and the binding's named handler
  still runs as the designed flush when the timer expires.
- One-way application: a ``$state`` write reaches a bound control through
  reactivity alone (no server round trip); after a self-render the
  reconciled server value lands the same way. After parent renders the
  binding scan rebinds without stacking: a control that lived through three
  parent renders holds exactly one application effect and at most one flush
  timer (``_internal.forms.snapshot``).
- The preservation poles as live typing (design 5.5): with the events route
  held open, each self-render patch is released against a verified
  unsent-draft stage (first the mid-debounce DOM draft, then the pending
  unsent ``$state`` write), and the typed text and caret survive both
  races; a submit-then-clear handler still clears a focused, flushed field.
- The draft-under-parent-render pair (design 5.5's lifecycle): a draft
  flushed into an unkeyed child's ``$state`` is discarded when the parent's
  poll response lands, observable through the retirement warning, and the
  child's queued flush call then delivers the server's own value back; the
  same page with ``#c-key`` keeps the draft, whose queued flush call then
  delivers it to the server with the parent-render's fresh token.
- Form collection on submit (design 5.1): the form's named controls
  serialize into the args payload (repeated fields as lists, numeric
  controls as numbers, the no-JS codec's reserved fields skipped, unchecked
  checkboxes absent), explicit expression args win on collision, and the
  runtime submission delivers the same handler data as a no-JS urlencoded
  form post to the per-event route (the parity rule of design 6.2).

Uses the live-server harness (conftest ``serve_live``) like the sibling
suites. Locked strings and shapes were observed from the real runtime
first, then locked.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

SIGNING_KEY = "e2e-secret"

READY = "window.Citry && Citry.events && Citry.events._internal && Citry.events._internal.alpineStarted === true"


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
        if "/ext/events/" not in request.url or request.url.endswith("/runtime.js"):
            return
        body = None
        try:
            body = json.loads(request.post_data or "null")
        except ValueError:
            body = None
        captured.append({"url": request.url, "body": body})

    page.on("request", record)
    return captured


def _wait_requests(page: Any, captured: list[dict], count: int, timeout_ms: int = 5000) -> None:
    """Wait until ``count`` events-route requests were captured."""
    deadline = time.monotonic() + timeout_ms / 1000
    while len(captured) < count:
        if time.monotonic() > deadline:
            msg = f"expected {count} captured request(s), saw {len(captured)}"
            raise AssertionError(msg)
        page.wait_for_timeout(25)


def _hold_route(page: Any, url_pattern: str) -> list[Any]:
    """Stash requests to ``url_pattern`` unanswered until the test releases them."""
    held: list[Any] = []
    page.route(url_pattern, lambda route: held.append(route))
    return held


def _wait_held(page: Any, held: list[Any], count: int, timeout_ms: int = 5000) -> None:
    """Wait until ``count`` requests sit at a held route."""
    deadline = time.monotonic() + timeout_ms / 1000
    while len(held) < count:
        if time.monotonic() > deadline:
            msg = f"expected {count} held request(s), saw {len(held)}"
            raise AssertionError(msg)
        page.wait_for_timeout(25)


def _goto(page: Any, serve_live: Any, citry: Citry, html: str) -> tuple[list[str], str]:
    """Serve the page, open it, wait for the runtime; return console messages and the base URL."""
    messages = _collect_console(page)
    base = serve_live(citry, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    return messages, base


def _calls_of(captured: list[dict]) -> list[dict]:
    """Every wire call of every captured request, in request order."""
    calls: list[dict] = []
    for request in captured:
        calls.extend((request["body"] or {}).get("calls", []))
    return calls


def _page_for(c: Citry, body: str, title: str) -> str:
    class Page(Component):
        citry = c
        template = f"""
          <html>
            <head><title>{title}</title></head>
            <body>
              {body}
            </body>
          </html>
        """

    return str(Page())


# ----- two-way bindings: the update-event table and the wire shape -----


def _make_two_way_app() -> tuple[Citry, str, type[Component]]:
    """One component carrying every two-way control form the table tests drive."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class TwoWayState:
        q: str = ""
        note: str = ""
        title: str = ""
        active: bool = False
        count: int = 0
        memo: str = ""
        _public = ("q", "note", "title", "active", "count", "memo")

    class TwoWay(Component):
        citry = c
        State = TwoWayState

        class Events:
            def seek(self, state):
                return None

            def ping(self, state):
                return TwoWay()

        template = """
          <div class="tw">
            <input class="q" :c-q="seek" />
            <input class="lazy" :c-note.lazy="seek" />
            <input class="title" :c-title.on:keyup.enter="seek" />
            <input class="chk" type="checkbox" :c-active="seek" />
            <input class="num" type="number" :c-count="seek" />
            <input class="deb" :c-q.debounce.200ms="seek" />
            <input class="thr" :c-memo.throttle.500ms="seek" />
            <input class="slow" :c-note.debounce.30s="seek" />
            <button class="ping" @c-click="ping">ping</button>
            <span class="mirror" x-text="$state.q"></span>
          </div>
        """

    return c, _page_for(c, "<c-two-way />", "forms two-way"), TwoWay


def test_two_way_input_sends_one_call_carrying_the_update_and_the_handler(page: Any, serve_live: Any) -> None:
    # The core two-way promise (design 5.1): on the control's update event,
    # ONE call carries both the field update and the named event, so the
    # handler always sees fresh state. The write also lands in $state through
    # the same proxy as user writes, so reactivity sees it immediately.
    c, html, two_way = _make_two_way_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.fill(".q", "shoes")
    _wait_requests(page, captured, 1)

    calls = _calls_of(captured)
    assert len(calls) == 1
    assert calls[0]["handlerName"] == "seek"
    assert calls[0]["stateUpdates"] == {"q": "shoes"}
    assert calls[0]["args"] == {}
    assert calls[0]["stateToken"].startswith("cev1.")
    assert captured[0]["url"].endswith(f"/e/{two_way.class_id}/seek")
    assert page.inner_text(".mirror") == "shoes"
    assert _citry_errors(messages) == []


def test_lazy_binding_updates_on_the_committed_value_event_only(page: Any, serve_live: Any) -> None:
    # `.lazy` (design 5.1's table): a text control flushes on `change`, not
    # per keystroke.
    c, html, _two_way = _make_two_way_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.locator(".lazy").press_sequentially("abc")
    page.wait_for_timeout(300)
    assert captured == []

    page.locator(".lazy").press("Tab")  # commit: blur fires `change`
    _wait_requests(page, captured, 1)
    calls = _calls_of(captured)
    assert calls[0]["handlerName"] == "seek"
    assert calls[0]["stateUpdates"] == {"note": "abc"}
    assert _citry_errors(messages) == []


def test_on_override_with_key_filter_updates_only_for_that_key(page: Any, serve_live: Any) -> None:
    # `.on:keyup.enter` (design 5.1): the update event is overridden outright
    # and the key filter gates it.
    c, html, _two_way = _make_two_way_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.locator(".title").press_sequentially("hi")  # keyups for h and i: filtered out
    page.wait_for_timeout(200)
    assert captured == []
    assert page.evaluate("Citry.events._internal.drafts.has(document.querySelector('.title'))") is True

    # A server self-render before Enter must preserve the pre-trigger draft.
    page.evaluate(
        r"""() => {
          const id = document.querySelector('.tw').getAttribute('data-cid').split(/\s+/).pop();
          return Citry.events.send(id, 'ping');
        }"""
    )
    page.wait_for_function("Citry.events._internal.queue.snapshot().length === 0")
    assert page.input_value(".title") == "hi"
    assert page.evaluate("document.activeElement === document.querySelector('.title')") is True
    assert page.evaluate("Citry.events._internal.drafts.has(document.querySelector('.title'))") is True

    page.locator(".title").press("Enter")
    _wait_requests(page, captured, 2)
    calls = _calls_of(captured)
    assert calls[-1]["handlerName"] == "seek"
    assert calls[-1]["stateUpdates"] == {"title": "hi"}
    assert page.evaluate("Citry.events._internal.drafts.has(document.querySelector('.title'))") is False
    assert _citry_errors(messages) == []


def test_checkbox_updates_on_change_with_a_boolean_value(page: Any, serve_live: Any) -> None:
    c, html, _two_way = _make_two_way_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.check(".chk")
    _wait_requests(page, captured, 1)
    page.uncheck(".chk")
    _wait_requests(page, captured, 2)

    updates = [call["stateUpdates"] for call in _calls_of(captured)]
    assert updates == [{"active": True}, {"active": False}]
    assert _citry_errors(messages) == []


def test_number_input_updates_carry_a_json_number(page: Any, serve_live: Any) -> None:
    # A State field declared `int` takes JSON numbers; the server checks
    # types without coercing (design 7.2), so the client sends the numeric
    # control's typed value.
    c, html, _two_way = _make_two_way_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.fill(".num", "5")
    _wait_requests(page, captured, 1)

    value = _calls_of(captured)[0]["stateUpdates"]["count"]
    assert value == 5
    assert isinstance(value, int)
    assert _citry_errors(messages) == []


def test_debounced_two_way_collapses_a_burst_into_one_call_with_the_final_value(page: Any, serve_live: Any) -> None:
    c, html, _two_way = _make_two_way_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.locator(".deb").press_sequentially("abc", delay=50)
    page.wait_for_timeout(150)  # inside the 200 ms hold: nothing sent yet
    assert captured == []
    _wait_requests(page, captured, 1)

    calls = _calls_of(captured)
    assert len(calls) == 1
    assert calls[0]["stateUpdates"] == {"q": "abc"}
    assert _citry_errors(messages) == []


def test_throttled_two_way_burst_sends_leading_then_one_trailing_flush_with_the_final_value(
    page: Any, serve_live: Any
) -> None:
    # `.throttle` on a two-way binding (design 5.1's knobs): at most one send
    # per window, and the window's close still delivers the user's final
    # input (a pure leading-edge drop would silently lose the burst's last
    # keystrokes, the loss the preservation contract forbids; see
    # scheduleTwoWayUpdate in the runtime). A burst typed inside one 500 ms
    # window therefore produces exactly two calls: the leading flush carrying
    # the first character, then one trailing flush carrying the whole text.
    c, html, _two_way = _make_two_way_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.locator(".thr").press_sequentially("abcde")
    _wait_requests(page, captured, 2)
    page.wait_for_timeout(800)  # a further window with no input: no extra send
    assert len(captured) == 2

    calls = _calls_of(captured)
    assert [call["handlerName"] for call in calls] == ["seek", "seek"]
    assert [call["stateUpdates"] for call in calls] == [{"memo": "a"}, {"memo": "abcde"}]
    assert _citry_errors(messages) == []


def test_a_mid_debounce_draft_piggybacks_on_an_earlier_call_from_the_instance(page: Any, serve_live: Any) -> None:
    # The updates piggyback (design 4.2): another call from the instance
    # fires while the draft's 30 s debounce is still pending, so that call
    # carries the update too. The draft mark clears (the server is about to
    # see the value) while the flush timer stays armed: the named handler is
    # still the designed flush.
    c, html, _two_way = _make_two_way_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.locator(".slow").press_sequentially("draft")
    assert page.evaluate("Citry.events._internal.drafts.has(document.querySelector('.slow'))") is True

    page.click(".ping")
    _wait_requests(page, captured, 1)

    calls = _calls_of(captured)
    assert calls[0]["handlerName"] == "ping"
    assert calls[0]["stateUpdates"] == {"note": "draft"}
    snapshot = page.evaluate(
        """(() => {
          const el = document.querySelector('.slow');
          return {
            draft: Citry.events._internal.drafts.has(el),
            flushes: Citry.events._internal.forms.snapshot(el).flushes,
          };
        })()"""
    )
    assert snapshot == {"draft": False, "flushes": 1}
    assert _citry_errors(messages) == []


# ----- one-way application and the rebind walk -----


def _make_one_way_app() -> tuple[Citry, str, type[Component]]:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class OneWayState:
        label: str = "start"
        _public = ("label",)

    class OneWay(Component):
        citry = c
        State = OneWayState

        class Kwargs:
            label: str = "start"

        class Events:
            def repaint(self, state):
                return OneWay(label=state.label + "!")

        def template_data(self, kwargs, slots):
            return {"label": kwargs.label}

        template = """
          <div class="ow">
            <input class="disp" :c-label />
            <button class="setx" @click="$state.label = 'local'">set</button>
            <button class="rr" @c-click="repaint">repaint</button>
          </div>
        """

    return c, _page_for(c, "<c-one-way />", "forms one-way"), OneWay


def test_one_way_binding_applies_state_writes_through_reactivity_alone(page: Any, serve_live: Any) -> None:
    # The application a one-way binding is (design 5.5): an Alpine effect
    # over $state.<field>. A plain client-side write reaches the control
    # with no server call and no patch.
    c, html, _one_way = _make_one_way_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    assert page.input_value(".disp") == "start"
    page.click(".setx")
    page.wait_for_function("document.querySelector('.disp').value === 'local'")
    assert captured == []  # reactivity alone: nothing hit the wire
    assert _citry_errors(messages) == []


def test_one_way_re_application_after_a_self_render_comes_from_the_kept_state_identity(
    page: Any, serve_live: Any
) -> None:
    # After a self-render the reconcile keeps the State object's identity
    # (design 5.5), so the server's new value reaches the bound control with
    # no rebind: the same effect fires. The pending local write rides the
    # call (design 4.2), so the server sees 'local' and answers 'local!'.
    c, html, _one_way = _make_one_way_app()
    messages, _base = _goto(page, serve_live, c, html)

    page.click(".setx")
    page.wait_for_function("document.querySelector('.disp').value === 'local'")
    page.click(".rr")
    page.wait_for_function("document.querySelector('.disp').value === 'local!'")
    assert _citry_errors(messages) == []


def _make_rebind_app() -> tuple[Citry, str, type[Component], type[Component]]:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class KidState:
        note: str = "srv"
        _public = ("note",)

    class Kid(Component):
        citry = c
        State = KidState

        class Events:
            def save(self, state):
                return None

        template = """
          <div class="kid">
            <input class="kn" :c-note.debounce.10s="save" />
          </div>
        """

    class Parent(Component):
        citry = c

        class Events:
            def re(self, state):
                return Parent()

        class State:
            tick: int = 0

        template = """
          <div class="par">
            <button class="pre" @c-click="re">re</button>
            <c-kid />
          </div>
        """

    return c, _page_for(c, "<c-parent />", "forms rebind"), Parent, Kid


def test_rebind_after_parent_renders_holds_one_effect_and_one_timer_per_control(page: Any, serve_live: Any) -> None:
    # The no-stacking rule (design 5.5): after a parent render the innermost
    # id under a bound control changed (the unkeyed child resets), the old
    # effect subscribed to a retired anchor's values, and the binding scan
    # rebinds. Three parent renders leave exactly one live application
    # effect; the rebound effect applies writes on the FRESH anchor; and a
    # rearmed debounce still means one flush timer, not three.
    c, html, _parent, _kid = _make_rebind_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    for round_trip in range(1, 4):
        page.click(".pre")
        _wait_requests(page, captured, round_trip)
        page.wait_for_function(
            "Citry.events._internal.queue.snapshot().length === 0"  # settled means applied
        )

    snapshot = page.evaluate("Citry.events._internal.forms.snapshot(document.querySelector('.kn'))")
    assert snapshot == {"effects": 1, "flushes": 0}

    # The surviving control is bound to the fresh anchor: a $state write on
    # the CURRENT innermost instance reaches it through reactivity.
    page.evaluate(
        """(() => {
          const id = document.querySelector('.kid').getAttribute('data-cid');
          Citry.events._internal.getAnchor(id).stateProxy.note = 'rebound';
        })()"""
    )
    page.wait_for_function("document.querySelector('.kn').value === 'rebound'")

    page.locator(".kn").press_sequentially("x")
    snapshot = page.evaluate("Citry.events._internal.forms.snapshot(document.querySelector('.kn'))")
    assert snapshot == {"effects": 1, "flushes": 1}
    assert _citry_errors(messages) == []


# ----- the preservation poles as live typing -----


def _make_pole_app() -> tuple[Citry, str, type[Component], type[Component]]:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class TyperState:
        q: str = ""
        _public = ("q",)

    class Typer(Component):
        citry = c
        State = TyperState

        class Kwargs:
            q: str = ""

        class Events:
            def refresh(self, state):
                return Typer(q=state.q)

        def template_data(self, kwargs, slots):
            return {"q": kwargs.q}

        # 400 ms leaves the released patch a wide, deterministic window to
        # land while the next chunk of typing is still mid-debounce.
        template = """
          <div class="typer">
            <input class="q" :c-q.debounce.400ms="refresh" />
            <p class="echo">{{ q }}</p>
          </div>
        """

    class ChatState:
        msg: str = ""
        _public = ("msg",)

    class Chat(Component):
        citry = c
        State = ChatState

        class Events:
            def send(self, state):
                state.msg = ""
                return Chat()

        template = """
          <div class="chat">
            <input class="msg" :c-msg.on:keyup.enter="send" />
          </div>
        """

    body = "<c-typer />\n              <c-chat />"
    return c, _page_for(c, body, "forms poles"), Typer, Chat


_TYPER_STAGE = """(() => {
  const el = document.querySelector('.typer .q');
  const anchor = Citry.events._internal.getAnchor(document.querySelector('.typer').getAttribute('data-cid'));
  return { draft: Citry.events._internal.drafts.has(el), pending: Object.keys(anchor.pending) };
})()"""

_TYPER_CARET = """(() => {
  const el = document.querySelector('.typer .q');
  return { focused: document.activeElement === el, at: el.selectionStart };
})()"""


def test_fast_typing_over_a_stream_of_patches_loses_nothing_and_keeps_the_caret(page: Any, serve_live: Any) -> None:
    # Pole one (design 5.5, research R1), with the races made real: against a
    # free-running localhost server every response applies in the quiet gap
    # between keystrokes, when no unsent draft exists to race. Holding the
    # events route pins each patch instead: a response is released only once
    # the typing has re-entered a specific unsent-draft stage, verified right
    # before the release, so both protections are actually exercised.
    c, html, typer, _chat = _make_pole_app()
    held = _hold_route(page, f"**/e/{typer.class_id}/refresh")
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)
    q = page.locator(".typer .q")

    # Patch one races the mid-debounce stage. Call A (the "abc" flush) sits
    # unanswered while "def" is typed, so the tail lives only in the DOM (the
    # drafts record marks the control; $state holds nothing pending). The
    # released patch must not clobber it: the morph guard keeps the live
    # value and the post-patch re-apply skips the guard-kept control.
    q.press_sequentially("abc")
    _wait_held(page, held, 1)
    q.press_sequentially("def")
    assert page.evaluate(_TYPER_STAGE) == {"draft": True, "pending": []}
    held.pop(0).continue_()
    page.wait_for_function("document.querySelector('.typer .echo').innerText === 'abc'")
    assert page.input_value(".typer .q") == "abcdef"
    assert page.evaluate(_TYPER_CARET) == {"focused": True, "at": 6}

    # Patch two races the pending-write stage. Call B (the "def" flush) sits
    # unanswered while "XY" is typed mid-string; the "XY" flush then writes
    # $state and queues call C behind B, so the draft now lives only as a
    # pending unsent $state write (the DOM mark is gone). The released patch
    # must not revert the field: the pending write wins the reconcile and the
    # re-apply leaves the control alone, so the text and the mid-string caret
    # both survive.
    _wait_held(page, held, 1)
    for _ in range(3):
        q.press("ArrowLeft")
    q.press_sequentially("XY")  # value abcXYdef, caret after the Y
    page.wait_for_function(
        "Citry.events._internal.queue.snapshot().some((n) => n.event === 'refresh' && !n.dispatched)"
    )
    assert page.evaluate(_TYPER_STAGE) == {"draft": False, "pending": ["q"]}
    held.pop(0).continue_()
    page.wait_for_function("document.querySelector('.typer .echo').innerText === 'abcdef'")
    assert page.input_value(".typer .q") == "abcXYdef"
    assert page.evaluate(_TYPER_CARET) == {"focused": True, "at": 5}

    # Release call C (the "XY" flush's queued call): everything settles at
    # the full text, the caret never moved, and the three calls carried the
    # drafts in order.
    _wait_held(page, held, 1)
    held.pop(0).continue_()
    page.wait_for_function("Citry.events._internal.queue.snapshot().length === 0")
    page.wait_for_function("document.querySelector('.typer .echo').innerText === 'abcXYdef'")
    assert page.input_value(".typer .q") == "abcXYdef"
    assert page.evaluate(_TYPER_CARET) == {"focused": True, "at": 5}
    assert [call["stateUpdates"] for call in _calls_of(captured)] == [{"q": "abc"}, {"q": "abcdef"}, {"q": "abcXYdef"}]
    assert _citry_errors(messages) == []


def test_submit_then_clear_clears_a_still_focused_flushed_field(page: Any, serve_live: Any) -> None:
    # Pole two (design 5.5, the Turbo issue 1194 shape): the Enter flush
    # hands the draft to the server, so protection ends and the handler's
    # clear lands on the still-focused control.
    c, html, _typer, _chat = _make_pole_app()
    messages, _base = _goto(page, serve_live, c, html)

    page.locator(".chat .msg").press_sequentially("yo")
    page.locator(".chat .msg").press("Enter")
    page.wait_for_function("document.querySelector('.chat .msg').value === ''")

    still_focused = page.evaluate("document.activeElement === document.querySelector('.chat .msg')")
    assert still_focused is True
    assert _citry_errors(messages) == []


# ----- the draft-under-parent-render pair -----


def _make_poll_pair_app(*, keyed: bool) -> tuple[Citry, str, type[Component], type[Component]]:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class KidState:
        note: str = "srv"
        _public = ("note",)

    class Kid(Component):
        citry = c
        State = KidState

        class Events:
            def save(self, state):
                return Kid(note=state.note)

        class Kwargs:
            note: str = "srv"

        def template_data(self, kwargs, slots):
            return {}

        template = """
          <div class="kid">
            <input class="kn" :c-note.debounce.300ms="save" />
          </div>
        """

    kid_tag = "<c-kid #c-key=\"'kid'\" />" if keyed else "<c-kid />"

    class PollerState:
        beat: int = 0
        _public = ("beat",)

    class Poller(Component):
        citry = c
        State = PollerState

        class Events:
            def tick(self, state):
                return Poller()

        template = f"""
          <div class="pol" @c-poll.1s="tick">
            {kid_tag}
          </div>
        """

    return c, _page_for(c, "<c-poller />", "forms poll pair"), Poller, Kid


def _drive_poll_pair(page: Any, serve_live: Any, *, keyed: bool) -> tuple[list[str], list[dict], str, str]:
    """Type a draft into the kid while the parent's poll is in flight; release the poll; settle."""
    c, html, poller, _kid = _make_poll_pair_app(keyed=keyed)
    held = _hold_route(page, f"**/e/{poller.class_id}/tick")
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    _wait_held(page, held, 1, timeout_ms=5000)  # the first poll tick is in flight, unanswered
    token_before = page.evaluate(
        "Citry.events._internal.getAnchor(document.querySelector('.kid').getAttribute('data-cid')).token"
    )

    # Type the draft (the one-way application already filled the server's
    # "srv" at boot, so `fill` replaces the whole value) and tab away; the
    # 300 ms debounce then flushes it into $state and enqueues `save`, which
    # waits behind the in-flight parent poll (the kid's anchor is contained
    # in the poller's, design 5.6).
    page.locator(".kn").fill("draft")
    page.keyboard.press("Tab")
    page.wait_for_function("Citry.events._internal.queue.snapshot().some((n) => n.event === 'save' && !n.dispatched)")

    held[0].continue_()  # the parent's poll response lands now
    page.wait_for_function("Citry.events._internal.queue.snapshot().length === 0")
    page.wait_for_timeout(100)  # let the save response's morph settle
    save_calls = [call for call in _calls_of(captured) if call["handlerName"] == "save"]
    assert len(save_calls) == 1
    return messages, save_calls, token_before, page.input_value(".kn")


def test_a_draft_in_an_unkeyed_child_resets_under_the_parents_poll_with_the_retirement_warning(
    page: Any, serve_live: Any
) -> None:
    # The unkeyed half of the pair (design 5.5): the parent's render resets
    # the child wholesale, discarding the flushed-but-unsent draft with the
    # retirement warning (never silently), and the child's queued flush call
    # re-resolves to the fresh anchor, carrying no update.
    messages, save_calls, token_before, final_value = _drive_poll_pair(page, serve_live, keyed=False)

    warnings = [m for m in messages if "was reset or removed while holding pending unsent writes (note)" in m]
    assert len(warnings) == 1
    assert "updates" not in save_calls[0]
    assert save_calls[0]["stateToken"] != token_before  # the fresh anchor's parent-derived token
    assert final_value == "srv"


def test_the_same_draft_under_a_keyed_child_survives_and_flushes_with_the_fresh_token(
    page: Any, serve_live: Any
) -> None:
    # The keyed half (design 5.5): #c-key links the child across the
    # parent's render, the anchor (with its pending write) carries over, and
    # the queued flush call delivers the draft with the token the parent's
    # render just minted.
    messages, save_calls, token_before, final_value = _drive_poll_pair(page, serve_live, keyed=True)

    warnings = [m for m in messages if "was reset or removed while holding pending unsent writes" in m]
    assert warnings == []
    assert save_calls[0]["stateUpdates"] == {"note": "draft"}
    assert save_calls[0]["stateToken"] != token_before  # the parent's render replaced the token before the send
    assert final_value == "draft"


# ----- form collection and the no-JS parity -----

RECORDED: list[dict] = []


def _wait_recorded(page: Any, count: int, timeout_ms: int = 5000) -> None:
    """Wait until the server-side handler recorded ``count`` submissions (the request capture only proves the send)."""
    deadline = time.monotonic() + timeout_ms / 1000
    while len(RECORDED) < count:
        if time.monotonic() > deadline:
            msg = f"expected {count} recorded submission(s), saw {len(RECORDED)}"
            raise AssertionError(msg)
        page.wait_for_timeout(25)


def _make_form_app() -> tuple[Citry, str, type[Component]]:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class OrderForm(Component):
        citry = c

        class OrderIn:
            email: str = ""
            quantity: int = 1
            tags: list[str] = ()

        class Events:
            def submit(self, data: OrderIn):  # noqa: F821
                # Returning nothing acknowledges (design 3.4): the wire tests
                # here assert the call, not a render.
                RECORDED.append({"email": data.email, "quantity": data.quantity, "tags": list(data.tags)})

        template = """
          <div class="wrap">
            <form class="order" @c-submit.prevent="submit">
              <input name="email" />
              <input name="quantity" type="number" />
              <input name="tags" class="tag1" />
              <input name="tags" class="tag2" />
              <input name="promo" type="checkbox" />
              <input name="_citry_state_token" type="hidden" value="decoy-token" />
              <input name="_citry_caller_render_id" type="hidden" value="decoy-id" />
              <button type="submit" class="go">order</button>
            </form>
            <form class="clash" @c-submit.prevent="submit({email: 'expr@win', quantity: 9, tags: []})">
              <input name="email" value="form@lose" />
              <button type="submit" class="clashgo">clash</button>
            </form>
          </div>
        """

    return c, _page_for(c, "<c-order-form />", "forms collection"), OrderForm


def test_submit_collects_named_controls_with_codec_shapes_and_reserved_fields_skipped(
    page: Any, serve_live: Any
) -> None:
    # Form collection (design 5.1): FormData semantics (unchecked checkbox
    # absent), repeated fields as lists of strings, numeric controls as
    # numbers, and the no-JS codec's reserved fields never enter args.
    RECORDED.clear()
    c, html, _order_form = _make_form_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.fill(".order input[name=email]", "a@b.co")
    page.fill(".order input[name=quantity]", "2")
    page.fill(".tag1", "red")
    page.fill(".tag2", "blue")
    page.click(".go")
    _wait_requests(page, captured, 1)
    _wait_recorded(page, 1)

    call = _calls_of(captured)[0]
    assert call["handlerName"] == "submit"
    assert call["args"] == {"email": "a@b.co", "quantity": 2, "tags": ["red", "blue"]}
    assert RECORDED == [{"email": "a@b.co", "quantity": 2, "tags": ["red", "blue"]}]
    assert _citry_errors(messages) == []


def test_expression_args_win_over_collected_form_fields_on_collision(page: Any, serve_live: Any) -> None:
    RECORDED.clear()
    c, html, _order_form = _make_form_app()
    messages, _base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.click(".clashgo")
    _wait_requests(page, captured, 1)
    _wait_recorded(page, 1)

    call = _calls_of(captured)[0]
    assert call["args"]["email"] == "expr@win"
    assert RECORDED[0]["email"] == "expr@win"
    assert _citry_errors(messages) == []


def test_runtime_submission_and_no_js_form_post_deliver_the_same_handler_data(page: Any, serve_live: Any) -> None:
    # The parity rule (design 5.1/6.2): the JS path and the no-JS urlencoded
    # form post deliver the same call. Both submissions land the identical
    # validated data in the handler (the urlencoded strings bind to the
    # declared int field through the codec's source-aware rule; the JS path
    # sends the number directly).
    RECORDED.clear()
    c, html, order_form = _make_form_app()
    messages, base = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.fill(".order input[name=email]", "p@q.co")
    page.fill(".order input[name=quantity]", "3")
    page.fill(".tag1", "x")
    page.fill(".tag2", "y")
    page.click(".go")
    _wait_requests(page, captured, 1)
    _wait_recorded(page, 1)

    form_body = urllib.parse.urlencode([("email", "p@q.co"), ("quantity", "3"), ("tags", "x"), ("tags", "y")]).encode()
    post = urllib.request.Request(  # noqa: S310 - a fixed-scheme http URL to the test's own local server
        f"{base}/citry/ext/events/e/{order_form.class_id}/submit",
        data=form_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(post) as response:  # noqa: S310 - same local test server
        response.read()

    assert len(RECORDED) == 2
    assert RECORDED[0] == RECORDED[1]
    assert _citry_errors(messages) == []
