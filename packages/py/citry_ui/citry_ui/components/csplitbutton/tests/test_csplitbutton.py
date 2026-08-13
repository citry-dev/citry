"""Server contract tests for the Split Button component family."""

from __future__ import annotations

import re
from dataclasses import fields

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cbutton import CButton
from citry_ui.components.cbutton.cbutton import _CBUTTON_SHARED_ASSETS
from citry_ui.components.cmenu import CMenu, CMenuItem
from citry_ui.components.cmenu.cmenu import (
    _CMENU_SHARED_ASSETS,
    CInternalMenuCollection,
    CInternalMenuContent,
    CInternalMenuSurface,
)
from citry_ui.components.csplitbutton import (
    CSplitButton,
    CSplitButtonDefaultSlotData,
    CSplitButtonEndSlotData,
    CSplitButtonLoadingSlotData,
    CSplitButtonMenuSlotData,
    CSplitButtonStartSlotData,
)

_COMPONENTS = (
    CSplitButton,
    CButton,
    CMenu,
    CMenuItem,
    CInternalMenuCollection,
    CInternalMenuContent,
    CInternalMenuSurface,
)


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-split-button-tests", _COMPONENTS))
    return app


def _render(template: str, data: dict[str, object] | None = None, *, deps: str = "ignore") -> str:
    app = _app()

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return data or {}

    Page.template = template
    return Page().render().serialize(deps_strategy=deps)


def _split(inputs: str = "", menu: str = '<c-CMenuItem value="copy">Copy</c-CMenuItem>') -> str:
    return f"""
      <c-CSplitButton
        id="save-actions"
        label="Save actions"
        menu_label="More save actions"
        {inputs}
      >
        <c-fill name="start">S</c-fill>
        <c-fill name="default">Save</c-fill>
        <c-fill name="end">E</c-fill>
        <c-fill name="menu">{menu}</c-fill>
      </c-CSplitButton>
    """


def test_schema_and_family_exports_are_exact():
    assert [item.name for item in fields(CSplitButton.Kwargs)] == [
        "id",
        "label",
        "menu_label",
        "type",
        "disabled",
        "primary_disabled",
        "menu_disabled",
        "loading",
        "variant",
        "intent",
        "size",
        "block",
        "loading_pos",
        "open",
        "loop",
        "placement",
        "match_width",
        "close_on_select",
        "class_",
        "style",
        "attrs",
        "primary_attrs",
        "trigger_attrs",
        "menu_attrs",
    ]
    from citry_ui.components import csplitbutton

    assert csplitbutton.__all__ == [
        "CSplitButton",
        "CSplitButtonDefaultSlotData",
        "CSplitButtonEndSlotData",
        "CSplitButtonLoadingSlotData",
        "CSplitButtonMenuSlotData",
        "CSplitButtonStartSlotData",
    ]
    assert all(
        item is not None
        for item in (
            CSplitButtonDefaultSlotData,
            CSplitButtonEndSlotData,
            CSplitButtonLoadingSlotData,
            CSplitButtonMenuSlotData,
            CSplitButtonStartSlotData,
        )
    )


def test_direct_python_sequence_menu_composition_registers_each_declaration():
    app = _app()

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return {
                "split": CSplitButton(
                    id="python-split",
                    label="Save actions",
                    menu_label="More save actions",
                    slots={
                        "default": "Save",
                        "menu": (
                            CMenuItem(value="save-copy", slots={"default": "Save a copy"}),
                            CMenuItem(value="export", slots={"default": "Export"}),
                        ),
                    },
                )
            }

        template = "<main>{{ split }}</main>"

    html = Page().render().serialize(deps_strategy="ignore")

    assert html.count("data-citry-menu-entry") == 2
    assert "Save a copy" in html
    assert "Export" in html


