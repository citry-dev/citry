"""Focused server contracts for CDateInput."""

from __future__ import annotations

import re
from dataclasses import fields
from datetime import UTC, date, datetime

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cdate_input import CDateInput, CDateInputSize, CDateInputValue, CDateInputVariant
from citry_ui.components.cfield import CField
from citry_ui.components.cform import CForm


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-date-input-tests", (CForm, CField, CDateInput)))
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
    match = re.search(r'<input class="cui-date-input[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_public_schema_and_exports_are_exact() -> None:
    assert [field.name for field in fields(CDateInput.Kwargs)] == [
        "value", "name", "form", "id", "min", "max", "step", "required", "disabled", "readonly",
        "invalid", "autocomplete", "variant", "size", "class_", "style", "attrs",
    ]
    assert fields(CDateInput.Slots) == ()
    assert all(item is not None for item in (CDateInputValue, CDateInputSize, CDateInputVariant))


def test_native_date_renders_canonical_form_contract() -> None:
    html = _render(
        '<c-CDateInput id="delivery" name="delivery" form="order" value="2026-08-19" '
        'min="2026-08-01" max="2026-08-31" c-step="2" required autocomplete="bday" '
        'variant="filled" size="lg" class_="brand-date" c-style="style" />',
        {"style": {"--cui-date-input-focus-color": "purple"}},
    )
    control = _input(html)
    assert 'class="cui-date-input brand-date"' in control
    assert 'id="delivery"' in control
    assert 'name="delivery"' in control
    assert 'form="order"' in control
    assert 'type="date"' in control
    assert 'value="2026-08-19"' in control
    assert 'min="2026-08-01"' in control
    assert 'max="2026-08-31"' in control
    assert 'step="2"' in control
    assert "required" in control
    assert 'autocomplete="bday"' in control
    assert 'data-variant="filled"' in control
    assert 'data-size="lg"' in control
    assert "--cui-date-input-focus-color: purple" in control


def test_python_date_and_empty_value_are_canonical() -> None:
    populated = _input(_render('<c-CDateInput c-value="value" />', {"value": date(2024, 2, 29)}))
    assert 'value="2024-02-29"' in populated
    assert "data-empty" not in populated
    empty = _input(_render("<c-CDateInput />"))
    assert 'value=""' not in empty
    assert "data-empty" in empty


def test_field_and_form_own_relationships_and_state() -> None:
    html = _render(
        """
          <c-CForm id="booking" readonly>
            <c-CField control_id="arrival" required invalid>
              <c-fill name="label">Arrival</c-fill>
              <c-fill name="description">Select the check-in day.</c-fill>
              <c-fill name="default"><c-CDateInput name="arrival" /></c-fill>
              <c-fill name="error">Choose an available date.</c-fill>
            </c-CField>
          </c-CForm>
        """
    )
    control = _input(html)
    assert 'id="arrival"' in control
    assert 'name="arrival"' in control
    assert 'form="booking"' in control
    assert "required" in control
    assert "readonly" in control
    assert 'aria-invalid="true"' in control
    assert 'aria-describedby="arrival-description arrival-error"' in control
    assert 'aria-errormessage="arrival-error"' in control
    assert "data-citry-field-control" in control
    assert 'for="arrival"' in html


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"value": "2026-8-19"}, ValueError, "canonical YYYY-MM-DD"),
        ({"value": "2025-02-29"}, ValueError, "real calendar date"),
        ({"value": datetime(2026, 8, 19, tzinfo=UTC)}, TypeError, "exact date"),
        ({"value": 20260819}, TypeError, "exact date"),
        ({"min": "2026-09-01", "max": "2026-08-31"}, ValueError, "cannot be later"),
        ({"step": True}, TypeError, "exact positive integer"),
        ({"step": 0}, ValueError, "greater than zero"),
        ({"variant": "soft"}, ValueError, "must be one of"),
        ({"size": "xl"}, ValueError, "must be one of"),
        ({"attrs": []}, TypeError, "mapping or None"),
    ],
)
def test_invalid_server_inputs_fail_deterministically(kwargs, error, match) -> None:
    with pytest.raises(error, match=match):
        _render('<c-CDateInput c-bind="kwargs" />', {"kwargs": kwargs})


@pytest.mark.parametrize("attribute", ["type", "value", "data-empty", ":min", "x-model", "data-citry-hostile"])
def test_owned_runtime_and_dynamic_attributes_are_rejected(attribute: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render('<c-CDateInput c-attrs="attrs" />', {"attrs": {attribute: "hostile"}})


def test_field_owned_state_and_cross_form_owner_conflicts_fail() -> None:
    with pytest.raises(ValueError, match="Field-owned state"):
        _render(
            '<c-CField><c-fill name="label">Date</c-fill>'
            '<c-fill name="default"><c-CDateInput required /></c-fill></c-CField>'
        )
    with pytest.raises(ValueError, match="different native form owner"):
        _render(
            '<c-CForm id="outer"><c-CField><c-fill name="label">Date</c-fill><c-fill name="default">'
            '<c-CDateInput form="other" /></c-fill></c-CField></c-CForm>'
        )


def test_css_covers_public_variables_states_and_native_affordance() -> None:
    css = _render("<c-CDateInput />", css=True)
    for suffix in (
        "background", "foreground", "border-color", "hover-border-color", "focus-color",
        "invalid-border-color", "disabled-background", "radius", "height", "inline-padding",
        "block-padding", "font-size", "min-inline-size",
    ):
        assert f"--cui-date-input-{suffix}" in css
    for contract in ('data-variant="filled"', 'data-variant="plain"', 'data-size="sm"', 'data-size="lg"'):
        assert contract in css
    assert "forced-colors: active" in css
    assert "appearance: none" not in css


def test_family_has_no_catalog_messages_or_browser_binding() -> None:
    html = _render("<c-CDateInput />")
    assert not hasattr(CDateInput, "messages")
    assert "data-citry-i18n-binding" not in html
