"""Focused browser contracts for CCommandPalette."""

# ruff: noqa: E501 - embedded Vue expressions remain readable in browser fixtures

from __future__ import annotations

import importlib
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import expect

from citry import Citry, Component, ComponentLibrary
from citry import citry as default_citry
from citry_ui.components.ccommand_palette import CCommandPalette, CCommandPaletteCommand

pytestmark = pytest.mark.e2e


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-command-palette-e2e", (CCommandPalette,)))
    return app


def _page() -> str:
    app = _app()

    class Page(Component):
        citry = app
        js = """$component({data(){const state=Citry.vue.reactive({actions:[],opens:[],queries:[],controlledOpen:false,controlledQuery:'',controlledRequests:[],controlledCloseReasons:[],acceptOpen:false,acceptClose:false,acceptQuery:false,showBasic:true,commands:[{value:'open-settings',label:'Open settings',keywords:['preferences'],disabled:false},{value:'deploy',label:'Deploy production',keywords:['release'],disabled:true},{value:'copy-id',label:'Copy ID',keywords:['identifier'],disabled:false}]});window.__commandPalette=state;return state;}});"""
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <button id="before" type="button">Before</button>
              <template v-if="showBasic">
              <c-CCommandPalette
                id="basic-palette"
                label="Workspace commands"
                c-entries="entries"
                :onAction="(value, detail) => actions.push({
                    value,
                    source: detail.source,
                    query: detail.query,
                    closeOnAction: detail.closeOnAction,
                  })"
                :onOpenChange="(value, detail) => opens.push({value, reason: detail.reason})"
                :onQueryChange="(value, detail) => queries.push({value, reason: detail.reason})"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button id="trigger" type="button" c-bind="activator_attrs">
                    Open commands
                  </button>
                </c-fill>
              </c-CCommandPalette>
              </template>
              <button id="remove-basic" type="button" @click="showBasic = false">Remove</button>
              <button id="owner-focus" type="button">Owner focus</button>
              <c-CCommandPalette
                id="controlled-palette"
                label="Controlled commands"
                c-entries="entries"
                :open="controlledOpen"
                :query="controlledQuery"
                :onOpenChange="(value, detail) => {
                    controlledRequests.push(['open', value, detail.reason]);
                    if ((value && acceptOpen) || (!value && acceptClose)) controlledOpen = value;
                  }"
                :onQueryChange="(value, detail) => {
                    controlledRequests.push(['query', value, detail.reason]);
                    if (detail.reason === 'close') controlledCloseReasons.push(detail.closeReason);
                    if (acceptQuery || detail.reason === 'close') controlledQuery = value;
                  }"
                :onAction="(value) => controlledRequests.push(['action', value])"
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
              <output id="ledger" :textContent="JSON.stringify({actions, opens, queries})"></output>
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
    # The page holds the basic and the controlled palette, and each one
    # initializes in its own callback, so wait for both.
    page.wait_for_function("document.querySelectorAll('[data-citry-command-palette-initialized]').length === 2")


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
    assert page.evaluate("() => window.__commandPalette.actions") == [
        {
            "value": "copy-id",
            "source": "keyboard",
            "query": "identifier",
            "closeOnAction": True,
        }
    ]
    assert page.evaluate("() => window.__commandPalette.queries.at(-1)") == {
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
    assert page.evaluate("() => window.__commandPalette.actions") == []
    input_.press("Escape")
    page.wait_for_function("() => !document.querySelector('#basic-palette').open")
    assert page.evaluate("() => window.__commandPalette.opens.at(-1).reason") == "escape"


def test_shared_helpers_transfer_shadow_focus_and_prepare_modal_in_order(page: Any) -> None:
    _ready(page)
    result = page.wait_for_function(
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
          // Hold a real queued event so frame timing cannot hide an obsolete native close.
          const nativeAddListener = nativeOwned.dialog.addEventListener.bind(nativeOwned.dialog);
          const nativeRemoveListener = nativeOwned.dialog.removeEventListener.bind(nativeOwned.dialog);
          const closeListeners = new Map();
          const pausedCloses = [];
          let holdNativeCloses = true;
          nativeOwned.dialog.addEventListener = (type, listener, options) => {
            if (type !== 'close') return nativeAddListener(type, listener, options);
            const forward = event => {
              const deliver = () => listener.call(nativeOwned.dialog, event);
              if (holdNativeCloses) pausedCloses.push(deliver);
              else deliver();
            };
            closeListeners.set(listener, forward);
            nativeAddListener(type, forward, options);
          };
          nativeOwned.dialog.removeEventListener = (type, listener, options) => {
            nativeRemoveListener(type, closeListeners.get(listener) ?? listener, options);
          };
          const staleCloseObserved = new Promise(resolve => {
            nativeAddListener('close', resolve, {once: true});
          });
          const nativeFirst = dialogs.create(nativeOwned.options);
          nativeFirst.setOpen(true, source);
          nativeOwned.dialog.close('obsolete');
          const nativeSecond = dialogs.create(nativeOwned.options);
          nativeFirst.cleanup();
          nativeSecond.setOpen(true, source);
          await staleCloseObserved;
          for (let frame = 0; frame < 3; frame++) {
            await new Promise(resolve => requestAnimationFrame(resolve));
          }
          const deferredCurrentOwnerClose = pausedCloses.length === 1 && nativeSecond.retained;
          pausedCloses.splice(0).forEach(deliver => deliver());
          const retainedLatestOpen = nativeOwned.dialog.matches(':modal')
            && nativeSecond.isOpen()
            && nativeCloses.length === 0;
          holdNativeCloses = false;
          const nativeCloseObserved = new Promise(resolve => {
            nativeOwned.dialog.addEventListener('close', resolve, {once: true});
          });
          nativeOwned.dialog.close('external');
          await nativeCloseObserved;
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
            deferredCurrentOwnerClose,
            retainedLatestOpen,
            retainedDirectNativeClose,
            shadowFocused,
            activeStaleCleanupPreserved,
            modalPrepared,
            modalCount: dialogs.counts().modals,
          };
        }""",
        timeout=10_000,
    ).json_value()
    assert result == {
        "focusedInitially": True,
        "retainedOpen": True,
        "staleCleanupPreserved": True,
        "retainedExpectedClose": True,
        "ownerFocusWon": True,
        "deferredCurrentOwnerClose": True,
        "retainedLatestOpen": True,
        "retainedDirectNativeClose": True,
        "shadowFocused": True,
        "activeStaleCleanupPreserved": True,
        "modalPrepared": True,
        "modalCount": 0,
    }, result


def test_controlled_open_query_decline_accept_and_close_reset(page: Any) -> None:
    _ready(page)
    state = "window.__commandPalette"
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
    state = "window.__commandPalette"
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
          const owner = host.parentNode;
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
          owner.insertBefore(host, before);
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


def test_vue_unmount_while_open_releases_the_modal_at_once(page: Any) -> None:
    _ready(page)
    page.locator("#trigger").click()
    page.wait_for_function("() => document.querySelector('#basic-palette').matches(':modal')")
    # The open modal blocks pointer input to the page, so click the button
    # directly. Vue then unmounts the palette in its next render.
    page.locator("#remove-basic").evaluate("element => element.click()")
    # The handoff timer would release the modal after one second; an unmount
    # has no next render to adopt it, so the release must come well before.
    page.wait_for_function(
        "() => !document.querySelector('#basic-palette')"
        " && globalThis[Symbol.for('citry-ui:dialog-controller-runtime')].counts().modals === 0",
        timeout=300,
    )
    assert page.evaluate("document.documentElement.style.overflow") == ""


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


class CommandPalettePreviewDocument(Component):
    citry = default_citry

    class Kwargs:
        content: object

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, _slots: Slots) -> dict[str, object]:
        return {"content": kwargs.content}

    template = """
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>CommandPalette snippet</title>
          <c-css />
        </head>
        <body>
          <main>{{ content }}</main>
          <c-js />
        </body>
      </html>
    """


def _open_snippet(page: Any, serve_citry_ui_live: Any, name: str) -> list[str]:
    # Snippets register Citry UI on the default instance when imported, so the
    # docs preview and this test render the same component.
    module = importlib.import_module(f"citry_ui.components.ccommand_palette.snippets.{name}")
    html = CommandPalettePreviewDocument(content=module.preview).render().serialize()
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(serve_citry_ui_live(default_citry, html) + "/", wait_until="networkidle")
    page.wait_for_selector("[data-citry-command-palette-initialized]")
    return errors


def _set_inert_box(page: Any, label: str, *, checked: bool = True) -> None:
    # The open modal palette makes the owner's checkbox inert, so change it
    # the way its v-model listens: set the native state and fire `change`.
    page.get_by_label(label).evaluate(
        "(element, checked) => {"
        " element.checked = checked;"
        " element.dispatchEvent(new Event('change', {bubbles: true}));"
        " }",
        checked,
    )


def _count_focus_calls(page: Any, selector: str) -> None:
    # The open modal palette makes the owner's button inert, so its focus()
    # call cannot move focus. Count the calls to prove the owner made one.
    page.locator(selector).evaluate(
        """element => {
          window.__ownerFocusCalls = 0;
          element.focus = function (...args) {
            window.__ownerFocusCalls += 1;
            return HTMLElement.prototype.focus.apply(this, args);
          };
        }"""
    )


def _wait_for_scenario_palettes(page: Any) -> None:
    page.wait_for_function(
        "['#quality-command-palette-lifecycle', '#quality-command-palette-actions'].every(id => "
        "document.querySelector(id)?.closest('[data-citry-command-palette-initialized]'))"
    )


def test_quality_lifecycle_palette_counts_each_open_and_query_request(page: Any, open_scenario: Any) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    open_scenario("command-palette.states")
    _wait_for_scenario_palettes(page)
    # The spans read: open state, query, actions, query requests, open requests.
    counters = page.locator("#quality-command-palette-lifecycle-output span")

    page.get_by_role("button", name="Open lifecycle palette").click()
    page.wait_for_function("document.querySelector('#quality-command-palette-lifecycle').open")
    lifecycle_input = page.locator('#quality-command-palette-lifecycle [data-citry-ui-part="command-palette-input"]')
    lifecycle_input.fill("settings")
    expect(counters).to_have_text(["open", "settings", "0", "1", "0"])

    lifecycle_input.press("Escape")
    page.wait_for_function("!document.querySelector('#quality-command-palette-lifecycle').open")
    # Closing also clears the query, which is the second query request.
    expect(counters).to_have_text(["closed", "empty", "0", "2", "1"])
    assert errors == []


def test_quality_controlled_palette_takes_the_close_reset_while_declining_query_edits(
    page: Any,
    open_scenario: Any,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    open_scenario("command-palette.states")
    _wait_for_scenario_palettes(page)
    palette = page.locator("#quality-command-palette-controlled")
    palette_input = palette.locator('[data-citry-ui-part="command-palette-input"]')
    # The spans read: open state, query.
    owner = page.locator("#quality-command-palette-controlled-output span")

    page.get_by_role("button", name="Restore controlled open").click()
    page.wait_for_function("document.querySelector('#quality-command-palette-controlled').open")
    palette_input.fill("rejected")
    expect(palette_input).to_have_value("open")
    expect(owner).to_have_text(["open", "open"])

    _set_inert_box(page, "Accept close")
    palette.locator('[data-citry-ui-part="command-palette-close"]').click()
    page.wait_for_function("!document.querySelector('#quality-command-palette-controlled').open")
    # The owner still declines query edits but takes the close's empty query.
    expect(owner).to_have_text(["closed", ""])
    assert errors == []


def test_quality_action_palette_logs_each_action_and_asks_the_owner_to_take_focus(
    page: Any,
    open_scenario: Any,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    open_scenario("command-palette.states")
    _wait_for_scenario_palettes(page)
    _count_focus_calls(page, "#quality-command-palette-owner-focus")
    palette = page.locator("#quality-command-palette-actions")
    palette_input = palette.locator('[data-citry-ui-part="command-palette-input"]')
    output = page.locator("#quality-command-palette-action-output")

    page.get_by_role("button", name="Restore action palette").click()
    page.wait_for_function("document.querySelector('#quality-command-palette-actions').open")
    palette_input.fill("copy draft")
    palette_input.press("Enter")
    expect(output).to_have_text("action:copy-id:keyboard:false")
    assert palette.evaluate("element => element.open") is True
    assert page.evaluate("window.__ownerFocusCalls") == 1

    palette_input.fill("create project")
    palette_input.press("Enter")
    # A closing command asks for the close first, then runs onAction.
    expect(output).to_have_text("action:copy-id:keyboard:false|open:false:action|action:create-project:keyboard:true")
    assert palette.evaluate("element => element.open") is False
    # Only the copy command asks the owner to take focus.
    assert page.evaluate("window.__ownerFocusCalls") == 1
    assert errors == []


def test_command_actions_snippet_logs_actions_moves_focus_and_reports_a_throw(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_snippet(page, serve_citry_ui_live, "command_actions")
    _count_focus_calls(page, "#command-action-focus-target")
    palette = page.locator("dialog")
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')
    output = page.locator("output[aria-live=polite]")

    palette_input.fill("copy")
    palette_input.press("Enter")
    expect(output).to_have_text("query:copy:input | action:copy-id:keyboard:false")
    assert page.evaluate("window.__ownerFocusCalls") == 0

    _set_inert_box(page, "Move owner focus")
    palette_input.press("Enter")
    expect(output).to_have_text("query:copy:input | action:copy-id:keyboard:false | action:copy-id:keyboard:false")
    assert page.evaluate("window.__ownerFocusCalls") == 1

    _set_inert_box(page, "Throw in next action")
    palette_input.press("Enter")
    page.wait_for_function("window.__ownerFocusCalls === 2")
    # The owner logs the action and clears the checkbox before it throws, so
    # only one action fails.
    expect(page.get_by_label("Throw in next action")).not_to_be_checked()
    expect(output).to_have_text(
        "query:copy:input | action:copy-id:keyboard:false"
        " | action:copy-id:keyboard:false | action:copy-id:keyboard:false"
    )
    assert palette.evaluate("element => element.open") is True
    assert errors == ["Application action failed"]


def test_controlled_snippet_declines_requests_until_the_owner_accepts_them(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_snippet(page, serve_citry_ui_live, "controlled_command_palette")
    palette = page.locator("dialog")
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')
    owner = page.locator("output[aria-live=polite]")
    expect(owner).to_have_text("Owner: open; query: work; requests: none")

    palette_input.fill("alpha")
    expect(owner).to_have_text("Owner: open; query: work; requests: query:alpha:input")
    assert palette_input.input_value() == "work"
    palette_input.press("Escape")
    expect(owner).to_have_text("Owner: open; query: work; requests: query:alpha:input | open:false:escape")
    assert palette.evaluate("element => element.open") is True

    _set_inert_box(page, "Accept query edits")
    palette_input.fill("bravo")
    expect(owner).to_have_text(
        "Owner: open; query: bravo; requests: query:alpha:input | open:false:escape | query:bravo:input"
    )
    # Turn query edits back off, so the close below shows the owner taking
    # the empty query that comes with a close even while it declines edits.
    _set_inert_box(page, "Accept query edits", checked=False)
    _set_inert_box(page, "Accept close")
    palette_input.press("Escape")
    # Closing sends an empty query with reason `close`.
    expect(owner).to_have_text(
        "Owner: closed; query: empty; requests: query:bravo:input | open:false:escape | query::close"
    )
    assert palette.evaluate("element => element.open") is False
    assert errors == []


def test_disabled_snippet_shortcuts_run_enabled_commands_only(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open_snippet(page, serve_citry_ui_live, "disabled_and_shortcuts")
    output = page.locator("output[aria-live=polite]")

    page.keyboard.press("Alt+Shift+KeyV")
    expect(output).to_have_text("Action: view-logs")
    page.keyboard.press("Alt+Shift+KeyX")
    expect(output).to_have_text("Action: delete-environment")
    # The disabled command shows a hint, but its key must not run it.
    page.keyboard.press("Alt+Shift+KeyD")
    page.wait_for_timeout(100)
    expect(output).to_have_text("Action: delete-environment")

    # The palette's search box is a combobox, so a key pressed with focus in
    # it still runs its command, even though other text fields are left alone.
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')
    palette_input.focus()
    palette_input.press("Alt+Shift+KeyV")
    expect(output).to_have_text("Action: view-logs")

    # A disabled palette's commands are unavailable, so their keys do nothing.
    _set_inert_box(page, "Disable palette")
    page.keyboard.press("Alt+Shift+KeyX")
    page.wait_for_timeout(100)
    expect(output).to_have_text("Action: view-logs")
    assert errors == []


def test_quality_scenario_shortcut_hint_runs_its_command_and_a_disabled_hint_does_not(
    page: Any,
    open_scenario: Any,
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    open_scenario("command-palette.states")
    _wait_for_scenario_palettes(page)
    # The spans read: open state, query, last action, shortcut opens.
    basic = page.locator("#quality-command-palette-basic-output span")

    page.keyboard.press("Alt+Shift+KeyO")
    expect(basic).to_have_text(["closed", "empty", "open-settings", "0"])
    # The disabled "Managed command" shows Alt Shift G, which must do nothing.
    page.keyboard.press("Alt+Shift+KeyG")
    page.wait_for_timeout(100)
    expect(basic).to_have_text(["closed", "empty", "open-settings", "0"])
    assert errors == []


def test_an_owner_focus_move_in_on_action_wins_when_the_command_closes_the_palette(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    # api.md promises that a deliberate focus move in onAction wins over the
    # Dialog's return-focus step, also for a command that closes the palette.
    errors = _open_snippet(page, serve_citry_ui_live, "command_actions")
    palette = page.locator("dialog")
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')
    output = page.locator("output[aria-live=polite]")

    _set_inert_box(page, "Move owner focus")
    palette_input.fill("delete")
    palette_input.press("Enter")

    page.wait_for_function("!document.querySelector('dialog').open")
    assert palette.evaluate("element => element.open") is False
    assert page.evaluate("document.activeElement.id") == "command-action-focus-target"
    # The owner's log shows the close request before the action.
    expect(output).to_contain_text("action:delete-draft:keyboard:true")
    log = output.inner_text()
    assert log.index("open:false:action") < log.index("action:delete-draft:")
    assert errors == []


# A small page whose palette has closing commands only. `__log` records what
# the owner's callbacks saw, in call order, so each test can check the order.
_ORDER_PAGE_JS = """
  window.__log = [];
  $component({
    data() {
      // `show` lets a test unmount the palette from the owner's callback, and
      // `tick` is reactive data that a test bumps from the page.
      const state = Citry.vue.reactive({ open: true, show: true, tick: 0 });
      window.__bumpTick = () => { state.tick += 1; };
      return state;
    },
    methods: {
      onOpenChange(value, detail) {
        window.__log.push(`open:${value}:${detail.reason}`);
        if (value || CLOSE_ACCEPTED) this.open = value;
        // A test arms these flags to make the owner fail once on a close.
        if (!value && HIDE_ON_CLOSE) this.show = false;
        if (!value && window.__releaseOnClose) this.open = null;
        if (!value && window.__reopenOnClose) {
          window.__reopenOnClose = false;
          document.getElementById('trigger').click();
        }
        if (!value && window.__throwOpenOnce) {
          window.__throwOpenOnce = false;
          throw new Error('Owner open failed');
        }
      },
      onQueryChange(value, detail) {
        window.__log.push(`query:${value}:${detail.reason}`);
        if (detail.reason === 'close' && window.__throwQueryOnce) {
          window.__throwQueryOnce = false;
          throw new Error('Owner query failed');
        }
      },
      onAction(value, detail) {
        // Reading `tick` shows whether a reactive effect ends up tracking it.
        void this.tick;
        // The dialog is gone when the owner unmounted the palette.
        const dialog = document.querySelector('dialog');
        window.__log.push(`action:${value}:dialogOpen=${dialog?.open ?? false}`);
        if (value === 'focus-owner') document.getElementById('owner-focus').focus();
        if (value === 'boom') throw new Error('Application action failed');
        if (value === 'copy-id') {
          window.__clip = 'pending';
          navigator.clipboard.writeText('copied-id').then(
            () => { window.__clip = 'resolved'; },
            (error) => { window.__clip = `rejected:${error}`; },
          );
        }
      },
    },
  });
