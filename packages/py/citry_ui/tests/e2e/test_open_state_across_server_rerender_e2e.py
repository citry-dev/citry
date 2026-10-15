"""
Open overlays follow the server's `open` input and stay open when a server
event re-renders the component that contains them without removing them.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e

# Each component's owner template. The uncontrolled branch passes the
# server's `open` (when the component has one) and `disabled` inputs and logs
# every `onOpenChange` call; the controlled branch drives `open` from the
# owner's Vue data instead. The overlay's own markup never changes between
# renders; only the owner's step counter and the server inputs do.
_TEMPLATES: dict[str, str] = {
    "chover_card": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CHoverCard
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <a href="#card" c-bind="activator_attrs">Open overlay</a>
              </c-fill>
              <c-fill name="default">Card body</c-fill>
            </c-CHoverCard>
          </c-if>
          <c-else>
            <c-CHoverCard
              c-open="server_open"
              c-disabled="disabled"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <a href="#card" c-bind="activator_attrs">Open overlay</a>
              </c-fill>
              <c-fill name="default">Card body</c-fill>
            </c-CHoverCard>
          </c-else>
        </div>
      </section>
    """,
    "cselect": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CSelect
              c-options="select_options"
              placeholder="Pick one"
              c-trigger_attrs="{'aria-label': 'Open overlay'}"
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            />
          </c-if>
          <c-else>
            <c-CSelect
              c-options="select_options"
              placeholder="Pick one"
              c-trigger_attrs="{'aria-label': 'Open overlay'}"
              c-open="server_open"
              c-disabled="disabled"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            />
          </c-else>
        </div>
      </section>
    """,
    "cmulti_select": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CMultiSelect
              c-options="multi_select_options"
              placeholder="Pick some"
              c-trigger_attrs="{'aria-label': 'Open overlay'}"
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            />
          </c-if>
          <c-else>
            <c-CMultiSelect
              c-options="multi_select_options"
              placeholder="Pick some"
              c-trigger_attrs="{'aria-label': 'Open overlay'}"
              c-open="server_open"
              c-disabled="disabled"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            />
          </c-else>
        </div>
      </section>
    """,
    "ccombobox": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CCombobox
              c-options="combobox_options"
              c-input_attrs="{'aria-label': 'Open overlay'}"
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            />
          </c-if>
          <c-else>
            <c-CCombobox
              c-options="combobox_options"
              c-input_attrs="{'aria-label': 'Open overlay'}"
              c-open="server_open"
              c-disabled="disabled"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            />
          </c-else>
        </div>
      </section>
    """,
    "ccascader": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CCascader
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            >
              <c-CCascaderOption value="earth" label="Earth">
                <c-CCascaderOption value="north" label="North" />
              </c-CCascaderOption>
            </c-CCascader>
          </c-if>
          <c-else>
            <c-CCascader
              c-open="server_open"
              c-disabled="disabled"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            >
              <c-CCascaderOption value="earth" label="Earth">
                <c-CCascaderOption value="north" label="North" />
              </c-CCascaderOption>
            </c-CCascader>
          </c-else>
        </div>
      </section>
    """,
    "ccolor_picker": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CColorPicker
              label="Accent"
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            />
          </c-if>
          <c-else>
            <c-CColorPicker
              label="Accent"
              c-open="server_open"
              c-disabled="disabled"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            />
          </c-else>
        </div>
      </section>
    """,
    "cdate_picker": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CDatePicker
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            />
          </c-if>
          <c-else>
            <c-CDatePicker
              c-disabled="disabled"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            />
          </c-else>
        </div>
      </section>
    """,
    "cdate_range": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CDateRange
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            />
          </c-if>
          <c-else>
            <c-CDateRange
              c-disabled="disabled"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            />
          </c-else>
        </div>
      </section>
    """,
    "ctime_picker": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CTimePicker
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            />
          </c-if>
          <c-else>
            <c-CTimePicker
              c-disabled="disabled"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            />
          </c-else>
        </div>
      </section>
    """,
    "cdialog": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CDialog
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
              </c-fill>
              <c-fill name="title">Overlay dialog</c-fill>
              <c-fill name="default">Dialog body</c-fill>
            </c-CDialog>
          </c-if>
          <c-else>
            <c-CDialog
              c-open="server_open"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
              </c-fill>
              <c-fill name="title">Overlay dialog</c-fill>
              <c-fill name="default">Dialog body</c-fill>
            </c-CDialog>
          </c-else>
        </div>
      </section>
    """,
    "cpopover": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CPopover
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
              </c-fill>
              <c-fill name="title">Overlay popover</c-fill>
              <c-fill name="default">Popover body</c-fill>
            </c-CPopover>
          </c-if>
          <c-else>
            <c-CPopover
              c-open="server_open"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton c-attrs="activator_attrs">Open overlay</c-CButton>
              </c-fill>
              <c-fill name="title">Overlay popover</c-fill>
              <c-fill name="default">Popover body</c-fill>
            </c-CPopover>
          </c-else>
        </div>
      </section>
    """,
    "cmenu": """
      <section>
        <output id="owner-step">{{ step }}</output>
        <button
          id="advance-owner"
          type="button"
          @c-click="advance"
        >Advance</button>
        <button
          id="open-on-server"
          type="button"
          @c-click="open_on_server"
        >Open on server</button>
        <button
          id="close-on-server"
          type="button"
          @c-click="close_on_server"
        >Close on server</button>
        <button
          id="disable-on-server"
          type="button"
          @c-click="disable_on_server"
        >Disable on server</button>
        <div id="overlay-slot">
          <c-if cond="controlled">
            <c-CMenu
              :open="clientOpen"
              :onOpenChange="(open, detail) => {
                  window.__openChanges.push({ open, reason: detail?.reason });
                  clientOpen = open;
                }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <button type="button" c-bind="activator_attrs">Open overlay</button>
              </c-fill>
              <c-fill name="default">
                <c-CMenuItem value="one">One</c-CMenuItem>
              </c-fill>
            </c-CMenu>
          </c-if>
          <c-else>
            <c-CMenu
              c-open="server_open"
              c-disabled="disabled"
              :onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <button type="button" c-bind="activator_attrs">Open overlay</button>
              </c-fill>
              <c-fill name="default">
                <c-CMenuItem value="one">One</c-CMenuItem>
              </c-fill>
            </c-CMenu>
          </c-else>
        </div>
      </section>
    """,
}

