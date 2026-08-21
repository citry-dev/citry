"""Focused server contracts for CDateRange."""

from __future__ import annotations

import re
from dataclasses import fields
from datetime import date, datetime, timezone

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.ccalendar import CCalendar
from citry_ui.components.cdate_range import (
    CDateRange,
    CDateRangeDate,
    CDateRangeOpenChangeDetail,
    CDateRangeSize,
    CDateRangeValue,
    CDateRangeValueChangeDetail,
    CDateRangeValueChangeSource,
    CDateRangeVariant,
)
from citry_ui.components.cfield import CField
from citry_ui.components.cform import CForm
from citry_ui.components.cicon import CIcon
from citry_ui.components.cpopover import CPopover


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(
        ComponentLibrary(
            "citry-ui-date-range-tests",
            (CForm, CField, CDateRange, CPopover, CCalendar, CIcon),
        )
    )
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
    match = re.search(r'<div class="cui-date-range[^>]*>', html)
    assert match is not None
    return match.group(0)


def _input(html: str, part: str) -> str:
    match = re.search(rf'<input[^>]*data-citry-ui-part="{part}"[^>]*/?>', html)
    assert match is not None
    return match.group(0)


def test_public_schema_and_exports_are_exact() -> None:
    assert [field.name for field in fields(CDateRange.Kwargs)] == [
        "start",
        "end",
        "start_name",
        "end_name",
        "form",
        "id",
        "min",
        "max",
        "unavailable_dates",
        "required",
        "disabled",
        "readonly",
        "invalid",
        "clearable",
        "dismissible",
        "placement",
        "match_width",
        "first_day_of_week",
        "show_adjacent_days",
        "fixed_weeks",
        "placeholder",
        "range_label",
        "change_label",
        "start_label",
        "end_label",
        "clear_label",
        "unavailable_message",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert fields(CDateRange.Slots) == ()
    assert all(
        item is not None
        for item in (
            CDateRangeDate,
            CDateRangeOpenChangeDetail,
            CDateRangeSize,
            CDateRangeValue,
            CDateRangeValueChangeDetail,
            CDateRangeValueChangeSource,
            CDateRangeVariant,
        )
    )


def test_two_native_fallbacks_and_one_composed_range_picker_render() -> None:
    html = _render(
        '<c-CDateRange id="trip" start_name="departure" end_name="return" '
        'start="2026-08-19" end="2026-08-24" min="2026-08-01" max="2026-09-15" '
        'required placement="top-end" c-match_width="False" variant="filled" size="lg" '
        'class_="brand-range" c-style="style" />',
        {"style": {"--cui-date-range-focus-color": "purple"}},
    )
    root = _root(html)
    for contract in (
        'class="cui-date-range brand-range"',
        'id="trip-root"',
        'role="group"',
        'aria-label="Choose date range"',
        'data-variant="filled"',
        'data-size="lg"',
        "--cui-date-range-focus-color: purple",
    ):
        assert contract in root
    start = _input(html, "start-input")
    end = _input(html, "end-input")
    for contract in (
        'id="trip-start"',
        'name="departure"',
        'value="2026-08-19"',
        'min="2026-08-01"',
        'max="2026-08-24"',
        "required",
    ):
        assert contract in start
    for contract in (
        'id="trip-end"',
        'name="return"',
        'value="2026-08-24"',
        'min="2026-08-19"',
        'max="2026-09-15"',
        "required",
    ):
        assert contract in end
    assert "August 19, 2026" in html
    assert "August 24, 2026" in html
    assert 'id="trip-popover"' in html
    assert 'data-placement="top-end"' in html
    assert "data-match-width" not in html
    assert 'id="trip-calendar-calendar"' in html
    assert 'data-name="calendar"' in html
    assert html.count('data-citry-ui-part="start-input"') == 1
    assert html.count('data-citry-ui-part="end-input"') == 1


def test_python_dates_empty_source_mode_and_explicit_text_overrides() -> None:
    html = _render(
        '<c-CDateRange c-start="start" c-end="end" placeholder="Pick interval" '
        'range_label="Travel window" change_label="Edit {start} until {end}" '
        'start_label="From" end_label="Through" clear_label="Remove interval" '
        'unavailable_message="Blocked interval" />',
        {"start": date(2026, 8, 19), "end": date(2026, 8, 24)},
    )
    assert "Edit August 19, 2026 until August 24, 2026" in html
    assert ">From<" in html
    assert ">Through<" in html
    assert 'aria-label="Remove interval"' in html
    empty = _render('<c-CDateRange start_name="start" end_name="end" />')
    assert "Choose dates" in empty
    assert "data-empty" in _root(empty)
    assert 'name="start"' in _input(empty, "start-input")
    assert 'name="end"' in _input(empty, "end-input")


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"start": "2026-08-19"}, ValueError, "both be provided"),
        ({"end": "2026-08-19"}, ValueError, "both be provided"),
        ({"start": "2026-08-24", "end": "2026-08-19"}, ValueError, "later than end"),
        ({"start": "2026-07-31", "end": "2026-08-02", "min": "2026-08-01"}, ValueError, "earlier than min"),
        ({"start": "2026-08-19", "end": "2026-09-16", "max": "2026-09-15"}, ValueError, "later than max"),
        (
            {"start": "2026-08-19", "end": "2026-08-24", "unavailable_dates": ("2026-08-21",)},
            ValueError,
            "include an unavailable",
        ),
        (
            {"start": datetime(2026, 8, 19, tzinfo=timezone.utc), "end": "2026-08-24"},
            TypeError,
            "must be an exact date",
        ),
        ({"unavailable_dates": "2026-08-21"}, TypeError, "must be a sequence"),
        ({"unavailable_dates": ("2026-08-21", "2026-08-21")}, ValueError, "duplicates"),
        ({"start_name": "same", "end_name": "same"}, ValueError, "must be different"),
        ({"first_day_of_week": 0}, ValueError, "from 1 through 7"),
        ({"placement": "sideways"}, ValueError, "placement"),
        ({"variant": "glass"}, ValueError, "variant"),
        ({"size": "xl"}, ValueError, "size"),
        ({"change_label": "Change dates"}, ValueError, "both {start} and {end}"),
    ],
)
def test_invalid_server_inputs_raise(kwargs: dict[str, object], error: type[Exception], message: str) -> None:
    with pytest.raises(error, match=re.escape(message)):
        _render('<c-CDateRange c-bind="kwargs" />', {"kwargs": kwargs})


