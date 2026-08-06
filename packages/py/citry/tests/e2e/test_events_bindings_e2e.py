"""
Browser e2e for the client bindings runtime, including the element-listener half of
``citry/ext/events/client/citry-events.js`` (design contract:
docs/design/events.md 5.1's vocabulary and modifier tables, 5.5's machinery
item 5, and 5.6's tick-skip rule; the compiled ``data-cev-*`` attribute
contract is the one published in ``citry/ext/events/bindings.py``).

What this suite locks, mapped to the design:

- Element listeners read the compiled specs at event time: a click binding
  sends its handler; one element carrying several event bindings evaluates
  each argument expression against its own ``$event`` (the explicit
  multi-binding case, design 5.1).
- The modifier table: ``.prevent`` stops the browser default while the send
  still happens, including for a cancelable synthetic event whose name also
  belongs to a non-cancelable native event; ``.stop`` keeps ancestors' bindings from firing while the
  element's own binding fires (and an unstopped click fires the ancestor's
  binding too, target first); ``.self`` ignores events bubbling up from
  descendants; ``.once`` fires at most once per element lifetime; ``.enter``
  and ``.escape`` send only for their key; bare ``.debounce`` holds 250 ms
  and carries the last trigger's value; an explicit time segment
  (``.debounce.600ms``) overrides the bare default; a handler's
  ``@event(debounce=...)`` default applies to a bare binding; bare
  ``.throttle`` admits the first trigger and drops the rest of the window.
  Key filters inspect ``event.key`` rather than restricting event names, so
  an arbitrarily named ``KeyboardEvent`` participates too.
- Argument expressions are Alpine expressions bound to the owning element:
  they see ``$event``, ``$el``, and ``$state``, and a non-object result
  raises the pointed error naming the binding, with nothing sent.
- Fire-time anchor resolution (machinery item 5): a debounce flush whose
  region a render replaced drops with the drop event (reason ``cancelled``)
  and a debug line, never a throw.
- ``@c-poll``: interval sends ride the element-keyed timer structure; a
  morph-surviving region polls at single cadence (no double poll); a
  replaced region's timer dies with it (no dead interval keeps firing: no
  ghost drop lines afterwards); a tick overlapping its previous call skips
  with the queue's debug breadcrumb; ticks pause while the tab is hidden
  and resume when it is visible again.
- The ``$component`` props form, the events-runtime half: every payload
  carries ``props`` and a bare callback sees an empty object; declared props
  resolve through ``Citry.events._resolveProps`` (defaults per instance, a
  function default never shared, validation failing loudly naming the
  component and the prop, resolved values reactive through Alpine).
- The ``$component`` config form end to end (the registration half lives
  in the dependency manager, ``citry/ext/dependencies/client/citry.js``): a
  ``{init, props}`` registration's init receives the resolved values
  under ``props`` while a bare callback on the same class keeps the empty
  object, and a failing validation logs the pointed error and skips just
  that handler, before it runs.

Uses the live-server harness (conftest ``serve_live``) like the sibling
suites. Region teardown is driven through the public ``applyActions`` entry
(the applier suite's pattern), so no second component is needed to replace a
region. Locked strings and shapes were observed from the real runtime first,
then locked.
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

# Registered where a test asserts drop surfacing: collects the lifecycle
# events (design 5.2's detail contract).
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


def _collect_console(page: Any) -> list[str]:
    """Start collecting console messages as ``type:text`` strings."""
    messages: list[str] = []
    page.on("console", lambda msg: messages.append(f"{msg.type}:{msg.text}"))
    return messages


def _collect_pageerrors(page: Any) -> list[str]:
    """Start collecting uncaught page errors as strings."""
    errors: list[str] = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    return errors


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


def _wait_requests(page: Any, captured: list[dict], count: int, timeout_ms: int = 5000) -> None:
    """Wait until ``count`` events-route requests were captured."""
    deadline = time.monotonic() + timeout_ms / 1000
    while len(captured) < count:
        if time.monotonic() > deadline:
            msg = f"expected {count} captured request(s), saw {len(captured)}"
            raise AssertionError(msg)
        page.wait_for_timeout(25)


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
    """Wait until ``count`` requests sit at a held route."""
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


def _args_of(captured: list[dict]) -> list[dict]:
    """The wire args of every captured call, in request order."""
    out: list[dict] = []
    for request in captured:
        for call in (request["body"] or {}).get("calls", []):
            out.append(call.get("args", {}))
    return out


# ----- the modifier matrix and argument expressions -----


def _make_matrix_app() -> tuple[Citry, str, type[Component]]:
    """One interactive component carrying every binding form the matrix tests drive."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class MatrixState:
        seen: int = 3
        _public = ("seen",)

    class Matrix(Component):
        citry = c
        State = MatrixState

        # Input schemas nested on the component so the handler annotations
        # resolve under `from __future__ import annotations` (the dispatcher
        # resolves them against the component's nested classes).
        class TapIn:
            kind: str = ""
            q: str = ""
            sid: int = 0
            did: str = ""

        class SeekIn:
            q: str = ""

        class Events:
            # The dispatcher resolves the `data` annotation against the
            # component's nested classes, which ruff cannot see lexically.
            def tap(self, data: TapIn, state):  # noqa: F821
                return None

            # The handler-level default (design 3.5): the rewrite merges it
            # into the compiled spec, so a bare binding debounces at 200 ms.
            @event(debounce=200)
            def seek(self, data: SeekIn, state):  # noqa: F821
                return None

        template = """
          <div class="matrix">
            <button
              class="both"
              @c-click="tap({kind: $event.type})"
              @c-mouseover="tap({kind: $event.type})"
            >both</button>
            <a
              class="plink"
              href="/never"
              @c-click.prevent="tap({kind: 'prevent'})"
            >link</a>
            <div
              class="outerbox"
              x-data
              @click="window.__alpineOuter = (window.__alpineOuter || 0) + 1"
              @c-click="tap({kind: 'outer'})"
            >
              <button
                class="stopbtn"
                @click="window.__alpineSameTarget = (window.__alpineSameTarget || 0) + 1"
                @c-click.stop="tap({kind: 'stopped'})"
              >stop</button>
              <button class="passbtn" @c-click="tap({kind: 'passed'})">pass</button>
            </div>
            <div
              class="selfbox"
              style="padding: 14px"
              @c-click.self="tap({kind: 'self'})"
            >
              <span class="inside">child</span>
            </div>
            <button class="oncebtn" @c-click.once="tap({kind: 'once'})">once</button>
            <div class="synthetic-prevent" @c-scroll.prevent="tap({kind: 'scroll-prevent'})"></div>
            <div class="custom-key" @c-lol.enter="tap({kind: 'custom-enter'})"></div>
            <input class="keyinput" @c-keyup.enter="tap({kind: 'enter'})" />
            <input class="esckey" @c-keyup.escape="tap({kind: 'escape'})" />
            <input class="deb" @c-input.debounce="tap({q: $event.target.value})" />
            <input class="deb600" @c-input.debounce.600ms="tap({q: $event.target.value})" />
            <input class="cfg" @c-input="seek({q: $event.target.value})" />
            <button class="thr" @c-click.throttle="tap({kind: 'thr'})">thr</button>
            <button
              class="rich"
              c-data-id="item_id"
              @c-click="tap({sid: $state.seen, did: $el.dataset.id})"
            >rich</button>
            <button class="bad" @c-click="tap(42)">bad</button>
          </div>
        """

        def template_data(self, kwargs, slots):
            return {"item_id": 7}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>bindings e2e</title></head>
            <body>
              <c-matrix />
            </body>
          </html>
        """

    return c, str(Page()), Matrix


def test_multi_binding_element_sends_each_event_with_its_own_expression(page: Any, serve_live: Any) -> None:
    # One element carrying several event bindings (the explicit e2e case,
    # design 5.1): each binding evaluates its own argument expression against
    # the same element, with its own $event.
    c, html, matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)
    debug = page.evaluate("Citry.events._internal.debug()")

    # `.both` is the fixture's only element with two event types. The target
    # count is listener registrations, not another spelling of element count.
    assert debug["bindingListenerTargets"] == debug["bindingListenerElements"] + 1

    page.hover(".both")
    page.click(".both")
    _wait_requests(page, captured, 2)

    assert [args["kind"] for args in _args_of(captured)] == ["mouseover", "click"]
    assert all(r["url"].endswith(f"/e/{matrix.class_id}/tap") for r in captured)
    assert _citry_errors(messages) == []


def test_changing_an_event_type_reconciles_the_native_listener_without_leaking_the_old_type(
    page: Any, serve_live: Any
) -> None:
    c, html, matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)
    before = page.evaluate("Citry.events._internal.debug()")

    page.evaluate(
        """
        () => {
          const el = document.querySelector('.both');
          window.__bothListenerOps = [];
          el.addEventListener = function(type, listener, options) {
            window.__bothListenerOps.push(['add', type]);
            return EventTarget.prototype.addEventListener.call(this, type, listener, options);
          };
          el.removeEventListener = function(type, listener, options) {
            window.__bothListenerOps.push(['remove', type]);
            return EventTarget.prototype.removeEventListener.call(this, type, listener, options);
          };
          const raw = el.getAttribute('data-cev-on');
          const bytes = Uint8Array.from(atob(raw), (character) => character.charCodeAt(0));
          const specs = JSON.parse(new TextDecoder().decode(bytes));
          specs.find((spec) => spec.event === 'mouseover').event = 'private-change';
          const encoded = btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(specs))));
          el.setAttribute('data-cev-on', encoded);
        }
        """
    )
    page.wait_for_function(
        """
        () => JSON.stringify(window.__bothListenerOps) ===
          JSON.stringify([['remove', 'mouseover'], ['add', 'private-change']])
        """
    )
    after = page.evaluate("Citry.events._internal.debug()")

    page.dispatch_event(".both", "mouseover")
    page.dispatch_event(".both", "private-change")
    _wait_requests(page, captured, 1)
    page.wait_for_timeout(50)

    assert len(captured) == 1
    assert captured[0]["url"].endswith(f"/e/{matrix.class_id}/tap")
    assert _args_of(captured) == [{"kind": "private-change"}]
    assert after["bindingListenerElements"] == before["bindingListenerElements"]
    assert after["bindingListenerTargets"] == before["bindingListenerTargets"]
    assert _citry_errors(messages) == []


def test_same_type_spec_update_reuses_the_listener_and_runs_only_the_new_handler(page: Any, serve_live: Any) -> None:
    c, html, matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)
    before = page.evaluate("Citry.events._internal.debug()")

    page.evaluate(
        """
        () => {
          const el = document.querySelector('.rich');
          const raw = el.getAttribute('data-cev-on');
          const bytes = Uint8Array.from(atob(raw), (character) => character.charCodeAt(0));
          const specs = JSON.parse(new TextDecoder().decode(bytes));
          specs[0].handler = 'seek';
          specs[0].args = "{q: 'changed'}";
          const encoded = btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(specs))));
          el.setAttribute('data-cev-on', encoded);
          el.click();
        }
        """
    )
    _wait_requests(page, captured, 1)
    page.wait_for_timeout(50)
    after = page.evaluate("Citry.events._internal.debug()")

    assert len(captured) == 1
    assert captured[0]["url"].endswith(f"/e/{matrix.class_id}/seek")
    assert _args_of(captured) == [{"q": "changed"}]
    assert after["bindingListenerElements"] == before["bindingListenerElements"]
    assert after["bindingListenerTargets"] == before["bindingListenerTargets"]
    assert _citry_errors(messages) == []


def test_prevent_modifier_stops_the_browser_default_and_still_sends(page: Any, serve_live: Any) -> None:
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)
    url_before = page.url

    page.click(".plink")
    _wait_requests(page, captured, 1)
    page.wait_for_timeout(150)

    # preventDefault kept the anchor from navigating; the send still went out.
    assert page.url == url_before
    assert _args_of(captured) == [{"kind": "prevent"}]
    assert _citry_errors(messages) == []


def test_prevent_modifier_cancels_a_synthetic_event_with_a_native_noncancelable_name(
    page: Any, serve_live: Any
) -> None:
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    result = page.locator(".synthetic-prevent").evaluate(
        """
        element => {
          const event = new CustomEvent('scroll', { cancelable: true });
          return {
            dispatched: element.dispatchEvent(event),
            defaultPrevented: event.defaultPrevented,
          };
        }
        """
    )
    _wait_requests(page, captured, 1)

    assert result == {"dispatched": False, "defaultPrevented": True}
    assert _args_of(captured) == [{"kind": "scroll-prevent"}]
    assert _citry_errors(messages) == []


def test_stop_modifier_uses_native_propagation_while_an_unstopped_child_reaches_the_ancestor(
    page: Any, serve_live: Any
) -> None:
    # The binding runs on the element, so `.stop` keeps Citry, Alpine, and
    # ordinary DOM listeners on ancestors from seeing the event. It does not
    # suppress another listener on the same target.
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)
    page.evaluate(
        """
        () => {
          window.__nativeOuter = 0;
          window.__nativeSameTarget = 0;
          window.__alpineSameTarget = 0;
          document.querySelector('.outerbox').addEventListener('click', () => { window.__nativeOuter += 1; });
          document.querySelector('.stopbtn').addEventListener('click', () => { window.__nativeSameTarget += 1; });
        }
        """
    )

    page.click(".stopbtn")
    _wait_requests(page, captured, 1)
    page.wait_for_timeout(150)
    assert [args["kind"] for args in _args_of(captured)] == ["stopped"]
    assert page.evaluate(
        "[window.__alpineOuter || 0, window.__nativeOuter, window.__alpineSameTarget, window.__nativeSameTarget]"
    ) == [0, 0, 1, 1]

    page.click(".passbtn")
    _wait_requests(page, captured, 3)
    assert [args["kind"] for args in _args_of(captured)] == ["stopped", "passed", "outer"]
    assert page.evaluate(
        "[window.__alpineOuter, window.__nativeOuter, window.__alpineSameTarget, window.__nativeSameTarget]"
    ) == [1, 1, 1, 1]
    assert _citry_errors(messages) == []


def test_self_modifier_ignores_events_bubbling_from_descendants(page: Any, serve_live: Any) -> None:
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    # A click on the child bubbles up to the bound element, but `.self` only
    # accepts the element itself as the target.
    page.click(".inside")
    page.wait_for_timeout(250)
    assert captured == []

    # A click landing on the bound element's own padding is the element.
    page.click(".selfbox", position={"x": 5, "y": 5})
    _wait_requests(page, captured, 1)
    assert _args_of(captured) == [{"kind": "self"}]
    assert _citry_errors(messages) == []


def test_once_modifier_fires_at_most_once_per_element_lifetime(page: Any, serve_live: Any) -> None:
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.click(".oncebtn")
    page.click(".oncebtn")
    page.click(".oncebtn")
    _wait_requests(page, captured, 1)
    page.wait_for_timeout(300)

    assert _args_of(captured) == [{"kind": "once"}]
    assert _citry_errors(messages) == []


def test_key_filter_sends_only_for_the_named_key(page: Any, serve_live: Any) -> None:
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.focus(".keyinput")
    page.keyboard.press("a")
    page.keyboard.press("b")
    page.wait_for_timeout(250)
    assert captured == []

    page.keyboard.press("Enter")
    _wait_requests(page, captured, 1)
    assert _args_of(captured) == [{"kind": "enter"}]
    assert _citry_errors(messages) == []


def test_key_filter_accepts_an_arbitrarily_named_keyed_event(page: Any, serve_live: Any) -> None:
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.locator(".custom-key").evaluate(
        "element => element.dispatchEvent(new KeyboardEvent('lol', { key: 'Escape' }))"
    )
    page.wait_for_timeout(200)
    assert captured == []

    page.locator(".custom-key").evaluate(
        "element => element.dispatchEvent(new KeyboardEvent('lol', { key: 'Enter' }))"
    )
    _wait_requests(page, captured, 1)

    assert _args_of(captured) == [{"kind": "custom-enter"}]
    assert _citry_errors(messages) == []


def test_escape_key_filter_sends_only_for_the_escape_key(page: Any, serve_live: Any) -> None:
    # The other key filter of the 5.1 table: `.escape` accepts only
    # KeyboardEvent.key "Escape"; a letter or a different named key sends
    # nothing.
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.focus(".esckey")
    page.keyboard.press("a")
    page.keyboard.press("Enter")
    page.wait_for_timeout(250)
    assert captured == []

    page.keyboard.press("Escape")
    _wait_requests(page, captured, 1)
    assert _args_of(captured) == [{"kind": "escape"}]
    assert _citry_errors(messages) == []


def test_bare_debounce_collapses_a_burst_and_carries_the_last_value(page: Any, serve_live: Any) -> None:
    # Bare `.debounce` is 250 ms (design 5.1): a typing burst collapses into
    # one send whose argument expression evaluated against the LAST trigger.
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.type(".deb", "abc", delay=40)
    _wait_requests(page, captured, 1)
    page.wait_for_timeout(350)
    assert _args_of(captured) == [{"q": "abc"}]

    page.type(".deb", "d", delay=10)
    _wait_requests(page, captured, 2)
    assert _args_of(captured) == [{"q": "abc"}, {"q": "abcd"}]
    assert _citry_errors(messages) == []


def test_an_explicit_debounce_time_segment_overrides_the_bare_default(page: Any, serve_live: Any) -> None:
    # `.debounce.600ms` (design 5.1): the binding's own time segment is the
    # debounce window. At ~350 ms after the last keystroke, past the bare
    # 250 ms default, nothing has been sent yet; the send arrives once the
    # 600 ms window closes.
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.type(".deb600", "zz", delay=40)
    page.wait_for_timeout(350)
    assert captured == []

    _wait_requests(page, captured, 1)
    assert _args_of(captured) == [{"q": "zz"}]
    assert _citry_errors(messages) == []


def test_handler_configured_debounce_applies_to_a_bare_binding(page: Any, serve_live: Any) -> None:
    # `@event(debounce=200)` (design 3.5) is the handler's default; the
    # rewrite merges it into the compiled spec, so a binding with no modifier
    # of its own still debounces.
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.type(".cfg", "xy", delay=40)
    _wait_requests(page, captured, 1)
    page.wait_for_timeout(350)

    assert _args_of(captured) == [{"q": "xy"}]
    assert _citry_errors(messages) == []


def test_bare_throttle_admits_the_first_trigger_and_drops_the_window(page: Any, serve_live: Any) -> None:
    # Bare `.throttle` is 250 ms (design 5.1): the first trigger sends, the
    # rest of the window drops, and the next window's first trigger sends
    # again.
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    # Three synchronous clicks land well inside one 250 ms window.
    page.evaluate(
        """
        () => {
          const el = document.querySelector(".thr");
          el.click();
          el.click();
          el.click();
        }
        """
    )
    _wait_requests(page, captured, 1)
    page.wait_for_timeout(400)
    assert _args_of(captured) == [{"kind": "thr"}]

    page.evaluate("document.querySelector('.thr').click()")
    _wait_requests(page, captured, 2)
    assert _args_of(captured) == [{"kind": "thr"}, {"kind": "thr"}]
    assert _citry_errors(messages) == []


def test_argument_expressions_see_state_and_el(page: Any, serve_live: Any) -> None:
    # The expression is an ordinary Alpine expression bound to the owning
    # element (design 5.1): `$state` reads the instance's State, and per-item
    # data rides the `c-*` channel into `$el.dataset`.
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    page.click(".rich")
    _wait_requests(page, captured, 1)

    assert _args_of(captured) == [{"sid": 3, "did": "7"}]
    assert _citry_errors(messages) == []


def test_non_object_argument_result_raises_the_pointed_error_and_sends_nothing(page: Any, serve_live: Any) -> None:
    c, html, _matrix = _make_matrix_app()
    messages = _goto(page, serve_live, c, html)
    errors = _collect_pageerrors(page)
    captured = _collect_event_requests(page)

    page.click(".bad")
    page.wait_for_timeout(300)

    assert captured == []
    joined = "\n".join(errors)
    assert "the argument expression of the '@c-click' binding for handler 'tap'" in joined
    assert "must evaluate to an object" in joined
    assert "got a number" in joined
    assert _citry_errors(messages) == []


# ----- fire-time anchor resolution: a replaced region's debounce flush -----


def _make_typer_app() -> tuple[Citry, str, type[Component]]:
    """A debounced input inside a region the test replaces mid-debounce."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class TyperState:
        query: str = ""
        _public = ("query",)

    class Typer(Component):
        citry = c
        State = TyperState

        class PingIn:
            q: str = ""

        class Events:
            # Resolved against the component's nested classes (see the
            # matrix app's note).
            def ping(self, data: PingIn, state):  # noqa: F821
                return None

        template = """
          <div class="typer">
            <input class="q" @c-input.debounce="ping({q: $event.target.value})" />
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>bindings flush e2e</title></head>
            <body>
              <div class="zone">
                <c-typer />
              </div>
            </body>
          </html>
        """

    return c, str(Page()), Typer


