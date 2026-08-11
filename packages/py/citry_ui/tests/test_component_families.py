"""Pressure tests for Field/Input, semantic Table, and server-rendered Tabs."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from dataclasses import fields

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import (
    CAlert,
    CButton,
    CCard,
    CCheckbox,
    CCombobox,
    CComboboxOption,
    CDialog,
    CDrawer,
    CField,
    CForm,
    CIcon,
    CInput,
    CNativeSelect,
    CNativeSelectOption,
    CTab,
    CTable,
    CTableCell,
    CTableColumn,
    CTableRow,
    CTabPanel,
    CTabs,
    CTextarea,
    CToastMessage,
    CToastRegion,
)


def _page_html(app: Citry, value: object, *, include_css: bool = False) -> str:
    class Page(Component):
        citry = app
        template = """
          <main>{{ value }}</main>{{ css }}
        """

        def template_data(self, kwargs, slots):
            return {
                "value": value,
                "css": app.get("css")() if include_css else "",
            }

    return str(Page())


def test_every_public_styled_component_exposes_root_class_and_style_inputs():
    # One immutable installation covers the whole public-input matrix; the
    # assertions exercise component roots, not registration isolation.
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class StyledInputsPage(Component):
        citry = app

        class Kwargs:
            value: object

        template = """
          <main>{{ value }}</main>
        """

    component_factories = (
        (
            CAlert,
            "alert",
            lambda: CAlert(slots={"default": "Notice"}),
        ),
        (
            CButton,
            "button",
            lambda: CButton(slots={"default": "Action"}),
        ),
        (
            CCombobox,
            "root",
            lambda: CCombobox(name="destination"),
        ),
        (
            CDialog,
            "dialog",
            lambda: CDialog(slots={"title": "Details", "default": "Body"}),
        ),
        (
            CDrawer,
            "drawer",
            lambda: CDrawer(slots={"title": "Details", "default": "Body"}),
        ),
        (
            CToastRegion,
            "region",
            lambda: CToastRegion(items=(CToastMessage(id="ready", title="Ready"),)),
        ),
        (
            CField,
            "field",
            lambda: CField(slots={"label": "Name", "default": "Control"}),
        ),
        (
            CInput,
            "input",
            lambda: CInput(name="name"),
        ),
        (
            CTextarea,
            "textarea",
            lambda: CTextarea(name="notes"),
        ),
        (
            CNativeSelect,
            "native-select",
            lambda: CNativeSelect(options=[CNativeSelectOption("reef", "Coral reef")]),
        ),
        (
            CCheckbox,
            "checkbox",
            lambda: CCheckbox(slots={"default": "Choice"}),
        ),
        (
            CForm,
            "form",
            lambda: CForm(slots={"default": "Fields"}),
        ),
        (
            CIcon,
            "icon",
            lambda: CIcon(name="leaf"),
        ),
        (
            CCard,
            "card",
            lambda: CCard(slots={"default": "Details"}),
        ),
        (
            CTable,
            "root",
            lambda: CTable(
                columns=(CTableColumn("name", "Name"),),
                rows=(),
            ),
        ),
    )

    for definition, part, factory in component_factories:
        field_names = {field.name for field in fields(definition.Kwargs)}
        assert {"class_", "style"} <= field_names

        invocation = factory()
        invocation = definition(
            **dict(invocation.kwargs),
            class_=["consumer-root", {"consumer-active": True}],
            style={"--consumer-token": definition.__name__},
            slots=dict(invocation.slots),
        )
        html = str(StyledInputsPage(value=invocation))
        root = re.search(rf'<[^>]+data-citry-ui-part="{part}"[^>]*>', html)

        assert root is not None
        assert "consumer-root" in root.group(0)
        assert "consumer-active" in root.group(0)
        assert f"--consumer-token: {definition.__name__};" in root.group(0)


def test_button_renders_direct_native_anatomy_and_public_configuration():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    button = CButton(
        type="submit",
        variant="outline",
        intent="danger",
        size="lg",
        block=True,
        loading_pos="end",
        class_=["direct-action", {"is-dangerous": True}],
        style={"--consumer-button-radius": "1rem"},
        attrs={
            "id": "delete-account",
            "name": "action",
            "value": "delete",
            "class": "application-action",
            "data-application": "settings",
        },
        slots={
            "default": "Delete account",
            "start": "Start icon",
            "end": "End icon",
            "loading": "Pending icon",
        },
    )

    html = _page_html(app, button)

    assert '<button class="cui-button application-action direct-action is-dangerous" type="submit"' in html
    assert 'style="--consumer-button-radius: 1rem;"' in html
    assert 'id="delete-account"' in html
    assert 'name="action"' in html
    assert 'value="delete"' in html
    assert 'data-application="settings"' in html
    assert 'data-variant="outline"' in html
    assert 'data-intent="danger"' in html
    assert 'data-size="lg"' in html
    assert "data-block" in html
    assert 'data-loading-position="end"' in html
    assert "data-citry-button-has-start" in html
    assert "data-citry-button-has-end" in html
    assert all(
        f'data-citry-ui-part="{part}"' in html for part in ("button", "start", "content", "end", "loading-indicator")
    )
    assert all(value in html for value in ("Delete account", "Start icon", "End icon", "Pending icon"))


def test_button_loading_server_fallback_is_natively_inert_without_javascript():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    html = _page_html(app, CButton(type="submit", loading=True, slots={"default": "Save"}))
    button_tag = re.search(r"<button[^>]*>", html)

    assert button_tag is not None
    assert " disabled" in button_tag.group(0)
    assert 'aria-busy="true"' in button_tag.group(0)
    assert 'aria-disabled="true"' in button_tag.group(0)
    assert " data-loading" in button_tag.group(0)
    assert "data-disabled" not in button_tag.group(0)
    assert 'data-citry-ui-part="loading-indicator"' in html
    assert " hidden" not in re.search(
        r'<span class="cui-button__loading"[^>]*>',
        html,
    ).group(0)


def test_button_href_renders_a_native_link_with_link_attributes():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    html = _page_html(
        app,
        CButton(
            href="/field-guide",
            attrs={"target": "_blank", "rel": "noreferrer", "download": "guide.pdf"},
            slots={"default": "Open field guide"},
        ),
    )
    link_tag = re.search(r"<a[^>]*>", html)

    assert link_tag is not None
    assert 'href="/field-guide"' in link_tag.group(0)
    assert 'target="_blank"' in link_tag.group(0)
    assert 'rel="noreferrer"' in link_tag.group(0)
    assert 'download="guide.pdf"' in link_tag.group(0)
    assert " type=" not in link_tag.group(0)
    assert " disabled" not in link_tag.group(0)


@pytest.mark.parametrize(
    ("kwargs", "expected_tabindex"),
    [
        ({"disabled": True}, "-1"),
        ({"loading": True}, "0"),
        ({"loading": True, "attrs": {"tabindex": "2"}}, "2"),
        ({"loading": True, "attrs": {"tabindex": "1", "TABINDEX": "2"}}, "2"),
    ],
)
def test_button_unavailable_link_is_inert_without_javascript(kwargs, expected_tabindex):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    html = _page_html(app, CButton(href="/next", **kwargs, slots={"default": "Next"}))
    link_tag = re.search(r"<a[^>]*>", html)

    assert link_tag is not None
    assert " href=" not in link_tag.group(0)
    assert f'tabindex="{expected_tabindex}"' in link_tag.group(0)
    assert 'aria-disabled="true"' in link_tag.group(0)


@pytest.mark.parametrize(
    ("kwargs", "exception", "message"),
    [
        ({"type": "link"}, ValueError, "CButton type"),
        ({"variant": "raised"}, ValueError, "CButton variant"),
        ({"intent": "accent"}, ValueError, "CButton intent"),
        ({"size": "tiny"}, ValueError, "CButton size"),
        ({"loading_pos": "middle"}, ValueError, "CButton loading_pos"),
        ({"href": 42}, TypeError, "CButton href"),
        ({"href": "/next", "type": "submit"}, ValueError, "type applies only"),
        ({"href": "/next", "attrs": {"name": "action"}}, ValueError, "apply only to action buttons"),
        ({"disabled": 1}, TypeError, "CButton disabled"),
        ({"loading": 1}, TypeError, "CButton loading"),
        ({"block": 1}, TypeError, "CButton block"),
        ({"attrs": {"type": "reset"}}, ValueError, "owned attribute"),
        ({"attrs": {"href": "/next"}}, ValueError, "owned attribute"),
        ({"attrs": {"DATA-LOADING": "false"}}, ValueError, "owned attribute"),
        ({"attrs": {"data-citry-button-has-start": True}}, ValueError, "owned attribute"),
        ({"attrs": {1: "invalid"}}, TypeError, "string keys"),
    ],
)
def test_button_rejects_ambiguous_or_invalid_server_inputs(kwargs, exception, message):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    button = CButton(**kwargs, slots={"default": "Action"})

    with pytest.raises(exception, match=message):
        _page_html(app, button)


def test_dialog_renders_native_modal_anatomy_and_typed_slot_bindings():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    seen = {}

    def activator(ctx):
        seen["activator"] = ctx.data
        return CButton(attrs=ctx.data.activator_attrs, slots={"default": "Open dialog"})

    def actions(ctx):
        seen["actions"] = ctx.data
        return CButton(attrs=ctx.data.close_attrs, slots={"default": "Cancel"})

    dialog = CDialog(
        id="settings-dialog",
        open=True,
        initial_focus="title",
        size="lg",
        scroll="dialog",
        attrs={"data-workflow": "settings"},
        slots={
            "activator": activator,
            "title": "Edit settings",
            "description": "Update account behavior.",
            "default": "Dialog body",
            "actions": actions,
            "close": "Dismiss",
        },
    )

    html = _page_html(app, dialog)
    dialog_tag = re.search(r"<dialog[^>]*>", html)

    assert dialog_tag is not None
    assert 'id="settings-dialog"' in dialog_tag.group(0)
    assert " open" in dialog_tag.group(0)
    assert 'aria-modal="true"' in dialog_tag.group(0)
    assert 'aria-labelledby="settings-dialog-title"' in dialog_tag.group(0)
    assert 'aria-describedby="settings-dialog-description"' in dialog_tag.group(0)
    assert 'data-size="lg"' in dialog_tag.group(0)
    assert 'data-scroll="dialog"' in dialog_tag.group(0)
    assert 'data-workflow="settings"' in dialog_tag.group(0)
    assert 'tabindex="-1"' not in dialog_tag.group(0)
    assert 'id="settings-dialog-title" tabindex="-1"' in html
    assert 'aria-controls="settings-dialog"' in html
    assert 'aria-expanded="true"' in html
    assert "data-citry-dialog-trigger" in html
    assert "data-citry-dialog-close" in html
    assert "Dismiss" in html
    assert seen["activator"].activator_attrs["aria-haspopup"] == "dialog"
    assert seen["actions"].close_attrs == {"data-citry-dialog-close": ""}


@pytest.mark.parametrize(
    ("kwargs", "exception", "message"),
    [
        ({"open": 1}, TypeError, "CDialog open"),
        ({"dismissible": 1}, TypeError, "CDialog dismissible"),
        ({"close_on_escape": 1}, TypeError, "CDialog close_on_escape"),
        ({"close_on_outside": 1}, TypeError, "CDialog close_on_outside"),
        ({"size": "huge"}, ValueError, "CDialog size"),
        ({"scroll": "page"}, ValueError, "CDialog scroll"),
        ({"initial_focus": "#target"}, ValueError, "CDialog initial_focus"),
        ({"close_label": ""}, ValueError, "CDialog close_label"),
        ({"attrs": {"open": True}}, ValueError, "owned attribute"),
        ({"attrs": {"closedby": "any"}}, ValueError, "owned attribute"),
        ({"attrs": {"aria-label": "Override"}}, ValueError, "owned attribute"),
        ({"attrs": {"data-citry-dialog-close": ""}}, ValueError, "owned attribute"),
        ({"attrs": {"data-citry-dialog-trigger": ""}}, ValueError, "owned attribute"),
        ({"attrs": {"popover": "manual"}}, ValueError, "owned attribute"),
        ({"attrs": {"tabindex": -1}}, ValueError, "owned attribute"),
    ],
)
def test_dialog_rejects_ambiguous_or_invalid_server_inputs(kwargs, exception, message):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    dialog = CDialog(**kwargs, slots={"title": "Title", "default": "Body"})

    with pytest.raises(exception, match=message):
        _page_html(app, dialog)


def test_combobox_renders_native_field_relationships_and_canonical_form_value():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    combobox = CField(
        control_id="owner",
        required=True,
        slots={
            "label": "Owner",
            "description": "Choose one account owner.",
            "default": CCombobox(
                name="owner_id",
                value="ada",
                options=(
                    CComboboxOption("ada", "Ada Lovelace", "Mathematician and writer"),
                    CComboboxOption("grace", "Grace Hopper", disabled=True),
                ),
            ),
        },
    )

    html = _page_html(app, combobox)
    visible = re.search(r'<input class="cui-combobox__input"[^>]*>', html)
    hidden = re.search(r'<input name="owner_id" value="ada"[^>]*>', html)

    assert visible is not None
    assert hidden is not None
    assert 'id="owner"' in visible.group(0)
    assert 'role="combobox"' in visible.group(0)
    assert 'aria-autocomplete="list"' in visible.group(0)
    assert 'aria-expanded="false"' in visible.group(0)
    assert "required" in visible.group(0)
    assert "readonly" in visible.group(0)
    assert 'value="Ada Lovelace"' in visible.group(0)
    assert 'aria-describedby="owner-description"' in visible.group(0)
    assert 'data-value="grace"' in html
    assert 'aria-disabled="true"' in html
    assert "Mathematician and writer" in html
    assert 'data-citry-ui-part="option-description"' in html
    assert 'data-citry-ui-part="form-value"' not in html


def test_combobox_without_name_is_not_a_named_form_participant():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    html = _page_html(
        app,
        CCombobox(options=(CComboboxOption("mars", "Mars"),)),
    )

    hidden = re.search(r"<input[^>]*data-citry-combobox-form-value[^>]*>", html)
    assert hidden is not None
    assert "name=" not in hidden.group(0)


def test_combobox_server_output_filters_open_options_and_matches_unicode_thresholds():
    options = (CComboboxOption("mars", "Mars"),)

    def render(combobox: object) -> str:
        app = Citry(autodiscover=False)
        app.register_library(citry_ui)
        return _page_html(app, combobox)

    empty_html = render(CCombobox(options=options, input_value="zz", open=True))
    below_threshold_html = render(CCombobox(options=options, input_value="🚀", min_chars=2, open=True))
    loading_html = render(CCombobox(options=options, loading=True, open=True))

    assert "Mars" not in empty_html
    assert "data-empty" in empty_html
    assert 'aria-expanded="false"' in below_threshold_html
    listbox = re.search(r'<ul class="cui-combobox__listbox"[^>]*>', loading_html)
    assert listbox is not None
    assert "hidden" in listbox.group(0)


@pytest.mark.parametrize(
    ("kwargs", "exception", "message"),
    [
        ({"name": ""}, ValueError, "name"),
        ({"name": "owner", "min_chars": -1}, ValueError, "min_chars"),
        ({"name": "owner", "debounce_ms": True}, TypeError, "debounce_ms"),
        ({"name": "owner", "filter": "fuzzy"}, ValueError, "filter"),
        ({"name": "owner", "size": "medium"}, ValueError, "size"),
        ({"name": "owner", "placeholder": 123}, TypeError, "placeholder"),
        (
            {"options": (CComboboxOption("mars", "Mars", description=""),)},
            ValueError,
            "description",
        ),
        ({"name": "owner", "attrs": {"data-open": True}}, ValueError, "owned attribute"),
        ({"name": "owner", "input_attrs": {"form": "other-form"}}, ValueError, "owned attribute"),
        (
            {
                "name": "owner",
                "options": (
                    CComboboxOption("same", "One"),
                    CComboboxOption("same", "Two"),
                ),
            },
            ValueError,
            "must be unique",
        ),
    ],
)
def test_combobox_rejects_ambiguous_or_invalid_server_inputs(kwargs, exception, message):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    with pytest.raises(exception, match=message):
        _page_html(app, CCombobox(**kwargs))


def test_field_and_input_preserve_native_relationships_and_component_like_slot_values():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    field = CField(
        required=True,
        invalid=True,
        slots={
            "label": "Email",
            "default": CInput(name="email", type="email", value="person@example.com"),
            "description": "Work address",
            "error": "Enter a valid address",
        },
    )

    html = _page_html(app, field)
    control_id = re.search(r'<input[^>]+\sid="([^"]+)"', html)

    assert control_id is not None
    assert f'for="{control_id.group(1)}"' in html
    assert 'name="email"' in html
    assert 'type="email"' in html
    assert 'value="person@example.com"' in html
    assert "required" in html
    assert 'aria-invalid="true"' in html
    assert 'aria-describedby="' in html
    assert 'aria-errormessage="' in html
    assert 'aria-live="polite"' in html
    assert "Work address" in html
    assert "Enter a valid address" in html


def test_field_keeps_an_empty_live_region_mounted_without_a_dangling_reference():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    field = CField(
        slots={
            "label": "Name",
            "default": CInput(name="name"),
        }
    )

    html = _page_html(app, field)
    input_tag = re.search(r"<input[^>]*>", html)

    assert 'data-citry-ui-part="error"' in html
    assert 'aria-live="polite"' in html
    assert input_tag is not None
    assert "aria-describedby" not in input_tag.group(0)
    assert "aria-errormessage" not in input_tag.group(0)


def test_styled_field_exposes_complete_bindings_to_a_custom_control():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <c-CField required invalid>
            <c-fill name="label">
              Biography
            </c-fill>
            <c-fill name="default" data="data">
              <textarea c-bind="data.control_attrs" name="bio"></textarea>
            </c-fill>
            <c-fill name="description">
              Tell us about yourself
            </c-fill>
            <c-fill name="error">
              Biography is required
            </c-fill>
          </c-CField>
        """

    html = str(Page())
    control_id = re.search(r'<textarea[^>]*\sid="([^"]+)"', html)

    assert control_id is not None
    assert f'for="{control_id.group(1)}"' in html
    assert "required" in html
    assert 'aria-invalid="true"' in html
    assert 'aria-describedby="' in html
    assert 'aria-errormessage="' in html
    assert "data-citry-field-control" in html


