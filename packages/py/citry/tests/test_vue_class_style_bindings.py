"""
A Vue `:class` or `:style` binding on an element that also has a class or style from the template or from Python.

Vue joins a bound class with every other class on the element and combines a
bound style with every other style. The server writes the element the way
Vue's first render leaves it: with every class and style it can compute, and,
when part of the value is only known in the browser, with the parts it does
know, so the element is styled before Vue runs. A `c-class` or `c-style`
joins the binding the same way a static `class` or `style` does. These tests
also cover a `:key` on a `v-for` item that carries a runtime directive, whose
value Citry keeps beside its own element key.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component
from citry._app_selection import CheckAppSelection
from citry._checker import check_project
from citry._vue.serialization import hydration_admission

if TYPE_CHECKING:
    from pathlib import Path


def _hydrated(page: type[Component]) -> tuple[str, list[tuple[str, str, str | None]]]:
    """Render one page and return the Vue host's server HTML and the reasons it wrote shells."""
    rendered = page().render()
    html = rendered.serialize()
    assert '"hydrate":true' in html
    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.hydrated
    match = re.search(r'<div id="citry-vue-[^"]+">(.*?)</div><script', html, re.DOTALL)
    assert match is not None, html[:500]
    return match.group(1), [(item.code, item.detail, item.shell_tag) for item in admission.declines]


def test_static_class_and_style_merge_with_bindings_the_server_can_read() -> None:
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
          <main>
            <p
              class="card"
              :class="{ 'card--done': done, 'card--late': late }"
              style="color: red"
              :style="{ fontWeight: weight }"
            >x</p>
          </main>
        """

        def js_data(self, kwargs, slots) -> dict[str, object]:
            return {"done": True, "late": False, "weight": "bold"}

    host, declines = _hydrated(Card)

    assert host == '<main><p class="card card--done" style="color:red;font-weight:bold;">x</p></main>'
    assert declines == []


def test_browser_only_binding_keeps_the_known_class_and_style_in_the_shell() -> None:
    engine = Citry(autodiscover=False)

    # `dragging` comes from `data()`, which only the browser runs, so Vue
    # builds the element; the shell's HTML still shows the static parts.
    class Card(Component):
        citry = engine
        template = """
          <main>
            <p
              class="card"
              :class="{ 'card--dragging': dragging }"
              style="color: red"
              :style="{ opacity: dragging ? 0.5 : 1 }"
            >x</p>
          </main>
        """
        js = """
          $component({ data() { return { dragging: false }; } });
        """

    host, declines = _hydrated(Card)

    assert host == '<main data-allow-mismatch="children"><p class="card" style="color:red;">x</p></main>'
    assert declines == [("browser-value", "class", "main")]


def test_python_class_and_style_merge_with_bindings_like_static_ones() -> None:
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
          <main>
            <p
              class="card"
              c-class="{'card--done': done}"
              :class="{ 'card--open': open }"
              c-style="'color: red; font-weight: normal'"
              :style="{ fontWeight: weight }"
            >x</p>
            <span
              c-bind="attrs"
              :class="tone"
              :style="{ color: 'green' }"
            >y</span>
          </main>
        """

        def template_data(self, kwargs, slots) -> dict[str, object]:
            return {"done": True, "attrs": {"class": "badge", "style": "color: blue", "title": "t"}}

        def js_data(self, kwargs, slots) -> dict[str, object]:
            return {"open": True, "weight": "bold", "tone": "badge--info"}

    host, declines = _hydrated(Card)

    # Python's classes come first, as a static class does, and the bound
    # style is applied after Python's, so the Vue binding wins for a
    # property both set.
    assert host == (
        "<main>"
        '<p class="card card--done card--open" style="color:red;font-weight:normal;font-weight:bold;">x</p>'
        '<span class="badge badge--info" style="color:green;" title="t">y</span>'
        "</main>"
    )
    assert declines == []