"""


def _serve_order_page(
    page: Any,
    serve_citry_ui_live: Any,
    *,
    controlled: bool,
    accept_close: bool = True,
    hide_on_close: bool = False,
) -> list[str]:
    app = _app()
    js = _ORDER_PAGE_JS.replace("CLOSE_ACCEPTED", "true" if accept_close else "false").replace(
        "HIDE_ON_CLOSE", "true" if hide_on_close else "false"
    )
    open_binding = ':open="open"' if controlled else ""

    class OrderPage(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <button id="owner-focus" type="button">Owner focus</button>
              <template v-if="show">
              <c-CCommandPalette
                label="Order commands"
                c-entries="entries"
                OPEN_BINDING
                :onOpenChange="onOpenChange"
                :onQueryChange="onQueryChange"
                :onAction="onAction"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <button id="trigger" type="button" c-bind="activator_attrs">
                    Open commands
                  </button>
                </c-fill>
              </c-CCommandPalette>
              </template>
              <c-js />
            </body>
          </html>
        """.replace("OPEN_BINDING", open_binding)

        def template_data(self, kwargs, slots):
            return {
                "entries": (
                    CCommandPaletteCommand("copy-id", "Copy ID"),
                    CCommandPaletteCommand("boom", "Boom"),
                    CCommandPaletteCommand("other", "Other"),
                    CCommandPaletteCommand("focus-owner", "Focus owner"),
                )
            }

    OrderPage.js = js
    html = str(OrderPage())
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    # Only Chromium knows these permission names; Firefox rejects them.
    if page.context.browser.browser_type.name == "chromium":
        page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page.goto(serve_citry_ui_live(app, html) + "/", wait_until="networkidle")
    page.wait_for_selector("[data-citry-command-palette-initialized]")
    if not controlled:
        page.locator("#trigger").click()
    page.wait_for_function("document.querySelector('dialog').open")
    return errors


