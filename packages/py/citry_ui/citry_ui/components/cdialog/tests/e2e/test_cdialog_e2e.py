"""Browser tests for the production CDialog."""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _dialog_page(*, controlled: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.dialog-brand) {
            --cui-dialog-background: rgb(21 43 65);
            --cui-dialog-foreground: rgb(245 246 247);
            --cui-dialog-radius: 1rem;
          }

          :where(.dialog-brand [data-citry-ui-part="title"]) {
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
            <body c-bind="body_attrs">
              <section
                class="dialog-brand"
                style="color-scheme: dark"
              >
                <c-CDialog
                  id="profile-dialog"
                  c-attrs="dialog_attrs"
                  $c-props="{
                    open: controlled ? open : undefined,
                    dismissible: dialogDismissible,
                    closeOnEscape: dialogCloseOnEscape,
                    closeOnOutside: dialogCloseOnOutside,
                    initialFocus: dialogInitialFocus,
                    size: dialogSize,
                    scroll: dialogScroll,
                    onOpenChange: (nextOpen, detail) => {
                      window.__dialogRequest = {
                        nextOpen,
                        reason: detail.reason,
                        controlled: detail.controlled,
                        returnValue: detail.returnValue,
                      };
                      window.__dialogRequests = (window.__dialogRequests || 0) + 1;
                      if (acceptRequests) {
                        open = nextOpen;
                      }
                    },
                  }"
                >
                  <c-fill
                    name="activator"
                    data="{ activator_attrs }"
                  >
                    <c-CButton c-attrs="activator_attrs">
                      Edit profile
                    </c-CButton>
                  </c-fill>
                  <c-fill name="title">
                    Edit profile
                  </c-fill>
                  <c-fill name="description">
                    Update the public details shown to your team.
                  </c-fill>
                  <c-fill name="default">
                    <label for="profile-name">
                      Display name
                    </label>
                    <input id="profile-name" value="Ada" autofocus />
                    <c-CDialog id="nested-dialog">
                      <c-fill
                        name="activator"
                        data="{ activator_attrs }"
                      >
                        <c-CButton c-attrs="activator_attrs">
                          Review access
                        </c-CButton>
                      </c-fill>
                      <c-fill name="title">
                        Review access
                      </c-fill>
                      <c-fill name="default">
                        Nested dialog content
                      </c-fill>
                      <c-fill
                        name="actions"
                        data="{ close_attrs }"
                      >
                        <c-CButton c-attrs="close_attrs">
                          Done
                        </c-CButton>
                      </c-fill>
                    </c-CDialog>
                    <form method="dialog">
                      <button
                        id="native-result"
                        type="submit"
                        value="charted"
                      >
                        Chart observation
                      </button>
                    </form>
                  </c-fill>
                  <c-fill
                    name="actions"
                    data="{ close_attrs }"
                  >
                    <c-CButton
                      variant="outline"
                      c-attrs="close_attrs"
                    >
                      Cancel
                    </c-CButton>
                    <c-CButton c-attrs="save_attrs">
                      Save
                    </c-CButton>
                  </c-fill>
                </c-CDialog>
              </section>
              <button id="accept-requests" type="button" @click="acceptRequests = true">
                Accept requests
              </button>
              <button id="force-open" type="button" @click="open = true">
                Force open
              </button>
              <button id="force-close" type="button" @click="open = false">
                Force close
              </button>
              <button id="invalidate-open" type="button" @click="open = 'invalid'">
                Invalidate open
              </button>
              <button
                id="configure-title-focus"
                type="button"
                @click="dialogInitialFocus = 'title'; dialogSize = 'lg'; dialogScroll = 'dialog'"
              >
                Configure title focus
              </button>
              <button
                id="disable-passive-dismissal"
                type="button"
                @click="dialogDismissible = false"
              >
                Disable passive dismissal
              </button>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "body_attrs": {
                    "x-data": (
                        "{ controlled: "
                        + str(controlled).lower()
                        + ", open: false, acceptRequests: false, dialogDismissible: true, "
                        + "dialogCloseOnEscape: true, dialogCloseOnOutside: true, "
                        + "dialogInitialFocus: 'auto', dialogSize: 'md', dialogScroll: 'body' }"
                    ),
                },
                "dialog_attrs": {"data-workflow": "profile"},
                "save_attrs": {"id": "save-profile"},
            }

    return str(Page())