@pytest.mark.parametrize("attribute", ["id", "role", "data-enhanced", "data-citry-ui-part", "aria-invalid"])
def test_attrs_reject_owned_root_attributes(attribute: str) -> None:
    with pytest.raises(ValueError, match="cannot override owned attribute"):
        _render('<c-CDateRange c-attrs="attrs" />', {"attrs": {attribute: "hostile"}})


def test_accessible_name_override_and_form_owner_work_without_field() -> None:
    html = _render(
        '<c-CForm id="booking"><c-CDateRange start_name="from" end_name="to" '
        "c-attrs=\"{'aria-label':'Stay dates','data-track':'range'}\" /></c-CForm>"
    )
    assert 'aria-label="Stay dates"' in _root(html)
    assert 'data-track="range"' in _root(html)
    assert 'form="booking"' in _input(html, "start-input")
    assert 'form="booking"' in _input(html, "end-input")


def test_date_range_rejects_single_control_field_composition() -> None:
    with pytest.raises(ValueError, match="cannot compose inside CField"):
        _render(
            '<c-CField><c-fill name="label">Dates</c-fill><c-fill name="default"><c-CDateRange /></c-fill></c-CField>'
        )


def test_css_messages_and_dependencies_are_explicit() -> None:
    css = _render("<c-CDateRange />", css=True)
    for token in (
        "--cui-date-range-background",
        "--cui-date-range-foreground",
        "--cui-date-range-border-color",
        "--cui-date-range-focus-color",
        "--cui-date-range-range-background",
        "--cui-date-range-endpoint-background",
        "--cui-date-range-endpoint-foreground",
        "--cui-date-range-radius",
        "--cui-date-range-min-block-size",
        "--cui-date-range-padding-inline",
        "--cui-date-range-gap",
    ):
        assert token in css
    assert CDateRange.Dependencies.js
    assert CDateRange.Dependencies.css
    assert "citry-ui-date-range-change" in CDateRange.messages
    assert CDateRange.messages.rstrip().endswith("citry-ui-date-range-unavailable = Choose an available date range.")
