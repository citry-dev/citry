"""Focused server contract tests for CTagsInput."""

from __future__ import annotations

import re
from dataclasses import fields

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cfield import CField
from citry_ui.components.ctags_input import (
    CTagsInput,
    CTagsInputChangeSource,
    CTagsInputInputValueChangeDetail,
    CTagsInputInvalidDetail,
    CTagsInputInvalidReason,
    CTagsInputMessages,
    CTagsInputSize,
    CTagsInputValueChangeDetail,
    CTagsInputVariant,
)


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-tags-input-tests", (CField, CTagsInput)))
    return app


def _render(template: str, data: dict[str, object] | None = None, *, css: bool = False) -> str:
    app = _app()
    source = template + ("<c-css />" if css else "")

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return data or {}

    page = Page()
    return str(page) if css else page.render().serialize(deps_strategy="ignore")


def _tags(extra: str = "") -> str:
    return f'<c-CTagsInput c-input_attrs="label" {extra} />'


def _tag(html: str, pattern: str) -> str:
    match = re.search(pattern, html)
    assert match is not None
    return match.group(0)


def test_schema_exports_and_public_records_are_exact() -> None:
    assert [item.name for item in fields(CTagsInput.Kwargs)] == [
        "name",
        "form",
        "id",
        "value",
        "input_value",
        "required",
        "disabled",
        "readonly",
        "invalid",
        "placeholder",
        "delimiters",
        "max_tags",
        "autocomplete",
        "inputmode",
        "variant",
        "size",
        "messages",
        "class_",
        "style",
        "attrs",
        "input_attrs",
    ]
    from citry_ui.components import ctags_input

    assert ctags_input.__all__ == [
        "CTagsInput",
        "CTagsInputChangeSource",
        "CTagsInputInputValueChangeDetail",
        "CTagsInputInvalidDetail",
        "CTagsInputInvalidReason",
        "CTagsInputMessages",
        "CTagsInputSize",
        "CTagsInputValueChangeDetail",
        "CTagsInputVariant",
    ]
    assert all(
        item is not None
        for item in (
            CTagsInputChangeSource,
            CTagsInputInputValueChangeDetail,
            CTagsInputInvalidDetail,
            CTagsInputInvalidReason,
            CTagsInputMessages,
            CTagsInputSize,
            CTagsInputValueChangeDetail,
            CTagsInputVariant,
        )
    )


def test_progressive_select_and_hidden_editor_share_ordered_values() -> None:
    html = _render(
        _tags('id="labels" name="label" form="ticket" c-value="values" input_value="draft" required'),
        {"label": {"aria-label": "Labels"}, "values": ("urgent", "billing")},
    )
    native = _tag(html, r"<select[^>]+data-citry-tags-input-native[^>]*>")
    editor = _tag(html, r'<input class="cui-tags-input__input"[^>]*>')
    root = _tag(html, r'<div class="cui-tags-input"[^>]*>')
    assert 'id="labels"' in native
    assert 'name="label"' in native
    assert 'form="ticket"' in native
    assert " required" in native
    assert 'aria-label="Labels"' in native
    assert 'id="labels-input"' in editor
    assert 'value="draft"' in editor
    assert 'aria-required="true"' in editor
    assert html.index('value="urgent" selected') < html.index('value="billing" selected')
    assert html.index('data-value="urgent"') < html.index('data-value="billing"')
    assert 'data-citry-ui-part="tags-input"' in root
    assert "data-required" in root
    assert "data-empty" not in root


def test_empty_reflections_and_exact_eight_public_descendant_parts() -> None:
    html = _render(_tags(), {"label": {"aria-label": "Labels"}})
    assert "data-empty" in _tag(html, r'<div class="cui-tags-input"[^>]*>')
    for part in ("control", "tag-list", "input", "status"):
        assert f'data-citry-ui-part="{part}"' in html
    assert 'data-citry-ui-part="tag"' not in html
    assert 'data-citry-ui-part="remove"' not in html


def test_readonly_submits_repeated_hidden_values_and_disables_proxy() -> None:
    html = _render(
        _tags('name="label" form="ticket" c-value="values" readonly required'),
        {"label": {"aria-label": "Labels"}, "values": ("a", "b")},
    )
    native = _tag(html, r"<select[^>]+data-citry-tags-input-native[^>]*>")
    assert " disabled" in native
    assert " name=" not in native
    assert " required" not in native
    assert html.count('<input name="label" form="ticket"') == 2
    assert len(re.findall(r'<button[^>]+disabled[^>]+data-citry-ui-part="remove"', html)) == 2


def test_disabled_excludes_native_and_hidden_transports() -> None:
    html = _render(
        _tags('name="label" c-value="values" readonly disabled'),
        {"label": {"aria-label": "Labels"}, "values": ("a", "b")},
    )
    native = _tag(html, r"<select[^>]+data-citry-tags-input-native[^>]*>")
    assert " disabled" in native
    assert " name=" not in native
    assert '<input name="label"' not in html


