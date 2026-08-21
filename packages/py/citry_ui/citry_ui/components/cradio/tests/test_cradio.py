from __future__ import annotations

import re
from dataclasses import fields

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CRadio, CRadioGroup
from citry_ui.quality.asset_sources import read_component_source_css


def _render(template: str, data: dict[str, object] | None = None, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    page_template = template

    class Page(Component):
        citry = app
        template = page_template

        def template_data(self, kwargs, slots):
            return dict(data or {})

    html = str(Page())
    return html + (str(app.get("css")()) if include_css else "")


def test_radio_schemas_keep_group_and_item_ownership_separate():
    assert [field.name for field in fields(CRadioGroup.Kwargs)] == [
        "name",
        "value",
        "form",
        "required",
        "disabled",
        "invalid",
        "orientation",
        "variant",
        "size",
        "label_pos",
        "id",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CRadioGroup.Slots)] == ["default", "label"]
    assert [field.name for field in fields(CRadio.Kwargs)] == [
        "value",
        "disabled",
        "class_",
        "style",
        "attrs",
        "input_attrs",
    ]
    assert [field.name for field in fields(CRadio.Slots)] == ["default", "description"]


def test_standalone_group_renders_native_fieldset_legend_and_radios():
    html = _render(
        """
          <c-CRadioGroup name="destination" value="moon" required orientation="horizontal">
            <c-fill name="label">Destination</c-fill>
            <c-fill name="default">
              <c-CRadio value="moon">Moon</c-CRadio>
              <c-CRadio value="mars">
                <c-fill name="default">Mars</c-fill>
                <c-fill name="description">A longer transfer.</c-fill>
              </c-CRadio>
            </c-fill>
          </c-CRadioGroup>
        """
    )

    assert '<fieldset class="cui-radio-group"' in html
    assert '<legend data-citry-ui-part="legend">' in html
    assert "Destination" in html
    radio_inputs = re.findall(r'<input[^>]+type="radio"[^>]*>', html)
    assert len(radio_inputs) == 2
    assert all('name="destination"' in input_html for input_html in radio_inputs)
    assert 'value="moon" checked' in html
    assert "data-required" in html
    assert 'data-orientation="horizontal"' in html
    assert 'data-value="moon"' in html
    assert "aria-describedby=" in html


def test_group_and_item_root_styling_and_form_owner_reach_exact_destinations():
    html = _render(
        """
          <c-CRadioGroup
            name="lens"
            form="survey"
            class_="group-class"
            c-style="{'--cui-radio-group-gap': '20px'}"
            c-attrs="{'data-owner': 'catalog'}"
          >
            <c-fill name="label">Lens</c-fill>
            <c-fill name="default">
              <c-CRadio
                value="wide"
                class_="item-class"
                c-attrs="{'data-item': 'wide'}"
                c-input_attrs="{'data-input': 'wide'}"
              >Wide</c-CRadio>
            </c-fill>
          </c-CRadioGroup>
        """
    )

    assert 'class="cui-radio-group group-class"' in html
    assert 'style="--cui-radio-group-gap: 20px;"' in html
    assert 'data-owner="catalog"' in html
    assert 'class="cui-radio item-class"' in html
    assert 'data-item="wide"' in html
    assert 'data-input="wide"' in html
    assert 'form="survey"' in html


def test_radio_requires_group_and_group_requires_label_and_items():
    with pytest.raises(ValueError, match="inside CRadioGroup"):
        _render("<c-CRadio value='moon'>Moon</c-CRadio>")
    with pytest.raises(ValueError, match="requires a label slot"):
        _render(
            """
              <c-CRadioGroup name="destination">
                <c-CRadio value="moon">Moon</c-CRadio>
              </c-CRadioGroup>
            """
        )
    with pytest.raises(ValueError, match="at least one descendant"):
        _render(
            """
              <c-CRadioGroup name="destination">
                <c-fill name="label">Destination</c-fill>
                <c-fill name="default"><span>No options</span></c-fill>
              </c-CRadioGroup>
            """
        )


