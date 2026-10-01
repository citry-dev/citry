"""
The browser shows State that an Events handler changed, even when the handler
does not render the component again.

The server then answers with a `state` action that carries the public State
values beside the new token. These tests drive a real browser through each
kind of handler answer that relies on that action, and through the ordering
cases where an older value must not replace a newer one.
"""

from __future__ import annotations

import threading
from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events import actions, event
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e

_FIRST_STATE = """() => {
  const app = __citryRuntime._apps.values().next().value;
  const mounted = [...app.mounted.values()].find(item => item.component.$state?.count !== undefined);
  return mounted.component.$state;
}"""


def _engine(secret: str) -> Citry:
    app = Citry(secret=secret, autodiscover=False)
    app.set_mounted_prefix("/citry")
    return app


def _collect_calls(page: Any) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    return calls


def _collect_errors(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    return errors


@pytest.mark.parametrize("handler", ["bump_none", "bump_data", "bump_mark"])
def test_state_bindings_show_values_a_handler_changed_without_rendering(
    page: Any, serve_live: Any, handler: str
) -> None:
    app = _engine("state-refresh-test")

    class Badge(Component):
        citry = app

        class Kwargs:
            count: int

        template = """
          <output id="badge">{{ count }}</output>
        """

        def template_data(self, kwargs, slots):
            return {"count": kwargs.count}

    class Counter(Component):
        citry = app

        class State:
            count: int = 0
            name: str = "first"

        class Events:
            # Each handler changes State and leaves the component itself on the page,
            # so only the `state` action can carry the new values to the browser.
            def bump_none(self, state):
                state.count += 1
                state.name = f"server-{state.count}"

            def bump_data(self, state):
                state.count += 1
                state.name = f"server-{state.count}"
                return actions.Data({"count": state.count})

            def bump_mark(self, state):
                state.count += 1
                state.name = f"server-{state.count}"
                return actions.Render(Badge(count=state.count), target="mark:badge")

        template = f"""
          <section>
            <button
              id="go"
              @c-click="{handler}"
            >
              go
            </button>
            <output
              id="count"
              v-text="$state.count"
            ></output>
            <input
              id="name"
              :c-name
            >
            <c-mark name="badge">
              <output id="badge">0</output>
            </c-mark>
          </section>
        """

    dispatcher_for(app)
    errors = _collect_errors(page)
    page.goto(serve_live(app, Counter().render().serialize(), "") + "/")
    page.wait_for_selector("#count")
    assert page.locator("#count").text_content() == "0"

    page.locator("#go").click()
    page.wait_for_function("document.querySelector('#count').textContent === '1'")
    # A two-way State binding shows the server's value too, not only `$state` reads.
    page.wait_for_function("document.querySelector('#name').value === 'server-1'")
    if handler == "bump_mark":
        page.wait_for_function("document.querySelector('#badge').textContent.trim() === '1'")

    page.locator("#go").click()
    page.wait_for_function("document.querySelector('#count').textContent === '2'")
    page.wait_for_function("document.querySelector('#name').value === 'server-2'")
    assert errors == []


def test_nested_child_shows_its_own_changed_state(page: Any, serve_live: Any) -> None:
    app = _engine("state-refresh-child-test")

    class Child(Component):
        citry = app

        class State:
            clicks: int = 0

        class Events:
            def press(self, state):
                state.clicks += 1

        template = """
          <div>
            <button
              id="child-go"
              @c-click="press"
            >
              press
            </button>
            <output
              id="child-clicks"
              v-text="$state.clicks"
            ></output>
          </div>
        """

    class Parent(Component):
        citry = app

        class State:
            total: int = 7

        class Events:
            def noop(self, state):
                return None

        template = """
          <main>
            <output
              id="parent-total"
              v-text="$state.total"
            ></output>
            <c-Child />
          </main>
        """

    dispatcher_for(app)
    errors = _collect_errors(page)
    page.goto(serve_live(app, Parent().render().serialize(), "") + "/")
    page.wait_for_selector("#child-clicks")

    page.locator("#child-go").click()
    page.wait_for_function("document.querySelector('#child-clicks').textContent === '1'")
    page.locator("#child-go").click()
    page.wait_for_function("document.querySelector('#child-clicks').textContent === '2'")
    # The refresh names the child's render ID, so the parent's State is untouched.
    assert page.locator("#parent-total").text_content() == "7"
    assert errors == []


def test_a_browser_write_made_while_a_call_is_in_flight_is_kept_and_sent_next(page: Any, serve_live: Any) -> None:
    app = _engine("state-refresh-pending-test")
    slow_started = threading.Event()
    release = threading.Event()

    class Draft(Component):
        citry = app

        class State:
            count: int = 0
            draft: str = "server"

        class Events:
            def slow(self, state):
                # Hold the answer until the browser has made its local write.
                slow_started.set()
                release.wait(5)
                state.count += 1

            def save(self, state):
                state.count += 10

        template = """
          <section>
            <button
              id="slow"
              @c-click="slow"
            >
              slow
            </button>
            <button
              id="save"
              @c-click="save"
            >
              save
            </button>
            <output
              id="count"
              v-text="$state.count"
            ></output>
            <output
              id="draft"
              v-text="$state.draft"
            ></output>
          </section>
        """

    dispatcher_for(app)
    calls = _collect_calls(page)
    errors = _collect_errors(page)
    page.goto(serve_live(app, Draft().render().serialize(), "") + "/")
    page.wait_for_selector("#count")

    page.locator("#slow").click()
    assert slow_started.wait(5)
    # The call is already on the wire, so this write stays unsent until the next call.
    page.evaluate(f"({_FIRST_STATE})().draft = 'local'")
    release.set()
    page.wait_for_function("document.querySelector('#count').textContent === '1'")
    # The refresh brought count=1 and draft='server', but the unsent local draft wins.
    assert page.locator("#draft").text_content() == "local"

    page.locator("#save").click()
    page.wait_for_function("document.querySelector('#count').textContent === '11'")
    assert page.locator("#draft").text_content() == "local"
    assert calls[0]["calls"][0].get("stateUpdates") is None
    assert calls[1]["calls"][0]["stateUpdates"] == {"draft": "local"}
    assert errors == []


class PickIn:
    value: int


def test_a_superseded_slow_answer_does_not_replace_newer_state(page: Any, serve_live: Any) -> None:
    app = _engine("state-refresh-supersede-test")
    slow_started = threading.Event()
    release = threading.Event()

    class Picker(Component):
        citry = app

        class State:
            count: int = 0

        class Events:
            @event(latest_wins=True)
            def pick(self, data: PickIn, state):
                if data.value == 1:
                    # The first call answers last: the browser has moved on by then.
                    slow_started.set()
                    release.wait(5)
                state.count = data.value

        template = """
          <section>
            <button
              id="first"
              @c-click="pick({value: 1})"
            >
              first
            </button>
            <button
              id="second"
              @c-click="pick({value: 2})"
            >
              second
            </button>
            <output
              id="count"
              v-text="$state.count"
            ></output>
          </section>
        """

    dispatcher_for(app)
    page.goto(serve_live(app, Picker().render().serialize(), "") + "/")
    page.wait_for_selector("#count")

    page.locator("#first").click()
    assert slow_started.wait(5)
    page.locator("#second").click()
    page.wait_for_function("document.querySelector('#count').textContent === '2'")
    release.set()
    # Give the slow answer time to arrive; the browser already dropped that call.
    page.wait_for_timeout(300)
    assert page.locator("#count").text_content() == "2"


def test_a_delayed_state_refresh_loses_to_a_newer_answer(page: Any, serve_live: Any) -> None:
    app = _engine("state-refresh-delayed-test")

    class Delayed(Component):
        citry = app

        class State:
            count: int = 0

        class Events:
            def bump(self, state):
                state.count += 1

        template = """
          <section>
            <button
              id="bump"
              @c-click="bump"
            >
              bump
            </button>
            <output
              id="count"
              v-text="$state.count"
            ></output>
          </section>
        """

    dispatcher_for(app)
    errors = _collect_errors(page)
    page.goto(serve_live(app, Delayed().render().serialize(), "") + "/")
    page.wait_for_selector("#count")

    # Schedule an old refresh that would show 99, then let a real call answer first.
    page.evaluate(
        """() => {
          const app = __citryRuntime._apps.values().next().value;
          const renderId = [...app.occurrences.values()].find(item => item.renderId).renderId;
          window.__staleReasons = [];
          document.addEventListener('citry:events:stale', event => {
            window.__staleReasons.push(event.detail.reason);
          });
          return Citry.events.applyActions([{
            action: 'state',
            targetRenderId: renderId,
            stateToken: 'scheduled-token',
            publicState: {count: 99},
            delay: 0.4,
            wait: false,
          }]);
        }"""
    )
    page.locator("#bump").click()
    page.wait_for_function("document.querySelector('#count').textContent === '1'")
    page.wait_for_function("window.__staleReasons.length === 1", timeout=3000)
    assert page.locator("#count").text_content() == "1"
    assert [error for error in errors if "stale" not in error.lower()] == []
