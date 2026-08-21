"""Focused server contracts for CDatePicker."""

from __future__ import annotations

import re
from dataclasses import fields
from datetime import UTC, date, datetime

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.ccalendar import CCalendar
from citry_ui.components.cdate_picker import (
    CDatePicker,
    CDatePickerDate,
    CDatePickerOpenChangeDetail,
    CDatePickerSize,
    CDatePickerValueChangeDetail,
    CDatePickerValueChangeSource,
    CDatePickerVariant,
)
from citry_ui.components.cfield import CField
from citry_ui.components.cform import CForm
from citry_ui.components.cicon import CIcon
from citry_ui.components.cpopover import CPopover
from citry_ui.quality.asset_sources import read_component_source_css


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(
        ComponentLibrary(
            "citry-ui-date-picker-tests",
            (CForm, CField, CDatePicker, CCalendar, CPopover, CIcon),
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
    match = re.search(r'<div class="cui-date-picker[^>]*>', html)
    assert match is not None
    return match.group(0)


def _input(html: str) -> str:
    match = re.search(r'<input class="cui-date-picker__fallback"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_public_schema_and_exports_are_exact() -> None:
    assert [field.name for field in fields(CDatePicker.Kwargs)] == [
        "value",
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
        "clearable",
        "dismissible",
        "placement",
        "match_width",
        "first_day_of_week",
        "show_adjacent_days",
        "fixed_weeks",
        "placeholder",
        "picker_label",
        "change_label",
        "clear_label",
        "unavailable_message",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert fields(CDatePicker.Slots) == ()
    assert all(
        item is not None
        for item in (
            CDatePickerDate,
            CDatePickerOpenChangeDetail,
            CDatePickerSize,
            CDatePickerValueChangeDetail,
            CDatePickerValueChangeSource,
            CDatePickerVariant,
        )
    )


def test_native_fallback_and_composed_picker_render_exact_canonical_contract() -> None:
    html = _render(
        '<c-CDatePicker id="delivery" name="delivery" form="order" value="2026-08-19" '
        'min="2026-08-01" max="2026-08-31" required c-clearable="False" '
        'placement="top-end" c-match_width="False" c-first_day_of_week="1" '
        'variant="filled" size="lg" class_="brand-picker" c-style="style" />',
        {"style": {"--cui-date-picker-focus-color": "purple"}},
    )
    root = _root(html)
    control = _input(html)
    assert 'class="cui-date-picker brand-picker"' in root
    assert 'id="delivery-root"' in root
    assert "data-required" in root
    assert 'data-variant="filled"' in root
    assert 'data-size="lg"' in root
    assert "--cui-date-picker-focus-color: purple" in root
    assert 'id="delivery"' in control
    assert 'name="delivery"' in control
    assert 'form="order"' in control
    assert 'type="date"' in control
    assert 'value="2026-08-19"' in control
    assert 'min="2026-08-01"' in control
    assert 'max="2026-08-31"' in control
    assert "August 19, 2026" in html
    assert 'aria-label="Change date,' in html
    assert 'id="delivery-popover"' in html
    assert 'data-placement="top-end"' in html
    assert "data-match-width" not in html
    assert 'id="delivery-calendar-calendar"' in html
    assert '<button class="cui-date-picker__clear"' in html
    assert " hidden" in html


def test_empty_source_mode_renders_a_useful_native_input_and_picker_defaults() -> None:
    html = _render('<c-CDatePicker name="arrival" />')
    assert 'name="arrival"' in _input(html)
    assert "Choose a date" in html
    assert "Choose date" in html
    assert 'aria-label="Clear date"' in html
    assert 'aria-label="Calendar"' in html
    assert "data-empty" in _root(html)


def test_exact_dates_and_datetime_rejection() -> None:
    html = _render('<c-CDatePicker c-value="value" />', {"value": date(2024, 2, 29)})
    assert 'value="2024-02-29"' in _input(html)
    with pytest.raises(TypeError, match="exact date"):
        _render(
            '<c-CDatePicker c-value="value" />',
            {"value": datetime(2024, 2, 29, tzinfo=UTC)},
        )


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"value": "2026-02-30"}, ValueError, "real calendar date"),
        ({"min": "2026-09-01", "max": "2026-08-01"}, ValueError, "cannot be later"),
        ({"value": "2026-08-01", "min": "2026-08-02"}, ValueError, "earlier than min"),
        ({"value": "2026-08-03", "max": "2026-08-02"}, ValueError, "later than max"),
        ({"value": "2026-08-03", "unavailable_dates": ("2026-08-03",)}, ValueError, "unavailable_dates"),
        ({"unavailable_dates": ("2026-08-03", "2026-08-03")}, ValueError, "duplicates"),
        ({"first_day_of_week": 0}, ValueError, "from 1 through 7"),
        ({"first_day_of_week": True}, TypeError, "exact integer"),
        ({"placement": "sideways"}, ValueError, "placement"),
        ({"variant": "glass"}, ValueError, "variant"),
        ({"size": "xl"}, ValueError, "size"),
        ({"change_label": "Change date"}, ValueError, "{date}"),
    ],
)
def test_invalid_server_inputs_raise(kwargs: dict[str, object], error: type[Exception], message: str) -> None:
    with pytest.raises(error, match=re.escape(message)):
        _render('<c-CDatePicker c-bind="kwargs" />', {"kwargs": kwargs})


