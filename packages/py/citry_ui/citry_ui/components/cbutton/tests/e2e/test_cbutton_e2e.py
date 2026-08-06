"""Browser tests for the production CButton."""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _interaction_page() -> str:
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
                loading: true,
                disabled: false,
              }"
            >
              <form
                id="probe-form"
                @submit.prevent="
                  window.__buttonSubmits = (window.__buttonSubmits || 0) + 1;
                  window.__buttonSubmitter = $event.submitter?.value;
                "
                @reset="window.__buttonResets = (window.__buttonResets || 0) + 1"
              >
                <input id="probe-input" name="title" value="Original" />
                <span id="submit-mount">
                  <c-CButton
                    type="submit"
                    c-attrs="submit_attrs"
                    $c-props="{
                      loading,
                      disabled,
                    }"
                    @click="window.__buttonClicks = (window.__buttonClicks || 0) + 1"
                  >
                    <c-fill name="start">
                      S
                    </c-fill>
                    <c-fill name="default">
                      Save changes
                    </c-fill>
                  </c-CButton>
                </span>
                <c-CButton
                  type="reset"
                  c-attrs="reset_attrs"
                >
                  Reset
                </c-CButton>
              </form>
              <button
                id="toggle-loading"
                type="button"
                @click="loading = !loading"
              >
                Toggle loading
              </button>
              <button
                id="toggle-disabled"
                type="button"
                @click="disabled = !disabled"
              >
                Toggle disabled
              </button>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "submit_attrs": {
                    "id": "submit-action",
                    "name": "action",
                    "value": "save",
                },
                "reset_attrs": {"id": "reset-action"},
            }

    return str(Page())


def _reactive_configuration_page() -> str:
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
                variant: 'outline',
                intent: 'danger',
                size: 'lg',
                block: true,
                loadingPosition: 'end',
              }"
            >
              <c-CButton
                c-attrs="button_attrs"
                $c-props="{
                  variant,
                  intent,
                  size,
                  block,
                  loadingPosition,
                }"
              >
                Save
              </c-CButton>
              <button
                id="restore-fallbacks"
                type="button"
                @click="
                  variant = undefined;
                  intent = undefined;
                  size = undefined;
                  block = undefined;
                  loadingPosition = undefined;
                "
              >
                Restore fallbacks
              </button>
              <button
                id="set-invalid"
                type="button"
                @click="
                  variant = null;
                  intent = 'success';
                  size = 'tiny';
                  block = 'yes';
                  loadingPosition = 'middle';
                "
              >
                Set invalid
              </button>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {"button_attrs": {"id": "configured-button"}}

    return str(Page())


def _theme_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.ancestor-brand) {
            --cui-button-background: rgb(21 43 65);
            --cui-button-foreground: rgb(245 246 247);
            --cui-button-radius: 1rem;
          }

          :where(.part-brand [data-citry-ui-part="content"]) {
            letter-spacing: 2px;
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
              <section class="ancestor-brand">
                <c-CButton c-attrs="ancestor_attrs">
                  Ancestor brand
                </c-CButton>
              </section>
              <section class="part-brand">
                <c-CButton c-attrs="root_attrs">
                  Root brand
                </c-CButton>
              </section>
              <section style="color-scheme: light">
                <c-CButton
                  intent="success"
                  c-attrs="light_attrs"
                >
                  Light success
                </c-CButton>
              </section>
              <section style="color-scheme: dark">
                <c-CButton
                  intent="success"
                  c-attrs="dark_attrs"
                >
                  Dark success
                </c-CButton>
              </section>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "ancestor_attrs": {"id": "ancestor-button"},
                "root_attrs": {
                    "id": "root-button",
                    "style": ("--cui-button-background: rgb(87 65 43); --cui-button-foreground: rgb(250 250 250);"),
                },
                "light_attrs": {"id": "light-button"},
                "dark_attrs": {"id": "dark-button"},
            }

    return str(Page())