def test_input_rejects_open_attributes_that_replace_typed_fields():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    input_value = CInput(
        name="canonical",
        type="email",
        id="typed-id",
        attrs={"id": "mapping-id", "name": "mapping-name", "type": "url", "data-extra": "kept"},
    )

    with pytest.raises(ValueError, match="owned attribute"):
        _page_html(app, input_value)


def test_input_rejects_an_id_that_would_break_its_field_label_relationship():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    field = CField(
        control_id="field-control",
        slots={
            "label": "Name",
            "default": CInput(name="name", id="different-control"),
        },
    )

    with pytest.raises(ValueError, match="conflicts with its CField control_id"):
        _page_html(app, field)


def test_input_merges_external_descriptions_without_dropping_field_relationships():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    field = CField(
        control_id="name-control",
        invalid=True,
        slots={
            "label": "Name",
            "default": CInput(
                name="name",
                attrs={
                    "ARIA-DESCRIBEDBY": "external-description name-control-description",
                    "ARIA-ERRORMESSAGE": "external-error",
                },
            ),
            "description": "Public name",
            "error": "Name is required",
        },
    )

    html = _page_html(app, field)

    assert 'aria-describedby="name-control-description name-control-error external-description"' in html
    assert 'aria-errormessage="name-control-error external-error"' in html