def _load(page, *, controlled: bool = False) -> None:
    page.set_content(_dialog_page(controlled=controlled), wait_until="load")
    page.wait_for_function(
        """() => {
          const hosts = document.querySelectorAll('[data-citry-dialog-host]');
          return hosts.length === 2
            && [...hosts].every((host) => host.hasAttribute('data-citry-dialog-initialized'));
        }"""
    )


def _outer_trigger(page):
    return page.locator('[aria-controls="profile-dialog"]')


def test_trigger_opens_modal_places_focus_and_preserves_theme(page):
    _load(page)
    trigger = _outer_trigger(page)
    trigger.click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")
    dialog = page.locator("#profile-dialog")

    assert dialog.get_attribute("data-open") == ""
    assert dialog.get_attribute("aria-labelledby") == "profile-dialog-title"
    assert dialog.get_attribute("aria-describedby") == "profile-dialog-description"
    assert trigger.get_attribute("aria-expanded") == "true"
    assert page.locator("#profile-name").evaluate("element => element === document.activeElement") is True
    assert page.evaluate("document.documentElement.style.overflow") == "hidden"
    assert dialog.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(21, 43, 65)"
    assert dialog.evaluate("element => getComputedStyle(element).borderRadius") == "16px"
    assert (
        page.locator("#profile-dialog-title").evaluate("element => getComputedStyle(element).letterSpacing") == "2px"
    )
    assert page.evaluate("window.__dialogRequest") == {
        "nextOpen": True,
        "reason": "trigger",
        "controlled": False,
        "returnValue": "",
    }
    requests = page.evaluate("window.__dialogRequests")
    trigger.evaluate("element => element.click()")
    assert page.evaluate("window.__dialogRequests") == requests


def test_escape_and_explicit_action_restore_focus_and_release_scroll_lock(page):
    _load(page)
    trigger = _outer_trigger(page)
    trigger.click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")

    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#profile-dialog').open")
    assert page.evaluate("window.__dialogRequest.reason") == "escape"
    assert trigger.evaluate("element => element === document.activeElement") is True
    assert trigger.get_attribute("aria-expanded") == "false"
    assert page.evaluate("document.documentElement.style.overflow") == ""

    trigger.click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")
    page.get_by_role("button", name="Cancel").click()
    page.wait_for_function("!document.querySelector('#profile-dialog').open")
    assert page.evaluate("window.__dialogRequest.reason") == "action"
    assert trigger.evaluate("element => element === document.activeElement") is True


def test_tab_wrap_and_outside_pointer_policy(page):
    _load(page)
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")
    save = page.locator("#save-profile")
    close = page.locator(
        '#profile-dialog > [data-citry-ui-part="surface"] '
        '> [data-citry-ui-part="header"] > [data-citry-ui-part="close"]'
    )

    save.focus()
    page.keyboard.press("Tab")
    assert close.evaluate("element => element === document.activeElement") is True
    page.keyboard.press("Shift+Tab")
    assert save.evaluate("element => element === document.activeElement") is True

    box = page.locator('#profile-dialog > [data-citry-ui-part="surface"]').bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + 20, box["y"] + 20)
    page.mouse.down()
    page.mouse.move(2, 2)
    page.mouse.up()
    assert page.locator("#profile-dialog").evaluate("element => element.open") is True

    page.mouse.click(2, 2)
    page.wait_for_function("!document.querySelector('#profile-dialog').open")
    assert page.evaluate("window.__dialogRequest.reason") == "outside"


def test_reactive_configuration_updates_focus_size_and_scroll(page):
    _load(page)
    page.locator("#configure-title-focus").click()
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")

    dialog = page.locator("#profile-dialog")
    title = page.locator("#profile-dialog-title")
    assert dialog.get_attribute("data-size") == "lg"
    assert dialog.get_attribute("data-scroll") == "dialog"
    assert title.get_attribute("tabindex") == "-1"
    assert title.evaluate("element => element === document.activeElement") is True

    page.keyboard.press("Shift+Tab")
    assert page.locator("#save-profile").evaluate("element => element === document.activeElement") is True


