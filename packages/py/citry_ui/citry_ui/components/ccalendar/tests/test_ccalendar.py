"""Focused server contracts for CCalendar."""

from __future__ import annotations

import re
from dataclasses import fields
from datetime import UTC, date, datetime

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.ccalendar import (
    CCalendar,
    CCalendarChangeSource,
    CCalendarDate,
    CCalendarSize,
    CCalendarValueChangeDetail,
    CCalendarVariant,
    CCalendarVisibleDateChangeDetail,
)
from citry_ui.components.cfield import CField
from citry_ui.components.cform import CForm
from citry_ui.quality.asset_sources import read_component_source_css


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-calendar-tests", (CForm, CField, CCalendar)))
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


def _root(html: str) -> str:
    match = re.search(r'<div class="cui-calendar[^>]*>', html)
    assert match is not None
    return match.group(0)


def _input(html: str) -> str:
    match = re.search(r'<input class="cui-calendar__fallback"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_public_schema_and_exports_are_exact() -> None:
    assert [field.name for field in fields(CCalendar.Kwargs)] == [
        "value",
        "visible_date",
        "name",
        "form",
        "id",
        "min",
        "max",
        "unavailable_dates",
        "required",
        "disabled",
        "readonly",
        "invalid",
        "first_day_of_week",
        "show_adjacent_days",
        "fixed_weeks",
        "label",
        "previous_label",
        "next_label",
        "unavailable_message",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert fields(CCalendar.Slots) == ()
    assert all(
        item is not None
        for item in (
            CCalendarDate,
            CCalendarChangeSource,
            CCalendarSize,
            CCalendarValueChangeDetail,
            CCalendarVariant,
            CCalendarVisibleDateChangeDetail,
        )
    )


def test_native_fallback_renders_canonical_form_contract_and_source_messages() -> None:
    html = _render(
        '<c-CCalendar id="delivery" name="delivery" form="order" value="2026-08-19" '
        'visible_date="2026-08-01" min="2026-08-01" max="2026-08-31" required '
        'c-first_day_of_week="1" variant="plain" size="lg" class_="brand-calendar" '
        'c-style="style" />',
        {"style": {"--cui-calendar-focus-color": "purple"}},
    )
    root = _root(html)
    control = _input(html)
    assert 'class="cui-calendar brand-calendar"' in root
    assert 'id="delivery-calendar"' in root
    assert 'role="group"' in root
    assert 'aria-label="Calendar"' in root
    assert 'data-variant="plain"' in root
    assert 'data-size="lg"' in root
    assert "--cui-calendar-focus-color: purple" in root
    assert 'id="delivery"' in control
    assert 'name="delivery"' in control
    assert 'form="order"' in control
    assert 'type="date"' in control
    assert 'value="2026-08-19"' in control
    assert 'min="2026-08-01"' in control
    assert 'max="2026-08-31"' in control
    assert "required" in control
    assert 'aria-label="Calendar"' in control
    assert 'aria-label="Previous month"' in html
    assert 'aria-label="Next month"' in html


def test_python_date_and_empty_value_are_canonical() -> None:
    populated = _input(_render('<c-CCalendar c-value="value" />', {"value": date(2024, 2, 29)}))
    assert 'value="2024-02-29"' in populated
    assert "data-empty" not in _root(_render('<c-CCalendar c-value="value" />', {"value": date(2024, 2, 29)}))
    html = _render("<c-CCalendar />")
    assert 'value=""' not in _input(html)
    assert "data-empty" in _root(html)


def test_authored_accessible_relationships_are_preserved() -> None:
    html = _render(
        '<c-CCalendar c-attrs="attrs" label="Ignored by authored label" />',
        {
            "attrs": {
                "aria-label": "Choose delivery day",
                "aria-describedby": "calendar-help",
                "aria-errormessage": "calendar-error",
            }
        },
    )
    root = _root(html)
    assert 'aria-label="Choose delivery day"' in root
    assert 'aria-describedby="calendar-help"' in root
    assert 'aria-errormessage="calendar-error"' not in root


def test_field_and_form_own_relationships_and_state() -> None:
    html = _render(
        """
          <c-CForm id="booking" readonly>
            <c-CField control_id="arrival" required invalid>
              <c-fill name="label">Arrival</c-fill>
              <c-fill name="description">Select the check-in day.</c-fill>
              <c-fill name="default"><c-CCalendar name="arrival" /></c-fill>
              <c-fill name="error">Choose an available date.</c-fill>
            </c-CField>
          </c-CForm>
        """
    )
    root = _root(html)
    control = _input(html)
    assert 'id="arrival-calendar"' in root
    assert 'aria-labelledby="arrival-label"' in root
    assert 'aria-describedby="arrival-description arrival-error"' in root
    assert 'aria-errormessage="arrival-error"' in root
    assert 'id="arrival"' in control
    assert 'name="arrival"' in control
    assert 'form="booking"' in control
    assert "required" in control
    assert "readonly" in control
    assert 'aria-invalid="true"' in control
    assert "data-citry-field-control" in control
    assert 'for="arrival"' in html


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"value": "2026-8-19"}, ValueError, "canonical YYYY-MM-DD"),
        ({"value": "2025-02-29"}, ValueError, "real calendar date"),
        ({"value": datetime(2026, 8, 19, tzinfo=UTC)}, TypeError, "exact date"),
        ({"min": "2026-09-01", "max": "2026-08-31"}, ValueError, "cannot be later"),
        ({"value": "2026-07-31", "min": "2026-08-01"}, ValueError, "earlier than min"),
        ({"value": "2026-09-01", "max": "2026-08-31"}, ValueError, "later than max"),
        ({"value": "2026-08-19", "unavailable_dates": ["2026-08-19"]}, ValueError, "unavailable"),
        ({"unavailable_dates": "2026-08-19"}, TypeError, "must be a sequence"),
        ({"unavailable_dates": ["2026-08-19", "2026-08-19"]}, ValueError, "duplicates"),
        ({"first_day_of_week": True}, TypeError, "exact integer"),
        ({"first_day_of_week": 0}, ValueError, "from 1 through 7"),
        ({"variant": "filled"}, ValueError, "must be one of"),
        ({"size": "xl"}, ValueError, "must be one of"),
        ({"attrs": []}, TypeError, "mapping or None"),
    ],
)
def test_invalid_server_inputs_fail_deterministically(kwargs, error, match) -> None:
    with pytest.raises(error, match=match):
        _render('<c-CCalendar c-bind="kwargs" />', {"kwargs": kwargs})


