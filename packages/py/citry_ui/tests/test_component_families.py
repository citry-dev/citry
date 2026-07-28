"""Pressure tests for Field/Input, semantic Table, and server-rendered Tabs."""

from __future__ import annotations

import re

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import (
    CButton,
    CField,
    CFieldHeadless,
    CInput,
    CTab,
    CTable,
    CTableCell,
    CTableColumn,
    CTableHeadless,
    CTableRow,
    CTabList,
    CTabPanel,
    CTabs,
    CTabsHeadless,
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

    assert 'data-citry-ui-part="error"' in html
    assert 'aria-live="polite"' in html
    assert "aria-describedby" not in html
    assert "aria-errormessage" not in html


def test_headless_field_owns_no_markup_and_context_reaches_a_component_like_callback_result():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    seen = []

    def control(ctx):
        seen.append(ctx.data)
        return CInput(name="query", attrs={"data-probe": "field-context"})

    field = CFieldHeadless(
        control_id="search-control",
        required=True,
        slots={"default": control},
    )
    html = _page_html(app, field)

    assert '<input class="cui-input"' in html
    assert 'id="search-control"' in html
    assert 'name="query"' in html
    assert 'data-probe="field-context"' in html
    assert "required" in html
    assert "cui-field" not in html
    assert seen[0].control_id == "search-control"
    assert seen[0].is_required is True


def test_styled_field_exposes_complete_bindings_to_a_custom_control():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <c-CField required invalid>
            <c-fill name="label">Biography</c-fill>
            <c-fill name="default" data="data">
              <textarea c-bind="data.control_attrs" name="bio"></textarea>
            </c-fill>
            <c-fill name="description">Tell us about yourself</c-fill>
            <c-fill name="error">Biography is required</c-fill>
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


def test_input_typed_fields_win_over_the_open_attribute_mapping():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    input_value = CInput(
        name="canonical",
        type="email",
        id="typed-id",
        attrs={"id": "mapping-id", "name": "mapping-name", "type": "url", "data-extra": "kept"},
    )

    html = _page_html(app, input_value)

    assert 'id="typed-id"' in html
    assert 'name="canonical"' in html
    assert 'type="email"' in html
    assert 'data-extra="kept"' in html
    assert "mapping-id" not in html
    assert "mapping-name" not in html


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

    with pytest.raises(ValueError, match="conflicts with its Field control_id"):
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
                    "aria-describedby": "external-description name-control-description",
                    "aria-errormessage": "external-error",
                },
            ),
            "description": "Public name",
            "error": "Name is required",
        },
    )

    html = _page_html(app, field)

    assert 'aria-describedby="name-control-description name-control-error external-description"' in html
    assert 'aria-errormessage="name-control-error external-error"' in html


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


def test_input_explicit_false_invalid_state_clears_inherited_error_relationships():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    field = CField(
        invalid=True,
        slots={
            "label": "Name",
            "default": CInput(name="name", invalid=False),
            "error": "Name is required",
        },
    )

    html = _page_html(app, field)
    input_tag = re.search(r"<input[^>]*>", html)

    assert input_tag is not None
    assert "aria-invalid" not in input_tag.group(0)
    assert "aria-errormessage" not in input_tag.group(0)
    assert "aria-describedby" not in input_tag.group(0)


def test_input_explicit_true_invalid_state_adds_field_error_relationships():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    field = CField(
        control_id="name-control",
        invalid=False,
        slots={
            "label": "Name",
            "default": CInput(name="name", invalid=True),
            "error": "Name is required",
        },
    )

    html = _page_html(app, field)
    input_tag = re.search(r"<input[^>]*>", html)

    assert input_tag is not None
    assert 'aria-invalid="true"' in input_tag.group(0)
    assert 'aria-describedby="name-control-error"' in input_tag.group(0)
    assert 'aria-errormessage="name-control-error"' in input_tag.group(0)


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
    assert re.search(r"<caption>\s*Projects\s*</caption>", html)
    assert html.count('scope="col"') == 2
    assert '<th scope="row"' in html
    assert 'data-row-key="alpha"' in html
    assert '<button class="cui-button"' in html
    assert "Open" in html
    assert 'role="grid"' not in html
    assert "<script" not in html


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


