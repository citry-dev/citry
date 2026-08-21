"""Focused server contract tests for CScrollArea."""

from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path
from typing import get_args, get_type_hints

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components._scroll_geometry import SCROLL_GEOMETRY_RUNTIME_DEPENDENCY
from citry_ui.components.ccarousel import CCarousel, CCarouselSlide
from citry_ui.components.cscroll_area import (
    CScrollArea,
    CScrollAreaAxis,
    CScrollAreaOverscroll,
    CScrollAreaScrollbarGutter,
    CScrollAreaScrollbarWidth,
    CScrollAreaScrollDetail,
)


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-scroll-area-tests", (CScrollArea,)))
    return app


def _render(source: str, data: dict[str, object] | None = None, *, dependencies: bool = False) -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return data or {}

    page = Page()
    return str(page) if dependencies else page.render().serialize(deps_strategy="ignore")


def test_schema_exports_and_records_are_exact() -> None:
    assert [item.name for item in fields(CScrollArea.Kwargs)] == [
        "id",
        "aria_label",
        "aria_labelledby",
        "axis",
        "scrollbar_width",
        "scrollbar_gutter",
        "overscroll",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CScrollArea.Slots)] == ["default"]
    hints = get_type_hints(CScrollArea.Kwargs)
    assert get_args(hints["axis"]) == ("block", "inline", "both")
    assert get_args(hints["scrollbar_width"]) == ("auto", "thin")
    assert get_args(hints["scrollbar_gutter"]) == ("auto", "stable", "stable-both-edges")
    assert get_args(hints["overscroll"]) == ("auto", "contain", "none")
    assert CScrollAreaScrollDetail.__required_keys__ == {"inlineOffset", "blockOffset", "source"}
    assert all(
        item is not None
        for item in (
            CScrollAreaAxis,
            CScrollAreaScrollbarWidth,
            CScrollAreaScrollbarGutter,
            CScrollAreaOverscroll,
        )
    )
    from citry_ui.components import cscroll_area

    assert cscroll_area.__all__ == [
        "CScrollArea",
        "CScrollAreaAxis",
        "CScrollAreaOverscroll",
        "CScrollAreaScrollDetail",
        "CScrollAreaScrollbarGutter",
        "CScrollAreaScrollbarWidth",
    ]


def test_server_output_is_one_native_named_viewport() -> None:
    html = _render(
        '<c-CScrollArea id="activity" aria_label="Recent activity" axis="both" '
        'scrollbar_width="thin" scrollbar_gutter="stable-both-edges" overscroll="contain">'
        "<p>Imported 12 records</p></c-CScrollArea>"
    )
    assert html.count('data-citry-ui-part="scroll-area"') == 1
    assert re.search(r'<div[^>]+id="activity"[^>]+tabindex="0"[^>]+role="region"', html)
    assert 'aria-label="Recent activity"' in html
    assert 'data-axis="both"' in html
    assert 'data-scrollbar-width="thin"' in html
    assert 'data-scrollbar-gutter="stable-both-edges"' in html
    assert 'data-overscroll="contain"' in html
    assert "Imported 12 records" in html
    assert all(token not in html for token in ("scroll-area-track", "scroll-area-thumb", "scroll-area-corner"))


def test_unnamed_empty_and_external_name_output() -> None:
    unnamed = _render('<c-CScrollArea id="empty" />')
    assert 'id="empty"' in unnamed
    assert "role=" not in unnamed
    assert "aria-label=" not in unnamed
    assert "aria-labelledby=" not in unnamed
    labelled = _render(
        '<h2 id="events-title">Events</h2><c-CScrollArea id="events" '
        'aria_labelledby="events-title secondary-title">Events</c-CScrollArea>'
    )
    assert 'role="region"' in labelled
    assert 'aria-labelledby="events-title secondary-title"' in labelled


def test_direct_python_composition_renders_and_escapes_content() -> None:
    app = _app()
    html = (
        CScrollArea(
            aria_label="Operations",
            slots={"default": "<script>unsafe()</script>"},
        )
        .render(citry=app)
        .serialize(deps_strategy="ignore")
    )
    assert 'aria-label="Operations"' in html
    assert "&lt;script&gt;unsafe()&lt;/script&gt;" in html


def test_class_style_attrs_merge_before_owned_scroll_behavior() -> None:
    html = _render(
        '<c-CScrollArea class_="audit" '
        "c-style=\"[{'color': 'purple'}, {'scroll-behavior': 'smooth !important'}]\" "
        "c-attrs=\"{'class': 'mapped', 'style': 'padding: 3px; scroll-behavior: smooth !important', "
        "'aria-describedby': 'hint', 'data-app-surface': 'audit', '@scroll.passive': 'seen = true'}\">"
        "Content</c-CScrollArea>"
    )
    tag = re.search(r"<div[^>]+data-citry-ui-part=\"scroll-area\"", html)
    assert tag is not None
    root = tag.group(0)
    assert 'class="cui-scroll-area mapped audit"' in root
    assert 'aria-describedby="hint"' in root
    assert 'data-app-surface="audit"' in root
    assert "scroll-behavior: smooth !important" not in root
    assert root.endswith('data-citry-ui-part="scroll-area"')
    assert root.count("scroll-behavior: auto !important") == 1


