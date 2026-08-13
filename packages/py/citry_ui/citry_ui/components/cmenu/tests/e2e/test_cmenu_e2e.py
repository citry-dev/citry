"""Browser tests for CMenu's owned interaction model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cmenu import (
    CMenu,
    CMenuCheckboxItem,
    CMenuGroup,
    CMenuItem,
    CMenuRadioGroup,
    CMenuRadioItem,
    CMenuSeparator,
    CMenuSubmenu,
)
from citry_ui.components.cmenu.cmenu import (
    CInternalMenuCollection,
    CInternalMenuContent,
    CInternalMenuSurface,
)

pytestmark = pytest.mark.e2e

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
    CInternalMenuSurface,
)


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the Menu e2e test path."
    raise RuntimeError(msg)


def _menu_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-menu-e2e", _MENU_COMPONENTS))

    class Page(Component):
        citry = app
        css = """
          :where(#library-menu) {
            --cui-menu-background: rgb(21 32 43);
            --cui-menu-foreground: rgb(245 247 250);
          }

          :where(#library-menu[data-test-item-token]) {
            --cui-menu-item-block-size: 41px;
          }

          :where(#library-menu [data-citry-ui-part="menu-item-label"]) {
            letter-spacing: 2px;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <title>Menu browser contract</title>
              <script>
                window.__menuEvents = [];
                window.__openMenuCallbackModal = () => {
                  const dialog = document.createElement('dialog');
                  dialog.id = 'menu-callback-modal';
                  dialog.innerHTML = '<button type="button">Callback modal focus</button>';
                  document.body.append(dialog);
                  dialog.showModal();
                  dialog.querySelector('button').focus();
                  window.__menuEvents.push(['modal-open']);
                };
              </script>
              <c-css />
            </head>
            <body
              x-data="{
                fieldsetDisabled: false,
                controlled: false,
                accepted: false,
                menuOpen: false,
                menuSize: 'md',
                matchMenuWidth: false,
              }"
              x-init="Alpine.store('menuSpec', {
                radio: 'list',
                badTextValue: null,
                submenuDisabled: false,
              })"
            >
              <form
                id="menu-form"
                @submit.prevent="window.__formSubmits = (window.__formSubmits || 0) + 1"
              >
              <fieldset x-bind:disabled="fieldsetDisabled">
                <c-CMenu
                  id="library-menu"
                  $c-props="{
                    open: controlled ? menuOpen : undefined,
                    size: menuSize,
                    matchWidth: matchMenuWidth,
                    onOpenChange: (nextOpen, detail) => {
                      window.__lastMenuOpenDetail = detail;
                      window.__menuEvents.push([
                        'open', nextOpen, detail.reason, detail.controlled,
                      ]);
                      if (accepted) menuOpen = nextOpen;
                    },
                    onAction: (value, detail) => {
                      if (window.__modalFromMenuCallback === 'command') {
                        window.__menuEvents.push(['action-enter']);
                        window.__openMenuCallbackModal();
                        window.__menuEvents.push(['action-exit']);
                      } else {
                        window.__menuEvents.push([
                          'action', value, detail.kind, detail.path.join('/'),
                        ]);
                      }
                    },
                  }"
                >
                  <c-fill
                    name="activator"
                    data="{ activator_attrs, activator_disabled }"
                  >
                    <button
                      type="button"
                      c-disabled="activator_disabled"
                      c-bind="activator_attrs"
                    >Library actions</button>
                  </c-fill>
                  <c-fill name="default">
                    <c-CMenuItem
                      value="rename"
                      c-attrs="command_attrs"
                      $c-props="{textValue: $store.menuSpec.badTextValue}"
                    >
                      Rename
                    </c-CMenuItem>
                    <c-CMenuCheckboxItem
                      value="notes"
                      checked="mixed"
                      $c-props="{
                        checked: null,
                        onCheckedChange: (nextChecked, detail) => {
                          if (window.__modalFromMenuCallback === 'checkbox') {
                            window.__menuEvents.push(['checked-enter']);
                            window.__openMenuCallbackModal();
                            window.__menuEvents.push(['checked-exit']);
                          }
                          window.__menuEvents.push([
                            'checked',
                            nextChecked,
                            detail.previousChecked,
                            detail.controlled,
                          ]);
                        },
                      }"
                    >
                      Show notes
                    </c-CMenuCheckboxItem>
                    <c-CMenuRadioGroup
                      value="grid"
                      $c-props="{
                        value: $store.menuSpec.radio,
                        onValueChange: (nextValue, detail) => {
                          window.__menuEvents.push([
                            'radio',
                            nextValue,
                            detail.previousValue,
                            detail.controlled,
                            detail.reason,
                          ]);
                        },
                      }"
                    >
                      <c-fill name="label">Layout</c-fill>
                      <c-fill name="default">
                        <c-CMenuRadioItem value="grid">Grid</c-CMenuRadioItem>
                        <c-CMenuRadioItem value="list">List</c-CMenuRadioItem>
                      </c-fill>
                    </c-CMenuRadioGroup>
                    <c-CMenuItem value="locked" disabled>
                      Locked action
                    </c-CMenuItem>
                    <c-CMenuItem href="#guide">
                      Open guide
                    </c-CMenuItem>
                    <c-CMenuSeparator />
                    <c-CMenuSubmenu
                      value="export"
                      $c-props="{disabled: $store.menuSpec.submenuDisabled}"
                    >
                      <c-fill name="label">Export</c-fill>
                      <c-fill name="default">
                        <c-CMenuItem value="pdf">PDF</c-CMenuItem>
                        <c-CMenuSubmenu value="more">
                          <c-fill name="label">More formats</c-fill>
                          <c-fill name="default">
                            <c-CMenuItem value="epub">EPUB</c-CMenuItem>
                            <c-CMenuItem value="markdown">Markdown</c-CMenuItem>
                          </c-fill>
                        </c-CMenuSubmenu>
                      </c-fill>
                    </c-CMenuSubmenu>
                  </c-fill>
                </c-CMenu>
              </fieldset>
              </form>
              <button
                id="disable-fieldset"
                type="button"
                @click="fieldsetDisabled = true"
              >Disable</button>
              <button
                id="control-menu"
                type="button"
                @click="controlled = true"
              >Control</button>
              <button
                id="accept-menu"
                type="button"
                @click="accepted = true"
              >Accept</button>
              <button
                id="release-menu"
                type="button"
                @click="controlled = false"
              >Release</button>
              <button id="outside" type="button">Outside</button>
              <div id="guide">Guide destination</div>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "command_attrs": {
                    "@click.stop": "window.__menuEvents.push(['author-click'])",
                }
            }

    return str(Page())


