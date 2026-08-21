"""Focused server contracts for CTimePicker."""

from __future__ import annotations

import re
from dataclasses import fields
from datetime import time, timezone

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cfield import CField
from citry_ui.components.cform import CForm
from citry_ui.components.cicon import CIcon
from citry_ui.components.clistbox import CListbox, CListboxOption
from citry_ui.components.cpopover import CPopover
from citry_ui.components.ctime_picker import (
    CTimePicker,
    CTimePickerOpenChangeDetail,
    CTimePickerSize,
    CTimePickerTime,
    CTimePickerValueChangeDetail,
    CTimePickerValueChangeSource,
    CTimePickerVariant,
)
from citry_ui.quality.asset_sources import read_component_source_css


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(
        ComponentLibrary(
            "citry-ui-time-picker-tests",
            (CForm, CField, CTimePicker, CPopover, CListbox, CListboxOption, CIcon),
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
    match = re.search(r'<div class="cui-time-picker[^>]*>', html)
    assert match is not None
    return match.group(0)


def _input(html: str) -> str:
    match = re.search(r'<input class="cui-time-picker__fallback"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_public_schema_and_exports_are_exact() -> None:
    assert [field.name for field in fields(CTimePicker.Kwargs)] == [
        "value",
        "name",
        "form",
        "id",
        "min",
        "max",
        "step",
        "options",
        "required",
        "disabled",
        "readonly",
        "invalid",
        "clearable",
        "dismissible",
        "placement",
        "match_width",
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
    assert fields(CTimePicker.Slots) == ()
    assert all(
        item is not None
        for item in (
            CTimePickerTime,
            CTimePickerOpenChangeDetail,
            CTimePickerSize,
            CTimePickerValueChangeDetail,
            CTimePickerValueChangeSource,
            CTimePickerVariant,
        )
    )


def test_native_fallback_and_composed_picker_render_exact_contract() -> None:
    html = _render(
        '<c-CTimePicker id="start" name="start" form="order" value="09:30" min="09:00" '
        'max="10:00" c-step="1800" required c-clearable="False" placement="top-end" '
        'c-match_width="False" variant="filled" size="lg" class_="brand-picker" c-style="style" />',
        {"style": {"--cui-time-picker-focus-color": "purple"}},
    )
    root = _root(html)
    control = _input(html)
    for contract in (
        'class="cui-time-picker brand-picker"',
        'id="start-root"',
        'data-variant="filled"',
        'data-size="lg"',
        "--cui-time-picker-focus-color: purple",
    ):
        assert contract in root
    for contract in (
        'id="start"',
        'name="start"',
        'form="order"',
        'type="time"',
        'value="09:30"',
        'min="09:00"',
        'max="10:00"',
        'step="1800"',
    ):
        assert contract in control
    assert "required" in root
    assert "9:30 AM" in html
    assert 'aria-label="Change time,' in html
    assert 'id="start-popover"' in html
    assert 'data-placement="top-end"' in html
    assert "data-match-width" not in html
    assert html.count('data-citry-ui-part="listbox-option"') == 3
    assert 'data-name="clock"' in html
    assert " hidden" in html


def test_explicit_options_preserve_order_seconds_and_native_any_step() -> None:
    html = _render(
        '<c-CTimePicker c-value="value" c-options="options" />',
        {"value": time(23, 5, 9), "options": ("23:05:09", time(0, 0, 10), "12:30:45")},
    )
    assert 'value="23:05:09"' in _input(html)
    assert 'step="any"' in _input(html)
    assert html.index('data-value="23:05:09"') < html.index('data-value="00:00:10"')
    assert "11:05:09 PM" in html
    assert "12:00:10 AM" in html


def test_wrapped_interval_generates_across_midnight() -> None:
    html = _render('<c-CTimePicker min="23:00" max="01:00" c-step="3600" />')
    for value in ("23:00", "00:00", "01:00"):
        assert f'data-value="{value}"' in html
    assert html.count('data-citry-ui-part="listbox-option"') == 3


def test_empty_source_mode_and_explicit_overrides_are_useful() -> None:
    empty = _render('<c-CTimePicker name="start" />')
    assert 'name="start"' in _input(empty)
    assert "Choose a time" in empty
    assert "Choose time" in empty
    assert 'aria-label="Clear time"' in empty
    assert "data-empty" in _root(empty)
    overridden = _render(
        '<c-CTimePicker value="09:00" c-options="(\'09:00\',)" placeholder="Pick hour" '
        'picker_label="Pick time" change_label="Edit {time}" clear_label="Remove time" '
        'unavailable_message="Blocked" />'
    )
    assert "Edit 9:00 AM" in overridden
    assert "Pick time" in overridden
    assert 'aria-label="Remove time"' in overridden
    assert "Choose time" not in overridden


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"value": "24:00"}, ValueError, "real wall-clock"),
        ({"value": time(9, tzinfo=timezone.utc)}, ValueError, "zone-free"),
        ({"step": True}, TypeError, "exact integer"),
        ({"step": 299}, ValueError, "at least 300"),
        ({"options": ()}, ValueError, "at least one"),
        ({"options": ("09:00", "09:00")}, ValueError, "duplicates"),
        ({"options": ("08:00",), "min": "09:00"}, ValueError, "inside the min/max"),
        ({"value": "09:15", "options": ("09:00", "09:30")}, ValueError, "must equal"),
        ({"placement": "sideways"}, ValueError, "placement"),
        ({"variant": "glass"}, ValueError, "variant"),
        ({"size": "xl"}, ValueError, "size"),
        ({"change_label": "Change time"}, ValueError, "{time}"),
    ],
)
def test_invalid_server_inputs_raise(kwargs: dict[str, object], error: type[Exception], message: str) -> None:
    with pytest.raises(error, match=re.escape(message)):
        _render('<c-CTimePicker c-bind="kwargs" />', {"kwargs": kwargs})


