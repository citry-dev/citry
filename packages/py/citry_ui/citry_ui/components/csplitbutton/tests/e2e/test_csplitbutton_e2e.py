"""Focused browser contracts for CSplitButton."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cmenu import CMenuItem
from citry_ui.components.cmenu.cmenu import CInternalMenuCollection, CInternalMenuSurface
from citry_ui.components.csplitbutton import CSplitButton

pytestmark = pytest.mark.e2e

_COMPONENTS = (CSplitButton, CMenuItem, CInternalMenuCollection, CInternalMenuSurface)


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the SplitButton e2e test path."
    raise RuntimeError(msg)


def _split_button_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-split-button-e2e", _COMPONENTS))

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <title>Split Button browser contract</title>
              <script>
                window.__splitEvents = [];
                window.__submitCount = 0;
                window.__resetCount = 0;
              </script>
              <c-css />
            </head>
            <body
              x-data="{
                acceptControlled: false,
                controlledOpen: false,
                submitLoading: false,
                commonDisabled: false,
              }"
            >
              <form
                id="record-form"
                @submit.prevent="
                  window.__submitCount += 1;
                  window.__splitEvents.push([
                    'submit',
                    $event.submitter?.id,
                    new FormData($event.currentTarget, $event.submitter).get('action'),
                  ]);
                "
                @reset="
                  window.__resetCount += 1;
                  window.__splitEvents.push([
                    'reset-event', document.querySelector('#record-title').value,
                  ]);
                "
              >
                <input id="record-title" name="title" value="Original" required />
                <c-CSplitButton
                  id="submit-split"
                  label="Save actions"
                  menu_label="More save actions"
                  type="submit"
                  c-primary_attrs="submit_attrs"
                  $c-props="{
                    loading: submitLoading,
                    disabled: commonDisabled,
                    onOpenChange: (nextOpen, detail) => {
                      window.__splitEvents.push([
                        'open',
                        'submit-split',
                        nextOpen,
                        detail.reason,
                        detail.controlled,
                        document.querySelector('#record-title').value,
                      ]);
                      if (window.__removeSubmitOnAction && detail.reason === 'action') {
                        document.querySelector('#submit-split')?.remove();
                      }
                    },
                    onAction: (value, detail) => {
                      window.__splitEvents.push(['menu-action', value, detail.kind]);
                    },
                  }"
                >
                  <c-fill name="default">Save record</c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="copy">Save a copy</c-CMenuItem>
                    <c-CMenuItem value="export">Export</c-CMenuItem>
                  </c-fill>
                </c-CSplitButton>
                <c-CSplitButton
                  id="reset-split"
                  label="Reset actions"
                  menu_label="More reset actions"
                  type="reset"
                  c-primary_attrs="reset_attrs"
                  $c-props="{
                    onOpenChange: (nextOpen, detail) => window.__splitEvents.push([
                      'open',
                      'reset-split',
                      nextOpen,
                      detail.reason,
                      detail.controlled,
                      document.querySelector('#record-title').value,
                    ]),
                  }"
                >
                  <c-fill name="default">Reset record</c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="clear-notes">Clear notes</c-CMenuItem>
                  </c-fill>
                </c-CSplitButton>
              </form>

              <c-CSplitButton
                id="controlled-split"
                label="Publication actions"
                menu_label="More publication actions"
                open
                $c-props="{
                  open: controlledOpen,
                  onOpenChange: (nextOpen, detail) => {
                    window.__splitEvents.push([
                      'controlled', nextOpen, detail.reason, detail.controlled,
                    ]);
                    if (acceptControlled) controlledOpen = nextOpen;
                  },
                }"
              >
                <c-fill name="default">Publish</c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="preview">Preview</c-CMenuItem>
                </c-fill>
              </c-CSplitButton>
              <button id="accept-controlled" type="button" @click="acceptControlled = true">
                Accept controlled requests
              </button>
              <button id="show-controlled" type="button" @click="controlledOpen = true">
                Show controlled Menu
              </button>
              <button id="toggle-loading" type="button" @click="submitLoading = !submitLoading">
                Toggle loading
              </button>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "submit_attrs": {
                    "name": "action",
                    "value": "save",
                    "@click.capture": (
                        "window.__splitEvents.push(['primary-capture-consumer', "
                        "document.querySelector('#submit-split').hasAttribute('data-open')])"
                    ),
                    "@click": "window.__splitEvents.push(['primary-target'])",
                },
                "reset_attrs": {
                    "@click": "window.__splitEvents.push(['reset-target'])",
                },
            }

    return str(Page())


def _load(page) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.set_content(_split_button_page(), wait_until="load")
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="split-button"]')]
          .every(root => root.hasAttribute('data-citry-split-button-initialized'))"""
    )
    return errors


