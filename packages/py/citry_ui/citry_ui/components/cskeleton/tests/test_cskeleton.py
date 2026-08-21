from __future__ import annotations

import re
from dataclasses import fields

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CSkeleton
from citry_ui.quality.asset_sources import read_component_source_css


def _render(skeleton: object, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "<main>{{ skeleton }}</main>{{ css }}"

        def template_data(self, kwargs, slots):
            return {"skeleton": skeleton, "css": app.get("css")() if include_css else ""}

    return str(Page())


def _root(html: str) -> str:
    match = re.search(r'<span[^>]+data-citry-ui-part="skeleton"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_schema_and_default_decorative_rect_are_exact():
    assert [field.name for field in fields(CSkeleton.Kwargs)] == [
        "kind",
        "lines",
        "animation",
        "width",
        "height",
        "last_line_width",
        "class_",
        "style",
        "attrs",
    ]
    root = _root(_render(CSkeleton()))
    assert 'data-kind="rect"' in root
    assert 'data-animation="pulse"' in root
    assert 'aria-hidden="true"' in root
    assert "tabindex" not in root


def test_text_lines_and_owned_dimensions_render_exactly():
    html = _render(CSkeleton(kind="text", lines=3, width="18rem", height="0.8em", last_line_width="42%"))
    root = _root(html)
    assert "--cui-skeleton-width: 18rem" in root
    assert "--cui-skeleton-height: 0.8em" in root
    assert "--cui-skeleton-last-line-width: 42%" in root
    assert len(re.findall(r'<span[^>]+data-citry-ui-part="line"', html)) == 3
    assert len(re.findall(r'<span[^>]+data-citry-ui-part="line"[^>]+data-last', html)) == 1


def test_circle_keeps_equal_geometry():
    root = _root(_render(CSkeleton(kind="circle", width="4rem")))
    assert "--cui-skeleton-width: 4rem" in root
    assert "--cui-skeleton-height: 4rem" in root
    with pytest.raises(ValueError, match="must match"):
        _render(CSkeleton(kind="circle", width="4rem", height="3rem"))


@pytest.mark.parametrize(
    ("input_name", "bad_value", "error"),
    [
        ("kind", "card", ValueError),
        ("animation", "spin", ValueError),
        ("lines", 0, ValueError),
        ("lines", 1.5, TypeError),
        ("width", "10px;color:red", ValueError),
        ("height", "", ValueError),
        ("attrs", [], TypeError),
    ],
)
def test_invalid_inputs_fail(input_name, bad_value, error):
    with pytest.raises(error):
        _render(CSkeleton(**{input_name: bad_value}))


def test_multiple_lines_require_text_kind():
    with pytest.raises(ValueError, match="require kind='text'"):
        _render(CSkeleton(lines=2))


@pytest.mark.parametrize(
    "attribute",
    ["role", "aria-hidden", "tabindex", "data-kind", ":data-animation", "x-if", "data-citry-morph"],
)
def test_owned_and_runtime_attributes_are_rejected(attribute):
    with pytest.raises(ValueError, match="cannot"):
        _render(CSkeleton(attrs={attribute: "consumer"}))


def test_css_surface_and_zero_javascript():
    css = read_component_source_css("cskeleton")
    for name in ("width", "height", "radius", "background", "highlight", "gap", "duration", "last-line-width"):
        assert f"--_cui-skeleton-{name}: var(--cui-skeleton-{name}," in css
    assert "prefers-reduced-motion" in css
    assert getattr(CSkeleton, "js", None) is None