def test_debounce_flush_on_a_replaced_region_drops_with_a_debug_log_never_a_throw(page: Any, serve_live: Any) -> None:
    # Machinery item 5 (design 5.5): a one-shot closure re-resolves its
    # element to an anchor when it fires. Here the region is replaced while
    # the flush timer is pending, so the flush finds no instance: the send
    # drops before anything hits the wire, with the drop event (reason
    # `cancelled`) and a debug line, and nothing throws.
    c, html, _typer = _make_typer_app()
    messages = _goto(page, serve_live, c, html)
    errors = _collect_pageerrors(page)
    captured = _collect_event_requests(page)

    page.type(".q", "x", delay=10)
    # Replace the whole region before the 250 ms debounce flushes (the
    # applier retires the departed instance synchronously).
    page.evaluate(
        """
        () => Citry.events.applyActions([
          { action: "render", target: ".zone", swap: "inner", html: "<p class='emptied'>gone</p>" },
        ])
        """
    )
    page.wait_for_function("document.querySelector('.emptied') !== null")
    page.wait_for_timeout(500)

    assert captured == []
    assert errors == []
    assert page.evaluate("window.__log.stale") == [{"instance": None, "event": "ping", "reason": "cancelled"}]
    drops = [m for m in messages if "dropped a 'ping' send" in m]
    assert len(drops) == 1
    assert drops[0].startswith("debug:")
    assert "its element is not live in this document" in drops[0]
    assert _citry_errors(messages) == []