def test_body_scroll_stays_reachable_without_optional_regions(page):
    _load(page)
    page.evaluate(
        """() => {
          document.querySelector('#profile-dialog-description').remove();
          document.querySelector('#profile-dialog [data-citry-ui-part="actions"]').remove();
          const dialog = document.querySelector('#profile-dialog');
          dialog.removeAttribute('aria-describedby');
          const body = dialog.querySelector('[data-citry-ui-part="body"]');
          body.replaceChildren(...Array.from({ length: 80 }, (_, index) => {
            const paragraph = document.createElement('p');
            paragraph.textContent = `Observation ${index + 1}`;
            return paragraph;
          }));
        }"""
    )
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")

    measurements = page.locator('#profile-dialog [data-citry-ui-part="body"]').evaluate(
        """element => ({
          clientHeight: element.clientHeight,
          scrollHeight: element.scrollHeight,
          overflowY: getComputedStyle(element).overflowY,
          dialogHeight: element.closest('dialog').getBoundingClientRect().height,
          viewportHeight: window.innerHeight,
        })"""
    )
    assert measurements["overflowY"] == "auto"
    assert measurements["scrollHeight"] > measurements["clientHeight"]
    assert measurements["dialogHeight"] <= measurements["viewportHeight"]

    page.locator('#profile-dialog [data-citry-ui-part="body"]').evaluate(
        "element => { element.scrollTop = element.scrollHeight; }"
    )
    assert page.locator('#profile-dialog [data-citry-ui-part="body"]').evaluate("element => element.scrollTop") > 0


def test_non_dismissible_dialog_requires_an_explicit_action(page):
    _load(page)
    page.locator("#disable-passive-dismissal").click()
    page.wait_for_function("document.querySelector('#profile-dialog [data-citry-dialog-built-in-close]').hidden")
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")

    close = page.locator(
        '#profile-dialog > [data-citry-ui-part="surface"] '
        '> [data-citry-ui-part="header"] > [data-citry-ui-part="close"]'
    )
    assert close.is_hidden()
    page.keyboard.press("Escape")
    assert page.locator("#profile-dialog").evaluate("element => element.open") is True

    page.get_by_role("button", name="Cancel").click()
    page.wait_for_function("!document.querySelector('#profile-dialog').open")
    assert page.evaluate("window.__dialogRequest.reason") == "action"


def test_controlled_owner_can_decline_then_accept_open_and_close_requests(page):
    _load(page, controlled=True)
    trigger = _outer_trigger(page)
    trigger.click()

    assert page.locator("#profile-dialog").evaluate("element => element.open") is False
    assert page.evaluate("window.__dialogRequest") == {
        "nextOpen": True,
        "reason": "trigger",
        "controlled": True,
        "returnValue": "",
    }

    page.locator("#accept-requests").click()
    trigger.click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#profile-dialog').open")
    assert page.evaluate("window.__dialogRequest.reason") == "escape"

    page.locator("#force-open").click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")
    requests = page.evaluate("window.__dialogRequests")
    page.evaluate("document.querySelector('#force-close').click()")
    page.wait_for_function("!document.querySelector('#profile-dialog').open")
    assert page.evaluate("window.__dialogRequests") == requests


def test_invalid_controlled_open_releases_ownership_from_current_state(page):
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    _load(page, controlled=True)
    page.locator("#invalidate-open").click()
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")

    assert page.evaluate("window.__dialogRequest") == {
        "nextOpen": True,
        "reason": "trigger",
        "controlled": False,
        "returnValue": "",
    }
    assert sum("CDialog open received invalid client value" in error for error in console_errors) == 1


def test_nested_dialogs_reference_count_scroll_lock_and_restore_focus(page):
    _load(page)
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")
    nested_trigger = page.locator('[aria-controls="nested-dialog"]')
    nested_trigger.click()
    page.wait_for_function("document.querySelector('#nested-dialog').open")

    assert page.evaluate("window[Symbol.for('citry-ui:dialog-runtime')].dialogs.length") == 2
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#nested-dialog').open")
    assert page.locator("#profile-dialog").evaluate("element => element.open") is True
    assert page.evaluate("document.documentElement.style.overflow") == "hidden"
    assert nested_trigger.evaluate("element => element === document.activeElement") is True

    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#profile-dialog').open")
    assert page.evaluate("window[Symbol.for('citry-ui:dialog-runtime')].dialogs.length") == 0
    assert page.evaluate("document.documentElement.style.overflow") == ""


def test_closing_parent_also_closes_nested_top_layer_dialog(page):
    _load(page, controlled=True)
    page.locator("#accept-requests").click()
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")
    page.locator('[aria-controls="nested-dialog"]').click()
    page.wait_for_function("document.querySelector('#nested-dialog').open")

    page.locator("#force-close").evaluate("element => element.click()")
    page.wait_for_function(
        """() => !document.querySelector('#profile-dialog').open
          && !document.querySelector('#nested-dialog').open
          && window[Symbol.for('citry-ui:dialog-runtime')].dialogs.length === 0"""
    )

    assert page.evaluate("document.documentElement.style.overflow") == ""