@pytest.mark.parametrize("attribute", ["id", "role", "data-enhanced", "data-citry-ui-part", "aria-invalid"])
def test_attrs_reject_owned_root_attributes(attribute: str) -> None:
    with pytest.raises(ValueError, match="cannot override owned attribute"):
        _render('<c-CTimePicker c-attrs="attrs" />', {"attrs": {attribute: "hostile"}})


def test_field_and_form_have_one_control_while_listbox_is_context_isolated() -> None:
    html = _render(
        """
        <c-CForm id="order">
          <c-CField control_id="start" required>
            <c-fill name="label">Start time</c-fill>
            <c-fill name="description">Choose one time.</c-fill>
            <c-fill name="default"><c-CTimePicker name="start" min="09:00" max="10:00" /></c-fill>
          </c-CField>
        </c-CForm>
        """
    )
    control = _input(html)
    for contract in ('id="start"', 'name="start"', 'form="order"', "required", "data-citry-field-control"):
        assert contract in control
    assert html.count("data-citry-field-control") == 1
    assert 'role="listbox"' in html
    assert 'name="start"' not in html.split('role="listbox"', 1)[1]


def test_field_rejects_duplicate_state_and_id_or_form_ownership() -> None:
    with pytest.raises(ValueError, match="Field-owned state"):
        _render(
            '<c-CField><c-fill name="label">Start</c-fill><c-fill name="default">'
            "<c-CTimePicker required /></c-fill></c-CField>"
        )
    with pytest.raises(ValueError, match="conflicts"):
        _render(
            '<c-CField control_id="field-time"><c-fill name="label">Start</c-fill>'
            '<c-fill name="default"><c-CTimePicker id="other" /></c-fill></c-CField>'
        )
    with pytest.raises(ValueError, match="different native form owner"):
        _render(
            '<c-CForm id="order"><c-CField><c-fill name="label">Start</c-fill>'
            '<c-fill name="default"><c-CTimePicker form="other" /></c-fill></c-CField></c-CForm>'
        )


def test_css_messages_and_profiles_are_explicit() -> None:
    css = read_component_source_css("ctime_picker")
    for token in (
        "--cui-time-picker-background",
        "--cui-time-picker-foreground",
        "--cui-time-picker-border-color",
        "--cui-time-picker-invalid-border-color",
        "--cui-time-picker-focus-color",
        "--cui-time-picker-radius",
        "--cui-time-picker-min-block-size",
        "--cui-time-picker-padding-inline",
        "--cui-time-picker-gap",
        "--cui-time-picker-list-max-block-size",
    ):
        assert token in css
    assert "forced-colors" in css
    assert "pointer: coarse" in css
    assert "@media print" in css
    keys = list(CTimePicker.__dict__)
    assert keys.index("messages") > keys.index("css_file")
    assert CTimePicker.I18n.messages_locale == "en-US"
    assert "citry-ui-time-picker-placeholder" in CTimePicker.messages
    assert "citry-ui-time-picker-change" in CTimePicker.messages
    assert "citry-ui-time-picker-unavailable" in CTimePicker.messages
