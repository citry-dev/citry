"""
Browser tests for the order in which `onServerRender` callbacks run.

A component's `onServerRender` callback runs after the component first mounts
and again after each server render that updates it. Citry runs the callbacks of
one pass children first, each parent after all of its descendants, and
siblings in the order they first mounted. The order follows the component
tree, so it does not change with the order of elements on the page or with the
order of components in a server response. A callback that throws stops the
callbacks that would run after it, and stops the app.

The page below holds a plain sibling, a parent with one child, a component
passed into another component's slot, and a keyed loop. Every callback pushes
its name onto `window.__order`, so a test reads the order straight from the
page. Each first-mount test runs on a page Vue hydrates and on a page Vue
mounts without hydrating.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.serialization import hydration_admission
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")

# The callbacks of the page below on the first mount: each child before its
# parent (Leaf, then Group; Filled, then Card; every Row, then the page), and
# the siblings Alpha, Group, Card and the Rows in the order they sit in the template.
_FIRST_MOUNT_ORDER = ["Alpha", "Leaf", "Group", "Filled", "Card", "Row:a", "Row:b", "Row:c", "Page"]


def _fail_in(page: Any, name: str) -> None:
    """Make the callback of the component called `name` throw, by setting a global before any script runs."""
    page.add_init_script(f"window.__failing = {name!r};")


def _build_page() -> tuple[Citry, type[Component]]:
    """Build the test page. Each callback throws when `window.__failing` names its component (see `_fail_in`)."""
    engine = Citry(secret="callback-order-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Leaf(Component):
        citry = engine
        template = """
            <i>leaf</i>
        """
        # The push comes first so a throwing callback still shows that it ran.
        js = """
            $component({
                onServerRender() {
                    (window.__order ||= []).push('Leaf');
                    if (window.__failing === 'Leaf') throw new Error('Leaf failed on purpose');
                },
            });
        """

    class Late(Component):
        citry = engine
        template = """
            <s>late</s>
        """
        # The push comes first so a throwing callback still shows that it ran.
        js = """
            $component({
                onServerRender() {
                    (window.__order ||= []).push('Late');
                    if (window.__failing === 'Late') throw new Error('Late failed on purpose');
                },
            });
        """

    class Group(Component):
        citry = engine
        template = """
            <section><c-Leaf /></section>
        """
        # The push comes first so a throwing callback still shows that it ran.
        js = """
            $component({
                onServerRender() {
                    (window.__order ||= []).push('Group');
                    if (window.__failing === 'Group') throw new Error('Group failed on purpose');
                },
            });
        """

    class Alpha(Component):
        citry = engine
        template = """
            <b>alpha</b>
        """
        # The push comes first so a throwing callback still shows that it ran.
        js = """
            $component({
                onServerRender() {
                    (window.__order ||= []).push('Alpha');
                    if (window.__failing === 'Alpha') throw new Error('Alpha failed on purpose');
                },
            });
        """

    class Card(Component):
        citry = engine
        template = """
            <article><c-slot name="default" /></article>
        """
        # The push comes first so a throwing callback still shows that it ran.
        js = """
            $component({
                onServerRender() {
                    (window.__order ||= []).push('Card');
                    if (window.__failing === 'Card') throw new Error('Card failed on purpose');
                },
            });
        """

    class Filled(Component):
        citry = engine
        template = """
            <u>filled</u>
        """
        # The push comes first so a throwing callback still shows that it ran.
        js = """
            $component({
                onServerRender() {
                    (window.__order ||= []).push('Filled');
                    if (window.__failing === 'Filled') throw new Error('Filled failed on purpose');
                },
            });
        """

    class Row(Component):
        citry = engine

        class Kwargs:
            name: str

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"name": kwargs.name}

        template = """
            <li>{{ name }}</li>
        """
        # Every instance shares one callback, so it reads its name from the element it rendered.
        js = """
            $component({
                onServerRender({els}) {
                    (window.__order ||= []).push('Row:' + els[0].textContent.trim());
                },
            });
        """

    class Page(Component):
        citry = engine

        class Kwargs:
            late: bool = False
            rows: tuple[str, ...] = ("a", "b", "c")

        class Events:
            # Each handler renders the whole page again. `grow` adds a component between two
            # existing ones, and `flip` also reverses the keyed rows.
            def grow(self) -> Any:
                return actions.Render(Page(late=True))

            def flip(self) -> Any:
                return actions.Render(Page(late=True, rows=("c", "b", "a")))

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"late": kwargs.late, "rows": kwargs.rows}

        template = """
            <main>
                <button
                    id="grow"
                    @c-click="grow"
                >grow</button>
                <button
                    id="flip"
                    @c-click="flip"
                >flip</button>
                <c-Alpha />
                <c-Late c-if="late" />
                <c-Group />
                <c-Card><c-Filled /></c-Card>
                <ul>
                    <c-Row
                        c-for="n in rows"
                        #c-key="n"
                        c-name="n"
                    />
                </ul>
            </main>
        """
        # The push comes first so a throwing callback still shows that it ran.
        js = """
            $component({
                onServerRender() {
                    (window.__order ||= []).push('Page');
                    if (window.__failing === 'Page') throw new Error('Page failed on purpose');
                },
            });
        """

    dispatcher_for(engine)
    return engine, Page


def _serialize(page_class: type[Component], *, hydrate: bool) -> str:
    """Return the page's HTML, and check that the server wrote it in the mode the test asked for."""
    rendered = page_class().render()
    html = rendered.serialize(ssr=hydrate)
    admission = hydration_admission(rendered)
    # A page that silently stopped hydrating would turn the hydrated case into a copy of the other one.
    assert admission is not None
    assert admission.hydrated is hydrate, admission
    assert ('"hydrate":true' in html) is hydrate
    return html