def _open(page, root_id: str) -> None:
    page.locator(f"#{root_id} [data-citry-ui-part='split-button-menu-trigger']").click()
    page.wait_for_function("id => document.querySelector(`#${id}`).hasAttribute('data-open')", arg=root_id)


def test_uncontrolled_primary_action_closes_before_native_submit_and_notifies_once_afterward(page):
    errors = _load(page)
    _open(page, "submit-split")
    page.evaluate("window.__splitEvents = []")
    page.locator("#submit-split-primary").click()
    page.wait_for_function(
        """() => window.__splitEvents.some(
          event => event[0] === 'open' && event[1] === 'submit-split' && event[3] === 'action'
        )"""
    )

    assert page.evaluate("window.__splitEvents") == [
        ["primary-capture-consumer", False],
        ["primary-target"],
        ["submit", "submit-split-primary", "save"],
        ["open", "submit-split", False, "action", False, "Original"],
    ]
    assert page.evaluate("window.__submitCount") == 1
    assert page.locator("#submit-split").get_attribute("data-open") is None
    assert errors == []


def test_controlled_menu_refuses_then_accepts_trigger_and_deferred_primary_requests(page):
    errors = _load(page)
    trigger = page.locator("#controlled-split-menu-trigger")
    trigger.click()
    page.wait_for_function("window.__splitEvents.length === 1")
    assert page.locator("#controlled-split").get_attribute("data-open") is None

    page.locator("#accept-controlled").click()
    trigger.click()
    page.wait_for_function("document.querySelector('#controlled-split').hasAttribute('data-open')")
    page.locator("#controlled-split-primary").click()
    page.wait_for_function("!document.querySelector('#controlled-split').hasAttribute('data-open')")

    controlled = page.evaluate("window.__splitEvents.filter(event => event[0] === 'controlled')")
    assert controlled == [
        ["controlled", True, "trigger", True],
        ["controlled", True, "trigger", True],
        ["controlled", False, "action", True],
    ]
    assert errors == []


def test_request_submit_validation_loading_guard_and_click_token_dedupe(page):
    errors = _load(page)
    form = page.locator("#record-form")
    primary = page.locator("#submit-split-primary")
    title = page.locator("#record-title")

    title.fill("")
    _open(page, "submit-split")
    page.evaluate(
        "document.querySelector('#record-form').requestSubmit(document.querySelector('#submit-split-primary'))"
    )
    assert page.evaluate("window.__submitCount") == 0
    assert page.locator("#submit-split").get_attribute("data-open") == ""

    title.fill("Accepted")
    page.evaluate("Alpine.$data(document.body).submitLoading = true")
    page.wait_for_function("document.querySelector('#submit-split-primary').hasAttribute('data-loading')")
    page.evaluate(
        "document.querySelector('#record-form').requestSubmit(document.querySelector('#submit-split-primary'))"
    )
    assert page.evaluate("window.__submitCount") == 0
    assert page.locator("#submit-split").get_attribute("data-open") == ""

    page.evaluate("Alpine.$data(document.body).submitLoading = false")
    page.wait_for_function("!document.querySelector('#submit-split-primary').hasAttribute('data-loading')")
    page.evaluate(
        "document.querySelector('#record-form').requestSubmit(document.querySelector('#submit-split-primary'))"
    )
    page.wait_for_function("window.__submitCount === 1")
    page.wait_for_function("!document.querySelector('#submit-split').hasAttribute('data-open')")
    action_notices = page.evaluate(
        "window.__splitEvents.filter(event => event[0] === 'open' && event[3] === 'action').length"
    )
    assert action_notices == 1
    assert form.is_visible()
    assert primary.is_visible()
    assert errors == []


def test_reset_finishes_before_notice_and_notice_callback_removal_cannot_cancel_submit(page):
    errors = _load(page)
    title = page.locator("#record-title")
    title.fill("Changed")
    _open(page, "reset-split")
    page.evaluate("window.__splitEvents = []")
    page.locator("#reset-split-primary").click()
    page.wait_for_function("window.__splitEvents.some(event => event[0] === 'open' && event[1] === 'reset-split')")
    assert title.input_value() == "Original"
    reset_events = page.evaluate(
        "window.__splitEvents.filter(event => ['reset-target', 'reset-event', 'open'].includes(event[0]))"
    )
    assert reset_events == [
        ["reset-target"],
        ["reset-event", "Changed"],
        ["open", "reset-split", False, "action", False, "Original"],
    ]

    page.evaluate("window.__splitEvents = []; window.__removeSubmitOnAction = true")
    _open(page, "submit-split")
    page.locator("#submit-split-primary").click()
    page.wait_for_function("!document.querySelector('#submit-split')")
    assert page.evaluate("window.__submitCount") == 1
    assert errors == []