def test_input_rejects_case_insensitive_form_conflicts_and_dynamic_rebinding():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    with pytest.raises(ValueError, match="different native form owner"):
        _page_html(
            app,
            CForm(
                id="inside",
                slots={"default": CInput(attrs={"FORM": "outside"})},
            ),
        )

    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    with pytest.raises(ValueError, match="dynamically bind HTML attribute 'form'"):
        _page_html(app, CInput(attrs={"X-BIND:FORM": "owner"}))


@pytest.mark.parametrize("omitted_value", [None, False])
def test_input_omitted_case_insensitive_form_attr_keeps_enclosing_owner(omitted_value):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    html = _page_html(
        app,
        CForm(
            id="inside",
            slots={"default": CInput(attrs={"FORM": omitted_value})},
        ),
    )

    input_tag = re.search(r'<input[^>]*data-citry-ui-part="input"[^>]*>', html)
    assert input_tag is not None
    assert " form=" not in input_tag.group(0).lower()


def test_explicit_field_control_ids_always_generate_unique_relationship_ids():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    first = CField(
        control_id="foo",
        slots={"label": "First", "default": CInput(name="first")},
    )
    second = CField(
        control_id="foo-control",
        slots={"label": "Second", "default": CInput(name="second")},
    )

    class Page(Component):
        citry = app
        template = "{{ first }}{{ second }}"

        def template_data(self, kwargs, slots):
            return {"first": first, "second": second}

    html = str(Page())

    assert html.count('id="foo-label"') == 1
    assert html.count('id="foo-control-label"') == 1
    assert html.count('id="foo-error"') == 1
    assert html.count('id="foo-control-error"') == 1


