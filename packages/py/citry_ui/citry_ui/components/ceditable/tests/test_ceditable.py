from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CEditable, CField


def _render(template: str, *, data: dict[str, object] | None = None, css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    source = template + ("<c-css />" if css else "")

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return data or {}

    page = Page()
    return str(page) if css else page.render().serialize(deps_strategy="ignore")


def _tag(html: str, part: str, index: int = 0) -> str:
    tags = re.findall(rf'<[^>]+data-citry-ui-part="{part}"[^>]*>', html)
    assert len(tags) > index
    return tags[index]


def test_public_schema_and_registration_are_exact() -> None:
    assert [field.name for field in fields(CEditable.Kwargs)] == [
        "value",
        "placeholder",
        "name",
        "form",
        "id",
        "editing",
        "required",
        "disabled",
        "readonly",
        "invalid",
        "max_length",
        "autocomplete",
        "inputmode",
        "submit_mode",
        "select_on_focus",
        "action_position",
        "edit_label",
        "submit_label",
        "cancel_label",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
        "input_attrs",
        "preview_attrs",
    ]
    hints = get_type_hints(CEditable.Kwargs)
    assert hints["action_position"] == citry_ui.CEditableActionPosition
    assert hints["submit_mode"] == citry_ui.CEditableSubmitMode
    assert CEditable in citry_ui.COMPONENTS


def test_progressive_native_input_and_default_inside_actions_are_exact() -> None:
    html = _render('<c-CEditable value="Project Atlas" name="title" required />')
    root = _tag(html, "root")
    input_tag = _tag(html, "input")
    assert 'data-action-position="inside"' in root
    assert 'data-submit-mode="both"' in root
    assert "data-required" in root
    assert 'name="title"' in input_tag
    assert 'value="Project Atlas"' in input_tag
    assert " required" in input_tag
    for part in (
        "preview",
        "preview-value",
        "edit-action",
        "edit-surface",
        "actions",
        "submit-action",
        "cancel-action",
    ):
        assert f'data-citry-ui-part="{part}"' in html
    assert html.count('type="button"') == 3


def test_outside_editing_states_and_labels_render() -> None:
    html = _render(
        '<c-CEditable value="Atlas" editing action_position="outside" '
        'edit_label="Rename" submit_label="Confirm" cancel_label="Reject" />'
    )
    root = _tag(html, "root")
    assert "data-editing" in root
    assert 'data-action-position="outside"' in root
    assert 'aria-label="Rename"' in html
    assert 'aria-label="Confirm"' in html
    assert 'aria-label="Reject"' in html


def test_field_owns_state_and_relationships() -> None:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "{{ field }}"

        def template_data(self, kwargs, slots):
            return {
                "field": CField(
                    required=True,
                    invalid=True,
                    slots={
                        "label": "Project title",
                        "description": "Keep it concise",
                        "error": "A title is required",
                        "default": CEditable(value="Atlas", name="title"),
                    },
                )
            }

    html = Page().render().serialize(deps_strategy="ignore")
    input_tag = _tag(html, "input")
    assert "aria-describedby=" in input_tag
    assert "aria-errormessage=" in input_tag
    assert 'aria-invalid="true"' in input_tag
    assert " required" in input_tag


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ('submit_mode="automatic"', "submit_mode must be one of"),
        ('action_position="left"', "action_position must be one of"),
        ('c-max_length="-1"', "zero or greater"),
        ("c-edit_label=\"' '\"", "must be nonempty"),
        ('c-select_on_focus="1"', "must be a bool"),
    ],
)
def test_invalid_server_inputs_fail(extra: str, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(f"<c-CEditable {extra} />")


@pytest.mark.parametrize(
    "extra",
    [
        "c-attrs=\"{'role':'application'}\"",
        "c-input_attrs=\"{'type':'email'}\"",
        "c-preview_attrs=\"{'x-show':'visible'}\"",
        "c-input_attrs=\"{':aria-describedby':'ids'}\"",
    ],
)
def test_owned_attrs_and_directives_are_rejected(extra: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(f"<c-CEditable {extra} />")


def test_strings_are_canonicalized_and_nul_is_rejected() -> None:
    html = _render('<c-CEditable c-value="value" />', data={"value": "a\r\nb"})
    assert 'value="a\nb"' in html
    with pytest.raises(ValueError, match="U\\+0000"):
        _render('<c-CEditable c-value="value" />', data={"value": "a\0b"})


def test_css_exposes_parts_tokens_and_environment_rules() -> None:
    html = _render("<c-CEditable />", css=True)
    for token in (
        "--cui-editable-background",
        "--cui-editable-action-background",
        "--cui-editable-action-size",
        "--cui-editable-radius",
    ):
        assert token in html
    assert "data-action-position" in html
    assert "forced-colors" in html
    assert "@media print" in html