def test_field_owns_state_label_relationships_and_public_id() -> None:
    html = _render(
        """
          <c-CField control_id="labels" required readonly invalid>
            <c-fill name="label">Labels</c-fill>
            <c-fill name="default"><c-CTagsInput name="label" /></c-fill>
            <c-fill name="description">One or more labels</c-fill>
            <c-fill name="error">Fix labels</c-fill>
          </c-CField>
        """
    )
    native = _tag(html, r"<select[^>]+data-citry-tags-input-native[^>]*>")
    editor = _tag(html, r'<input class="cui-tags-input__input"[^>]*>')
    assert 'id="labels"' in native
    assert 'id="labels-input"' in editor
    assert "data-citry-field-control" in editor
    assert "data-citry-field-control" not in native
    assert 'aria-labelledby="labels-label"' in native
    assert 'aria-labelledby="labels-label"' in editor
    assert 'aria-describedby="labels-description labels-error"' in editor
    assert 'aria-required="true"' in editor
    assert 'for="labels"' in html


@pytest.mark.parametrize(
    ("extra", "data", "message"),
    [
        ("", {"label": {}}, "requires a static aria-label"),
        ("", {"label": {"aria-label": " \t"}}, "non-whitespace accessible text"),
        ("", {"label": {"aria-labelledby": "later"}}, "owned attribute"),
        ('c-value="value"', {"label": {"aria-label": "Labels"}, "value": "a"}, "sequence"),
        ('c-value="value"', {"label": {"aria-label": "Labels"}, "value": (" a",)}, "canonical"),
        ('c-value="value"', {"label": {"aria-label": "Labels"}, "value": ("a", "a")}, "unique"),
        ('c-value="value"', {"label": {"aria-label": "Labels"}, "value": ("a,b",)}, "delimiter"),
        ('c-delimiters="value"', {"label": {"aria-label": "Labels"}, "value": (" ",)}, "Unicode scalars"),
        ('c-delimiters="value"', {"label": {"aria-label": "Labels"}, "value": (",", ",")}, "unique"),
        ('max_tags="0"', {"label": {"aria-label": "Labels"}}, "positive integer"),
        ('c-value="value" max_tags="1"', {"label": {"aria-label": "Labels"}, "value": ("a", "b")}, "exceed"),
        (
            'c-input_value="value"',
            {"label": {"aria-label": "Labels"}, "value": "a\nb"},
            "cannot contain",
        ),
        ('variant="soft"', {"label": {"aria-label": "Labels"}}, "must be one of"),
    ],
)
def test_structural_input_validation_is_fail_fast(extra: str, data: dict[str, object], message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(_tags(extra), data)


def test_messages_validate_exact_placeholders_and_render_text_safely() -> None:
    messages = CTagsInputMessages(remove_label="Delete {value}")
    html = _render(
        _tags('c-value="value" c-messages="messages"'),
        {
            "label": {"aria-label": "Labels"},
            "value": ("<script>alert(1)</script>",),
            "messages": messages,
        },
    )
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert 'aria-label="Delete &lt;script&gt;alert(1)&lt;/script&gt;"' in html
    with pytest.raises(ValueError, match="unsupported placeholder"):
        _render(
            _tags('c-messages="messages"'),
            {
                "label": {"aria-label": "Labels"},
                "messages": CTagsInputMessages(remove_label="Remove {value.__class__}"),
            },
        )


@pytest.mark.parametrize(
    ("destination", "attrs"),
    [
        ("attrs", {"id": "hostile"}),
        ("attrs", {"x-data": "{}"}),
        ("attrs", {":data-empty": "false"}),
        ("input_attrs", {"id": "hostile"}),
        ("input_attrs", {"aria-labelledby": "missing"}),
        ("input_attrs", {":placeholder": "value"}),
        ("input_attrs", {"data-citry-hostile": "yes"}),
    ],
)
def test_owned_static_dynamic_and_runtime_attributes_are_rejected(
    destination: str,
    attrs: dict[str, object],
) -> None:
    data = {"label": {"aria-label": "Labels"}, destination: attrs}
    extra = f'c-{destination}="{destination}"'
    if destination == "attrs":
        extra += ' c-input_attrs="label"'
        template = f"<c-CTagsInput {extra} />"
    else:
        template = f"<c-CTagsInput {extra} />"
    with pytest.raises(ValueError, match="cannot override owned attribute"):
        _render(template, data)


def test_direct_python_composition_and_empty_slot_contract() -> None:
    app = _app()

    class Page(Component):
        citry = app
        template = "{{ tags }}"

        def template_data(self, kwargs, slots):
            return {
                "tags": CTagsInput(
                    name="label",
                    value=("a", "b"),
                    input_attrs={"aria-label": "Labels"},
                )
            }

    html = Page().render().serialize(deps_strategy="ignore")
    assert html.count("<option") == 2
    with pytest.raises((TypeError, ValueError)):
        CTagsInput(input_attrs={"aria-label": "Labels"}, slots={"default": "owned"}).render(citry=app)


def test_css_contains_public_variables_parts_and_environment_profiles() -> None:
    html = _render(_tags(), {"label": {"aria-label": "Labels"}}, css=True)
    for name in (
        "--cui-tags-input-background",
        "--cui-tags-input-tag-highlighted-background",
        "--cui-tags-input-font-size",
    ):
        assert name in html
    assert "@media (forced-colors:active)" in html
    assert "@media print" in html
    assert ".cui-form-control__native--enhanced" in html
