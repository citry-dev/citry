from __future__ import annotations

import re
from typing import get_args
from xml.etree import ElementTree as ET

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CIcon, CIconName
from citry_ui.components.cicon._catalog import ICON_GLYPHS, ICON_SOURCES

_ICON_APP = Citry(autodiscover=False)
_ICON_APP.register_library(citry_ui)


class IconTestPage(Component):
    """Reuse one installed catalog while each render supplies fresh inputs."""

    citry = _ICON_APP

    class Kwargs:
        icon: object
        css: str = ""

    template = """
      <main>{{ icon }}</main>{{ css }}
    """


def _render(icon: object, *, include_css: bool = False) -> str:
    css = _ICON_APP.get("css")() if include_css else ""
    return str(IconTestPage(icon=icon, css=css))


def _glyph(html: str) -> str:
    match = re.search(r'<g class="cui-icon__glyph">\s*(.*?)\s*</g>', html, re.DOTALL)
    assert match is not None
    return match.group(1)


def test_every_public_name_renders_a_local_inline_svg():
    names = get_args(CIconName)

    assert len(names) == 57
    for name in names:
        html = _render(CIcon(name=name))
        assert '<svg class="cui-icon' in html
        assert f'data-name="{name}"' in html
        assert "<path" in html or "<circle" in html or "<rect" in html
        assert "http" not in _glyph(html)


@pytest.mark.parametrize(
    ("alias", "visual"),
    [
        ("back", "arrow-left"),
        ("forward", "arrow-right"),
        ("prev", "chevron-left"),
        ("next", "chevron-right"),
        ("close", "x"),
        ("clear", "x"),
        ("success", "circle-check"),
        ("info", "circle-info"),
        ("warn", "triangle-alert"),
        ("danger", "circle-x"),
        ("expand", "chevron-down"),
        ("collapse", "chevron-up"),
        ("dropdown", "chevron-down"),
    ],
)
def test_semantic_aliases_share_the_expected_audited_geometry(alias: str, visual: str):
    assert _glyph(_render(CIcon(name=alias))) == _glyph(_render(CIcon(name=visual)))


def test_decorative_and_meaningful_semantics_are_explicit():
    decorative = _render(CIcon(name="leaf"))
    meaningful = _render(CIcon(name="leaf", label="Native silver fern"))

    assert 'aria-hidden="true"' in decorative
    assert " role=" not in decorative
    assert "aria-label=" not in decorative
    assert 'role="img"' in meaningful
    assert 'aria-label="Native silver fern"' in meaningful
    assert "aria-hidden=" not in meaningful
    assert "tabindex=" not in decorative + meaningful


def test_root_classes_styles_and_inert_metadata_merge_without_replacing_owned_contracts():
    html = _render(
        CIcon(
            name="leaf",
            size="lg",
            class_=["field-icon", {"field-icon--fresh": True}],
            style={"--cui-icon-stroke-width": "1.5"},
            attrs={
                "id": "specimen-icon",
                "aria-describedby": "specimen-note",
                "data-specimen": "pteridium",
                "class": "from-attrs",
            },
        )
    )

    tag = re.search(r"<svg[^>]+>", html)
    assert tag is not None
    assert 'class="cui-icon from-attrs field-icon field-icon--fresh"' in tag.group(0)
    assert 'style="--cui-icon-stroke-width: 1.5;"' in tag.group(0)
    assert 'id="specimen-icon"' in tag.group(0)
    assert 'aria-describedby="specimen-note"' in tag.group(0)
    assert 'data-specimen="pteridium"' in tag.group(0)
    assert 'data-size="lg"' in tag.group(0)
    assert 'data-citry-ui-part="icon"' in tag.group(0)


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"name": 2}, TypeError, "name must be a string"),
        ({"name": "unknown"}, ValueError, "documented icon name"),
        ({"name": "leaf", "size": "xl"}, ValueError, "size must be one of"),
        ({"name": "leaf", "label": 2}, TypeError, "label must be a string"),
        ({"name": "leaf", "label": "  "}, ValueError, "non-whitespace"),
        ({"name": "leaf", "attrs": []}, TypeError, "attrs must be a mapping"),
    ],
)
def test_invalid_server_inputs_fail_deterministically(kwargs, error, match):
    with pytest.raises(error, match=match):
        _render(CIcon(**kwargs))


@pytest.mark.parametrize(
    "attribute",
    [
        "aria-label",
        "aria-labelledby",
        "aria-hidden",
        "role",
        "tabindex",
        "viewBox",
        "width",
        "stroke-width",
        "data-name",
        "data-size",
        "data-citry-ui-part",
        "@click",
        ":stroke",
        "x-data",
        "x-bind:aria-label",
        "c-if",
        "onclick",
        "onClick",
        "data-citry-morph",
        "data-citry-root",
        "data-citry-key",
        "data-cev-action",
        "data-cid",
        "data-cid-c00example",
    ],
)
def test_owned_or_executable_svg_attributes_are_rejected(attribute: str):
    with pytest.raises(ValueError, match="cannot"):
        _render(CIcon(name="leaf", attrs={attribute: "consumer"}))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": Markup("leaf")},
        {"name": "leaf", "label": Markup('good" onload="window.__iconPwned=true')},
        {"name": "leaf", "class_": ["safe", Markup('bad" onload="window.__iconPwned=true')]},
        {"name": "leaf", "style": {"color": Markup('red" onload="window.__iconPwned=true')}},
        {"name": "leaf", "attrs": {"title": Markup('good" onload="window.__iconPwned=true')}},
        {"name": "leaf", "attrs": {Markup('title" onload="window.__iconPwned=true'): "bad"}},
        {"name": "leaf", "attrs": {"style": [{"color": Markup("red")}]}},
    ],
)
def test_trusted_html_values_cannot_cross_the_icon_input_boundary(kwargs):
    with pytest.raises(ValueError, match="trusted HTML"):
        _render(CIcon(**kwargs))


def test_plain_label_markup_is_escaped_as_attribute_text():
    html = _render(CIcon(name="leaf", label='<good" onload="window.__iconPwned=true'))

    assert "&lt;good&#34;" in html
    assert ' onload="' not in html


def test_generated_catalog_contains_only_audited_geometry_and_is_immutable():
    assert ICON_GLYPHS.keys() == ICON_SOURCES.keys()
    for geometry in ICON_GLYPHS.values():
        root = ET.fromstring(f"<svg>{geometry}</svg>")  # noqa: S314 - package-owned generated geometry
        assert {child.tag for child in root} <= {"path", "circle", "rect"}
        assert not any(child.text for child in root)

    with pytest.raises(TypeError):
        ICON_GLYPHS["leaf"] = "<script></script>"  # type: ignore[index]


def test_icon_has_css_but_no_javascript_asset():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)
    icon = installed[CIcon]

    assert icon.get_js() is None
    assert "--cui-icon-size" in icon.get_css()
    assert "--cui-icon-stroke-width" in icon.get_css()
    assert ":dir(rtl)" in icon.get_css()
