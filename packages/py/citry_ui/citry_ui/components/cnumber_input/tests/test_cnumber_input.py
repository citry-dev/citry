"""Focused server contract tests for CNumberInput."""

from __future__ import annotations

import re
from dataclasses import fields
from decimal import Decimal

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cfield import CField
from citry_ui.components.cnumber_input import (
    CNumberInput,
    CNumberInputChangeSource,
    CNumberInputCommitBehavior,
    CNumberInputExact,
    CNumberInputInputValueChangeDetail,
    CNumberInputParseStatus,
    CNumberInputSize,
    CNumberInputValueChangeDetail,
    CNumberInputVariant,
)
from citry_ui.quality.asset_sources import read_component_source_css


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-number-input-tests", (CField, CNumberInput)))
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


def _tag(html: str, pattern: str) -> str:
    match = re.search(pattern, html)
    assert match is not None
    return match.group(0)


def test_public_schema_and_exports_are_exact() -> None:
    assert [field.name for field in fields(CNumberInput.Kwargs)] == [
        "value",
        "name",
        "form",
        "id",
        "min",
        "max",
        "step",
        "required",
        "disabled",
        "readonly",
        "invalid",
        "show_controls",
        "wheel",
        "commit_behavior",
        "placeholder",
        "autocomplete",
        "increment_label",
        "decrement_label",
        "required_message",
        "invalid_message",
        "minimum_message",
        "maximum_message",
        "step_message",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
        "input_attrs",
    ]
    assert fields(CNumberInput.Slots) == ()
    assert all(
        item is not None
        for item in (
            CNumberInputChangeSource,
            CNumberInputCommitBehavior,
            CNumberInputExact,
            CNumberInputInputValueChangeDetail,
            CNumberInputParseStatus,
            CNumberInputSize,
            CNumberInputValueChangeDetail,
            CNumberInputVariant,
        )
    )


def test_exact_decimal_ssr_and_progressive_form_anatomy() -> None:
    html = _render(
        """
          <c-CNumberInput
            id="quantity"
            name="quantity"
            form="order"
            c-value="value"
            min="-2"
            max="10"
            step="0.25"
            required
            class_="quantity-control"
            c-style="style"
            c-input_attrs="input_attrs"
          />
        """,
        {
            "value": Decimal("01.5000"),
            "style": {"--cui-number-input-control-size": "3rem"},
            "input_attrs": {"aria-label": "Quantity"},
        },
    )
    root = _tag(html, r'<div class="cui-number-input quantity-control"[^>]*>')
    editor = _tag(html, r'<input id="quantity"[^>]*>')
    transport = _tag(html, r'<input id="quantity-transport"[^>]*>')
    assert "data-required" in root
    assert 'style="--cui-number-input-control-size: 3rem;"' in root
    assert 'name="quantity"' in editor
    assert 'form="order"' in editor
    assert 'value="1.5"' in editor
    assert 'role="spinbutton"' in editor
    assert 'aria-valuemin="-2"' in editor
    assert 'aria-valuemax="10"' in editor
    assert 'aria-valuenow="1.5"' in editor
    assert 'aria-label="Quantity"' in editor
    assert 'type="hidden" disabled' in transport
    assert 'data-citry-ui-part="decrement"' in html
    assert 'data-citry-ui-part="increment"' in html


def test_empty_and_hidden_controls_render_useful_no_javascript_input() -> None:
    html = _render('<c-CNumberInput name="quantity" c-show_controls="False" />')
    root = _tag(html, r'<div class="cui-number-input"[^>]*>')
    editor = _tag(html, r'<input id="cui-number-input-[^"]+"[^>]*>')
    assert "data-empty" in root
    assert 'name="quantity"' in editor
    assert 'value=""' in editor
    assert len(re.findall(r"<button[^>]+hidden[^>]*>", html)) == 2


