"""Server contract tests for the Menu component family."""

from __future__ import annotations

import re
from dataclasses import fields
from typing import get_args, get_type_hints

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cmenu import (
    CMenu,
    CMenuCheckboxItem,
    CMenuGroup,
    CMenuIntent,
    CMenuItem,
    CMenuPlacement,
    CMenuRadioGroup,
    CMenuRadioItem,
    CMenuSeparator,
    CMenuSize,
    CMenuSubmenu,
)
from citry_ui.components.cmenu.cmenu import CInternalMenuCollection, CInternalMenuContent

_MENU_COMPONENTS = (
    CMenu,
    CMenuItem,
    CMenuCheckboxItem,
    CMenuRadioGroup,
    CMenuRadioItem,
    CMenuGroup,
    CMenuSeparator,
    CMenuSubmenu,
    CInternalMenuCollection,
    CInternalMenuContent,
)


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary(name="citry-ui-menu-tests", components=_MENU_COMPONENTS))
    return app


def _render(template: str, data: dict[str, object] | None = None) -> str:
    app = _app()

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return data or {}

    Page.template = template
    return Page().render().serialize(deps_strategy="ignore")


def _menu(default: str, root_inputs: str = "") -> str:
    root_id = "" if "id=" in root_inputs else 'id="archive-menu"'
    return f"""
      <c-CMenu {root_id} {root_inputs}>
        <c-fill name="activator" data="{{ activator_attrs, activator_disabled }}">
          <button
            type="button"
            c-disabled="activator_disabled"
            c-bind="activator_attrs"
          >Open archive</button>
        </c-fill>
        <c-fill name="default">
          {default}
        </c-fill>
      </c-CMenu>
    """


def test_menu_schema_is_exact_and_runtime_introspectable():
    assert [item.name for item in fields(CMenu.Kwargs)] == [
        "id",
        "open",
        "disabled",
        "loop",
        "placement",
        "match_width",
        "close_on_select",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CMenuItem.Kwargs)] == [
        "value",
        "href",
        "disabled",
        "close_on_select",
        "intent",
        "text_value",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CMenuSubmenu.Kwargs)] == [
        "value",
        "disabled",
        "intent",
        "text_value",
        "class_",
        "style",
        "attrs",
        "trigger_attrs",
        "menu_attrs",
    ]
    hints = get_type_hints(CMenu.Kwargs)
    assert hints["placement"] == CMenuPlacement
    assert hints["size"] == CMenuSize
    assert get_type_hints(CMenuItem.Kwargs)["intent"] == CMenuIntent
    assert get_args(CMenuPlacement) == (
        "top-start",
        "top",
        "top-end",
        "bottom-start",
        "bottom",
        "bottom-end",
    )


def test_menu_renders_complete_native_anatomy_and_typed_activator_data():
    html = _render(
        _menu(
            """
              <c-CMenuItem value="rename">Rename</c-CMenuItem>
              <c-CMenuCheckboxItem value="annotations" checked>
                Show annotations
              </c-CMenuCheckboxItem>
              <c-CMenuGroup>
                <c-fill name="label">Reading view</c-fill>
                <c-fill name="default">
                  <c-CMenuRadioGroup value="folio">
                    <c-fill name="label">Layout</c-fill>
                    <c-fill name="default">
                      <c-CMenuRadioItem value="folio">Folio</c-CMenuRadioItem>
                      <c-CMenuRadioItem value="scroll">Scroll</c-CMenuRadioItem>
                    </c-fill>
                  </c-CMenuRadioGroup>
                </c-fill>
              </c-CMenuGroup>
              <c-CMenuSeparator />
              <c-CMenuSubmenu value="export">
                <c-fill name="label">Export</c-fill>
                <c-fill name="default">
                  <c-CMenuItem value="pdf">PDF</c-CMenuItem>
                </c-fill>
              </c-CMenuSubmenu>
            """,
            'open placement="top-end" match_width size="lg" class_="archive" style="--cui-menu-radius: 1rem"',
        )
    )

    assert 'id="archive-menu-trigger"' in html
    assert 'aria-haspopup="menu"' in html
    assert 'aria-controls="archive-menu"' in html
    assert 'aria-expanded="true"' in html
    surface = re.search(r'<div class="cui-menu archive" id="archive-menu"[^>]*>', html)
    assert surface is not None
    assert 'role="menu"' in surface.group(0)
    assert 'popover="manual"' in surface.group(0)
    assert "data-open" in surface.group(0)
    assert 'data-placement="top-end"' in surface.group(0)
    assert "data-match-width" in surface.group(0)
    assert 'data-size="lg"' in surface.group(0)
    assert "--cui-menu-radius: 1rem" in surface.group(0)
    assert "--_cui-menu-anchor: --_cui-menu-anchor-ref-" in surface.group(0)
    assert html.count('role="menuitem"') == 3
    assert html.count('role="menuitemcheckbox"') == 1
    assert html.count('role="menuitemradio"') == 2
    assert html.count('role="group"') == 2
    assert 'role="separator"' in html
    assert 'aria-checked="true"' in html
    assert 'aria-labelledby="archive-menu-trigger"' in html


