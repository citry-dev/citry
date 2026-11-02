"""
Tags inside ``v-pre`` render as written, as Vue renders them.

Vue's parser decides that a tag is a slot outlet, a component, or a built-in
such as ``<teleport>`` only outside ``v-pre``. Inside it, and on the element
that carries it, these stay plain elements, and ``<component>`` loses its
``is`` attribute. The template parser accepts Vue-only syntax there for the
same reason: it is plain text to Vue.
"""

import re

import pytest

from citry import Citry, Component
from citry_core.template_parser import parse_template


def _host(template: str) -> str:
    """Render a Vue page and return the Vue host's contents as the server writes them."""
    engine = Citry(autodiscover=False)
    page = type("Page", (Component,), {"citry": engine, "template": template, "js": "\n$component({});\n"})
    html = page().render().serialize()
    assert '"hydrate":true' in html
    match = re.search(r'<div id="citry-vue-[^"]+">(.*?)</div><script', html, re.DOTALL)
    assert match is not None, html[:500]
    return match.group(1)


@pytest.mark.parametrize(
    ("template", "host"),
    [
        # Vue writes a slot outlet inside `v-pre` as an element, fallback and all.
        (
            '<main><div v-pre><slot name="a">FALLBACK</slot></div></main>',
            '<main><div><slot name="a">FALLBACK</slot></div></main>',
        ),
        # The element that carries `v-pre` is plain too.
        (
            '<main><slot v-pre name="a">FALLBACK</slot></main>',
            '<main><slot name="a">FALLBACK</slot></main>',
        ),
        # A plain `<component>` has no `is` attribute in Vue's output.
        (
            '<main><div v-pre><component is="x">c</component></div></main>',
            "<main><div><component>c</component></div></main>",
        ),
        # The server writes the built-ins itself, with no part left for the
        # browser to build.
        (
            '<main><div v-pre><teleport to="body">t</teleport><transition>t</transition></div></main>',
            '<main><div><teleport to="body">t</teleport><transition>t</transition></div></main>',
        ),
    ],
)
def test_tags_inside_v_pre_are_written_as_plain_elements(template: str, host: str) -> None:
    rendered = _host(template)
    assert rendered == host
    assert "data-allow-mismatch" not in rendered


@pytest.mark.parametrize(
    ("template", "host"),
    [
        (
            "<main><div v-pre><keep-alive>k</keep-alive></div></main>",
            '<main><div data-allow-mismatch="children"></div></main>',
        ),
        # `v-pre` reaches the whole subtree.
        (
            "<main><div v-pre><section><keep-alive>k</keep-alive></section></div></main>",
            '<main><div><section data-allow-mismatch="children"></section></div></main>',
        ),
    ],
)
def test_a_custom_element_name_inside_v_pre_is_built_by_the_browser(template: str, host: str) -> None:
    # The server leaves a custom element such as <keep-alive> for the browser
    # to build, as it does for any custom element: a defined one may add its
    # own children before the page hydrates. The browser builds it as the
    # plain element Vue writes under `v-pre`.
    assert _host(template) == host


@pytest.mark.parametrize(
    "template",
    [
        '<main><slot v-pre name="a">{{ title }}</slot></main>',
        '<main><component v-pre is="x">{{ title }}</component></main>',
        "<main><Comp v-pre>{{ title }}</Comp></main>",
        '<main><teleport v-pre to="body">{{ title }}</teleport></main>',
    ],
)
def test_a_vue_typed_tag_carrying_v_pre_with_citry_values_is_refused(template: str) -> None:
    # Citry compiles a v-pre element that holds Citry values as live Vue,
    # where these tags would run as a slot, a component, or a built-in.
    with pytest.raises(TypeError, match="Put 'v-pre' on an element around it"):
        _page_with_title(template)().render().serialize()


def test_an_svg_element_carrying_v_pre_with_citry_values_renders() -> None:
    # SVG's camelCase names are native elements in Vue, not components.
    html = (
        _page_with_title('<main><svg><foreignObject v-pre width="1">{{ title }}</foreignObject></svg></main>')()
        .render()
        .serialize()
    )
    assert "T" in html


def _page_with_title(template: str) -> type[Component]:
    """Build a Vue page whose template reads a Citry value, ``title``."""
    engine = Citry(autodiscover=False)
    return type(
        "Page",
        (Component,),
        {
            "citry": engine,
            "template": template,
            "js": "$component({});",
            "template_data": lambda _self, _kwargs, _slots: {"title": "T"},
        },
    )


def test_a_transition_inside_v_pre_loads_and_renders() -> None:
    # Outside `v-pre` the template parser rejects `<transition>`.
    assert _host("<main><div v-pre><transition><p>a</p></transition></div></main>") == (
        "<main><div><transition><p>a</p></transition></div></main>"
    )


def test_v_once_inside_v_pre_renders_as_an_attribute() -> None:
    # Vue compiles nothing for `v-once` there, so Citry has no cached output
    # to refuse.
    assert _host("<main><div v-pre><p v-once>a</p></div></main>") == ('<main><div><p v-once="">a</p></div></main>')


@pytest.mark.parametrize(
    "template",
    [
        "<main><div v-pre><p v-once>a</p></div></main>",
        "<main><div v-pre><transition><p>a</p></transition></div></main>",
        '<main><div v-pre><button @click.bogus="x">a</button></div></main>',
    ],
)
def test_vue_only_syntax_inside_v_pre_loads(template: str) -> None:
    parse_template(template)


def test_a_slot_inside_v_pre_is_not_an_outlet_for_a_parent_fill() -> None:
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
<main><div v-pre><slot name="a">FALLBACK</slot></div></main>
"""
        js = """
$component({});
"""

    class Page(Component):
        citry = engine
        template = """
<c-Card><c-fill name="a">FILLED</c-fill></c-Card>
"""
        js = """
$component({});
"""

    html = Page().render().serialize()
    match = re.search(r'<div id="citry-vue-[^"]+">(.*?)</div><script', html, re.DOTALL)
    assert match is not None, html[:500]
    # Vue writes the tag as written, so the fill is not placed in it.
    assert match.group(1) == '<main><div><slot name="a">FALLBACK</slot></div></main>'
    assert "FILLED" not in html
