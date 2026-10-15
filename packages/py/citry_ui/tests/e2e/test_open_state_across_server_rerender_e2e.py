"""Open overlays stay open when a server event re-renders their owner and keeps them."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e

# Every case logs its `onOpenChange` calls, so the test can check that the
# re-render neither closed the overlay nor reported a close.
_LOG = ':onOpenChange="(open, detail) => window.__openChanges.push({ open, reason: detail?.reason })"'

# Each case is the component's markup and how a user opens it. The markup is
# kept minimal: only what the component needs to render and open.
_CASES: dict[str, tuple[str, str]] = {
    "chover_card": (
        f'<c-CHoverCard {_LOG}><c-fill name="activator" data="{{ activator_attrs }}">'
        '<a href="#card" c-bind="activator_attrs">Open overlay</a></c-fill>'
        '<c-fill name="default">Card body</c-fill></c-CHoverCard>',
        "focus",
    ),
    "cselect": (
        '<c-CSelect c-options="select_options" placeholder="Pick one"'
        f" c-trigger_attrs=\"{{'aria-label':'Open overlay'}}\" {_LOG} />",
        "click",
    ),
    "cmulti_select": (
        '<c-CMultiSelect c-options="multi_select_options" placeholder="Pick some"'
        f" c-trigger_attrs=\"{{'aria-label':'Open overlay'}}\" {_LOG} />",
        "click",
    ),
    "ccombobox": (
        f"<c-CCombobox c-options=\"combobox_options\" c-input_attrs=\"{{'aria-label':'Open overlay'}}\" {_LOG} />",
        "keyboard",
    ),
    "ccascader": (
        f'<c-CCascader {_LOG}><c-CCascaderOption value="earth" label="Earth">'
        '<c-CCascaderOption value="north" label="North" /></c-CCascaderOption></c-CCascader>',
        "first-button",
    ),
    "ccolor_picker": (f'<c-CColorPicker label="Accent" {_LOG} />', "first-button"),
    "cdate_picker": (f"<c-CDatePicker {_LOG} />", "first-button"),
    "cdate_range": (f"<c-CDateRange {_LOG} />", "first-button"),
    "ctime_picker": (f"<c-CTimePicker {_LOG} />", "first-button"),
}

# The components mark an open overlay differently: a showing popover, an open
# dialog, a `data-open` attribute, or an expanded trigger.
_IS_OPEN = """() => !!document.querySelector(
  '#overlay-slot :popover-open, #overlay-slot dialog[open], '
  + '#overlay-slot [data-open], #overlay-slot [aria-expanded=true]'
)"""


def _owner_page(markup: str) -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-open-state-rerender-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class OverlayOwner(Component):
        citry = app

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Events:
            def advance(self, state: Any) -> OverlayOwner:
                return OverlayOwner(step=state.step + 1)

        # The overlay's own markup does not change between renders; only the
        # owner's step counter does.
        template = (
            '<section><output id="owner-step">{{ step }}</output>'
            '<button id="advance-owner" type="button" @c-click="advance">Advance</button>'
            '<div id="overlay-slot">' + markup + "</div></section>"
        )

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {
                "step": kwargs.step,
                "select_options": [citry_ui.CSelectOption("a", "Alpha"), citry_ui.CSelectOption("b", "Beta")],
                "multi_select_options": [
                    citry_ui.CMultiSelectOption("a", "Alpha"),
                    citry_ui.CMultiSelectOption("b", "Beta"),
                ],
                "combobox_options": [citry_ui.CComboboxOption("a", "Alpha"), citry_ui.CComboboxOption("b", "Beta")],
            }

    class Page(Component):
        citry = app
        js = """
          $component({data(){window.__openChanges=[];return{};}});
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body><c-overlay-owner /><c-js /></body>
          </html>
        """

    return app, str(Page())


@pytest.mark.parametrize("component", list(_CASES))
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
    markup, opening = _CASES[component]
    app, html = _owner_page(markup)
    page.goto(serve_citry_ui_live(app, html) + "/")
    wait_for_citry_ready()

    if opening == "focus":
        page.get_by_text("Open overlay").focus()
    elif opening == "click":
        page.get_by_role("combobox", name="Open overlay").click()
    elif opening == "keyboard":
        page.get_by_role("combobox", name="Open overlay").click()
        page.keyboard.press("ArrowDown")
    else:
        page.locator("#overlay-slot button").first.click()
    page.wait_for_function(_IS_OPEN)
    opened = page.evaluate("window.__openChanges")
    assert [change["open"] for change in opened] == [True]

    # Hold the server's answer until the overlay is known to be open, so the
    # re-render always lands on an open overlay. A script click on the owner's
    # button sends the event without pointer or focus changes that would close
    # the overlay on their own.
    held: list[Any] = []
    page.route("**/ext/events/call", lambda route: held.append(route))
    page.locator("#advance-owner").evaluate("element => element.click()")
    wait_for_count(held, 1)
    assert page.evaluate(_IS_OPEN)
    send_event(lambda: held[0].continue_(), handler="advance")
    page.unroute("**/ext/events/call")
    page.wait_for_function("document.querySelector('#owner-step').textContent === '1'")
    # A close scheduled by the re-render would run on a timer or a frame.
    settle_timers()

    assert page.evaluate(_IS_OPEN), f"{component} closed when a server re-render kept it"
    assert page.evaluate("window.__openChanges") == opened