def _events_menu_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-menu-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(ComponentLibrary("citry-ui-menu-events-e2e", _MENU_COMPONENTS))

    class WorkspaceMenu(Component):
        citry = app

        class Kwargs:
            step: int = 0
            clear_recent: bool = True
            submenu_disabled: bool = False

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                if state.step >= 2:
                    state.clear_recent = False
                return WorkspaceMenu(
                    step=state.step,
                    clear_recent=state.clear_recent,
                    submenu_disabled=state.submenu_disabled,
                )

            def disable_submenu(self, state):
                state.submenu_disabled = True
                return WorkspaceMenu(
                    step=state.step,
                    clear_recent=state.clear_recent,
                    submenu_disabled=True,
                )

        template = """
          <section data-workspace-menu>
            <button
              class="advance-menu"
              type="button"
              @c-click="advance"
            >Advance</button>
            <button
              class="disable-submenu"
              type="button"
              @c-click="disable_submenu"
            >Disable submenu</button>
            <c-CMenu
              #c-key="'events-menu'"
              id="events-menu"
              c-close_on_select="False"
              $c-props="{
                onOpenChange: (open, detail) => {
                  $store.menuMorph.events.push(['open', open, detail.reason]);
                },
              }"
            >
              <c-fill
                name="activator"
                data="{ activator_attrs, activator_disabled }"
              >
                <button
                  type="button"
                  c-disabled="activator_disabled"
                  c-bind="activator_attrs"
                >Library workspace</button>
              </c-fill>
              <c-fill name="default">
                <c-for each="item in items">
                  <c-CMenuItem
                    c-value="item['value']"
                  >{{ item["label"] }}</c-CMenuItem>
                </c-for>
                <c-for each="label in anonymous_items">
                  <c-CMenuItem>{{ label }}</c-CMenuItem>
                </c-for>
                <c-CMenuRadioGroup
                  value="layout-list"
                  $c-props="{
                    onValueChange: (value, detail) => {
                      $store.menuMorph.events.push([
                        'layout', value, detail.previousValue, detail.reason, detail.controlled,
                      ]);
                    },
                  }"
                >
                  <c-fill name="label">Layout</c-fill>
                  <c-fill name="default">
                    <c-for each="radio in layout_radios">
                      <c-CMenuRadioItem
                        c-value="radio['value']"
                      >{{ radio["label"] }}</c-CMenuRadioItem>
                    </c-for>
                  </c-fill>
                </c-CMenuRadioGroup>
                <c-CMenuRadioGroup
                  value="theme-day"
                  $c-props="{
                    value: $store.menuMorph.theme,
                    onValueChange: (value, detail) => {
                      $store.menuMorph.events.push([
                        'theme', value, detail.previousValue, detail.reason, detail.controlled,
                      ]);
                    },
                  }"
                >
                  <c-fill name="label">Theme</c-fill>
                  <c-fill name="default">
                    <c-for each="radio in theme_radios">
                      <c-CMenuRadioItem
                        c-value="radio['value']"
                      >{{ radio["label"] }}</c-CMenuRadioItem>
                    </c-for>
                  </c-fill>
                </c-CMenuRadioGroup>
                <c-if cond="show_submenu">
                  <c-CMenuSubmenu
                    c-disabled="submenu_disabled"
                    value="tools"
                  >
                    <c-fill name="label">Tools</c-fill>
                    <c-fill name="default">
                      <c-CMenuItem value="tools-index">Build index</c-CMenuItem>
                      <c-CMenuItem value="tools-export">Export notes</c-CMenuItem>
                      <c-CMenuSubmenu value="more-tools">
                        <c-fill name="label">More tools</c-fill>
                        <c-fill name="default">
                          <c-for each="item in nested_tool_items">
                            <c-CMenuItem
                              #c-key="item['value']"
                              c-value="item['value']"
                            >{{ item["label"] }}</c-CMenuItem>
                          </c-for>
                        </c-fill>
                      </c-CMenuSubmenu>
                    </c-fill>
                  </c-CMenuSubmenu>
                </c-if>
              </c-fill>
            </c-CMenu>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            del slots
            commands = {
                "rename": {"value": "rename", "label": "Rename shelf"},
                "archive": {"value": "archive", "label": "Archive shelf"},
                "delete": {"value": "delete", "label": "Delete shelf"},
            }
            order = (
                ("rename", "archive", "delete")
                if kwargs.step == 0
                else ("delete", "archive", "rename")
                if kwargs.step == 1
                else ("delete", "rename")
            )
            layout_radios = (
                (
                    {"value": "layout-grid", "label": "Grid layout"},
                    {"value": "layout-list", "label": "List layout"},
                )
                if kwargs.step < 2
                else ({"value": "layout-list", "label": "List layout"},)
            )
            theme_radios = (
                (
                    {"value": "theme-day", "label": "Day theme"},
                    {"value": "theme-night", "label": "Night theme"},
                )
                if kwargs.step < 2
                else ({"value": "theme-day", "label": "Day theme"},)
            )
            return {
                "items": tuple(commands[value] for value in order),
                "anonymous_items": (("Open recent", "Clear recent") if kwargs.clear_recent else ("Open recent",)),
                "layout_radios": layout_radios,
                "theme_radios": theme_radios,
                "show_submenu": kwargs.step < 2,
                "submenu_disabled": kwargs.submenu_disabled,
                "nested_tool_items": (
                    (
                        {"value": "archive", "label": "Archive tool"},
                        {"value": "batch", "label": "Batch tool"},
                        {"value": "inspect", "label": "Inspect graph"},
                    )
                    if kwargs.step == 0
                    else (
                        {"value": "archive", "label": "Archive tool"},
                        {"value": "inspect", "label": "Inspect graph"},
                    )
                ),
            }

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <title>Menu correlated rerender</title>
              <c-css />
            </head>
            <body
              x-data
              x-init="Alpine.store('menuMorph', {events: [], theme: 'theme-night'})"
            >
              <c-workspace-menu />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def _disabled_handoff_page(*, controlled: bool, via_fieldset: bool) -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-menu-disabled-handoff", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(ComponentLibrary("citry-ui-menu-disabled-handoff", _MENU_COMPONENTS))

    class DisabledMenu(Component):
        citry = app

        class Kwargs:
            disabled: bool = False

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def disable(self, state):
                state.disabled = True
                return DisabledMenu(disabled=True)

        template = """
          <section data-disabled-menu>
            <button
              class="server-disable-menu"
              type="button"
              @c-click="disable"
            >Disable Menu</button>
            <fieldset c-disabled="fieldset_disabled">
              <c-CMenu
                #c-key="'disabled-menu'"
                id="disabled-menu"
                c-disabled="menu_disabled"
                $c-props="{
                  open: $store.disabledHandoff.controlled
                    ? $store.disabledHandoff.open
                    : undefined,
                  onOpenChange: (open, detail) => {
                    window.__disabledHandoffEvents.push([
                      open,
                      detail.reason,
                      detail.controlled,
                      detail.forced,
                    ]);
                    if ($store.disabledHandoff.controlled) {
                      $store.disabledHandoff.open = open;
                    }
                  },
                }"
              >
                <c-fill
                  name="activator"
                  data="{ activator_attrs, activator_disabled }"
                >
                  <button
                    type="button"
                    c-disabled="activator_disabled"
                    c-bind="activator_attrs"
                  >Open disabled handoff</button>
                </c-fill>
                <c-fill name="default">
                  <c-CMenuItem value="first">First command</c-CMenuItem>
                  <c-CMenuItem value="second">Second command</c-CMenuItem>
                </c-fill>
              </c-CMenu>
            </fieldset>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, bool]:
            del slots
            return {
                "fieldset_disabled": kwargs.disabled and via_fieldset,
                "menu_disabled": kwargs.disabled and not via_fieldset,
            }

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body
              x-data
              x-init="
                window.__disabledHandoffEvents = [];
                Alpine.store('disabledHandoff', {controlled: __CONTROLLED__, open: false});
              "
            >
              <c-disabled-menu />
              <c-js />
            </body>
          </html>
        """.replace("__CONTROLLED__", "true" if controlled else "false")

    return app, str(Page())


def _configuration_handoff_page(config_case: str) -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-menu-configuration-handoff", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(ComponentLibrary("citry-ui-menu-configuration-handoff", _MENU_COMPONENTS))

    class ConfiguredMenu(Component):
        citry = app

        class Kwargs:
            changed: bool = False

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def change(self, state):
                state.changed = True
                return ConfiguredMenu(changed=True)

        template = """
          <section data-configured-menu>
            <button
              class="change-menu-configuration"
              type="button"
              @c-click="change"
            >Change configuration</button>
            <c-CMenu
              #c-key="'configuration-menu'"
              id="configuration-menu"
              c-close_on_select="close_on_select"
              c-loop="loop"
              c-match_width="match_width"
              c-placement="placement"
              c-size="size"
            >
              <c-fill
                name="activator"
                data="{ activator_attrs, activator_disabled }"
              >
                <button
                  type="button"
                  c-disabled="activator_disabled"
                  c-bind="activator_attrs"
                >Open configuration Menu</button>
              </c-fill>
              <c-fill name="default">
                <c-CMenuItem value="standalone">Standalone action</c-CMenuItem>
                <c-CMenuSubmenu value="first-level">
                  <c-fill name="label">First level</c-fill>
                  <c-fill name="default">
                    <c-CMenuSubmenu value="second-level">
                      <c-fill name="label">Second level</c-fill>
                      <c-fill name="default">
                        <c-CMenuItem value="first-leaf">First leaf</c-CMenuItem>
                        <c-CMenuItem value="second-leaf">Second leaf</c-CMenuItem>
                      </c-fill>
                    </c-CMenuSubmenu>
                  </c-fill>
                </c-CMenuSubmenu>
              </c-fill>
            </c-CMenu>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            del slots
            changed = kwargs.changed
            return {
                "close_on_select": not (changed and config_case == "close_on_select"),
                "loop": not (changed and config_case == "loop"),
                "match_width": changed and config_case == "match_width",
                "placement": "top-end" if changed and config_case == "placement" else "bottom-start",
                "size": "lg" if changed and config_case == "size" else "md",
            }

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <c-configured-menu />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def _two_menu_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-two-menu-e2e", _MENU_COMPONENTS))

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body>
              <c-CMenu id="first-menu">
                <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                  <button
                    type="button"
                    c-disabled="activator_disabled"
                    c-bind="activator_attrs"
                  >First menu</button>
                </c-fill>
                <c-fill name="default">
                  <c-CMenuItem value="first">First action</c-CMenuItem>
                </c-fill>
              </c-CMenu>
              <c-CMenu id="second-menu">
                <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                  <button
                    type="button"
                    c-disabled="activator_disabled"
                    c-bind="activator_attrs"
                  >Second menu</button>
                </c-fill>
                <c-fill name="default">
                  <c-CMenuItem value="second">Second action</c-CMenuItem>
                </c-fill>
              </c-CMenu>
              <div id="unrelated"></div>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _load(page) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"[pageerror] {error}"))
    page.set_content(_menu_page(), wait_until="load")
    page.wait_for_function("document.querySelector('#library-menu')?.hasAttribute('data-citry-menu-initialized')")
    return errors