def test_table_rejects_spans_until_it_can_validate_the_logical_grid():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    table = CTable(
        columns=(CTableColumn("name", "Name"),),
        rows=(CTableRow("one", {"name": CTableCell("A", colspan=2)}),),
    )

    with pytest.raises(ValueError, match="does not support spans yet"):
        _page_html(app, table)


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
            columns=(CTableColumn("name", "Name", attrs={"scope": "row"}),),
            rows=(CTableRow("one", {"name": "A"}),),
        ),
    ],
    ids=["cell-span-attr", "column-scope-attr"],
)
def test_table_open_attrs_cannot_override_semantic_structure(table):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    with pytest.raises(ValueError, match="cannot override semantic attribute"):
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


def test_headless_table_exposes_normalized_data_without_owning_html_or_javascript():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)
    seen = []
    table = CTableHeadless(
        columns=(CTableColumn("name", "Name"),),
        rows=(CTableRow("one", {"name": "A"}),),
        slots={"default": lambda ctx: seen.append(ctx.data) or "headless table"},
    )

    html = _page_html(app, table)

    assert "headless table" in html
    assert "<table" not in html
    assert seen[0]["column_count"] == 1
    assert seen[0]["rows"][0].row.key == "one"
    assert installed[CTableHeadless].get_js() is None


def _tabs_content(app: Citry, *, duplicate: bool = False) -> type[Component]:
    second_value = "account" if duplicate else "security"

    class TabsContent(Component):
        citry = app
        template = f"""
          <c-CTabList aria_label="Account settings">
            <c-CTab value="account">Account</c-CTab>
            <c-CTab value="{second_value}">Security</c-CTab>
          </c-CTabList>
          <c-CTabPanel value="account">Account panel</c-CTabPanel>
          <c-CTabPanel value="security">Security panel</c-CTabPanel>
        """

    return TabsContent


def test_server_rendered_tabs_pair_aria_ids_and_initial_selection():
    app = Citry(autodiscover=False)
    installed = app.register_library(citry_ui)
    TabsContent = _tabs_content(app)
    tabs = CTabs(default_value="account", slots={"default": TabsContent()})

    html = _page_html(app, tabs)
    selected_tab = re.search(r'<button[^>]+aria-selected="true"[^>]+>', html)

    assert selected_tab is not None
    controls = re.search(r'aria-controls="([^"]+)"', selected_tab.group(0))
    tab_id = re.search(r'id="([^"]+)"', selected_tab.group(0))
    assert controls is not None
    assert tab_id is not None
    assert f'id="{controls.group(1)}"' in html
    assert f'aria-labelledby="{tab_id.group(1)}"' in html
    assert 'aria-orientation="horizontal"' in html
    assert 'aria-label="Account settings"' in html
    assert 'tabindex="-1"' in html
    assert html.count(" hidden") == 1
    assert installed[CTabs].get_js() is None
    assert installed[CTabsHeadless].get_js() is None


def test_tabs_reject_duplicate_tabs_and_mismatched_panels_after_descendants_render():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    TabsContent = _tabs_content(app, duplicate=True)
    tabs = CTabs(default_value="account", slots={"default": TabsContent()})

    with pytest.raises(ValueError, match="Tab value to be unique"):
        _page_html(app, tabs)


def test_imported_compound_tabs_can_be_nested_as_component_like_slot_values():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    tab_list = CTabList(
        aria_label="Account settings",
        slots={
            "default": CTab(value="account", slots={"default": "Account"}),
        },
    )

    class TabsContent(Component):
        citry = app
        template = """
          {{ tab_list }}
          {{ panel }}
        """

        def template_data(self, kwargs, slots):
            return {
                "tab_list": tab_list,
                "panel": CTabPanel(value="account", slots={"default": "Panel"}),
            }

    tabs = CTabs(default_value="account", slots={"default": TabsContent()})
    html = _page_html(app, tabs)

    assert "Account" in html
    assert "Panel" in html
    assert 'role="tab"' in html
    assert 'role="tabpanel"' in html