def test_removing_an_event_attribute_keeps_work_already_accepted_by_debounce(page: Any, serve_live: Any) -> None:
    c, html, _typer = _make_typer_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    assert page.evaluate("Citry.events._internal.debug().bindingListenerTargets") == 1
    page.evaluate(
        """
        () => {
          const input = document.querySelector('.q');
          input.value = 'kept';
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.removeAttribute('data-cev-on');
        }
        """
    )
    page.wait_for_function("Citry.events._internal.debug().bindingListenerTargets === 0")
    _wait_requests(page, captured, 1)

    assert _args_of(captured) == [{"q": "kept"}]
    assert page.evaluate("window.__log.stale") == []
    assert _citry_errors(messages) == []


def test_debounce_flush_drops_after_the_element_moves_to_another_document(page: Any, serve_live: Any) -> None:
    c, html, _typer = _make_typer_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    adopted = page.evaluate(
        """
        () => {
          const input = document.querySelector('.q');
          input.value = 'foreign';
          input.dispatchEvent(new Event('input', { bubbles: true }));
          const frame = document.createElement('iframe');
          document.body.append(frame);
          frame.contentDocument.body.append(frame.contentDocument.adoptNode(input));
          return input.isConnected && input.ownerDocument === frame.contentDocument;
        }
        """
    )
    assert adopted is True
    page.wait_for_timeout(500)

    assert captured == []
    assert page.evaluate("window.__log.stale") == [{"instance": None, "event": "ping", "reason": "cancelled"}]
    assert any("its element is not live in this document" in message for message in messages)
    assert _citry_errors(messages) == []