def _trigger(page):
    return page.locator('[aria-controls="library-menu"]')


def _surface(page):
    return page.locator("#library-menu")


def _focused_text(page) -> str:
    return page.evaluate("document.activeElement?.innerText?.trim() || ''")


def _open_deepest_submenu(page) -> None:
    _trigger(page).click()
    page.keyboard.press("e")
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "document.querySelector('[data-citry-menu-submenu] > [role=menu]').matches(':popover-open')"
    )
    page.wait_for_timeout(550)
    page.keyboard.press("m")
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "document.querySelectorAll('[data-citry-menu-submenu] > [role=menu]:popover-open').length === 2"
    )


def test_menu_initializes_native_anatomy_and_runs_exactly_one_action_sequence(page):
    errors = _load(page)
    trigger = _trigger(page)
    trigger.click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")

    assert _focused_text(page) == "Rename"
    assert _surface(page).get_attribute("role") == "menu"
    assert page.locator('#library-menu [role="menuitemradio"]').count() == 2
    assert page.locator('#library-menu [role="menuitemcheckbox"]').count() == 1

    page.keyboard.press("ArrowDown")
    assert _focused_text(page) == "Show notes"
    page.keyboard.press("Enter")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")

    assert page.evaluate("window.__menuEvents") == [
        ["open", True, "trigger", False],
        ["checked", True, "mixed", False],
        ["action", "notes", "checkbox", ""],
        ["open", False, "action", False],
    ]
    assert errors == []


def test_capture_owned_actions_typeahead_disabled_items_and_native_link_behavior(page):
    errors = _load(page)
    trigger = _trigger(page)
    trigger.click()
    page.keyboard.press("Enter")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")

    events = page.evaluate("window.__menuEvents")
    assert events[:2] == [
        ["open", True, "trigger", False],
        ["action", "rename", "command", ""],
    ]
    assert events.count(["action", "rename", "command", ""]) == 1
    assert events.count(["author-click"]) == 1

    trigger.click()
    page.keyboard.press("l")
    page.keyboard.press("o")
    assert _focused_text(page) == "Locked action"
    page.keyboard.press("Enter")
    assert _surface(page).evaluate("element => element.matches(':popover-open')")
    assert [event for event in page.evaluate("window.__menuEvents") if event[0] == "action"] == [
        ["action", "rename", "command", ""]
    ]

    page.wait_for_timeout(550)
    page.keyboard.press("o")
    assert _focused_text(page) == "Open guide"
    page.keyboard.press("Enter")
    page.wait_for_function("location.hash === '#guide'")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert errors == []


def test_radio_control_release_and_controlled_root_requests_are_owner_authoritative(page):
    errors = _load(page)
    trigger = _trigger(page)
    trigger.click()
    page.keyboard.press("g")
    assert _focused_text(page) == "Grid"
    page.keyboard.press("Enter")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert [event for event in page.evaluate("window.__menuEvents") if event[0] == "radio"] == [
        ["radio", "grid", "list", True, "activation"]
    ]
    radios = page.locator('#library-menu [role="menuitemradio"]')
    assert radios.nth(0).get_attribute("aria-checked") == "false"
    assert radios.nth(1).get_attribute("aria-checked") == "true"

    page.evaluate("Alpine.store('menuSpec').radio = 'grid'")
    page.wait_for_function(
        "document.querySelector('#library-menu [role=menuitemradio]').getAttribute('aria-checked') === 'true'"
    )
    page.evaluate("Alpine.store('menuSpec').radio = null")
    trigger.click()
    page.wait_for_timeout(550)
    page.keyboard.press("l")
    page.keyboard.press("Enter")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert [event for event in page.evaluate("window.__menuEvents") if event[0] == "radio"][-1] == [
        "radio",
        "list",
        "grid",
        False,
        "activation",
    ]

    page.locator("#control-menu").click()
    page.evaluate("window.__menuEvents = []")
    trigger.click()
    page.wait_for_function("window.__menuEvents.length === 1")
    assert not _surface(page).evaluate("element => element.matches(':popover-open')")
    assert page.evaluate("window.__menuEvents") == [["open", True, "trigger", True]]

    page.locator("#accept-menu").click()
    trigger.click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    requests = page.evaluate("window.__menuEvents.length")
    page.evaluate("Alpine.$data(document.body).menuOpen = false")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert page.evaluate("window.__menuEvents.length") == requests

    page.evaluate("Alpine.$data(document.body).menuOpen = true")
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    page.evaluate("document.querySelector('#release-menu').click()")
    _trigger(page).evaluate("element => element.click()")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert page.evaluate("window.__menuEvents.at(-1)") == ["open", False, "trigger", False]
    assert errors == []


def test_submenu_keyboard_navigation_closes_one_logical_level_at_a_time(page):
    errors = _load(page)
    _trigger(page).click()
    page.keyboard.press("e")
    assert _focused_text(page).startswith("Export")
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "document.querySelector('[data-citry-menu-submenu] > [role=menu]').matches(':popover-open')"
    )
    assert _focused_text(page) == "PDF"

    page.wait_for_timeout(550)
    page.keyboard.press("m")
    assert _focused_text(page).startswith("More formats")
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "document.querySelectorAll('[data-citry-menu-submenu] > [role=menu]:popover-open').length === 2"
    )
    assert _focused_text(page) == "EPUB"
    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 3

    page.keyboard.press("Escape")
    assert _focused_text(page).startswith("More formats")
    assert page.locator('[data-citry-menu-submenu] > [role="menu"]:popover-open').count() == 1
    page.keyboard.press("Escape")
    assert _focused_text(page).startswith("Export")
    assert page.locator('[data-citry-menu-submenu] > [role="menu"]:popover-open').count() == 0
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert _trigger(page).evaluate("element => element === document.activeElement")
    assert errors == []


def test_disabling_open_submenu_returns_focus_to_its_apg_focusable_trigger(page):
    errors = _load(page)
    _trigger(page).click()
    page.keyboard.press("e")
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "document.querySelector('[data-citry-menu-submenu] > [role=menu]').matches(':popover-open')"
    )
    assert _focused_text(page) == "PDF"
    page.evaluate("Alpine.store('menuSpec').submenuDisabled = true")
    page.wait_for_function(
        "!document.querySelector('[data-citry-menu-submenu] > [role=menu]').matches(':popover-open')"
    )
    trigger = page.get_by_role("menuitem", name="Export", exact=True)
    assert trigger.get_attribute("aria-disabled") == "true"
    assert trigger.evaluate("element => element === document.activeElement")
    assert errors == []


def test_keyboard_boundaries_tab_outside_deduplication_and_no_form_submit(page):
    errors = _load(page)
    trigger = _trigger(page)
    trigger.focus()
    trigger.press("ArrowUp")
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    assert _focused_text(page).startswith("Export")

    page.keyboard.press("Home")
    assert _focused_text(page) == "Rename"
    page.keyboard.press("End")
    assert _focused_text(page).startswith("Export")
    page.keyboard.press("Shift+Tab")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert page.evaluate("window.__formSubmits || 0") == 0

    page.evaluate("window.__menuEvents = []")
    trigger.click()
    page.locator("#outside").click()
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    close_events = [
        event for event in page.evaluate("window.__menuEvents") if event[0] == "open" and event[1] is False
    ]
    assert len(close_events) == 1
    assert close_events[0][2] in {"outside", "focus-outside"}
    assert errors == []


def test_root_retoggle_and_outside_dismissal_cascade_two_submenu_levels(page):
    errors = _load(page)
    _open_deepest_submenu(page)
    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 3

    _trigger(page).evaluate("element => element.click()")
    page.wait_for_function(
        "!document.querySelector('#library-menu').matches(':popover-open')"
        " && document.querySelectorAll('[data-citry-menu-submenu] > [role=menu]:popover-open').length === 0"
    )
    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 0

    _open_deepest_submenu(page)
    page.locator("#outside").click()
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert page.locator('[data-citry-menu-submenu] > [role="menu"]:popover-open').count() == 0
    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 0
    assert errors == []


