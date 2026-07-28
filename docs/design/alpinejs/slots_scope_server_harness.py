# ruff: noqa: ANN001, ANN202, ARG002, S101, T201
"""
Server-side evidence for the redone Alpine slot-scope exploration.

Run from the repository root:

    uv run python docs/design/alpinejs/slots_scope_server_harness.py

The harness exercises the real parser, slot normalization, render tree, and
serializer. It does not add fill provenance to the product.
"""

from __future__ import annotations

import json
import re
from typing import Any

from citry import Citry, CitryRender, Component, Extension, Slot
from citry.util.html import SafeString


def _scrub_ids(html: str) -> str:
    return re.sub(r' data-cid-[^= ]+=""', "", html)


def _context_name(render: CitryRender) -> str:
    component = render.context.component
    return type(component).__name__ if component is not None else "None"


def _render_tree(part: Any) -> Any:
    if not isinstance(part, CitryRender):
        return type(part).__name__
    return {
        "owner": _context_name(part),
        "children": [_render_tree(child) for child in part.parts if isinstance(child, CitryRender)],
    }


def syntax_cases() -> dict[str, Any]:
    c = Citry()
    invalid_error = None
    try:

        class Invalid(Component):
            citry = c
            template = "<button>saved {{ $state.saves }} times</button>"

        str(Invalid())
    except Exception as error:  # noqa: BLE001
        invalid_error = {"type": type(error).__name__, "message": str(error)}

    class Valid(Component):
        citry = c
        template = '<button x-text="`saved ${$state.saves} times`"></button>'

    valid_html = _scrub_ids(str(Valid()))
    assert invalid_error is not None
    assert "$" in invalid_error["message"]
    assert valid_html == '<button x-text="`saved ${$state.saves} times`"></button>'
    return {"invalidPythonInterpolation": invalid_error, "validAlpineAttribute": valid_html}


def origin_cases() -> dict[str, Any]:
    c = Citry()
    captured: dict[str, Slot] = {}

    class Box(Component):
        citry = c
        template = '<div><c-slot name="x" /></div>'

        def template_data(self, kwargs, slots):
            captured["template"] = slots.get("x")
            return {}

    class Page(Component):
        citry = c
        template = '<c-box><c-fill name="x"><span x-text="owner"></span></c-fill></c-box>'

    template_html = _scrub_ids(str(Page()))
    template_slot = captured["template"]
    template_result = template_slot()
    assert isinstance(template_result, CitryRender)
    assert _context_name(template_result) == "Page"
    assert template_slot.component_name == "box"

    escaped = _scrub_ids(str(Box(slots={"x": '<button x-text="bad"></button>'})))
    raw = _scrub_ids(str(Box(slots={"x": SafeString('<button x-text="raw"></button>')})))
    assert "&lt;button" in escaped
    assert raw == '<div><button x-text="raw"></button></div>'

    reusable = Slot(SafeString('<span class="shared" x-text="owner"></span>'))

    class ReusedAtTwoLocations(Component):
        citry = c
        template = """
          <section>
            <div id="source-a" x-data="{ owner: 'A' }">{{ left }}</div>
            <div id="source-b" x-data="{ owner: 'B' }">{{ right }}</div>
          </section>
        """

        def template_data(self, kwargs, slots):
            return {
                "left": Box(slots={"x": reusable}),
                "right": Box(slots={"x": reusable}),
            }

    reused_html = _scrub_ids(str(ReusedAtTwoLocations()))
    assert reused_html.count('class="shared"') == 2
    assert reusable.source_position is None
    assert "data-cfill" not in reused_html

    return {
        "templateFill": {
            "html": template_html,
            "resultOwner": _context_name(template_result),
            "slotComponentName": template_slot.component_name,
            "hasSourcePosition": template_slot.source_position is not None,
        },
        "plainString": escaped,
        "safeString": raw,
        "reusedSlot": {
            "html": reused_html,
            "constructionSourcePosition": reusable.source_position,
            "fillCopies": reused_html.count('class="shared"'),
            "browserProvenancePresent": "data-cfill" in reused_html,
        },
    }


def fallback_transition_case() -> dict[str, Any]:
    observed: list[CitryRender] = []

    class CaptureSlotResult(Extension):
        name = "capture_slot_result"

        def on_slot_rendered(self, ctx):
            if isinstance(ctx.result, CitryRender):
                observed.append(ctx.result)

    c = Citry(extensions=[CaptureSlotResult])

    class Card(Component):
        citry = c
        template = '<c-slot name="x"><i x-text="child"></i></c-slot>'

    class Page(Component):
        citry = c
        template = """
          <c-card>
            <c-fill name="x" fallback="fb">
              <b x-text="parent">{{ fb }}</b>
            </c-fill>
          </c-card>
        """

    html = _scrub_ids(str(Page())).strip()
    assert html == '<b x-text="parent"><i x-text="child"></i></b>'
    assert observed
    tree = _render_tree(observed[-1])
    assert tree == {
        "owner": "Page",
        "children": [{"owner": "Card", "children": []}],
    }
    assert "data-cfill" not in html
    return {"html": html, "renderTree": tree, "browserProvenancePresent": False}


def root_shapes() -> dict[str, Any]:
    c = Citry()

    class Outlet(Component):
        citry = c
        template = "<c-slot />"

    class Multi(Component):
        citry = c
        template = "<c-outlet><span>A</span>text<b>B</b></c-outlet>"

    class Text(Component):
        citry = c
        template = "<c-outlet>plain text</c-outlet>"

    class EmptyPage(Component):
        citry = c
        template = '<c-outlet><c-fill name="default" /></c-outlet>'

    multi = _scrub_ids(str(Multi()))
    text = _scrub_ids(str(Text()))
    empty = _scrub_ids(str(EmptyPage()))
    assert multi == "<span>A</span>text<b>B</b>"
    assert text == "plain text"
    assert empty == ""
    return {"multiRoot": multi, "textOnly": text, "empty": empty}


def main() -> None:
    evidence = {
        "syntax": syntax_cases(),
        "origins": origin_cases(),
        "fallbackTransition": fallback_transition_case(),
        "rootShapes": root_shapes(),
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
