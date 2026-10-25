"""
Rendering a body produces the same output, structure and errors as before.

The body renderer walks a template's nodes with an explicit stack instead
of calling itself once per ``<c-if>`` or ``<c-for>``. These snapshots were
recorded on 1b64f7102, before that change, and lock what it produced, for
each fixture on both render paths:

- the serialized HTML;
- the nested structure of the render result: which ``CitryRender`` and
  other parts hold which, written by ``_structure`` below;
- the error text for an expression that fails three levels deep, and the
  nodes that add their template position as the error passes out.

Run with ``CITRY_UPDATE_RENDER_SNAPSHOTS=1`` to record them again; the file
is ``render_body_snapshots.json`` next to this one.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component, component_render
from citry.citry_render import CitryRender

if TYPE_CHECKING:
    from collections.abc import Callable

SNAPSHOT_FILE = Path(__file__).with_name("render_body_snapshots.json")
UPDATE = os.environ.get("CITRY_UPDATE_RENDER_SNAPSHOTS") == "1"

# Every condition and loop reads the template data. A constant one, such as
# `cond="1"`, is computed once when the component compiles, and the body
# renderer never sees it.

# How deep the nested fixtures go: deep enough that every level is a frame
# of the walk, shallow enough that the recorded structure stays readable.
DEPTH = 8


def _nest(open_tag: str, inner: str, close_tag: str, depth: int = DEPTH) -> str:
    return open_tag * depth + inner + close_tag * depth


def _structure(part: Any) -> Any:
    """Write a render part's nesting as plain data: type names and children."""
    if isinstance(part, str):
        return part
    if isinstance(part, CitryRender):
        return [type(part).__name__, [_structure(child) for child in part.parts]]
    return type(part).__name__


