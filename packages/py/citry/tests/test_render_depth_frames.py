"""
Rendering a deeper template does not need more Python frames.

The body renderer, fill collection and the Vue leaf program walk nested
``<c-if>``, ``<c-for>`` and ``c-if=`` bodies, and the fallback bodies of
``<c-slot>`` tags nobody fills, on their own stacks, and the generated
leaf code stops at a fixed nesting depth. So the deepest Python call stack
during a render stays the same however deeply control flow and fallbacks
nest. Each case renders once to compile, then measures the second render
with a profile hook that records the deepest stack. The peak at depth 128
may be at most 20 frames above the peak at depth 32. A first render, which
also compiles the component and walks its template several times, is
measured the same way.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component, Const, Extension

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FrameType

# Both depths are past the 15 levels a Vue leaf program runs as generated
# code (one frame per level by design), so both use the same evaluator.
SHALLOW = 32
DEEP = 128
ALLOWED_GROWTH = 20


def _for_tags(depth: int) -> str:
    """Nested `<c-for>` tags that each bind their own name."""
    return "".join(f'<c-for each="x{level} in items">' for level in range(depth))


# Each shape builds a template nested `depth` levels deep. A shape that
# starts with `<c-Row />` renders through the body renderer; one without a
# component renders through a Vue leaf program.
SHAPES: dict[str, Callable[[int], str]] = {
    "if_tags": lambda d: "<c-Row />" + '<c-if cond="flag">' * d + "x" + "</c-if>" * d,
    "for_tags": lambda d: "<c-Row />" + _for_tags(d) + "x" + "</c-for>" * d,
    "if_attributes": lambda d: "<c-Row />" + '<div c-if="flag">' * d + "x" + "</div>" * d,
    "leaf_if_tags": lambda d: '<c-if cond="flag">' * d + "{{ n }}" + "</c-if>" * d,
    "leaf_for_tags": lambda d: _for_tags(d) + "{{ n }}" + "</c-for>" * d,
    "leaf_if_attributes": lambda d: '<p c-if="flag">' * d + "{{ n }}" + "</p>" * d,
    "components": lambda d: "<c-Row />" + "<c-Card>" * d + "{{ n }}" + "</c-Card>" * d,
    "simple_components": lambda d: "<c-Row />" + "<c-Label>" * d + "{{ n }}" + "</c-Label>" * d,
    # A `<c-slot>` nobody fills renders its own body, its fallback.
    "slot_fallbacks": lambda d: (
        "<c-Row />" + "".join(f'<c-slot name="s{level}">' for level in range(d)) + "{{ n }}" + "</c-slot>" * d
    ),
    # Each step is three logic levels (a component, a fill and a <c-if>), so
    # it takes half as many steps, to stay within the 256 logic levels a
    # template may nest.
    "fills_under_control_flow": lambda d: (
        "<c-Row />"
        + '<c-Card><c-fill name="default"><c-if cond="flag">' * (d // 2)
        + "{{ n }}"
        + "</c-if></c-fill></c-Card>" * (d // 2)
    ),
}


def _component(template: str) -> type[Component]:
    app = Citry()

    class Card(Component):
        citry = app
        template = "<section><c-slot /></section>"

    class Label(Component):
        citry = app
        simple = True
        template = "<span><c-slot /></span>"

    class Row(Component):
        citry = app
        template = "<li>r</li>"

    class Root(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"flag": True, "n": 1, "items": [1]}

    del Card, Label, Row
    Root.template = template
    return Root


def _peak_frames(root: type[Component], *, first_render: bool = False, count_generated: bool = True) -> int:
    """
    Return the deepest Python stack seen while rendering ``root``, a second time unless ``first_render``.

    With ``count_generated`` off, frames of code Citry generated at runtime
    (file names that start with ``<citry``) are left out of the count.
    """
    if not first_render:
        root().render().serialize(deps_strategy="ignore")
    peak = 0

    def profile(frame: FrameType, event: str, arg: object) -> None:
        nonlocal peak
        if event != "call":
            return
        depth = 0
        current: FrameType | None = frame
        while current is not None:
            if count_generated or not current.f_code.co_filename.startswith("<citry"):
                depth += 1
            current = current.f_back
        peak = max(peak, depth)

    sys.setprofile(profile)
    try:
        root().render().serialize(deps_strategy="ignore")
    finally:
        sys.setprofile(None)
    return peak


@pytest.mark.parametrize("shape", SHAPES)
def test_deeper_templates_render_in_the_same_python_stack(shape: str, render_path: str) -> None:
    build = SHAPES[shape]
    shallow = _peak_frames(_component(build(SHALLOW)))
    deep = _peak_frames(_component(build(DEEP)))
    assert deep - shallow <= ALLOWED_GROWTH, f"{shape}: {shallow} frames at depth {SHALLOW}, {deep} at {DEEP}"


@pytest.mark.parametrize("depth", [15, 16, 20])
def test_simple_vue_components_render_at_every_depth(depth: int, render_path: str) -> None:
    # A `simple='vue'` component renders without an instance, through the
    # generated evaluator only, so the generated code must exist at any depth.
    app = Citry()

    class Leaf(Component):
        citry = app
        simple = "vue"
        template = '<div c-if="flag">' * depth + "{{ n }}" + "</div>" * depth

    class Root(Component):
        citry = app
        template = '<c-Leaf c-flag="flag" c-n="n" />'

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"flag": True, "n": 7}

    del Leaf
    html = Root().render().serialize(deps_strategy="ignore")
    assert html.count("<div") == depth
    assert ">7<" in html


@pytest.mark.parametrize("shape", SHAPES)
def test_deeper_templates_render_the_first_time_in_the_same_python_stack(
    shape: str,
    render_path: str,
) -> None:
    # A component's first render also runs the precompute pass, the i18n and
    # events transforms (both on by default) and the Vue leaf compiler; each
    # of those walks the whole template.
    _peak_frames(_component(SHAPES["if_tags"](2)), first_render=True)
    build = SHAPES[shape]
    shallow = _peak_frames(_component(build(SHALLOW)), first_render=True)
    deep = _peak_frames(_component(build(DEEP)), first_render=True)
    assert deep - shallow <= ALLOWED_GROWTH, f"{shape}: {shallow} frames at depth {SHALLOW}, {deep} at {DEEP}"


def _chained_loops(depth: int) -> str:
    """Nested `<c-for>` tags where each loop reads the one around it."""
    opens = '<c-for each="x0 in items">' + "".join(
        f"<c-for each=\"x{level} in x{level - 1}['c']\">" for level in range(1, depth)
    )
    return opens + "{{ n }}" + "</c-for>" * depth


def _chained_items(depth: int) -> list[Any]:
    """Data for `_chained_loops`: one row per level, each holding the next level's rows."""
    rows: list[Any] = [{"c": []}]
    for _ in range(depth - 1):
        rows = [{"c": rows}]
    return rows


