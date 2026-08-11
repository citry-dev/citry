"""Browser contract tests for the Disclosure component family."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cdisclosure.cdisclosure import (
    CDisclosure,
    CInternalDisclosureActionsContent,
    CInternalDisclosurePanelContent,
    CInternalDisclosureTitleContent,
)

pytestmark = pytest.mark.e2e

_DISCLOSURE_COMPONENTS = (
    CDisclosure,
    CInternalDisclosureTitleContent,
    CInternalDisclosureActionsContent,
    CInternalDisclosurePanelContent,
)


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root.")


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-disclosure-e2e", _DISCLOSURE_COMPONENTS))
    return app


def _page_html() -> str:
    app = _app()

    class Page(Component):
        citry = app
        css = """
          :where(.disclosure-brand) {
            --cui-disclosure-radius: 19px;
            --cui-disclosure-trigger-open-color: rgb(88 28 135);
          }
          :where(.disclosure-fast) {
            --cui-disclosure-duration: 80ms;
          }
          :where(.disclosure-zero) {
            --cui-disclosure-duration: 0ms;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body
              x-data
              x-init="Alpine.store('disclosureTest', {
                events: [],
                nativeClicks: 0,
                controlled: true,
                controlledDisabled: false,
                variant: 'outline',
                size: 'md',
                indicator: true,
                indicatorPosition: 'end',
                mutateGuideCallback: false,
              })"
            >
              <button id="before" type="button">Before</button>
              <form id="settings-form">
                <c-CDisclosure
                  id="guide"
                  class_="disclosure-brand disclosure-fast"
                  actions_label="Guide actions"
                  c-trigger_attrs="{'@click.stop': '$store.disclosureTest.nativeClicks += 1'}"
                  $c-props="{
                    variant: $store.disclosureTest.variant,
                    size: $store.disclosureTest.size,
                    indicator: $store.disclosureTest.indicator,
                    indicatorPosition: $store.disclosureTest.indicatorPosition,
                    onOpenChange: (next, detail) => {
                      $store.disclosureTest.events.push({
                        next,
                        detail,
                        observed: document.querySelector('#guide button').ariaExpanded,
                      });
                      if ($store.disclosureTest.mutateGuideCallback) {
                        document.querySelector('#guide-title').textContent = '';
                      }
                    },
                  }"
                >
                  <c-fill name="title"><strong id="guide-title">System requirements</strong></c-fill>
                  <c-fill name="actions">
                    <button id="copy-guide" type="button">Copy link</button>
                  </c-fill>
                  <c-fill name="default">
                    <label for="guide-note">Installation note</label>
                    <input id="guide-note" name="note" value="original" required />
                    <c-CDisclosure id="nested" class_="disclosure-zero" heading_level="4">
                      <c-fill name="title">Proxy settings</c-fill>
                      <c-fill name="default">
                        <button id="nested-control" type="button">Test proxy</button>
                      </c-fill>
                    </c-CDisclosure>
                  </c-fill>
                </c-CDisclosure>
              </form>

              <c-CDisclosure
                id="controlled"
                class_="disclosure-zero"
                $c-props="{
                  open: $store.disclosureTest.controlled,
                  disabled: $store.disclosureTest.controlledDisabled,
                  onOpenChange: (next, detail) => $store.disclosureTest.events.push({next, detail}),
                }"
              >
                <c-fill name="title"><span id="controlled-title">Advanced logging</span></c-fill>
                <c-fill name="default">
                  <input id="controlled-input" value="trace" />
                </c-fill>
              </c-CDisclosure>

              <fieldset id="native-fieldset">
                <legend id="native-legend">Native fieldset</legend>
                <div id="fieldset-holder">
                  <c-CDisclosure id="fieldset-disclosure" class_="disclosure-zero">
                    <c-fill name="title"><span id="fieldset-title">Managed policy</span></c-fill>
                    <c-fill name="default">Policy details</c-fill>
                  </c-CDisclosure>
                </div>
              </fieldset>

              <c-CDisclosure id="validation" open class_="disclosure-zero">
                <c-fill name="title"><span id="validation-title">Validation title</span></c-fill>
                <c-fill name="default"><div id="validation-content">Safe content</div></c-fill>
              </c-CDisclosure>
              <button id="after" type="button">After</button>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _initial_invalid_page_html() -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body
              x-data
              x-init="Alpine.store('initialInvalid', {open: true, events: []})"
            >
              <c-CDisclosure
                id="initial-invalid"
                $c-props="{
                  open: $store.initialInvalid.open,
                  onOpenChange: (next, detail) => $store.initialInvalid.events.push({next, detail}),
                }"
              >
                <c-fill name="title"><span id="initial-invalid-title">Declared title</span></c-fill>
                <c-fill name="default">Declared closed content</c-fill>
              </c-CDisclosure>
              <script>
                document.querySelector('#initial-invalid-title').textContent = '';
              </script>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _local_scope_page_html() -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body>
              <section x-data="{open:false, controlled:true}">
                <c-CDisclosure
                  id="local-controlled"
                  style="--cui-disclosure-duration: 0ms"
                  $c-props="{
                    open: controlled ? open : null,
                    onOpenChange: next => { if (controlled) open = next; },
                  }"
                >
                  <c-fill name="title">Local owner</c-fill>
                  <c-fill name="default">Local panel</c-fill>
                </c-CDisclosure>
                <button id="local-show" type="button" @click="controlled=true; open=true">
                  Show
                </button>
                <button id="local-hide" type="button" @click="controlled=true; open=false">
                  Hide
                </button>
                <button id="local-release" type="button" @click="controlled=false">
                  Release
                </button>
                <output id="local-state" x-text="`${controlled}:${open}`"></output>
              </section>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _events_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-disclosure-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(ComponentLibrary("citry-ui-disclosure-events-e2e", _DISCLOSURE_COMPONENTS))

    class EventsDisclosure(Component):
        citry = app

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return EventsDisclosure(step=state.step)

        template = """
          <section data-events-disclosure>
            <button class="advance-disclosure" type="button" @c-click="advance">
              Advance
            </button>
            <output id="events-step">{{ step }}</output>
            <c-CDisclosure
              #c-key="'events-disclosure'"
              id="events-disclosure"
              c-open="server_open"
              style="--cui-disclosure-duration: 0ms"
              $c-props="{
                open: $store.disclosureMorph.controlled,
                onOpenChange: (next, detail) => $store.disclosureMorph.events.push({next, detail}),
              }"
            >
              <c-fill name="title">Morph title {{ step }}</c-fill>
              <c-fill name="default"><input id="morph-input" value="preserved" /></c-fill>
            </c-CDisclosure>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {
                "server_open": kwargs.step >= 2,
                "step": kwargs.step,
            }

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body
              x-data
              x-init="Alpine.store('disclosureMorph', {controlled: undefined, events: []})"
            >
              <c-events-disclosure />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def _overlay_page_html(kind: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    surfaces = {
        "popover": """
          <c-CPopover
            id="anchored-surface"
            $c-props="{
              onOpenChange: (next, detail) => window.__overlayClose = {
                next, reason: detail.reason, forced: detail.forced,
              },
            }"
          >
            <c-fill name="activator" data="{ activator_attrs }">
              <button id="anchored-trigger" type="button" c-bind="activator_attrs">
                Open help
              </button>
            </c-fill>
            <c-fill name="title">Credential format</c-fill>
            <c-fill name="default"><input id="anchored-focus" value="token" /></c-fill>
          </c-CPopover>
        """,
        "menu": """
          <c-CMenu
            id="anchored-surface"
            $c-props="{
              onOpenChange: (next, detail) => window.__overlayClose = {
                next, reason: detail.reason, forced: detail.forced,
              },
            }"
          >
            <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
              <button
                id="anchored-trigger"
                type="button"
                c-disabled="activator_disabled"
                c-bind="activator_attrs"
              >Open menu</button>
            </c-fill>
            <c-fill name="default">
              <c-CMenuItem value="inspect">Inspect credential</c-CMenuItem>
            </c-fill>
          </c-CMenu>
        """,
        "tooltip": """
          <c-CTooltip
            id="anchored-surface"
            text="Credential format"
            c-delay="0"
            c-close_delay="0"
            $c-props="{
              onOpenChange: (next, detail) => window.__overlayClose = {
                next, reason: detail.reason, forced: detail.forced,
              },
            }"
          >
            <c-fill name="activator" data="{ activator_attrs }">
              <button id="anchored-trigger" type="button" c-bind="activator_attrs">
                Explain format
              </button>
            </c-fill>
          </c-CTooltip>
        """,
    }
    surface = surfaces[kind]

    class Page(Component):
        citry = app
        template = (
            """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body x-data>
              <c-CDisclosure
                id="overlay-disclosure"
                open
                style="--cui-disclosure-duration: 0ms"
              >
                <c-fill name="title">Credential help</c-fill>
                <c-fill name="default">
            """
            + surface
            + """
                </c-fill>
              </c-CDisclosure>
              <c-js />
            </body>
          </html>
        """
        )

    return str(Page())


def _incompatible_runtime_page_html() -> str:
    app = _app()

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body>
              <script>
                (() => {
                  const coordinator = { generation: 'closed-v2-coordinator' };
                  const runtime = {
                    version: 2,
                    stats: { listenerSets: 0, reconciliations: 0 },
                    layers: [],
                    coordinatorFor: () => coordinator,
                  };
                  window.__closedV2Coordinator = coordinator;
                  window.__oldAnchoredRuntime = runtime;
                  globalThis[Symbol.for('citry-ui:anchored-layer-runtime')] = runtime;
                })();
              </script>
              <div id="closed-v2-owner" data-citry-tooltip-initialized hidden></div>
              <c-CDisclosure id="new-disclosure">
                <c-fill name="title">New fragment title</c-fill>
                <c-fill name="default">New fragment panel</c-fill>
              </c-CDisclosure>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


@pytest.fixture
def disclosure_page(page: Any):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page_html())
    page.wait_for_function(
        """() => {
          const roots = [...document.querySelectorAll('[data-citry-disclosure-root]')];
          return roots.length === 5
            && roots.every(root => root.hasAttribute('data-citry-disclosure-initialized'));
        }"""
    )
    return page, errors


def _trigger(page: Any, root_id: str):
    return page.locator(f"#{root_id} > [data-citry-ui-part=disclosure-header] button").first


def _panel(page: Any, root_id: str):
    return page.locator(f"#{root_id} > [data-citry-disclosure-panel]")


def test_uncontrolled_native_activation_callback_actions_and_nested_isolation(disclosure_page):
    page, errors = disclosure_page
    guide = page.locator("#guide")
    trigger = _trigger(page, "guide")
    panel = _panel(page, "guide")

    assert trigger.get_attribute("aria-expanded") == "false"
    trigger.click()
    page.wait_for_timeout(100)
    assert trigger.get_attribute("aria-expanded") == "true"
    assert not panel.is_hidden()
    assert guide.get_attribute("data-state") == "open"
    assert page.evaluate("Alpine.store('disclosureTest').nativeClicks") == 1
    event = page.evaluate("Alpine.store('disclosureTest').events.at(-1)")
    assert event == {
        "next": True,
        "observed": "false",
        "detail": {
            "open": True,
            "previousOpen": False,
            "source": "activation",
            "controlled": False,
        },
    }

    page.locator("#copy-guide").click()
    assert trigger.get_attribute("aria-expanded") == "true"
    nested_trigger = _trigger(page, "nested")
    nested_trigger.click()
    assert nested_trigger.get_attribute("aria-expanded") == "true"
    assert trigger.get_attribute("aria-expanded") == "true"

    trigger.focus()
    trigger.press("ArrowDown")
    assert trigger.evaluate("element => element === document.activeElement")
    trigger.press("Enter")
    page.wait_for_timeout(100)
    assert trigger.get_attribute("aria-expanded") == "false"
    trigger.press("Space")
    page.wait_for_timeout(100)
    assert trigger.get_attribute("aria-expanded") == "true"
    assert page.evaluate("Alpine.store('disclosureTest').nativeClicks") == 3
    assert errors == []


def test_initial_and_active_disclosure_have_a_name_and_no_serious_axe_findings(
    disclosure_page,
):
    page, errors = disclosure_page
    root = page.locator("#guide")
    trigger = page.get_by_role("button", name="System requirements", exact=True)
    assert trigger.count() == 1
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))

    for expected in ("false", "true"):
        assert trigger.get_attribute("aria-expanded") == expected
        violations = root.evaluate(
            """async element => (await axe.run(element, {resultTypes:['violations']})).violations
              .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
        )
        assert violations == []
        if expected == "false":
            trigger.click()
            page.wait_for_timeout(100)

    assert errors == []