def test_nested_actions_belong_only_to_the_nearest_dialog(page):
    _load(page)
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")
    nested_trigger = page.locator('[aria-controls="nested-dialog"]')
    nested_trigger.click()
    page.wait_for_function("document.querySelector('#nested-dialog').open")

    page.get_by_role("button", name="Done").click()
    page.wait_for_function("!document.querySelector('#nested-dialog').open")

    assert page.locator("#profile-dialog").evaluate("element => element.open") is True
    assert page.evaluate("window.__dialogRequest.reason") == "trigger"
    assert nested_trigger.evaluate("element => element === document.activeElement") is True


def test_native_dialog_form_reports_return_value_and_restores_focus(page):
    _load(page)
    trigger = _outer_trigger(page)
    trigger.click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")

    page.locator("#native-result").click()
    page.wait_for_function("!document.querySelector('#profile-dialog').open")
    page.wait_for_function("window.__dialogRequest?.reason === 'native'")

    assert page.evaluate("window.__dialogRequest") == {
        "nextOpen": False,
        "reason": "native",
        "controlled": False,
        "returnValue": "charted",
    }
    assert trigger.evaluate("element => element === document.activeElement") is True


def test_controlled_native_form_close_can_be_declined_then_accepted(page):
    _load(page, controlled=True)
    page.locator("#force-open").click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")

    page.evaluate(
        """() => {
          const form = document.querySelector('#native-result').form;
          window.__preventDialogSubmit = (event) => event.preventDefault();
          form.addEventListener('submit', window.__preventDialogSubmit);
        }"""
    )
    page.locator("#native-result").click()
    assert page.locator("#profile-dialog").evaluate("element => element.open") is True
    assert page.evaluate("window.__dialogRequest") is None
    page.evaluate(
        """() => {
          const form = document.querySelector('#native-result').form;
          form.removeEventListener('submit', window.__preventDialogSubmit);
        }"""
    )

    page.locator("#native-result").click()
    assert page.locator("#profile-dialog").evaluate("element => element.open") is True
    assert page.evaluate("window.__dialogRequest") == {
        "nextOpen": False,
        "reason": "native",
        "controlled": True,
        "returnValue": "charted",
    }

    page.locator("#accept-requests").evaluate("element => element.click()")
    page.locator("#native-result").click()
    page.wait_for_function("!document.querySelector('#profile-dialog').open")
    assert page.evaluate("window.__dialogRequest.returnValue") == "charted"
    assert page.locator("#profile-dialog").evaluate("element => element.returnValue") == "charted"


def test_direct_native_close_does_not_reopen_from_stale_controlled_value(page):
    _load(page, controlled=True)
    page.locator("#force-open").click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")

    page.evaluate("document.querySelector('#profile-dialog').close('external')")
    page.wait_for_function("!document.querySelector('#profile-dialog').open")
    page.wait_for_function("window.__dialogRequest?.reason === 'native'")
    assert page.evaluate("window.__dialogRequest") == {
        "nextOpen": False,
        "reason": "native",
        "controlled": True,
        "returnValue": "external",
    }

    page.locator("#configure-title-focus").evaluate("element => element.click()")
    assert page.locator("#profile-dialog").evaluate("element => element.open") is False

    page.locator("#force-close").click()
    page.locator("#force-open").click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")


def test_removal_while_open_releases_document_state_and_component_resources(page):
    _load(page)
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#profile-dialog').open")
    page.evaluate(
        """() => {
          const host = document.querySelector('#profile-dialog').closest('[data-citry-dialog-host]');
          let start = host.previousSibling;
          while (start && !(start.nodeType === Node.COMMENT_NODE && start.data.endsWith(':s'))) {
            start = start.previousSibling;
          }
          let end = host.nextSibling;
          while (end && !(end.nodeType === Node.COMMENT_NODE && end.data.endsWith(':e'))) {
            end = end.nextSibling;
          }
          if (!start || !end) {
            throw new Error('Could not locate the dialog invocation range.');
          }
          const range = document.createRange();
          range.setStartBefore(start);
          range.setEndAfter(end);
          range.deleteContents();
        }"""
    )
    page.wait_for_function("window[Symbol.for('citry-ui:dialog-runtime')].dialogs.length === 0")

    assert page.evaluate("document.documentElement.style.overflow") == ""
    assert page.locator("#profile-dialog").count() == 0
