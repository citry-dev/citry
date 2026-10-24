"""
Rendering a deeper template does not need more Python frames.

The body renderer, fill collection and the Vue leaf program walk nested
``<c-if>``, ``<c-for>`` and ``c-if=`` bodies on their own stacks, and the
generated leaf code stops at a fixed nesting depth. So the deepest Python
call stack during a render stays the same however deeply control flow
nests. Each case renders once to compile, then measures the second render
with a profile hook that records the deepest stack. The peak at depth 128
may be at most 20 frames above the peak at depth 32. A first render, which
also compiles the component and walks its template several times, is
measured the same way.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component

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
    "fills_under_control_flow": lambda d: (
        "<c-Row />"
        + '<c-Card><c-fill name="default"><c-if cond="flag">' * d
        + "{{ n }}"
        + "</c-if></c-fill></c-Card>" * d
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


def _peak_frames(root: type[Component], *, first_render: bool = False) -> int:
    """Return the deepest Python stack seen while rendering ``root``, a second time unless ``first_render``."""
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
    # A component's first render also precomputes its constant parts, runs
    # the i18n and events transforms (both on by default), and compiles its
    # Vue leaf program; each of those walks the whole template.
    build = SHAPES[shape]
    shallow = _peak_frames(_component(build(SHALLOW)), first_render=True)
    deep = _peak_frames(_component(build(DEEP)), first_render=True)
    assert deep - shallow <= ALLOWED_GROWTH, f"{shape}: {shallow} frames at depth {SHALLOW}, {deep} at {DEEP}"
