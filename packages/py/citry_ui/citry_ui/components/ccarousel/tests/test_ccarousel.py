from __future__ import annotations

import json
import re
from dataclasses import fields
from pathlib import Path
from typing import get_args, get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CCarousel, CCarouselSlide
from citry_ui.components._scroll_geometry import SCROLL_GEOMETRY_RUNTIME_DEPENDENCY


def _render(source: str, *, static_fallback: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = source

    page = Page()
    return page.render().serialize(security_javascript="omit") if static_fallback else str(page)


def _manifest(html: str) -> dict[str, object]:
    match = re.search(r"CitryStable\.startPrepared\((\{.*\})\)\.catch", html, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))["manifest"]


def _occurrences(manifest: dict[str, object], type_name: str) -> list[dict[str, object]]:
    return [item for item in manifest["occurrences"] if item["typeKey"].startswith(f"{type_name}_")]


def _source(root: str = "", slide: str = "") -> str:
    return (
        f'<c-CCarousel label="Featured stories" {root}>'
        f'<c-CCarouselSlide value="aurora" label="Aurora field report" {slide}>Aurora</c-CCarouselSlide>'
        '<c-CCarouselSlide value="tide" label="Tide field report">Tide</c-CCarouselSlide>'
        "</c-CCarousel>"
    )


def test_carousel_renders_apg_semantics_and_form_safe_controls() -> None:
    source = _source('c-index="1" variant="surface" size="lg"')
    html = _render(source)
    static_html = _render(source, static_fallback=True)
    assert re.search(r'<section[^>]+role="region"[^>]+aria-label="Featured stories"', static_html)
    assert 'aria-roledescription="carousel"' in static_html
    assert static_html.count('aria-roledescription="slide"') == 2
    assert static_html.count('role="group"') >= 3
    assert re.search(r'<button[^>]+type="button"[^>]+aria-label="Previous slide"', static_html)
    assert re.search(r'<button[^>]+type="button"[^>]+aria-label="Next slide"', static_html)
    assert re.search(r'<div[^>]+tabindex="0"[^>]+data-citry-carousel-viewport', static_html)
    assert re.search(r'<div[^>]+data-value="tide"[^>]+data-active', static_html)
    assert "Aurora" in static_html
    assert "Tide" in static_html
    manifest = _manifest(html)
    carousel = _occurrences(manifest, "CCarousel")[0]["preparedData"]
    assert carousel["citryAttrs0"]["aria-label"] == "Featured stories"
    assert carousel["citryAttrs0"]["data-index"] == 1
    assert carousel["citryAttrs1"]["aria-label"] == "Previous slide"
    assert carousel["citryAttrs2"]["aria-label"] == "Next slide"
    slides = _occurrences(manifest, "CCarouselSlide")
    assert [slide["preparedData"]["citryAttrs0"]["data-value"] for slide in slides] == ["aurora", "tide"]
    assert slides[1]["preparedData"]["citryAttrs0"]["data-active"] == ""


def test_schema_registration_and_types_are_public() -> None:
    assert [item.name for item in fields(CCarousel.Kwargs)] == [
        "label",
        "id",
        "index",
        "orientation",
        "loop",
        "disabled",
        "controls",
        "indicators",
        "draggable",
        "variant",
        "size",
        "previous_label",
        "next_label",
        "picker_label",
        "role_description",
        "class_",
        "style",
        "attrs",
    ]
    hints = get_type_hints(CCarousel.Kwargs)
    assert get_args(hints["orientation"]) == ("horizontal", "vertical")
    assert CCarousel in citry_ui.COMPONENTS
    assert CCarouselSlide in citry_ui.COMPONENTS


def test_carousel_uses_the_shared_scroll_geometry_dependency() -> None:
    assert CCarousel.Dependencies.js == [SCROLL_GEOMETRY_RUNTIME_DEPENDENCY]
    assert 'Symbol.for("citry-ui:scroll-geometry")' in CCarousel.js
    assert "horizontalFromRaw" in CCarousel.js
    assert "horizontalToRaw" in CCarousel.js