def test_owned_identity_parts_and_readiness_repair_after_hostile_mutation(page):
    errors = _load(page)
    page.evaluate(
        """() => {
          const root = document.querySelector('#submit-split');
          root.id = 'hostile-root';
          root.setAttribute('role', 'toolbar');
          root.setAttribute('aria-label', 'Hostile');
          root.dataset.citryUiPart = 'hostile';
          root.querySelector('[data-citry-ui-part="split-button-menu-trigger"]').type = 'submit';
          root.querySelector('[data-citry-ui-part="menu"]').id = 'hostile-menu';
        }"""
    )
    page.wait_for_function(
        """() => {
          const root = document.querySelector('#submit-split');
          return root?.getAttribute('role') === 'group'
            && root.getAttribute('aria-label') === 'Save actions'
            && root.dataset.citryUiPart === 'split-button'
            && root.querySelector('#submit-split-menu-trigger')?.type === 'button'
            && root.querySelector('#submit-split-menu');
        }"""
    )
    assert page.locator("#submit-split").get_attribute("data-citry-split-button-initialized") == ""
    assert len(errors) <= 2
    assert all(error.startswith("[citry-ui] CSplitButton") for error in errors)

    page.evaluate(
        """() => {
          const forbidden = document.createElement('button');
          forbidden.id = 'forbidden-menu-content';
          document.querySelector(
            '#submit-split [data-citry-ui-part="menu-item-label"]',
          ).append(forbidden);
        }"""
    )
    page.wait_for_function(
        """() => {
          const root = document.querySelector('#submit-split');
          return !root.hasAttribute('data-citry-split-button-initialized')
            && !root.querySelector('[data-citry-ui-part="menu"]')
              .hasAttribute('data-citry-menu-initialized');
        }"""
    )
    page.evaluate("document.querySelector('#forbidden-menu-content').remove()")
    page.wait_for_function(
        """() => {
          const root = document.querySelector('#submit-split');
          return root.hasAttribute('data-citry-split-button-initialized')
            && root.querySelector('[data-citry-ui-part="menu"]')
              .hasAttribute('data-citry-menu-initialized');
        }"""
    )


def test_submit_registry_transfers_to_open_shadow_root_and_cleans_up_last_scope(page):
    errors = _load(page)
    baseline = page.evaluate("""() => ({...globalThis[Symbol.for('citry-ui:split-button-submit-runtime')].stats})""")
    page.evaluate(
        """() => {
          const host = document.createElement('div');
          host.id = 'shadow-host';
          document.body.append(host);
          const shadow = host.attachShadow({mode: 'open'});
          const form = document.querySelector('#record-form');
          shadow.append(form);
          form.addEventListener('submit', event => {
            event.preventDefault();
            event.stopImmediatePropagation();
            window.__submitCount += 1;
          }, {capture: true, once: true});
          window.__splitShadow = shadow;
        }"""
    )
    page.wait_for_function(
        """() => globalThis[Symbol.for('citry-ui:split-button-submit-runtime')].stats.scopes === 1"""
    )
    page.evaluate(
        """() => {
          const form = window.__splitShadow.querySelector('#record-form');
          form.requestSubmit(window.__splitShadow.querySelector('#submit-split-primary'));
        }"""
    )
    page.wait_for_function("window.__submitCount === 1")
    page.evaluate("document.querySelector('#shadow-host').remove()")
    page.wait_for_function(
        """() => globalThis[Symbol.for('citry-ui:split-button-submit-runtime')].stats.registrations === 0"""
    )
    final_stats = page.evaluate(
        """() => ({...globalThis[Symbol.for('citry-ui:split-button-submit-runtime')].stats})"""
    )
    assert baseline == {"scopes": 1, "registrations": 1}
    assert final_stats == {"scopes": 0, "registrations": 0}
    assert errors == []


def test_full_group_is_anchor_and_inside_element_for_layer_dismissal(page):
    errors = _load(page)
    _open(page, "submit-split")
    values = page.locator("#submit-split").evaluate(
        """root => {
          const surface = root.querySelector('[data-citry-ui-part="menu"]');
          root.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, composed: true}));
          root.dispatchEvent(new MouseEvent('click', {bubbles: true, composed: true}));
          return {
            anchorName: getComputedStyle(root).getPropertyValue('anchor-name'),
            positionAnchor: getComputedStyle(surface).positionAnchor,
            open: root.hasAttribute('data-open'),
          };
        }"""
    )
    assert values["anchorName"].startswith("--_cui-menu-anchor-ref-")
    assert values["positionAnchor"] == values["anchorName"]
    assert values["open"] is True
    assert errors == []