@pytest.mark.parametrize("invalid", [False, True])
def test_input_cannot_override_field_owned_invalid_state(invalid):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    field = CField(
        invalid=True,
        slots={
            "label": "Name",
            "default": CInput(name="name", invalid=invalid),
            "error": "Name is required",
        },
    )

    with pytest.raises(ValueError, match="CInput inside CField cannot set Field-owned state: invalid"):
        _page_html(app, field)


@pytest.mark.parametrize("state", ["required", "disabled", "readonly", "invalid"])
def test_input_rejects_every_explicit_field_owned_state(state):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    field = CField(
        slots={
            "label": "Name",
            "default": CInput(name="name", **{state: False}),
        },
    )

    with pytest.raises(ValueError, match=rf"Field-owned state: {state}"):
        _page_html(app, field)


@pytest.mark.parametrize("state", ["required", "disabled", "readonly", "invalid"])
def test_combobox_rejects_every_explicit_field_owned_state(state):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    field = CField(
        slots={
            "label": "Owner",
            "default": CCombobox(name="owner", **{state: False}),
        },
    )

    with pytest.raises(ValueError, match=rf"Field-owned state: {state}"):
        _page_html(app, field)


def test_field_rejects_nested_fields_and_multiple_library_controls():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    nested = CField(
        slots={
            "label": "Outer",
            "default": CField(slots={"label": "Inner", "default": CInput()}),
        },
    )

    with pytest.raises(ValueError, match="CField cannot be nested"):
        _page_html(app, nested)

    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class TwoControls(Component):
        citry = app
        template = """
          <c-CInput name="first" />
          <c-CCombobox name="second" />
        """

    multiple = CField(slots={"label": "Two controls", "default": TwoControls()})
    with pytest.raises(ValueError, match="accepts exactly one library control"):
        _page_html(app, multiple)


def test_input_supports_unnamed_usage_concise_visual_size_and_native_character_width():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    input_value = CInput(
        size="sm",
        attrs={"aria-label": "Filter observations", "size": 24},
    )

    html = _page_html(app, input_value)
    input_tag = re.search(r"<input[^>]*>", html)

    assert input_tag is not None
    assert " name=" not in input_tag.group(0)
    assert 'aria-label="Filter observations"' in input_tag.group(0)
    assert 'size="24"' in input_tag.group(0)
    assert 'data-size="sm"' in input_tag.group(0)
    assert re.search(r'id="cui-input-[^"]+"', input_tag.group(0))