def _render_root(template: str, data: dict[str, Any], extra: Callable[[Citry], None] | None = None) -> Any:
    app = Citry()
    if extra is not None:
        extra(app)

    class Root(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return dict(data)

    Root.template = template
    return Root().render()


def _children(app: Citry) -> None:
    """Register the small components the fixtures place."""

    class Card(Component):
        citry = app
        template = '<section class="card"><c-slot name="title">no title</c-slot><c-slot>{{ body }}</c-slot></section>'

        def template_data(self, kwargs, slots):
            return {"body": kwargs.get("body", "default body")}

    class Row(Component):
        citry = app
        template = "<li>{{ label }}</li>"

        def template_data(self, kwargs, slots):
            return {"label": kwargs.get("label", "?")}

    class Label(Component):
        citry = app
        simple = True
        template = "<span>{{ text }}<c-slot /></span>"

    class Holder(Component):
        citry = app
        template = "<div>{{ body }}</div>"

        def template_data(self, kwargs, slots):
            return {"body": kwargs.get("body")}

    del Card, Row, Label, Holder


FIXTURES: dict[str, tuple[str, dict[str, Any]]] = {
    "if_elif_else": (
        _nest(
            '<c-if cond="n > 5">',
            "{{ n }}",
            '</c-if><c-elif cond="n > 2">mid</c-elif><c-else>low</c-else>',
        ),
        {"n": 7},
    ),
    "if_falls_to_else": (
        _nest('<c-if cond="flag"><b>', "{{ n }}", "</b></c-if><c-else>none</c-else>"),
        {"n": 1, "flag": False},
    ),
    "for_with_empty": (
        # Each level binds its own name, because a loop may not shadow one.
        "".join(f'<c-for each="x{level} in items">' for level in range(DEPTH))
        + "{{ x0 }}{{ x7 }}"
        + "</c-for><c-empty>empty</c-empty>" * DEPTH,
        {"items": [1, 2]},
    ),
    "for_empty_branch": (
        '<c-for each="x in items">{{ x }}</c-for><c-empty>' + _nest("<i>", "nothing", "</i>") + "</c-empty>",
        {"items": []},
    ),
    "shorthand_forms": (
        _nest(
            '<div c-if="flag">',
            '<p c-for="x in items">{{ x }}</p><p c-empty>none</p>',
            '</div><span c-elif="other">o</span><span c-else>e</span>',
        ),
        {"flag": True, "other": False, "items": ["a", "b"]},
    ),
    "mixed_elements_and_logic": (
        _nest('<c-if cond="flag"><ul>', '<c-for each="x in items"><li>{{ x }}</li></c-for>', "</ul></c-if>"),
        {"flag": True, "items": [1, 2, 3]},
    ),
    "components_with_slots_and_fills": (
        _nest(
            '<c-Card body="b"><c-fill name="title">T</c-fill><c-fill name="default">',
            "{{ n }}",
            "</c-fill></c-Card>",
        ),
        {"flag": True, "n": 3},
    ),
    "component_default_slot_content": (
        _nest('<c-if cond="flag"><c-Card body="inner">', "", "</c-Card></c-if>"),
        {"flag": True},
    ),
    "simple_component_slot_outlet": (
        _nest('<c-Label text="t">', "{{ n }}", "</c-Label>"),
        {"flag": True, "n": 4},
    ),
    "call_run_rows": (
        _nest('<c-if cond="flag"><ul>', '<c-Row c-for="k in keys" c-key="k" label="row" />', "</ul></c-if>"),
        {"flag": True, "keys": [1, 2, 3]},
    ),
    "template_in_attribute": (
        "<c-Holder c-body='" + _nest('<c-if cond="flag"><b>', "{{ n }}", "</b></c-if>") + "' />",
        {"flag": True, "n": 5},
    ),
    "dynamic_component_and_element": (
        _nest(
            '<c-if cond="flag">', '<c-component is="card" body="dyn" /><c-element c-is="tag">x</c-element>', "</c-if>"
        ),
        {"flag": True, "tag": "em"},
    ),
    "provide_and_inject": (
        _nest('<c-if cond="flag">', '<c-provide key="theme" mode="dark">{{ n }}</c-provide>', "</c-if>"),
        {"flag": True, "n": 6},
    ),
}

# A body made only of HTML, expressions and control flow renders through a
# Vue leaf program, which evaluates it without the body renderer. One child
# component in the body turns that off, so these copies render through the
# body renderer and its `IfNode` and `ForNode` steps.
_GENERAL_RENDERER_COPIES = (
    "if_elif_else",
    "if_falls_to_else",
    "for_with_empty",
    "shorthand_forms",
    "mixed_elements_and_logic",
)
for _name in _GENERAL_RENDERER_COPIES:
    _template, _data = FIXTURES[_name]
    FIXTURES[f"{_name}_with_component"] = ('<c-Row label="r" />' + _template, _data)

# An expression that fails three levels below the root, inside an `<c-if>`,
# a `<c-for>` and an element, so each level's template position is added to
# the error as it passes through.
ERROR_TEMPLATE = (
    '<main><c-Row label="r" /><c-if cond="flag"><c-for each="x in items">'
    '<p class="row">{{ x.missing }}</p></c-for></c-if></main>'
)


def _load() -> dict[str, Any]:
    if SNAPSHOT_FILE.exists():
        return json.loads(SNAPSHOT_FILE.read_text())
    return {}


def _check(key: str, observed: Any) -> None:
    """Compare `observed` with the recorded snapshot, or record it when updating."""
    snapshots = _load()
    if UPDATE:
        snapshots[key] = observed
        SNAPSHOT_FILE.write_text(json.dumps(snapshots, indent=1, sort_keys=True) + "\n")
        return
    assert key in snapshots, f"no snapshot for {key}; record with CITRY_UPDATE_RENDER_SNAPSHOTS=1"
    assert observed == snapshots[key]


@pytest.mark.parametrize("name", FIXTURES)
def test_render_output_and_structure_match_the_snapshot(name: str, render_path: str) -> None:
    template, data = FIXTURES[name]
    rendered = _render_root(template, data, _children)
    _check(
        f"{name}/{render_path}",
        {"html": rendered.serialize(deps_strategy="ignore"), "structure": _structure(rendered)},
    )


def test_an_error_three_levels_deep_matches_the_snapshot(render_path: str, monkeypatch: pytest.MonkeyPatch) -> None:
    # Only the innermost node's snippet shows in the text, so the nodes that
    # add their position on the way out are recorded too, in order.
    attached: list[str] = []
    original = component_render._attach_template_position

    def spy(err: Exception, node: object, context: object) -> None:
        attached.append(type(node).__name__)
        original(err, node, context)  # type: ignore[arg-type]

    monkeypatch.setattr(component_render, "_attach_template_position", spy)
    with pytest.raises(Exception) as caught:  # noqa: PT011 - the recorded text is what is compared
        _render_root(ERROR_TEMPLATE, {"items": [1], "flag": True}, _children).serialize(deps_strategy="ignore")
    # The error names the template's origin, this file's absolute path, which
    # differs between checkouts; the snapshot stores a placeholder for it.
    text = str(caught.value).replace(str(Path(__file__)), "<this test file>")
    _check(
        f"error/{render_path}",
        {"type": type(caught.value).__name__, "text": text, "attached": attached},
    )