def test_controlled_refusal_acceptance_release_and_invalid_input_episodes(disclosure_page):
    page, errors = disclosure_page
    trigger = _trigger(page, "controlled")
    panel = _panel(page, "controlled")

    assert trigger.get_attribute("aria-expanded") == "true"
    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "true"
    request = page.evaluate("Alpine.store('disclosureTest').events.at(-1)")
    assert request["next"] is False
    assert request["detail"]["controlled"] is True

    page.evaluate("Alpine.store('disclosureTest').controlled = false")
    page.wait_for_function("document.querySelector('#controlled button').ariaExpanded === 'false'")
    assert panel.evaluate("element => element.hidden && element.inert")
    count = page.evaluate("Alpine.store('disclosureTest').events.length")

    page.evaluate("Alpine.store('disclosureTest').controlled = null")
    page.wait_for_timeout(20)
    assert trigger.get_attribute("aria-expanded") == "false"
    assert page.evaluate("Alpine.store('disclosureTest').events.length") == count

    page.evaluate("Alpine.store('disclosureTest').controlled = 'bad-one'")
    page.wait_for_timeout(20)
    page.evaluate("Alpine.store('disclosureTest').controlled = 'bad-two'")
    page.wait_for_timeout(20)
    open_errors = [error for error in errors if "CDisclosure open received invalid" in error]
    assert len(open_errors) == 1
    assert trigger.get_attribute("aria-expanded") == "false"

    page.evaluate("Alpine.store('disclosureTest').controlled = true")
    page.wait_for_function("document.querySelector('#controlled button').ariaExpanded === 'true'")
    page.evaluate("Alpine.store('disclosureTest').controlled = 42")
    page.wait_for_timeout(20)
    open_errors = [error for error in errors if "CDisclosure open received invalid" in error]
    assert len(open_errors) == 2


