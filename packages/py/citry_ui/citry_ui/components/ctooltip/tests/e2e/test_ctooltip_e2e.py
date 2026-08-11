"""Browser tests for CTooltip's owned overlay behavior."""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _tooltip_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.space-tooltip) {
            --cui-tooltip-background: rgb(15 35 54);
            --cui-tooltip-foreground: rgb(244 248 251);
            --cui-tooltip-duration: 20ms;
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
                disabled: false,
                placement: 'top',
                label: 'Jupiter moon',
              }"
            >
              <main style="display: flex; gap: 6rem; padding: 220px; min-block-size: 900px">
                <c-CTooltip
                  id="europa-tooltip"
                  text="Jupiter's icy moon"
                  class_="space-tooltip"
                  c-delay="60"
                  c-close_delay="120"
                  $c-props="{
                    open: controlled ? open : undefined,
                    text: label,
                    disabled,
                    placement,
                    onOpenChange: (nextOpen, detail) => {
                      window.__tooltipRequest = {
                        nextOpen,
                        reason: detail.reason,
                        controlled: detail.controlled,
                        forced: detail.forced,
                      };
                      window.__tooltipRequests = (window.__tooltipRequests || 0) + 1;
                      if (accept) open = nextOpen;
                    },
                  }"
                >
                  <c-fill name="activator" data="{ activator_attrs }">
                    <c-CButton c-attrs="activator_attrs">
                      Inspect Europa
                    </c-CButton>
                  </c-fill>
                </c-CTooltip>

                <c-CTooltip
                  id="ganymede-tooltip"
                  text="The Solar System's largest moon"
                  class_="space-tooltip"
                  c-delay="600"
                  c-close_delay="0"
                >
                  <c-fill name="activator" data="{ activator_attrs }">
                    <c-CButton c-attrs="activator_attrs">
                      Inspect Ganymede
                    </c-CButton>
                  </c-fill>
                </c-CTooltip>
              </main>
              <button id="outside" type="button">
                Outside
              </button>
              <button id="enable-control" type="button" @click="controlled = true">
                Control
              </button>
              <button id="accept" type="button" @click="accept = true">
                Accept
              </button>
              <button id="force-open" type="button" @click="open = true">
                Force open
              </button>
              <button id="update" type="button" @click="label = 'Europa has a hidden ocean'">
                Update
              </button>
              <button id="disable" type="button" @click="disabled = true">
                Disable
              </button>
              <button id="place" type="button" @click="placement = 'bottom-end'">
                Place
              </button>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _invalid_tooltip_page(*, wrapper: bool) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = (
            """
              <!doctype html>
              <html lang="en">
                <head><c-css /></head>
                <body>
                  <c-CTooltip text="Europa">
                    <c-fill name="activator" data="{ activator_attrs }">
                      <span>
                        <button type="button" c-bind="activator_attrs">Inspect</button>
                      </span>
                    </c-fill>
                  </c-CTooltip>
                  <c-js />
                </body>
              </html>
            """
            if wrapper
            else """
              <!doctype html>
              <html lang="en">
                <head><c-css /></head>
                <body>
                  <c-CTooltip>
                    <c-fill name="activator" data="{ activator_attrs }">
                      <button type="button" c-bind="activator_attrs">Inspect</button>
                    </c-fill>
                    <c-fill name="default">
                      <a href="#ocean">Interactive help</a>
                    </c-fill>
                  </c-CTooltip>
                  <c-js />
                </body>
              </html>
            """
        )

    return str(Page())