# ----- Alpine structural copies: inert templates and live element listeners -----


def _make_dynamic_binding_app() -> tuple[Citry, str]:
    """An x-for template whose live copies carry custom event bindings."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class DynamicState:
        seen: int = 0
        _public = ("seen",)

    class Dynamic(Component):
        citry = c
        State = DynamicState

        class TapIn:
            item: int = 0

        class Events:
            def tap(self, data: TapIn, state):  # noqa: F821
                return None

        template = """
          <div class="dynamic" x-data="{ items: [] }">
            <button class="toggle" @click="items = items.length ? [] : [1, 2]">toggle</button>
            <template x-for="item in items" :key="item">
              <button
                class="dynamic-hit"
                :data-item="item"
                @c-private-event="tap({item: item})"
              >hit</button>
            </template>
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>dynamic binding copies</title></head>
            <body><c-dynamic /></body>
          </html>
        """

    return c, str(Page())


def test_alpine_template_bindings_activate_only_on_live_copies_without_stacking(page: Any, serve_live: Any) -> None:
    c, html = _make_dynamic_binding_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    assert page.evaluate("Citry.events._internal.debug().bindingListenerTargets") == 0
    assert (
        page.evaluate(
            """
        () => {
          const template = document.querySelector('template[x-for]');
          return template.content.querySelector('[data-cev-on]') !== null;
        }
        """
        )
        is True
    )

    page.click(".toggle")
    page.wait_for_function("document.querySelectorAll('.dynamic-hit').length === 2")
    page.wait_for_function("Citry.events._internal.debug().bindingListenerTargets === 2")
    page.evaluate(
        """
        () => document.querySelectorAll('.dynamic-hit').forEach(
          (el) => el.dispatchEvent(new CustomEvent('private-event')),
        )
        """
    )
    _wait_requests(page, captured, 2)
    assert [args["item"] for args in _args_of(captured)] == [1, 2]

    page.click(".toggle")
    page.wait_for_function("document.querySelectorAll('.dynamic-hit').length === 0")
    page.wait_for_function("Citry.events._internal.debug().bindingListenerTargets === 0")
    page.click(".toggle")
    page.wait_for_function("document.querySelectorAll('.dynamic-hit').length === 2")
    page.wait_for_function("Citry.events._internal.debug().bindingListenerTargets === 2")
    page.evaluate("document.querySelector('.dynamic-hit').dispatchEvent(new CustomEvent('private-event'))")
    _wait_requests(page, captured, 3)
    page.wait_for_timeout(150)

    assert [args["item"] for args in _args_of(captured)] == [1, 2, 1]
    assert _citry_errors(messages) == []


# ----- @c-poll: interval sends, retirement, tick-skip -----


def _make_poll_app() -> tuple[Citry, str, type[Component]]:
    """A polling region whose handler re-renders it (each tick morphs the region)."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class PollState:
        n: int = 0
        _public = ("n",)

        def render(self):
            return Poller(n=self.n)

    class Poller(Component):
        citry = c
        State = PollState

        class Events:
            def tick(self, state):
                state.n += 1
                return state.render()

        template = """
          <div class="poller" @c-poll.1s="tick">
            <span class="n" x-text="$state.n">{{ n }}</span>
          </div>
        """

        def template_data(self, kwargs, slots):
            return {"n": kwargs.get("n", 0)}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>poll e2e</title></head>
            <body>
              <c-poller />
            </body>
          </html>
        """

    return c, str(Page()), Poller


def test_poll_sends_on_its_interval_and_a_morph_survivor_never_double_polls(page: Any, serve_live: Any) -> None:
    # The timer is keyed to the element (design 5.5 machinery item 5): each
    # tick's self-render morphs the region in place, the element survives,
    # and the re-scan dedupes against the running timer, so the cadence
    # stays one send per interval instead of compounding.
    c, html, _poller = _make_poll_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    _wait_requests(page, captured, 1, timeout_ms=4000)
    started = len(captured)
    page.wait_for_timeout(2600)
    ticks = len(captured) - started

    # One send per second over ~2.6 s: two or three at single cadence; a
    # doubled timer would produce five or more.
    assert 2 <= ticks <= 4
    # Every tick applied: the counter advanced with the requests.
    assert int(page.inner_text(".n")) >= 2
    assert _citry_errors(messages) == []


def test_a_replaced_poll_region_stops_polling_with_no_dead_interval_left_firing(page: Any, serve_live: Any) -> None:
    # A replaced region's timer dies with it (design 5.5 machinery item 5):
    # after the replacement no further poll requests happen, and no ghost
    # timer keeps firing dropped sends into the console.
    c, html, _poller = _make_poll_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    _wait_requests(page, captured, 1, timeout_ms=4000)
    page.evaluate(
        """
        () => Citry.events.applyActions([
          { action: "render", target: ".poller", swap: "replace", html: "<p class='eplaced'>done</p>" },
        ])
        """
    )
    page.wait_for_function("document.querySelector('.eplaced') !== null")
    count_after_replace = len(captured)
    page.wait_for_timeout(2600)

    assert len(captured) == count_after_replace
    # A dead interval would keep firing and leave a dropped-send debug line
    # every second; a retired timer leaves none.
    assert [m for m in messages if "dropped a 'tick' send" in m] == []
    assert _citry_errors(messages) == []


def test_a_tick_overlapping_its_previous_call_skips_with_the_breadcrumb(page: Any, serve_live: Any) -> None:
    # The queue's tick-skip rule (design 5.6): at most one outstanding call
    # per recurring binding. With the first tick's request held, the next
    # tick skips with the debug breadcrumb instead of queueing behind it.
    c, html, poller = _make_poll_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)
    held = _hold_route(page, _event_url(poller, "tick"))

    _wait_held(page, held, 1, timeout_ms=4000)
    # Two more intervals elapse while the call is in flight; each tick skips.
    page.wait_for_timeout(2300)
    assert len(held) == 1
    assert len(captured) == 1
    breadcrumbs = [m for m in messages if "skipped a recurring 'tick' tick" in m]
    assert len(breadcrumbs) >= 1
    assert breadcrumbs[0].startswith("debug:")
    assert "its previous call is still queued or in flight" in breadcrumbs[0]

    held[0].continue_()
    page.wait_for_function("document.querySelector('.n').innerText === '1'")
    assert _citry_errors(messages) == []


def test_poll_ticks_pause_while_the_tab_is_hidden_and_resume_when_visible(page: Any, serve_live: Any) -> None:
    # Hidden-tab pause (design 5.1's @c-poll row): the interval keeps firing
    # but each tick reads document.hidden before sending, so shadowing the
    # property with an own getter exercises the exact pause path; deleting
    # the shadow restores the native getter and the next tick sends again.
    c, html, _poller = _make_poll_app()
    messages = _goto(page, serve_live, c, html)
    captured = _collect_event_requests(page)

    _wait_requests(page, captured, 1, timeout_ms=4000)
    page.evaluate(
        """
        () => {
          Object.defineProperty(document, "hidden", { get: () => true, configurable: true });
          document.dispatchEvent(new Event("visibilitychange"));
        }
        """
    )
    # Let a tick that was already past the check land, then freeze the count.
    page.wait_for_timeout(150)
    frozen = len(captured)
    page.wait_for_timeout(2600)
    assert len(captured) == frozen

    page.evaluate(
        """
        () => {
          delete document.hidden;
          document.dispatchEvent(new Event("visibilitychange"));
        }
        """
    )
    _wait_requests(page, captured, frozen + 1, timeout_ms=4000)
    assert _citry_errors(messages) == []


# ----- the $component props form (the events-runtime half) -----


def _make_props_app() -> tuple[Citry, str]:
    """A page with one interactive instance whose JS records its payload's props."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class DemoState:
        label: str = "d"
        _public = ("label",)

    class Demo(Component):
        citry = c
        State = DemoState

        class Events:
            def poke(self, state):
                return None

        js = """
          $component((ctx) => {
            window.__bare = { props: ctx.props, keys: Object.keys(ctx.props) };
          });
        """
        template = """
          <div class="demo">demo</div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>props e2e</title></head>
            <body>
              <c-demo />
            </body>
          </html>
        """

    return c, str(Page())