def test_public_variables_parts_and_media_contracts_are_effective(page):
    errors = _load(page)
    _surface(page).evaluate("element => element.setAttribute('data-test-item-token', '')")
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    styles = page.evaluate(
        """() => {
          const surface = document.querySelector('#library-menu');
          const item = surface.querySelector('[data-citry-ui-part="menu-item"]');
          const label = item.querySelector('[data-citry-ui-part="menu-item-label"]');
          const surfaceStyle = getComputedStyle(surface);
          return {
            background: surfaceStyle.backgroundColor,
            color: surfaceStyle.color,
            itemBlockSize: getComputedStyle(item).minBlockSize,
            letterSpacing: getComputedStyle(label).letterSpacing,
          };
        }"""
    )
    assert styles == {
        "background": "rgb(21, 32, 43)",
        "color": "rgb(245, 247, 250)",
        "itemBlockSize": "41px",
        "letterSpacing": "2px",
    }
    focused = _surface(page).locator('[data-citry-ui-part="menu-item"]').first
    focused.evaluate(
        """element => {
          element.dataset.intent = 'danger';
          const copy = element.querySelector('.cui-menu__item-copy');
          const description = document.createElement('span');
          description.className = 'cui-menu__item-description';
          description.textContent = 'Irreversible command';
          copy.append(description);
          const end = document.createElement('span');
          end.className = 'cui-menu__item-end';
          end.textContent = '⌘D';
          element.append(end);
        }"""
    )
    focused.focus()
    assert focused.evaluate(
        """element => [
          getComputedStyle(element).backgroundColor,
          getComputedStyle(element).color,
          getComputedStyle(element.querySelector('.cui-menu__item-description')).color,
          getComputedStyle(element.querySelector('.cui-menu__item-end')).color,
        ]"""
    ) == ["rgb(23, 92, 211)", "rgb(255, 255, 255)", "rgb(255, 255, 255)", "rgb(255, 255, 255)"]
    _surface(page).evaluate("element => { element.style.colorScheme = 'dark'; }")
    assert focused.evaluate(
        """element => [
          getComputedStyle(element).backgroundColor,
          getComputedStyle(element).color,
          getComputedStyle(element.querySelector('.cui-menu__item-description')).color,
          getComputedStyle(element.querySelector('.cui-menu__item-end')).color,
        ]"""
    ) == ["rgb(132, 173, 255)", "rgb(16, 24, 40)", "rgb(16, 24, 40)", "rgb(16, 24, 40)"]
    _surface(page).evaluate("element => element.style.setProperty('--cui-menu-focus-foreground', 'rgb(1 2 3)')")
    assert focused.evaluate(
        """element => [
          getComputedStyle(element).color,
          getComputedStyle(element.querySelector('.cui-menu__item-description')).color,
          getComputedStyle(element.querySelector('.cui-menu__item-end')).color,
        ]"""
    ) == ["rgb(1, 2, 3)", "rgb(1, 2, 3)", "rgb(1, 2, 3)"]

    page.emulate_media(reduced_motion="reduce")
    assert (
        _surface(page).evaluate("element => getComputedStyle(element).getPropertyValue('--_cui-menu-duration').trim()")
        == "0ms"
    )
    page.emulate_media(forced_colors="active")
    assert _surface(page).evaluate("element => getComputedStyle(element).boxShadow") == "none"
    page.emulate_media(media="print", forced_colors="none", reduced_motion="no-preference")
    assert _surface(page).evaluate("element => getComputedStyle(element).display") == "block"
    assert errors == []


def test_open_submenu_follows_dynamic_ancestor_color_scheme(page):
    errors = _load(page)
    root = _surface(page)
    root.evaluate(
        """element => {
          element.style.colorScheme = 'light';
          element.style.setProperty(
            '--cui-menu-background',
            'light-dark(rgb(250 251 252), rgb(20 21 22))',
          );
        }"""
    )
    _trigger(page).click()
    page.keyboard.press("e")
    page.keyboard.press("ArrowRight")
    submenu = page.locator('[data-citry-menu-submenu] > [role="menu"]:popover-open').first
    assert submenu.evaluate(
        "element => [getComputedStyle(element).colorScheme, getComputedStyle(element).backgroundColor]"
    ) == ["light", "rgb(250, 251, 252)"]
    root.evaluate("element => { element.style.colorScheme = 'dark'; }")
    page.wait_for_function(
        "getComputedStyle(document.querySelector('[data-citry-menu-submenu] > [role=menu]')).colorScheme === 'dark'"
    )
    assert submenu.evaluate(
        "element => [getComputedStyle(element).colorScheme, getComputedStyle(element).backgroundColor]"
    ) == ["dark", "rgb(20, 21, 22)"]
    assert errors == []


def test_submenu_geometry_drives_chevron_and_shared_runtime_cleans_up(page):
    errors = _load(page)
    _trigger(page).click()
    page.keyboard.press("e")
    page.keyboard.press("ArrowRight")
    submenu = page.locator("[data-citry-menu-submenu]").first
    page.wait_for_function(
        "document.querySelector('[data-citry-menu-submenu]').hasAttribute('data-citry-menu-physical-side')"
    )
    side = submenu.get_attribute("data-citry-menu-physical-side")
    assert side in {"inline-start", "inline-end", "block-start", "block-end"}
    transform = submenu.locator(
        ':scope > [data-citry-ui-part="menu-submenu-trigger"] > [data-citry-ui-part="menu-item-end"]'
    ).evaluate("element => getComputedStyle(element).transform")
    if side == "inline-end":
        assert transform == "none"
    else:
        assert transform != "none"

    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    runtime = page.evaluate(
        """() => {
          const value = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          return {
            layers: value.layers.length,
            activeListenerSets: value.stats.activeListenerSets,
            listening: value.listeners !== null,
          };
        }"""
    )
    assert runtime == {"layers": 0, "activeListenerSets": 0, "listening": False}
    assert errors == []


@pytest.mark.parametrize(
    ("width", "direction", "forward", "planned", "physical"),
    [
        (280, "ltr", "ArrowRight", "block-end", "block-end"),
        (1280, "rtl", "ArrowLeft", "inline-end", "inline-start"),
    ],
)
def test_submenu_collision_fallback_and_rtl_follow_actual_geometry(
    page,
    width,
    direction,
    forward,
    planned,
    physical,
):
    page.set_viewport_size({"width": width, "height": 720})
    errors = _load(page)
    page.evaluate("direction => document.documentElement.dir = direction", direction)
    _trigger(page).click()
    page.keyboard.press("e")
    page.keyboard.press(forward)
    page.wait_for_function(
        "document.querySelector('[data-citry-menu-submenu]').hasAttribute('data-citry-menu-physical-side')"
    )
    submenu = page.locator("[data-citry-menu-submenu]").first
    surface = submenu.locator(':scope > [data-citry-ui-part="menu"]')
    assert surface.get_attribute("data-citry-menu-side") == planned
    assert submenu.get_attribute("data-citry-menu-physical-side") == physical
    chevron_transform = submenu.locator(
        ':scope > [data-citry-ui-part="menu-submenu-trigger"] > [data-citry-ui-part="menu-item-end"]'
    ).evaluate("element => getComputedStyle(element).transform")
    assert chevron_transform != "none"
    assert errors == []


def test_mouse_hover_delay_cancels_before_open_and_keeps_open_on_child_transfer(page):
    errors = _load(page)
    _trigger(page).click()
    submenu = page.locator("[data-citry-menu-submenu]").first
    submenu_trigger = submenu.locator(':scope > [data-citry-ui-part="menu-submenu-trigger"]')
    submenu_surface = submenu.locator(':scope > [data-citry-ui-part="menu"]')

    submenu_trigger.hover()
    page.get_by_role("menuitem", name="Rename").hover()
    page.wait_for_timeout(160)
    assert not submenu_surface.evaluate("element => element.matches(':popover-open')")

    submenu_trigger.hover()
    page.wait_for_function(
        "document.querySelector('[data-citry-menu-submenu] > [role=menu]').matches(':popover-open')"
    )
    submenu_surface.get_by_role("menuitem", name="PDF").hover()
    page.wait_for_timeout(350)
    assert submenu_surface.evaluate("element => element.matches(':popover-open')")
    assert errors == []


@pytest.mark.parametrize("controlled", [False, True], ids=["uncontrolled", "controlled"])
@pytest.mark.parametrize("in_shadow", [False, True], ids=["document-modal", "shadow-modal"])
def test_unrelated_modal_force_closes_open_menu_without_resurrection(page, controlled, in_shadow):
    errors = _load(page)
    if controlled:
        page.locator("#control-menu").click()
        page.locator("#accept-menu").click()
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    page.evaluate("window.__menuEvents = []; window.__lastMenuOpenDetail = null")
    page.evaluate(
        """inShadow => {
          const dialog = document.createElement('dialog');
          dialog.id = 'menu-modal';
          dialog.innerHTML = '<button type="button">Modal focus</button>';
          if (inShadow) {
            const host = document.createElement('div');
            document.body.append(host);
            host.attachShadow({mode: 'open'}).append(dialog);
          } else {
            document.body.append(dialog);
          }
          dialog.showModal();
          dialog.querySelector('button').focus();
        }""",
        in_shadow,
    )
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    close_events = [
        event for event in page.evaluate("window.__menuEvents") if event[0] == "open" and event[1] is False
    ]
    assert close_events == [["open", False, "ancestor", controlled]]
    assert page.evaluate("window.__lastMenuOpenDetail.forced") is True
    page.evaluate("window.__menuEvents = []")
    _trigger(page).evaluate("element => element.click()")
    page.wait_for_timeout(30)
    assert not _surface(page).evaluate("element => element.matches(':popover-open')")
    assert errors == []