def _first_render_root(template: str, data: dict[str, Any], *, simple_vue: bool) -> type[Component]:
    app = Citry()

    class Row(Component):
        citry = app
        template = "<li>r</li>"

    if simple_vue:

        class Leaf(Component):
            citry = app
            simple = "vue"

        Leaf.template = template
        root_template = '<ul><c-Leaf c-for="k in keys" c-key="k" c-flag="flag" c-n="n" c-items="items" /></ul>'
        del Leaf
    else:
        root_template = "<c-Row />" + template

    class Root(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return dict(data)

    del Row
    Root.template = root_template
    return Root


# Shapes for the first-render walkers the shapes above leave shallow: `Const`
# conditions and loops are precomputed and unrolled, chained loops build a
# nested read set, and a `simple='vue'` leaf builds its row plans.
FIRST_RENDER_SHAPES: dict[str, Callable[[int], tuple[str, dict[str, Any], bool]]] = {
    "const_if_tags": lambda d: (
        '<c-if cond="cflag">' * d + "{{ n }}" + "</c-if>" * d,
        {"cflag": Const(True), "n": 1},  # noqa: FBT003 - a constant data value, not a flag
        False,
    ),
    "const_loop_with_dynamic_body": lambda d: (
        '<c-for each="x in citems">' + '<c-if cond="flag">' * d + "{{ n }}" + "</c-if>" * d + "</c-for>",
        {"citems": Const([1, 2]), "flag": True, "n": 1},
        False,
    ),
    "chained_loops": lambda d: (_chained_loops(d), {"items": _chained_items(d), "n": 1}, False),
    "simple_vue_if_attributes": lambda d: (
        '<p c-if="flag">' * d + "{{ n }}" + "</p>" * d,
        {"flag": True, "n": 7, "keys": [1, 2], "items": []},
        True,
    ),
}


@pytest.mark.parametrize("shape", FIRST_RENDER_SHAPES)
def test_first_renders_of_const_and_simple_vue_templates_use_the_same_python_stack(
    shape: str,
    render_path: str,
) -> None:
    # Compile something unrelated first, so one-time import and set-up work
    # does not land in the shallow measurement.
    _peak_frames(_component(SHAPES["if_tags"](2)), first_render=True)
    peaks = []
    for depth in (SHALLOW, DEEP):
        template, data, simple_vue = FIRST_RENDER_SHAPES[shape](depth)
        root = _first_render_root(template, data, simple_vue=simple_vue)
        # A simple='vue' leaf's generated evaluator keeps one frame per level
        # by design, so only the frames of Citry's own walkers are counted.
        peaks.append(_peak_frames(root, first_render=True, count_generated=not simple_vue))
    shallow, deep = peaks
    assert deep - shallow <= ALLOWED_GROWTH, f"{shape}: {shallow} frames at depth {SHALLOW}, {deep} at {DEEP}"


class _SlotHook(Extension):
    """An `on_slot_rendered` hook that keeps each result as it is."""

    name = "slot_hook"

    def on_slot_rendered(self, ctx: Any) -> None:
        return None


@pytest.mark.parametrize("setting", ["slot_hook", "development"])
def test_nested_fallbacks_stay_flat_with_a_slot_hook_and_in_development_mode(setting: str, render_path: str) -> None:
    # Either setting adds work around each slot: an `on_slot_rendered` hook
    # runs on every slot's result, and development mode installs Citry's
    # own development extensions.
    def build(depth: int) -> type[Component]:
        app = Citry(extensions=[_SlotHook]) if setting == "slot_hook" else Citry(mode="development")

        class Row(Component):
            citry = app
            template = """
                <li>r</li>
            """

        class Root(Component):
            citry = app

            def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
                return {"flag": True, "n": 1, "items": [1]}

        del Row
        Root.template = SHAPES["slot_fallbacks"](depth)
        return Root

    shallow = _peak_frames(build(SHALLOW))
    deep = _peak_frames(build(DEEP))
    assert deep - shallow <= ALLOWED_GROWTH, f"{setting}: {shallow} frames at depth {SHALLOW}, {deep} at {DEEP}"