@pytest.mark.parametrize(
    "attribute",
    ["role", "tabindex", "data-empty", ":aria-disabled", "x-model", "data-citry-hostile"],
)
def test_owned_runtime_and_dynamic_attributes_are_rejected(attribute: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render('<c-CCalendar c-attrs="attrs" />', {"attrs": {attribute: "hostile"}})


def test_field_owned_state_label_and_cross_form_owner_conflicts_fail() -> None:
    with pytest.raises(ValueError, match="Field-owned state"):
        _render(
            '<c-CField><c-fill name="label">Date</c-fill>'
            '<c-fill name="default"><c-CCalendar required /></c-fill></c-CField>'
        )
    with pytest.raises(ValueError, match="use the CField label slot"):
        _render(
            '<c-CField><c-fill name="label">Date</c-fill>'
            '<c-fill name="default"><c-CCalendar label="Delivery" /></c-fill></c-CField>'
        )
    with pytest.raises(ValueError, match="different native form owner"):
        _render(
            '<c-CForm id="outer"><c-CField><c-fill name="label">Date</c-fill><c-fill name="default">'
            '<c-CCalendar form="other" /></c-fill></c-CField></c-CForm>'
        )


def test_catalog_overrides_replace_source_messages_without_registering_bindings() -> None:
    html = _render(
        '<c-CCalendar label="Dates" previous_label="Back" next_label="Forward" unavailable_message="Not this day" />'
    )
    assert 'aria-label="Dates"' in _root(html)
    assert 'aria-label="Back"' in html
    assert 'aria-label="Forward"' in html
    assert "data-citry-i18n-binding" not in html


def test_css_covers_public_variables_states_and_calendar_anatomy() -> None:
    css = read_component_source_css("ccalendar")
    for suffix in (
        "background",
        "foreground",
        "border-color",
        "focus-color",
        "selected-background",
        "selected-foreground",
        "today-color",
        "adjacent-color",
        "unavailable-color",
        "radius",
        "padding",
        "gap",
        "cell-size",
        "navigation-size",
        "font-size",
    ):
        assert f"--cui-calendar-{suffix}" in css
    for contract in (
        'data-variant="plain"',
        'data-size="sm"',
        'data-size="lg"',
        "data-selected",
        "data-today",
        "data-unavailable",
        "data-outside",
    ):
        assert contract in css
    assert "forced-colors: active" in css
    assert "prefers-reduced-motion: reduce" in css


def test_messages_are_the_final_component_member() -> None:
    names = list(CCalendar.__dict__)
    assert names.index("messages") > names.index("css_file")
    assert "citry-ui-calendar-label = Calendar" in CCalendar.messages
    assert "citry-ui-calendar-unavailable = Choose an available date." in CCalendar.messages
