"""
Components render at the nesting limits, and fail cleanly one level past them.

A template may nest 512 tags of any kind and 256 of Citry's logic levels.
At each limit a component renders on both render paths, with and without
Vue, and ``citry check`` finds nothing wrong with its depth. One level more is a ``SyntaxError``, and
``citry check`` reports it with the ``citry.parse.too-deep`` code. A template
far deeper, 100,000 levels, also fails cleanly: it runs in a subprocess, so
a crash would fail the test instead of ending the pytest run.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component
from citry._app_selection import CheckAppSelection
from citry._checker import check_project
from citry_core import _rust

if TYPE_CHECKING:
    from pathlib import Path

MAX_TAG_NESTING = _rust.template_parser._MAX_TAG_NESTING
MAX_LOGIC_NESTING = _rust.template_parser._MAX_LOGIC_NESTING

# Each template nests exactly to one limit; the second one goes one level
# past it. Every shape puts `{{ n }}` ("deepest") innermost, or a <c-Row>
# that renders "row", so a render that drops a level shows in the output.
AT_LIMITS: dict[str, tuple[str, str]] = {
    "elements": (
        "<div>" * MAX_TAG_NESTING + "{{ n }}" + "</div>" * MAX_TAG_NESTING,
        "<div>" * (MAX_TAG_NESTING + 1) + "{{ n }}" + "</div>" * (MAX_TAG_NESTING + 1),
    ),
    "if_tags_around_a_component": (
        '<c-if cond="flag">' * (MAX_LOGIC_NESTING - 1) + "<c-Row />" + "</c-if>" * (MAX_LOGIC_NESTING - 1),
        '<c-if cond="flag">' * MAX_LOGIC_NESTING + "<c-Row />" + "</c-if>" * MAX_LOGIC_NESTING,
    ),
    # Each step is one logic level and one plain element, so this sits at
    # both limits at once, and the validators that look at `#c-ignore`
    # elements see the full depth.
    "ignored_elements_inside_if_tags": (
        '<c-if cond="flag"><div #c-ignore>' * MAX_LOGIC_NESTING + "{{ n }}" + "</div></c-if>" * MAX_LOGIC_NESTING,
        '<c-if cond="flag"><div #c-ignore>' * MAX_LOGIC_NESTING
        + "<b>{{ n }}</b>"
        + "</div></c-if>" * MAX_LOGIC_NESTING,
    ),
    # Each step is a component and its fill: two logic levels.
    "fills_inside_components": (
        '<c-Box><c-fill name="default">' * (MAX_LOGIC_NESTING // 2)
        + "{{ n }}"
        + "</c-fill></c-Box>" * (MAX_LOGIC_NESTING // 2),
        '<c-Box><c-fill name="default">' * (MAX_LOGIC_NESTING // 2)
        + "<c-Box>{{ n }}</c-Box>"
        + "</c-fill></c-Box>" * (MAX_LOGIC_NESTING // 2),
    ),
}


# The tag each shape renders once per level, and how many it renders.
RENDERED_LEVELS: dict[str, tuple[str, int]] = {
    "elements": ("<div", MAX_TAG_NESTING),
    "if_tags_around_a_component": ("row</li>", 1),
    "ignored_elements_inside_if_tags": ("<div", MAX_LOGIC_NESTING),
    "fills_inside_components": ("<section", MAX_LOGIC_NESTING // 2),
}


def _app_with(template: str, *, uses_vue: bool = False) -> tuple[Citry, type[Component]]:
    app = Citry()

    class Row(Component):
        citry = app
        template = """
            <li>row</li>
        """

    class Box(Component):
        citry = app
        template = """
            <section><c-slot /></section>
        """

    class Root(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"flag": True, "n": "deepest"}

    del Row, Box
    Root.template = template
    if uses_vue:
        # A component with `js` also renders through its prepared template,
        # and serializing the page with its dependencies runs the Vue
        # compiler on it.
        Root.js = """
            $component({});
        """
    return app, Root


@pytest.mark.parametrize("uses_vue", [False, True], ids=["html", "vue"])
@pytest.mark.parametrize("shape", AT_LIMITS)
def test_a_template_at_the_limit_renders_and_one_level_more_fails(
    shape: str, uses_vue: bool, render_path: str
) -> None:
    at_limit, past_limit = AT_LIMITS[shape]
    _, root = _app_with(at_limit, uses_vue=uses_vue)
    html = root().render().serialize() if uses_vue else root().render().serialize(deps_strategy="ignore")
    # With Vue, the server HTML leaves elements nested deeper than 400 for
    # Vue to build in the browser, so the innermost value may be only in the
    # data the page sends Vue. Either way it must reach the page.
    assert ("row" in html) if "c-Row" in at_limit else ("deepest" in html)
    if not uses_vue:
        # Without Vue the server writes every level, so each must be there.
        tag, count = RENDERED_LEVELS[shape]
        assert html.count(tag) == count
    _, deeper = _app_with(past_limit, uses_vue=uses_vue)
    with pytest.raises(SyntaxError, match="levels deep"):
        deeper().render()


def test_a_simple_vue_component_renders_at_the_limit(render_path: str) -> None:
    # A `simple='vue'` component renders through its prepared template only.
    # Each `<div c-if>` is two levels, one of them logic: both limits.
    app = Citry()

    class Leaf(Component):
        citry = app
        simple = "vue"

    Leaf.template = '<div c-if="flag">' * MAX_LOGIC_NESTING + "{{ n }}" + "</div>" * MAX_LOGIC_NESTING

    class Root(Component):
        citry = app
        template = """
            <c-Leaf c-flag="flag" c-n="n" />
        """

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"flag": True, "n": 7}

    del Leaf
    html = Root().render().serialize(deps_strategy="ignore")
    assert html.count("<div") == MAX_LOGIC_NESTING
    assert ">7<" in html


def test_a_component_rendered_in_a_loop_can_nest_to_the_limit(render_path: str) -> None:
    # The native path renders a component once per row of a `c-for`; the
    # component's own template starts again at depth zero.
    app = Citry()

    class Row(Component):
        citry = app

    Row.template = '<c-if cond="True">' * MAX_LOGIC_NESTING + "<li>row</li>" + "</c-if>" * MAX_LOGIC_NESTING

    class Root(Component):
        citry = app
        template = """
            <ul><c-Row c-for="i in items" /></ul>
        """

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"items": [1, 2, 3]}

    del Row
    html = Root().render().serialize(deps_strategy="ignore")
    assert html.count(">row</li>") == 3


# `citry check` reads the tree through the binding, which copies a node's
# whole subtree each time Python reads its body, so its cost grows with
# the cube of the depth. The two shapes that cost the most are left out
# here to keep the suite fast; the parser counts them the same way.
CHECKED_SHAPES = ("elements", "fills_inside_components")


@pytest.mark.parametrize("shape", CHECKED_SHAPES)
def test_check_reports_too_deep_only_past_the_limit(shape: str, tmp_path: Path) -> None:
    at_limit, past_limit = AT_LIMITS[shape]
    for template, expect_too_deep in ((at_limit, False), (past_limit, True)):
        engine = Citry(autodiscover=False)
        type("Page", (Component,), {"citry": engine, "template": template, "__module__": __name__})
        report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
        codes = [finding.code for finding in report.findings]
        assert ("citry.parse.too-deep" in codes) is expect_too_deep, codes


@pytest.mark.parametrize(
    "template_code",
    [
        "'<c-if cond=\"flag\">' * 100_000 + 'x' + '</c-if>' * 100_000",
        "'<div>' * 100_000 + 'x' + '</div>' * 100_000",
        "'<div><c-if cond=\"flag\">' * 50_000 + 'x' + '</c-if></div>' * 50_000",
    ],
    ids=["if_tags", "elements", "mixed"],
)
def test_a_template_100_000_levels_deep_fails_cleanly(template_code: str) -> None:
    code = f"""
        from citry import Citry, Component

        app = Citry()

        class Root(Component):
            citry = app

        Root.template = {template_code}
        try:
            Root().render()
        except SyntaxError as error:
            print("SyntaxError", "levels deep" in str(error))
    """
    # The code goes in on stdin: a Windows command line could not hold it.
    result = subprocess.run(
        [sys.executable, "-"],
        input=textwrap.dedent(code),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.split() == ["SyntaxError", "True"]