def test_disabled_form_wins_over_explicit_false_field_state():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    form = CForm(
        disabled=True,
        slots={
            "default": CField(
                disabled=False,
                slots={"label": "Site", "default": CInput(name="site")},
            )
        },
    )

    html = _page_html(app, form)
    field_tag = re.search(r"<div[^>]*data-citry-field-root[^>]*>", html)
    input_tag = re.search(r"<input[^>]*>", html)

    assert field_tag is not None
    assert input_tag is not None
    assert "data-disabled" in field_tag.group(0)
    assert "disabled" in input_tag.group(0)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"value": 1}, "value must be a string or None"),
        ({"autocomplete": 1}, "autocomplete must be a string or None"),
        ({"inputmode": 1}, "inputmode must be a string or None"),
        ({"placeholder": 1}, "placeholder must be a string or None"),
        ({"id": 1}, "id must be a string or None"),
    ],
)
def test_input_rejects_invalid_optional_string_inputs(kwargs, message):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    with pytest.raises(TypeError, match=message):
        _page_html(app, CInput(**kwargs))


def test_form_preserves_native_structure_and_inherited_field_configuration():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    form = CForm(
        id="profile-form",
        disabled=True,
        readonly=True,
        novalidate=True,
        method="post",
        action="/profiles",
        attrs={"data-workflow": "profile"},
        slots={
            "default": CField(
                required=True,
                slots={
                    "label": "Display name",
                    "default": CInput(name="profile.name"),
                },
            )
        },
    )

    html = _page_html(app, form)
    form_tag = re.search(r"<form[^>]*>", html)
    fieldset_tag = re.search(r"<fieldset[^>]*>", html)
    input_tag = re.search(r"<input[^>]*>", html)

    assert form_tag is not None
    assert fieldset_tag is not None
    assert input_tag is not None
    assert 'id="profile-form"' in form_tag.group(0)
    assert 'method="post"' in form_tag.group(0)
    assert 'action="/profiles"' in form_tag.group(0)
    assert 'data-workflow="profile"' in form_tag.group(0)
    assert "novalidate" in form_tag.group(0)
    assert "disabled" in fieldset_tag.group(0)
    assert "required" in input_tag.group(0)
    assert "disabled" in input_tag.group(0)
    assert "readonly" in input_tag.group(0)


def test_form_rejects_nesting_and_owned_native_attributes():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    nested = CForm(slots={"default": CForm(slots={"default": "Nested"})})

    with pytest.raises(ValueError, match="CForm cannot be nested"):
        _page_html(app, nested)

    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    ambiguous = CForm(attrs={"novalidate": True}, slots={"default": "Fields"})
    with pytest.raises(ValueError, match="owned attribute"):
        _page_html(app, ambiguous)


def test_semantic_table_renders_ordered_headers_row_headers_and_nested_components():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    table = CTable(
        columns=(
            CTableColumn("name", "Name", row_header=True),
            CTableColumn("action", "Action"),
        ),
        rows=(
            CTableRow(
                "alpha",
                {
                    "name": "Alpha",
                    "action": CButton(slots={"default": "Open"}),
                },
            ),
        ),
        slots={"caption": "Projects"},
    )

    html = _page_html(app, table)

    assert "<table" in html
    assert '<caption id="' in html
    assert 'data-citry-ui-part="caption"' in html
    assert "Projects" in html
    assert html.count('scope="col"') == 2
    assert '<th scope="row"' in html
    assert 'data-row-key="alpha"' in html
    assert '<button class="cui-button"' in html
    assert "Open" in html
    assert 'role="grid"' not in html
    assert "<script" in html


def test_table_renders_footer_and_merges_column_cell_defaults():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    table = CTable(
        columns=(
            CTableColumn(
                "moon",
                "Moon",
                row_header=True,
                cell_attrs={"class": "moon-cell", "style": {"white-space": "nowrap"}},
                footer="Known moons",
                footer_attrs={"class": "summary-label"},
            ),
            CTableColumn(
                "radius",
                "Radius",
                align="end",
                header_attrs={"abbr": "Mean radius"},
                cell_attrs={"class": "number-cell", "style": {"font-variant-numeric": "tabular-nums"}},
                footer=CButton(size="sm", slots={"default": "4 records"}),
                footer_attrs={"class": "summary-value"},
            ),
        ),
        rows=(
            CTableRow(
                "europa",
                {
                    "moon": "Europa",
                    "radius": CTableCell(
                        "1,560.8 km",
                        attrs={"class": "precise", "style": {"font-weight": "700"}},
                    ),
                },
            ),
        ),
    )

    html = _page_html(app, table)

    assert '<tfoot data-citry-ui-part="footer">' in html
    assert '<th scope="row" data-column-key="moon"' in html
    assert 'class="summary-label" data-citry-ui-part="footer-cell"' in html
    assert 'class="number-cell precise"' in html
    assert "font-variant-numeric: tabular-nums; font-weight: 700;" in html
    assert 'abbr="Mean radius"' in html
    assert "Known moons" in html
    assert "4 records" in html


def test_table_scroll_region_uses_caption_explicit_or_native_table_name():
    def render(table: CTable) -> str:
        app = Citry(autodiscover=False)
        app.register_library(citry_ui)
        return _page_html(app, table)

    captioned = render(
        CTable(
            id="moons",
            columns=(CTableColumn("moon", "Moon"),),
            rows=(),
            slots={"caption": "Visible moons"},
        ),
    )
    explicit = render(
        CTable(
            columns=(CTableColumn("moon", "Moon"),),
            rows=(),
            scroll_label="Scrollable moon table",
        ),
    )
    native_named = render(
        CTable(
            columns=(CTableColumn("moon", "Moon"),),
            rows=(),
            table_attrs={"aria-label": "Moon catalog"},
        ),
    )

    assert 'id="moons" role="region" aria-labelledby="moons-caption" tabindex="0"' in captioned
    assert 'id="moons-caption" data-citry-ui-part="caption"' in captioned
    assert 'role="region" aria-label="Scrollable moon table" tabindex="0"' in explicit
    assert 'role="region" aria-label="Moon catalog" tabindex="0"' in native_named