def _page_errors(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    return errors


@pytest.mark.e2e
@pytest.mark.parametrize("hydrate", [True, False], ids=["hydrated", "client-rendered"])
def test_first_mount_runs_children_before_parents_and_siblings_in_order(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, hydrate: bool
) -> None:
    engine, page_class = _build_page()
    errors = _page_errors(page)

    page.goto(serve_live(engine, _serialize(page_class, hydrate=hydrate), "") + "/")
    wait_for_citry_ready()

    # `citry:ready` waits for every first-mount callback, so the list is complete here.
    assert page.evaluate("window.__order") == _FIRST_MOUNT_ORDER
    assert errors == []


@pytest.mark.e2e
@pytest.mark.parametrize("hydrate", [True, False], ids=["hydrated", "client-rendered"])
def test_server_render_keeps_the_first_mount_order(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, send_event: Any, hydrate: bool
) -> None:
    engine, page_class = _build_page()
    errors = _page_errors(page)
    reversed_responses: list[list[str]] = []

    def list_updates_in_reverse(route: Any) -> None:
        # The server lists the updated components in one fixed order. Reversing it checks that the
        # callbacks do not follow the response: the two orders cannot both equal the mount order.
        response = route.fetch()
        body = response.json()
        for result in body["results"]:
            for action in result["actions"]:
                prepared = action.get("prepared")
                if prepared:
                    prepared["updatedIds"].reverse()
                    reversed_responses.append(prepared["updatedIds"])
        route.fulfill(response=response, body=json.dumps(body))

    page.route("**/ext/events/call", list_updates_in_reverse)
    page.goto(serve_live(engine, _serialize(page_class, hydrate=hydrate), "") + "/")
    wait_for_citry_ready()
    page.evaluate("window.__order = []")

    send_event(lambda: page.locator("#grow").click())

    # The server render updated every component of the page, and the callbacks of the pass
    # ran in the first-mount order, with the new `Late` placed where its mount puts it (see
    # the next test).
    assert len(reversed_responses[0]) >= len(_FIRST_MOUNT_ORDER)
    order = page.evaluate("window.__order")
    assert [name for name in order if name != "Late"] == _FIRST_MOUNT_ORDER
    assert errors == []


@pytest.mark.e2e
@pytest.mark.parametrize("hydrate", [True, False], ids=["hydrated", "client-rendered"])
def test_new_sibling_and_reordered_rows_follow_mount_order_not_page_order(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, send_event: Any, hydrate: bool
) -> None:
    engine, page_class = _build_page()
    errors = _page_errors(page)
    page.goto(serve_live(engine, _serialize(page_class, hydrate=hydrate), "") + "/")
    wait_for_citry_ready()
    page.evaluate("window.__order = []")

    send_event(lambda: page.locator("#grow").click())

    # `Late` sits second on the page, between Alpha and Group, but it mounted after the
    # components that were already there, so its callback runs after theirs, before their parent.
    page_order = page.evaluate("[...document.querySelectorAll('main > *')].map(element => element.tagName)")
    assert page_order == ["BUTTON", "BUTTON", "B", "S", "SECTION", "ARTICLE", "UL"]
    expected = [*_FIRST_MOUNT_ORDER[:-1], "Late", "Page"]
    assert page.evaluate("window.__order") == expected

    page.evaluate("window.__order = []")
    send_event(lambda: page.locator("#flip").click())

    # Vue moves the keyed rows, so the page now lists c, b, a. The callbacks still run a, b, c.
    rows = page.evaluate("[...document.querySelectorAll('li')].map(element => element.textContent)")
    assert rows == ["c", "b", "a"]
    assert page.evaluate("window.__order") == expected
    assert errors == []


@pytest.mark.e2e
@pytest.mark.parametrize("hydrate", [True, False], ids=["hydrated", "client-rendered"])
def test_throwing_callback_on_first_mount_stops_later_callbacks_and_the_app(
    page: Any, serve_live: Any, hydrate: bool
) -> None:
    engine, page_class = _build_page()
    _fail_in(page, "Group")
    errors = _page_errors(page)
    page.add_init_script(
        """
        window.__ready = [];
        document.addEventListener('citry:ready', event => window.__ready.push(event.detail.appId));
        """
    )

    page.goto(serve_live(engine, _serialize(page_class, hydrate=hydrate), "") + "/")
    # The app removes itself from the runtime once it fails, so an empty app list is the stop signal.
    page.wait_for_function("window.__citryRuntime && window.__citryRuntime._apps.size === 0 && window.__order")
    page.wait_for_timeout(100)

    # Alpha and Leaf run before Group, which throws. Filled, Card, the rows and the page come
    # later in the order, so none of them ran.
    assert page.evaluate("window.__order") == ["Alpha", "Leaf", "Group"]
    assert page.evaluate("window.__ready") == []
    assert any("Group failed on purpose" in error for error in errors), errors


@pytest.mark.e2e
def test_throwing_callback_after_a_server_render_stops_later_callbacks_and_the_app(
    page: Any, serve_live: Any, wait_for_citry_ready: Any
) -> None:
    # `Late` mounts only after the server render, so the first mount runs without a failure.
    engine, page_class = _build_page()
    _fail_in(page, "Late")
    errors = _page_errors(page)
    page.goto(serve_live(engine, _serialize(page_class, hydrate=False), "") + "/")
    wait_for_citry_ready()
    assert page.evaluate("window.__order") == _FIRST_MOUNT_ORDER
    page.evaluate("window.__order = []")

    page.locator("#grow").click()
    # The failed render removes the app from the runtime. That is the stop signal, because the
    # event never finishes, so `citry:events:after` does not fire.
    page.wait_for_function("window.__citryRuntime._apps.size === 0")

    # Everything before `Late` ran, `Late` threw, and the page's own callback never ran.
    assert page.evaluate("window.__order") == [*_FIRST_MOUNT_ORDER[:-1], "Late"]
    # Firefox prints an Error argument of `console.error` as just "Error", so the check names
    # the runtime's own message. The order above shows which callback threw.
    assert any("a server render failed and the app has stopped" in error for error in errors), errors


def _build_toggle_page() -> tuple[Citry, type[Component]]:
    """
    Build a page whose browser-only `v-if` shows a `Spinner` or a `Bad` component.

    The page keeps its `v-if` flags as Vue data and exposes the component as `window.__page`, so a
    test or another component's callback can flip them. `Alpha` sits before the toggled
    component in the template, so its callback runs first and can remove the component that
    is still waiting for its own callback. `Alpha` does that when the revision it runs in equals
    `window.__removeAtRevision`.
    """
    engine = Citry(secret="callback-toggle-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Alpha(Component):
        citry = engine
        template = """
            <b>alpha</b>
        """
        js = """
            $component({
                onServerRender({revision}) {
                    if (window.__removeAtRevision === revision) window.__page.shown = false;
                },
            });
        """

    class Spinner(Component):
        citry = engine
        template = """
            <s>spinner</s>
        """
        # A callback that starts a timer must hand back the function that stops it, and Citry calls
        # that function when the component goes away.
        js = """
            $component({
                onServerRender() {
                    const stats = (window.__spinner ||= {started: 0, cleaned: 0, ticks: 0});
                    stats.started++;
                    const timer = setInterval(() => { stats.ticks++; }, 10);
                    return () => {
                        stats.cleaned++;
                        clearInterval(timer);
                    };
                },
            });
        """

    class Bad(Component):
        citry = engine
        template = """
            <u>bad</u>
        """
        js = """
            $component({
                onServerRender() {
                    (window.__order ||= []).push('Bad');
                    throw new Error('Bad failed on purpose');
                },
            });
        """

    class Page(Component):
        citry = engine

        class Events:
            def refresh(self) -> Any:
                return actions.Render(Page())

        template = """
            <main>
                <button
                    id="refresh"
                    @c-click="refresh"
                >refresh</button>
                <c-Alpha />
                <template v-if="shown"><c-Spinner /></template>
                <template v-if="badShown"><c-Bad /></template>
            </main>
        """
        js = """
            $component({
                data() { return {shown: true, badShown: false}; },
                mounted() { window.__page = this; },
            });
        """

    dispatcher_for(engine)
    return engine, Page


@pytest.mark.e2e
@pytest.mark.parametrize("hydrate", [True, False], ids=["hydrated", "client-rendered"])
def test_first_mount_skips_a_component_that_an_earlier_callback_removed(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, hydrate: bool
) -> None:
    engine, page_class = _build_toggle_page()
    errors = _page_errors(page)
    # Alpha runs before Spinner and takes it off the page, so Vue unmounts Spinner before its turn.
    page.add_init_script("window.__removeAtRevision = 0;")

    page.goto(serve_live(engine, _serialize(page_class, hydrate=hydrate), "") + "/")
    wait_for_citry_ready()
    # A timer that a skipped callback had started would keep counting; give it time to show.
    page.wait_for_timeout(150)

    assert page.locator("s").count() == 0
    # Spinner's callback never ran, so it started no timer and has nothing left to stop.
    assert page.evaluate("window.__spinner ?? null") is None
    assert errors == []


@pytest.mark.e2e
@pytest.mark.parametrize("hydrate", [True, False], ids=["hydrated", "client-rendered"])
def test_server_render_skips_a_component_that_an_earlier_callback_removed(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, send_event: Any, hydrate: bool
) -> None:
    engine, page_class = _build_toggle_page()
    errors = _page_errors(page)
    # Revision 0 is the first mount, which leaves Spinner in place. The server render is revision 1.
    page.add_init_script("window.__removeAtRevision = 1;")
    page.goto(serve_live(engine, _serialize(page_class, hydrate=hydrate), "") + "/")
    wait_for_citry_ready()
    assert page.evaluate("window.__spinner.started") == 1
    assert page.locator("s").count() == 1

    send_event(lambda: page.locator("#refresh").click())

    # The server render updated Spinner too, but Alpha's callback ran first and removed it. Citry
    # ran the timer's cleanup when the server render began, and Spinner's callback did not start
    # another timer.
    assert page.locator("s").count() == 0
    stats = page.evaluate("window.__spinner")
    assert (stats["started"], stats["cleaned"]) == (1, 1)
    ticks = stats["ticks"]
    page.wait_for_timeout(150)
    # The only timer was stopped, so the count has not moved.
    assert page.evaluate("window.__spinner.ticks") == ticks
    assert errors == []


@pytest.mark.e2e
def test_throwing_callback_of_a_component_shown_after_startup_stops_the_app_and_says_so(
    page: Any, serve_live: Any, wait_for_citry_ready: Any
) -> None:
    engine, page_class = _build_toggle_page()
    errors = _page_errors(page)
    page.goto(serve_live(engine, _serialize(page_class, hydrate=False), "") + "/")
    wait_for_citry_ready()
    assert errors == []

    # `Bad` mounts only now, after startup, so no start-up code waits on its callback.
    page.evaluate("window.__page.badShown = true")
    page.wait_for_function("window.__citryRuntime._apps.size === 0")

    assert page.evaluate("window.__order") == ["Bad"]
    # Firefox prints an Error argument of `console.error` as just "Error", so the check names the
    # message that comes first. The order above shows which callback threw.
    assert any("an onServerRender callback failed and the app has stopped" in error for error in errors), errors