# How a user opens each component, and the element that is the open popup.
# Each check reads the popup itself, so an expanded trigger alone does not
# count as open.
_OPENING: dict[str, tuple[str, str]] = {
    "chover_card": ("focus", ".cui-hover-card"),
    "cselect": ("click", ".cui-select__popup"),
    "cmulti_select": ("click", ".cui-multi-select__popup"),
    "ccombobox": ("keyboard", '[data-citry-ui-part="popup"]'),
    "ccascader": ("first-button", '[data-citry-ui-part="popup"]'),
    "ccolor_picker": ("first-button", '[data-citry-ui-part="popup"]'),
    "cdate_picker": ("first-button", ".cui-date-picker__popover"),
    "cdate_range": ("first-button", ".cui-date-range__popover"),
    "ctime_picker": ("first-button", ".cui-time-picker__popover"),
    "cdialog": ("button", "dialog"),
    "cpopover": ("button", ".cui-popover"),
    "cmenu": ("button", "[role=menu]"),
}

# Components whose server render takes an `open` input, and those that take
# `disabled`.
_SERVER_OPEN = [name for name in _OPENING if name not in {"cdate_picker", "cdate_range", "ctime_picker"}]
_DISABLED = [name for name in _OPENING if name not in {"cdialog", "cpopover"}]