def test_tabs_require_tabs_to_be_owned_by_one_accessibly_named_tab_list():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class DirectTabContent(Component):
        citry = app
        template = """
          <c-CTab value="account">Account</c-CTab>
          <c-CTabPanel value="account">Panel</c-CTabPanel>
        """

    direct_tab = CTabs(default_value="account", slots={"default": DirectTabContent()})
    with pytest.raises(ValueError, match="inside a TabList"):
        _page_html(app, direct_tab)

    unnamed_app = Citry(autodiscover=False)
    unnamed_app.register_library(citry_ui)

    class UnnamedListContent(Component):
        citry = unnamed_app
        template = """
          <c-CTabList>
            <c-CTab value="account">Account</c-CTab>
          </c-CTabList>
          <c-CTabPanel value="account">Panel</c-CTabPanel>
        """

    unnamed_list = CTabs(default_value="account", slots={"default": UnnamedListContent()})
    with pytest.raises(ValueError, match="accessible name"):
        _page_html(unnamed_app, unnamed_list)


def test_tabs_reject_a_panel_nested_inside_the_tab_list():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class NestedPanelContent(Component):
        citry = app
        template = """
          <c-CTabList aria_label="Account settings">
            <c-CTab value="account">Account</c-CTab>
            <c-CTabPanel value="account">Panel</c-CTabPanel>
          </c-CTabList>
        """

    tabs = CTabs(default_value="account", slots={"default": NestedPanelContent()})

    with pytest.raises(ValueError, match="outside TabList"):
        _page_html(app, tabs)


@pytest.mark.parametrize("boundary", ["tab", "panel"])
def test_tab_and_panel_boundaries_require_nested_tabs_to_establish_a_fresh_context(boundary):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    if boundary == "tab":
        content_template = """
          <c-CTabList aria_label="Outer tabs">
            <c-CTab value="outer">
              <c-CTab value="inner">
                Inner
              </c-CTab>
            </c-CTab>
          </c-CTabList>
          <c-CTabPanel value="outer">
            Outer panel
          </c-CTabPanel>
        """
    else:
        content_template = """
          <c-CTabList aria_label="Outer tabs">
            <c-CTab value="outer">
              Outer
            </c-CTab>
          </c-CTabList>
          <c-CTabPanel value="outer">
            <c-CTab value="inner">
              Inner
            </c-CTab>
          </c-CTabPanel>
        """

    class NestedContent(Component):
        citry = app
        template = content_template

    tabs = CTabs(default_value="outer", slots={"default": NestedContent()})

    with pytest.raises(ValueError, match="inside a Tabs root"):
        _page_html(app, tabs)


def test_nested_tabs_are_valid_below_a_tab_panel_boundary():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class NestedContent(Component):
        citry = app
        template = """
          <c-CTabList aria_label="Outer tabs">
            <c-CTab value="outer">
              Outer
            </c-CTab>
          </c-CTabList>
          <c-CTabPanel value="outer">
            <c-CTabs default_value="inner">
              <c-CTabList aria_label="Inner tabs">
                <c-CTab value="inner">
                  Inner
                </c-CTab>
              </c-CTabList>
              <c-CTabPanel value="inner">
                Nested panel
              </c-CTabPanel>
            </c-CTabs>
          </c-CTabPanel>
        """

    tabs = CTabs(default_value="outer", slots={"default": NestedContent()})
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
          <c-CTabList aria_label="Outer tabs">
            <c-CTab value="outer">
              <c-CTabs default_value="inner">
                <c-CTabList aria_label="Inner tabs">
                  <c-CTab value="inner">
                    Inner
                  </c-CTab>
                </c-CTabList>
                <c-CTabPanel value="inner">
                  Nested panel
                </c-CTabPanel>
              </c-CTabs>
            </c-CTab>
          </c-CTabList>
          <c-CTabPanel value="outer">
            Outer panel
          </c-CTabPanel>
        """

    tabs = CTabs(default_value="outer", slots={"default": NestedContent()})

    with pytest.raises(ValueError, match="inside a native button"):
        _page_html(app, tabs)


def test_tabs_cannot_nest_directly_under_an_existing_tabs_root():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class NestedContent(Component):
        citry = app
        template = """
          <c-CTabs default_value="inner">
            Inner tabs
          </c-CTabs>
        """

    tabs = CTabs(default_value="outer", slots={"default": NestedContent()})

    with pytest.raises(ValueError, match="inside a Tab or TabPanel"):
        _page_html(app, tabs)
