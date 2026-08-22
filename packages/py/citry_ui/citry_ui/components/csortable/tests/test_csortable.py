# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CSortable, CSortableItem


def _render(source: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>"

    return str(Page())


def test_public_schema_and_registration_are_explicit() -> None:
    assert [item.name for item in fields(CSortable.Kwargs)] == [
        "id",
        "order",
        "name",
        "form",
        "layout",
        "disabled",
        "size",
        "label",
        "handle_label",
        "instructions_label",
        "picked_up_label",
        "moved_label",
        "dropped_label",
        "cancelled_label",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CSortableItem.Kwargs)] == [
        "value",
        "label",
        "disabled",
        "class_",
        "style",
        "attrs",
    ]
    assert CSortable in citry_ui.COMPONENTS
    assert CSortableItem in citry_ui.COMPONENTS


def test_server_order_semantics_and_native_form_entries() -> None:
    html = _render(
        '<c-CSortable id="tasks" name="priority" form="settings" layout="grid" '
        "c-order=\"['c','a','b']\">"
        '<c-CSortableItem value="a" label="Alpha" />'
        '<c-CSortableItem value="b" label="Beta" c-disabled="True" />'
        '<c-CSortableItem value="c" label="Gamma" />'
        "</c-CSortable>"
    )
    root = re.search(r'<div[^>]+id="tasks"[^>]*>', html)
    assert root is not None
    assert 'data-layout="grid"' in root.group(0)
    assert "aria-label" not in root.group(0)
    assert re.search(r'<ol[^>]+aria-label="Reorder items"', html)
    values = re.findall(r'data-value="([abc])"', html)
    assert values[:3] == ["c", "a", "b"]
    assert html.count('name="priority"') == 3
    assert html.count('form="settings"') == 3
    assert html.count("data-citry-sortable-handle") >= 3
    assert 'aria-live="polite"' in html


def test_default_and_handle_slots_render_without_replacing_owned_button() -> None:
    html = _render(
        '<c-CSortable><c-CSortableItem value="a" label="Alpha">'
        '<c-fill name="handle"><span>Move icon</span></c-fill>'
        '<c-fill name="default"><strong>Rich Alpha</strong></c-fill>'
        "</c-CSortableItem></c-CSortable>"
    )
    assert "<strong>Rich Alpha</strong>" in html
    assert "<span>Move icon</span>" in html
    assert re.search(r"<button[^>]+data-citry-sortable-handle", html)


@pytest.mark.parametrize(
    ("source", "match"),
    [
        ("<c-CSortable></c-CSortable>", "requires 1 slot"),
        (
            '<c-CSortable><c-CSortableItem value="a" label="A" /><c-CSortableItem value="a" label="B" /></c-CSortable>',
            "duplicated",
        ),
        (
            '<c-CSortable c-order="[\'missing\']"><c-CSortableItem value="a" label="A" /></c-CSortable>',
            "every declared",
        ),
        ('<c-CSortable layout="stack"><c-CSortableItem value="a" label="A" /></c-CSortable>', "must be one of"),
        ('<c-CSortable><p>wrong</p><c-CSortableItem value="a" label="A" /></c-CSortable>', "may contain only"),
    ],
)
def test_invalid_composition_fails(source: str, match: str) -> None:
    with pytest.raises((SyntaxError, TypeError, ValueError), match=match):
        _render(source)


def test_explicit_labels_do_not_register_catalog_bindings() -> None:
    html = _render(
        '<c-CSortable label="Custom order" handle_label="Reorder {item}">'
        '<c-CSortableItem value="a" label="Alpha" /></c-CSortable>'
    )
    assert re.search(r'<ol[^>]+aria-label="Custom order"', html)
    assert 'aria-label="Reorder Alpha"' in html


def test_assets_cover_keyboard_pointer_controlled_cleanup_and_environment() -> None:
    root = Path(__file__).parents[1]
    js = (root / "runtime.source.js").read_text(encoding="utf8")
    css = (root / "runtime.source.css").read_text(encoding="utf8")
    for fragment in (
        "onOrderChange",
        "pointerdown",
        "pointercancel",
        "setPointerCapture",
        "ArrowDown",
        "Escape",
        "controlled",
        "onReset",
        "removeEventListener",
        "i18n.tr",
    ):
        assert fragment in js
    for fragment in (
        'data-layout="grid"',
        "prefers-reduced-motion",
        "forced-colors",
        "pointer: coarse",
        "@media print",
    ):
        assert fragment in css


def test_public_docs_and_structured_reference_exist() -> None:
    root = Path(__file__).parents[1]
    guide = (root / "api.md").read_text(encoding="utf8")
    reference = (root / "api.yml").read_text(encoding="utf8")
    assert guide.count("<c-ui-demo ") == 6
    assert "translations:" in reference
    for key in (
        "citry-ui-sortable-label",
        "citry-ui-sortable-handle",
        "citry-ui-sortable-picked-up",
        "citry-ui-sortable-moved",
        "citry-ui-sortable-dropped",
        "citry-ui-sortable-cancelled",
    ):
        assert key in reference
