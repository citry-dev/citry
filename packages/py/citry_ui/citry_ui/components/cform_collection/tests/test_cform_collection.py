# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CFormCollection, CFormCollectionItem


def _render(source: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>"

    return str(Page())


def test_public_schemas_and_catalog_are_explicit() -> None:
    assert [item.name for item in fields(CFormCollection.Kwargs)] == [
        "label",
        "id",
        "description",
        "action_name",
        "add_value",
        "allow_add",
        "allow_remove",
        "allow_reorder",
        "min_items",
        "max_items",
        "disabled",
        "size",
        "add_label",
        "remove_label",
        "move_up_label",
        "move_down_label",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CFormCollectionItem.Kwargs)] == [
        "value",
        "label",
        "remove_value",
        "move_up_value",
        "move_down_value",
        "removable",
        "movable",
        "disabled",
        "class_",
        "style",
        "attrs",
    ]
    assert CFormCollection in citry_ui.COMPONENTS
    assert CFormCollectionItem in citry_ui.COMPONENTS


def test_one_outer_form_native_actions_and_arbitrary_field_names() -> None:
    html = _render(
        '<form id="account"><c-CFormCollection id="contacts" label="Contacts" action_name="contact_action">'
        '<c-CFormCollectionItem value="a" label="Primary"><input name="contacts[a][email]" required /></c-CFormCollectionItem>'
        '<c-CFormCollectionItem value="b" label="Backup"><input name="custom-flat-name" /></c-CFormCollectionItem>'
        "</c-CFormCollection></form>"
    )
    assert html.count("<form") == 1
    assert "<fieldset" in html
    assert "<legend" in html
    assert "<h3" not in html
    assert 'role="group"' in html
    assert 'name="contacts[a][email]"' in html
    assert 'name="custom-flat-name"' in html
    assert html.count('name="contact_action"') == 7
    assert len(re.findall(r"<button[^>]+formnovalidate", html)) == 7
    assert 'value="remove:a"' in html
    assert 'value="move-down:b"' in html


def test_min_max_and_item_policy_disable_or_omit_controls() -> None:
    html = _render(
        '<c-CFormCollection label="Approvers" c-min_items="2" c-max_items="2">'
        '<c-CFormCollectionItem value="a" label="Owner" c-removable="False" c-movable="False"><input /></c-CFormCollectionItem>'
        '<c-CFormCollectionItem value="b" label="Reviewer"><input /></c-CFormCollectionItem>'
        "</c-CFormCollection>"
    )
    assert re.search(r'data-citry-ui-part="add"[^>]*disabled|disabled[^>]*data-citry-ui-part="add"', html)
    owner = re.search(r'<li[^>]+data-value="a".*?</li>', html, re.DOTALL)
    assert owner is not None
    assert "data-citry-form-collection-action" not in owner.group(0)
    reviewer = re.search(r'<li[^>]+data-value="b".*?</li>', html, re.DOTALL)
    assert reviewer is not None
    assert re.search(
        r'data-citry-form-collection-action="remove"[^>]*disabled|disabled[^>]*data-citry-form-collection-action="remove"',
        reviewer.group(0),
    )


@pytest.mark.parametrize(
    ("source", "match"),
    [
        (
            '<c-CFormCollection><c-CFormCollectionItem value="a" label="A"><input /></c-CFormCollectionItem></c-CFormCollection>',
            "must have",
        ),
        (
            '<c-CFormCollection label="X"><c-CFormCollectionItem value="a" label="A"><input /></c-CFormCollectionItem><c-CFormCollectionItem value="a" label="B"><input /></c-CFormCollectionItem></c-CFormCollection>',
            "duplicated",
        ),
        (
            '<c-CFormCollection label="X" c-min_items="2"><c-CFormCollectionItem value="a" label="A"><input /></c-CFormCollectionItem></c-CFormCollection>',
            "renders 1",
        ),
        ('<c-CFormCollection label="X" c-min_items="3" c-max_items="2"></c-CFormCollection>', "greater than or equal"),
        ('<c-CFormCollection label="X"><p>wrong</p></c-CFormCollection>', "may contain only"),
    ],
)
def test_invalid_composition_fails(source: str, match: str) -> None:
    with pytest.raises((SyntaxError, TypeError, ValueError), match=match):
        _render(source)


def test_explicit_action_labels_render_without_catalog_ownership() -> None:
    html = _render(
        '<c-CFormCollection label="Rows" add_label="Append" remove_label="Delete {item}" '
        'move_up_label="Raise {item}" move_down_label="Lower {item}">'
        '<c-CFormCollectionItem value="a" label="Alpha"><input /></c-CFormCollectionItem></c-CFormCollection>'
    )
    assert ">Append</button>" in html
    assert 'aria-label="Delete Alpha"' in html


def test_assets_docs_and_translation_reference_cover_the_contract() -> None:
    root = Path(__file__).parents[1]
    js = (root / "runtime.source.js").read_text(encoding="utf8")
    css = (root / "runtime.source.css").read_text(encoding="utf8")
    guide = (root / "api.md").read_text(encoding="utf8")
    reference = (root / "api.yml").read_text(encoding="utf8")
    for fragment in ("onAction", "toIndex", "sourceEvent", "removeEventListener"):
        assert fragment in js
    for fragment in ("prefers-reduced-motion", "forced-colors", "@media print"):
        assert fragment in css
    assert guide.count("<c-ui-demo ") == 6
    for key in (
        "citry-ui-form-collection-add",
        "citry-ui-form-collection-remove",
        "citry-ui-form-collection-move-up",
        "citry-ui-form-collection-move-down",
    ):
        assert key in reference
