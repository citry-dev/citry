"""Focused server contracts for CTimeInput."""

from __future__ import annotations

import re
from dataclasses import fields
from datetime import time, timezone

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cfield import CField
from citry_ui.components.cform import CForm
from citry_ui.components.ctime_input import CTimeInput, CTimeInputSize, CTimeInputValue, CTimeInputVariant
from citry_ui.quality.asset_sources import read_component_source_css


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-time-input-tests", (CForm, CField, CTimeInput)))
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
    match = re.search(r'<input class="cui-time-input[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_public_schema_and_exports_are_exact() -> None:
    assert [field.name for field in fields(CTimeInput.Kwargs)] == [
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
        "autocomplete",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert fields(CTimeInput.Slots) == ()
    assert all(item is not None for item in (CTimeInputValue, CTimeInputSize, CTimeInputVariant))


def test_native_time_renders_canonical_form_contract() -> None:
    html = _render(
        '<c-CTimeInput id="start" name="start" form="order" value="09:30:15" '
        'min="20:00" max="08:00" c-step="15" required autocomplete="off" '
        'variant="filled" size="lg" class_="brand-time" c-style="style" />',
        {"style": {"--cui-time-input-focus-color": "purple"}},
    )
    control = _input(html)
    for contract in (
        'class="cui-time-input brand-time"',
        'id="start"',
        'name="start"',
        'form="order"',
        'type="time"',
        'value="09:30:15"',
        'min="20:00"',
        'max="08:00"',
        'step="15"',
        'autocomplete="off"',
        'data-variant="filled"',
        'data-size="lg"',
    ):
        assert contract in control
    assert "required" in control
    assert "--cui-time-input-focus-color: purple" in control


def test_python_time_seconds_and_empty_value_are_canonical() -> None:
    populated = _input(_render('<c-CTimeInput c-value="value" />', {"value": time(23, 59, 7)}))
    assert 'value="23:59:07"' in populated
    assert "data-empty" not in populated
    minute = _input(_render('<c-CTimeInput c-value="value" />', {"value": time(9, 5)}))
    assert 'value="09:05"' in minute
    empty = _input(_render("<c-CTimeInput />"))
    assert 'step="60"' in empty
    assert "data-empty" in empty


def test_field_and_form_own_relationships_and_state() -> None:
    html = _render(
        """
          <c-CForm id="booking" readonly>
            <c-CField control_id="arrival" required invalid>
              <c-fill name="label">Arrival time</c-fill>
              <c-fill name="description">Choose a check-in time.</c-fill>
              <c-fill name="default"><c-CTimeInput name="arrival" /></c-fill>
              <c-fill name="error">Choose an available time.</c-fill>
            </c-CField>
          </c-CForm>
        """
    )
    control = _input(html)
    for contract in (
        'id="arrival"',
        'name="arrival"',
        'form="booking"',
        'aria-invalid="true"',
        'aria-describedby="arrival-description arrival-error"',
        'aria-errormessage="arrival-error"',
        "data-citry-field-control",
    ):
        assert contract in control
    assert "required" in control
    assert "readonly" in control
    assert 'for="arrival"' in html


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"value": "9:30"}, ValueError, "canonical HH:MM"),
        ({"value": "24:00"}, ValueError, "real wall-clock"),
        ({"value": time(9, tzinfo=timezone.utc)}, ValueError, "zone-free"),
        ({"value": time(9, microsecond=1)}, ValueError, "fractional"),
        ({"value": 930}, TypeError, "time or canonical"),
        ({"step": True}, TypeError, "exact positive integer"),
        ({"step": 0}, ValueError, "greater than zero"),
        ({"variant": "soft"}, ValueError, "must be one of"),
        ({"size": "xl"}, ValueError, "must be one of"),
        ({"attrs": []}, TypeError, "mapping or None"),
    ],
)
def test_invalid_server_inputs_fail_deterministically(kwargs, error, match) -> None:
    with pytest.raises(error, match=match):
        _render('<c-CTimeInput c-bind="kwargs" />', {"kwargs": kwargs})


@pytest.mark.parametrize("attribute", ["type", "value", "data-empty", ":min", "x-model", "data-citry-hostile"])
def test_owned_runtime_and_dynamic_attributes_are_rejected(attribute: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render('<c-CTimeInput c-attrs="attrs" />', {"attrs": {attribute: "hostile"}})


def test_field_owned_state_and_cross_form_owner_conflicts_fail() -> None:
    with pytest.raises(ValueError, match="Field-owned state"):
        _render(
            '<c-CField><c-fill name="label">Time</c-fill>'
            '<c-fill name="default"><c-CTimeInput required /></c-fill></c-CField>'
        )
    with pytest.raises(ValueError, match="different native form owner"):
        _render(
            '<c-CForm id="outer"><c-CField><c-fill name="label">Time</c-fill><c-fill name="default">'
            '<c-CTimeInput form="other" /></c-fill></c-CField></c-CForm>'
        )


def test_css_and_message_contract() -> None:
    css = read_component_source_css("ctime_input")
    for suffix in (
        "background",
        "foreground",
        "border-color",
        "hover-border-color",
        "focus-color",
        "invalid-border-color",
        "disabled-background",
        "radius",
        "height",
        "inline-padding",
        "block-padding",
        "font-size",
        "min-inline-size",
    ):
        assert f"--cui-time-input-{suffix}" in css
    assert "forced-colors: active" in css
    assert "appearance: none" not in css
    assert not hasattr(CTimeInput, "messages")
    assert "data-citry-i18n-binding" not in _render("<c-CTimeInput />")
