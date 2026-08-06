"""Browser tests for the first production CTabs increment."""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _tabs_page(
    *,
    activation: str = "automatic",
    orientation: str = "horizontal",
    direction: str | None = None,
    loop: bool = True,
) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

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
              <div id="tabs-mount">
                <c-CTabs
                  default_value="account"
                  aria_label="Account settings"
                  c-activation="activation"
                  c-orientation="orientation"
                  c-direction="direction"
                  c-loop="loop"
                >
                    <c-CTab value="account">
                      Account
                    </c-CTab>
                    <c-CTab value="profile" disabled>
                      Profile
                    </c-CTab>
                    <c-CTab value="security">
                      Security
                    </c-CTab>
                  <c-CTabPanel value="account">
                    Account panel
                  </c-CTabPanel>
                  <c-CTabPanel value="profile">
                    Profile panel
                  </c-CTabPanel>
                  <c-CTabPanel value="security">
                    Security panel
                  </c-CTabPanel>
                </c-CTabs>
              </div>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "activation": activation,
                "orientation": orientation,
                "direction": direction,
                "loop": loop,
            }

    return str(Page())


def _customized_tabs_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.brand-scope) {
            --cui-tabs-list-background: rgb(21 43 65);
            --cui-tabs-active-background: rgb(87 65 43);
          }

          :where(.brand-scope [data-citry-ui-part="tab"]) {
            font-weight: 400;
          }

          :where(.brand-scope [data-citry-ui-part="tab-panel"]) {
            padding: 2rem;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <section class="brand-scope">
                <c-CTabs
                  default_value="account"
                  aria_label="Account settings"
                  variant="pill"
                  density="compact"
                  c-attrs="tabs_attrs"
                >
                    <c-CTab value="account">
                      Account
                    </c-CTab>
                    <c-CTab value="security">
                      Security
                    </c-CTab>
                  <c-CTabPanel value="account">
                    Account panel
                  </c-CTabPanel>
                  <c-CTabPanel value="security">
                    Security panel
                  </c-CTabPanel>
                </c-CTabs>
              </section>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "tabs_attrs": {
                    "style": (
                        "--cui-tabs-accent: rgb(18 52 86); "
                        "--cui-tabs-radius: 1rem; "
                        "--cui-tabs-tab-inline-padding: 1.25rem;"
                    ),
                },
            }

    return str(Page())


