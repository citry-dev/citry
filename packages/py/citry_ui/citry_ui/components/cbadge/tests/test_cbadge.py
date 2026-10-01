from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CBadge
from citry_ui.quality.asset_sources import read_component_source_css


def _render(badge: object, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>{{ badge }}</main>{{ css }}
        """

        def template_data(self, kwargs, slots):
            return {
                "badge": badge,
                "css": app.get("css")() if include_css else "",
            }

    return str(Page())


def test_badge_schema_is_small_and_runtime_introspectable():
    assert [field.name for field in fields(CBadge.Kwargs)] == [
        "variant",
        "intent",
        "size",
        "shape",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CBadge.Slots)] == ["default", "start", "end"]
    assert get_type_hints(CBadge.Kwargs)["variant"] is not None


def test_badge_requires_visible_default_content():
    with pytest.raises(ValueError, match="requires a default slot"):
        _render(CBadge())


def test_defaults_render_one_neutral_unfocusable_root_and_label_only():
    html = _render(CBadge(slots={"default": "Ready"}))
    root = re.search(r'<span[^>]+data-citry-ui-part="badge"[^>]*>', html)

    assert root is not None
    assert 'data-variant="soft"' in root.group(0)
    assert 'data-intent="neutral"' in root.group(0)
    assert 'data-size="md"' in root.group(0)
    assert 'data-shape="rounded"' in root.group(0)
    assert 'data-citry-ui-part="label"' in html
    assert re.search(r'<span[^>]+data-citry-ui-part="start"', html) is None
    assert re.search(r'<span[^>]+data-citry-ui-part="end"', html) is None
    assert "role=" not in root.group(0)
    assert "tabindex=" not in root.group(0)


def test_optional_icon_wrappers_and_root_styling_render_only_when_supplied():
    html = _render(
        CBadge(
            variant="outline",
            intent="success",
            size="lg",
            shape="pill",
            class_=["mineral", {"verified": True}],
            style={"--cui-badge-radius": "7px"},
            attrs={"class": "from-attrs", "data-mineral": "jade"},
            slots={"default": "Verified", "start": "S", "end": "E"},
        )
    )
    root = re.search(r'<span[^>]+data-citry-ui-part="badge"[^>]*>', html)

    assert root is not None
    assert 'class="cui-badge from-attrs mineral verified"' in root.group(0)
    assert 'style="--cui-badge-radius: 7px;"' in root.group(0)
    assert 'data-mineral="jade"' in root.group(0)
    assert 'data-variant="outline"' in root.group(0)
    assert 'data-intent="success"' in root.group(0)
    assert 'data-size="lg"' in root.group(0)
    assert 'data-shape="pill"' in root.group(0)
    assert len(re.findall(r'<span[^>]+data-citry-ui-part="start"', html)) == 1
    assert len(re.findall(r'<span[^>]+data-citry-ui-part="end"', html)) == 1


@pytest.mark.parametrize(
    ("input_name", "bad_value", "error", "match"),
    [
        ("variant", 2, TypeError, "variant must be a string"),
        ("variant", "filled", ValueError, "variant must be one of"),
        ("intent", "error", ValueError, "intent must be one of"),
        ("size", "xl", ValueError, "size must be one of"),
        ("shape", "circle", ValueError, "shape must be one of"),
        ("attrs", [], TypeError, "attrs must be a mapping"),
    ],
)
def test_invalid_inputs_fail_deterministically(input_name, bad_value, error, match):
    with pytest.raises(error, match=match):
        _render(CBadge(**{input_name: bad_value}, slots={"default": "Badge"}))


@pytest.mark.parametrize(
    ("attribute", "message"),
    [
        ("DATA-VARIANT", "cannot override owned attribute"),
        ("data-intent", "cannot override owned attribute"),
        ("role", "cannot override owned attribute"),
        ("tabindex", "cannot override owned attribute"),
        ("contenteditable", "cannot override owned attribute"),
        ("aria-hidden", "cannot override owned attribute"),
        ("data-citry-ui-part", "cannot override owned attribute"),
        ("data-citry-morph", "reserved Citry runtime attribute"),
        ("data-cev-action", "reserved Citry runtime attribute"),
        ("data-cid", "reserved Citry runtime attribute"),
    ],
)
def test_badge_rejects_owned_and_runtime_attributes(attribute, message):
    with pytest.raises(ValueError, match=message):
        _render(CBadge(attrs={attribute: "consumer"}, slots={"default": "Badge"}))


@pytest.mark.parametrize(
    "attribute",
    [
        ":data-size",
        ":role",
        ".aria-hidden",
        "v-bind:role",
        "v-bind:aria-hidden.prop",
        "V-BIND:data-shape",
        "v-bind",
        "v-if",
        "V-IF",
        "v-for",
        "v-html",
        "v-model",
        ":class",
        "@click",
        "#default",
    ],
)
def test_python_attrs_reject_vue_directives_before_rendering(attribute):
    with pytest.raises(ValueError, match=r"CBadge attrs cannot contain the Vue directive"):
        _render(CBadge(attrs={attribute: "value"}, slots={"default": "Badge"}))


def test_attrs_without_vue_syntax_stay_ordinary_attributes():
    html = _render(CBadge(attrs={"x-if": "plain", "data-note": "kept"}, slots={"default": "Badge"}))
    assert 'x-if="plain"' in html
    assert 'data-note="kept"' in html


def test_direct_choices_are_detrusted_before_rendering():
    with pytest.raises(ValueError, match="variant must be one of"):
        _render(CBadge(variant=Markup('soft" onfocus="evil'), slots={"default": "Badge"}))


def test_css_exposes_every_public_variable_and_no_component_javascript():
    css = read_component_source_css("cbadge")

    for variable in (
        "background",
        "foreground",
        "border-color",
        "radius",
        "min-height",
        "padding-inline",
        "gap",
        "font-size",
        "font-weight",
    ):
        assert f"--_cui-badge-{variable}: var(--cui-badge-{variable}," in css
    assert "@media (forced-colors: active)" in css
    assert "@media print" in css
    assert getattr(CBadge, "js", None) is None