def test_native_anatomy_ids_relationships_and_form_destination_are_exact():
    html = _render(
        _split(
            'type="submit" open placement="top-end" match_width size="lg" '
            'c-primary_attrs="primary_attrs" c-trigger_attrs="trigger_attrs" '
            'c-menu_attrs="menu_attrs"'
        ),
        {
            "primary_attrs": {"name": "action", "value": "save", "aria-label": "Save record"},
            "trigger_attrs": {"aria-describedby": "menu-help"},
            "menu_attrs": {"aria-describedby": "menu-description"},
        },
    )
    root = re.search(r'<div class="cui-split-button"[^>]*>', html)
    assert root is not None
    assert 'id="save-actions"' in root.group(0)
    assert 'role="group"' in root.group(0)
    assert 'aria-label="Save actions"' in root.group(0)
    assert "data-open" in root.group(0)
    assert 'data-citry-ui-part="split-button"' in root.group(0)

    primary = re.search(r'<button class="cui-button cui-split-button__primary"[^>]*>', html)
    assert primary is not None
    assert 'id="save-actions-primary"' in primary.group(0)
    assert 'type="submit"' in primary.group(0)
    assert 'name="action"' in primary.group(0)
    assert 'value="save"' in primary.group(0)
    assert 'aria-label="Save record"' in primary.group(0)
    trigger = re.search(r'<button class="cui-button cui-split-button__menu-trigger"[^>]*>', html)
    assert trigger is not None
    assert 'id="save-actions-menu-trigger"' in trigger.group(0)
    assert 'type="button"' in trigger.group(0)
    assert 'aria-label="More save actions"' in trigger.group(0)
    assert 'aria-controls="save-actions-menu"' in trigger.group(0)
    assert 'aria-expanded="true"' in trigger.group(0)
    assert 'aria-describedby="menu-help"' in trigger.group(0)
    surface = re.search(r'<div class="cui-menu"[^>]*>', html)
    assert surface is not None
    assert 'id="save-actions-menu"' in surface.group(0)
    assert 'aria-labelledby="save-actions-menu-trigger"' in surface.group(0)
    assert 'aria-describedby="menu-description"' in surface.group(0)
    assert 'popover="manual"' in surface.group(0)
    assert 'role="menu"' in surface.group(0)
    assert 'data-placement="top-end"' in surface.group(0)
    assert "data-match-width" in surface.group(0)
    assert html.index(primary.group(0)) < html.index(trigger.group(0)) < html.index(surface.group(0))
    assert 'data-citry-ui-part="split-button-primary-start"' in html
    assert 'data-citry-ui-part="split-button-primary-end"' in html


@pytest.mark.parametrize(
    ("inputs", "message"),
    [
        ('id="save" label=" " menu_label="Menu actions"', "label must contain non-whitespace"),
        ('id="save" label="Save" menu_label=" "', "menu_label must contain non-whitespace"),
        ('id="two words" label="Save" menu_label="Menu actions"', "cannot contain ASCII whitespace"),
        ('id="save" label="Save" menu_label="Menu actions" type="link"', "type must be one of"),
        (
            'id="save" label="Save" menu_label="Menu actions" placement="left"',
            "placement must be one of",
        ),
        ('id="save" label="Save" menu_label="Menu actions" disabled=1', "disabled must be a bool"),
    ],
)
def test_invalid_structural_inputs_fail_before_render(inputs: str, message: str):
    template = f"""
      <c-CSplitButton {inputs}>
        <c-fill name="default">Save</c-fill>
        <c-fill name="menu"><c-CMenuItem value="copy">Copy</c-CMenuItem></c-fill>
      </c-CSplitButton>
    """
    with pytest.raises((TypeError, ValueError), match=message):
        _render(template)


@pytest.mark.parametrize(
    ("destination", "attrs", "message"),
    [
        ("attrs", {"role": "toolbar"}, "cannot override owned"),
        ("primary_attrs", {"tabindex": 3}, "cannot override owned"),
        ("trigger_attrs", {"form": "other"}, "cannot override owned"),
        ("menu_attrs", {"x-data": "{}"}, "ownership directive"),
        ("primary_attrs", {"onclick": "alert(1)"}, "raw event attribute"),
        ("trigger_attrs", {":type": "kind"}, "dynamically bind"),
        ("menu_attrs", {"DATA-X": "a", "data-x": "b"}, "duplicate case variants"),
    ],
)
def test_destination_security_rejects_owned_dynamic_and_ambiguous_attrs(
    destination: str,
    attrs: dict[str, object],
    message: str,
):
    with pytest.raises(ValueError, match=message):
        _render(_split(f'c-{destination}="destination_attrs"'), {"destination_attrs": attrs})


def test_existing_menu_declarations_validate_without_a_forwarding_component():
    html = _render(
        _split(
            menu="""
              <c-CMenuItem value="copy">Copy</c-CMenuItem>
              <c-CMenuItem href="/export">Export</c-CMenuItem>
            """
        )
    )
    assert html.count('role="menuitem"') == 2
    assert 'href="/export"' in html

    with pytest.raises(ValueError, match=r"requires at least one|only valid direct Menu declarations"):
        _render(_split(menu="<button>Unsafe</button>"))


def test_button_and_menu_runtime_and_style_dependencies_are_deduplicated():
    html = _render(
        """
          <!doctype html>
          <html><head><c-css /></head><body>
            <c-CButton>Plain action</c-CButton>
            <c-CMenu id="plain-menu">
              <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                <button type="button" c-bind="activator_attrs">Menu</button>
              </c-fill>
              <c-fill name="default"><c-CMenuItem value="plain">Plain</c-CMenuItem></c-fill>
            </c-CMenu>
            """
        + _split()
        + """
            <c-js />
          </body></html>
        """,
        deps="document",
    )
    assert html.count("cannot replace an incompatible CButton runtime") == 1
    assert html.count("cannot replace an incompatible CMenu runtime") == 1
    assert html.count(_CBUTTON_SHARED_ASSETS.style.content or "missing Button style") == 1
    assert html.count(_CMENU_SHARED_ASSETS.style.content or "missing Menu style") == 1