# The reason each component reports when disabling closes it. CSelect and
# CMultiSelect already report a forced "ancestor" close when they are
# disabled while open; the others use "disabled", as CMenu does.
_DISABLED_REASON = {name: "ancestor" if name in {"cselect", "cmulti_select"} else "disabled" for name in _DISABLED}

# A popup is open when it is an open dialog, or a showing popover or popup
# part that is not hidden. A popover left in the top layer with `hidden` set
# is not visible, so it does not count.
_IS_OPEN = """selector => {
  const popup = document.querySelector('#overlay-slot ' + selector);
  if (!popup) return false;
  if (popup.tagName === 'DIALOG') return popup.open;
  if (popup.hidden) return false;
  return popup.hasAttribute('popover') ? popup.matches(':popover-open') : true;
}"""


def _owner_page(component: str, *, controlled: bool = False) -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-open-state-rerender-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class OverlayOwner(Component):
        citry = app

        class Kwargs:
            step: int = 0
            server_open: bool = False
            disabled: bool = False
            controlled: bool = False

        class State(Kwargs):
            pass

        class Events:
            # Every event re-renders the owner with the next step, so the test
            # can wait for the new render by its counter.
            def advance(self, state: Any) -> OverlayOwner:
                return _next(state)

            def open_on_server(self, state: Any) -> OverlayOwner:
                return _next(state, server_open=True)

            def close_on_server(self, state: Any) -> OverlayOwner:
                return _next(state, server_open=False)

            def disable_on_server(self, state: Any) -> OverlayOwner:
                return _next(state, disabled=True)

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {
                "step": kwargs.step,
                "server_open": kwargs.server_open,
                "disabled": kwargs.disabled,
                "controlled": kwargs.controlled,
                "select_options": [citry_ui.CSelectOption("a", "Alpha"), citry_ui.CSelectOption("b", "Beta")],
                "multi_select_options": [
                    citry_ui.CMultiSelectOption("a", "Alpha"),
                    citry_ui.CMultiSelectOption("b", "Beta"),
                ],
                "combobox_options": [citry_ui.CComboboxOption("a", "Alpha"), citry_ui.CComboboxOption("b", "Beta")],
            }

        template = _TEMPLATES[component]
        js = """
          $component({
            data() {
              return { clientOpen: false };
            },
            mounted() {
              window.__owner = this;
            },
          });
        """

    def _next(state: Any, **changes: Any) -> OverlayOwner:
        values = {
            "step": state.step + 1,
            "server_open": state.server_open,
            "disabled": state.disabled,
            "controlled": state.controlled,
        }
        values.update(changes)
        return OverlayOwner(**values)

    class Page(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"controlled": controlled}

        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body>
              <c-overlay-owner c-controlled="controlled" />
              <c-js />
            </body>
          </html>
        """
        js = """
          $component({
            data() {
              window.__openChanges = [];
              return {};
            },
          });
        """

    return app, str(Page())


def _is_open(page: Any, component: str) -> bool:
    return bool(page.evaluate(_IS_OPEN, _OPENING[component][1]))


def _wait_open(page: Any, component: str, *, open_: bool = True) -> None:
    page.wait_for_function(
        f"selector => ({_IS_OPEN})(selector) === {'true' if open_ else 'false'}",
        arg=_OPENING[component][1],
    )


def _open_by_user(page: Any, component: str) -> None:
    opening = _OPENING[component][0]
    if opening == "focus":
        page.get_by_text("Open overlay").focus()
    elif opening == "click":
        page.get_by_role("combobox", name="Open overlay").click()
    elif opening == "keyboard":
        page.get_by_role("combobox", name="Open overlay").click()
        page.keyboard.press("ArrowDown")
    elif opening == "button":
        page.get_by_role("button", name="Open overlay").click()
    else:
        page.locator("#overlay-slot button").first.click()
    _wait_open(page, component)


def _load(page: Any, serve_citry_ui_live: Any, wait_for_citry_ready: Any, component: str, **options: Any) -> None:
    app, html = _owner_page(component, **options)
    page.goto(serve_citry_ui_live(app, html) + "/")
    wait_for_citry_ready()


def _server_event(page: Any, send_event: Any, button: str, handler: str, step: int) -> None:
    # A script click sends the event without pointer or focus changes that
    # would close the overlay on their own.
    send_event(lambda: page.locator(button).evaluate("element => element.click()"), handler=handler)
    page.wait_for_function(f"document.querySelector('#owner-step').textContent === '{step}'")


def _rerender_while_open(page: Any, component: str, send_event: Any, wait_for_count: Any) -> None:
    # Hold the server's answer until the overlay is known to be open, so the
    # re-render always lands on an open overlay. Only the call is held: the
    # render may also fetch new component definitions under /ext/events/.
    held: list[Any] = []
    page.route("**/ext/events/call", lambda route: held.append(route))
    page.locator("#advance-owner").evaluate("element => element.click()")
    wait_for_count(held, 1)
    assert _is_open(page, component)
    send_event(lambda: held[0].continue_(), handler="advance")
    page.unroute("**/ext/events/call")
    page.wait_for_function("document.querySelector('#owner-step').textContent === '1'")


@pytest.mark.parametrize("component", list(_OPENING))
def test_server_rerender_that_keeps_an_open_overlay_keeps_it_open(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    wait_for_count: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A server event that re-renders the owner leaves an open overlay open and reports no close."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    _open_by_user(page, component)
    opened = page.evaluate("window.__openChanges")
    assert [change["open"] for change in opened] == [True]

    _rerender_while_open(page, component, send_event, wait_for_count)
    # A close scheduled by the re-render would run on a timer or a frame.
    settle_timers()

    assert _is_open(page, component), f"{component} closed when a server re-render kept it"
    assert page.evaluate("window.__openChanges") == opened


@pytest.mark.parametrize("component", _SERVER_OPEN)
def test_server_open_input_change_opens_and_closes_the_overlay(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A re-render that changes the server's `open` input opens or closes the overlay to match."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    assert not _is_open(page, component)

    _server_event(page, send_event, "#open-on-server", "open_on_server", 1)
    _wait_open(page, component)

    _server_event(page, send_event, "#close-on-server", "close_on_server", 2)
    _wait_open(page, component, open_=False)
    settle_timers()
    # The owner changed its own input, so neither change is reported back.
    assert page.evaluate("window.__openChanges") == []


@pytest.mark.parametrize("component", list(_OPENING))
def test_client_open_binding_still_controls_the_overlay_after_a_rerender(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    wait_for_count: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A client `:open` binding keeps control across a server re-render that lands while the overlay is open."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component, controlled=True)
    _open_by_user(page, component)
    _rerender_while_open(page, component, send_event, wait_for_count)
    settle_timers()
    assert _is_open(page, component), f"{component} closed when a server re-render kept it"

    page.evaluate("window.__owner.clientOpen = false")
    _wait_open(page, component, open_=False)
    settle_timers()
    # Only the user's open was a request; the owner's own close is not reported back.
    assert [change["open"] for change in page.evaluate("window.__openChanges")] == [True]


@pytest.mark.parametrize("component", _DISABLED)
def test_server_disable_closes_an_open_overlay_and_reports_it(
    page: Any,
    serve_citry_ui_live: Any,
    wait_for_citry_ready: Any,
    send_event: Any,
    settle_timers: Any,
    component: str,
) -> None:
    """A re-render that disables an open overlay closes it and reports the close to `onOpenChange`."""
    _load(page, serve_citry_ui_live, wait_for_citry_ready, component)
    _open_by_user(page, component)

    opened = page.evaluate("window.__openChanges")

    _server_event(page, send_event, "#disable-on-server", "disable_on_server", 1)
    settle_timers()

    assert not _is_open(page, component), f"{component} stayed open after the server disabled it"
    assert page.evaluate("window.__openChanges") == [*opened, {"open": False, "reason": _DISABLED_REASON[component]}]
