# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

import json
import re
from dataclasses import fields
from pathlib import Path

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CFormCollection, CFormCollectionItem


def _render(source: str, *, static_fallback: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>"

    page = Page()
    return page.render().serialize(security_javascript="omit") if static_fallback else str(page)


def _manifest(html: str) -> dict[str, object]:
    match = re.search(r"CitryStable\.startPrepared\((\{.*\})\)\.catch", html, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))["manifest"]


def _collection_occurrence(manifest: dict[str, object]) -> dict[str, object]:
    return next(item for item in manifest["occurrences"] if item["typeKey"].startswith("CFormCollection_"))


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
    assert [item.name for item in fields(CFormCollection.JsData)] == ["serverDefaults"]
    assert CFormCollection in citry_ui.COMPONENTS
    assert CFormCollectionItem in citry_ui.COMPONENTS


def test_one_outer_form_native_actions_and_arbitrary_field_names() -> None:
    source = (
        '<form id="account"><c-CFormCollection id="contacts" label="Contacts" action_name="contact_action">'
        '<c-CFormCollectionItem value="a" label="Primary"><input name="contacts[a][email]" required /></c-CFormCollectionItem>'
        '<c-CFormCollectionItem value="b" label="Backup"><input name="custom-flat-name" /></c-CFormCollectionItem>'
        "</c-CFormCollection></form>"
    )
    html = _render(source)
    static_html = _render(source, static_fallback=True)
    assert static_html.count("<form") == 1
    assert "<fieldset" in static_html
    assert "<legend" in static_html
    assert "<h3" not in static_html
    assert 'role="group"' in static_html
    assert 'name="contacts[a][email]"' in static_html
    assert 'name="custom-flat-name"' in static_html
    assert static_html.count('name="contact_action"') == 7
    assert len(re.findall(r"<button[^>]+formnovalidate", static_html)) == 7
    assert 'value="remove:a"' in static_html
    assert 'value="move-down:b"' in static_html
    prepared = _collection_occurrence(_manifest(html))["preparedData"]
    actions = [
        attrs
        for key, attrs in prepared.items()
        if key.startswith("citryAttrs") and attrs.get("name") == "contact_action"
    ]
    assert len(actions) == 7
    assert {attrs["value"] for attrs in actions} == {
        "move-up:a",
        "move-down:a",
        "remove:a",
        "move-up:b",
        "move-down:b",
        "remove:b",
        "add",
    }


def test_min_max_and_item_policy_disable_or_omit_controls() -> None:
    source = (
        '<c-CFormCollection label="Approvers" c-min_items="2" c-max_items="2">'
        '<c-CFormCollectionItem value="a" label="Owner" c-removable="False" c-movable="False"><input /></c-CFormCollectionItem>'
        '<c-CFormCollectionItem value="b" label="Reviewer"><input /></c-CFormCollectionItem>'
        "</c-CFormCollection>"
    )
    html = _render(source)
    static_html = _render(source, static_fallback=True)
    assert re.search(r'data-citry-ui-part="add"[^>]*disabled|disabled[^>]*data-citry-ui-part="add"', static_html)
    owner = re.search(r'<li[^>]+data-value="a".*?</li>', static_html, re.DOTALL)
    assert owner is not None
    assert "data-citry-form-collection-action" not in owner.group(0)
    reviewer = re.search(r'<li[^>]+data-value="b".*?</li>', static_html, re.DOTALL)
    assert reviewer is not None
    assert re.search(
        r'data-citry-form-collection-action="remove"[^>]*disabled|disabled[^>]*data-citry-form-collection-action="remove"',
        reviewer.group(0),
    )
    prepared = _collection_occurrence(_manifest(html))["preparedData"]
    attrs = [value for key, value in prepared.items() if key.startswith("citryAttrs")]
    assert any(value.get("value") == "add" and "disabled" in value for value in attrs)
    assert any(value.get("value") == "move-down:b" and "disabled" in value for value in attrs)


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
        ("<c-CFormCollection label=\"X\" c-attrs=\"{'ref':'other'}\"></c-CFormCollection>", "owned attribute"),
    ],
)
def test_invalid_composition_fails(source: str, match: str) -> None:
    with pytest.raises((SyntaxError, TypeError, ValueError), match=match):
        _render(source)


def test_explicit_action_labels_render_without_catalog_ownership() -> None:
    source = (
        '<c-CFormCollection label="Rows" add_label="Append" remove_label="Delete {item}" '
        'move_up_label="Raise {item}" move_down_label="Lower {item}">'
        '<c-CFormCollectionItem value="a" label="Alpha"><input /></c-CFormCollectionItem></c-CFormCollection>'
    )
    html = _render(source)
    static_html = _render(source, static_fallback=True)
    assert ">Append</button>" in static_html
    assert 'aria-label="Delete Alpha"' in static_html
    prepared = _collection_occurrence(_manifest(html))["preparedData"]
    assert prepared["citryText2"] == "Append"
    assert any(
        attrs.get("aria-label") == "Delete Alpha" for key, attrs in prepared.items() if key.startswith("citryAttrs")
    )


def test_assets_docs_and_translation_reference_cover_the_contract() -> None:
    root = Path(__file__).parents[1]
    python = (root / "cform_collection.py").read_text(encoding="utf8")
    js = (root / "runtime.source.js").read_text(encoding="utf8")
    css = (root / "runtime.source.css").read_text(encoding="utf8")
    guide = (root / "api.md").read_text(encoding="utf8")
    reference = (root / "api.yml").read_text(encoding="utf8")
    for fragment in (
        "onServerRender",
        "component.$refs.root",
        "Citry.vue.watchEffect",
        "resolvedDisabled",
        "onAction",
        "toIndex",
        "sourceEvent",
        "removeEventListener",
    ):
        assert fragment in js
    assert "citryInitiallyDisabled" not in js
    assert "data-citry-form-collection-action-disabled" in python
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