def test_callback_runs_precommit_and_post_callback_preflight_rejects_new_invalidity(
    disclosure_page,
):
    page, errors = disclosure_page
    root = page.locator("#guide")
    trigger = _trigger(page, "guide")
    panel = _panel(page, "guide")
    page.evaluate("Alpine.store('disclosureTest').mutateGuideCallback = true")

    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "false"
    assert panel.evaluate("element => element.hidden && element.inert")
    assert root.get_attribute("data-citry-disclosure-initialized") is None
    event = page.evaluate("Alpine.store('disclosureTest').events.at(-1)")
    assert event["observed"] == "false"
    assert event["next"] is True
    assert len([error for error in errors if "settled structure is invalid" in error]) == 1

    page.evaluate("Alpine.store('disclosureTest').mutateGuideCallback = false")
    page.locator("#guide-title").evaluate("element => { element.textContent = 'Repaired title'; }")
    page.wait_for_function("document.querySelector('#guide').hasAttribute('data-citry-disclosure-initialized')")
    assert trigger.get_attribute("aria-expanded") == "false"


def test_focus_presence_animation_rapid_reversal_and_form_continuity(disclosure_page):
    page, errors = disclosure_page
    trigger = _trigger(page, "guide")
    panel = _panel(page, "guide")
    note = page.locator("#guide-note")
    trigger.click()
    page.wait_for_timeout(100)
    note.fill("edited")
    note.focus()

    trigger.evaluate("element => element.click()")
    assert trigger.get_attribute("aria-expanded") == "false"
    assert panel.get_attribute("aria-hidden") == "true"
    assert panel.evaluate("element => element.inert && !element.hidden")
    assert trigger.evaluate("element => element === document.activeElement")
    page.wait_for_timeout(100)
    assert panel.evaluate("element => element.hidden")
    assert panel.evaluate("element => element.style.blockSize === '' && element.style.overflow === ''")

    trigger.click()
    page.wait_for_timeout(20)
    trigger.click()
    page.wait_for_timeout(20)
    trigger.click()
    page.wait_for_timeout(100)
    assert trigger.get_attribute("aria-expanded") == "true"
    assert not panel.is_hidden()
    assert note.input_value() == "edited"
    form = page.locator("#settings-form").evaluate("form => Object.fromEntries(new FormData(form).entries())")
    assert form["note"] == "edited"
    assert errors == []