def _loading_presentation_page() -> str:
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
            <body x-data="{ centeredLoading: false }">
              <c-CButton
                loading
                loading_pos="start"
                c-attrs="start_attrs"
              >
                <c-fill name="start">
                  S
                </c-fill>
                <c-fill name="default">
                  Trace spores
                </c-fill>
                <c-fill name="end">
                  E
                </c-fill>
              </c-CButton>
              <c-CButton
                loading
                loading_pos="start"
                c-attrs="start_empty_attrs"
              >
                Trace spores
              </c-CButton>
              <c-CButton
                loading
                loading_pos="end"
                c-attrs="end_attrs"
              >
                <c-fill name="start">
                  S
                </c-fill>
                <c-fill name="default">
                  Trace spores
                </c-fill>
                <c-fill name="end">
                  E
                </c-fill>
              </c-CButton>
              <c-CButton
                c-attrs="center_attrs"
                $c-props="{ loading: centeredLoading }"
              >
                <c-fill name="start">
                  S
                </c-fill>
                <c-fill name="default">
                  Trace spores
                </c-fill>
                <c-fill name="end">
                  E
                </c-fill>
              </c-CButton>
              <button
                id="toggle-centered-loading"
                type="button"
                @click="centeredLoading = true"
              >
                Start centered loading
              </button>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "start_attrs": {"id": "loading-start-with-decoration"},
                "start_empty_attrs": {"id": "loading-start-without-decoration"},
                "end_attrs": {"id": "loading-end-with-decoration"},
                "center_attrs": {"id": "loading-center"},
            }

    return str(Page())


def _link_page() -> str:
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
                disabled: false,
                loading: true,
              }"
            >
              <c-CButton
                href="/field-guide"
                c-attrs="link_attrs"
                $c-props="{
                  disabled,
                  loading,
                }"
                @click="
                  window.__linkClicks = (window.__linkClicks || 0) + 1;
                  window.__linkModifier = $event.ctrlKey;
                  $event.preventDefault();
                "
              >
                Open field guide
              </c-CButton>
              <button
                id="toggle-link-loading"
                type="button"
                @click="loading = !loading"
              >
                Toggle loading
              </button>
              <button
                id="toggle-link-disabled"
                type="button"
                @click="disabled = !disabled"
              >
                Toggle disabled
              </button>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "link_attrs": {
                    "id": "field-guide-link",
                    "target": "_blank",
                    "rel": "noreferrer",
                    "tabindex": "2",
                }
            }

    return str(Page())


def _load(page, html: str, selector: str = ".cui-button") -> None:
    page.set_content(html, wait_until="load")
    page.wait_for_function(
        """selector => {
          const button = document.querySelector(selector);
          return button?.hasAttribute('data-citry-button-initialized');
        }""",
        arg=selector,
    )


def test_loading_retains_focus_and_blocks_click_keyboard_and_form_submission(page):
    _load(page, _interaction_page(), "#submit-action")
    button = page.locator("#submit-action")

    assert button.evaluate("element => !element.disabled") is True
    assert button.get_attribute("aria-busy") == "true"
    assert button.get_attribute("aria-disabled") == "true"
    assert button.get_attribute("data-loading") == ""
    button.focus()
    assert button.evaluate("element => element === document.activeElement") is True

    page.evaluate("document.querySelector('#submit-action').click()")
    button.press("Enter")
    button.press(" ")
    page.evaluate("document.querySelector('#probe-form').requestSubmit(document.querySelector('#submit-action'))")

    assert page.evaluate("window.__buttonClicks || 0") == 0
    assert page.evaluate("window.__buttonSubmits || 0") == 0
    assert button.evaluate("element => element === document.activeElement") is True


def test_releasing_loading_restores_native_click_submitter_and_reset_behavior(page):
    _load(page, _interaction_page(), "#submit-action")
    button = page.locator("#submit-action")
    page.locator("#toggle-loading").click()
    page.wait_for_function("!document.querySelector('#submit-action').hasAttribute('data-loading')")

    button.click()

    assert page.evaluate("window.__buttonClicks") == 1
    assert page.evaluate("window.__buttonSubmits") == 1
    assert page.evaluate("window.__buttonSubmitter") == "save"

    page.locator("#probe-input").fill("Changed")
    page.locator("#reset-action").click()
    assert page.locator("#probe-input").input_value() == "Original"
    assert page.evaluate("window.__buttonResets") == 1


