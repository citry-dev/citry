from __future__ import annotations

import re
from dataclasses import fields

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component, Const
from citry_ui import CField, CForm, CTextarea


def _render(value: object) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>{{ value }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"value": value}

    return Page().render().serialize(deps_strategy="ignore")


def _root(html: str) -> str:
    match = re.search(r'<textarea[^>]+data-citry-ui-part="textarea"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_textarea_schema_exposes_native_and_presentation_inputs_without_slots():
    assert [field.name for field in fields(CTextarea.Kwargs)] == [
        "name",
        "id",
        "value",
        "rows",
        "cols",
        "wrap",
        "required",
        "disabled",
        "readonly",
        "invalid",
        "autocomplete",
        "inputmode",
        "placeholder",
        "variant",
        "size",
        "resize",
        "class_",
        "style",
        "attrs",
    ]
    assert fields(CTextarea.Slots) == ()


def test_textarea_defaults_render_one_native_control():
    html = _render(CTextarea(name="journal"))
    root = _root(html)

    assert html.count("<textarea") == 1
    assert 'name="journal"' in root
    assert 'rows="4"' in root
    assert 'wrap="soft"' in root
    assert 'data-variant="outline"' in root
    assert 'data-size="md"' in root
    assert 'data-resize="vertical"' in root
    assert "<textarea" in html
    assert "></textarea>" in html


def test_textarea_preserves_native_text_and_escapes_trusted_string_subclasses():
    hostile = Markup('\n</textarea><script id="escaped-script">bad()</script>&')
    html = _render(CTextarea(value=hostile))

    assert html.count("<textarea") == 1
    assert '<script id="escaped-script">' not in html
    assert "&lt;/textarea&gt;&lt;script id=&#34;escaped-script&#34;&gt;bad()&lt;/script&gt;&amp;" in html
    assert re.search(r'data-citry-ui-part="textarea"[^>]*>\n\n&lt;/textarea&gt;', html) is not None


def test_textarea_accepts_static_template_numeric_attributes():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <c-CTextarea rows="6" cols="48" wrap="hard" />
        """

    root = _root(Page().render().serialize(deps_strategy="ignore"))

    assert 'rows="6"' in root
    assert 'cols="48"' in root
    assert 'wrap="hard"' in root


@pytest.mark.parametrize(
    ("kwargs", "error", "message"),
    [
        ({"name": ""}, ValueError, "name must be non-empty"),
        ({"id": "two words"}, ValueError, "cannot contain ASCII whitespace"),
        ({"value": 3}, TypeError, "value must be a string or None"),
        ({"rows": 0}, ValueError, "rows must be greater than zero"),
        ({"rows": True}, TypeError, "rows must be a positive integer"),
        ({"cols": 0}, ValueError, "cols must be greater than zero"),
        ({"wrap": "hard"}, ValueError, "wrap='hard' requires cols"),
        ({"wrap": "physical"}, ValueError, "wrap must be one of"),
        ({"variant": "raised"}, ValueError, "variant must be one of"),
        ({"size": "xl"}, ValueError, "size must be one of"),
        ({"resize": "auto"}, ValueError, "resize must be one of"),
        ({"required": 1}, TypeError, "required must be a bool"),
        ({"attrs": "id=notes"}, TypeError, "attrs must be a mapping"),
        ({"attrs": {"rows": 9}}, ValueError, "cannot override owned attribute"),
        ({"attrs": {"data-citry-root": "x"}}, ValueError, "reserved Citry runtime attribute"),
    ],
)
def test_textarea_rejects_invalid_server_inputs(kwargs, error, message):
    with pytest.raises(error, match=message):
        _render(CTextarea(**kwargs))


def test_non_string_html_protocol_objects_are_rejected_before_rendering():
    class TrustedValue:
        def __html__(self):
            return "</textarea><script>bad()</script>"

    with pytest.raises(TypeError, match="value must be a string or None"):
        _render(CTextarea(value=TrustedValue()))


def test_direct_string_inputs_are_plain_text_but_attrs_remain_trusted_code():
    html = _render(
        CTextarea(
            name=Markup('notes" autofocus onfocus="bad()'),
            placeholder=Markup('<write "here">'),
            attrs={"data-workflow": "journal", "minlength": 8},
        )
    )
    root = _root(html)

    assert 'name="notes&#34; autofocus onfocus=&#34;bad()"' in root
    assert 'placeholder="&lt;write &#34;here&#34;&gt;"' in root
    assert 'data-workflow="journal"' in root
    assert 'minlength="8"' in root


def test_root_class_style_and_attrs_merge_on_the_native_textarea():
    root = _root(
        _render(
            CTextarea(
                class_=["journal-note", {"is-featured": True}],
                style={"--cui-textarea-radius": "1rem"},
                attrs={"class": "from-attrs", "data-probe": "notes"},
            )
        )
    )

    assert "cui-textarea" in root
    assert "journal-note" in root
    assert "is-featured" in root
    assert "from-attrs" in root
    assert "--cui-textarea-radius: 1rem" in root
    assert 'data-probe="notes"' in root


def test_field_owns_state_relationships_and_control_id():
    html = _render(
        CField(
            control_id="observation",
            required=True,
            invalid=True,
            slots={
                "label": "Observation",
                "default": CTextarea(name="observation"),
                "description": "Use plain language.",
                "error": "Add an observation.",
            },
        )
    )
    root = _root(html)

    assert 'id="observation"' in root
    assert "required" in root
    assert 'aria-invalid="true"' in root
    assert 'aria-describedby="observation-description observation-error"' in root
    assert 'aria-errormessage="observation-error"' in root
    assert FIELD_MARKER in root


FIELD_MARKER = "data-citry-field-control"


@pytest.mark.parametrize("input_name", ["required", "disabled", "readonly", "invalid"])
def test_textarea_cannot_override_field_owned_state(input_name):
    with pytest.raises(ValueError, match="Field-owned state"):
        _render(
            CField(
                slots={
                    "label": "Observation",
                    "default": CTextarea(**{input_name: False}),
                }
            )
        )


def test_form_state_and_native_owner_apply_to_textarea():
    html = _render(
        CForm(
            id="journal-form",
            disabled=True,
            readonly=True,
            slots={"default": CTextarea(name="notes")},
        )
    )
    root = _root(html)

    assert "disabled" in root
    assert "readonly" in root
    assert "data-disabled" in root
    assert "data-readonly" in root


def test_textarea_rejects_a_conflicting_form_owner_and_field_id():
    with pytest.raises(ValueError, match="different native form owner"):
        _render(
            CForm(
                id="journal-form",
                slots={"default": CTextarea(attrs={"FORM": "other-form"})},
            )
        )

    with pytest.raises(ValueError, match="dynamically bind HTML attribute 'form'"):
        _render(CTextarea(attrs={":form": "owner"}))

    with pytest.raises(ValueError, match="conflicts with its CField control_id"):
        _render(
            CField(
                control_id="expected",
                slots={"label": "Observation", "default": CTextarea(id="different")},
            )
        )


@pytest.mark.parametrize("omitted_value", [None, False])
def test_textarea_omitted_case_insensitive_form_attr_keeps_enclosing_owner(omitted_value):
    root = _root(
        _render(
            CForm(
                id="inside",
                slots={"default": CTextarea(attrs={"FORM": omitted_value})},
            )
        )
    )

    assert " form=" not in root.lower()


def test_textarea_merges_case_insensitive_external_idrefs():
    root = _root(
        _render(
            CField(
                control_id="observation",
                invalid=True,
                slots={
                    "label": "Observation",
                    "description": "Describe the habitat.",
                    "error": "Add an observation.",
                    "default": CTextarea(
                        attrs={
                            "ARIA-DESCRIBEDBY": "external observation-description",
                            "ARIA-ERRORMESSAGE": "external-error",
                        }
                    ),
                },
            )
        )
    )

    assert 'aria-describedby="observation-description observation-error external"' in root
    assert 'aria-errormessage="observation-error external-error"' in root


def test_textarea_has_component_javascript_without_global_retained_resources():
    app = Citry(autodiscover=False)
    installation = app.register_library(citry_ui)
    javascript = installation[CTextarea].get_js()

    assert javascript is not None
    assert "MutationObserver" not in javascript
    assert "setInterval" not in javascript
    assert "document.addEventListener" not in javascript
    assert 'removeEventListener("compositionend", onCompositionEnd)' in javascript
    assert "clearTimeout(reconcileTimer)" in javascript


def test_const_safe_string_uses_the_same_de_trusted_value_pipeline():
    html = _render(CTextarea(value=Const(Markup("</textarea><b>safe text</b>"))))

    assert html.count("<textarea") == 1
    assert "&lt;/textarea&gt;&lt;b&gt;safe text&lt;/b&gt;" in html
    assert "<b>safe text</b>" not in html
