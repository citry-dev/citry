from __future__ import annotations

import re
from dataclasses import fields

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CGroup, CStack


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
    assert [field.name for field in fields(CStack.Kwargs)] == [
        "tag",
        "gap",
        "align",
        "justify",
        "reverse",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CGroup.Kwargs)] == [
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
    assert [field.name for field in fields(CStack.Slots)] == ["default"]
    assert [field.name for field in fields(CGroup.Slots)] == ["default"]


def test_defaults_render_one_root_without_child_wrappers():
    group = CGroup(slots={"default": "Actions"})
    html = _render(CStack(slots={"default": group}))

    assert len(re.findall(r'<[^>]+data-citry-ui-part="stack"[^>]*>', html)) == 1
    assert len(re.findall(r'<[^>]+data-citry-ui-part="group"[^>]*>', html)) == 1
    assert 'data-gap="md"' in html
    assert 'data-align="stretch"' in html
    assert 'data-justify="start"' in html
    assert 'data-gap="sm"' in html
    assert 'data-align="center"' in html
    assert "cui-stack__" not in html
    assert "cui-group__" not in html


def test_semantic_root_configuration_and_root_styling_merge():
    html = _render(
        CGroup(
            tag="nav",
            gap="lg",
            align="baseline",
            justify="between",
            reverse=True,
            wrap=False,
            class_=["studio-actions", {"is-ready": True}],
            style={"--cui-group-gap": "2rem"},
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
    assert 'class="cui-group from-attrs studio-actions is-ready"' in root
    assert 'style="--cui-group-gap: 2rem;"' in root
    assert 'aria-label="Studio actions"' in root
    assert 'data-studio="wheel-room"' in root
    assert 'data-gap="lg"' in root
    assert 'data-align="baseline"' in root
    assert 'data-justify="between"' in root
    assert "data-reverse" in root
    assert "data-wrap" not in root


def test_empty_roots_are_valid_static_layout_destinations():
    assert '<div class="cui-stack"' in _render(CStack())
    assert '<div class="cui-group"' in _render(CGroup())


@pytest.mark.parametrize("component", [CStack, CGroup])
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
        _render(CGroup(wrap=bad_value))


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
        _render(CStack(attrs={attribute: "consumer"}))


def test_group_also_owns_wrap_but_allows_unrelated_bindings_and_listeners():
    with pytest.raises(ValueError, match="owned attribute"):
        _render(CGroup(attrs={"data-wrap": False}))

    html = _render(
        CGroup(
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
    css = _render(CStack(slots={"default": CGroup()}), include_css=True)

    assert "--_cui-stack-gap: var(--cui-stack-gap, 0.75rem)" in css
    assert "--_cui-group-gap: var(--cui-group-gap, 0.5rem)" in css
    assert ':where([data-citry-ui-part="stack"] > *)' in css
    assert ':where([data-citry-ui-part="group"] > *)' in css
    assert getattr(CStack, "js", None) is None
    assert getattr(CGroup, "js", None) is None