@pytest.mark.parametrize("attribute", ["id", "role", "data-enhanced", "data-citry-ui-part", "aria-invalid"])
def test_attrs_reject_owned_root_attributes(attribute: str) -> None:
    with pytest.raises(ValueError, match="cannot override owned attribute"):
        _render('<c-CDatePicker c-attrs="attrs" />', {"attrs": {attribute: "hostile"}})


def test_explicit_message_overrides_render_without_default_text() -> None:
    html = _render(
        '<c-CDatePicker value="2026-08-19" placeholder="Pick day" picker_label="Pick date" '
        'change_label="Edit {date}" clear_label="Remove day" unavailable_message="Blocked" />'
    )
    assert "Edit August 19, 2026" in html
    assert "Pick date" in html
    assert 'aria-label="Remove day"' in html
    assert "Choose date" not in html
    assert "Clear date" not in html


def test_field_and_form_have_one_control_while_calendar_is_context_isolated() -> None:
    html = _render(
        """
        <c-CForm id="order">
          <c-CField control_id="arrival" required>
            <c-fill name="label">Arrival</c-fill>
            <c-fill name="description">Choose one day.</c-fill>
            <c-fill name="default"><c-CDatePicker name="arrival" /></c-fill>
          </c-CField>
        </c-CForm>
        """
    )
    control = _input(html)
    assert 'id="arrival"' in control
    assert 'name="arrival"' in control
    assert 'form="order"' in control
    assert "required" in control
    assert "data-citry-field-control" in control
    assert html.count("data-citry-field-control") == 1
    assert 'id="arrival-calendar-calendar"' in html
    assert 'id="arrival-calendar" type="date"' in html
    assert 'name="arrival"' not in html.split('id="arrival-calendar"', 1)[1].split("/>", 1)[0]


def test_field_rejects_duplicate_state_and_id_or_form_ownership() -> None:
    with pytest.raises(ValueError, match="Field-owned state"):
        _render(
            '<c-CField><c-fill name="label">Arrival</c-fill><c-fill name="default">'
            "<c-CDatePicker required /></c-fill></c-CField>"
        )
    with pytest.raises(ValueError, match="conflicts"):
        _render(
            '<c-CField control_id="field-date"><c-fill name="label">Arrival</c-fill>'
            '<c-fill name="default"><c-CDatePicker id="other" /></c-fill></c-CField>'
        )
    with pytest.raises(ValueError, match="different native form owner"):
        _render(
            '<c-CForm id="order"><c-CField><c-fill name="label">Arrival</c-fill>'
            '<c-fill name="default"><c-CDatePicker form="other" /></c-fill></c-CField></c-CForm>'
        )


def test_css_contains_public_variables_and_progressive_enhancement_contract() -> None:
    css = read_component_source_css("cdate_picker")
    for token in (
        "--cui-date-picker-background",
        "--cui-date-picker-foreground",
        "--cui-date-picker-border-color",
        "--cui-date-picker-invalid-border-color",
        "--cui-date-picker-focus-color",
        "--cui-date-picker-radius",
        "--cui-date-picker-min-block-size",
        "--cui-date-picker-padding-inline",
        "--cui-date-picker-gap",
    ):
        assert token in css
    assert "data-enhanced" in css
    assert "forced-colors" in css
    assert "pointer: coarse" in css
    assert "@media print" in css


def test_messages_are_the_final_class_member_and_source_locale_is_explicit() -> None:
    keys = list(CDatePicker.__dict__)
    assert keys.index("messages") > keys.index("css_file")
    assert CDatePicker.I18n.messages_locale == "en-US"
    assert "citry-ui-date-picker-placeholder" in CDatePicker.messages
    assert "citry-ui-date-picker-change" in CDatePicker.messages
    assert "citry-ui-date-picker-unavailable" in CDatePicker.messages
