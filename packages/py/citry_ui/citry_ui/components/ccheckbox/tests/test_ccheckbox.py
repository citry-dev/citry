from __future__ import annotations

import re
from dataclasses import fields

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CCheckbox


def _render(value: object) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "<main>{{ value }}</main>"

        def template_data(self, kwargs, slots):
            return {"value": value}

    return Page().render().serialize(deps_strategy="ignore")


def _root(html: str) -> str:
    match = re.search(r'<span[^>]+data-citry-ui-part="checkbox"[^>]*>', html)
    assert match is not None
    return match.group(0)


def _input(html: str) -> str:
    match = re.search(r'<input[^>]+data-citry-ui-part="input"[^>]*/>', html)
    assert match is not None
    return match.group(0)


def test_checkbox_schema_is_exact():
    assert [field.name for field in fields(CCheckbox.Kwargs)] == [
        "name",
        "value",
        "id",
        "checked",
        "indeterminate",
        "required",
        "disabled",
        "invalid",
        "variant",
        "size",
        "label_pos",
        "class_",
        "style",
        "attrs",
        "input_attrs",
    ]
    assert [field.name for field in fields(CCheckbox.Slots)] == ["default", "description"]


def test_checkbox_renders_explicit_label_and_sibling_description_without_static_runtime_mirrors():
    html = _render(
        CCheckbox(
            name="digest",
            value="weekly",
            checked=True,
            indeterminate=True,
            slots={"default": "Weekly digest", "description": "Every Friday"},
        )
    )
    root = _root(html)
    native_input = _input(html)

    assert root.startswith("<span")
    assert " data-checked" not in root
    assert " data-indeterminate" not in root
    assert 'type="checkbox"' in native_input
    assert " checked" in native_input
    assert "aria-checked" not in native_input
    input_id = re.search(r'id="([^"]+)"', native_input)
    assert input_id is not None
    assert f'<label for="{input_id.group(1)}" data-citry-ui-part="label">' in html
    assert f'id="{input_id.group(1)}-description" data-citry-ui-part="description"' in html
    assert f'aria-describedby="{input_id.group(1)}-description"' in native_input


def test_label_free_checkbox_requires_and_accepts_one_static_accessible_name():
    with pytest.raises(ValueError, match="requires aria-label or aria-labelledby"):
        _render(CCheckbox())

    html = _render(CCheckbox(input_attrs={"ARIA-LABEL": "Select fern row"}))
    assert 'aria-label="Select fern row"' in _input(html)
    assert 'data-citry-ui-part="label"' not in html

    with pytest.raises(ValueError, match="either aria-label or aria-labelledby"):
        _render(CCheckbox(input_attrs={"aria-label": "Fern", "aria-labelledby": "fern-label"}))


@pytest.mark.parametrize("attribute", ["aria-label", "aria-labelledby"])
def test_visible_label_rejects_hidden_aria_name_override(attribute):
    with pytest.raises(ValueError, match="cannot override"):
        _render(CCheckbox(input_attrs={attribute: "hidden-name"}, slots={"default": "Visible name"}))


def test_root_customization_and_native_attributes_land_on_distinct_destinations():
    html = _render(
        CCheckbox(
            class_="field-guide-choice",
            style={"--cui-checkbox-radius": "0.4rem"},
            attrs={"class": "from-attrs", "data-guide": "moss"},
            input_attrs={"autocomplete": "off", "data-native": "choice"},
            slots={"default": "Include moss"},
        )
    )
    root = _root(html)
    native_input = _input(html)

    assert "field-guide-choice" in root
    assert "from-attrs" in root
    assert "--cui-checkbox-radius: 0.4rem" in root
    assert 'data-guide="moss"' in root
    assert 'autocomplete="off"' in native_input
    assert 'data-native="choice"' in native_input
    assert "field-guide-choice" not in native_input


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"name": ""}, "name must be non-empty"),
        ({"value": "a\0b"}, r"U\+0000"),
        ({"id": "a\0b"}, r"U\+0000"),
        ({"id": "bad id"}, "cannot contain ASCII whitespace"),
        ({"checked": 1}, "checked must be a bool"),
        ({"indeterminate": None}, "indeterminate must be a bool"),
        ({"variant": "loud"}, "must be one of"),
        ({"size": "xl"}, "must be one of"),
        ({"label_pos": "left"}, "must be one of"),
    ],
)
def test_checkbox_rejects_invalid_direct_inputs(kwargs, message):
    with pytest.raises((TypeError, ValueError), match=message):
        _render(CCheckbox(**kwargs, slots={"default": "Choice"}))


def test_checkbox_detrusts_direct_safe_strings_and_normalizes_value_newlines():
    html = _render(
        CCheckbox(
            name=Markup('digest" onfocus="evil'),
            value=Markup("north\r\nsouth"),
            slots={"default": "Choice"},
        )
    )
    native_input = _input(html)

    assert ' onfocus="' not in native_input
    assert "digest&#34; onfocus=&#34;evil" in native_input
    assert 'value="north\nsouth"' in native_input