def test_disabled_client_prop_uses_native_disabled_semantics(page):
    _load(page, _interaction_page(), "#submit-action")
    page.locator("#toggle-loading").click()
    page.locator("#toggle-disabled").click()
    page.wait_for_function("document.querySelector('#submit-action').disabled")
    button = page.locator("#submit-action")

    assert button.is_disabled()
    assert button.get_attribute("data-disabled") == ""
    assert button.get_attribute("aria-disabled") == "true"
    page.evaluate("document.querySelector('#submit-action').click()")
    assert page.evaluate("window.__buttonClicks || 0") == 0
    assert page.evaluate("window.__buttonSubmits || 0") == 0


def test_reactive_configuration_updates_and_omission_restores_server_fallbacks(page):
    _load(page, _reactive_configuration_page(), "#configured-button")
    button = page.locator("#configured-button")
    page.wait_for_function("document.querySelector('#configured-button').dataset.variant === 'outline'")

    assert button.get_attribute("data-intent") == "danger"
    assert button.get_attribute("data-size") == "lg"
    assert button.get_attribute("data-block") == ""
    assert button.get_attribute("data-loading-position") == "end"

    page.locator("#restore-fallbacks").click()
    page.wait_for_function("document.querySelector('#configured-button').dataset.variant === 'solid'")

    assert button.get_attribute("data-intent") == "primary"
    assert button.get_attribute("data-size") == "md"
    assert button.get_attribute("data-block") is None
    assert button.get_attribute("data-loading-position") == "center"


def test_invalid_client_configuration_falls_back_per_field_and_logs_once(page):
    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    _load(page, _reactive_configuration_page(), "#configured-button")
    page.locator("#set-invalid").click()
    page.wait_for_function("document.querySelector('#configured-button').dataset.intent === 'success'")
    button = page.locator("#configured-button")

    assert button.get_attribute("data-variant") == "solid"
    assert button.get_attribute("data-intent") == "success"
    assert button.get_attribute("data-size") == "md"
    assert button.get_attribute("data-block") is None
    assert button.get_attribute("data-loading-position") == "center"
    assert sum("CButton variant received invalid client value null" in message for message in messages) == 1
    assert sum("CButton size received invalid client value" in message for message in messages) == 1
    assert sum("CButton block received invalid client value" in message for message in messages) == 1
    assert sum("CButton loadingPosition received invalid client value" in message for message in messages) == 1


def test_public_variables_parts_and_nested_color_schemes_affect_computed_styles(page):
    _load(page, _theme_page(), "#ancestor-button")
    styles = page.evaluate(
        """() => {
          const read = (selector) => getComputedStyle(document.querySelector(selector));
          const ancestor = read('#ancestor-button');
          const root = read('#root-button');
          const content = read('#root-button [data-citry-ui-part="content"]');
          const light = read('#light-button');
          const dark = read('#dark-button');
          return {
            ancestorBackground: ancestor.backgroundColor,
            ancestorColor: ancestor.color,
            ancestorRadius: ancestor.borderRadius,
            rootBackground: root.backgroundColor,
            rootColor: root.color,
            contentSpacing: content.letterSpacing,
            lightBackground: light.backgroundColor,
            darkBackground: dark.backgroundColor,
          };
        }"""
    )

    assert styles["ancestorBackground"] == "rgb(21, 43, 65)"
    assert styles["ancestorColor"] == "rgb(245, 246, 247)"
    assert styles["ancestorRadius"] == "16px"
    assert styles["rootBackground"] == "rgb(87, 65, 43)"
    assert styles["rootColor"] == "rgb(250, 250, 250)"
    assert styles["contentSpacing"] == "2px"
    assert styles["lightBackground"] != styles["darkBackground"]


