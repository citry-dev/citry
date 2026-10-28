"""
The listener modifiers `.outside`, `.window`, `.document`, `.debounce` and `.throttle` on Vue listeners (#170).

The Vue compiler rewrites each such listener into a `v-citry-on` directive that
the browser runtime runs. These tests drive a real browser through the
documented author-facing cases: the Alpine-style menu, a hidden `.outside`
element, listeners on `window` and `document` that stop when the element
unmounts, a debounced call across a server re-render, and the interplay with
Vue's own modifiers.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")
expect = pytest.importorskip("playwright.sync_api").expect
pytestmark = pytest.mark.e2e


def _engine(secret: str) -> Citry:
    engine = Citry(secret=secret, autodiscover=False)
    engine.set_mounted_prefix("/citry")
    return engine


def _open(page: Any, serve_live: Any, open_citry_page: Any, root: type[Component]) -> list[str]:
    """Serve `root` as the whole page, wait for the app to mount, and return the browser errors collected so far."""
    # Every case must run without a browser error, so each collects them.
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: faults.append(message.text) if message.type == "error" else None)
    open_citry_page(serve_live(root.citry, root().render().serialize(), "") + "/")
    return faults


def test_menu_button_toggles_and_outside_click_closes(
    page: Any, serve_live: Any, open_citry_page: Any, settle_timers: Any
) -> None:
    engine = _engine("listener-modifiers-menu-secret")

    class Menu(Component):
        citry = engine

        template = """
          <main>
            <button
              id="toggle"
              @click="open = !open"
            >menu</button>
            <div
              id="panel"
              v-show="open"
              @click.outside="open = false"
            >
              <button id="inside">inside</button>
            </div>
            <p id="elsewhere">elsewhere</p>
          </main>
        """
        js = """
          $component({data(){return {open: false}}});
        """

    faults = _open(page, serve_live, open_citry_page, Menu)
    panel = page.locator("#panel")
    expect(panel).to_be_hidden()

    # The toggle button sits outside the panel. Its own handler runs first
    # and the outside handler after it, so the first click must leave the
    # panel open and the second must close it.
    page.locator("#toggle").click()
    expect(panel).to_be_visible()
    settle_timers()
    expect(panel).to_be_visible()
    page.locator("#toggle").click()
    expect(panel).to_be_hidden()

    # A click elsewhere on the page closes an open panel.
    page.locator("#toggle").click()
    expect(panel).to_be_visible()
    page.locator("#elsewhere").click()
    expect(panel).to_be_hidden()

    # A click inside the panel, on the panel or on a child, leaves it open.
    page.locator("#toggle").click()
    expect(panel).to_be_visible()
    page.locator("#inside").click()
    settle_timers()
    expect(panel).to_be_visible()
    panel.click(position={"x": 1, "y": 1})
    settle_timers()
    expect(panel).to_be_visible()
    assert faults == [], faults


@pytest.mark.parametrize("hidden", ["element", "ancestor"])
def test_outside_does_not_call_the_handler_while_the_element_is_hidden(
    page: Any, serve_live: Any, open_citry_page: Any, settle_timers: Any, hidden: str
) -> None:
    engine = _engine("listener-modifiers-hidden-secret")

    class Hidden(Component):
        citry = engine

        def js_data(self, kwargs, slots):
            # The element itself is hidden by `v-show` in one case, and its
            # wrapper (so a hidden ancestor) in the other.
            return {"open": hidden != "element", "wrapperOpen": hidden != "ancestor", "hits": 0}

        template = """
          <main>
            <button
              id="show"
              @click.stop="open = true; wrapperOpen = true"
            >show</button>
            <p id="elsewhere">elsewhere</p>
            <div
              id="wrapper"
              v-show="wrapperOpen"
            >
              <div
                id="panel"
                v-show="open"
                @click.outside="hits++"
              >panel</div>
            </div>
            <output id="hits" v-text="hits"></output>
          </main>
        """
        js = """
          $component({});
        """

    faults = _open(page, serve_live, open_citry_page, Hidden)
    expect(page.locator("#panel")).to_be_hidden()
    hits = page.locator("#hits")

    # Clicks elsewhere while the panel is hidden do not call its handler.
    page.locator("#elsewhere").click()
    page.locator("#elsewhere").click()
    settle_timers()
    expect(hits).to_have_text("0")

    # The show button stops the click, so the outside handler does not see it.
    page.locator("#show").click()
    expect(page.locator("#panel")).to_be_visible()
    settle_timers()
    expect(hits).to_have_text("0")

    # Once visible, the same listener runs for an outside click and not for an
    # inside click, which proves the earlier zero was the visibility check.
    page.locator("#elsewhere").click()
    expect(hits).to_have_text("1")
    page.locator("#panel").click()
    settle_timers()
    expect(hits).to_have_text("1")
    assert faults == [], faults


def test_window_and_document_listeners_fire_anywhere_and_stop_after_unmount(
    page: Any, serve_live: Any, open_citry_page: Any, settle_timers: Any
) -> None:
    engine = _engine("listener-modifiers-window-secret")

    class Watcher(Component):
        citry = engine

        template = """
          <main>
            <button
              id="toggle"
              @click.stop="shown = !shown"
            >toggle</button>
            <p id="anywhere">anywhere</p>
            <div
              v-if="shown"
              id="watcher"
              @keydown.escape.window="escapes++"
              @click.document="clicks++"
            >watcher</div>
            <output id="escapes" v-text="escapes"></output>
            <output id="clicks" v-text="clicks"></output>
          </main>
        """
        js = """
          $component({data(){return {shown: true, escapes: 0, clicks: 0}}});
        """

    faults = _open(page, serve_live, open_citry_page, Watcher)
    escapes = page.locator("#escapes")
    clicks = page.locator("#clicks")

    # Other keys do not match `.escape`, and Escape works with focus on the
    # page body, far from the element.
    page.keyboard.press("a")
    settle_timers()
    expect(escapes).to_have_text("0")
    page.keyboard.press("Escape")
    expect(escapes).to_have_text("1")

    # A click on an unrelated element reaches the document listener.
    page.locator("#anywhere").click()
    expect(clicks).to_have_text("1")

    # The toggle button stops its click, so only the unmount is observed. Both
    # listeners must be gone afterwards.
    page.locator("#toggle").click()
    expect(page.locator("#watcher")).to_have_count(0)
    page.keyboard.press("Escape")
    page.locator("#anywhere").click()
    settle_timers()
    expect(escapes).to_have_text("1")
    expect(clicks).to_have_text("1")
    assert faults == [], faults


def test_debounced_call_survives_a_server_rerender_and_runs_once_with_the_last_value(
    page: Any, serve_live: Any, open_citry_page: Any, fake_clock: Any, send_event: Any
) -> None:
    engine = _engine("listener-modifiers-debounce-secret")

    class Search(Component):
        citry = engine

        class State:
            renders: int = 0

        class Events:
            def refresh(self, state: Search.State):
                state.renders += 1
                return actions.Render(Search(renders=state.renders))

        def template_data(self, kwargs, slots):
            return {"renders": int(kwargs.get("renders", 0))}

        template = """
          <section>
            <input
              id="field"
              @input.debounce.500ms="record($event.target.value)"
            >
            <button
              id="refresh"
              @c-click="refresh"
            >refresh</button>
            <output id="renders">{{ renders }}</output>
            <output id="calls" v-text="calls.join('|')"></output>
          </section>
        """
        js = """
          $component({
            data(){return {calls: []}},
            methods: {record(value){this.calls.push(value)}},
          });
        """

    dispatcher_for(engine)
    # Pause the clock before the page starts its timers, so only the steps
    # below move them and "before the delay" is exact rather than a race.
    fake_clock.install_paused()
    faults = _open(page, serve_live, open_citry_page, Search)
    field = page.locator("#field")
    calls = page.locator("#calls")

    field.fill("a")
    field.fill("ab")
    fake_clock.run_for(100)
    # Mark the element so a replaced input is noticed after the re-render.
    page.evaluate("document.querySelector('#field').dataset.original = 'yes'")

    # The server re-renders the component while the debounced call is pending.
    send_event(lambda: page.locator("#refresh").click(), handler="refresh")
    expect(page.locator("#renders")).to_have_text("1")
    assert page.locator("#field").get_attribute("data-original") == "yes"
    expect(calls).to_have_text("")

    # One millisecond short of 500 ms after the last input, nothing has run.
    fake_clock.run_short_of(400)
    expect(calls).to_have_text("")

    # Past the delay the call runs once with the last value.
    fake_clock.run_past_deadline()
    expect(calls).to_have_text("ab")
    fake_clock.run_for(1000)
    expect(calls).to_have_text("ab")
    assert faults == [], faults


def test_debounced_call_is_cancelled_when_the_element_unmounts(
    page: Any, serve_live: Any, open_citry_page: Any, fake_clock: Any
) -> None:
    engine = _engine("listener-modifiers-debounce-unmount-secret")

    class Search(Component):
        citry = engine

        template = """
          <section>
            <input
              v-if="shown"
              id="gone"
              @input.debounce.500ms="record('gone:' + $event.target.value)"
            >
            <input
              id="kept"
              @input.debounce.500ms="record('kept:' + $event.target.value)"
            >
            <button
              id="remove"
              @click="shown = false"
            >remove</button>
            <output id="calls" v-text="calls.join('|')"></output>
          </section>
        """
        js = """
          $component({
            data(){return {shown: true, calls: []}},
            methods: {record(value){this.calls.push(value)}},
          });
        """

    fake_clock.install_paused()
    faults = _open(page, serve_live, open_citry_page, Search)
    calls = page.locator("#calls")

    # Both inputs have a pending call. Removing one of them must cancel only
    # its call; the other, which is the control, proves the timers did run.
    page.locator("#gone").fill("x")
    page.locator("#kept").fill("y")
    page.locator("#remove").click()
    expect(page.locator("#gone")).to_have_count(0)
    expect(calls).to_have_text("")

    fake_clock.run_for(600)
    expect(calls).to_have_text("kept:y")
    fake_clock.run_for(1000)
    expect(calls).to_have_text("kept:y")
    assert faults == [], faults


@pytest.mark.parametrize("binding", ["@click.once", "@click.once.document"])
def test_once_runs_on_the_first_click_only(
    page: Any, serve_live: Any, open_citry_page: Any, settle_timers: Any, binding: str
) -> None:
    engine = _engine("listener-modifiers-once-secret")

    class Once(Component):
        citry = engine

        template = f"""
          <main>
            <div @click="all++">
              <button
                id="once"
                {binding}="once++"
              >once</button>
            </div>
            <output id="once-count" v-text="once"></output>
            <output id="all-count" v-text="all"></output>
          </main>
        """
        js = """
          $component({data(){return {once: 0, all: 0}}});
        """

    faults = _open(page, serve_live, open_citry_page, Once)
    page.locator("#once").click()
    expect(page.locator("#once-count")).to_have_text("1")
    # The wrapper's plain listener counts every click, so it proves the second
    # click happened and only the `.once` listener ignored it.
    page.locator("#once").click()
    expect(page.locator("#all-count")).to_have_text("2")
    settle_timers()
    expect(page.locator("#once-count")).to_have_text("1")
    assert faults == [], faults


def test_a_document_listener_ignores_the_click_that_mounted_it(
    page: Any, serve_live: Any, open_citry_page: Any, settle_timers: Any
) -> None:
    engine = _engine("listener-modifiers-mount-secret")

    class Popup(Component):
        citry = engine

        template = """
          <main>
            <button
              id="open"
              @click="shown = true"
            >open</button>
            <p id="anywhere">anywhere</p>
            <div
              v-if="shown"
              id="popup"
              @click.document="clicks++"
              @click.once.document="once++"
            >popup</div>
            <output id="clicks" v-text="clicks"></output>
            <output id="once" v-text="once"></output>
          </main>
        """
        js = """
          $component({data(){return {shown: false, clicks: 0, once: 0}}});
        """

    faults = _open(page, serve_live, open_citry_page, Popup)
    # The click that mounts the popup reaches `document` after Vue mounted the
    # new listeners. The browser's real event times must mark it as older than
    # them, so neither counts it and `.once` is not used up by it.
    page.locator("#open").click()
    expect(page.locator("#popup")).to_have_count(1)
    settle_timers()
    expect(page.locator("#clicks")).to_have_text("0")
    expect(page.locator("#once")).to_have_text("0")
    page.locator("#anywhere").click()
    page.locator("#anywhere").click()
    expect(page.locator("#clicks")).to_have_text("2")
    expect(page.locator("#once")).to_have_text("1")
    assert faults == [], faults


@pytest.mark.parametrize(
    ("modifiers", "button"),
    [
        ("right", "right"),
        ("right.document", "right"),
        ("middle", "middle"),
        ("middle.document", "middle"),
    ],
)
def test_mouse_button_modifiers_run_on_that_button_only(
    page: Any, serve_live: Any, open_citry_page: Any, settle_timers: Any, modifiers: str, button: str
) -> None:
    engine = _engine("listener-modifiers-buttons-secret")

    class Buttons(Component):
        citry = engine

        template = f"""
          <main>
            <button
              id="target"
              @click.{modifiers}="hits++"
            >target</button>
            <output id="hits" v-text="hits"></output>
          </main>
        """
        js = """
          $component({data(){return {hits: 0}}});
        """

    faults = _open(page, serve_live, open_citry_page, Buttons)
    target = page.locator("#target")
    hits = page.locator("#hits")

    # The other buttons do not run the handler. A left click is the one the
    # `click` event name alone would have matched.
    target.click()
    target.click(button="middle" if button == "right" else "right")
    settle_timers()
    expect(hits).to_have_text("0")

    target.click(button=button)
    expect(hits).to_have_text("1")
    assert faults == [], faults
