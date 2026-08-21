"""Focused server contracts for CSlider and CRangeSlider."""

from __future__ import annotations

import re
from dataclasses import fields
from decimal import Decimal

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cfield import CField
from citry_ui.components.cslider import (
    CRangeSlider,
    CRangeSliderThumb,
    CRangeSliderValueChangeDetail,
    CSlider,
    CSliderChangePhase,
    CSliderChangeSource,
    CSliderExact,
    CSliderOrientation,
    CSliderShowValue,
    CSliderSize,
    CSliderValueChangeDetail,
    CSliderVariant,
)
from citry_ui.quality.asset_sources import read_component_source_css


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-slider-tests", (CField, CSlider, CRangeSlider)))
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


def test_public_schemas_and_exports_are_exact() -> None:
    assert [field.name for field in fields(CSlider.Kwargs)] == [
        "value",
        "name",
        "form",
        "id",
        "min",
        "max",
        "step",
        "large_step",
        "disabled",
        "readonly",
        "invalid",
        "orientation",
        "variant",
        "size",
        "show_value",
        "show_marks",
        "marks",
        "format",
        "class_",
        "style",
        "attrs",
        "input_attrs",
    ]
    assert [field.name for field in fields(CRangeSlider.Kwargs)] == [
        "value",
        "name",
        "lower_name",
        "upper_name",
        "form",
        "id",
        "min",
        "max",
        "step",
        "large_step",
        "min_steps_between_thumbs",
        "disabled",
        "readonly",
        "invalid",
        "orientation",
        "variant",
        "size",
        "show_value",
        "show_marks",
        "marks",
        "format",
        "lower_label",
        "upper_label",
        "class_",
        "style",
        "attrs",
        "lower_input_attrs",
        "upper_input_attrs",
    ]
    assert fields(CSlider.Slots) == ()
    assert fields(CRangeSlider.Slots) == ()
    assert all(
        item is not None
        for item in (
            CSliderExact,
            CSliderOrientation,
            CSliderVariant,
            CSliderSize,
            CSliderShowValue,
            CSliderChangeSource,
            CSliderChangePhase,
            CRangeSliderThumb,
            CSliderValueChangeDetail,
            CRangeSliderValueChangeDetail,
        )
    )


def test_slider_exact_decimal_progressive_anatomy_and_marks() -> None:
    html = _render(
        '<c-CSlider id="volume" name="volume" form="settings" value="0.30" min="0.1" max="0.5" '
        'step="0.05" c-marks="marks" class_="volume" c-style="style" />',
        {"marks": {Decimal("0.10"): "Quiet", "0.30": "Medium", "0.5": "Loud"}, "style": {"inline-size": "20rem"}},
    )
    root = _tag(html, r'<div class="cui-slider volume"[^>]*>')
    native = _tag(html, r'<input id="volume"[^>]*>')
    transport = _tag(html, r'<input id="volume-readonly"[^>]*>')
    assert 'data-citry-ui-part="slider"' in root
    assert 'style="inline-size: 20rem;"' in root
    assert 'name="volume"' in native
    assert 'form="settings"' in native
    assert 'min="0.1"' in native
    assert 'max="0.5"' in native
    assert 'step="0.05"' in native
    assert 'value="0.3"' in native
    assert 'type="hidden" disabled' in transport
    assert html.count('data-citry-ui-part="mark"') == 3
    assert "Quiet" in html
    assert "Medium" in html
    assert "Loud" in html


def test_range_has_fixed_thumb_identity_names_and_accessible_labels() -> None:
    html = _render(
        '<c-CRangeSlider id="price" lower_name="minimum" upper_name="maximum" '
        'c-value="(20, 80)" c-min_steps_between_thumbs="5" />'
    )
    root = _tag(html, r'<div class="cui-slider" id="price-root"[^>]*>')
    lower = _tag(html, r'<input id="price"[^>]*>')
    upper = _tag(html, r'<input id="price-upper"[^>]*>')
    assert 'data-citry-ui-part="range-slider"' in root
    assert 'name="minimum"' in lower
    assert 'data-thumb="lower"' in lower
    assert 'name="maximum"' in upper
    assert 'data-thumb="upper"' in upper
    assert 'aria-labelledby="price-lower-label"' in lower
    assert 'aria-labelledby="price-upper-label"' in upper
    assert '<span class="cui-slider__visually-hidden" id="price-lower-label">Lower value</span>' in html
    assert '<span class="cui-slider__visually-hidden" id="price-upper-label">Upper value</span>' in html
    assert html.count('role="slider"') == 2