def _tooltip_events_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-tooltip-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class SpecimenTooltip(Component):
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
                return SpecimenTooltip(step=state.step)

        template = """
          <section data-tooltip-specimen>
            <button class="advance-tooltip" type="button" @c-click="advance">
              Advance
            </button>
            <c-CTooltip
              #c-key="'survey-tooltip'"
              id="survey-tooltip"
              c-text="tooltip_text"
              c-placement="placement"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton c-attrs="activator_attrs">Inspect survey</c-CButton>
              </c-fill>
            </c-CTooltip>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {
                "placement": "bottom-end" if kwargs.step else "top",
                "tooltip_text": f"Survey step {kwargs.step}",
            }

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><c-css /></head>
            <body>
              <c-specimen-tooltip />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def _load(page) -> list[str]:
    console_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.set_content(_tooltip_page(), wait_until="load")
    page.wait_for_function(
        """() => {
          const hosts = [...document.querySelectorAll('[data-citry-tooltip-host]')];
          return hosts.length === 2
            && hosts.every((host) => host.hasAttribute('data-citry-tooltip-initialized'));
        }"""
    )
    return console_errors


def _europa(page):
    return page.locator("#europa-tooltip")


def _europa_trigger(page):
    return page.get_by_role("button", name="Inspect Europa")


def test_focus_opens_immediately_and_escape_closes_without_moving_focus(page):
    errors = _load(page)
    trigger = _europa_trigger(page)
    trigger.focus()
    page.wait_for_function("document.querySelector('#europa-tooltip').matches(':popover-open')")

    assert _europa(page).get_attribute("data-open") == ""
    assert trigger.get_attribute("aria-describedby") == "europa-tooltip"
    assert _europa(page).evaluate("element => getComputedStyle(element).backgroundColor") == ("rgb(15, 35, 54)")
    assert page.evaluate("window.__tooltipRequest.reason") == "focus"

    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#europa-tooltip').matches(':popover-open')")
    assert trigger.evaluate("element => element === document.activeElement")
    assert page.evaluate("window.__tooltipRequest.reason") == "escape"

    page.wait_for_timeout(100)
    assert not _europa(page).evaluate("element => element.matches(':popover-open')")
    assert errors == []


def test_structural_safety_force_closes_a_controlled_tooltip_truthfully(page):
    _load(page)
    page.locator("#enable-control").click()
    page.locator("#accept").click()
    page.locator("#force-open").click()
    page.wait_for_function("document.querySelector('#europa-tooltip').matches(':popover-open')")
    page.evaluate(
        """() => document.querySelector('#europa-tooltip')
          .closest('[data-citry-tooltip-host]')
          .setAttribute('hidden', '')"""
    )
    page.wait_for_function("!document.querySelector('#europa-tooltip').matches(':popover-open')")

    assert page.evaluate("window.__tooltipRequest") == {
        "nextOpen": False,
        "reason": "ancestor",
        "controlled": True,
        "forced": True,
    }


def test_hover_delay_surface_bridge_and_departure_close(page):
    _load(page)
    trigger = _europa_trigger(page)
    trigger.hover()
    page.wait_for_timeout(20)
    assert not _europa(page).evaluate("element => element.matches(':popover-open')")
    page.wait_for_function("document.querySelector('#europa-tooltip').matches(':popover-open')")

    _europa(page).hover()
    page.wait_for_timeout(160)
    assert _europa(page).evaluate("element => element.matches(':popover-open')")

    page.locator("#outside").hover()
    page.wait_for_function("!document.querySelector('#europa-tooltip').matches(':popover-open')")
    assert page.evaluate("window.__tooltipRequest.reason") == "pointer-leave"


def test_open_peer_warms_next_tooltip_and_closes_previous(page):
    _load(page)
    _europa_trigger(page).focus()
    page.wait_for_function("document.querySelector('#europa-tooltip').matches(':popover-open')")

    second = page.get_by_role("button", name="Inspect Ganymede")
    started = page.evaluate("performance.now()")
    second.hover()
    page.wait_for_function("document.querySelector('#ganymede-tooltip').matches(':popover-open')")
    page.wait_for_function("!document.querySelector('#europa-tooltip').matches(':popover-open')")
    elapsed = page.evaluate("started => performance.now() - started", started)

    assert elapsed < 300
    assert not _europa(page).evaluate("element => element.matches(':popover-open')")
    assert page.locator("#ganymede-tooltip").evaluate("element => element.matches(':popover-open')")


def test_trigger_press_dismisses_without_preventing_native_activation(page):
    _load(page)
    trigger = _europa_trigger(page)
    trigger.focus()
    page.wait_for_function("document.querySelector('#europa-tooltip').matches(':popover-open')")
    trigger.click()
    page.wait_for_function("!document.querySelector('#europa-tooltip').matches(':popover-open')")

    assert page.evaluate("window.__tooltipRequest.reason") == "press"
    # Tooltip never assigns focus. Pointer activation keeps each browser's
    # native Button focus behavior, which differs in WebKit.
    assert not _europa(page).evaluate("element => element === document.activeElement")


def test_controlled_owner_can_decline_then_accept_requests(page):
    _load(page)
    page.locator("#enable-control").click()
    trigger = _europa_trigger(page)
    trigger.focus()
    page.wait_for_function("window.__tooltipRequest?.reason === 'focus'")

    assert not _europa(page).evaluate("element => element.matches(':popover-open')")
    assert page.evaluate("window.__tooltipRequest") == {
        "nextOpen": True,
        "reason": "focus",
        "controlled": True,
        "forced": False,
    }

    page.locator("#accept").click()
    page.locator("#force-open").click()
    page.wait_for_function("document.querySelector('#europa-tooltip').matches(':popover-open')")
    requests = page.evaluate("window.__tooltipRequests")
    page.evaluate("Alpine.$data(document.body).open = false")
    page.wait_for_function("!document.querySelector('#europa-tooltip').matches(':popover-open')")
    assert page.evaluate("window.__tooltipRequests") == requests


def test_client_text_placement_and_disabled_state_reconcile(page):
    errors = _load(page)
    page.locator("#update").click()
    page.locator("#place").click()

    assert _europa(page).inner_text().strip() == "Europa has a hidden ocean"
    assert _europa(page).get_attribute("data-placement") == "bottom-end"

    _europa_trigger(page).focus()
    page.wait_for_function("document.querySelector('#europa-tooltip').matches(':popover-open')")
    page.locator("#disable").click()
    page.wait_for_function("!document.querySelector('#europa-tooltip').matches(':popover-open')")
    assert errors == []


def test_closing_last_tooltip_removes_shared_document_listeners(page):
    _load(page)
    trigger = _europa_trigger(page)
    trigger.focus()
    page.wait_for_function("document.querySelector('#europa-tooltip').matches(':popover-open')")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#europa-tooltip').matches(':popover-open')")

    runtime = page.evaluate(
        """() => {
          const value = window[Symbol.for('citry-ui:anchored-layer-runtime')];
          return { layers: value.layers.length, listening: value.listeners !== null };
        }"""
    )
    assert runtime == {"layers": 0, "listening": False}


def test_touch_pointer_and_following_focus_do_not_open_visual_tooltip(page):
    _load(page)
    trigger = _europa_trigger(page)
    trigger.dispatch_event("pointerdown", {"pointerType": "touch", "isPrimary": True})
    trigger.focus()
    page.wait_for_timeout(120)

    assert not _europa(page).evaluate("element => element.matches(':popover-open')")


@pytest.mark.parametrize("wrapper", [False, True], ids=["interactive-content", "wrapped-trigger"])
def test_settled_dom_rejects_interactive_content_and_wrapped_activators(page, wrapper):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_invalid_tooltip_page(wrapper=wrapper), wait_until="load")
    page.wait_for_timeout(100)

    assert page.locator("[data-citry-tooltip-initialized]").count() == 0
    assert errors
    assert any("CTooltip" in error or "noninteractive" in error for error in errors)


def test_correlated_rerender_retains_open_state_and_one_layer(page, serve_citry_ui_live):
    app, html = _tooltip_events_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function(
        "document.querySelector('[data-tooltip-specimen] [data-citry-tooltip-host]')"
        ".hasAttribute('data-citry-tooltip-initialized')"
    )
    trigger = page.get_by_role("button", name="Inspect survey")
    trigger.focus()
    page.wait_for_function("document.querySelector('#survey-tooltip').matches(':popover-open')")
    page.evaluate("window.__tooltipRoot = document.querySelector('[data-citry-tooltip-host]')")

    page.evaluate("() => Citry.events.send(document.querySelector('.advance-tooltip'), 'advance', {})")
    page.wait_for_function("document.querySelector('#survey-tooltip')?.dataset.placement === 'bottom-end'")

    assert page.evaluate("document.querySelector('[data-citry-tooltip-host]') === window.__tooltipRoot") is True
    assert page.locator("#survey-tooltip").evaluate("element => element.matches(':popover-open')") is True
    assert page.locator("#survey-tooltip").inner_text().strip() == "Survey step 1"
    assert page.evaluate("window[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == 1
