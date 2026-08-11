from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CDivider


def _render(divider: object, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>{{ divider }}</main>{{ css }}
        """

        def template_data(self, kwargs, slots):
            return {
                "divider": divider,
                "css": app.get("css")() if include_css else "",
            }

    return str(Page())


def _root(html: str) -> str:
    match = re.search(r'<(?:hr|div)[^>]+data-citry-ui-part="divider"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_divider_schema_is_small_and_runtime_introspectable():
    assert [field.name for field in fields(CDivider.Kwargs)] == [
        "orientation",
        "variant",
        "size",
        "inset",
        "label_pos",
        "decorative",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CDivider.Slots)] == ["default"]
    assert get_type_hints(CDivider.Kwargs)["orientation"] is not None


def test_default_is_one_native_horizontal_thematic_break():
    html = _render(CDivider())
    root = _root(html)

    assert root.startswith("<hr")
    assert 'data-orientation="horizontal"' in root
    assert 'data-variant="solid"' in root
    assert 'data-size="sm"' in root
    assert 'data-inset="none"' in root
    assert "data-decorative" not in root
    assert "aria-hidden" not in root
    assert "role=" not in root
    assert "aria-orientation" not in root
    assert "tabindex" not in root


def test_decorative_and_vertical_semantics_are_exact():
    decorative = _root(_render(CDivider(decorative=True)))
    vertical = _root(_render(CDivider(orientation="vertical")))
    vertical_decorative = _root(_render(CDivider(orientation="vertical", decorative=True)))

    assert decorative.startswith("<hr")
    assert "data-decorative" in decorative
    assert "aria-hidden" in decorative
    assert vertical.startswith("<div")
    assert 'role="separator"' in vertical
    assert 'aria-orientation="vertical"' in vertical
    assert "aria-hidden" not in vertical
    assert "data-decorative" not in vertical
    assert vertical_decorative.startswith("<div")
    assert "data-decorative" in vertical_decorative
    assert "aria-hidden" in vertical_decorative
    assert "role=" not in vertical_decorative
    assert "aria-orientation" not in vertical_decorative


def test_labelled_divider_has_one_neutral_root_two_hidden_lines_and_one_label():
    html = _render(
        CDivider(
            variant="dashed",
            size="md",
            inset="both",
            label_pos="start",
            slots={"default": "Outer planets"},
        )
    )
    root = _root(html)

    assert root.startswith("<div")
    assert "role=" not in root
    assert "aria-orientation" not in root
    assert "aria-hidden" not in root
    assert "data-labeled" in root
    assert "data-decorative" in root
    assert 'data-label-pos="start"' in root
    assert 'data-variant="dashed"' in root
    assert 'data-size="md"' in root
    assert 'data-inset="both"' in root
    assert len(re.findall(r'<hr[^>]+data-citry-ui-part="line"[^>]+aria-hidden="true"', html)) == 2
    assert len(re.findall(r'<span[^>]+data-citry-ui-part="label"', html)) == 1
    assert "Outer planets" in html


def test_root_styling_and_trusted_attributes_merge_on_every_anatomy():
    for divider in (
        CDivider(
            class_=["orbit", {"visible": True}],
            style={"--cui-divider-color": "purple"},
            attrs={"class": "from-attrs", "data-chart": "north"},
        ),
        CDivider(
            class_="orbit",
            style="--cui-divider-color: purple",
            attrs={"data-chart": "north"},
            slots={"default": "North"},
        ),
    ):
        root = _root(_render(divider))
        assert "cui-divider" in root
        assert "orbit" in root
        assert 'style="--cui-divider-color: purple;' in root
        assert 'data-chart="north"' in root


@pytest.mark.parametrize(
    ("input_name", "bad_value", "error", "match"),
    [
        ("orientation", 2, TypeError, "orientation must be a string"),
        ("orientation", "diagonal", ValueError, "orientation must be one of"),
        ("variant", "double", ValueError, "variant must be one of"),
        ("size", "xl", ValueError, "size must be one of"),
        ("inset", "middle", ValueError, "inset must be one of"),
        ("label_pos", "left", ValueError, "label_pos must be one of"),
        ("decorative", 1, TypeError, "decorative must be a bool"),
        ("attrs", [], TypeError, "attrs must be a mapping"),
    ],
)
def test_invalid_inputs_fail_deterministically(input_name, bad_value, error, match):
    with pytest.raises(error, match=match):
        _render(CDivider(**{input_name: bad_value}))


def test_invalid_label_combinations_fail_before_rendering():
    with pytest.raises(ValueError, match="label with vertical"):
        _render(CDivider(orientation="vertical", slots={"default": "Invalid"}))
    with pytest.raises(ValueError, match="label_pos requires"):
        _render(CDivider(label_pos="start"))


@pytest.mark.parametrize(
    "attribute",
    [
        "data-citry-ui-part",
        "DATA-ORIENTATION",
        "data-variant",
        "data-size",
        "data-inset",
        "data-labeled",
        "data-label-pos",
        "data-decorative",
        "role",
        "aria-orientation",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "tabindex",
        "contenteditable",
        ":role",
        "x-bind:aria-hidden",
        ".data-orientation",
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
def test_divider_rejects_owned_runtime_and_structural_attributes(attribute):
    with pytest.raises(ValueError, match="cannot"):
        _render(CDivider(attrs={attribute: "consumer"}))


def test_unrelated_bindings_visibility_and_listeners_remain_available():
    html = _render(
        CDivider(
            attrs={
                "x-data": "{shown: true}",
                "x-show": "shown",
                ":class": "{active: shown}",
                "@click": "shown = false",
            }
        )
    )

    assert 'x-data="{shown: true}"' in html
    assert 'x-show="shown"' in html
    assert ':class="{active: shown}"' in html
    assert '@click="shown = false"' in html


def test_direct_choices_are_detrusted_and_label_text_is_escaped():
    with pytest.raises(ValueError, match="variant must be one of"):
        _render(CDivider(variant=Markup('solid" onfocus="evil')))

    html = _render(CDivider(slots={"default": '<script id="evil">x</script>'}))
    assert "&lt;script" in html
    assert '<script id="evil">' not in html


def test_css_exposes_every_public_variable_and_no_component_javascript():
    css = _render(CDivider(), include_css=True)

    for variable in (
        "color",
        "thickness",
        "inset",
        "label-gap",
        "label-color",
        "label-font-size",
        "label-font-weight",
        "min-length",
    ):
        assert f"--_cui-divider-{variable}: var(--cui-divider-{variable}," in css
    assert "@media (forced-colors: active)" in css
    assert "@media print" in css
    assert getattr(CDivider, "js", None) is None
