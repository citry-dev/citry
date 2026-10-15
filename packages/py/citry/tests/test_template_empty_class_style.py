"""
A `class` or `style` written empty in the template next to a value from Python.

The template parser reads `<p class>` and `<p class="">` as the boolean value
`True`, the same as any valueless attribute. The class and style merge
rejects `True` from Python data, so the renderer turns the written empty
attribute into an empty contribution before merging. These tests cover that
on pages with and without Vue, in `simple=True` and `simple="vue"`
components, and check that a `True` from Python still raises.

The rule they lock: when Python sets the same attribute (`c-class`,
`c-style`, or a `c-bind` key, even one that resolves to an empty value or
`None`), the written empty attribute adds nothing, so the element renders as
if only the Python value were there. When nothing from Python sets it, the
element keeps the empty attribute the template wrote.
"""

from __future__ import annotations

import re

import pytest

from citry import Citry, Component, merge_attrs
from citry.attrs import TEMPLATE_EMPTY_VALUE, format_attrs, template_attr_value


def _strip_cid(html: str) -> str:
    return re.sub(r' data-cid-[^=]+=""', "", html)


def _vue_host(html: str) -> str:
    """Return the HTML the server wrote inside the Vue host."""
    match = re.search(r'<div id="citry-vue-[^"]+">(.*?)</div><script', html, re.DOTALL)
    assert match is not None, html[:500]
    return match.group(1)


PAGE_TEMPLATE = """
  <main>
    <p class c-class="cls">a</p>
    <p class="" c-class="cls">b</p>
    <p style c-style="sty">c</p>
    <p style="" c-style="sty">d</p>
    <p class="" style="" c-bind="attrs">e</p>
    <i c-for="i in [1, 2]" class="" c-class="cls">{{ i }}</i>
    <c-element is="section" class="" c-class="cls">f</c-element>
    <p class="" c-class="empty">g</p>
    <p style="" c-style="empty">h</p>
    <p class="" c-class="none">i</p>
    <p class style="" c-title="cls">j</p>
    <p class="" c-bind="{'title': 't'}">k</p>
    {button}
  </main>
"""


def _page(*, interactive: bool) -> type[Component]:
    engine = Citry(autodiscover=False)
    # A Vue listener makes the page interactive, so the same elements go
    # through the Vue render.
    button = '<button @click="n += 1">{{ n }}</button>' if interactive else ""

    class Card(Component):
        citry = engine
        template = PAGE_TEMPLATE.replace("{button}", button)

        def template_data(self, kwargs, slots) -> dict[str, object]:
            return {
                "cls": "on",
                "sty": {"color": "red"},
                "attrs": {"class": "x", "style": "top: 0"},
                "empty": "",
                "none": None,
                "n": 0,
            }

    return Card


def test_written_empty_class_and_style_merge_with_python_values_on_a_static_page() -> None:
    html = _strip_cid(str(_page(interactive=False)()))

    # The written empty attribute adds nothing to a Python value.
    assert '<p class="on">a</p>' in html
    assert '<p class="on">b</p>' in html
    assert '<p style="color: red;">c</p>' in html
    assert '<p style="color: red;">d</p>' in html
    assert '<p class="x" style="top: 0;">e</p>' in html
    assert '<i class="on">1</i><i class="on">2</i>' in html
    assert '<section class="on">f</section>' in html
    # An empty Python value leaves the attribute out, as it does alone.
    assert "<p>g</p>" in html
    assert "<p>h</p>" in html
    assert "<p>i</p>" in html
    # With no Python value for it, the attribute renders as written.
    assert '<p class style="" title="on">j</p>' in html
    assert '<p class="" title="t">k</p>' in html


def test_written_empty_class_and_style_merge_with_python_values_on_a_vue_page() -> None:
    host = _vue_host(str(_page(interactive=True)()))

    assert host == (
        '<main><p class="on">a</p><p class="on">b</p><p style="color: red;">c</p>'
        '<p style="color: red;">d</p><p class="x" style="top: 0;">e</p>'
        '<!--[--><i class="on">1</i><i class="on">2</i><!--]--><section class="on">f</section>'
        '<p>g</p><p>h</p><p>i</p><p class="" style="" title="on">j</p><p class="" title="t">k</p>'
        "<button>0</button></main>"
    )