def _controlled_tabs_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

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
              x-data="{
                selected: 'security',
                locked: false,
                controlled: true,
                acceptRequests: true,
              }"
            >
              <c-CTabs
                default_value="account"
                aria_label="Account settings"
                $c-props="{
                  value: controlled ? selected : undefined,
                  disabled: locked,
                  onValueChange: (value, detail) => {
                    window.__tabsCallbackCount = (window.__tabsCallbackCount || 0) + 1;
                    window.__tabsCallback = detail;
                    if (acceptRequests) {
                      selected = value;
                    }
                  },
                }"
              >
                  <c-CTab value="account">
                    Account
                  </c-CTab>
                  <c-CTab value="security">
                    Security
                  </c-CTab>
                <c-CTabPanel value="account">
                  Account panel
                </c-CTabPanel>
                <c-CTabPanel value="security">
                  Security panel
                </c-CTabPanel>
              </c-CTabs>
              <button id="toggle-disabled" type="button" @click="locked = !locked">
                Toggle disabled
              </button>
              <button id="release-control" type="button" @click="controlled = false">
                Release control
              </button>
              <button id="ignore-requests" type="button" @click="acceptRequests = false">
                Ignore requests
              </button>
              <button id="select-null" type="button" @click="selected = null">
                Select null
              </button>
              <button id="select-account" type="button" @click="selected = 'account'">
                Select account
              </button>
              <button
                id="restore-control"
                type="button"
                @click="selected = 'security'; controlled = true"
              >
                Restore control
              </button>
              <button
                id="select-while-disabled"
                type="button"
                @click="locked = true; selected = 'account'"
              >
                Select while disabled
              </button>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _reactive_configuration_tabs_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

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
              x-data="{
                activation: 'manual',
                orientation: 'vertical',
                direction: 'rtl',
                loop: false,
                disabled: false,
                variant: 'pill',
                density: 'compact',
                align: 'end',
                grow: true,
              }"
            >
              <c-CTabs
                default_value="account"
                aria_label="Account settings"
                direction="ltr"
                $c-props="{
                  activation,
                  orientation,
                  direction,
                  loop,
                  disabled,
                  variant,
                  density,
                  align,
                  grow,
                }"
              >
                  <c-CTab value="account">
                    Account
                  </c-CTab>
                  <c-CTab value="security">
                    Security
                  </c-CTab>
                <c-CTabPanel value="account">
                  Account panel
                </c-CTabPanel>
                <c-CTabPanel value="security">
                  Security panel
                </c-CTabPanel>
              </c-CTabs>
              <button
                id="switch-configuration"
                type="button"
                @click="
                  activation = 'automatic';
                  orientation = 'horizontal';
                  direction = null;
                  loop = true;
                  variant = 'underline';
                  density = 'comfortable';
                  align = 'center';
                  grow = false;
                "
              >
                Switch configuration
              </button>
              <button
                id="omit-configuration"
                type="button"
                @click="
                  activation = undefined;
                  orientation = undefined;
                  direction = undefined;
                  loop = undefined;
                  disabled = undefined;
                  variant = undefined;
                  density = undefined;
                  align = undefined;
                  grow = undefined;
                "
              >
                Omit configuration
              </button>
              <button
                id="invalidate-configuration"
                type="button"
                @click="
                  activation = null;
                  orientation = 'diagonal';
                  direction = 'sideways';
                  loop = null;
                  disabled = null;
                  variant = 'ghost';
                  density = 'tiny';
                  align = 'around';
                  grow = null;
                "
              >
                Invalidate configuration
              </button>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _initially_invalid_props_tabs_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

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
              x-data="{
                invalidLoop: 'yes',
                invalidOrientation: 42,
                invalidGrow: null,
                invalidCallback: 'not-a-function',
              }"
            >
              <c-CTabs
                default_value="account"
                aria_label="Account settings"
                $c-props="{
                  loop: invalidLoop,
                  orientation: invalidOrientation,
                  grow: invalidGrow,
                  onValueChange: invalidCallback,
                }"
              >
                  <c-CTab value="account">
                    Account
                  </c-CTab>
                  <c-CTab value="security">
                    Security
                  </c-CTab>
                <c-CTabPanel value="account">
                  Account panel
                </c-CTabPanel>
                <c-CTabPanel value="security">
                  Security panel
                </c-CTabPanel>
              </c-CTabs>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _nested_tabs_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

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
              x-data="{
                outerValue: undefined,
                outerActivation: 'automatic',
                outerOrientation: 'vertical',
                outerDirection: null,
                outerLoop: true,
                outerDisabled: false,
                outerVariant: 'pill',
                outerDensity: 'compact',
                outerAlign: 'start',
                outerGrow: false,
              }"
            >
              <c-CTabs
                default_value="outer-one"
                aria_label="Outer sections"
                id="outer-tabs"
                orientation="vertical"
                density="compact"
                variant="pill"
                $c-props="{
                  value: outerValue,
                  activation: outerActivation,
                  orientation: outerOrientation,
                  direction: outerDirection,
                  loop: outerLoop,
                  disabled: outerDisabled,
                  variant: outerVariant,
                  density: outerDensity,
                  align: outerAlign,
                  grow: outerGrow,
                }"
              >
                <c-CTab value="outer-one">
                  Outer one
                </c-CTab>
                <c-CTab value="outer-two">
                  Outer two
                </c-CTab>
                <c-CTabPanel value="outer-one">
                  <c-CTabs
                    default_value="inner-one"
                    aria_label="Inner sections"
                    id="inner-tabs"
                  >
                    <c-CTab value="inner-one">
                      Inner one
                    </c-CTab>
                    <c-CTab value="inner-two">
                      Inner two
                    </c-CTab>
                    <c-CTabPanel value="inner-one">
                      Inner panel one
                    </c-CTabPanel>
                    <c-CTabPanel value="inner-two">
                      Inner panel two
                    </c-CTabPanel>
                  </c-CTabs>
                </c-CTabPanel>
                <c-CTabPanel value="outer-two">
                  Outer panel two
                </c-CTabPanel>
              </c-CTabs>
              <button
                id="update-outer-tabs"
                type="button"
                @click="
                  outerActivation = 'manual';
                  outerOrientation = 'horizontal';
                  outerDirection = 'rtl';
                  outerLoop = false;
                  outerDisabled = true;
                  outerVariant = 'underline';
                  outerDensity = 'comfortable';
                  outerAlign = 'end';
                  outerGrow = true;
                "
              >
                Update outer tabs
              </button>
              <button id="control-outer-tabs" type="button" @click="outerValue = 'outer-two'">
                Control outer tabs
              </button>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _dynamic_removal_tabs_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

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
              <c-CTabs
                default_value="account"
                aria_label="Account settings"
                $c-props="{
                  onValueChange: (value, detail) => {
                    window.__tabsRemoval = { value, detail };
                  },
                }"
              >
                <c-CTab value="account">
                  Account
                </c-CTab>
                <c-CTab value="profile" disabled>
                  Profile
                </c-CTab>
                <c-CTab value="security">
                  Security
                </c-CTab>
                <c-CTabPanel value="account">
                  Account panel
                </c-CTabPanel>
                <c-CTabPanel value="profile">
                  Profile panel
                </c-CTabPanel>
                <c-CTabPanel value="security">
                  Security panel
                </c-CTabPanel>
              </c-CTabs>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _events_tabs_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-tabs-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class WorkspaceTabs(Component):
        citry = app

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return WorkspaceTabs(step=state.step)

        template = """
          <section data-workspace-tabs>
            <button
              class="advance-tabs"
              type="button"
              @c-click="advance"
            >
              Advance
            </button>
            <c-CTabs
              #c-key="'workspace-tabs'"
              c-default_value="selected_value"
              aria_label="Workspace sections"
              $c-props="{
                onValueChange: (value, detail) => {
                  window.__serverTabsChange = { value, detail };
                },
              }"
            >
              <c-for each="item in items">
                <c-CTab c-value="item['value']">
                  {{ item["label"] }}
                </c-CTab>
              </c-for>
              <c-for each="item in items">
                <c-CTabPanel c-value="item['value']">
                  {{ item["label"] }} panel
                </c-CTabPanel>
              </c-for>
            </c-CTabs>
          </section>
        """

        def template_data(self, kwargs, slots):
            all_items = {
                "account": {"value": "account", "label": "Account"},
                "security": {"value": "security", "label": "Security"},
                "billing": {"value": "billing", "label": "Billing"},
            }
            order = (
                ("account", "security", "billing")
                if kwargs.step == 0
                else ("billing", "security", "account")
                if kwargs.step == 1
                else ("billing", "account")
            )
            return {
                "items": tuple(all_items[value] for value in order),
                "selected_value": "security" if kwargs.step < 2 else "billing",
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
              <c-workspace-tabs />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def _load(page, html: str) -> None:
    page.set_content(html, wait_until="load")
    page.wait_for_function(
        """() => {
          const root = document.querySelector('[data-citry-tabs-root]');
          return root
            && root.hasAttribute('data-citry-tabs-initialized')
            && root.querySelectorAll('[role="tab"]').length >= 2;
        }"""
    )


def _selected_value(page) -> str:
    return page.locator("[data-citry-tabs-root]").get_attribute("data-value")


def test_pointer_selection_updates_aria_and_panel_state(page):
    _load(page, _tabs_page())

    page.get_by_role("tab", name="Security").click()

    assert _selected_value(page) == "security"
    assert page.get_by_role("tab", name="Security").get_attribute("aria-selected") == "true"
    assert page.get_by_role("tab", name="Account").get_attribute("tabindex") == "-1"
    assert page.get_by_role("tabpanel", name="Security").is_visible()
    assert page.locator('[role="tabpanel"][data-value="account"]').is_hidden()


def test_public_variables_and_part_selectors_override_computed_styles(page):
    _load(page, _customized_tabs_page())

    styles = page.evaluate(
        """() => {
          const list = document.querySelector('[data-citry-ui-part="tab-list"]');
          const activeTab = document.querySelector(
            '[data-citry-ui-part="tab"][data-state="active"]',
          );
          const panel = document.querySelector(
            '[data-citry-ui-part="tab-panel"][data-state="active"]',
          );
          const listStyle = getComputedStyle(list);
          const tabStyle = getComputedStyle(activeTab);
          const panelStyle = getComputedStyle(panel);
          return {
            listBackground: listStyle.backgroundColor,
            activeBackground: tabStyle.backgroundColor,
            activeColor: tabStyle.color,
            activeRadius: tabStyle.borderRadius,
            activePaddingInline: tabStyle.paddingInline,
            activeWeight: tabStyle.fontWeight,
            panelPadding: panelStyle.padding,
          };
        }"""
    )

    assert styles == {
        "listBackground": "rgb(21, 43, 65)",
        "activeBackground": "rgb(87, 65, 43)",
        "activeColor": "rgb(18, 52, 86)",
        "activeRadius": "14px",
        "activePaddingInline": "20px",
        "activeWeight": "400",
        "panelPadding": "32px",
    }


def test_automatic_keyboard_navigation_skips_disabled_tabs_and_uses_home_end(page):
    _load(page, _tabs_page())
    account = page.get_by_role("tab", name="Account")
    security = page.get_by_role("tab", name="Security")
    account.focus()

    account.press("ArrowRight")
    assert security.evaluate("element => element === document.activeElement") is True
    assert _selected_value(page) == "security"

    security.press("Home")
    assert account.evaluate("element => element === document.activeElement") is True
    assert _selected_value(page) == "account"

    account.press("End")
    assert security.evaluate("element => element === document.activeElement") is True
    assert _selected_value(page) == "security"


def test_manual_activation_separates_focus_from_selection(page):
    _load(page, _tabs_page(activation="manual"))
    account = page.get_by_role("tab", name="Account")
    security = page.get_by_role("tab", name="Security")
    account.focus()

    account.press("ArrowRight")
    assert security.evaluate("element => element === document.activeElement") is True
    assert _selected_value(page) == "account"
    assert security.get_attribute("aria-selected") == "false"

    security.press("Enter")
    assert _selected_value(page) == "security"
    assert security.get_attribute("aria-selected") == "true"


def test_vertical_tabs_only_consume_vertical_arrows(page):
    _load(page, _tabs_page(orientation="vertical"))
    result = page.get_by_role("tab", name="Account").evaluate(
        """tab => {
          tab.focus();
          const horizontal = new KeyboardEvent('keydown', {
            key: 'ArrowRight',
            bubbles: true,
            cancelable: true,
          });
          tab.dispatchEvent(horizontal);
          const vertical = new KeyboardEvent('keydown', {
            key: 'ArrowDown',
            bubbles: true,
            cancelable: true,
          });
          tab.dispatchEvent(vertical);
          return {
            horizontalPrevented: horizontal.defaultPrevented,
            verticalPrevented: vertical.defaultPrevented,
            focusedValue: document.activeElement.dataset.value,
          };
        }"""
    )

    assert result == {
        "horizontalPrevented": False,
        "verticalPrevented": True,
        "focusedValue": "security",
    }
    assert _selected_value(page) == "security"


def test_horizontal_rtl_reverses_arrow_direction_and_loop_can_stop(page):
    _load(page, _tabs_page(direction="rtl"))
    account = page.get_by_role("tab", name="Account")
    account.focus()
    account.press("ArrowRight")

    assert page.get_by_role("tab", name="Security").evaluate("element => element === document.activeElement") is True

    _load(page, _tabs_page(loop=False))
    account = page.get_by_role("tab", name="Account")
    account.focus()
    account.press("ArrowLeft")

    assert account.evaluate("element => element === document.activeElement") is True
    assert _selected_value(page) == "account"


def test_client_props_control_value_callback_and_disabled_state(page):
    _load(page, _controlled_tabs_page())
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.value === 'security'")

    page.get_by_role("tab", name="Account").click()
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.value === 'account'")
    assert page.evaluate("window.__tabsCallback") == {
        "value": "account",
        "previousValue": "security",
        "source": "pointer",
    }

    page.locator("#toggle-disabled").click()
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').hasAttribute('data-disabled')")
    assert page.get_by_role("tab", name="Account").is_disabled()
    assert page.get_by_role("tab", name="Security").is_disabled()


def test_controlled_value_remains_authoritative_while_root_is_disabled(page):
    _load(page, _controlled_tabs_page())
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.value === 'security'")

    page.locator("#select-while-disabled").click()
    page.wait_for_function(
        """() => {
          const root = document.querySelector('[data-citry-tabs-root]');
          return root.hasAttribute('data-disabled') && root.dataset.value === 'account';
        }"""
    )
    assert page.get_by_role("tab", name="Account").get_attribute("aria-selected") == "true"
    assert page.get_by_role("tab", name="Account").is_disabled()

    page.locator("#toggle-disabled").click()
    page.wait_for_function("!document.querySelector('[data-citry-tabs-root]').hasAttribute('data-disabled')")
    assert _selected_value(page) == "account"
    assert page.get_by_role("tab", name="Account").is_enabled()


def test_removing_and_restoring_control_preserves_then_recontrols_selection(page):
    _load(page, _controlled_tabs_page())
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.value === 'security'")

    page.locator("#release-control").click()
    assert _selected_value(page) == "security"

    page.get_by_role("tab", name="Account").click()
    assert _selected_value(page) == "account"

    page.locator("#restore-control").click()
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.value === 'security'")
    assert page.get_by_role("tab", name="Security").get_attribute("aria-selected") == "true"


def test_configuration_props_override_python_and_update_dom_and_behavior(page):
    _load(page, _reactive_configuration_tabs_page())
    root = page.locator("[data-citry-tabs-root]")
    tab_list = page.get_by_role("tablist")
    account = page.get_by_role("tab", name="Account")
    security = page.get_by_role("tab", name="Security")
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.orientation === 'vertical'")

    assert root.get_attribute("data-activation") == "manual"
    assert root.get_attribute("data-orientation") == "vertical"
    assert root.get_attribute("data-direction") == "rtl"
    assert root.get_attribute("dir") == "rtl"
    assert root.get_attribute("data-loop") is None
    assert root.get_attribute("data-variant") == "pill"
    assert root.get_attribute("data-density") == "compact"
    assert root.get_attribute("data-align") == "end"
    assert root.get_attribute("data-grow") == ""
    assert tab_list.get_attribute("aria-orientation") == "vertical"
    assert tab_list.get_attribute("data-orientation") == "vertical"

    account.focus()
    account.press("ArrowDown")
    assert security.evaluate("element => element === document.activeElement") is True
    assert _selected_value(page) == "account"

    page.evaluate("document.querySelector('#switch-configuration').click()")
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.orientation === 'horizontal'")
    assert root.get_attribute("data-activation") == "automatic"
    assert root.get_attribute("data-direction") is None
    assert root.get_attribute("dir") is None
    assert root.get_attribute("data-loop") == ""
    assert root.get_attribute("data-variant") == "underline"
    assert root.get_attribute("data-density") == "comfortable"
    assert root.get_attribute("data-align") == "center"
    assert root.get_attribute("data-grow") is None
    assert tab_list.get_attribute("aria-orientation") == "horizontal"
    assert security.evaluate("element => element === document.activeElement") is True
    assert security.get_attribute("tabindex") == "0"

    account.focus()
    account.press("ArrowLeft")
    assert security.evaluate("element => element === document.activeElement") is True
    assert _selected_value(page) == "security"


def test_omitted_and_invalid_configuration_props_restore_python_fallbacks(page):
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    _load(page, _reactive_configuration_tabs_page())
    root = page.locator("[data-citry-tabs-root]")

    page.locator("#omit-configuration").click()
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.variant === 'underline'")
    assert root.get_attribute("data-activation") == "automatic"
    assert root.get_attribute("data-orientation") == "horizontal"
    assert root.get_attribute("data-direction") == "ltr"
    assert root.get_attribute("dir") == "ltr"
    assert root.get_attribute("data-loop") == ""
    assert root.get_attribute("data-disabled") is None
    assert root.get_attribute("data-density") == "default"
    assert root.get_attribute("data-align") == "start"
    assert root.get_attribute("data-grow") is None

    page.locator("#invalidate-configuration").click()
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.orientation === 'horizontal'")
    assert root.get_attribute("data-activation") == "automatic"
    assert root.get_attribute("data-direction") == "ltr"
    assert root.get_attribute("data-loop") == ""
    assert root.get_attribute("data-disabled") is None
    assert root.get_attribute("data-variant") == "underline"
    assert root.get_attribute("data-density") == "default"
    assert root.get_attribute("data-align") == "start"
    assert root.get_attribute("data-grow") is None
    for name in (
        "activation",
        "orientation",
        "direction",
        "loop",
        "disabled",
        "variant",
        "density",
        "align",
        "grow",
    ):
        assert sum(f"CTabs {name} received invalid client value" in message for message in messages) == 1


def test_initial_invalid_prop_values_keep_the_ssr_fallback_interactive(page):
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    _load(page, _initially_invalid_props_tabs_page())
    root = page.locator("[data-citry-tabs-root]")

    assert root.get_attribute("data-citry-tabs-initialized") == ""
    assert root.get_attribute("data-orientation") == "horizontal"
    assert root.get_attribute("data-loop") == ""
    assert root.get_attribute("data-grow") is None
    for name in ("loop", "orientation", "grow", "onValueChange"):
        assert sum(f"CTabs {name} received invalid client value" in message for message in messages) == 1

    page.get_by_role("tab", name="Security").click()
    assert _selected_value(page) == "security"


def test_controlled_requests_wait_for_parent_and_external_updates_do_not_call_back(page):
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    _load(page, _controlled_tabs_page())
    page.locator("#ignore-requests").click()

    page.get_by_role("tab", name="Account").click()
    assert _selected_value(page) == "security"
    assert page.evaluate("window.__tabsCallbackCount") == 1

    page.locator("#select-account").click()
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.value === 'account'")
    assert page.evaluate("window.__tabsCallbackCount") == 1

    page.locator("#select-null").click()
    assert _selected_value(page) == "account"
    assert sum("CTabs value null does not identify an enabled tab" in message for message in messages) == 1

    page.get_by_role("tab", name="Security").click()
    assert _selected_value(page) == "account"
    assert page.evaluate("window.__tabsCallbackCount") == 2


def test_public_state_attributes_are_mirrors_not_behavioral_source_of_truth(page):
    _load(page, _reactive_configuration_tabs_page())
    page.locator("#omit-configuration").click()
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.orientation === 'horizontal'")
    account = page.get_by_role("tab", name="Account")
    security = page.get_by_role("tab", name="Security")

    page.evaluate(
        """() => {
          const root = document.querySelector('[data-citry-tabs-root]');
          root.dataset.orientation = 'vertical';
          root.dataset.value = 'security';
          root.setAttribute('data-disabled', '');
        }"""
    )
    security.click()
    assert security.get_attribute("aria-selected") == "true"

    security.focus()
    security.press("ArrowLeft")
    assert account.evaluate("element => element === document.activeElement") is True
    assert _selected_value(page) == "account"


def test_nested_tabs_keep_selection_and_behavior_inside_the_nearest_root(page):
    _load(page, _nested_tabs_page())
    outer = page.locator("#outer-tabs")
    inner = page.locator("#inner-tabs")
    styles = page.evaluate(
        """() => {
          const outerTab = document.querySelector('#outer-tabs > [role="tablist"] > [role="tab"]');
          const innerTab = document.querySelector('#inner-tabs > [role="tablist"] > [role="tab"]');
          const outerStyle = getComputedStyle(outerTab);
          const innerStyle = getComputedStyle(innerTab);
          return {
            outerMinBlockSize: outerStyle.minBlockSize,
            innerMinBlockSize: innerStyle.minBlockSize,
            outerBorderRadius: outerStyle.borderRadius,
            innerBorderRadius: innerStyle.borderRadius,
            innerBorderBlockEndWidth: innerStyle.borderBlockEndWidth,
          };
        }"""
    )

    assert styles == {
        "outerMinBlockSize": "36px",
        "innerMinBlockSize": "44px",
        "outerBorderRadius": "6px",
        "innerBorderRadius": "0px",
        "innerBorderBlockEndWidth": "3px",
    }

    page.get_by_role("tab", name="Inner two").click()

    assert inner.get_attribute("data-value") == "inner-two"
    assert outer.get_attribute("data-value") == "outer-one"

    page.get_by_role("tab", name="Outer two").click()
    assert outer.get_attribute("data-value") == "outer-two"
    assert inner.get_attribute("data-value") == "inner-two"


def test_reactive_root_configuration_does_not_disable_nested_tabs(page):
    _load(page, _nested_tabs_page())
    page.locator("#update-outer-tabs").click()
    page.wait_for_function("document.querySelector('#outer-tabs').hasAttribute('data-disabled')")

    outer = page.locator("#outer-tabs")
    inner = page.locator("#inner-tabs")
    assert outer.get_attribute("data-value") == "outer-one"
    assert outer.get_attribute("data-activation") == "manual"
    assert outer.get_attribute("data-orientation") == "horizontal"
    assert outer.get_attribute("data-direction") == "rtl"
    assert outer.get_attribute("data-loop") is None
    assert outer.get_attribute("data-variant") == "underline"
    assert outer.get_attribute("data-density") == "comfortable"
    assert outer.get_attribute("data-align") == "end"
    assert outer.get_attribute("data-grow") == ""
    assert page.locator("#outer-tabs > [role='tablist']").get_attribute("aria-orientation") == "horizontal"
    assert page.get_by_role("tab", name="Outer one").is_disabled()
    assert page.get_by_role("tab", name="Outer two").is_disabled()

    assert inner.get_attribute("data-value") == "inner-one"
    assert inner.get_attribute("data-activation") == "automatic"
    assert inner.get_attribute("data-orientation") == "horizontal"
    assert inner.get_attribute("data-direction") is None
    assert inner.get_attribute("data-loop") == ""
    assert inner.get_attribute("data-variant") == "underline"
    assert inner.get_attribute("data-density") == "default"
    assert inner.get_attribute("data-align") == "start"
    assert inner.get_attribute("data-grow") is None
    assert inner.get_attribute("data-disabled") is None
    assert page.get_by_role("tab", name="Inner one").is_enabled()
    assert page.get_by_role("tab", name="Inner two").is_enabled()

    page.get_by_role("tab", name="Inner two").click()
    assert inner.get_attribute("data-value") == "inner-two"

    page.locator("#control-outer-tabs").click()
    page.wait_for_function("document.querySelector('#outer-tabs').dataset.value === 'outer-two'")
    assert outer.get_attribute("data-value") == "outer-two"
    assert inner.get_attribute("data-value") == "inner-two"


def test_extra_rendered_wrappers_are_rejected_during_declaration_collection(page):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

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
              <c-CTabs
                default_value="account"
                aria_label="Account settings"
              >
                <div>
                  <c-CTab value="account">
                    Account
                  </c-CTab>
                  <c-CTab value="security">
                    Security
                  </c-CTab>
                </div>
                <div>
                  <c-CTabPanel value="account">
                    Account panel
                  </c-CTabPanel>
                  <c-CTabPanel value="security">
                    Security panel
                  </c-CTabPanel>
                </div>
              </c-CTabs>
              <c-js />
            </body>
          </html>
        """

    with pytest.raises(ValueError, match="only CTab and CTabPanel declarations"):
        str(Page())


def test_removing_the_component_runs_its_listener_cleanup(page):
    _load(page, _tabs_page())
    assert page.locator("[data-citry-tabs-root]").get_attribute("data-citry-tabs-initialized") == ""

    page.evaluate(
        """() => {
          window.__removedTabsRoot = document.querySelector('[data-citry-tabs-root]');
          document.querySelector('#tabs-mount').remove();
        }"""
    )
    page.wait_for_function("!window.__removedTabsRoot.hasAttribute('data-citry-tabs-initialized')")

    assert page.locator("[data-citry-tabs-root]").count() == 0
    assert page.evaluate(
        """() => {
          const root = window.__removedTabsRoot;
          const account = root.querySelector('[role="tab"][data-value="account"]');
          const security = root.querySelector('[role="tab"][data-value="security"]');
          security.click();
          account.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'ArrowRight',
            bubbles: true,
            cancelable: true,
          }));
          return {
            value: root.dataset.value,
            accountSelected: account.getAttribute('aria-selected'),
            securitySelected: security.getAttribute('aria-selected'),
          };
        }"""
    ) == {
        "value": "account",
        "accountSelected": "true",
        "securitySelected": "false",
    }


def test_removing_the_selected_focused_tab_chooses_and_focuses_an_enabled_fallback(page):
    _load(page, _dynamic_removal_tabs_page())
    security = page.get_by_role("tab", name="Security")
    security.click()
    security.focus()

    page.evaluate(
        """() => {
          document.querySelector('[data-citry-tabs-tab][data-value="security"]').remove();
          document.querySelector('[data-citry-tabs-panel][data-value="security"]').remove();
        }"""
    )
    page.wait_for_function("document.querySelector('[data-citry-tabs-root]').dataset.value === 'account'")

    account = page.get_by_role("tab", name="Account")
    assert account.get_attribute("aria-selected") == "true"
    assert account.get_attribute("tabindex") == "0"
    assert account.evaluate("element => document.activeElement === element") is True
    assert page.get_by_role("tabpanel", name="Account").is_visible()
    assert page.evaluate("window.__tabsRemoval") == {
        "value": "account",
        "detail": {
            "value": "account",
            "previousValue": "security",
            "source": "removal",
        },
    }


def test_events_reorder_preserves_focus_and_server_removal_selects_without_callback(
    page,
    serve_citry_ui_live,
):
    app, html = _events_tabs_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function("window.Citry && Citry.events && Citry.events._internal.alpineStarted === true")

    security = page.get_by_role("tab", name="Security")
    security.focus()
    outcome = page.evaluate(
        """() => Citry.events.send(document.querySelector('.advance-tabs'), 'advance', {}).then(
          () => ({ ok: true }),
          (error) => ({
            ok: false,
            code: error?.code,
            message: error?.message,
            detail: error?.detail,
          }),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function("document.querySelectorAll('[role=tab]')[0].dataset.value === 'billing'")

    assert security.evaluate("element => document.activeElement === element") is True
    assert page.locator("[data-citry-tabs-root]").get_attribute("data-value") == "security"

    page.evaluate("() => Citry.events.send(document.querySelector('.advance-tabs'), 'advance', {})")
    page.wait_for_function("!document.querySelector('[role=tab][data-value=security]')")

    billing = page.get_by_role("tab", name="Billing")
    assert billing.get_attribute("aria-selected") == "true"
    assert billing.evaluate("element => document.activeElement === element") is True
    assert page.get_by_role("tabpanel", name="Billing").is_visible()
    assert page.evaluate("window.__serverTabsChange") is None