def test_table_snapshots_record_attrs_before_binding_them():
    class ChangingAttrs(Mapping[str, object]):
        def __init__(self) -> None:
            self.iterations = 0

        def __iter__(self) -> Iterator[str]:
            self.iterations += 1
            return iter(("class",) if self.iterations == 1 else ("scope",))

        def __len__(self) -> int:
            return 1

        def __getitem__(self, key: str) -> object:
            return "validated" if key == "class" else "row"

    attrs = ChangingAttrs()
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    html = _page_html(
        app,
        CTable(
            columns=(CTableColumn("moon", "Moon", cell_attrs=attrs),),
            rows=(CTableRow("europa", {"moon": "Europa"}),),
        ),
    )

    assert 'class="validated"' in html
    assert 'scope="row"' not in html
    assert attrs.iterations == 1


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ((CTableRow("same", {"name": "A"}), CTableRow("same", {"name": "B"})), "row keys"),
        ((CTableRow("one", {}),), "cells do not match columns"),
        ((CTableRow("one", {"name": "A", "extra": "B"}),), "cells do not match columns"),
    ],
)
def test_table_rejects_ambiguous_row_identity_and_shape(rows, message):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    table = CTable(columns=(CTableColumn("name", "Name"),), rows=rows)

    with pytest.raises(ValueError, match=message):
        _page_html(app, table)


def test_table_rejects_more_than_one_row_header_column():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    table = CTable(
        columns=(
            CTableColumn("group", "Group", row_header=True),
            CTableColumn("moon", "Moon", row_header=True),
        ),
        rows=(),
    )

    with pytest.raises(ValueError, match="at most one row_header"):
        _page_html(app, table)


def test_table_rejects_spans_until_it_can_validate_the_logical_grid():
    with pytest.raises(TypeError, match="unexpected keyword argument 'colspan'"):
        CTableCell("A", colspan=2)  # type: ignore[call-arg]


@pytest.mark.parametrize(
    "table",
    [
        CTable(
            columns=(CTableColumn("a", "A"), CTableColumn("b", "B")),
            rows=(
                CTableRow(
                    "one",
                    {
                        "a": CTableCell("A", attrs={"colspan": 2}),
                        "b": "B",
                    },
                ),
            ),
        ),
        CTable(
            columns=(CTableColumn("name", "Name", header_attrs={"scope": "row"}),),
            rows=(CTableRow("one", {"name": "A"}),),
        ),
    ],
    ids=["cell-span-attr", "column-scope-attr"],
)
def test_table_open_attrs_cannot_override_semantic_structure(table):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    with pytest.raises(ValueError, match="cannot override owned attribute"):
        _page_html(app, table)


@pytest.mark.parametrize(
    ("state", "text", "busy"),
    [
        ("ready", "No records", False),
        ("loading", "Fetching", True),
        ("error", "Try again", False),
    ],
)
def test_table_state_slots_span_columns_and_only_loading_is_busy(state, text, busy):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    slot_name = {"ready": "empty", "loading": "loading", "error": "error"}[state]
    table = CTable(
        columns=(CTableColumn("a", "A"), CTableColumn("b", "B")),
        rows=(),
        state=state,
        slots={slot_name: text},
    )

    html = _page_html(app, table)

    assert text in html
    assert 'colspan="2"' in html
    assert ('aria-busy="true"' in html) is busy
    assert '<td colspan="2" data-citry-ui-part="state-cell">' in html
    assert '<td colspan="2" role="status"' not in html
    assert '<span class="cui-table-announcer" role="status" aria-live="polite" aria-atomic="true">' in html


def _tabs_content(
    app: Citry,
    *,
    duplicate: bool = False,
    customized: bool = False,
) -> type[Component]:
    second_value = "account" if duplicate else "security"
    tab_customization = ' class_="consumer-tab" style="--consumer-order: tab"' if customized else ""
    panel_customization = ' class_="consumer-panel" style="--consumer-order: panel"' if customized else ""

    class TabsContent(Component):
        citry = app
        transparent = True
        template = f"""
          <c-CTab value="account"{tab_customization}>Account</c-CTab>
          <c-CTab value="{second_value}">Security</c-CTab>
          <c-CTabPanel value="account"{panel_customization}>Account panel</c-CTabPanel>
          <c-CTabPanel value="security">Security panel</c-CTabPanel>
        """

    return TabsContent


def test_server_rendered_tabs_pair_aria_ids_and_initial_selection():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)
    TabsContent = _tabs_content(app)
    tabs = CTabs(
        default_value="account",
        aria_label="Account settings",
        slots={"default": TabsContent()},
    )

    html = _page_html(app, tabs)
    selected_tab = re.search(r'<button[^>]+aria-selected="true"[^>]+>', html)
    root_tag = re.search(r'<div[^>]+data-citry-ui-part="tabs"[^>]*>', html)

    assert selected_tab is not None
    assert root_tag is not None
    controls = re.search(r'aria-controls="([^"]+)"', selected_tab.group(0))
    tab_id = re.search(r'id="([^"]+)"', selected_tab.group(0))
    assert controls is not None
    assert tab_id is not None
    assert f'id="{controls.group(1)}"' in html
    assert f'aria-labelledby="{tab_id.group(1)}"' in html
    assert 'aria-orientation="horizontal"' in html
    assert 'aria-label="Account settings"' in html
    assert "data-loop" in root_tag.group(0)
    assert 'tabindex="-1"' in html
    assert len(re.findall(r'<div[^>]+role="tabpanel"[^>]+hidden[^>]*>', html)) == 1
    assert "onValueChange?.(value, detail)" in installed[CTabs].get_js()
    assert "citry-ui:tabs-change" not in installed[CTabs].get_js()