def test_native_fieldset_and_first_legend_reconciliation(disclosure_page):
    page, errors = disclosure_page
    root = page.locator("#fieldset-disclosure")
    trigger = _trigger(page, "fieldset-disclosure")

    page.locator("#native-fieldset").evaluate("element => { element.disabled = true; }")
    page.wait_for_function("document.querySelector('#fieldset-disclosure button').matches(':disabled')")
    assert root.get_attribute("data-disabled") == ""
    trigger.evaluate("element => element.click()")
    assert trigger.get_attribute("aria-expanded") == "false"

    page.evaluate("document.querySelector('#native-legend').append(document.querySelector('#fieldset-holder'))")
    page.wait_for_function("!document.querySelector('#fieldset-disclosure button').matches(':disabled')")
    assert root.get_attribute("data-disabled") is None
    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "true"

    page.evaluate(
        """() => {
          const legend = document.createElement('legend');
          legend.id = 'new-first-legend';
          legend.textContent = 'New first legend';
          document.querySelector('#native-fieldset').prepend(legend);
        }"""
    )
    page.wait_for_function("document.querySelector('#fieldset-disclosure button').matches(':disabled')")
    assert root.get_attribute("data-disabled") == ""

    page.locator("#fieldset-title").evaluate("element => { element.textContent = ''; }")
    page.wait_for_function(
        "!document.querySelector('#fieldset-disclosure').hasAttribute('data-citry-disclosure-initialized')"
    )
    page.locator("#native-fieldset").evaluate("element => { element.disabled = false; }")
    assert root.get_attribute("data-disabled") == ""
    page.locator("#fieldset-title").evaluate("element => { element.textContent = 'Repaired policy'; }")
    page.wait_for_function(
        "document.querySelector('#fieldset-disclosure').hasAttribute('data-citry-disclosure-initialized')"
    )
    assert root.get_attribute("data-disabled") is None
    page.locator("#native-fieldset").evaluate("element => { element.disabled = true; }")
    page.wait_for_function("document.querySelector('#fieldset-disclosure').hasAttribute('data-disabled')")
    assert len([error for error in errors if "settled structure is invalid" in error]) == 1
    assert all("settled structure is invalid" in error for error in errors)