@pytest.mark.parametrize("callback_kind", ["command", "checkbox"])
def test_modal_opened_in_action_callbacks_closes_after_callback_order_without_reentrancy(
    page,
    callback_kind,
):
    errors = _load(page)
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    page.evaluate(
        """kind => {
          window.__menuEvents = [];
          window.__lastMenuOpenDetail = null;
          window.__modalFromMenuCallback = kind;
        }""",
        callback_kind,
    )
    target = (
        page.get_by_role("menuitem", name="Rename")
        if callback_kind == "command"
        else page.get_by_role("menuitemcheckbox", name="Show notes")
    )
    target.click()
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    events = page.evaluate("window.__menuEvents")
    if callback_kind == "command":
        assert events == [
            ["action-enter"],
            ["modal-open"],
            ["action-exit"],
            ["open", False, "ancestor", False],
            ["author-click"],
        ]
    else:
        assert events == [
            ["checked-enter"],
            ["modal-open"],
            ["checked-exit"],
            ["checked", True, "mixed", False],
            ["action", "notes", "checkbox", ""],
            ["open", False, "ancestor", False],
        ]
    assert page.evaluate("window.__lastMenuOpenDetail.forced") is True
    assert page.evaluate("document.activeElement?.textContent === 'Callback modal focus'")
    assert errors == []