def test_both_safe_native_listener_spellings_are_forwarded() -> None:
    html = _render(
        "<c-CScrollArea c-attrs=\"{'@scroll.passive': 'window.seen = $event.type', "
        "'x-on:wheel.prevent': 'window.wheel = $event.type'}\">Content</c-CScrollArea>"
    )
    assert '@scroll.passive="window.seen = $event.type"' in html
    assert 'x-on:wheel.prevent="window.wheel = $event.type"' in html


@pytest.mark.parametrize(
    ("inputs", "message"),
    [
        ('aria_label=" "', "aria_label"),
        ('aria_label="Name" aria_labelledby="title"', "mutually exclusive"),
        ('aria_labelledby="title title"', "duplicate"),
        ('id="two words"', "ASCII whitespace"),
        ('axis="horizontal"', "axis"),
        ('scrollbar_width="none"', "scrollbar_width"),
        ('scrollbar_gutter="always"', "scrollbar_gutter"),
        ('overscroll="chain"', "overscroll"),
    ],
)
def test_invalid_public_inputs_fail(inputs: str, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(f"<c-CScrollArea {inputs}>Content</c-CScrollArea>")


@pytest.mark.parametrize(
    "attrs",
    [
        "{'id': 'other'}",
        "{'role': 'group'}",
        "{'tabindex': '-1'}",
        "{'aria-hidden': 'true'}",
        "{'data-citry-ui-part': 'other'}",
        "{'hidden': True}",
        "{'inert': True}",
        "{'is': 'x-scroll'}",
        "{'x-data': '{}'}",
        "{'x-bind:role': 'role'}",
        "{'onclick': 'unsafe()'}",
        "{'@scroll.window': 'unsafe()'}",
        "{'x-on:wheel.document': 'unsafe()'}",
    ],
)
def test_owned_or_untrusted_root_attributes_fail(attrs: str) -> None:
    with pytest.raises(ValueError, match="attrs"):
        _render(f'<c-CScrollArea c-attrs="{attrs}">Content</c-CScrollArea>')


def test_assets_include_one_shared_geometry_copy_and_environment_rules() -> None:
    html = _render(
        '<c-CScrollArea>One</c-CScrollArea><c-CScrollArea axis="inline">Two</c-CScrollArea><c-css /><c-js />',
        dependencies=True,
    )
    helper = SCROLL_GEOMETRY_RUNTIME_DEPENDENCY.content
    assert helper is not None
    assert html.count(helper.strip()) == 1
    assert len(re.findall(r'<div[^>]+data-citry-ui-part="scroll-area"', html)) == 2
    css = (Path(__file__).parents[1] / "runtime.source.css").read_text(encoding="utf8")
    assert "overflow-block" in css
    assert "scrollbar-width" in css
    assert "scrollbar-gutter" in css
    assert "forced-colors: active" in css
    assert "scrollbar-color: auto" in css
    assert "@media print" in css
    assert "overflow: visible !important" in css


@pytest.mark.parametrize("count", [1, 10, 100])
def test_geometry_dependency_is_deduplicated_for_many_scroll_areas(count: int) -> None:
    source = "".join(f'<c-CScrollArea id="area-{index}">Area</c-CScrollArea>' for index in range(count))
    html = _render(f"{source}<c-js />", dependencies=True)
    assert html.count(SCROLL_GEOMETRY_RUNTIME_DEPENDENCY.content.strip()) == 1
    assert len(re.findall(r'<div[^>]+data-citry-ui-part="scroll-area"', html)) == count


def test_geometry_dependency_is_one_copy_when_carousel_and_scroll_area_coexist() -> None:
    app = Citry(autodiscover=False)
    app.register_library(
        ComponentLibrary("citry-ui-scroll-coexistence-tests", (CScrollArea, CCarousel, CCarouselSlide))
    )

    class Page(Component):
        citry = app
        template = """
          <c-CScrollArea id="area">Area</c-CScrollArea>
          <c-CCarousel label="Stories">
            <c-CCarouselSlide value="story" label="Story">Story</c-CCarouselSlide>
          </c-CCarousel>
          <c-js />
        """

    html = str(Page())
    assert html.count(SCROLL_GEOMETRY_RUNTIME_DEPENDENCY.content.strip()) == 1


def test_runtime_has_no_custom_input_or_content_geometry_observers() -> None:
    javascript = CScrollArea.js
    assert 'addEventListener("scroll"' in javascript
    assert all(
        token not in javascript
        for token in (
            'addEventListener("wheel"',
            'addEventListener("touch',
            'addEventListener("key',
            "ResizeObserver",
            'addEventListener("scrollend"',
            "preventDefault",
            "stopPropagation",
        )
    )
    assert "MutationObserver" in javascript
    assert "subtree" not in javascript