def test_a_bare_callback_sees_an_empty_props_object(page: Any, serve_live: Any) -> None:
    # Design 5.5: the payload's `props` member exists on every callback
    # context; the bare form declares nothing, so it is an empty object.
    c, html = _make_props_app()
    messages = _goto(page, serve_live, c, html)

    page.wait_for_function("!!window.__bare")
    assert page.evaluate("window.__bare") == {"props": {}, "keys": []}
    assert _citry_errors(messages) == []


def test_declared_props_resolve_defaults_per_instance_and_validate_loudly(page: Any, serve_live: Any) -> None:
    # The events-runtime half of the config form (design 5.5), exposed at
    # `Citry.events._resolveProps` for the dependency manager to call per
    # instance: defaults resolve per instance (a function default is called
    # each time, so an object default is never shared), validation runs
    # before init and fails loudly naming the component and the prop,
    # and the resolved values are reactive through plain Alpine reactivity.
    c, html = _make_props_app()
    messages = _goto(page, serve_live, c, html)

    out = page.evaluate(
        """
        async () => {
          const out = {};
          const declare = () => ({
            name: { type: [String, Boolean], default: "hi" },
            limit: { default: 5 },
            tags: { type: Array, default: () => [] },
          });
          const r1 = Citry.events._resolveProps("PropsDemo", declare());
          const r2 = Citry.events._resolveProps("PropsDemo", declare());
          r1.tags.push("mine");
          out.resolved = { name: r1.name, limit: r1.limit, tags1: r1.tags.slice(), tags2: r2.tags.slice() };
          try {
            Citry.events._resolveProps("PropsDemo", { title: { type: String, required: true } });
            out.requiredError = null;
          } catch (err) {
            out.requiredError = String(err.message);
          }
          try {
            Citry.events._resolveProps("PropsDemo", { title: { type: String, default: 5 } });
            out.typeError = null;
          } catch (err) {
            out.typeError = String(err.message);
          }
          let seen = null;
          window.Alpine.effect(() => { seen = r1.name; });
          r1.name = "later";
          await new Promise((res) => setTimeout(res, 20));
          out.reactive = seen;
          return out;
        }
        """
    )

    assert out["resolved"] == {"name": "hi", "limit": 5, "tags1": ["mine"], "tags2": []}
    assert "component PropsDemo prop 'title' is required" in out["requiredError"]
    assert "no value was supplied and it declares no default" in out["requiredError"]
    assert "component PropsDemo prop 'title': the value does not match the declared type" in out["typeError"]
    assert "expected String, got a number" in out["typeError"]
    assert out["reactive"] == "later"
    assert _citry_errors(messages) == []