def test_styled_tabs_expose_production_configuration_parts_and_tokens():
    for definition in (CTabs, CTab, CTabPanel):
        assert {"class_", "style"} <= {field.name for field in fields(definition.Kwargs)}

    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    TabsContent = _tabs_content(app, customized=True)
    tabs = CTabs(
        default_value="account",
        activation="manual",
        orientation="vertical",
        direction="rtl",
        loop=False,
        disabled=True,
        variant="pill",
        density="compact",
        align="end",
        grow=True,
        aria_label="Account settings",
        class_=["consumer-tabs", {"consumer-active": True}],
        style={"--consumer-order": "tabs"},
        attrs={"data-consumer": "kept"},
        tab_list_attrs={"data-consumer-list": "kept"},
        slots={"default": TabsContent()},
    )

    html = _page_html(app, tabs, include_css=True)
    root_tag = re.search(r'<div[^>]+data-citry-ui-part="tabs"[^>]*>', html)

    assert root_tag is not None
    assert 'data-activation="manual"' in html
    assert 'data-orientation="vertical"' in html
    assert 'data-direction="rtl"' in html
    assert 'data-variant="pill"' in html
    assert 'data-density="compact"' in html
    assert 'data-align="end"' in html
    assert "data-grow" in html
    assert "data-loop" not in root_tag.group(0)
    assert "data-disabled" in html
    assert 'aria-disabled="true"' in html
    assert 'data-consumer="kept"' in html
    assert 'data-consumer-list="kept"' in html
    assert "consumer-tabs" in root_tag.group(0)
    assert "consumer-active" in root_tag.group(0)
    assert "--consumer-order: tabs;" in root_tag.group(0)
    tab_tag = re.search(r'<button[^>]+data-citry-ui-part="tab"[^>]*>', html)
    panel_tag = re.search(r'<div[^>]+data-citry-ui-part="tab-panel"[^>]*>', html)
    assert tab_tag is not None
    assert panel_tag is not None
    assert "consumer-tab" in tab_tag.group(0)
    assert "--consumer-order: tab;" in tab_tag.group(0)
    assert "consumer-panel" in panel_tag.group(0)
    assert "--consumer-order: panel;" in panel_tag.group(0)
    assert html.count('data-citry-ui-part="tabs"') == 1
    assert html.count('data-citry-ui-part="tab-list"') == 1
    assert html.count('data-citry-ui-part="tab"') == 2
    assert html.count('data-citry-ui-part="tab-panel"') == 2
    assert "--_cui-tabs-accent: var(--cui-tabs-accent, LinkText);" in html
    assert "background: var(--_cui-tabs-active-background);" in html
    assert "@media (forced-colors: active)" in html


@pytest.mark.parametrize(
    ("component", "message"),
    [
        (
            CTabs(
                default_value="account",
                aria_label="Settings",
                attrs={"dir": "rtl"},
                slots={"default": ""},
            ),
            "CTabs attrs",
        ),
        (
            CTabs(
                default_value="account",
                aria_label="Settings",
                tab_list_attrs={"role": "list"},
                slots={"default": ""},
            ),
            "CTabs tab_list_attrs",
        ),
        (CTab(value="account", attrs={"ARIA-SELECTED": "false"}, slots={"default": ""}), "CTab attrs"),
        (CTabPanel(value="account", attrs={"hidden": True}, slots={"default": ""}), "CTabPanel attrs"),
    ],
)
def test_styled_tabs_reject_open_attrs_that_replace_owned_contracts(component, message):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    with pytest.raises(ValueError, match=message):
        _page_html(app, component)


def test_tabs_reject_duplicate_tabs_and_mismatched_panels_after_descendants_render():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    TabsContent = _tabs_content(app, duplicate=True)
    tabs = CTabs(
        default_value="account",
        aria_label="Settings",
        slots={"default": TabsContent()},
    )

    with pytest.raises(ValueError, match="every Tab value to be unique"):
        _page_html(app, tabs)


@pytest.mark.parametrize(
    ("content_template", "default_value", "message"),
    [
        (
            '<c-CTabPanel value="account">Panel</c-CTabPanel>',
            "account",
            "matching Tab and TabPanel",
        ),
        (
            """
              <c-CTab value="account">Account</c-CTab>
              <c-CTab value="security">Security</c-CTab>
              <c-CTabPanel value="account">Account panel</c-CTabPanel>
              <c-CTabPanel value="security">Security panel</c-CTabPanel>
              <c-CTabPanel value="security">Duplicate panel</c-CTabPanel>
            """,
            "account",
            "TabPanel value to be unique",
        ),
        (
            """
              <c-CTab value="account">Account</c-CTab>
              <c-CTab value="security">Security</c-CTab>
              <c-CTabPanel value="account">Account panel</c-CTabPanel>
              <c-CTabPanel value="profile">Profile panel</c-CTabPanel>
            """,
            "account",
            "matching Tab and TabPanel",
        ),
        (
            """
              <c-CTab value="account">Account</c-CTab>
              <c-CTabPanel value="account">Account panel</c-CTabPanel>
            """,
            "missing",
            "does not identify a Tab",
        ),
        (
            """
              <c-CTab value="account" disabled>Account</c-CTab>
              <c-CTabPanel value="account">Account panel</c-CTabPanel>
            """,
            "account",
            "identifies a disabled Tab",
        ),
    ],
)
def test_tabs_reject_invalid_compound_registry_states(content_template, default_value, message):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class InvalidTabsContent(Component):
        citry = app
        template = content_template

    tabs = CTabs(
        default_value=default_value,
        aria_label="Settings",
        slots={"default": InvalidTabsContent()},
    )
    with pytest.raises(ValueError, match=message):
        _page_html(app, tabs)


@pytest.mark.parametrize(
    ("component", "message"),
    [
        (CTab(value="", slots={"default": "Empty"}), "Tab value must be non-empty"),
        (CTabPanel(value="", slots={"default": "Empty"}), "TabPanel value must be non-empty"),
    ],
)
def test_tab_and_panel_reject_empty_values_before_resolving_compound_context(component, message):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    with pytest.raises(ValueError, match=message):
        _page_html(app, component)


@pytest.mark.parametrize(
    "component",
    [
        CTab(value="account", slots={"default": "Account"}),
        CTabPanel(value="account", slots={"default": "Panel"}),
    ],
)
def test_tab_and_panel_are_declarations_that_require_tabs(component):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    with pytest.raises(ValueError, match=r"declaration component.*inside CTabs"):
        _page_html(app, component)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"activation": "eager"}, "activation"),
        ({"orientation": "diagonal"}, "orientation"),
        ({"direction": "sideways"}, "direction"),
        ({"variant": "ghost"}, "variant"),
        ({"density": "tiny"}, "density"),
        ({"align": "around"}, "align"),
    ],
)
def test_tabs_reject_unknown_configuration_values(overrides, message):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    tabs = CTabs(
        default_value="account",
        aria_label="Settings",
        slots={"default": ""},
        **overrides,
    )

    with pytest.raises(ValueError, match=message):
        _page_html(app, tabs)


