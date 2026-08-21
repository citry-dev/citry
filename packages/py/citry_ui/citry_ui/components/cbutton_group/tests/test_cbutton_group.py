from __future__ import annotations

import re
from dataclasses import fields

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CButtonGroup
from citry_ui.quality.asset_sources import read_component_source_css


def _render(template: str, *, include_css: bool = False, data: dict[str, object] | None = None) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    source = template + ("{{ css }}" if include_css else "")

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return {"css": app.get("css")(), **(data or {})}

    return str(Page())


def _root(html: str) -> str:
    match = re.search(r'<div[^>]+data-citry-ui-part="button-group"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_schema_and_default_group_are_exact():
    assert [field.name for field in fields(CButtonGroup.Kwargs)] == [
        "label",
        "orientation",
        "attached",
        "grow",
        "class_",
        "style",
        "attrs",
    ]
    html = _render('<c-CButtonGroup label="Map"><c-CButton>Open</c-CButton></c-CButtonGroup>')
    root = _root(html)
    assert 'role="group"' in root
    assert 'aria-label="Map"' in root
    assert 'data-orientation="horizontal"' in root
    assert "data-attached" in root
    assert "aria-orientation" not in root


def test_vertical_growing_group_reflects_layout():
    root = _root(
        _render(
            '<c-CButtonGroup label="Tools" orientation="vertical" c-grow="True">'
            "<c-CButton>One</c-CButton></c-CButtonGroup>"
        )
    )
    assert "aria-orientation" not in root
    assert 'data-orientation="vertical"' in root
    assert "data-grow" in root


@pytest.mark.parametrize(
    ("template", "error"),
    [
        ('<c-CButtonGroup label=""><c-CButton>One</c-CButton></c-CButtonGroup>', TypeError),
        ('<c-CButtonGroup label="Map" orientation="diagonal"><c-CButton>One</c-CButton></c-CButtonGroup>', ValueError),
        ('<c-CButtonGroup label="Map"></c-CButtonGroup>', SyntaxError),
        ('<c-CButtonGroup label="Map" c-attrs="[]"><c-CButton>One</c-CButton></c-CButtonGroup>', TypeError),
    ],
)
def test_invalid_inputs_fail(template, error):
    with pytest.raises(error):
        _render(template)


@pytest.mark.parametrize(
    "attribute",
    ["role", "aria-label", "tabindex", "disabled", ":data-grow", "x-if", "data-citry-morph"],
)
def test_owned_and_runtime_attributes_are_rejected(attribute):
    with pytest.raises(ValueError, match="cannot"):
        _render(
            '<c-CButtonGroup label="Map" c-attrs="attrs"><c-CButton>One</c-CButton></c-CButtonGroup>',
            data={"attrs": {attribute: "consumer"}},
        )


def test_css_surface_and_zero_javascript():
    css = read_component_source_css("cbutton_group")
    for name in ("gap", "radius", "border-width"):
        assert f"--_cui-button-group-{name}: var(--cui-button-group-{name}," in css
    assert getattr(CButtonGroup, "js", None) is None
