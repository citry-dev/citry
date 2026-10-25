"""
Checking a deeper template does not need more Python frames.

``citry check`` walks each template's parsed tree with several linters and
collectors. They run as walk generators on one driver loop, so the deepest
Python call stack during a check stays the same however deeply the template
nests. Each case checks one component at depth 32 and at depth 128; the
peak at 128 may be at most 20 frames above the peak at 32.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component
from citry._app_selection import CheckAppSelection
from citry._checker import check_project

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import FrameType

SHALLOW = 32
DEEP = 128
ALLOWED_GROWTH = 20


def _for_tags(depth: int) -> str:
    """Nested `<c-for>` tags that each bind their own name."""
    return "".join(f'<c-for each="x{level} in items">' for level in range(depth))


SHAPES: dict[str, Callable[[int], str]] = {
    "elements": lambda d: "<div>" * d + "{{ n }}" + "</div>" * d,
    "if_tags": lambda d: '<c-if cond="flag">' * d + "{{ n }}" + "</c-if>" * d,
    "for_tags": lambda d: _for_tags(d) + "{{ n }}" + "</c-for>" * d,
    "if_attributes": lambda d: '<p c-if="flag">' * d + "{{ n }}" + "</p>" * d,
    "fills_under_control_flow": lambda d: (
        '<c-Card><c-fill name="default">' + '<c-if cond="flag">' * d + "{{ n }}" + "</c-if>" * d + "</c-fill></c-Card>"
    ),
    "template_in_an_attribute": lambda d: "<c-Card c-body='" + "<b>" * d + "{{ n }}" + "</b>" * d + "' />",
}


def _check_peak(template: str, tmp_path: Path) -> int:
    """Return the deepest Python stack seen while checking a component with ``template``."""
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = "<section><c-slot /></section>"

    type("Page", (Component,), {"citry": engine, "template": template, "__module__": __name__})
    del Card
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
        check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    finally:
        sys.setprofile(None)
    return peak


@pytest.mark.parametrize("shape", SHAPES)
def test_checking_a_deeper_template_uses_the_same_python_stack(shape: str, tmp_path: Path) -> None:
    # Check something small first, so one-time set-up work does not land in
    # the shallow measurement.
    _check_peak(SHAPES["elements"](2), tmp_path)
    build = SHAPES[shape]
    shallow = _check_peak(build(SHALLOW), tmp_path)
    deep = _check_peak(build(DEEP), tmp_path)
    assert deep - shallow <= ALLOWED_GROWTH, f"{shape}: {shallow} frames at depth {SHALLOW}, {deep} at {DEEP}"