def test_uncontrolled_closing_command_runs_on_action_after_the_close_and_query_reset(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _serve_order_page(page, serve_citry_ui_live, controlled=False)
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')

    palette_input.fill("other")
    palette_input.press("Enter")

    page.wait_for_function("window.__log.some(entry => entry.startsWith('action:'))")
    # The query-change from the typing comes first, then the close, the
    # close's own query reset, and only then the action.
    assert page.evaluate("window.__log") == [
        "open:true:trigger",
        "query:other:input",
        "open:false:action",
        "query::close",
        "action:other:dialogOpen=false",
    ]
    assert errors == []


def test_declined_controlled_close_still_runs_on_action_once_with_the_dialog_open(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _serve_order_page(page, serve_citry_ui_live, controlled=True, accept_close=False)
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')

    palette_input.press("Enter")

    page.wait_for_function("window.__log.some(entry => entry.startsWith('action:'))")
    # Let any second call surface before counting.
    page.wait_for_timeout(200)
    log = page.evaluate("window.__log")
    assert [entry for entry in log if entry.startswith("action:")] == ["action:copy-id:dialogOpen=true"]
    assert log.index("open:false:action") < log.index("action:copy-id:dialogOpen=true")
    assert page.locator("dialog").evaluate("element => element.open") is True
    assert errors == []


@pytest.mark.parametrize("controlled", [False, True])
def test_throwing_on_action_of_a_closing_command_leaves_the_palette_closed_and_reports_once(
    page: Any,
    serve_citry_ui_live: Any,
    controlled: bool,
) -> None:
    errors = _serve_order_page(page, serve_citry_ui_live, controlled=controlled)
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')

    palette_input.fill("boom")
    palette_input.press("Enter")

    page.wait_for_function("!document.querySelector('dialog').open")
    page.wait_for_function("window.__log.some(entry => entry.startsWith('action:'))")
    page.wait_for_timeout(200)
    assert page.locator("dialog").evaluate("element => element.open") is False
    assert errors == ["Application action failed"]


@pytest.mark.parametrize("controlled", [False, True], ids=["uncontrolled", "controlled"])
@pytest.mark.parametrize("activation", ["click", "enter"])
def test_clipboard_write_in_on_action_of_a_closing_command_keeps_the_user_activation(
    page: Any,
    serve_citry_ui_live: Any,
    controlled: bool,
    activation: str,
) -> None:
    # Firefox lets writeText() resolve only while the user's activation is
    # still live, so the Firefox run shows that the deferred onAction still
    # has the user's activation. Chromium is granted the clipboard
    # permission, so there this only checks the write.
    errors = _serve_order_page(page, serve_citry_ui_live, controlled=controlled)
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')

    if activation == "click":
        page.get_by_role("option", name="Copy ID").click()
    else:
        palette_input.fill("copy")
        palette_input.press("Enter")

    page.wait_for_function("window.__clip && window.__clip !== 'pending'")
    assert page.evaluate("window.__clip") == "resolved"
    # Reading the clipboard back needs the permission only Chromium is granted.
    if page.context.browser.browser_type.name == "chromium":
        assert page.evaluate("navigator.clipboard.readText()") == "copied-id"
    assert errors == []


def _action_entries(page: Any) -> list[str]:
    return [entry for entry in page.evaluate("window.__log") if entry.startswith("action:")]


def _wait_frames(page: Any, count: int = 2) -> None:
    # Resolves after `count` animation frames, so queued work has run.
    page.evaluate(
        """count => new Promise(resolve => {
          const step = (left) => left === 0 ? resolve() : requestAnimationFrame(() => step(left - 1));
          step(count);
        })""",
        count,
    )


@pytest.mark.parametrize("controlled", [False, True], ids=["uncontrolled", "controlled"])
@pytest.mark.parametrize("failing_callback", ["open", "query"])
def test_owner_callback_throwing_during_the_close_still_runs_on_action_once(
    page: Any,
    serve_citry_ui_live: Any,
    failing_callback: str,
    controlled: bool,
) -> None:
    errors = _serve_order_page(page, serve_citry_ui_live, controlled=controlled)
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')

    # The query reset on close only fires when there is a query to reset, so
    # type one before the command closes the palette.
    palette_input.fill("other")
    page.evaluate(
        "flag => { window[flag] = true; }", "__throwOpenOnce" if failing_callback == "open" else "__throwQueryOnce"
    )
    palette_input.press("Enter")

    page.wait_for_function("window.__log.some(entry => entry.startsWith('action:'))")
    page.wait_for_function("!document.querySelector('dialog').open")
    expected_error = "Owner open failed" if failing_callback == "open" else "Owner query failed"
    # A controlled close applies inside Vue's update, so Vue catches an
    # onQueryChange error there and logs it to the console, in a form that
    # differs between browsers, instead of raising it as a page error.
    vue_logs_it = controlled and failing_callback == "query"
    assert errors == ([] if vue_logs_it else [expected_error])
    log = page.evaluate("window.__log")
    # The action runs right after the failed close request, not later.
    assert log[-1] == "action:other:dialogOpen=false"
    assert _action_entries(page) == ["action:other:dialogOpen=false"]

    # A later, unrelated close must not run the action a second time.
    page.locator("#trigger").click()
    page.wait_for_function("document.querySelector('dialog').open")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('dialog').open")
    _wait_frames(page)
    assert _action_entries(page) == ["action:other:dialogOpen=false"]
    assert errors == ([] if vue_logs_it else [expected_error])


def test_owner_releasing_control_in_on_open_change_still_runs_on_action_once(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _serve_order_page(page, serve_citry_ui_live, controlled=True)
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')

    # The owner hands control back with open=null instead of accepting the
    # close, so the palette stays open and no close ever settles.
    page.evaluate("window.__releaseOnClose = true")
    palette_input.fill("other")
    palette_input.press("Enter")

    page.wait_for_function("window.__log.some(entry => entry.startsWith('action:'))")
    assert _action_entries(page) == ["action:other:dialogOpen=true"]

    # The next close must not run that action again.
    page.evaluate("window.__releaseOnClose = false")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('dialog').open")
    _wait_frames(page)
    assert _action_entries(page) == ["action:other:dialogOpen=true"]
    assert errors == []


def test_uncontrolled_owner_reopening_in_on_open_change_still_runs_on_action_once(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _serve_order_page(page, serve_citry_ui_live, controlled=False)
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')

    # The owner opens the palette again from onOpenChange(false), so the
    # close it reported never stays applied.
    page.evaluate("window.__reopenOnClose = true")
    palette_input.fill("other")
    palette_input.press("Enter")

    page.wait_for_function("window.__log.some(entry => entry.startsWith('action:'))")
    assert _action_entries(page) == ["action:other:dialogOpen=true"]

    # A later, unrelated close must not run that action again.
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('dialog').open")
    _wait_frames(page)
    assert _action_entries(page) == ["action:other:dialogOpen=true"]
    assert errors == []


def test_controlled_owner_unmounting_the_palette_on_close_still_runs_on_action(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _serve_order_page(page, serve_citry_ui_live, controlled=True, hide_on_close=True)
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')

    palette_input.fill("other")
    palette_input.press("Enter")

    page.wait_for_function("window.__log.some(entry => entry.startsWith('action:'))")
    # Let any second call surface before counting.
    _wait_frames(page)
    page.wait_for_timeout(200)
    assert page.locator("dialog").count() == 0
    assert _action_entries(page) == ["action:other:dialogOpen=false"]
    assert errors == []


@pytest.mark.parametrize("controlled", [False, True], ids=["uncontrolled", "controlled"])
def test_owner_focus_move_in_on_action_survives_the_close(
    page: Any,
    serve_citry_ui_live: Any,
    controlled: bool,
) -> None:
    errors = _serve_order_page(page, serve_citry_ui_live, controlled=controlled)
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')

    palette_input.fill("focus")
    palette_input.press("Enter")

    page.wait_for_function("window.__log.some(entry => entry.startsWith('action:'))")
    # The Dialog's return-focus step runs after the close, so check after it.
    _wait_frames(page)
    assert page.evaluate("document.activeElement.id") == "owner-focus"
    assert errors == []


def test_controlled_on_action_reading_reactive_data_does_not_rerun_the_palette_effect(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _serve_order_page(page, serve_citry_ui_live, controlled=True)
    palette_input = page.locator('[data-citry-ui-part="command-palette-input"]')

    palette_input.fill("other")
    palette_input.press("Enter")
    page.wait_for_function("window.__log.some(entry => entry.startsWith('action:'))")
    page.wait_for_function("!document.querySelector('dialog').open")

    # Check before anything else re-runs the effect, because each run
    # records again which reactive values it reads. Set the closed palette's
    # input without an input event, so the palette's own state still holds
    # the empty query; an effect re-run caused by `tick` would write that
    # state back.
    palette_input.evaluate("element => { element.value = 'zzz'; }")
    page.evaluate("window.__bumpTick()")
    _wait_frames(page)
    assert palette_input.input_value() == "zzz"
    assert errors == []
