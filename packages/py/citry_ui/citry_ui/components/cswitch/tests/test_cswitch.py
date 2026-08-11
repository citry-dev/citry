from __future__ import annotations

import re
from dataclasses import fields

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CSwitch


def _render(template: str, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    template_source = template

    class Page(Component):
        citry = app
        template = template_source

    html = str(Page())
    return html + (str(app.get("css")()) if include_css else "")


def test_switch_schema_is_concise_and_explicit():
    assert [field.name for field in fields(CSwitch.Kwargs)] == [
        "name",
        "value",
        "id",
        "checked",
        "required",
        "disabled",
        "invalid",
        "size",
        "label_pos",
        "class_",
        "style",
        "attrs",
        "input_attrs",
    ]
    assert [field.name for field in fields(CSwitch.Slots)] == ["default", "description"]


def test_switch_renders_native_checkbox_switch_semantics_and_parts():
    html = _render(
        """
          <c-CSwitch name="night" value="enabled" checked required>
            <c-fill name="default">Night lighting</c-fill>
            <c-fill name="description">Use warm path lights after sunset.</c-fill>
          </c-CSwitch>
        """
    )

    input_tag = re.search(r"<input[^>]+>", html)
    assert input_tag is not None
    assert 'type="checkbox"' in input_tag.group(0)
    assert 'role="switch"' in input_tag.group(0)
    assert 'name="night"' in input_tag.group(0)
    assert 'value="enabled"' in input_tag.group(0)
    assert "checked" in input_tag.group(0)
    assert "required" in input_tag.group(0)
    assert 'data-citry-ui-part="track"' in html
    assert 'data-citry-ui-part="thumb"' in html
    assert "aria-checked" not in input_tag.group(0)


def test_switch_requires_one_accessible_name_and_protects_visible_label():
    with pytest.raises(ValueError, match="requires input_attrs ARIA naming"):
        _render("<c-CSwitch />")
    with pytest.raises(ValueError, match="cannot replace its visible"):
        _render("<c-CSwitch c-input_attrs=\"{'aria-label': 'Hidden'}\">Visible</c-CSwitch>")
    html = _render("<c-CSwitch c-input_attrs=\"{'aria-label': 'Night lighting'}\" />")
    assert 'aria-label="Night lighting"' in html


def test_switch_merges_root_styling_and_routes_input_attrs():
    html = _render(
        """
          <c-CSwitch
            class_="garden-switch"
            c-style="{'--cui-switch-on-color': 'green'}"
            c-attrs="{'data-owner': 'garden'}"
            c-input_attrs="{'data-native': 'switch'}"
          >Irrigation</c-CSwitch>
        """
    )

    assert 'class="cui-switch garden-switch"' in html
    assert 'style="--cui-switch-on-color: green;"' in html
    assert 'data-owner="garden"' in html
    assert 'data-native="switch"' in html


@pytest.mark.parametrize(
    ("attribute", "destination"),
    [
        ("role", "attrs"),
        ("tabindex", "attrs"),
        ("aria-hidden", "attrs"),
        ("x-if", "attrs"),
        ("data-citry-morph", "attrs"),
        ("type", "input_attrs"),
        ("role", "input_attrs"),
        ("aria-checked", "input_attrs"),
        (":checked", "input_attrs"),
        ("x-model", "input_attrs"),
    ],
)
def test_switch_rejects_competing_semantics_and_ownership(attribute, destination):
    with pytest.raises(ValueError, match=r"owned|ownership|reserved"):
        _render(f"<c-CSwitch c-{destination}=\"{{'{attribute}': 'x'}}\">Irrigation</c-CSwitch>")


def test_switch_validates_exact_strings_booleans_and_choices():
    with pytest.raises(ValueError, match="non-empty"):
        _render("<c-CSwitch c-name=\"''\">Irrigation</c-CSwitch>")
    with pytest.raises(ValueError, match=r"U\+0000"):
        _render("<c-CSwitch c-value=\"'a\\0b'\">Irrigation</c-CSwitch>")
    with pytest.raises(TypeError, match="checked"):
        _render('<c-CSwitch checked="yes">Irrigation</c-CSwitch>')
    with pytest.raises(ValueError, match="size"):
        _render('<c-CSwitch size="xl">Irrigation</c-CSwitch>')


def test_switch_field_composition_uses_field_ownership():
    html = _render(
        """
          <c-CField control_id="garden-lights" required>
            <c-fill name="label">Garden lights</c-fill>
            <c-fill name="default"><c-CSwitch name="lights" /></c-fill>
            <c-fill name="description">Use after dusk.</c-fill>
          </c-CField>
        """
    )

    assert 'id="garden-lights"' in html
    assert "data-citry-field-control" in html
    assert "required" in html
    assert 'aria-describedby="garden-lights-description"' in html


def test_switch_css_declares_public_parts_variables_and_environment_rules():
    html = _render("<c-CSwitch>Garden lights</c-CSwitch>", include_css=True)

    for variable in (
        "--cui-switch-off-color",
        "--cui-switch-on-color",
        "--cui-switch-thumb-color",
        "--cui-switch-width",
        "--cui-switch-duration",
    ):
        assert variable in html
    assert "prefers-reduced-motion" in html
    assert "forced-colors" in html
    assert "@media print" in html
