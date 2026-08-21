"""Focused server contracts for CRating."""

from __future__ import annotations

import re
from dataclasses import fields
from decimal import Decimal

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cfield import CField
from citry_ui.components.crating import (
    CRating,
    CRatingChangeSource,
    CRatingExact,
    CRatingHoverChangeDetail,
    CRatingSize,
    CRatingValueChangeDetail,
    CRatingVariant,
)
from citry_ui.quality.asset_sources import read_component_source_css


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-rating-tests", (CField, CRating)))
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
    assert [field.name for field in fields(CRating.Kwargs)] == [
        "value",
        "name",
        "form",
        "id",
        "max",
        "precision",
        "required",
        "disabled",
        "readonly",
        "invalid",
        "allow_clear",
        "label",
        "value_label",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
        "input_attrs",
    ]
    assert fields(CRating.Slots) == ()
    assert all(
        item is not None
        for item in (
            CRatingExact,
            CRatingSize,
            CRatingVariant,
            CRatingChangeSource,
            CRatingValueChangeDetail,
            CRatingHoverChangeDetail,
        )
    )


def test_fractional_rating_renders_exact_native_radio_fallback() -> None:
    html = _render(
        '<c-CRating id="quality" name="quality" form="review" label="Quality" '
        'value="3.50" precision="0.5" required class_="review-rating" c-style="style" />',
        {"style": {"--cui-rating-fill-color": "gold"}},
    )
    root = _tag(html, r'<div class="cui-rating review-rating"[^>]*>')
    radios = re.findall(r'<input[^>]+type="radio"[^>]*>', html)
    assert 'role="radiogroup"' in root
    assert 'id="quality-root"' in root
    assert 'aria-label="Quality"' in root
    assert "--_cui-rating-ratio: 70.0%" in root
    assert "--cui-rating-fill-color: gold" in root
    assert len(radios) == 10
    assert radios[0].startswith('<input id="quality"')
    assert 'id="quality-10"' in radios[-1]
    assert all('name="quality"' in radio and 'form="review"' in radio and "required" in radio for radio in radios)
    assert sum("checked" in radio for radio in radios) == 1
    assert 'value="3.5" checked' in next(radio for radio in radios if "checked" in radio)
    assert ">3.5 out of 5</span>" in html.replace("\u2068", "").replace("\u2069", "")
    assert html.count('data-citry-ui-part="symbol"') == 10


def test_zero_and_none_are_the_same_unrated_state() -> None:
    for value in (None, 0, "0.0", Decimal("0.00")):
        html = _render('<c-CRating c-bind="kwargs" />', {"kwargs": {"label": "Rating", "value": value}})
        assert " checked" not in html
        assert "--_cui-rating-ratio: 0%" in html


def test_readonly_submits_hidden_value_and_disabled_submits_nothing() -> None:
    readonly = _render('<c-CRating id="score" name="score" label="Score" value="2.5" precision="0.5" readonly />')
    root = _tag(readonly, r'<div class="cui-rating"[^>]*>')
    radios = re.findall(r'<input[^>]+type="radio"[^>]*>', readonly)
    transport = _tag(readonly, r'<input id="score-transport"[^>]*>')
    assert 'aria-readonly="true"' in root
    assert 'tabindex="0"' in root
    assert all(" disabled" in radio for radio in radios)
    assert 'name="score"' in transport
    assert 'value="2.5"' in transport
    assert " disabled" not in transport
    assert 'data-citry-ui-part="readonly-value"' in readonly

    disabled = _render('<c-CRating id="score" name="score" label="Score" value="2" disabled />')
    transport = _tag(disabled, r'<input id="score-transport"[^>]*>')
    assert "disabled" in transport
    assert all(" disabled" in radio for radio in re.findall(r'<input[^>]+type="radio"[^>]*>', disabled))


def test_field_owns_label_state_and_relationships() -> None:
    html = _render(
        """
          <c-CField control_id="score" required invalid>
            <c-fill name="label">Review score</c-fill>
            <c-fill name="default"><c-CRating name="score" /></c-fill>
            <c-fill name="description">One through five</c-fill>
            <c-fill name="error">Choose a score</c-fill>
          </c-CField>
        """
    )
    root = _tag(html, r'<div class="cui-rating"[^>]*>')
    first = _tag(html, r'<input id="score"[^>]*>')
    assert 'aria-labelledby="score-label"' in root
    assert 'aria-describedby="score-description score-error"' in root
    assert "data-required" in root
    assert "data-invalid" in root
    assert "required" in first
    assert 'aria-describedby="score-description score-error"' in first
    assert 'aria-errormessage="score-error"' in first
    assert 'aria-invalid="true"' in first
    assert 'for="score"' in html


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({}, ValueError, "requires label"),
        ({"label": "Rating", "value": 1.5}, TypeError, "int, Decimal"),
        ({"label": "Rating", "value": "1e2"}, ValueError, "plain-decimal"),
        ({"label": "Rating", "max": 0}, ValueError, "between 1 and 20"),
        ({"label": "Rating", "max": True}, TypeError, "must be an integer"),
        ({"label": "Rating", "precision": 0}, ValueError, "precision must be positive"),
        ({"label": "Rating", "precision": "0.3"}, ValueError, "divide 1 exactly"),
        ({"label": "Rating", "precision": "0.01", "max": 3}, ValueError, "at most 200"),
        ({"label": "Rating", "value": "2.3", "precision": "0.5"}, ValueError, "precision-grid"),
        ({"label": "Rating", "value_label": "{value}"}, ValueError, "both {value} and {max}"),
        ({"label": "Rating", "variant": "outline"}, ValueError, "must be one of"),
    ],
)
def test_invalid_inputs_fail_deterministically(kwargs, error, match) -> None:
    with pytest.raises(error, match=re.escape(match)):
        _render('<c-CRating c-bind="kwargs" />', {"kwargs": kwargs})


@pytest.mark.parametrize(
    ("destination", "attribute"),
    [
        ("attrs", "role"),
        ("attrs", "data-disabled"),
        ("input_attrs", "name"),
        ("input_attrs", "aria-label"),
        ("input_attrs", "x-model"),
    ],
)
def test_owned_attributes_are_rejected(destination, attribute) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(
            '<c-CRating label="Rating" c-bind="kwargs" />',
            {"kwargs": {destination: {attribute: "override"}}},
        )


def test_explicit_value_pattern_removes_catalog_lookup() -> None:
    html = _render('<c-CRating label="Score" value="2" value_label="Score {value} / {max}" />')
    assert ">Score 2 / 5</span>" in html


def test_css_exposes_public_variables_parts_and_environment_rules() -> None:
    css = read_component_source_css("crating")
    for variable in (
        "empty-color",
        "fill-color",
        "hover-color",
        "focus-color",
        "gap",
        "symbol-size",
        "control-size",
        "disabled-opacity",
    ):
        assert f"--_cui-rating-{variable}: var(--cui-rating-{variable}" in css
    assert '[data-citry-ui-part="choice"]' in css
    assert "@media (pointer: coarse)" in css
    assert "@media (forced-colors: active)" in css