def test_field_owns_state_and_labels_both_range_thumbs() -> None:
    html = _render(
        """
          <c-CField control_id="price" readonly invalid>
            <c-fill name="label">Price range</c-fill>
            <c-fill name="default"><c-CRangeSlider name="price" c-value="(20, 80)" /></c-fill>
            <c-fill name="description">Inclusive limits</c-fill>
            <c-fill name="error">Choose a valid range</c-fill>
          </c-CField>
        """
    )
    lower = _tag(html, r'<input id="price"[^>]*>')
    upper = _tag(html, r'<input id="price-upper"[^>]*>')
    assert "disabled" in lower
    assert "disabled" in upper
    assert 'aria-labelledby="price-label price-lower-label"' in lower
    assert 'aria-labelledby="price-label price-upper-label"' in upper
    assert 'aria-describedby="price-description price-error"' in lower
    assert 'aria-describedby="price-description price-error"' in upper
    assert 'aria-invalid="true"' in lower
    assert 'aria-invalid="true"' in upper
    assert 'for="price"' in html


def test_readonly_uses_successful_hidden_form_transports() -> None:
    html = _render('<c-CRangeSlider id="price" name="price" c-value="(20, 80)" readonly />')
    assert re.search(r'<input id="price"[^>]+disabled[^>]*>', html)
    assert re.search(r'<input id="price-upper"[^>]+disabled[^>]*>', html)
    lower_transport = _tag(html, r'<input id="price-readonly"[^>]*>')
    upper_transport = _tag(html, r'<input id="price-upper-readonly"[^>]*>')
    assert 'name="price"' in lower_transport
    assert " disabled" not in lower_transport
    assert 'name="price"' in upper_transport
    assert " disabled" not in upper_transport


@pytest.mark.parametrize(
    ("component", "kwargs", "error", "match"),
    [
        ("CSlider", {"value": 1.5}, TypeError, "int, Decimal"),
        ("CSlider", {"value": "1e3"}, ValueError, "plain-decimal"),
        ("CSlider", {"min": 10, "max": 10}, ValueError, "less than max"),
        ("CSlider", {"step": 0}, ValueError, "greater than zero"),
        ("CSlider", {"min": 0, "max": 1, "step": "0.3"}, ValueError, "whole steps"),
        ("CSlider", {"value": "0.3", "step": "0.2"}, ValueError, "step grid"),
        ("CSlider", {"marks": [0, 0]}, ValueError, "duplicate"),
        ("CRangeSlider", {"value": (80, 20)}, ValueError, "min_steps_between"),
        ("CRangeSlider", {"value": (20, 21), "min_steps_between_thumbs": 2}, ValueError, "min_steps_between"),
        ("CRangeSlider", {"lower_name": "lower"}, ValueError, "supplied together"),
        ("CRangeSlider", {"orientation": "diagonal"}, ValueError, "must be one of"),
    ],
)
def test_invalid_server_inputs_fail_deterministically(component, kwargs, error, match) -> None:
    with pytest.raises(error, match=match):
        _render(f'<c-{component} c-bind="kwargs" />', {"kwargs": kwargs})


@pytest.mark.parametrize(
    ("component", "destination", "attribute"),
    [
        ("CSlider", "attrs", "data-disabled"),
        ("CSlider", "attrs", "x-model"),
        ("CSlider", "input_attrs", "aria-valuenow"),
        ("CSlider", "input_attrs", ":min"),
        ("CRangeSlider", "attrs", "id"),
        ("CRangeSlider", "lower_input_attrs", "aria-label"),
        ("CRangeSlider", "upper_input_attrs", "data-citry-hostile"),
    ],
)
def test_owned_runtime_and_dynamic_attributes_are_rejected(component, destination, attribute) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(f'<c-{component} c-{destination}="attributes" />', {"attributes": {attribute: "hostile"}})


def test_explicit_range_label_overrides_remove_catalog_bindings() -> None:
    html = _render('<c-CRangeSlider lower_label="Minimum price" upper_label="Maximum price" />')
    assert "Minimum price" in html
    assert "Maximum price" in html
    assert "data-citry-i18n-binding" not in html


def test_css_covers_public_variables_parts_and_environment_modes() -> None:
    css = read_component_source_css("cslider")
    for variable in (
        "track-color",
        "fill-color",
        "thumb-color",
        "thumb-border-color",
        "focus-color",
        "mark-color",
        "value-background",
        "value-foreground",
        "track-size",
        "thumb-size",
        "control-size",
        "radius",
    ):
        assert f"--cui-slider-{variable}" in css
    for part in ("control", "track", "fill", "thumb", "value", "mark"):
        assert f'data-citry-ui-part="{part}"' in css
    assert "pointer: coarse" in css
    assert "forced-colors: active" in css
    assert "prefers-reduced-motion" in css
    assert "@media print" in css


def test_messages_are_the_final_range_slider_member() -> None:
    names = list(CRangeSlider.__dict__)
    assert names.index("messages") > names.index("css_file")
    assert "citry-ui-range-slider-lower" in CRangeSlider.messages
    assert "citry-ui-range-slider-upper" in CRangeSlider.messages
