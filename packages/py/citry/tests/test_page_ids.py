"""
The development check that warns about an ``id`` repeated across one page.

The ``citry.template.duplicate-id`` rule covers one template. This check runs
when a page is serialized with ``Citry(mode="development")`` and sees the
whole page: the same id from two components, or from one component rendered
twice.
"""

import warnings
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.serialization import hydration_admission


def _serialize_warnings(page: Component) -> list[str]:
    """Serialize one page and return the messages of the duplicate-id warnings it raised."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        page.render().serialize()
    return [str(item.message) for item in caught if "used by more than one element on one page" in str(item.message)]


def _page(engine: Citry, body: str, *, interactive: bool = False) -> type[Component]:
    """A document page around ``body``; an interactive one hydrates in Vue."""

    class Board(Component):
        citry = engine
        template = """
<section id="board">
  <h2>Board</h2>
</section>
"""

    class Sidebar(Component):
        citry = engine
        template = """
<aside id="board">Sidebar</aside>
"""

    class Card(Component):
        citry = engine
        template = """
<article id="card">{{ title }}</article>
"""

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"title": kwargs.get("title")}

    class Page(Component):
        citry = engine
        template = f"""
<!doctype html>
<html>
  <head><title>Page</title></head>
  <body><main>{body}</main></body>
</html>
"""
        js = (
            """
$component({data() { return {count: 0}; }});
"""
            if interactive
            else None
        )

    return Page


@pytest.mark.parametrize("interactive", [False, True])
def test_two_components_with_the_same_id_warn(interactive: bool) -> None:
    page = _page(Citry(autodiscover=False, mode="development"), "<c-Board /><c-Sidebar />", interactive=interactive)

    [message] = _serialize_warnings(page())

    assert '- id "board": Board (' in message
    assert ", Sidebar (" in message
    # Each component is named with the template it came from.
    assert "test_page_ids.py::Board" in message
    assert "Give each element its own id" in message


def test_one_component_rendered_twice_with_a_literal_id_warns() -> None:
    page = _page(Citry(autodiscover=False, mode="development"), '<c-Card title="One" /><c-Card title="Two" />')

    [message] = _serialize_warnings(page())

    assert '- id "card": Card (2 elements, ' in message


def test_a_repeat_from_a_loop_warns() -> None:
    page = _page(
        Citry(autodiscover=False, mode="development"),
        '<c-for each="title in titles"><c-Card c-title="title" /></c-for>',
    )

    class Loop(page):  # type: ignore[valid-type,misc]
        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"titles": ["One", "Two", "Three"]}

    [message] = _serialize_warnings(Loop())

    assert '- id "card": Card (3 elements, ' in message


def test_unique_ids_do_not_warn() -> None:
    page = _page(Citry(autodiscover=False, mode="development"), '<c-Board /><c-Card title="One" />')

    assert _serialize_warnings(page()) == []


def test_production_mode_does_not_check() -> None:
    page = _page(Citry(autodiscover=False), "<c-Board /><c-Sidebar />", interactive=True)

    assert _serialize_warnings(page()) == []


def test_two_separate_pages_are_checked_separately() -> None:
    engine = Citry(autodiscover=False, mode="development")
    page = _page(engine, "<c-Board />")

    # Each serialization is its own page, so one id per page is fine.
    assert _serialize_warnings(page()) == []
    assert _serialize_warnings(page()) == []


def test_ids_the_browser_decides_or_never_shows_are_not_counted() -> None:
    engine = Citry(autodiscover=False, mode="development")
    # A <template>'s contents stay out of the document, and Vue decides in
    # the browser whether a v-if element exists or how often a v-for repeats.
    page = _page(
        engine,
        """
<c-Board />
<template><p id="board">Inert</p></template>
<p
  v-if="count"
  id="board"
>Shown later</p>
<ul><li
  v-for="item in []"
  id="board"
></li></ul>
""",
        interactive=True,
    )

    assert _serialize_warnings(page()) == []


def test_only_the_rendered_branch_of_a_server_condition_counts() -> None:
    engine = Citry(autodiscover=False, mode="development")
    page = _page(
        engine,
        """
<c-Board />
<c-if cond="False"><p id="board">Never rendered</p></c-if>
""",
    )

    assert _serialize_warnings(page()) == []


def test_raw_html_counts_because_the_browser_shows_it() -> None:
    engine = Citry(autodiscover=False, mode="development")
    page = _page(engine, '<c-Board /><c-raw><div id="board">Raw</div></c-raw>')

    [message] = _serialize_warnings(page())

    assert '- id "board": Board (' in message
    assert ", Page (" in message


@pytest.mark.parametrize(
    "branches",
    [
        '<div v-if="count"><c-Board /></div><div v-else><c-Board /></div>',
        '<template v-if="count"><c-Board /></template><template v-else><c-Board /></template>',
    ],
)
def test_a_component_in_both_branches_of_a_vue_condition_does_not_warn(branches: str) -> None:
    # The browser shows only one branch, so the component's id appears once.
    page = _page(Citry(autodiscover=False, mode="development"), branches, interactive=True)

    assert _serialize_warnings(page()) == []


def test_noscript_contents_are_not_counted() -> None:
    # A browser that runs scripts reads <noscript> as text.
    page = _page(
        Citry(autodiscover=False, mode="development"),
        '<c-Board /><noscript><p id="board">Turn on JavaScript</p></noscript>',
    )

    assert _serialize_warnings(page()) == []


def test_a_page_served_without_server_html_still_warns() -> None:
    # Vue mounts this page in the browser, so its body's HTML is not sent,
    # but the ids it would write still repeat.
    page = _page(Citry(autodiscover=False, mode="development"), "<c-Board /><c-Sidebar />", interactive=True)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        page().render().serialize(ssr=False)

    [message] = [str(item.message) for item in caught if "used by more than one element" in str(item.message)]
    assert '- id "board": Board (' in message


@pytest.mark.parametrize("simple", [True, "vue"])
def test_a_simple_component_rendered_twice_warns(simple: object) -> None:
    engine = Citry(autodiscover=False, mode="development")

    class Leaf(Component):
        citry = engine
        locals()["simple"] = simple
        template = """
<button
  id="open"
  type="button"
>Open</button>
"""

    page = _page(engine, "<c-Leaf /><c-Leaf />", interactive=True)

    [message] = _serialize_warnings(page())

    assert '- id "open": ' in message


def test_a_page_that_cannot_hydrate_counts_each_component_once() -> None:
    # Such a page serves HTML built from its whole body; the check must
    # count each component in it once.
    engine = Citry(autodiscover=False, mode="development")

    class Board(Component):
        citry = engine
        template = """
<section id="board">Board</section>
"""

    class Page(Component):
        citry = engine
        # A browser-only v-if right in <body> keeps Vue from adopting the page.
        template = """
<!doctype html>
<html>
  <head><title>Page</title></head>
  <body>
    <p v-if="count">Clicked</p>
    <c-Board />
  </body>
</html>
"""
        js = """
$component({data() { return {count: 0}; }});
"""

    rendered = Page().render()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rendered.serialize()

    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.server_html
    assert [item for item in caught if "used by more than one element" in str(item.message)] == []