def test_synchronous_structure_preflight_suspension_repair_and_latest_owner_state(disclosure_page):
    page, errors = disclosure_page
    root = page.locator("#validation")
    trigger = _trigger(page, "validation")
    panel = _panel(page, "validation")

    page.evaluate(
        """() => {
          document.querySelector('#validation-title').textContent = '   ';
          document.querySelector('#validation button').click();
        }"""
    )
    assert root.get_attribute("data-citry-disclosure-initialized") is None
    assert trigger.get_attribute("aria-expanded") == "true"
    assert not panel.evaluate("element => element.hidden || element.inert")
    structure_errors = [error for error in errors if "settled structure is invalid" in error]
    assert len(structure_errors) == 1

    page.locator("#validation-title").evaluate("element => { element.textContent = 'Repaired title'; }")
    page.wait_for_function("document.querySelector('#validation').hasAttribute('data-citry-disclosure-initialized')")
    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "false"

    trigger.click()
    page.evaluate(
        """() => {
          const dialog = document.createElement('dialog');
          dialog.id = 'forbidden-dialog';
          dialog.textContent = 'Unsafe';
          document.querySelector('#validation-content').append(dialog);
          document.querySelector('#validation button').click();
        }"""
    )
    assert trigger.get_attribute("aria-expanded") == "true"
    assert not panel.evaluate("element => element.hidden || element.inert")
    assert root.get_attribute("data-citry-disclosure-initialized") is None
    page.locator("#forbidden-dialog").evaluate("element => element.remove()")
    page.wait_for_function("document.querySelector('#validation').hasAttribute('data-citry-disclosure-initialized')")
    assert trigger.get_attribute("aria-expanded") == "true"

    controlled_root = page.locator("#controlled")
    page.evaluate(
        """() => {
          document.querySelector('#controlled-title').textContent = '';
          Alpine.store('disclosureTest').controlled = false;
        }"""
    )
    page.wait_for_function("!document.querySelector('#controlled').hasAttribute('data-citry-disclosure-initialized')")
    assert _trigger(page, "controlled").get_attribute("aria-expanded") == "true"
    page.locator("#controlled-title").evaluate("element => { element.textContent = 'Repaired'; }")
    page.wait_for_function("document.querySelector('#controlled').hasAttribute('data-citry-disclosure-initialized')")
    assert _trigger(page, "controlled").get_attribute("aria-expanded") == "false"
    assert controlled_root.get_attribute("data-state") == "closed"