def test_a_modified_class_binding_next_to_c_class_is_rejected_when_the_template_loads() -> None:
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
          <p c-class="'card'" :class.prop="extra">x</p>
        """

    with pytest.raises(SyntaxError, match="Remove the modifier and write ':class'"):
        Card().render()


def test_citry_check_reports_a_binding_that_competes_with_a_python_value(tmp_path: Path) -> None:
    engine = Citry(autodiscover=False)
    type(
        "Page",
        (Component,),
        {
            "citry": engine,
            "template": """<p c-title="label" :title="hint" c-class="'a'" :class="b">x</p>""",
            "__module__": __name__,
        },
    )

    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)

    assert [finding.code for finding in report.findings] == ["citry.parse.syntax"]
    assert "':title' on <p>" in report.findings[0].message
    assert "sets the same attribute as 'c-title'" in report.findings[0].message


def test_v_for_key_is_kept_beside_the_element_key_of_a_runtime_directive() -> None:
    engine = Citry(autodiscover=False)

    class List(Component):
        citry = engine
        template = """
          <ul>
            <li
              v-for="item in items"
              :key="item.id"
              class="item"
              v-show="item.shown"
            >{{ 1 }}</li>
          </ul>
        """

        def js_data(self, kwargs, slots) -> dict[str, object]:
            return {"items": [{"id": 1, "shown": True}, {"id": 2, "shown": False}]}

    html = List().render().serialize()

    # The item key and the directive digest together tell the items apart.
    assert re.search(r"key: JSON\.stringify\(\['citryReplacement[0-9a-f]{64}', \(item\.id\)\]\)", html)

    # Without a runtime directive the authored key is used as it is.
    class Plain(Component):
        citry = engine
        template = """
          <ul>
            <li
              v-for="item in items"
              :key="item.id"
              v-text="item.label"
            ></li>
          </ul>
        """

        def js_data(self, kwargs, slots) -> dict[str, object]:
            return {"items": [{"id": 1, "label": "a"}]}

    assert "key: item.id" in Plain().render().serialize()


def test_simple_vue_rows_keep_their_static_class_beside_a_browser_only_binding() -> None:
    engine = Citry(autodiscover=False)

    class Row(Component):
        citry = engine
        simple = "vue"
        template = """
          <article
            class="row"
            :class="{ 'row--open': open }"
          >x</article>
        """
        js = """
          $component({ data() { return { open: false }; } });
        """

    class Board(Component):
        citry = engine
        template = """
          <section>
            <c-Row c-for="n in [1, 2]" #c-key="n" />
          </section>
        """

    host, declines = _hydrated(Board)

    assert host == (
        '<section data-allow-mismatch="children"><article class="row">x</article>'
        '<article class="row">x</article></section>'
    )
    assert declines == [("browser-value", "class", "section")]


@pytest.mark.parametrize("binding", ['.title="hint"', '^title="hint"', ':class.prop="hint"'])
def test_a_c_bind_key_and_a_modified_binding_for_one_attribute_stop_the_render(binding: str) -> None:
    engine = Citry(autodiscover=False)

    # A `c-bind` key is only known while rendering, so the render refuses
    # the pair that the template loader cannot see.
    class Card(Component):
        citry = engine
        template = f"""
          <p c-bind="attrs" {binding}>x</p>
        """

        def template_data(self, kwargs, slots) -> dict[str, object]:
            return {"attrs": {"title": "t", "class": "c"}}

        def js_data(self, kwargs, slots) -> dict[str, object]:
            return {"hint": "h"}

    with pytest.raises(Exception, match="target the same HTML name"):
        Card().render().serialize()


# Values that leave no class or style once Citry reads them: a style string
# without a `property: value` pair, an empty string, an empty mapping, or a
# mapping whose entries are all turned off.
EMPTY_CLASS_AND_STYLE = pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("c-style", "color"),
        ("c-style", ""),
        ("c-style", {}),
        ("c-style", {"color": None}),
        ("c-class", ""),
        ("c-class", {"open": False}),
    ],
    ids=["style-unparsed", "style-empty", "style-dict", "style-none-value", "class-empty", "class-false"],
)


@EMPTY_CLASS_AND_STYLE
@pytest.mark.parametrize("interactive", [False, True], ids=["static", "interactive"])
def test_an_empty_c_class_or_c_style_is_left_out_on_static_and_interactive_pages(
    attribute: str,
    value: object,
    interactive: bool,
) -> None:
    engine = Citry(autodiscover=False)
    # A Vue listener makes the page interactive; the attribute under test
    # sits on its own element beside it, and inside a loop.
    button = '<button @click="n += 1">{{ n }}</button>' if interactive else ""

    class Card(Component):
        citry = engine
        template = f"""
          <main>
            <p {attribute}="value">x</p>
            <i c-for="i in [1, 2]" {attribute}="value">{{{{ i }}}}</i>
            <span c-bind="{{'{attribute.removeprefix("c-")}': value, 'title': 't'}}">y</span>
            {button}
          </main>
        """

        def template_data(self, kwargs, slots) -> dict[str, object]:
            return {"value": value, "n": 0}

    html = str(Card())

    assert "<p>x</p>" in html
    assert "<i>1</i><i>2</i>" in html
    assert '<span title="t">y</span>' in html
    assert 'class=""' not in html
    assert 'style=""' not in html


@EMPTY_CLASS_AND_STYLE
def test_an_empty_c_class_or_c_style_is_left_out_of_the_hydrated_html(attribute: str, value: object) -> None:
    engine = Citry(autodiscover=False)

    # The server writes the hydrated HTML the way Vue renders the same data,
    # so the attribute is absent there too, not written as `style=""`.
    class Card(Component):
        citry = engine
        template = f"""
          <main>
            <p {attribute}="value">x</p>
            <button @click="n += 1">{{{{ n }}}}</button>
          </main>
        """

        def template_data(self, kwargs, slots) -> dict[str, object]:
            return {"value": value, "n": 0}

    host, declines = _hydrated(Card)

    assert host == "<main><p>x</p><button>0</button></main>"
    assert declines == []
