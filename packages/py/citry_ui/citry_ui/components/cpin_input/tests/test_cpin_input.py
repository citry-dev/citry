"""Focused server contracts for CPinInput."""

from __future__ import annotations

import re
from dataclasses import fields

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cfield import CField
from citry_ui.components.cpin_input import (
    CPinInput,
    CPinInputChangeSource,
    CPinInputCompleteDetail,
    CPinInputFocusChangeDetail,
    CPinInputInvalidDetail,
    CPinInputInvalidSource,
    CPinInputSeparatorSlotData,
    CPinInputSize,
    CPinInputType,
    CPinInputValueChangeDetail,
    CPinInputVariant,
)
from citry_ui.quality.asset_sources import read_component_source_css


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-pin-input-tests", (CField, CPinInput)))
    return app


def _render(template: str, data: dict[str, object] | None = None, *, css: bool = False) -> str:
    app = _app()
    source = template + ("<c-css />" if css else "")

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return data or {}

    page = Page()
    return str(page) if css else page.render().serialize(deps_strategy="ignore")


def _input(html: str) -> str:
    match = re.search(r'<input[^>]+data-citry-ui-part="input"[^>]*/?>', html)
    assert match is not None
    return match.group(0)


def test_public_schema_and_exports_are_exact() -> None:
    assert [field.name for field in fields(CPinInput.Kwargs)] == [
        "value",
        "name",
        "form",
        "id",
        "length",
        "type",
        "required",
        "disabled",
        "readonly",
        "invalid",
        "mask",
        "one_time_code",
        "placeholder",
        "attached",
        "separator_after",
        "label",
        "size",
        "variant",
        "class_",
        "style",
        "attrs",
        "input_attrs",
    ]
    assert [field.name for field in fields(CPinInput.Slots)] == ["separator"]
    assert all(
        item is not None
        for item in (
            CPinInputType,
            CPinInputSize,
            CPinInputVariant,
            CPinInputChangeSource,
            CPinInputInvalidSource,
            CPinInputValueChangeDetail,
            CPinInputCompleteDetail,
            CPinInputInvalidDetail,
            CPinInputFocusChangeDetail,
            CPinInputSeparatorSlotData,
        )
    )


def test_numeric_code_renders_one_progressive_native_input_and_visual_cells() -> None:
    html = _render(
        '<c-CPinInput id="code" name="code" form="verify" label="Verification code" '
        'value="0123" c-length="6" required class_="brand-code" c-style="style" />',
        {"style": {"--cui-pin-input-focus-color": "purple"}},
    )
    root = re.search(r'<div class="cui-pin-input brand-code"[^>]*>', html)
    assert root is not None
    native = _input(html)
    assert 'id="code"' in native
    assert 'name="code"' in native
    assert 'form="verify"' in native
    assert 'value="0123"' in native
    assert 'maxlength="6"' in native
    assert 'pattern="[0-9]{6}"' in native
    assert 'inputmode="numeric"' in native
    assert 'autocomplete="one-time-code"' in native
    assert 'aria-label="Verification code"' in native
    assert "required" in native
    assert html.count('data-citry-ui-part="cell"') == 6
    assert html.count("data-filled") >= 5  # root plus four cells
    assert "--cui-pin-input-focus-color: purple" in root.group(0)


def test_alphanumeric_mask_and_autocomplete_override_are_exact() -> None:
    html = _render(
        '<c-CPinInput label="Recovery code" value="A7c9" type="alphanumeric" c-length="4" mask '
        'c-input_attrs="input_attrs" />',
        {"input_attrs": {"autocomplete": "off", "enterkeyhint": "done"}},
    )
    native = _input(html)
    assert 'value="A7c9"' in native
    assert 'pattern="[A-Za-z0-9]{4}"' in native
    assert 'inputmode="text"' in native
    assert 'autocomplete="off"' in native
    assert 'enterkeyhint="done"' in native
    assert html.count("data-masked") == 4
    assert html.count(">•</span>") == 4


def test_readonly_submits_and_disabled_uses_native_unsuccessful_control() -> None:
    readonly = _input(_render('<c-CPinInput name="code" label="Code" value="123456" readonly />'))
    assert 'name="code"' in readonly
    assert "readonly" in readonly
    assert "disabled" not in readonly
    disabled = _input(_render('<c-CPinInput name="code" label="Code" value="123456" disabled />'))
    assert 'name="code"' in disabled
    assert "disabled" in disabled


def test_field_owns_label_state_and_relationships() -> None:
    html = _render(
        """
          <c-CField control_id="code" required invalid>
            <c-fill name="label">Verification code</c-fill>
            <c-fill name="default"><c-CPinInput name="code" /></c-fill>
            <c-fill name="description">Six digits</c-fill>
            <c-fill name="error">Enter the complete code</c-fill>
          </c-CField>
        """
    )
    native = _input(html)
    assert 'id="code"' in native
    assert 'aria-labelledby="code-label"' in native
    assert 'aria-describedby="code-description code-error"' in native
    assert 'aria-errormessage="code-error"' in native
    assert 'aria-invalid="true"' in native
    assert "required" in native
    assert 'for="code"' in html


def test_separator_slot_receives_boundary_index() -> None:
    html = _render(
        """
          <c-CPinInput label="Grouped code" c-separator_after="(2,)">
            <c-fill name="separator" data="{ index }">—{{ index }}</c-fill>
          </c-CPinInput>
        """
    )
    assert html.count('data-citry-ui-part="separator"') == 1
    assert "—2" in html


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({}, ValueError, "requires label"),
        ({"label": "Code", "length": 0}, ValueError, "between 1 and 32"),
        ({"label": "Code", "length": True}, TypeError, "must be an integer"),
        ({"label": "Code", "type": "unicode"}, ValueError, "must be one of"),
        ({"label": "Code", "value": "12a"}, ValueError, "numeric alphabet"),
        ({"label": "Code", "value": "1234567"}, ValueError, "at most 6"),
        ({"label": "Code", "placeholder": "ab"}, ValueError, "one Unicode code point"),
        ({"label": "Code", "separator_after": (5,)}, ValueError, "between 0 and 4"),
        ({"label": "Code", "separator_after": (2, 2)}, ValueError, "duplicate"),
    ],
)
def test_invalid_inputs_fail_deterministically(kwargs, error, match) -> None:
    with pytest.raises(error, match=re.escape(match)):
        _render('<c-CPinInput c-bind="kwargs" />', {"kwargs": kwargs})


@pytest.mark.parametrize(
    ("destination", "attribute"),
    [
        ("attrs", "id"),
        ("attrs", "data-focused"),
        ("input_attrs", "name"),
        ("input_attrs", "pattern"),
        ("input_attrs", "x-model"),
    ],
)
def test_owned_attributes_are_rejected(destination, attribute) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(
            '<c-CPinInput label="Code" c-bind="kwargs" />',
            {"kwargs": {destination: {attribute: "override"}}},
        )


def test_css_exposes_public_variables_parts_and_environment_rules() -> None:
    css = read_component_source_css("cpin_input")
    for variable in (
        "cell-size",
        "gap",
        "separator-gap",
        "border-color",
        "focus-color",
        "invalid-color",
        "background",
        "color",
        "placeholder-color",
        "radius",
        "disabled-opacity",
    ):
        assert f"--_cui-pin-input-{variable}: var(--cui-pin-input-{variable}" in css
    assert '[data-citry-ui-part="cell"]' in css
    assert "@media (pointer: coarse)" in css
    assert "@media (forced-colors: active)" in css