def test_beforetoggle_guard_shadow_host_guard_and_open_shadow_root_operation(disclosure_page):
    page, errors = disclosure_page
    root = page.locator("#validation")

    opened = page.evaluate(
        """() => {
          const raw = document.createElement('div');
          raw.id = 'raw-popover';
          raw.popover = 'manual';
          document.querySelector('#validation-content').append(raw);
          raw.showPopover();
          return raw.matches(':popover-open');
        }"""
    )
    assert opened is False
    assert root.get_attribute("data-citry-disclosure-initialized") is None
    page.locator("#raw-popover").evaluate("element => element.remove()")
    page.wait_for_function("document.querySelector('#validation').hasAttribute('data-citry-disclosure-initialized')")

    modal = page.evaluate(
        """() => {
          const dialog = document.createElement('dialog');
          dialog.id = 'raw-dialog';
          dialog.textContent = 'Unsafe modal';
          document.querySelector('#validation-content').append(dialog);
          dialog.showModal();
          return dialog.matches(':modal');
        }"""
    )
    assert modal is False
    assert root.get_attribute("data-citry-disclosure-initialized") is None
    page.locator("#raw-dialog").evaluate("element => element.remove()")
    page.wait_for_function("document.querySelector('#validation').hasAttribute('data-citry-disclosure-initialized')")

    page.evaluate(
        """() => {
          const unresolved = document.createElement('x-unresolved');
          unresolved.id = 'unresolved-descendant';
          document.querySelector('#validation-content').append(unresolved);
          document.querySelector('#validation button').click();
        }"""
    )
    assert root.get_attribute("data-citry-disclosure-initialized") is None
    page.locator("#unresolved-descendant").evaluate("element => element.remove()")
    page.wait_for_function("document.querySelector('#validation').hasAttribute('data-citry-disclosure-initialized')")

    page.evaluate(
        """() => {
          const host = document.createElement('div');
          host.id = 'shadow-descendant';
          host.attachShadow({mode: 'open'}).innerHTML = '<button>Opaque</button>';
          document.querySelector('#validation-content').append(host);
          document.querySelector('#validation button').click();
        }"""
    )
    assert root.get_attribute("data-citry-disclosure-initialized") is None
    assert any("ShadowRoot" in error for error in errors)
    page.locator("#shadow-descendant").evaluate("element => element.remove()")
    page.wait_for_function("document.querySelector('#validation').hasAttribute('data-citry-disclosure-initialized')")

    page.evaluate(
        """() => {
          const host = document.createElement('div');
          host.id = 'disclosure-shadow-host';
          document.body.append(host);
          const shadow = host.attachShadow({mode: 'open'});
          shadow.append(document.querySelector('#validation'));
          window.__disclosureShadow = shadow;
        }"""
    )
    page.evaluate("window.__disclosureShadow.querySelector('button').click()")
    assert page.evaluate("window.__disclosureShadow.querySelector('button').getAttribute('aria-expanded')") == "false"


def test_disabled_close_uses_body_or_composed_modal_focus_fallback(disclosure_page):
    page, errors = disclosure_page
    input_ = page.locator("#controlled-input")
    input_.focus()
    page.evaluate(
        """() => {
          Alpine.store('disclosureTest').controlledDisabled = true;
          Alpine.store('disclosureTest').controlled = false;
        }"""
    )
    page.wait_for_function("document.querySelector('#controlled button').matches(':disabled')")
    assert page.evaluate("document.activeElement === document.body")
    assert page.locator("body").get_attribute("tabindex") is None

    page.evaluate(
        """() => {
          Alpine.store('disclosureTest').controlledDisabled = false;
          Alpine.store('disclosureTest').controlled = true;
        }"""
    )
    page.wait_for_function("document.querySelector('#controlled button').ariaExpanded === 'true'")
    page.evaluate(
        """() => {
          const dialog = document.createElement('dialog');
          dialog.id = 'modal-owner';
          const host = document.createElement('div');
          dialog.append(host);
          document.body.append(dialog);
          dialog.showModal();
          const shadow = host.attachShadow({mode: 'open'});
          shadow.append(document.querySelector('#controlled'));
          window.__controlledShadow = shadow;
        }"""
    )
    page.evaluate("window.__controlledShadow.querySelector('#controlled-input').focus()")
    page.evaluate(
        """() => {
          Alpine.store('disclosureTest').controlledDisabled = true;
          Alpine.store('disclosureTest').controlled = false;
        }"""
    )
    page.wait_for_function("document.activeElement === document.querySelector('#modal-owner')")
    assert page.locator("#modal-owner").get_attribute("tabindex") is None
    assert errors == []


