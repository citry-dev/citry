"""Browser tests for CPopover's owned overlay behavior."""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _popover_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.space-popover) {
            --cui-popover-background: rgb(15 35 54);
            --cui-popover-foreground: rgb(244 248 251);
            --cui-popover-duration: 30ms;
          }

          :where(.space-popover [data-citry-ui-part="title"]) {
            letter-spacing: 1px;
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
              x-data="{
                controlled: false,
                open: false,
                accept: false,
                dismissible: true,
                placement: 'bottom-start',
                matchWidth: false,
              }"
            >
              <div style="padding: 180px 240px; min-block-size: 900px">
                <c-CPopover
                  id="europa-popover"
                  class_="space-popover"
                  $c-props="{
                    open: controlled ? open : undefined,
                    dismissible,
                    placement,
                    matchWidth,
                    onOpenChange: (nextOpen, detail) => {
                      window.__popoverRequest = {
                        nextOpen,
                        reason: detail.reason,
                        controlled: detail.controlled,
                        forced: detail.forced,
                      };
                      window.__popoverRequests = (window.__popoverRequests || 0) + 1;
                      if (accept) open = nextOpen;
                    },
                  }"
                >
                  <c-fill
                    name="activator"
                    data="{ activator_attrs }"
                  >
                    <c-CButton c-attrs="activator_attrs">
                      Inspect Europa
                    </c-CButton>
                  </c-fill>
                  <c-fill name="title">
                    Europa
                  </c-fill>
                  <c-fill name="description">
                    Icy moon of Jupiter
                  </c-fill>
                  <c-fill name="default">
                    <label for="ocean-depth">
                      Ocean depth
                    </label>
                    <input id="ocean-depth" value="100 km" autofocus />
                    <c-CPopover id="nested-popover" placement="bottom-end">
                      <c-fill
                        name="activator"
                        data="{ activator_attrs }"
                      >
                        <c-CButton
                          variant="outline"
                          c-attrs="activator_attrs"
                        >
                          Inspect plume
                        </c-CButton>
                      </c-fill>
                      <c-fill name="title">
                        Water plume
                      </c-fill>
                      <c-fill name="default">
                        Candidate vapor above the ice.
                      </c-fill>
                      <c-fill
                        name="actions"
                        data="{ close_attrs }"
                      >
                        <c-CButton c-attrs="close_attrs">
                          Done
                        </c-CButton>
                      </c-fill>
                    </c-CPopover>
                  </c-fill>
                  <c-fill
                    name="actions"
                    data="{ close_attrs }"
                  >
                    <c-CButton c-attrs="close_attrs">
                      Close
                    </c-CButton>
                  </c-fill>
                </c-CPopover>
              </div>
              <button id="outside" type="button">
                Outside
              </button>
              <button
                id="enable-control"
                type="button"
                @click="controlled = true"
              >
                Control
              </button>
              <button
                id="accept"
                type="button"
                @click="accept = true"
              >
                Accept
              </button>
              <button
                id="force-open"
                type="button"
                @click="open = true"
              >
                Force open
              </button>
              <button
                id="force-close"
                type="button"
                @click="open = false"
              >
                Force close
              </button>
              <button
                id="configure"
                type="button"
                @click="placement = 'top-end'; matchWidth = true"
              >
                Configure
              </button>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _popover_events_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-popover-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class SpecimenPopover(Component):
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
                return SpecimenPopover(step=state.step)

        template = """
          <section data-popover-specimen>
            <button class="advance-popover" type="button" @c-click="advance">
              Advance
            </button>
            <c-CPopover
              #c-key="'survey-popover'"
              id="survey-popover"
              c-placement="placement"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton c-attrs="activator_attrs">
                  Inspect survey
                </c-CButton>
              </c-fill>
              <c-fill name="title">
                Survey step {{ step }}
              </c-fill>
              <c-fill name="default">
                <input id="survey-note" value="Original note" />
              </c-fill>
            </c-CPopover>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {
                "placement": "top-end" if kwargs.step else "bottom-start",
                "step": kwargs.step,
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
              <c-specimen-popover />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def _mixed_anchored_runtime_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><c-css /></head>
            <body>
              <c-CPopover id="mixed-popover">
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Open details</c-CButton>
                </c-fill>
                <c-fill name="title">Europa</c-fill>
                <c-fill name="default">Icy surface</c-fill>
              </c-CPopover>
              <c-CTooltip id="mixed-tooltip" text="Jupiter's moon">
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Describe Europa</c-CButton>
                </c-fill>
              </c-CTooltip>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _load(page) -> list[str]:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.set_content(_popover_page(), wait_until="load")
    page.wait_for_function(
        """() => {
          const hosts = [...document.querySelectorAll('[data-citry-popover-host]')];
          return hosts.length === 2
            && hosts.every((host) => host.hasAttribute('data-citry-popover-initialized'));
        }"""
    )
    return console_errors


def _outer_trigger(page):
    return page.locator('[aria-controls="europa-popover"]')


def _outer(page):
    return page.locator("#europa-popover")


def test_popover_and_tooltip_initialize_one_shared_coordinator_dependency(page):
    page.set_content(_mixed_anchored_runtime_page(), wait_until="load")
    page.wait_for_function(
        """() => document.querySelector('[data-citry-popover-host]')
          ?.hasAttribute('data-citry-popover-initialized')
          && document.querySelector('[data-citry-tooltip-host]')
            ?.hasAttribute('data-citry-tooltip-initialized')"""
    )

    runtime = page.evaluate(
        """() => ({
          dependencies: [...document.scripts].filter((script) => script.textContent.includes(
            'cannot replace an incompatible anchored-layer runtime',
          )).length,
          version: window[Symbol.for('citry-ui:anchored-layer-runtime')]?.version,
          generation: window[Symbol.for('citry-ui:anchored-layer-runtime')]?.generation,
          capabilities: window[Symbol.for('citry-ui:anchored-layer-runtime')]?.capabilities,
          coordinators: window[Symbol.for('citry-ui:anchored-layer-runtime')]
            ?.stats.activeCoordinators,
        })"""
    )
    assert runtime == {
        "dependencies": 1,
        "version": 3,
        "generation": 3,
        "capabilities": ["ancestor-close-transaction-v1"],
        "coordinators": 0,
    }


def test_trigger_enters_top_layer_places_focus_and_preserves_theme(page):
    errors = _load(page)
    trigger = _outer_trigger(page)
    trigger.click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")

    assert _outer(page).get_attribute("data-open") == ""
    assert trigger.get_attribute("aria-expanded") == "true"
    assert page.locator("#ocean-depth").evaluate("element => element === document.activeElement")
    assert _outer(page).evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(15, 35, 54)"
    assert _outer(page).evaluate("element => getComputedStyle(element).color") == "rgb(244, 248, 251)"
    assert (
        page.locator("#europa-popover-title").evaluate("element => getComputedStyle(element).letterSpacing") == "1px"
    )
    assert page.evaluate("window.__popoverRequest") == {
        "nextOpen": True,
        "reason": "trigger",
        "controlled": False,
        "forced": False,
    }
    assert errors == []


def test_explicit_action_and_escape_close_and_restore_trigger_focus(page):
    _load(page)
    trigger = _outer_trigger(page)
    trigger.click()
    page.get_by_role("button", name="Close", exact=True).click()
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")

    assert page.evaluate("window.__popoverRequest.reason") == "action"
    assert _outer(page).evaluate("element => getComputedStyle(element).display") == "none"
    assert _outer(page).evaluate("element => element.getClientRects().length") == 0
    assert trigger.evaluate("element => element === document.activeElement")
    assert trigger.get_attribute("aria-expanded") == "false"

    trigger.click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")
    assert page.evaluate("window.__popoverRequest.reason") == "escape"
    assert trigger.evaluate("element => element === document.activeElement")


def test_outside_pointer_and_focus_keep_the_new_destination(page):
    _load(page)
    trigger = _outer_trigger(page)
    outside = page.locator("#outside")
    trigger.click()
    outside.click()
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")

    assert page.evaluate("window.__popoverRequest.reason") in {"outside", "focus-outside"}
    # WebKit does not focus a Button for every pointer activation. The
    # Popover must preserve that browser destination rather than force focus
    # back to its activator.
    assert not trigger.evaluate("element => element === document.activeElement")


def test_controlled_owner_can_decline_then_accept_requests(page):
    _load(page)
    page.locator("#enable-control").click()
    trigger = _outer_trigger(page)
    trigger.click()
    page.wait_for_function("window.__popoverRequest?.reason === 'trigger'")

    assert not _outer(page).evaluate("element => element.matches(':popover-open')")
    assert page.evaluate("window.__popoverRequest") == {
        "nextOpen": True,
        "reason": "trigger",
        "controlled": True,
        "forced": False,
    }

    page.locator("#accept").click()
    trigger.click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")
    requests = page.evaluate("window.__popoverRequests")
    page.evaluate("Alpine.$data(document.body).open = false")
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")
    assert page.evaluate("window.__popoverRequests") == requests


def test_controlled_owner_reconciles_external_native_show_and_hide(page):
    _load(page)
    page.locator("#enable-control").click()
    surface = _outer(page)

    surface.evaluate("element => element.showPopover()")
    page.wait_for_function("window.__popoverRequest?.reason === 'native'")
    assert surface.evaluate("element => element.matches(':popover-open')") is False
    assert page.evaluate("window.__popoverRequest") == {
        "nextOpen": True,
        "reason": "native",
        "controlled": True,
        "forced": False,
    }

    page.locator("#force-open").click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")
    page.evaluate("window.__popoverRequest = null")
    surface.evaluate("element => element.hidePopover()")
    page.wait_for_function("window.__popoverRequest?.reason === 'native'")

    assert surface.evaluate("element => element.matches(':popover-open')") is True
    assert page.evaluate("window.__popoverRequest") == {
        "nextOpen": False,
        "reason": "native",
        "controlled": True,
        "forced": False,
    }


def test_nested_popover_owns_escape_before_its_parent(page):
    _load(page)
    _outer_trigger(page).click()
    nested_trigger = page.locator('[aria-controls="nested-popover"]')
    nested_trigger.click()
    page.wait_for_function(
        """() => document.querySelector('#europa-popover').matches(':popover-open')
          && document.querySelector('#nested-popover').matches(':popover-open')"""
    )

    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 2
    page.evaluate("Alpine.$data(document.body).placement = 'top-end'")
    page.wait_for_function("document.querySelector('#europa-popover').dataset.placement === 'top-end'")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#nested-popover').matches(':popover-open')")
    assert _outer(page).evaluate("element => element.matches(':popover-open')")
    assert nested_trigger.evaluate("element => element === document.activeElement")

    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")
    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 0


def test_closing_parent_force_closes_its_logical_child(page):
    _load(page)
    outer_trigger = _outer_trigger(page)
    outer_trigger.click()
    nested_trigger = page.locator('[aria-controls="nested-popover"]')
    nested_trigger.click()
    page.wait_for_function(
        """() => document.querySelector('#europa-popover').matches(':popover-open')
          && document.querySelector('#nested-popover').matches(':popover-open')"""
    )

    outer_trigger.click()
    page.wait_for_function(
        """() => !document.querySelector('#europa-popover').matches(':popover-open')
          && !document.querySelector('#nested-popover').matches(':popover-open')"""
    )

    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 0


def test_one_outside_pointer_gesture_dismisses_only_the_top_popover(page):
    _load(page)
    _outer_trigger(page).click()
    nested = page.locator("#nested-popover")
    page.locator('[aria-controls="nested-popover"]').click()
    page.wait_for_function("document.querySelector('#nested-popover').matches(':popover-open')")

    page.locator("#outside").click()
    page.wait_for_function("!document.querySelector('#nested-popover').matches(':popover-open')")

    assert _outer(page).evaluate("element => element.matches(':popover-open')") is True
    assert nested.evaluate("element => element.matches(':popover-open')") is False


def test_open_shadow_root_uses_composed_paths_and_releases_both_scopes(page):
    errors = _load(page)
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")
    page.evaluate(
        """() => {
          const nestedHost = document.querySelector('#nested-popover')
            .closest('[data-citry-popover-host]');
          nestedHost.id = 'shadow-mount';
          const root = nestedHost.attachShadow({ mode: 'open' });
          root.innerHTML = `
            <button id="shadow-trigger" type="button">Shadow trigger</button>
            <div id="shadow-surface">Shadow surface</div>
          `;
          const trigger = root.querySelector('#shadow-trigger');
          const surface = root.querySelector('#shadow-surface');
          const runtime = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          const coordinator = runtime.coordinatorFor(surface);
          let open = true;
          let dismissals = 0;
          let forced = null;
          const layer = {
            surface,
            trigger,
            isOpen: () => open,
            requestDismiss: () => {
              dismissals += 1;
              open = false;
              coordinator.unregister(layer);
            },
            forceClose: (reason) => {
              forced = reason;
              open = false;
              coordinator.unregister(layer);
            },
          };
          if (!coordinator.register(layer)) {
            throw new Error('ShadowRoot test layer was ineligible.');
          }
          window.__shadowLayer = {
            get dismissals() { return dismissals; },
            get forced() { return forced; },
            get open() { return open; },
          };
        }"""
    )

    page.locator("#ocean-depth").dispatch_event("pointerdown")
    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 2
    assert page.evaluate("window.__shadowLayer.dismissals") == 0

    _outer_trigger(page).click()
    page.wait_for_function(
        """() => !window.__shadowLayer.open
          && !document.querySelector('#europa-popover').matches(':popover-open')
          && window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length === 0"""
    )
    assert page.evaluate("window.__shadowLayer.forced") == "ancestor"
    runtime = page.evaluate(
        """() => {
          const value = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          return {
            activeListenerSets: value.stats.activeListenerSets,
            listening: value.listeners !== null,
          };
        }"""
    )
    assert runtime == {"activeListenerSets": 0, "listening": False}
    assert errors == []


def test_popover_in_open_shadow_root_restores_deep_trigger_focus(page):
    errors = _load(page)
    page.evaluate(
        """() => {
          const mount = document.createElement('div');
          mount.id = 'popover-shadow-host';
          document.body.append(mount);
          const root = mount.attachShadow({ mode: 'open' });
          root.append(document.querySelector('[data-citry-popover-host]'));
          window.__popoverShadowRoot = root;
        }"""
    )
    page.evaluate(
        """() => window.__popoverShadowRoot
          .querySelector('[aria-controls="europa-popover"]')
          .click()"""
    )
    page.wait_for_function(
        """() => window.__popoverShadowRoot
          .querySelector('#europa-popover')
          .matches(':popover-open')"""
    )
    page.evaluate(
        """() => window.__popoverShadowRoot
          .querySelector('#europa-popover')
          .dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Escape',
            bubbles: true,
            composed: true,
          }))"""
    )
    page.wait_for_function(
        """() => !window.__popoverShadowRoot
          .querySelector('#europa-popover')
          .matches(':popover-open')"""
    )

    assert page.evaluate(
        """() => window.__popoverShadowRoot.activeElement
          === window.__popoverShadowRoot.querySelector('[aria-controls="europa-popover"]')"""
    )
    assert errors == []


def test_escape_microtask_does_not_dismiss_a_reregistered_layer(page):
    _load(page)
    result = page.evaluate(
        """async () => {
          const runtime = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          const trigger = document.createElement('button');
          const surface = document.createElement('div');
          trigger.textContent = 'Generation trigger';
          surface.textContent = 'Generation surface';
          document.body.append(trigger, surface);
          const coordinator = runtime.coordinatorFor(surface);
          let open = true;
          let dismissals = 0;
          const layer = {
            surface,
            trigger,
            isOpen: () => open,
            requestDismiss: () => { dismissals += 1; },
            forceClose: () => { open = false; },
          };
          coordinator.register(layer);
          trigger.addEventListener('keydown', () => {
            coordinator.unregister(layer);
            coordinator.clearSuppression(layer);
            coordinator.register(layer);
          }, { once: true });
          trigger.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Escape',
            bubbles: true,
            composed: true,
          }));
          await Promise.resolve();
          const value = { dismissals, registered: coordinator.layers.includes(layer) };
          coordinator.unregister(layer);
          trigger.remove();
          surface.remove();
          return value;
        }"""
    )

    assert result == {"dismissals": 0, "registered": True}


@pytest.mark.parametrize("mutation", ["hidden", "inert", "display-none", "visibility-hidden"])
def test_surface_structural_invalidation_force_closes_with_truthful_reason(page, mutation):
    _load(page)
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")
    page.evaluate(
        """mutation => {
          const surface = document.querySelector('#europa-popover');
          if (mutation === 'hidden') surface.hidden = true;
          if (mutation === 'inert') surface.inert = true;
          if (mutation === 'visibility-hidden') surface.style.visibility = 'hidden';
          if (mutation === 'display-none') {
            const style = document.createElement('style');
            style.textContent = '.force-display-none { display: none !important; }';
            document.head.append(style);
            surface.classList.add('force-display-none');
          }
        }""",
        mutation,
    )
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")

    assert page.evaluate("window.__popoverRequest") == {
        "nextOpen": False,
        "reason": "ancestor",
        "controlled": False,
        "forced": True,
    }
    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].stats.activeListenerSets") == 0


def test_controlled_native_restore_stays_blocked_under_an_inert_ancestor(page):
    _load(page)
    page.locator("#enable-control").click()
    page.locator("#accept").click()
    page.locator("#force-open").click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")
    page.evaluate(
        """() => document.querySelector('[data-citry-popover-host]')
          .setAttribute('inert', '')"""
    )
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")
    page.evaluate("window.__popoverRequest = null")
    _outer(page).evaluate("element => element.showPopover()")
    page.wait_for_function("window.__popoverRequest?.forced === true")

    assert _outer(page).evaluate("element => element.matches(':popover-open')") is False
    assert page.evaluate("window.__popoverRequest") == {
        "nextOpen": False,
        "reason": "ancestor",
        "controlled": True,
        "forced": True,
    }


def test_known_modal_order_is_not_promoted_by_an_event_in_an_older_modal(page):
    _load(page)
    result = page.evaluate(
        """() => {
          const first = document.createElement('dialog');
          const second = document.createElement('dialog');
          first.innerHTML = '<button type="button">First</button>';
          second.innerHTML = '<button type="button">Second</button><div>Surface</div>';
          document.body.append(first, second);
          first.showModal();
          second.showModal();
          second.querySelector('button').focus();
          const runtime = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          const coordinator = runtime.coordinatorFor(second);
          let open = true;
          let forced = null;
          const layer = {
            trigger: second.querySelector('button'),
            surface: second.querySelector('div'),
            isOpen: () => open,
            requestDismiss: () => {},
            forceClose: (reason) => { forced = reason; open = false; },
          };
          const registered = coordinator.register(layer);
          first.querySelector('button').dispatchEvent(new PointerEvent('pointerdown', {
            bubbles: true,
            composed: true,
          }));
          const eligibleAfterEvent = coordinator.mayOpen(layer);
          first.querySelector('button').focus();
          const eligibleAfterOlderFocus = coordinator.mayOpen(layer);
          coordinator.unregister(layer);
          second.close();
          first.close();
          first.remove();
          second.remove();
          return { registered, eligibleAfterEvent, eligibleAfterOlderFocus, forced };
        }"""
    )

    assert result == {
        "registered": True,
        "eligibleAfterEvent": True,
        "eligibleAfterOlderFocus": True,
        "forced": None,
    }


def test_synchronous_modal_close_and_reopen_advances_its_generation(page):
    _load(page)
    result = page.evaluate(
        """() => {
          const first = document.createElement('dialog');
          const second = document.createElement('dialog');
          first.innerHTML = '<button type="button">First</button><div>First surface</div>';
          second.innerHTML = '<button type="button">Second</button><div>Second surface</div>';
          document.body.append(first, second);
          first.showModal();
          second.showModal();
          second.querySelector('button').focus();
          const runtime = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          const coordinator = runtime.coordinatorFor(second);
          let secondOpen = true;
          let secondForced = null;
          const secondLayer = {
            trigger: second.querySelector('button'),
            surface: second.querySelector('div'),
            isOpen: () => secondOpen,
            requestDismiss: () => {},
            forceClose: (reason) => {
              secondForced = reason;
              secondOpen = false;
              coordinator.unregister(secondLayer);
            },
          };
          coordinator.register(secondLayer);

          first.close();
          first.showModal();
          const firstLayer = {
            trigger: first.querySelector('button'),
            surface: first.querySelector('div'),
            isOpen: () => false,
            requestDismiss: () => {},
            forceClose: () => {},
          };
          const firstEligible = coordinator.mayOpen(firstLayer);
          const secondEligible = coordinator.mayOpen(secondLayer);
          first.close();
          second.close();
          first.remove();
          second.remove();
          return { firstEligible, secondEligible, secondForced };
        }"""
    )

    assert result == {
        "firstEligible": True,
        "secondEligible": False,
        "secondForced": "modal",
    }


def test_modal_eligibility_requires_the_trigger_inside_the_modal(page):
    _load(page)
    result = page.evaluate(
        """() => {
          const dialog = document.createElement('dialog');
          const outsideTrigger = document.createElement('button');
          dialog.innerHTML = '<div>Portalled surface</div>';
          document.body.append(outsideTrigger, dialog);
          dialog.showModal();
          const runtime = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          const coordinator = runtime.coordinatorFor(dialog);
          const layer = {
            trigger: outsideTrigger,
            surface: dialog.querySelector('div'),
            isOpen: () => true,
            requestDismiss: () => {},
            forceClose: () => {},
          };
          const eligible = coordinator.mayOpen(layer);
          const reason = coordinator.blockedReason(layer);
          dialog.close();
          dialog.remove();
          outsideTrigger.remove();
          return { eligible, reason };
        }"""
    )

    assert result == {"eligible": False, "reason": "modal"}


def test_modal_dialog_suppresses_outside_layer_but_allows_and_closes_inside_layer(page):
    errors = _load(page)
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")

    page.evaluate(
        """() => {
          const dialog = document.createElement('dialog');
          dialog.id = 'modal-owner';
          dialog.innerHTML = '<button id="modal-focus" type="button">Modal focus</button>';
          document.body.append(dialog);
          dialog.showModal();
          dialog.querySelector('#modal-focus').focus();
        }"""
    )
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")

    _outer_trigger(page).evaluate("element => element.click()")
    page.wait_for_timeout(50)
    assert _outer(page).evaluate("element => element.matches(':popover-open')") is False

    page.evaluate(
        """() => document.querySelector('#modal-owner').append(
          document.querySelector('[data-citry-popover-host]'),
        )"""
    )
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")

    page.evaluate("document.querySelector('#modal-owner').close()")
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")
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


def test_modal_in_unrelated_open_shadow_root_suppresses_document_layer(page):
    errors = _load(page)
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")

    page.evaluate(
        """() => {
          const host = document.createElement('div');
          document.body.append(host);
          const root = host.attachShadow({ mode: 'open' });
          root.innerHTML = `
            <dialog id="shadow-modal">
              <button id="shadow-modal-focus" type="button">Modal focus</button>
            </dialog>
          `;
          const dialog = root.querySelector('#shadow-modal');
          dialog.showModal();
          root.querySelector('#shadow-modal-focus').focus();
          window.__shadowModal = dialog;
        }"""
    )
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")

    page.evaluate("window.__shadowModal.close()")
    page.wait_for_function("window[Symbol.for('citry-ui:anchored-layer-runtime')].stats.activeListenerSets === 0")
    assert errors == []


def test_reactive_placement_and_match_width_update_geometry(page):
    _load(page)
    page.locator("#configure").click()
    trigger = _outer_trigger(page)
    trigger.click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")

    surface = _outer(page)
    assert surface.get_attribute("data-placement") == "top-end"
    assert surface.get_attribute("data-match-width") == ""
    geometry = page.evaluate(
        """() => {
          const trigger = document.querySelector('[aria-controls="europa-popover"]');
          const popover = document.querySelector('#europa-popover');
          const triggerRect = trigger.getBoundingClientRect();
          const popoverRect = popover.getBoundingClientRect();
          return {
            triggerWidth: triggerRect.width,
            popoverWidth: popoverRect.width,
            positionArea: getComputedStyle(popover).positionArea,
            anchorName: getComputedStyle(trigger).getPropertyValue("anchor-name"),
            positionAnchor: getComputedStyle(popover).getPropertyValue("position-anchor"),
          };
        }"""
    )
    assert geometry["popoverWidth"] >= geometry["triggerWidth"] - 1
    assert geometry["positionArea"] in {"block-start span-inline-start", "end span-start"}
    assert geometry["anchorName"].startswith("--_cui-popover-anchor-ref-")
    assert geometry["positionAnchor"] == geometry["anchorName"]


def test_closing_last_layer_removes_shared_document_listeners(page):
    _load(page)
    _outer_trigger(page).click()
    page.wait_for_function("document.querySelector('#europa-popover').matches(':popover-open')")
    page.get_by_role("button", name="Close", exact=True).click()
    page.wait_for_function("!document.querySelector('#europa-popover').matches(':popover-open')")

    runtime = page.evaluate(
        """() => {
          const value = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          return { layers: value.layers.length, listening: value.listeners !== null };
        }"""
    )
    assert runtime == {"layers": 0, "listening": False}


def test_correlated_rerender_retains_open_state_edits_and_one_layer(
    page,
    serve_citry_ui_live,
):
    app, html = _popover_events_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function(
        "document.querySelector('[data-popover-specimen] [data-citry-popover-host]')"
        ".hasAttribute('data-citry-popover-initialized')"
    )
    page.get_by_role("button", name="Inspect survey").click()
    page.wait_for_function("document.querySelector('#survey-popover').matches(':popover-open')")
    note = page.locator("#survey-note")
    note.fill("Retained note")
    page.evaluate("window.__popoverRoot = document.querySelector('[data-citry-popover-host]')")

    page.evaluate("() => Citry.events.send(document.querySelector('.advance-popover'), 'advance', {})")
    page.wait_for_function("document.querySelector('#survey-popover')?.dataset.placement === 'top-end'")

    assert page.evaluate("document.querySelector('[data-citry-popover-host]') === window.__popoverRoot") is True
    assert page.locator("#survey-popover").evaluate("element => element.matches(':popover-open')") is True
    assert note.input_value() == "Retained note"
    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 1
    assert page.get_by_role("heading", name="Survey step 1").count() == 1
