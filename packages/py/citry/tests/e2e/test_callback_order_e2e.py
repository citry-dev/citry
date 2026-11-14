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

# The callback that records its component's name. A repeated component reads its name from the
# element it rendered, since every instance shares one callback.
_RECORD_ROW = """
    $component({
        onServerRender({els}) {
            (window.__order ||= []).push('Row:' + els[0].textContent.trim());
        },
    });
"""


def _record(name: str, *, throws: bool = False) -> str:
    """Return the `js` of a component whose callback pushes `name`, then throws when `throws` is set."""
    # The push comes first so a throwing callback still shows that it ran.
    throw = f"throw new Error('{name} failed on purpose');" if throws else ""
    return f"""
        $component({{
            onServerRender() {{
                (window.__order ||= []).push('{name}');
                {throw}
            }},
        }});
    """


def _build_page(*, failing: str | None = None) -> tuple[Citry, type[Component]]:
    """Build the test page; the callback of the component named `failing` throws."""
    engine = Citry(secret="callback-order-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Leaf(Component):
        citry = engine
        template = """
            <i>leaf</i>
        """
        js = _record("Leaf", throws=failing == "Leaf")

    class Late(Component):
        citry = engine
        template = """
            <s>late</s>
        """
        js = _record("Late", throws=failing == "Late")

    class Group(Component):
        citry = engine
        template = """
            <section><c-Leaf /></section>
        """
        js = _record("Group", throws=failing == "Group")

    class Alpha(Component):
        citry = engine
        template = """
            <b>alpha</b>
        """
        js = _record("Alpha", throws=failing == "Alpha")

    class Card(Component):
        citry = engine
        template = """
            <article><c-slot name="default" /></article>
        """
        js = _record("Card", throws=failing == "Card")

    class Filled(Component):
        citry = engine
        template = """
            <u>filled</u>
        """
        js = _record("Filled", throws=failing == "Filled")

    class Row(Component):
        citry = engine

        class Kwargs:
            name: str

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"name": kwargs.name}

        template = """
            <li>{{ name }}</li>
        """
        js = _RECORD_ROW

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
        js = _record("Page", throws=failing == "Page")

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
@pytest.mark.parametrize("hydrate", [True, False], ids=["hydrated", "mounted"])
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
@pytest.mark.parametrize("hydrate", [True, False], ids=["hydrated", "mounted"])
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
@pytest.mark.parametrize("hydrate", [True, False], ids=["hydrated", "mounted"])
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
@pytest.mark.parametrize("hydrate", [True, False], ids=["hydrated", "mounted"])
def test_throwing_callback_on_first_mount_stops_later_callbacks_and_the_app(
    page: Any, serve_live: Any, hydrate: bool
) -> None:
    engine, page_class = _build_page(failing="Group")
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
    engine, page_class = _build_page(failing="Late")
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