def test_open_nested_menu_has_no_serious_or_critical_axe_findings(page):
    errors = _load(page)
    _open_deepest_submenu(page)
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` at the repository root before Citry UI axe tests"
    page.add_script_tag(path=str(axe_path))
    violations = page.evaluate(
        """async () => {
          const result = await axe.run(document, { resultTypes: ['violations'] });
          return result.violations.filter(
            (violation) => violation.impact === 'serious' || violation.impact === 'critical',
          );
        }"""
    )
    assert violations == []
    assert errors == []


def test_native_fieldset_disabling_closes_and_blocks_the_menu(page):
    errors = _load(page)
    trigger = _trigger(page)
    trigger.click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    page.evaluate("document.querySelector('#disable-fieldset').click()")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")

    assert trigger.evaluate("element => element.matches(':disabled')")
    trigger.evaluate("element => element.click()")
    page.wait_for_timeout(30)
    assert not _surface(page).evaluate("element => element.matches(':popover-open')")
    assert errors == []


def test_shared_disabled_observer_notifies_only_affected_menu_registrants(page):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"[pageerror] {error}"))
    page.set_content(_two_menu_page(), wait_until="load")
    page.wait_for_function("document.querySelectorAll('[data-citry-menu-initialized]').length === 2")
    page.evaluate(
        """() => {
          const runtime = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          const manager = runtime.menuDisabledObservers.get(document);
          for (const [trigger, callback] of [...manager.entries]) {
            manager.entries.set(trigger, records => {
              trigger.dataset.disabledObserverCalls = String(
                Number(trigger.dataset.disabledObserverCalls || 0) + 1,
              );
              callback(records);
            });
          }
          document.querySelector('[aria-controls="first-menu"]').disabled = true;
        }"""
    )
    page.wait_for_function(
        "document.querySelector('[aria-controls=first-menu]').dataset.disabledObserverCalls === '1'"
    )
    assert page.evaluate(
        """() => [...document.querySelectorAll('[data-citry-menu-trigger]')].map(
          trigger => Number(trigger.dataset.disabledObserverCalls || 0),
        )"""
    ) == [1, 0]
    page.evaluate("document.querySelector('#unrelated').append(document.createElement('span'))")
    page.wait_for_timeout(20)
    assert page.evaluate(
        """() => [...document.querySelectorAll('[data-citry-menu-trigger]')].map(
          trigger => Number(trigger.dataset.disabledObserverCalls || 0),
        )"""
    ) == [1, 0]
    assert errors == []


def test_shadow_root_escape_restores_the_deep_activator(page):
    errors = _load(page)
    page.evaluate(
        """() => {
          const mount = document.createElement('div');
          document.body.append(mount);
          const shadow = mount.attachShadow({mode: 'open'});
          shadow.append(document.querySelector('[data-citry-menu-host]'));
          window.__menuShadow = shadow;
        }"""
    )
    trigger = page.locator("body").evaluate_handle(
        "() => window.__menuShadow.querySelector('[data-citry-menu-trigger]')"
    )
    trigger.as_element().click()
    page.wait_for_function("window.__menuShadow.querySelector('#library-menu').matches(':popover-open')")
    page.evaluate("window.__menuShadow.querySelector('[role=menuitem]').focus()")
    page.keyboard.press("Escape")
    page.wait_for_function("!window.__menuShadow.querySelector('#library-menu').matches(':popover-open')")
    assert page.evaluate(
        "window.__menuShadow.activeElement === window.__menuShadow.querySelector('[data-citry-menu-trigger]')"
    )
    assert errors == []


def test_invalid_settled_content_and_activator_anatomy_fail_closed_then_recover(page):
    errors = _load(page)
    trigger = _trigger(page)
    trigger.click()
    page.evaluate(
        """() => {
          const input = document.createElement('input');
          input.id = 'invalid-menu-label-control';
          document.querySelector('#library-menu [data-citry-ui-part="menu-item-label"]').append(input);
        }"""
    )
    page.wait_for_function("!document.querySelector('#library-menu').hasAttribute('data-citry-menu-initialized')")
    assert not _surface(page).evaluate("element => element.matches(':popover-open')")
    assert _surface(page).evaluate("element => element.inert")

    page.locator("#invalid-menu-label-control").evaluate("element => element.remove()")
    page.wait_for_function("document.querySelector('#library-menu').hasAttribute('data-citry-menu-initialized')")
    assert not _surface(page).evaluate("element => element.matches(':popover-open')")
    trigger.click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")

    page.evaluate(
        """() => {
          document.querySelector('#library-menu').hidePopover();
          const extra = document.createElement('a');
          extra.id = 'extra-activator';
          extra.href = '#extra';
          extra.textContent = 'Extra';
          document.querySelector('[data-citry-menu-host]').prepend(extra);
        }"""
    )
    page.wait_for_function("!document.querySelector('#library-menu').hasAttribute('data-citry-menu-initialized')")
    assert _surface(page).evaluate("element => element.inert")
    assert any("content must remain noninteractive" in error for error in errors)
    assert any("no additional interactive content" in error for error in errors)


@pytest.mark.parametrize("controlled", [False, True], ids=["uncontrolled", "controlled"])
@pytest.mark.parametrize("invalid_kind", ["content", "activator", "empty"])
def test_dynamic_invalid_structure_emits_one_forced_close_and_requires_new_edge(
    page,
    controlled,
    invalid_kind,
):
    errors = _load(page)
    if controlled:
        page.locator("#control-menu").click()
        page.locator("#accept-menu").click()
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    page.evaluate("window.__menuEvents = []; window.__lastMenuOpenDetail = null")
    page.evaluate(
        """kind => {
          const surface = document.querySelector('#library-menu');
          if (kind === 'content') {
            const input = document.createElement('input');
            input.id = 'dynamic-invalid-content';
            surface.querySelector('[data-citry-ui-part="menu-item-label"]').append(input);
          } else if (kind === 'activator') {
            const extra = document.createElement('a');
            extra.id = 'dynamic-invalid-activator';
            extra.href = '#invalid';
            extra.textContent = 'Invalid activator';
            document.querySelector('[data-citry-menu-host]').prepend(extra);
          } else {
            window.__removedMenuChildren = [...surface.children];
            surface.replaceChildren();
          }
        }""",
        invalid_kind,
    )
    page.wait_for_function("!document.querySelector('#library-menu').hasAttribute('data-citry-menu-initialized')")
    page.wait_for_function(
        "window.__menuEvents.filter(event => event[0] === 'open' && event[1] === false).length === 1"
    )
    assert [event for event in page.evaluate("window.__menuEvents") if event[0] == "open" and event[1] is False] == [
        ["open", False, "ancestor", controlled]
    ]
    assert page.evaluate("window.__lastMenuOpenDetail.forced") is True
    page.wait_for_timeout(50)
    assert (
        len([event for event in page.evaluate("window.__menuEvents") if event[0] == "open" and event[1] is False]) == 1
    )

    if invalid_kind == "empty":
        assert any("requires at least one actionable item" in error for error in errors)
        return

    page.evaluate(
        """kind => {
          if (kind === 'content') {
            document.querySelector('#dynamic-invalid-content').remove();
          } else if (kind === 'activator') {
            document.querySelector('#dynamic-invalid-activator').remove();
          } else {
            document.querySelector('#library-menu').append(...window.__removedMenuChildren);
          }
        }""",
        invalid_kind,
    )
    page.wait_for_function("document.querySelector('#library-menu').hasAttribute('data-citry-menu-initialized')")
    assert not _surface(page).evaluate("element => element.matches(':popover-open')")
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    assert errors


@pytest.mark.parametrize(
    ("attribute", "value"),
    [("href", "#details"), ("tabindex", "0")],
)
def test_authored_content_becoming_interactive_fails_closed_and_recovers(
    page,
    attribute,
    value,
):
    errors = _load(page)
    _trigger(page).click()
    page.evaluate(
        """() => {
          const candidate = document.createElement('a');
          candidate.id = 'late-interactive-content';
          candidate.textContent = 'Details';
          document.querySelector('#library-menu [data-citry-ui-part="menu-item-label"]')
            .append(candidate);
        }"""
    )
    page.wait_for_timeout(20)
    assert _surface(page).get_attribute("data-citry-menu-initialized") == ""
    page.locator("#late-interactive-content").evaluate(
        "(element, args) => element.setAttribute(args.attribute, args.value)",
        {"attribute": attribute, "value": value},
    )
    page.wait_for_function("!document.querySelector('#library-menu').hasAttribute('data-citry-menu-initialized')")
    assert _surface(page).evaluate("element => element.inert")
    assert not _surface(page).evaluate("element => element.matches(':popover-open')")

    page.locator("#late-interactive-content").evaluate(
        "(element, name) => element.removeAttribute(name)",
        attribute,
    )
    page.wait_for_function("document.querySelector('#library-menu').hasAttribute('data-citry-menu-initialized')")
    assert not _surface(page).evaluate("element => element.matches(':popover-open')")
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    assert any("content must remain noninteractive" in error for error in errors)


@pytest.mark.parametrize("disabled_source", ["direct", "fieldset"])
def test_dynamic_native_disabled_is_preserved_and_uses_modal_shadow_focus_fallback(
    page,
    disabled_source,
):
    errors = _load(page)
    page.evaluate(
        """() => {
          const mount = document.createElement('div');
          document.body.append(mount);
          const shadow = mount.attachShadow({mode: 'open'});
          const dialog = document.createElement('dialog');
          dialog.id = 'menu-owner-modal';
          dialog.innerHTML = '<button id="modal-fallback" type="button">Fallback</button>';
          shadow.append(dialog);
          dialog.append(document.querySelector('#menu-form'));
          window.__disabledMenuShadow = shadow;
          dialog.showModal();
        }"""
    )
    trigger = (
        page.locator("body")
        .evaluate_handle("() => window.__disabledMenuShadow.querySelector('[data-citry-menu-trigger]')")
        .as_element()
    )
    trigger.click()
    page.evaluate("window.__disabledMenuShadow.querySelector('#library-menu [role=menuitem]').focus()")
    page.evaluate(
        """source => {
          const shadow = window.__disabledMenuShadow;
          if (source === 'direct') shadow.querySelector('[data-citry-menu-trigger]').disabled = true;
          else shadow.querySelector('fieldset').disabled = true;
        }""",
        disabled_source,
    )
    page.wait_for_function("!window.__disabledMenuShadow.querySelector('#library-menu').matches(':popover-open')")
    assert page.evaluate("window.__disabledMenuShadow.querySelector('[data-citry-menu-trigger]').matches(':disabled')")
    assert page.evaluate("window.__disabledMenuShadow.activeElement?.id === 'menu-owner-modal'")

    page.evaluate(
        """source => {
          const shadow = window.__disabledMenuShadow;
          if (source === 'direct') shadow.querySelector('[data-citry-menu-trigger]').disabled = false;
          else shadow.querySelector('fieldset').disabled = false;
        }""",
        disabled_source,
    )
    page.wait_for_function(
        "!window.__disabledMenuShadow.querySelector('[data-citry-menu-trigger]').matches(':disabled')"
    )
    trigger.click()
    page.wait_for_function("window.__disabledMenuShadow.querySelector('#library-menu').matches(':popover-open')")
    assert errors == []


def test_disabled_menu_without_containing_modal_focuses_document_body(page):
    errors = _load(page)
    _trigger(page).click()
    page.locator("#library-menu [role=menuitem]").first.focus()
    _trigger(page).evaluate("element => { element.disabled = true; }")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert page.evaluate("document.activeElement === document.body")
    assert page.locator("body").get_attribute("tabindex") == "-1"
    assert errors == []


def test_dynamic_missing_activator_type_never_submits_and_requires_a_new_open_edge(page):
    errors = _load(page)
    trigger = _trigger(page)
    trigger.evaluate("element => element.removeAttribute('type')")
    trigger.click()
    page.wait_for_function("document.querySelector('[data-citry-menu-trigger]').type === 'button'")
    assert page.evaluate("window.__formSubmits || 0") == 0
    assert not _surface(page).evaluate("element => element.matches(':popover-open')")
    page.wait_for_function("document.querySelector('#library-menu').hasAttribute('data-citry-menu-initialized')")
    trigger.click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    assert any('type="button"' in error for error in errors)


def test_controlled_native_close_and_hidden_open_are_gated_without_resurrection(page):
    errors = _load(page)
    page.locator("#control-menu").click()
    page.locator("#accept-menu").click()
    page.evaluate("Alpine.$data(document.body).menuOpen = true")
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")

    page.evaluate(
        """() => {
          const host = document.querySelector('[data-citry-menu-host]');
          host.hidden = true;
          document.querySelector('#library-menu').hidePopover();
        }"""
    )
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert _surface(page).evaluate("element => element.inert && !element.hasAttribute('data-open')")
    assert _trigger(page).get_attribute("aria-expanded") == "false"

    page.evaluate("document.querySelector('[data-citry-menu-host]').hidden = false")
    page.wait_for_timeout(180)
    assert not _surface(page).evaluate("element => element.matches(':popover-open')")
    page.evaluate("Alpine.$data(document.body).menuOpen = false")
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    assert errors == []


def test_size_match_width_and_optional_regions_propagate_across_the_tree(page):
    page.set_viewport_size({"width": 900, "height": 720})
    errors = _load(page)
    page.evaluate(
        """() => {
          const trigger = document.querySelector('[data-citry-menu-trigger]');
          trigger.style.inlineSize = '96px';
          const state = Alpine.$data(document.body);
          state.menuSize = 'lg';
          state.matchMenuWidth = true;
        }"""
    )
    _trigger(page).click()
    page.keyboard.press("e")
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "document.querySelector('[data-citry-menu-submenu] > [role=menu]').matches(':popover-open')"
    )
    dimensions = page.evaluate(
        """() => {
          const root = document.querySelector('#library-menu');
          const child = document.querySelector('[data-citry-menu-submenu] > [role=menu]');
          return {
            rootWidth: root.getBoundingClientRect().width,
                rootItem: getComputedStyle(root.querySelector('[role=menuitem]')).minBlockSize,
                childItem: getComputedStyle(child.querySelector('[role=menuitem]')).minBlockSize,
            rootSize: root.dataset.size,
            childSize: child.dataset.size,
          };
        }"""
    )
    assert dimensions == {
        "rootWidth": pytest.approx(96, abs=1),
        "rootItem": "40px",
        "childItem": "40px",
        "rootSize": "lg",
        "childSize": "lg",
    }

    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    page.set_viewport_size({"width": 280, "height": 720})
    _trigger(page).evaluate("element => { element.style.inlineSize = '1000px'; element.click(); }")
    page.wait_for_function("document.querySelector('#library-menu').matches(':popover-open')")
    assert _surface(page).evaluate("element => element.getBoundingClientRect().width") <= 264
    assert errors == []


def test_stable_grid_regions_cover_commands_submenus_and_choices_in_ltr_and_rtl(page):
    errors = _load(page)
    _trigger(page).click()
    page.evaluate(
        """() => {
          const add = (root, className, text, before) => {
            const span = document.createElement('span');
            span.className = className;
            span.textContent = text;
            span.setAttribute('aria-hidden', 'true');
            if (before) root.insertBefore(span, before);
            else root.append(span);
          };
          const checkbox = document.querySelector('[role=menuitemcheckbox]');
          const copy = checkbox.querySelector('.cui-menu__item-copy');
          add(checkbox, 'cui-menu__item-start', 'S', copy);
          add(checkbox, 'cui-menu__item-end', 'E');
          const command = document.querySelector('[role=menuitem]');
          add(command, 'cui-menu__item-end', 'K');
        }"""
    )

    def positions(direction: str) -> dict[str, list[float]]:
        page.evaluate("direction => { document.documentElement.dir = direction; }", direction)
        return page.evaluate(
            """() => {
              const centers = elements => elements.map(element => {
                const rect = element.getBoundingClientRect();
                return rect.left + rect.width / 2;
              });
              const choice = document.querySelector('[role=menuitemcheckbox]');
              const submenu = document.querySelector('[data-citry-menu-submenu] > button');
              const command = document.querySelector('[role=menuitem]');
              return {
                choice: centers([
                  choice.querySelector('.cui-menu__choice-indicator'),
                  choice.querySelector('.cui-menu__item-start'),
                  choice.querySelector('.cui-menu__item-copy'),
                  choice.querySelector('.cui-menu__item-end'),
                ]),
                submenu: centers([
                  submenu.querySelector('.cui-menu__item-copy'),
                  submenu.querySelector('.cui-menu__item-end'),
                ]),
                command: centers([
                  command.querySelector('.cui-menu__item-copy'),
                  command.querySelector('.cui-menu__item-end'),
                ]),
              };
            }"""
        )

    ltr = positions("ltr")
    rtl = positions("rtl")
    assert ltr["choice"] == sorted(ltr["choice"])
    assert ltr["submenu"] == sorted(ltr["submenu"])
    assert ltr["command"] == sorted(ltr["command"])
    assert rtl["choice"] == sorted(rtl["choice"], reverse=True)
    assert rtl["submenu"] == sorted(rtl["submenu"], reverse=True)
    assert rtl["command"] == sorted(rtl["command"], reverse=True)
    assert errors == []


def test_reactivating_selected_radio_skips_value_change_but_runs_action_and_close(page):
    errors = _load(page)
    _trigger(page).click()
    page.keyboard.press("l")
    page.evaluate("window.__menuEvents = []")
    page.keyboard.press("Enter")
    page.wait_for_function("!document.querySelector('#library-menu').matches(':popover-open')")
    assert [event for event in page.evaluate("window.__menuEvents") if event[0] == "radio"] == []
    assert [event for event in page.evaluate("window.__menuEvents") if event[0] == "action"] == [
        ["action", "list", "radio", ""]
    ]
    assert [event for event in page.evaluate("window.__menuEvents") if event[0] == "open"] == [
        ["open", False, "action", False]
    ]
    assert errors == []


def test_invalid_text_value_uses_canonical_fallback_until_a_valid_episode(page):
    errors = _load(page)
    _trigger(page).click()
    page.evaluate("Alpine.store('menuSpec').badTextValue = 'wrong\\0value'")
    page.wait_for_timeout(20)
    page.keyboard.press("r")
    assert _focused_text(page) == "Rename"
    assert sum("textValue received invalid client value" in error for error in errors) == 1

    page.evaluate("Alpine.store('menuSpec').badTextValue = 'zebra\\r\\ncommand'")
    page.wait_for_timeout(20)
    page.keyboard.press("z")
    assert _focused_text(page) == "Rename"
    page.evaluate("Alpine.store('menuSpec').badTextValue = 'still\\0wrong'")
    page.wait_for_timeout(20)
    assert sum("textValue received invalid client value" in error for error in errors) == 2


def test_correlated_rerender_retains_reorder_and_recovers_from_removed_choices_and_submenu(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _events_menu_page()
    base = serve_citry_ui_live(app, html)
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"[pageerror] {error}"))
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#events-menu')?.hasAttribute('data-citry-menu-initialized')")
    trigger = page.get_by_role("button", name="Library workspace")
    trigger.click()
    archive = page.get_by_role("menuitem", name="Archive shelf")
    archive.focus()
    page.evaluate(
        """() => {
          window.__menuMorphHost = document.querySelector('[data-citry-menu-host]');
          window.__menuMorphSurface = document.querySelector('#events-menu');
          window.__menuMorphTrigger = document.querySelector('[aria-controls="events-menu"]');
          window.__menuMorphArchive = document.activeElement;
        }"""
    )

    outcome = page.evaluate(
        """() => Citry.events.send(document.querySelector('.advance-menu'), 'advance', {}).then(
          () => ({ok: true}),
          error => ({ok: false, code: error?.code, message: error?.message}),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function(
        "document.querySelector('#events-menu [role=menuitem]').textContent.includes('Delete shelf')"
    )
    retained = page.evaluate(
        """() => ({
          host: document.querySelector('[data-citry-menu-host]') === window.__menuMorphHost,
          surface: document.querySelector('#events-menu') === window.__menuMorphSurface,
          trigger: document.querySelector('[aria-controls="events-menu"]') === window.__menuMorphTrigger,
          focus: document.activeElement?.innerText?.trim(),
        })"""
    )
    assert retained == {
        "host": True,
        "surface": True,
        "trigger": True,
        "focus": "Archive shelf",
    }
    assert page.locator("#events-menu").evaluate("element => element.matches(':popover-open')")
    assert page.locator("#events-menu > [role=menuitem]").all_inner_texts()[:3] == [
        "Delete shelf",
        "Archive shelf",
        "Rename shelf",
    ]

    layout_grid = page.get_by_role("menuitemradio", name="Grid layout")
    layout_grid.focus()
    layout_grid.press("Enter")
    assert layout_grid.get_attribute("aria-checked") == "true"
    submenu_trigger = page.get_by_role("menuitem", name="Tools", exact=True)
    submenu_trigger.hover()
    page.wait_for_function(
        "document.querySelector('#events-menu [data-citry-menu-submenu] > [role=menu]').matches(':popover-open')"
    )
    assert submenu_trigger.evaluate("element => element === document.activeElement")
    outcome = page.evaluate(
        """() => Citry.events.send(document.querySelector('.advance-menu'), 'advance', {}).then(
          () => ({ok: true}),
          error => ({ok: false, code: error?.code, message: error?.message}),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function("!document.querySelector('#events-menu [data-citry-menu-submenu]')")
    page.wait_for_function(
        "[...document.querySelectorAll('[role=menuitemradio]')].some(item => "
        "item.textContent.includes('Day theme') && item === document.activeElement)"
    )

    assert page.get_by_role("menuitemradio", name="Day theme").evaluate(
        "element => element === document.activeElement"
    ), page.evaluate("document.activeElement?.outerHTML")
    assert page.get_by_role("menuitemradio", name="List layout").get_attribute("aria-checked") == "true"
    page.wait_for_function(
        "Alpine.store('menuMorph').events.filter(event => ['layout', 'theme'].includes(event[0])).length === 3"
    )
    assert page.get_by_role("menuitemradio", name="Day theme").get_attribute("aria-checked") == "false"
    choice_events = [
        event for event in page.evaluate("Alpine.store('menuMorph').events") if event[0] in {"layout", "theme"}
    ]
    assert choice_events == [
        ["layout", "layout-grid", "layout-list", "activation", False],
        ["layout", "layout-list", "layout-grid", "removal", False],
        ["theme", "theme-day", "theme-night", "removal", True],
    ], choice_events
    assert page.evaluate("Alpine.store('menuMorph').theme") == "theme-night"
    page.evaluate("Alpine.store('menuMorph').theme = 'theme-day'")
    page.wait_for_function(
        "[...document.querySelectorAll('[role=menuitemradio]')].some("
        "item => item.textContent.includes('Day theme') && item.getAttribute('aria-checked') === 'true'"
        ")"
    )
    assert [event for event in page.evaluate("Alpine.store('menuMorph').events") if event[0] == "theme"] == [
        ["theme", "theme-day", "theme-night", "removal", True]
    ]
    assert page.locator('#events-menu [data-citry-menu-submenu] > [role="menu"]:popover-open').count() == 0
    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 1

    trigger.evaluate("element => element.click()")
    page.wait_for_function("!document.querySelector('#events-menu').matches(':popover-open')")
    assert page.evaluate(
        """() => {
          const runtime = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          return [runtime.layers.length, runtime.stats.activeListenerSets, runtime.listeners !== null];
        }"""
    ) == [0, 0, False]
    assert errors == []


def test_correlated_rerender_restores_two_level_submenu_path_and_duplicate_leaf_value(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _events_menu_page()
    base = serve_citry_ui_live(app, html)
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"[pageerror] {error}"))
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#events-menu')?.hasAttribute('data-citry-menu-initialized')")
    page.get_by_role("button", name="Library workspace").click()
    tools = page.get_by_role("menuitem", name="Tools", exact=True)
    tools.focus()
    tools.press("ArrowRight")
    page.wait_for_function("document.querySelectorAll('#events-menu [role=menu]:popover-open').length === 1")
    more = page.get_by_role("menuitem", name="More tools")
    more.focus()
    more.press("ArrowRight")
    page.wait_for_function("document.querySelectorAll('#events-menu [role=menu]:popover-open').length === 2")
    page.get_by_role("menuitem", name="Archive tool").focus()

    outcome = page.evaluate(
        """() => Citry.events.send(document.querySelector('.advance-menu'), 'advance', {}).then(
          () => ({ok: true}),
          error => ({ok: false, code: error?.code, message: error?.message}),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function(
        "document.querySelector('#events-menu > [role=menuitem]').textContent.includes('Delete shelf')"
    )
    page.wait_for_function("document.querySelectorAll('#events-menu [role=menu]:popover-open').length === 2")
    page.wait_for_function(
        "[...document.querySelectorAll('[role=menuitem]')].some(item => "
        "item.textContent.includes('Archive tool') && item === document.activeElement)"
    )
    assert page.get_by_role("menuitem", name="Archive tool").evaluate("element => element === document.activeElement")
    assert page.get_by_role("menuitem", name="Archive shelf").get_attribute("tabindex") == "-1"
    assert errors == []


def test_correlated_rerender_recovers_removed_leaf_within_retained_submenu(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _events_menu_page()
    base = serve_citry_ui_live(app, html)
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"[pageerror] {error}"))
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#events-menu')?.hasAttribute('data-citry-menu-initialized')")
    page.get_by_role("button", name="Library workspace").click()
    tools = page.get_by_role("menuitem", name="Tools", exact=True)
    tools.focus()
    tools.press("ArrowRight")
    more = page.get_by_role("menuitem", name="More tools")
    more.focus()
    more.press("ArrowRight")
    page.wait_for_function("document.querySelectorAll('#events-menu [role=menu]:popover-open').length === 2")
    page.get_by_role("menuitem", name="Batch tool").focus()

    outcome = page.evaluate(
        """() => Citry.events.send(document.querySelector('.advance-menu'), 'advance', {}).then(
          () => ({ok: true}),
          error => ({ok: false, code: error?.code, message: error?.message}),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function("!document.querySelector('#events-menu').textContent.includes('Batch tool')")
    page.wait_for_function("document.querySelectorAll('#events-menu [role=menu]:popover-open').length === 2")
    page.wait_for_function(
        "[...document.querySelectorAll('[role=menuitem]')].some(item => "
        "item.textContent.includes('Inspect graph') && item === document.activeElement)"
    )
    assert page.get_by_role("menuitem", name="Inspect graph").evaluate("element => element === document.activeElement")
    assert errors == []


def test_correlated_rerender_disabled_submenu_collapses_focus_to_its_trigger(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _events_menu_page()
    base = serve_citry_ui_live(app, html)
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"[pageerror] {error}"))
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#events-menu')?.hasAttribute('data-citry-menu-initialized')")
    page.get_by_role("button", name="Library workspace").click()
    tools = page.get_by_role("menuitem", name="Tools", exact=True)
    tools.focus()
    tools.press("ArrowRight")
    page.wait_for_function("document.querySelectorAll('#events-menu [role=menu]:popover-open').length === 1")
    page.get_by_role("menuitem", name="Build index").focus()

    outcome = page.evaluate(
        """() => Citry.events.send(
          document.querySelector('.disable-submenu'),
          'disable_submenu',
          {},
        ).then(
          () => ({ok: true}),
          error => ({ok: false, code: error?.code, message: error?.message}),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function(
        "document.querySelector('#events-menu [aria-disabled=true]')?.textContent.includes('Tools')"
    )
    page.wait_for_function("document.querySelectorAll('#events-menu [role=menu]:popover-open').length === 0")
    page.wait_for_function(
        "[...document.querySelectorAll('[role=menuitem]')].some(item => "
        "item.textContent.includes('Tools') && item === document.activeElement)"
    )
    tools = page.get_by_role("menuitem", name="Tools", exact=True)
    assert tools.get_attribute("aria-disabled") == "true"
    assert tools.evaluate("element => element === document.activeElement")
    assert errors == []


@pytest.mark.parametrize("controlled", [False, True], ids=["uncontrolled", "controlled"])
@pytest.mark.parametrize("via_fieldset", [False, True], ids=["component-disabled", "fieldset-disabled"])
def test_correlated_rerender_effective_disabled_emits_one_forced_close_and_restores_focus(
    page: Any,
    serve_citry_ui_live: Any,
    controlled: bool,
    via_fieldset: bool,
) -> None:
    app, html = _disabled_handoff_page(controlled=controlled, via_fieldset=via_fieldset)
    base = serve_citry_ui_live(app, html)
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"[pageerror] {error}"))
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#disabled-menu')?.hasAttribute('data-citry-menu-initialized')")
    page.get_by_role("button", name="Open disabled handoff").click()
    page.wait_for_function("document.querySelector('#disabled-menu').matches(':popover-open')")
    page.get_by_role("menuitem", name="Second command").focus()

    outcome = page.evaluate(
        """() => Citry.events.send(
          document.querySelector('.server-disable-menu'),
          'disable',
          {},
        ).then(
          () => ({ok: true}),
          error => ({ok: false, code: error?.code, message: error?.message}),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function("document.querySelector('[aria-controls=disabled-menu]').matches(':disabled')")
    page.wait_for_function("!document.querySelector('#disabled-menu').matches(':popover-open')")
    page.wait_for_function(
        "window.__disabledHandoffEvents.filter(event => event[0] === false && event[1] === 'disabled').length === 1"
    )
    assert page.evaluate("document.activeElement === document.body")
    assert page.locator("#disabled-menu").get_attribute("data-open") is None
    assert page.locator("#disabled-menu").get_attribute("inert") is not None
    page.wait_for_timeout(100)
    close_events = page.evaluate(
        "window.__disabledHandoffEvents.filter(event => event[0] === false && event[1] === 'disabled')"
    )
    assert close_events == [[False, "disabled", controlled, True]]
    assert errors == []


@pytest.mark.parametrize(
    "config_case",
    ["size", "placement", "loop", "match_width", "close_on_select"],
)
def test_correlated_rerender_preserves_open_tree_and_focus_across_non_open_configuration_changes(
    page: Any,
    serve_citry_ui_live: Any,
    config_case: str,
) -> None:
    app, html = _configuration_handoff_page(config_case)
    base = serve_citry_ui_live(app, html)
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"[pageerror] {error}"))
    page.goto(base + "/")
    page.wait_for_function(
        "document.querySelector('#configuration-menu')?.hasAttribute('data-citry-menu-initialized')"
    )
    page.get_by_role("button", name="Open configuration Menu").click()
    first_level = page.get_by_role("menuitem", name="First level")
    first_level.focus()
    first_level.press("ArrowRight")
    second_level = page.get_by_role("menuitem", name="Second level")
    second_level.focus()
    second_level.press("ArrowRight")
    page.wait_for_function("document.querySelectorAll('#configuration-menu [role=menu]:popover-open').length === 2")
    page.get_by_role("menuitem", name="First leaf").focus()

    outcome = page.evaluate(
        """() => Citry.events.send(
          document.querySelector('.change-menu-configuration'),
          'change',
          {},
        ).then(
          () => ({ok: true}),
          error => ({ok: false, code: error?.code, message: error?.message}),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function("document.querySelectorAll('#configuration-menu [role=menu]:popover-open').length === 2")
    page.wait_for_function(
        "[...document.querySelectorAll('[role=menuitem]')].some(item => "
        "item.textContent.includes('First leaf') && item === document.activeElement)"
    )
    assert page.locator("#configuration-menu").evaluate("element => element.matches(':popover-open')")
    assert page.get_by_role("menuitem", name="First leaf").evaluate("element => element === document.activeElement")

    surface = page.locator("#configuration-menu")
    if config_case == "size":
        assert surface.get_attribute("data-size") == "lg"
        assert page.locator('#configuration-menu [role="menu"]').evaluate_all(
            "elements => elements.every(element => element.dataset.size === 'lg')"
        )
    elif config_case == "placement":
        assert surface.get_attribute("data-placement") == "top-end"
    elif config_case == "match_width":
        assert surface.get_attribute("data-match-width") == ""
    elif config_case == "loop":
        page.get_by_role("menuitem", name="First leaf").press("ArrowUp")
        assert page.get_by_role("menuitem", name="First leaf").evaluate(
            "element => element === document.activeElement"
        )
    else:
        page.get_by_role("menuitem", name="Standalone action").click()
        assert surface.evaluate("element => element.matches(':popover-open')")
    assert errors == []


def test_correlated_rerender_distinguishes_retained_anonymous_commands_and_recovers_removal(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _events_menu_page()
    base = serve_citry_ui_live(app, html)
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(f"[pageerror] {error}"))
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#events-menu')?.hasAttribute('data-citry-menu-initialized')")
    page.get_by_role("button", name="Library workspace").click()
    page.get_by_role("menuitem", name="Clear recent").focus()

    outcome = page.evaluate(
        """() => Citry.events.send(document.querySelector('.advance-menu'), 'advance', {}).then(
          () => ({ok: true}),
          error => ({ok: false, code: error?.code, message: error?.message}),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function(
        "document.querySelector('#events-menu > [role=menuitem]').textContent.includes('Delete shelf')"
    )
    assert page.get_by_role("menuitem", name="Clear recent").evaluate("element => element === document.activeElement")

    outcome = page.evaluate(
        """() => Citry.events.send(document.querySelector('.advance-menu'), 'advance', {}).then(
          () => ({ok: true}),
          error => ({ok: false, code: error?.code, message: error?.message}),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function("!document.querySelector('#events-menu').textContent.includes('Clear recent')")
    page.wait_for_function(
        "[...document.querySelectorAll('[role=menuitemradio]')].some(item => "
        "item.textContent.includes('List layout') && item === document.activeElement)"
    )
    assert page.get_by_role("menuitemradio", name="List layout").evaluate(
        "element => element === document.activeElement"
    )
    assert errors == []