def test_group_rejects_duplicate_and_unknown_values():
    with pytest.raises(ValueError, match="value to be unique"):
        _render(
            """
              <c-CRadioGroup name="destination">
                <c-fill name="label">Destination</c-fill>
                <c-fill name="default">
                  <c-CRadio value="moon">Moon</c-CRadio>
                  <c-CRadio value="moon">Moon again</c-CRadio>
                </c-fill>
              </c-CRadioGroup>
            """
        )
    with pytest.raises(ValueError, match="does not match"):
        _render(
            """
              <c-CRadioGroup name="destination" value="venus">
                <c-fill name="label">Destination</c-fill>
                <c-fill name="default"><c-CRadio value="moon">Moon</c-CRadio></c-fill>
              </c-CRadioGroup>
            """
        )


@pytest.mark.parametrize(
    ("attribute", "destination"),
    [
        ("role", "group"),
        ("tabindex", "group"),
        ("aria-hidden", "group"),
        ("disabled", "group"),
        ("data-value", "group"),
        ("x-bind", "group"),
        ("x-if", "group"),
        ("data-citry-morph", "group"),
        ("role", "item"),
        ("for", "item"),
        ("data-checked", "item"),
        ("type", "input"),
        ("name", "input"),
        ("checked", "input"),
        ("aria-label", "input"),
        (":disabled", "input"),
    ],
)
def test_owned_runtime_and_semantic_attributes_are_rejected(attribute, destination):
    group_attrs = {attribute: "consumer"} if destination == "group" else {}
    item_attrs = {attribute: "consumer"} if destination == "item" else {}
    input_attrs = {attribute: "consumer"} if destination == "input" else {}
    with pytest.raises(ValueError, match="cannot"):
        _render(
            """
              <c-CRadioGroup name="destination" c-attrs="group_attrs">
                <c-fill name="label">Destination</c-fill>
                <c-fill name="default">
                  <c-CRadio value="moon" c-attrs="item_attrs" c-input_attrs="input_attrs">Moon</c-CRadio>
                </c-fill>
              </c-CRadioGroup>
            """,
            {"group_attrs": group_attrs, "item_attrs": item_attrs, "input_attrs": input_attrs},
        )


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"name": ""}, ValueError, "name must be non-empty"),
        ({"name": 4}, TypeError, "name must be a string"),
        ({"name": "choice", "required": "yes"}, TypeError, "required must be a bool"),
        ({"name": "choice", "orientation": "diagonal"}, ValueError, "orientation must be one of"),
        ({"name": "choice", "variant": "plain"}, ValueError, "variant must be one of"),
        ({"name": "choice", "size": "xl"}, ValueError, "size must be one of"),
        ({"name": "choice", "label_pos": "above"}, ValueError, "label_pos must be one of"),
    ],
)
def test_invalid_group_inputs_fail_deterministically(kwargs, error, match):
    group = CRadioGroup(**kwargs, slots={"label": "Choice", "default": CRadio(value="a", slots={"default": "A"})})
    with pytest.raises(error, match=match):
        _render("{{ group }}", {"group": group})


def test_safe_string_values_are_detrusted_and_canonicalized():
    html = _render(
        """
          <c-CRadioGroup c-name="name" c-value="value">
            <c-fill name="label">Destination</c-fill>
            <c-fill name="default"><c-CRadio c-value="value">Moon</c-CRadio></c-fill>
          </c-CRadioGroup>
        """,
        {"name": Markup('orbit" data-evil="x'), "value": Markup("moon\r\nbase")},
    )
    assert 'name="orbit&#34; data-evil=&#34;x"' in html
    assert 'value="moon\nbase"' in html


def test_css_exposes_group_item_and_environment_contract():
    css = read_component_source_css("cradio")

    for variable in (
        "group-gap",
        "active-color",
        "border-color",
        "background",
        "foreground",
        "focus-color",
        "invalid-color",
        "control-size",
        "item-gap",
        "label-gap",
        "disabled-opacity",
    ):
        assert f"--_cui-radio-{variable}: var(" in css
        assert f"--cui-radio-{variable}" in css
    assert "forced-colors: active" in css
    assert "@media print" in css