def test_loading_positions_replace_only_the_documented_visual_content(page):
    _load(page, _loading_presentation_page(), "#loading-start-with-decoration")

    styles = page.evaluate(
        """() => {
          const opacity = (root, part) => getComputedStyle(
            document.querySelector(`${root} [data-citry-ui-part="${part}"]`),
          ).opacity;
          const emptyRoot = document.querySelector('#loading-start-without-decoration');
          const emptyContent = emptyRoot.querySelector('[data-citry-ui-part="content"]');
          const emptyIndicator = emptyRoot.querySelector(
            '[data-citry-ui-part="loading-indicator"]',
          );
          const contentRect = emptyContent.getBoundingClientRect();
          const indicatorRect = emptyIndicator.getBoundingClientRect();
          return {
            start: {
              start: opacity('#loading-start-with-decoration', 'start'),
              content: opacity('#loading-start-with-decoration', 'content'),
              end: opacity('#loading-start-with-decoration', 'end'),
            },
            end: {
              start: opacity('#loading-end-with-decoration', 'start'),
              content: opacity('#loading-end-with-decoration', 'content'),
              end: opacity('#loading-end-with-decoration', 'end'),
            },
            missingStartMargin: getComputedStyle(emptyContent).marginInlineStart,
            missingStartDoesNotOverlap: indicatorRect.right <= contentRect.left,
          };
        }"""
    )

    assert styles["start"] == {"start": "0", "content": "1", "end": "1"}
    assert styles["end"] == {"start": "1", "content": "1", "end": "0"}
    assert styles["missingStartMargin"] != "0px"
    assert styles["missingStartDoesNotOverlap"] is True

    center = page.locator("#loading-center")
    indicator = center.locator('[data-citry-ui-part="loading-indicator"]')
    assert indicator.is_hidden()
    assert indicator.evaluate("element => getComputedStyle(element).display") == "none"
    width_before = center.evaluate("element => element.getBoundingClientRect().width")
    page.locator("#toggle-centered-loading").click()
    page.wait_for_function("document.querySelector('#loading-center').hasAttribute('data-loading')")
    width_after = center.evaluate("element => element.getBoundingClientRect().width")

    assert width_after == pytest.approx(width_before, abs=0.01)
    assert indicator.is_visible()
    assert indicator.evaluate("element => getComputedStyle(element).display") == "flex"
    assert (
        center.locator('[data-citry-ui-part="start"]').evaluate("element => getComputedStyle(element).opacity") == "0"
    )
    assert (
        center.locator('[data-citry-ui-part="content"]').evaluate("element => getComputedStyle(element).opacity")
        == "0"
    )
    assert center.locator('[data-citry-ui-part="end"]').evaluate("element => getComputedStyle(element).opacity") == "0"


def test_link_loading_and_disabled_states_block_activation_then_restore_native_link_behavior(page):
    _load(page, _link_page(), "#field-guide-link")
    link = page.locator("#field-guide-link")

    assert link.evaluate("element => element.localName") == "a"
    assert link.get_attribute("href") is None
    assert link.get_attribute("tabindex") == "2"
    link.focus()
    assert link.evaluate("element => element === document.activeElement") is True
    link.dispatch_event("click", {"ctrlKey": True})
    assert page.evaluate("window.__linkClicks || 0") == 0

    page.locator("#toggle-link-loading").click()
    page.wait_for_function("document.querySelector('#field-guide-link').getAttribute('href') === '/field-guide'")
    assert link.get_attribute("tabindex") == "2"
    link.dispatch_event("click", {"ctrlKey": True})
    assert page.evaluate("window.__linkClicks") == 1
    assert page.evaluate("window.__linkModifier") is True

    page.locator("#toggle-link-disabled").click()
    page.wait_for_function("!document.querySelector('#field-guide-link').hasAttribute('href')")
    assert link.get_attribute("tabindex") == "-1"
    link.dispatch_event("click")
    assert page.evaluate("window.__linkClicks") == 1


def test_removing_button_runs_component_listener_cleanup(page):
    _load(page, _interaction_page(), "#submit-action")
    page.evaluate(
        """() => {
          window.__removedButton = document.querySelector('#submit-action');
          document.querySelector('#submit-mount').remove();
        }"""
    )
    page.wait_for_timeout(100)

    assert page.evaluate("!window.__removedButton.hasAttribute('data-citry-button-initialized')") is True
    page.evaluate("window.__removedButton.click()")
    assert page.evaluate("window.__buttonClicks || 0") == 0