# ----- the $component config form (the registration half, in citry.js) -----

# Run one instance's `$component` callback again, the documented citry.js
# contract for a later manifest naming the same id.
_RECALL_INSTANCE = """
(args) => {
  const el = document.querySelector(args.selector);
  const marker = Array.from(el.attributes)
    .map((a) => a.name)
    .find((n) => n.startsWith("data-cid-"));
  Citry.manager.callComponent(args.classId, marker.slice("data-cid-".length), null);
}
"""


def _wait_citry_errors(page: Any, messages: list[str], count: int, timeout_ms: int = 5000) -> None:
    """Wait until ``count`` error-level console messages were captured."""
    deadline = time.monotonic() + timeout_ms / 1000
    while len(_citry_errors(messages)) < count:
        if time.monotonic() > deadline:
            msg = f"expected {count} console error(s), saw {len(_citry_errors(messages))}"
            raise AssertionError(msg)
        page.wait_for_timeout(25)


def _make_config_props_app() -> tuple[Citry, str, type[Component]]:
    """A component registering once through the config form with valid props."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class GadgetState:
        tick: int = 0
        _public = ("tick",)

    class Gadget(Component):
        citry = c
        State = GadgetState

        class Events:
            def poke(self, state):
                return None

        js = """
          $component({
            props: {
              label: { type: String, default: "unset" },
              limit: { type: Number, default: () => 41 + 1 },
            },
            init: (ctx) => {
              window.__cfg = {
                label: ctx.props.label,
                limit: ctx.props.limit,
                keys: Object.keys(ctx.props).sort(),
              };
            },
          });
        """
        template = """
          <div class="gadget">gadget</div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>config props e2e</title></head>
            <body>
              <c-gadget />
            </body>
          </html>
        """

    return c, str(Page()), Gadget


def _make_broken_props_app() -> tuple[Citry, str, type[Component]]:
    """A component whose config form declares a required prop nothing supplies."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class BrokenState:
        tick: int = 0
        _public = ("tick",)

    class Broken(Component):
        citry = c
        State = BrokenState

        class Events:
            def poke(self, state):
                return None

        js = """
          $component({
            props: {
              title: { type: String, required: true },
            },
            init: () => {
              window.__never = true;
            },
          });
        """
        template = """
          <div class="broken">broken</div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>broken props e2e</title></head>
            <body>
              <c-broken />
            </body>
          </html>
        """

    return c, str(Page()), Broken