@pytest.mark.parametrize("name", ["loop", "disabled", "grow"])
@pytest.mark.parametrize("value", [1, 0, "yes", None])
def test_tabs_reject_non_boolean_root_configuration(name, value):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    tabs = CTabs(
        default_value="account",
        aria_label="Settings",
        slots={"default": ""},
        **{name: value},
    )

    with pytest.raises(TypeError, match=rf"Tabs {name} must be a bool"):
        _page_html(app, tabs)


@pytest.mark.parametrize("value", [1, 0, "yes", None])
def test_tab_rejects_non_boolean_disabled(value):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    tab = CTab(value="account", disabled=value, slots={"default": "Account"})

    with pytest.raises(TypeError, match="Tab disabled must be a bool"):
        _page_html(app, tab)


def test_tabs_reject_an_empty_initial_value_before_rendering_children():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    tabs = CTabs(default_value="", aria_label="Settings", slots={"default": ""})

    with pytest.raises(ValueError, match="non-empty value"):
        _page_html(app, tabs)


@pytest.mark.parametrize("tabs_id", ["", "bad id", "bad\tid"])
def test_tabs_reject_explicit_ids_that_cannot_form_html_relationships(tabs_id):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    TabsContent = _tabs_content(app)
    tabs = CTabs(
        default_value="account",
        aria_label="Settings",
        id=tabs_id,
        slots={"default": TabsContent()},
    )

    with pytest.raises(ValueError, match="Tabs id"):
        _page_html(app, tabs)


def test_imported_compound_tabs_can_be_nested_as_component_like_slot_values():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    tab = CTab(value="account", slots={"default": "Account"})
    panel = CTabPanel(value="account", slots={"default": "Panel"})

    class TabsContent(Component):
        citry = app
        template = """
          {{ tab }}
          {{ panel }}
        """

        def template_data(self, kwargs, slots):
            return {
                "tab": tab,
                "panel": panel,
            }

    tabs = CTabs(
        default_value="account",
        aria_label="Account settings",
        slots={"default": TabsContent()},
    )
    html = _page_html(app, tabs)

    assert "Account" in html
    assert "Panel" in html
    assert 'role="tab"' in html
    assert 'role="tabpanel"' in html


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"aria_label": "   "},
        {"aria_labelledby": "   "},
    ],
)
def test_tabs_require_an_accessible_name_for_the_generated_tab_list(kwargs):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    tabs = CTabs(default_value="account", slots={"default": ""}, **kwargs)

    with pytest.raises(ValueError, match="accessible tab-list name"):
        _page_html(app, tabs)


def test_tabs_reject_non_declaration_output_in_the_default_slot():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class InvalidContent(Component):
        citry = app
        template = """
          This is rendered output, not a declaration.
          <c-CTab value="account">Account</c-CTab>
          <c-CTabPanel value="account">Panel</c-CTabPanel>
        """

    tabs = CTabs(
        default_value="account",
        aria_label="Account settings",
        slots={"default": InvalidContent()},
    )

    with pytest.raises(ValueError, match="only CTab and CTabPanel declarations"):
        _page_html(app, tabs)


@pytest.mark.parametrize("boundary", ["tab", "panel"])
def test_tab_and_panel_boundaries_require_nested_tabs_to_establish_a_fresh_context(boundary):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    if boundary == "tab":
        content_template = """
          <c-CTab value="outer">
            <c-CTab value="inner">
              Inner
            </c-CTab>
          </c-CTab>
          <c-CTabPanel value="outer">
            Outer panel
          </c-CTabPanel>
        """
    else:
        content_template = """
          <c-CTab value="outer">
            Outer
          </c-CTab>
          <c-CTabPanel value="outer">
            <c-CTab value="inner">
              Inner
            </c-CTab>
          </c-CTabPanel>
        """

    class NestedContent(Component):
        citry = app
        template = content_template

    tabs = CTabs(
        default_value="outer",
        aria_label="Outer tabs",
        slots={"default": NestedContent()},
    )

    with pytest.raises(ValueError, match=r"declaration component.*inside CTabs"):
        _page_html(app, tabs)


def test_nested_tabs_are_valid_below_a_tab_panel_boundary():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class NestedContent(Component):
        citry = app
        transparent = True
        template = """
          <c-CTab value="outer">
            Outer
          </c-CTab>
          <c-CTabPanel value="outer">
            <c-CTabs
              default_value="inner"
              aria_label="Inner tabs"
            >
              <c-CTab value="inner">
                Inner
              </c-CTab>
              <c-CTabPanel value="inner">
                Nested panel
              </c-CTabPanel>
            </c-CTabs>
          </c-CTabPanel>
        """

    tabs = CTabs(
        default_value="outer",
        aria_label="Outer tabs",
        slots={"default": NestedContent()},
    )
    html = _page_html(app, tabs)

    assert html.count('role="tablist"') == 2
    assert html.count('role="tab"') == 2
    assert html.count('role="tabpanel"') == 2
    assert "Nested panel" in html


def test_styled_tabs_cannot_nest_inside_a_styled_tab_button():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class NestedContent(Component):
        citry = app
        template = """
          <c-CTab value="outer">
            <c-CTabs
              default_value="inner"
              aria_label="Inner tabs"
            >
              <c-CTab value="inner">
                Inner
              </c-CTab>
                <c-CTabPanel value="inner">
                  Nested panel
                </c-CTabPanel>
            </c-CTabs>
          </c-CTab>
          <c-CTabPanel value="outer">
            Outer panel
          </c-CTabPanel>
        """

    tabs = CTabs(
        default_value="outer",
        aria_label="Outer tabs",
        slots={"default": NestedContent()},
    )

    with pytest.raises(ValueError, match="inside a native button"):
        _page_html(app, tabs)


def test_tabs_cannot_nest_directly_under_an_existing_tabs_root():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class NestedContent(Component):
        citry = app
        template = """
          <c-CTabs
            default_value="inner"
            aria_label="Inner tabs"
          >
            Inner tabs
          </c-CTabs>
        """

    tabs = CTabs(
        default_value="outer",
        aria_label="Outer tabs",
        slots={"default": NestedContent()},
    )

    with pytest.raises(ValueError, match="inside a Tab or TabPanel"):
        _page_html(app, tabs)