@pytest.mark.parametrize(
    ("root", "message"),
    [
        ('orientation="diagonal"', "orientation"),
        ('variant="filled"', "variant"),
        ('size="xl"', "size"),
        ('c-index="-1"', "nonnegative"),
        ('c-loop="1"', "loop"),
        ('id="two words"', "ASCII whitespace"),
        ('previous_label=""', "previous_label"),
        ("c-attrs=\"{'role': 'group'}\"", "owned"),
        ("c-attrs=\"{'x-show': 'shown'}\"", "ownership"),
    ],
)
def test_invalid_root_inputs_fail(root: str, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(_source(root))


def test_invalid_collections_and_slide_inputs_fail() -> None:
    with pytest.raises(ValueError, match="at least one"):
        _render(
            '<c-CCarousel label="Empty"><c-fill name="default"><c-if cond="False">'
            '<c-CCarouselSlide value="hidden" label="Hidden">Hidden</c-CCarouselSlide>'
            "</c-if></c-fill></c-CCarousel>"
        )
    with pytest.raises(ValueError, match="outside"):
        _render(_source('c-index="3"'))
    with pytest.raises(ValueError, match="duplicated"):
        _render(
            '<c-CCarousel label="Duplicate"><c-CCarouselSlide value="same" label="A">A</c-CCarouselSlide>'
            '<c-CCarouselSlide value="same" label="B">B</c-CCarouselSlide></c-CCarousel>'
        )
    with pytest.raises(ValueError, match="inside CCarousel"):
        _render('<c-CCarouselSlide value="loose" label="Loose">Loose</c-CCarouselSlide>')
    with pytest.raises((TypeError, ValueError), match="label"):
        _render(
            '<c-CCarousel label="Labels"><c-CCarouselSlide value="empty" label="">'
            "Empty</c-CCarouselSlide></c-CCarousel>"
        )
    with pytest.raises(ValueError, match="inside CCarousel"):
        _render(
            '<c-CCarousel label="Outer"><c-CCarouselSlide value="outer" label="Outer">'
            '<c-CCarouselSlide value="nested" label="Nested">Nested</c-CCarouselSlide>'
            "</c-CCarouselSlide></c-CCarousel>"
        )


def test_nested_independent_carousel_is_allowed_inside_slide_content() -> None:
    source = (
        '<c-CCarousel label="Outer"><c-CCarouselSlide value="outer" label="Outer">'
        '<c-CCarousel label="Inner"><c-CCarouselSlide value="inner" label="Inner">'
        "Inner slide</c-CCarouselSlide></c-CCarousel>"
        "</c-CCarouselSlide></c-CCarousel>"
    )
    html = _render(source)
    static_html = _render(source, static_fallback=True)
    assert static_html.count('aria-roledescription="carousel"') == 2
    assert static_html.count('aria-roledescription="slide"') == 2
    manifest = _manifest(html)
    assert len(_occurrences(manifest, "CCarousel")) == 2
    assert len(_occurrences(manifest, "CCarouselSlide")) == 2


def test_owned_slide_attrs_fail() -> None:
    with pytest.raises(ValueError, match="owned"):
        _render(_source(slide="c-attrs=\"{'aria-hidden': 'true'}\""))


def test_css_contract_covers_native_scroll_and_environments() -> None:
    component_root = Path(__file__).parents[1]
    css = (component_root / "runtime.source.css").read_text(encoding="utf8")
    minified = (component_root / "runtime.min.css").read_text(encoding="utf8")
    assert "scroll-snap-type" in css
    assert "--cui-carousel-block-size" in css
    assert '[data-citry-ui-part="indicator"]' in css
    assert "prefers-reduced-motion: reduce" in css
    assert "forced-colors: active" in css
    assert "@media print" in css
    assert ":where()" not in minified
    assert "])::-webkit-scrollbar" in minified
