"""Focused browser contracts for CCommandPalette."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.ccommand_palette import CCommandPalette

pytestmark = pytest.mark.e2e


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-command-palette-e2e", (CCommandPalette,)))
    return app


def _page() -> str:
    app = _app()

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
                actions: [], opens: [], queries: [],
                controlledOpen: false, controlledQuery: '', controlledRequests: [],
                controlledCloseReasons: [],
                acceptOpen: false, acceptClose: false, acceptQuery: false,
                commands: [
                  {value: 'open-settings', label: 'Open settings', keywords: ['preferences'], disabled: false},
                  {value: 'deploy', label: 'Deploy production', keywords: ['release'], disabled: true},
                  {value: 'copy-id', label: 'Copy ID', keywords: ['identifier'], disabled: false}
                ]
              }"
            >
              <button id="before" type="button">Before</button>
              <c-CCommandPalette
                id="basic-palette"
                label="Workspace commands"
                c-entries="entries"
                $c-props="{
                  onAction: (value, detail) => actions.push({
                    value,
                    source: detail.source,
                    query: detail.query,
                    closeOnAction: detail.closeOnAction,
                  }),
                  onOpenChange: (value, detail) => opens.push({value, reason: detail.reason}),
                  onQueryChange: (value, detail) => queries.push({value, reason: detail.reason})
                }"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button id="trigger" type="button" c-bind="activator_attrs">
                    Open commands
                  </button>
                </c-fill>
              </c-CCommandPalette>
              <button id="owner-focus" type="button">Owner focus</button>
              <c-CCommandPalette
                id="controlled-palette"
                label="Controlled commands"
                c-entries="entries"
                $c-props="{
                  open: controlledOpen,
                  query: controlledQuery,
                  onOpenChange: (value, detail) => {
                    controlledRequests.push(['open', value, detail.reason]);
                    if ((value && acceptOpen) || (!value && acceptClose)) controlledOpen = value;
                  },
                  onQueryChange: (value, detail) => {
                    controlledRequests.push(['query', value, detail.reason]);
                    if (detail.reason === 'close') controlledCloseReasons.push(detail.closeReason);
                    if (acceptQuery || detail.reason === 'close') controlledQuery = value;
                  },
                  onAction: (value) => controlledRequests.push(['action', value]),
                }"
              >
                <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                  <button
                    id="controlled-trigger"
                    type="button"
                    c-disabled="activator_disabled"
                    c-bind="activator_attrs"
                  >Controlled</button>
                </c-fill>
              </c-CCommandPalette>
              <output id="ledger" x-text="JSON.stringify({actions, opens, queries})"></output>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            from citry_ui.components.ccommand_palette import (
                CCommandPaletteCommand,
                CCommandPaletteGroup,
                CCommandPaletteSeparator,
            )

            return {
                "entries": (
                    CCommandPaletteGroup(
                        "Navigation",
                        (
                            CCommandPaletteCommand(
                                "open-settings",
                                "Open settings",
                                keywords=("preferences",),
                            ),
                            CCommandPaletteCommand(
                                "deploy",
                                "Deploy production",
                                keywords=("release",),
                                disabled=True,
                            ),
                        ),
                    ),
                    CCommandPaletteSeparator(),
                    CCommandPaletteCommand(
                        "copy-id",
                        "Copy ID",
                        keywords=("identifier",),
                    ),
                )
            }

    return str(Page())


def _ready(page: Any) -> None:
    page.set_content(_page())
    page.wait_for_selector("[data-citry-command-palette-initialized]")


def test_open_filter_keyboard_action_and_close_reset(page: Any) -> None:
    _ready(page)
    page.locator("#trigger").focus()
    page.locator("#trigger").click()
    dialog = page.locator("#basic-palette")
    input_ = page.locator("#basic-palette-input")
    page.wait_for_function("() => document.querySelector('#basic-palette').matches(':modal')")
    assert input_.evaluate("element => element === document.activeElement")
    assert input_.get_attribute("aria-activedescendant")

    input_.fill("identifier")
    assert dialog.locator('[data-value="copy-id"]').is_visible()
    assert not dialog.locator('[data-value="open-settings"]').is_visible()
    input_.press("Enter")
    page.wait_for_function("() => !document.querySelector('#basic-palette').open")
    assert page.evaluate("() => document.body._x_dataStack[0].actions") == [
        {
            "value": "copy-id",
            "source": "keyboard",
            "query": "identifier",
            "closeOnAction": True,
        }
    ]
    assert page.evaluate("() => document.body._x_dataStack[0].queries.at(-1)") == {
        "value": "",
        "reason": "close",
    }
    assert page.locator("#trigger").evaluate("element => element === document.activeElement")
    assert not dialog.evaluate("element => element.open")


def test_disabled_navigation_click_refusal_and_escape(page: Any) -> None:
    _ready(page)
    page.locator("#trigger").click()
    input_ = page.locator("#basic-palette-input")
    input_.press("ArrowDown")
    active = input_.get_attribute("aria-activedescendant")
    dialog = page.locator("#basic-palette")
    assert active == dialog.locator('[data-value="copy-id"]').get_attribute("id")
    dialog.locator('[data-value="deploy"]').evaluate("element => element.click()")
    assert page.evaluate("() => document.body._x_dataStack[0].actions") == []
    input_.press("Escape")
    page.wait_for_function("() => !document.querySelector('#basic-palette').open")
    assert page.evaluate("() => document.body._x_dataStack[0].opens.at(-1).reason") == "escape"


def test_shared_helpers_transfer_shadow_focus_and_prepare_modal_in_order(page: Any) -> None:
    _ready(page)
    result = page.evaluate(
        """async () => {
          const dialogs = globalThis[Symbol.for('citry-ui:dialog-controller-runtime')];
          const anchored = globalThis[Symbol.for('citry-ui:anchored-layer-runtime')];
          const activeRuntime = globalThis[Symbol.for('citry-ui:active-descendant-runtime')];
          const makeDialog = (root, prefix) => {
            const host = document.createElement('span');
            host.innerHTML = `
              <dialog id="${prefix}-dialog">
                <section><h2>Title</h2><button type="button">Close</button>
                  <input id="${prefix}-input">
                </section>
              </dialog>`;
            root.append(host);
            const dialog = host.querySelector('dialog');
            const surface = dialog.querySelector('section');
            const title = dialog.querySelector('h2');
            const closeButton = dialog.querySelector('button');
            const input = dialog.querySelector('input');
            const options = {
              host, dialog, surface, title, closeButton,
              signature: 'focused-helper',
              policy: () => ({dismissible: true, closeOnEscape: true, closeOnOutside: true}),
              initialFocus: () => input,
              containmentFallback: () => input,
              escapeBlocked: () => false,
              interceptDialogSubmit: () => false,
              requestClose: () => {}, nativeClosed: () => {}, forceClose: () => {},
              failed: () => {}, handoffAborted: () => {},
            };
            return {host, dialog, input, options};
          };

          const source = document.createElement('button');
          source.textContent = 'Source';
          const ownerFocus = document.createElement('button');
          ownerFocus.textContent = 'Owner focus';
          document.body.append(source, ownerFocus);
          source.focus();
          const ordinary = makeDialog(document.body, 'ordinary');
          const first = dialogs.create(ordinary.options);
          first.setOpen(true, source);
          await new Promise(resolve => queueMicrotask(resolve));
          const focusedInitially = document.activeElement === ordinary.input;
          const second = dialogs.create(ordinary.options);
          const retainedOpen = ordinary.dialog.matches(':modal') && second.retained;
          first.cleanup();
          const staleCleanupPreserved = ordinary.dialog.matches(':modal');
          second.setOpen(false, ordinary.input);
          const retainedExpectedClose = !ordinary.dialog.open && !second.isOpen();
          ownerFocus.focus();
          await new Promise(resolve => queueMicrotask(resolve));
          const ownerFocusWon = document.activeElement === ownerFocus;
          second.cleanup();

          const nativeOwned = makeDialog(document.body, 'native-owned');
          const nativeCloses = [];
          nativeOwned.options.nativeClosed = (reason, _source, returnValue) => {
            nativeCloses.push([reason, returnValue]);
          };
          const nativeFirst = dialogs.create(nativeOwned.options);
          nativeFirst.setOpen(true, source);
          const nativeSecond = dialogs.create(nativeOwned.options);
          nativeFirst.cleanup();
          nativeOwned.dialog.close('external');
          await new Promise(resolve => setTimeout(resolve, 0));
          const retainedDirectNativeClose = !nativeOwned.dialog.open
            && !nativeSecond.isOpen()
            && JSON.stringify(nativeCloses) === JSON.stringify([['native', 'external']]);
          nativeSecond.cleanup();

          const shadowHost = document.createElement('div');
          document.body.append(shadowHost);
          const shadow = shadowHost.attachShadow({mode: 'open'});
          const shadowOwned = makeDialog(shadow, 'shadow');
          const shadowController = dialogs.create(shadowOwned.options);
          shadowController.setOpen(true, source);
          await new Promise(resolve => queueMicrotask(resolve));
          const shadowFocused = shadowOwned.dialog.matches(':modal')
            && shadow.activeElement === shadowOwned.input;
          shadowController.cleanup();

          const activeInput = document.createElement('input');
          const activeListbox = document.createElement('div');
          const activeGroup = document.createElement('section');
          const groupedOption = document.createElement('div');
          groupedOption.id = 'grouped-option';
          groupedOption.dataset.value = 'grouped';
          activeGroup.append(groupedOption);
          activeListbox.append(activeGroup);
          document.body.append(activeInput, activeListbox);
          const activeOptions = {
            input: activeInput,
            listbox: activeListbox,
            idPrefix: 'grouped-command',
          };
          const activeFirst = activeRuntime.create(activeOptions);
          const activeSecond = activeRuntime.create(activeOptions);
          activeFirst.cleanup();
          activeSecond.sync({
            items: [{value: 'grouped', disabled: false, visible: true}],
            activeValue: 'grouped',
            open: true,
            optionFor: value => value === 'grouped' ? groupedOption : null,
          });
          const activeStaleCleanupPreserved = activeSecond.retained
            && activeInput.getAttribute('aria-activedescendant') === 'grouped-option';
          activeSecond.cleanup();

          const layerTrigger = document.createElement('button');
          const layerSurface = document.createElement('div');
          document.body.append(layerTrigger, layerSurface);
          const coordinator = anchored.coordinatorFor(layerSurface);
          let layerOpen = true;
          let modalAtLayerClose = null;
          const layer = {
            trigger: layerTrigger,
            surface: layerSurface,
            isOpen: () => layerOpen,
            requestDismiss: () => {},
            forceClose: () => {
              modalAtLayerClose = ordinary.dialog.matches(':modal');
              layerOpen = false;
              coordinator.unregister(layer);
            },
          };
          coordinator.register(layer);
          const third = dialogs.create(ordinary.options);
          third.setOpen(true, source);
          const modalPrepared = layerOpen === false
            && modalAtLayerClose === false
            && ordinary.dialog.matches(':modal');
          third.cleanup();
          source.remove();
          ownerFocus.remove();
          shadowHost.remove();
          layerTrigger.remove();
          layerSurface.remove();
          activeInput.remove();
          activeListbox.remove();
          nativeOwned.host.remove();
          ordinary.host.remove();
          return {
            focusedInitially,
            retainedOpen,
            staleCleanupPreserved,
            retainedExpectedClose,
            ownerFocusWon,
            retainedDirectNativeClose,
            shadowFocused,
            activeStaleCleanupPreserved,
            modalPrepared,
            modalCount: dialogs.counts().modals,
          };
        }"""
    )
    assert result == {
        "focusedInitially": True,
        "retainedOpen": True,
        "staleCleanupPreserved": True,
        "retainedExpectedClose": True,
        "ownerFocusWon": True,
        "retainedDirectNativeClose": True,
        "shadowFocused": True,
        "activeStaleCleanupPreserved": True,
        "modalPrepared": True,
        "modalCount": 0,
    }


def test_controlled_open_query_decline_accept_and_close_reset(page: Any) -> None:
    _ready(page)
    state = "document.body._x_dataStack[0]"
    page.locator("#controlled-trigger").click()
    assert not page.locator("#controlled-palette").evaluate("element => element.open")
    assert page.evaluate(f"() => {state}.controlledRequests") == [["open", True, "trigger"]]

    page.evaluate(f"() => {state}.acceptOpen = true")
    page.locator("#controlled-trigger").click()
    page.wait_for_function("() => document.querySelector('#controlled-palette').matches(':modal')")
    controlled_input = page.locator("#controlled-palette-input")
    controlled_input.fill("identifier")
    assert controlled_input.input_value() == ""
    assert page.evaluate(f"() => {state}.controlledQuery") == ""

    page.evaluate(f"() => {state}.acceptQuery = true")
    controlled_input.fill("identifier")
    assert controlled_input.input_value() == "identifier"
    assert page.evaluate(f"() => {state}.controlledQuery") == "identifier"

    controlled_input.press("Escape")
    assert page.locator("#controlled-palette").evaluate("element => element.open")
    assert controlled_input.input_value() == "identifier"

    page.evaluate(f"() => {state}.acceptClose = true")
    controlled_input.press("Escape")
    page.wait_for_function("() => !document.querySelector('#controlled-palette').open")
    assert page.evaluate(f"() => {state}.controlledQuery") == ""
    assert page.evaluate(f"() => {state}.controlledRequests.slice(-2)") == [
        ["open", False, "escape"],
        ["query", "", "close"],
    ]
    assert page.evaluate(f"() => {state}.controlledCloseReasons") == ["escape"]


def test_declined_controlled_close_does_not_label_later_owner_close(page: Any) -> None:
    _ready(page)
    state = "document.body._x_dataStack[0]"
    page.evaluate(f"() => {{ {state}.acceptOpen = true; {state}.acceptQuery = true; }}")
    page.locator("#controlled-trigger").click()
    page.wait_for_function("() => document.querySelector('#controlled-palette').matches(':modal')")
    controlled_input = page.locator("#controlled-palette-input")
    controlled_input.fill("identifier")
    controlled_input.press("Escape")
    assert page.locator("#controlled-palette").evaluate("element => element.open")

    page.evaluate(f"() => {state}.controlledOpen = false")
    page.wait_for_function("() => !document.querySelector('#controlled-palette').open")
    assert page.evaluate(f"() => {state}.controlledCloseReasons") == ["owner"]


def test_document_open_shadow_root_move_refreshes_scope_and_closes_modal(page: Any) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    _ready(page)
    page.locator("#trigger").click()
    page.wait_for_function("() => document.querySelector('#basic-palette').matches(':modal')")
    result = page.evaluate(
        """async () => {
          const dialog = document.querySelector('#basic-palette');
          const host = dialog.parentElement;
          const before = host.nextSibling;
          const shadowHost = document.createElement('div');
          document.body.append(shadowHost);
          const shadow = shadowHost.attachShadow({mode:'open'});
          shadow.append(host);
          await new Promise(resolve => setTimeout(resolve, 0));
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          const moved = {
            ready: host.hasAttribute('data-citry-command-palette-initialized'),
            closed: !dialog.open,
            root: host.getRootNode() === shadow,
          };
          document.body.insertBefore(host, before);
          await new Promise(resolve => setTimeout(resolve, 0));
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          const restored = {
            ready: host.hasAttribute('data-citry-command-palette-initialized'),
            closed: !dialog.open,
            root: host.getRootNode() === document,
          };
          shadowHost.remove();
          return {
            moved,
            restored,
            modals: globalThis[Symbol.for('citry-ui:dialog-controller-runtime')].counts().modals,
          };
        }"""
    )
    assert result == {
        "moved": {"ready": True, "closed": True, "root": True},
        "restored": {"ready": True, "closed": True, "root": True},
        "modals": 0,
    }
    assert errors == []


def test_hostile_owned_mutation_fails_closed_and_removal_cleans_resources(page: Any) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    _ready(page)
    page.locator("#trigger").click()
    page.wait_for_function("() => document.querySelector('#basic-palette').matches(':modal')")
    page.locator("#basic-palette-input").evaluate("element => element.setAttribute('data-citry-forged', '')")
    page.wait_for_function(
        "() => !document.querySelector('#basic-palette').parentElement"
        ".hasAttribute('data-citry-command-palette-initialized')"
    )
    assert not page.locator("#basic-palette").evaluate("element => element.open")
    assert errors == ["[citry-ui] CCommandPalette lost its owned anatomy; component behavior was removed."]

    before = page.evaluate("() => globalThis[Symbol.for('citry-ui:dialog-controller-runtime')].counts().modals")
    page.locator("#controlled-palette").evaluate("element => element.parentElement.remove()")
    page.wait_for_timeout(50)
    after = page.evaluate("() => globalThis[Symbol.for('citry-ui:dialog-controller-runtime')].counts().modals")
    assert before == after == 0
    assert len(errors) == 1