def test_command_link_and_item_regions_keep_exact_accessible_relationships():
    html = _render(
        _menu(
            """
              <c-CMenuItem href="/codex">
                <c-fill name="start">S</c-fill>
                <c-fill name="default">Open codex</c-fill>
                <c-fill name="description">Illuminated manuscript</c-fill>
                <c-fill name="end">⌘O</c-fill>
              </c-CMenuItem>
            """
        )
    )

    item = re.search(r'<a class="cui-menu__item"[^>]*>', html)
    assert item is not None
    assert 'href="/codex"' in item.group(0)
    assert 'role="menuitem"' in item.group(0)
    assert 'aria-labelledby="' in item.group(0)
    assert 'aria-describedby="' in item.group(0)
    assert html.count('aria-hidden="true"') >= 2
    assert 'data-citry-ui-part="menu-item-start"' in html
    assert 'data-citry-ui-part="menu-item-description"' in html
    assert 'data-citry-ui-part="menu-item-end"' in html


@pytest.mark.parametrize(
    ("root_inputs", "message"),
    [
        ("open=1", "open must be a bool"),
        ('placement="left"', "placement must be one of"),
        ('size="xl"', "size must be one of"),
        ('id="two words"', "cannot contain ASCII whitespace"),
    ],
)
def test_menu_rejects_invalid_root_inputs(root_inputs: str, message: str):
    with pytest.raises((TypeError, ValueError), match=message):
        _render(_menu('<c-CMenuItem value="read">Read</c-CMenuItem>', root_inputs))


@pytest.mark.parametrize(
    ("declaration", "message"),
    [
        (
            '<c-CMenuItem value="x" href="/x">X</c-CMenuItem>',
            "value cannot be combined with href",
        ),
        (
            '<c-CMenuCheckboxItem value="x" c-checked="1">X</c-CMenuCheckboxItem>',
            "checked must be false, true, or 'mixed'",
        ),
        (
            '<c-CMenuSubmenu value="x" intent="quiet"><c-fill name="label">X</c-fill>'
            '<c-fill name="default"><c-CMenuItem>Y</c-CMenuItem></c-fill></c-CMenuSubmenu>',
            "intent must be one of",
        ),
    ],
)
def test_menu_rejects_invalid_item_inputs(declaration: str, message: str):
    with pytest.raises((TypeError, ValueError), match=message):
        _render(_menu(declaration))


def test_menu_rejects_orphans_stray_markup_and_spoofed_roots():
    with pytest.raises(ValueError, match="valid CMenu declaration collection"):
        _render('<c-CMenuItem value="orphan">Orphan</c-CMenuItem>')

    with pytest.raises(ValueError, match="only valid direct Menu declarations"):
        _render(
            _menu(
                """
                  <div>Stray</div>
                  <c-CMenuItem value="real">Real</c-CMenuItem>
                """
            )
        )

    with pytest.raises(ValueError, match="only valid direct Menu declarations"):
        _render(
            _menu(
                """
                  <div data-citry-menu-entry>
                    <c-CMenuItem value="real">Real</c-CMenuItem>
                  </div>
                """
            )
        )


def test_menu_allows_transparent_declaration_sources():
    app = _app()

    class Entries(Component):
        citry = app
        transparent = True
        template = """
          <c-CMenuItem value="read">Read</c-CMenuItem>
          <c-CMenuItem value="shelve">Shelve</c-CMenuItem>
        """

    class Page(Component):
        citry = app
        template = """
          <c-CMenu>
            <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
              <button
                type="button"
                c-disabled="activator_disabled"
                c-bind="activator_attrs"
              >Open</button>
            </c-fill>
            <c-fill name="default"><c-entries /></c-fill>
          </c-CMenu>
        """

    html = Page().render().serialize(deps_strategy="ignore")
    assert html.count('role="menuitem"') == 2


def test_menu_rejects_collection_value_and_separator_errors():
    with pytest.raises(ValueError, match="unique within the current menu level"):
        _render(
            _menu(
                """
                  <c-CMenuItem value="same">First</c-CMenuItem>
                  <c-CMenuGroup>
                    <c-fill name="label">More</c-fill>
                    <c-fill name="default">
                      <c-CMenuCheckboxItem value="same">Second</c-CMenuCheckboxItem>
                    </c-fill>
                  </c-CMenuGroup>
                """
            )
        )

    with pytest.raises(ValueError, match="between actionable"):
        _render(
            _menu(
                """
                  <c-CMenuSeparator />
                  <c-CMenuItem value="read">Read</c-CMenuItem>
                """
            )
        )

    with pytest.raises(ValueError, match="cannot be consecutive"):
        _render(
            _menu(
                """
                  <c-CMenuItem value="read">Read</c-CMenuItem>
                  <c-CMenuSeparator />
                  <c-CMenuSeparator />
                  <c-CMenuItem value="close">Close</c-CMenuItem>
                """
            )
        )