def test_written_empty_class_and_style_join_a_vue_class_and_style_binding() -> None:
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
          <main>
            <p
              class=""
              c-class="cls"
              :class="{ open: on }"
              style
              :style="{ color: tone }"
            >x</p>
          </main>
        """

        def template_data(self, kwargs, slots) -> dict[str, object]:
            return {"cls": "card"}

        def js_data(self, kwargs, slots) -> dict[str, object]:
            return {"on": True, "tone": "red"}

    assert _vue_host(str(Card())) == '<main><p class="card open" style="color:red;">x</p></main>'


def test_written_empty_class_and_style_in_a_simple_component() -> None:
    engine = Citry(autodiscover=False)

    class Tag(Component):
        citry = engine
        simple = True
        template = """
          <p
            class=""
            c-class="cls"
            style
            c-style="sty"
          >a</p>
          <p
            class
            style=""
            c-bind="attrs"
          >b</p>
          <i c-for="n in [1, 2]" class c-class="cls">{{ n }}</i>
          <p class c-title="cls">c</p>
        """

    html = Tag(cls="on", sty={"color": "red"}, attrs={"class": "x", "style": "top: 0"}).render()

    # Only the elements matter here, not the template's indentation.
    assert re.sub(r">\s+<", "><", _strip_cid(html.serialize(deps_strategy="ignore"))).strip() == (
        '<p class="on" style="color: red;">a</p><p class="x" style="top: 0;">b</p>'
        '<i class="on">1</i><i class="on">2</i><p class title="on">c</p>'
    )


def test_written_empty_class_and_style_beside_a_spread_in_simple_vue_rows() -> None:
    engine = Citry(autodiscover=False)

    class Row(Component):
        citry = engine
        simple = "vue"
        template = """
          <article class="" style c-bind="attrs">row</article>
        """

    class Board(Component):
        citry = engine
        template = """
          <section>
            <c-Row
              c-for="row in rows"
              #c-key="row['key']"
              c-attrs="row['attrs']"
            />
            <button @click="n += 1">{{ n }}</button>
          </section>
        """

        def template_data(self, kwargs, slots) -> dict[str, object]:
            spreads = [
                {"class": "x", "style": "top: 0"},
                {"title": "t"},
                {"class": "", "style": ""},
                {"class": None},
            ]
            return {"rows": [{"key": i, "attrs": attrs} for i, attrs in enumerate(spreads)], "n": 0}

    assert _vue_host(Board().render().serialize()) == (
        '<section><!--[--><article class="x" style="top: 0;">row</article>'
        '<article class="" style="" title="t">row</article><article>row</article>'
        '<article style="">row</article><!--]--><button>0</button></section>'
    )


@pytest.mark.parametrize("interactive", [False, True], ids=["static", "interactive"])
@pytest.mark.parametrize(
    ("element", "message"),
    [
        ('<p class="" c-class="flag">x</p>', "Invalid class value: True"),
        ('<p style c-style="flag">x</p>', "Invalid style value: True"),
        ("<p class c-bind=\"{'class': flag}\">x</p>", "Invalid class value: True"),
        ('<p c-class="flag">x</p>', "Invalid class value: True"),
    ],
    ids=["c-class", "c-style", "c-bind", "c-class-alone"],
)
def test_true_from_python_data_still_raises(element: str, message: str, interactive: bool) -> None:
    engine = Citry(autodiscover=False)
    button = '<button @click="n += 1">{{ n }}</button>' if interactive else ""

    class Card(Component):
        citry = engine
        template = f"<main>{element}{button}</main>"

        def template_data(self, kwargs, slots) -> dict[str, object]:
            return {"flag": True, "n": 0}

    with pytest.raises(TypeError, match=message):
        str(Card())


def test_only_a_written_empty_class_or_style_becomes_the_marker() -> None:
    assert template_attr_value("class", value=True) is TEMPLATE_EMPTY_VALUE
    assert template_attr_value("STYLE", value=True) is TEMPLATE_EMPTY_VALUE
    # Other boolean attributes and written text keep their value.
    assert template_attr_value("disabled", value=True) is True
    assert template_attr_value("class", "btn") == "btn"


def test_the_marker_renders_as_written_only_when_nothing_else_sets_the_attribute() -> None:
    assert format_attrs(merge_attrs({"class": TEMPLATE_EMPTY_VALUE, "id": "x"})) == 'class id="x"'
    assert format_attrs(merge_attrs({"class": TEMPLATE_EMPTY_VALUE}, {"class": "on"})) == 'class="on"'
    assert format_attrs(merge_attrs({"style": TEMPLATE_EMPTY_VALUE}, {"style": None})) == ""
    assert format_attrs(merge_attrs({"style": TEMPLATE_EMPTY_VALUE}, {"style": ""})) == ""