def test_checkbox_detrusts_safe_string_identity_before_label_association():
    html = _render(
        CCheckbox(
            id=Markup('choice"unsafe'),
            slots={"default": "Choice"},
        )
    )

    assert 'id="choice&#34;unsafe"' in html
    assert 'for="choice&#34;unsafe"' in html


@pytest.mark.parametrize(
    ("destination", "attribute"),
    [
        ("attrs", "for"),
        ("attrs", "aria-hidden"),
        ("attrs", "role"),
        ("attrs", "tabindex"),
        ("attrs", ":contenteditable"),
        ("attrs", "x-bind"),
        ("attrs", "x-html"),
        ("input_attrs", "role"),
        ("input_attrs", "aria-hidden"),
        ("input_attrs", "aria-checked"),
        ("input_attrs", "readonly"),
        ("input_attrs", "x-model"),
        ("input_attrs", ":form"),
        ("input_attrs", "x-bind:aria-describedby"),
        ("input_attrs", ".checked"),
    ],
)
def test_checkbox_rejects_owned_and_dynamic_attribute_paths(destination, attribute):
    kwargs = {destination: {attribute: "value"}, "slots": {"default": "Choice"}}
    with pytest.raises(ValueError, match="CCheckbox"):
        _render(CCheckbox(**kwargs))


def test_checkbox_rejects_duplicate_case_variants_for_singleton_attributes():
    with pytest.raises(ValueError, match="duplicate case variants"):
        _render(
            CCheckbox(
                input_attrs={"aria-describedby": "one", "ARIA-DESCRIBEDBY": "two"},
                slots={"default": "Choice"},
            )
        )


def test_checkbox_composes_with_field_and_merges_concrete_relationships():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <c-CField control_id="botanical-choice" required invalid>
            <c-fill name="label">Botanical choice</c-fill>
            <c-fill name="default">
              <c-CCheckbox
                name="botanical"
                c-input_attrs="{'ARIA-DESCRIBEDBY': 'external-help'}"
              />
            </c-fill>
            <c-fill name="description">Choose one preference.</c-fill>
            <c-fill name="error">This choice is required.</c-fill>
          </c-CField>
          <span id="external-help">External help.</span>
        """

    html = Page().render().serialize(deps_strategy="ignore")
    native_input = _input(html)

    assert 'id="botanical-choice"' in native_input
    assert " required" in native_input
    assert 'data-citry-field-supports-readonly="false"' in native_input
    assert 'aria-describedby="botanical-choice-description botanical-choice-error external-help"' in native_input
    assert 'aria-errormessage="botanical-choice-error"' in native_input
    assert html.count('data-citry-ui-part="label"') == 1


def test_checkbox_rejects_field_owned_slots_and_state():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class SlotConflict(Component):
        citry = app
        template = """
          <c-CField>
            <c-fill name="label">Field label</c-fill>
            <c-fill name="default">
              <c-CCheckbox required>Checkbox label</c-CCheckbox>
            </c-fill>
          </c-CField>
        """

    with pytest.raises(ValueError, match="cannot supply default or description"):
        str(SlotConflict())


def test_checkbox_rejects_inherited_field_readonly_but_allows_explicit_opt_out():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Rejected(Component):
        citry = app
        template = """
          <c-CForm readonly>
            <c-CField>
              <c-fill name="label">Choice</c-fill>
              <c-fill name="default"><c-CCheckbox /></c-fill>
            </c-CField>
          </c-CForm>
        """

    class Allowed(Component):
        citry = app
        template = """
          <c-CForm readonly>
            <c-CField c-readonly="False">
              <c-fill name="label">Choice</c-fill>
              <c-fill name="default"><c-CCheckbox /></c-fill>
            </c-CField>
          </c-CForm>
        """

    with pytest.raises(ValueError, match="readonly=True is not supported"):
        str(Rejected())
    assert 'type="checkbox"' in str(Allowed())


@pytest.mark.parametrize("omitted_value", [None, False])
def test_uppercase_omitted_form_attr_keeps_enclosing_form_owner(omitted_value):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return {"input_attrs": {"FORM": omitted_value}}

        template = """
          <c-CForm id="inside">
            <c-CCheckbox c-input_attrs="input_attrs">Choice</c-CCheckbox>
          </c-CForm>
        """

    assert 'type="checkbox"' in str(Page())


def test_checkbox_rejects_conflicting_cform_owner_case_insensitively():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <c-CForm id="inside">
            <c-CCheckbox c-input_attrs="{'FORM': 'outside'}">Choice</c-CCheckbox>
          </c-CForm>
        """

    with pytest.raises(ValueError, match="different native form owner"):
        str(Page())


def test_checkbox_assets_are_component_owned_and_do_not_author_aria_checked():
    assert "data-citry-checkbox-initialized" in CCheckbox.js
    assert "aria-checked" not in CCheckbox.js
    assert ":checked" in CCheckbox.css
    assert ":indeterminate" in CCheckbox.css
    assert "@layer citry-ui.theme" in CCheckbox.css