def test_radio_group_requires_direct_unique_items_and_known_initial_value():
    with pytest.raises(ValueError, match="identify one direct CMenuRadioItem"):
        _render(
            _menu(
                """
                  <c-CMenuRadioGroup value="missing">
                    <c-CMenuRadioItem value="folio">Folio</c-CMenuRadioItem>
                  </c-CMenuRadioGroup>
                """
            )
        )

    with pytest.raises(ValueError, match="only direct CMenuRadioItem"):
        _render(
            _menu(
                """
                  <c-CMenuRadioGroup value="folio">
                    <c-CMenuItem value="folio">Folio</c-CMenuItem>
                  </c-CMenuRadioGroup>
                """
            )
        )

    with pytest.raises(ValueError, match="every radio value to be unique"):
        _render(
            _menu(
                """
                  <c-CMenuRadioGroup value="folio">
                    <c-CMenuRadioItem value="folio">First</c-CMenuRadioItem>
                    <c-CMenuRadioItem value="folio">Second</c-CMenuRadioItem>
                  </c-CMenuRadioGroup>
                """
            )
        )


def test_groups_submenus_and_radio_items_enforce_their_nesting_contracts():
    with pytest.raises(ValueError, match="cannot be nested inside another CMenuGroup"):
        _render(
            _menu(
                """
                  <c-CMenuGroup>
                    <c-fill name="label">Outer</c-fill>
                    <c-fill name="default">
                      <c-CMenuGroup>
                        <c-fill name="label">Inner</c-fill>
                        <c-fill name="default">
                          <c-CMenuItem value="read">Read</c-CMenuItem>
                        </c-fill>
                      </c-CMenuGroup>
                    </c-fill>
                  </c-CMenuGroup>
                """
            )
        )

    with pytest.raises(ValueError, match="direct child of CMenuRadioGroup"):
        _render(_menu('<c-CMenuRadioItem value="folio">Folio</c-CMenuRadioItem>'))

    with pytest.raises(ValueError, match="requires at least one direct declaration"):
        _render(
            _menu(
                """
                  <c-CMenuSubmenu value="empty">
                    <c-fill name="label">Empty</c-fill>
                    <c-fill name="default"></c-fill>
                  </c-CMenuSubmenu>
                """
            )
        )


@pytest.mark.parametrize(
    ("component", "input_name", "attribute"),
    [
        ("CMenu", "attrs", "role"),
        ("CMenu", "attrs", ":aria-labelledby"),
        ("CMenuItem", "attrs", "tabindex"),
        ("CMenuItem", "attrs", "x-show"),
        ("CMenuGroup", "attrs", "aria-label"),
        ("CMenuSeparator", "attrs", "aria-orientation"),
        ("CMenuSubmenu", "trigger_attrs", "aria-expanded"),
        ("CMenuSubmenu", "menu_attrs", "popover"),
    ],
)
def test_owned_attributes_and_directives_are_rejected(
    component: str,
    input_name: str,
    attribute: str,
):
    declaration = {
        "CMenuItem": '<c-CMenuItem value="read" c-attrs="attrs">Read</c-CMenuItem>',
        "CMenuGroup": (
            '<c-CMenuGroup c-attrs="attrs"><c-fill name="label">Group</c-fill>'
            '<c-fill name="default"><c-CMenuItem>Read</c-CMenuItem></c-fill></c-CMenuGroup>'
        ),
        "CMenuSeparator": '<c-CMenuSeparator c-attrs="attrs" />',
        "CMenuSubmenu": (
            f'<c-CMenuSubmenu value="more" c-{input_name}="attrs">'
            '<c-fill name="label">More</c-fill><c-fill name="default">'
            "<c-CMenuItem>Read</c-CMenuItem></c-fill></c-CMenuSubmenu>"
        ),
    }.get(component, '<c-CMenuItem value="read">Read</c-CMenuItem>')
    root_inputs = 'c-attrs="attrs"' if component == "CMenu" else ""

    with pytest.raises(ValueError, match="cannot"):
        _render(_menu(declaration, root_inputs), {"attrs": {attribute: "x"}})


def test_attributes_are_snapshotted_and_root_shortcuts_land_on_documented_roots():
    attrs = {"data-owner": "librarian"}
    html = _render(
        _menu(
            """
              <c-CMenuItem
                value="read"
                class_="reader-action"
                style="color: green"
                c-attrs="attrs"
              >Read</c-CMenuItem>
            """
        ),
        {"attrs": attrs},
    )
    attrs["role"] = "alert"

    assert 'class="cui-menu__item reader-action"' in html
    assert 'style="color: green;"' in html
    assert 'data-owner="librarian"' in html
    assert 'role="alert"' not in html


def test_python_composition_receives_attribute_slot_data():
    seen: dict[str, object] = {}

    def activator(context):
        seen["data"] = context.data
        return "Open"

    value = CMenu(
        slots={
            "activator": activator,
            "default": CMenuItem(value="read", slots={"default": "Read"}),
        }
    )
    html = _render("<main>{{ value }}</main>", {"value": value})

    assert "Read" in html
    assert not isinstance(seen["data"], dict)
    assert seen["data"].activator_attrs["aria-haspopup"] == "menu"
    assert seen["data"].activator_disabled is False