def test_a_config_form_init_receives_resolved_props_during_page_load(page: Any, serve_live: Any) -> None:
    # The registration half of the config form (design 5.5), through a real
    # `$component({init, props})`: the dependency manager resolves the
    # declaration via the events runtime right before init runs, so init sees
    # the resolved values under `props` (defaults included,
    # a function default called to produce its value).
    c, html, _ = _make_config_props_app()
    messages = _goto(page, serve_live, c, html)

    page.wait_for_function("!!window.__cfg")
    assert page.evaluate("window.__cfg") == {"label": "unset", "limit": 42, "keys": ["label", "limit"]}

    assert _citry_errors(messages) == []


def test_a_config_form_validation_failure_skips_init_loudly(page: Any, serve_live: Any) -> None:
    # Validation runs at instance initialization, before init (design
    # 5.5): a required prop nothing supplies fails loudly naming the
    # component and the prop, and init never runs.
    c, html, broken = _make_broken_props_app()
    # Registered before goto: the validation failure happens during page
    # load, so a thrown (instead of logged) error must be catchable here.
    errors = _collect_pageerrors(page)
    messages = _goto(page, serve_live, c, html)

    _wait_citry_errors(page, messages, 1)
    assert page.evaluate("window.__never") is None

    # Recalling the same instance remains in the same failure episode: init
    # stays skipped without duplicating the direct diagnostic.
    page.evaluate(_RECALL_INSTANCE, {"selector": ".broken", "classId": broken.class_id})
    page.wait_for_timeout(50)
    assert page.evaluate("window.__never") is None
    assert errors == []
    citry_errors = _citry_errors(messages)
    assert len(citry_errors) == 1
    assert f"component {broken.class_id} props" in citry_errors[0]
    assert "prop 'title' is required" in citry_errors[0]
    assert "current supply and declaration default are both undefined" in citry_errors[0]