def test_public_css_reflections_rtl_zero_motion_and_print_expansion(disclosure_page):
    page, errors = disclosure_page
    root = page.locator("#guide")
    trigger = _trigger(page, "guide")
    indicator = trigger.locator('[data-citry-ui-part="disclosure-indicator"]')

    assert root.evaluate("element => getComputedStyle(element).borderTopLeftRadius") == "19px"
    page.evaluate(
        """() => {
          const store = Alpine.store('disclosureTest');
          store.variant = 'plain';
          store.size = 'lg';
          store.indicatorPosition = 'start';
          document.documentElement.dir = 'rtl';
        }"""
    )
    page.wait_for_function("document.querySelector('#guide').dataset.variant === 'plain'")
    assert root.get_attribute("data-size") == "lg"
    assert root.get_attribute("data-indicator-pos") == "start"
    assert indicator.evaluate("element => getComputedStyle(element).order") == "-1"

    zero_panel = _panel(page, "controlled")
    page.evaluate(
        """() => {
          Alpine.store('disclosureTest').controlledDisabled = false;
          Alpine.store('disclosureTest').controlled = false;
        }"""
    )
    page.wait_for_function("document.querySelector('#controlled button').ariaExpanded === 'false'")
    assert zero_panel.evaluate(
        "element => element.hidden && element.style.blockSize === '' && element.style.overflow === ''"
    )

    page.emulate_media(media="print")
    assert zero_panel.evaluate("element => getComputedStyle(element).display") == "block"
    assert errors == []


def test_initial_invalid_is_validation_only_and_repair_applies_latest_raw_owner_state(page: Any):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_initial_invalid_page_html())
    root = page.locator("#initial-invalid")
    trigger = _trigger(page, "initial-invalid")
    panel = _panel(page, "initial-invalid")
    page.wait_for_function("window.Alpine && Alpine.store('initialInvalid')")

    assert root.get_attribute("data-citry-disclosure-initialized") is None
    assert trigger.get_attribute("aria-expanded") == "false"
    assert panel.evaluate("element => element.hidden && element.inert")
    trigger.evaluate("element => element.click()")
    assert trigger.get_attribute("aria-expanded") == "false"

    page.evaluate("Alpine.store('initialInvalid').open = 'not-a-boolean'")
    page.wait_for_timeout(20)
    assert not any("CDisclosure open received invalid" in error for error in errors)
    page.evaluate(
        """() => {
          Alpine.store('initialInvalid').open = false;
          Alpine.store('initialInvalid').open = true;
        }"""
    )
    page.wait_for_timeout(20)
    assert trigger.get_attribute("aria-expanded") == "false"
    page.locator("#initial-invalid-title").evaluate("element => { element.textContent = 'Repaired declared title'; }")
    page.wait_for_function(
        "document.querySelector('#initial-invalid').hasAttribute('data-citry-disclosure-initialized')"
    )
    assert trigger.get_attribute("aria-expanded") == "true"
    assert not panel.evaluate("element => element.hidden || element.inert")
    assert page.evaluate("Alpine.store('initialInvalid').events.length") == 0
    assert len([error for error in errors if "settled structure is invalid" in error]) == 1


def test_local_alpine_scope_controls_external_and_trigger_requests(page: Any):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_local_scope_page_html())
    trigger = _trigger(page, "local-controlled")
    page.wait_for_function(
        "document.querySelector('#local-controlled').hasAttribute('data-citry-disclosure-initialized')"
    )

    page.locator("#local-show").click()
    page.wait_for_function("document.querySelector('#local-controlled button').ariaExpanded === 'true'")
    assert page.locator("#local-state").text_content() == "true:true"
    page.locator("#local-hide").click()
    page.wait_for_function("document.querySelector('#local-controlled button').ariaExpanded === 'false'")
    assert page.locator("#local-state").text_content() == "true:false"

    trigger.click()
    page.wait_for_function("document.querySelector('#local-controlled button').ariaExpanded === 'true'")
    page.locator("#local-release").click()
    page.wait_for_function("document.querySelector('#local-controlled button').ariaExpanded === 'false'")
    assert page.locator("#local-state").text_content() == "false:true"
    assert errors == []


