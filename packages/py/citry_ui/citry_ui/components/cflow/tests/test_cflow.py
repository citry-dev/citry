from __future__ import annotations

import re
from dataclasses import fields

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CCol, CRow
from citry_ui.quality.asset_sources import read_component_source_css


def _render(layout: object, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>{{ layout }}</main>{{ css }}
        """

        def template_data(self, kwargs, slots):
            return {
                "layout": layout,
                "css": app.get("css")() if include_css else "",
            }

    return str(Page())


def test_flow_schemas_keep_the_frequent_surface_small():
    assert [field.name for field in fields(CCol.Kwargs)] == [
        "tag",
        "gap",
        "align",
        "justify",
        "reverse",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CRow.Kwargs)] == [
        "tag",
        "gap",
        "align",
        "justify",
        "reverse",
        "wrap",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CCol.Slots)] == ["default"]
    assert [field.name for field in fields(CRow.Slots)] == ["default"]


def test_defaults_render_one_root_without_child_wrappers():
    row = CRow(slots={"default": "Actions"})
    html = _render(CCol(slots={"default": row}))

    assert len(re.findall(r'<[^>]+data-citry-ui-part="col"[^>]*>', html)) == 1
    assert len(re.findall(r'<[^>]+data-citry-ui-part="row"[^>]*>', html)) == 1
    assert 'data-gap="md"' in html
    assert 'data-align="stretch"' in html
    assert 'data-justify="start"' in html
    assert 'data-gap="sm"' in html
    assert 'data-align="center"' in html
    assert "cui-col__" not in html
    assert "cui-row__" not in html


def test_semantic_root_configuration_and_root_styling_merge():
    html = _render(
        CRow(
            tag="nav",
            gap="lg",
            align="baseline",
            justify="between",
            reverse=True,
            wrap=False,
            class_=["studio-actions", {"is-ready": True}],
            style={"--cui-row-gap": "2rem"},
            attrs={
                "aria-label": "Studio actions",
                "class": "from-attrs",
                "data-studio": "wheel-room",
            },
            slots={"default": "Actions"},
        )
    )

    tag = re.search(r"<nav[^>]+>", html)
    assert tag is not None
    root = tag.group(0)
    assert 'class="cui-row from-attrs studio-actions is-ready"' in root
    assert 'style="--cui-row-gap: 2rem;"' in root
    assert 'aria-label="Studio actions"' in root
    assert 'data-studio="wheel-room"' in root
    assert 'data-gap="lg"' in root
    assert 'data-align="baseline"' in root
    assert 'data-justify="between"' in root
    assert "data-reverse" in root
    assert "data-wrap" not in root


def test_empty_roots_are_valid_static_layout_destinations():
    assert '<div class="cui-col"' in _render(CCol())
    assert '<div class="cui-row"' in _render(CRow())


@pytest.mark.parametrize("component", [CCol, CRow])
@pytest.mark.parametrize(
    ("input_name", "bad_value", "error", "match"),
    [
        ("tag", 2, TypeError, "tag must be a string"),
        ("tag", "main", ValueError, "tag must be one of"),
        ("gap", "xxl", ValueError, "gap must be one of"),
        ("align", "left", ValueError, "align must be one of"),
        ("justify", "space-between", ValueError, "justify must be one of"),
        ("reverse", 1, TypeError, "reverse must be a bool"),
        ("attrs", [], TypeError, "attrs must be a mapping"),
    ],
)
def test_invalid_shared_inputs_fail_deterministically(component, input_name, bad_value, error, match):
    with pytest.raises(error, match=match):
        _render(component(**{input_name: bad_value}))


@pytest.mark.parametrize("bad_value", [1, "yes", None])
def test_group_wrap_requires_a_boolean(bad_value):
    with pytest.raises(TypeError, match="wrap must be a bool"):
        _render(CRow(wrap=bad_value))


@pytest.mark.parametrize(
    "attribute",
    [
        "data-citry-ui-part",
        "data-gap",
        "DATA-ALIGN",
        ":data-justify",
        "x-bind:data-reverse",
        "data-citry-morph",
        "data-cev-action",
        "data-cid",
        "x-bind",
        "x-if",
        "x-for",
        "x-teleport",
        "x-ignore",
        "x-html",
        "x-text",
        "x-model",
    ],
)
def test_stack_rejects_owned_runtime_and_structural_attributes(attribute):
    with pytest.raises(ValueError, match="cannot"):
        _render(CCol(attrs={attribute: "consumer"}))


def test_group_also_owns_wrap_but_allows_unrelated_bindings_and_listeners():
    with pytest.raises(ValueError, match="owned attribute"):
        _render(CRow(attrs={"data-wrap": False}))

    html = _render(
        CRow(
            attrs={
                "x-data": "{active: false}",
                ":class": "{active}",
                "@click": "active = true",
            }
        )
    )
    assert 'x-data="{active: false}"' in html
    assert ':class="{active}"' in html
    assert '@click="active = true"' in html


def test_css_uses_public_gap_inputs_and_no_component_javascript():
    css = read_component_source_css("cflow")

    assert "--_cui-col-gap: var(--cui-col-gap, 0.75rem)" in css
    assert "--_cui-row-gap: var(--cui-row-gap, 0.5rem)" in css
    assert ':where([data-citry-ui-part="col"] > *)' in css
    assert ':where([data-citry-ui-part="row"] > *)' in css
    assert getattr(CCol, "js", None) is None
    assert getattr(CRow, "js", None) is None