def test_field_owns_state_and_editor_relationships() -> None:
    html = _render(
        """
          <c-CField control_id="quantity" required readonly invalid>
            <c-fill name="label">Quantity</c-fill>
            <c-fill name="default"><c-CNumberInput name="quantity" value="2" /></c-fill>
            <c-fill name="description">Whole crates</c-fill>
            <c-fill name="error">Check quantity</c-fill>
          </c-CField>
        """
    )
    editor = _tag(html, r'<input id="quantity"[^>]*>')
    assert "required" in editor
    assert "readonly" in editor
    assert 'aria-invalid="true"' in editor
    assert 'aria-describedby="quantity-description quantity-error"' in editor
    assert 'aria-errormessage="quantity-error"' in editor
    assert "data-citry-field-control" in editor
    assert 'for="quantity"' in html


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"value": 1.5}, TypeError, "int, Decimal"),
        ({"value": True}, TypeError, "int, Decimal"),
        ({"value": "1e3"}, ValueError, "plain-decimal"),
        ({"value": Decimal("NaN")}, ValueError, "finite"),
        ({"step": 0}, ValueError, "greater than zero"),
        ({"min": "2", "max": "1"}, ValueError, "min cannot be greater"),
        ({"value": "0", "min": "1"}, ValueError, "less than min"),
        ({"value": "11", "max": "10"}, ValueError, "greater than max"),
        ({"commit_behavior": "snap"}, ValueError, "must be one of"),
        ({"size": "xl"}, ValueError, "must be one of"),
        ({"attrs": []}, TypeError, "mapping or None"),
        ({"minimum_message": "Too small"}, ValueError, r"must contain \{min\}"),
        ({"step_message": "Use {step.__class__}"}, ValueError, "unsupported placeholder"),
    ],
)
def test_invalid_server_inputs_fail_deterministically(kwargs, error, match) -> None:
    with pytest.raises(error, match=match):
        _render('<c-CNumberInput c-bind="kwargs" />', {"kwargs": kwargs})


@pytest.mark.parametrize(
    ("destination", "attribute"),
    [
        ("attrs", "data-empty"),
        ("attrs", ":data-invalid"),
        ("attrs", "data-citry-hostile"),
        ("attrs", "x-model"),
        ("input_attrs", "id"),
        ("input_attrs", "role"),
        ("input_attrs", "aria-valuenow"),
        ("input_attrs", ":placeholder"),
        ("input_attrs", "data-citry-hostile"),
    ],
)
def test_owned_runtime_and_dynamic_attributes_are_rejected(destination: str, attribute: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(
            f'<c-CNumberInput c-{destination}="attributes" />',
            {"attributes": {attribute: "hostile"}},
        )


def test_explicit_translation_overrides_render_without_catalog_bindings() -> None:
    html = _render(
        """
          <c-CNumberInput
            increment_label="Add one"
            decrement_label="Take one"
            required_message="A number is required."
          />
        """
    )
    assert 'aria-label="Add one"' in html
    assert 'aria-label="Take one"' in html
    assert "data-citry-i18n-binding" not in html


def test_css_covers_public_variables_parts_and_environment_modes() -> None:
    css = read_component_source_css("cnumber_input")
    for variable in (
        "background",
        "foreground",
        "border-color",
        "focus-color",
        "invalid-border-color",
        "radius",
        "height",
        "inline-padding",
        "control-size",
    ):
        assert f"--cui-number-input-{variable}" in css
    for part in ("control", "input", "decrement", "increment"):
        assert f'data-citry-ui-part="{part}"' in css
    assert "pointer: coarse" in css
    assert "forced-colors: active" in css
    assert "@media print" in css


def test_messages_are_the_final_component_member() -> None:
    names = list(CNumberInput.__dict__)
    assert names.index("messages") > names.index("css_file")
    assert all(
        message in CNumberInput.messages
        for message in (
            "citry-ui-number-input-decrement",
            "citry-ui-number-input-increment",
            "citry-ui-number-input-required",
            "citry-ui-number-input-invalid",
            "citry-ui-number-input-minimum",
            "citry-ui-number-input-maximum",
            "citry-ui-number-input-step",
        )
    )