def test_incompatible_runtime_generation_fails_closed_without_replacing_closed_v2_owner(
    page: Any,
):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_incompatible_runtime_page_html())
    page.wait_for_timeout(50)

    assert page.evaluate(
        """() => {
          const installed = globalThis[Symbol.for('citry-ui:anchored-layer-runtime')];
          return installed === window.__oldAnchoredRuntime
            && installed.coordinatorFor(document.body) === window.__closedV2Coordinator
            && installed.version === 2
            && installed.generation === undefined;
        }"""
    )
    assert page.locator("#closed-v2-owner").get_attribute("data-citry-tooltip-initialized") == ""
    assert page.locator("#new-disclosure").get_attribute("data-citry-disclosure-initialized") is None
    assert any("a full page reload is required" in error for error in errors)


def test_server_fingerprint_morph_handoff_preserves_and_replaces_only_the_release_baseline(
    page: Any,
    serve_citry_ui_live: Any,
):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    app, html = _events_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function("window.Citry && Citry.events && Citry.events._internal.alpineStarted")
    trigger = _trigger(page, "events-disclosure")
    page.evaluate("window.__eventsDisclosureRoot = document.querySelector('#events-disclosure')")

    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "true"
    assert page.evaluate("Alpine.store('disclosureMorph').events.length") == 1
    page.locator("#morph-input").fill("browser-owned")

    page.evaluate("() => Citry.events.send(document.querySelector('.advance-disclosure'), 'advance', {})")
    page.wait_for_function("document.querySelector('#events-step').textContent.trim() === '1'")
    assert page.evaluate("document.querySelector('#events-disclosure') === window.__eventsDisclosureRoot")
    assert trigger.get_attribute("aria-expanded") == "true"
    assert page.locator("#morph-input").input_value() == "browser-owned"

    page.evaluate("Alpine.store('disclosureMorph').controlled = false")
    page.wait_for_function("document.querySelector('#events-disclosure button').ariaExpanded === 'false'")
    page.evaluate("() => Citry.events.send(document.querySelector('.advance-disclosure'), 'advance', {})")
    page.wait_for_function("document.querySelector('#events-step').textContent.trim() === '2'")
    assert trigger.get_attribute("aria-expanded") == "false"
    assert page.evaluate("Alpine.store('disclosureMorph').events.length") == 1

    page.evaluate("Alpine.store('disclosureMorph').controlled = null")
    page.wait_for_function("document.querySelector('#events-disclosure button').ariaExpanded === 'true'")
    assert page.evaluate("Alpine.store('disclosureMorph').events.length") == 1
    assert errors == []


@pytest.mark.parametrize("kind", ["popover", "menu", "tooltip"])
def test_anchored_descendant_force_closes_after_disclosure_focus_recovery(
    page: Any,
    kind: str,
):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_overlay_page_html(kind))
    page.wait_for_function(
        """() => document.querySelector('#overlay-disclosure')
          ?.hasAttribute('data-citry-disclosure-initialized')"""
    )
    disclosure_trigger = _trigger(page, "overlay-disclosure")
    anchored_trigger = page.locator("[data-citry-menu-trigger]" if kind == "menu" else "#anchored-trigger")
    if kind == "tooltip":
        anchored_trigger.focus()
    else:
        anchored_trigger.click()
    page.wait_for_function("document.querySelector('#anchored-surface').matches(':popover-open')")
    if kind == "popover":
        page.locator("#anchored-focus").focus()
    elif kind == "menu":
        page.locator("#anchored-surface [role=menuitem]").focus()

    disclosure_trigger.evaluate("element => element.click()")
    page.wait_for_function("!document.querySelector('#anchored-surface').matches(':popover-open')")
    assert disclosure_trigger.evaluate("element => element === document.activeElement")
    assert page.evaluate("window.__overlayClose") == {
        "next": False,
        "reason": "ancestor",
        "forced": True,
    }
    if kind == "tooltip":
        disclosure_trigger.click()
        page.wait_for_function("document.querySelector('#overlay-disclosure button').ariaExpanded === 'true'")
        anchored_trigger.focus()
        page.wait_for_function("document.querySelector('#anchored-surface').matches(':popover-open')")
        assert page.evaluate("window.__overlayClose") == {
            "next": True,
            "reason": "focus",
            "forced": False,
        }
    assert errors == []
