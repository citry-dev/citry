"""Cross-browser behavior tests for CDrawer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body x-data="{
              open: false, accept: true, placement: 'inline-end', size: 'md',
              scroll: 'body', dismissible: true, requests: []
            }">
              <c-CDrawer
                id="field-drawer"
                $c-props="{
                  open,
                  placement,
                  size,
                  scroll,
                  dismissible,
                  onOpenChange: (next, detail) => {
                    requests.push([
                      next, detail.reason, detail.controlled, detail.returnValue, detail.forced
                    ]);
                    if (accept) open = next;
                  },
                }"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Edit field note</c-CButton>
                </c-fill>
                <c-fill name="title">Field note</c-fill>
                <c-fill name="description">Update this observation.</c-fill>
                <c-fill name="default">
                  <label for="drawer-name">Name</label>
                  <input id="drawer-name" value="Aurora" autofocus />
                  <form method="dialog">
                    <button type="submit" value="charted">Chart</button>
                  </form>
                </c-fill>
                <c-fill name="actions" data="{ close_attrs }">
                  <c-CButton variant="outline" c-attrs="close_attrs">Cancel</c-CButton>
                  <c-CButton c-attrs="save_attrs">Save</c-CButton>
                </c-fill>
              </c-CDrawer>
              <c-CDrawer
                id="native-drawer"
                $c-props="{onOpenChange: (next, detail) => requests.push([
                  next, detail.reason, detail.controlled, detail.returnValue, detail.forced
                ])}"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Native close drawer</c-CButton>
                </c-fill>
                <c-fill name="title">Native close path</c-fill>
                <c-fill name="default">
                  <form method="dialog"><button type="submit" value="done">Complete native</button></form>
                </c-fill>
              </c-CDrawer>
              <button id="toggle-accept" type="button" @click="accept = !accept">Toggle accept</button>
              <button id="force-open" type="button" @click="open = true">Force open</button>
              <button id="force-close" type="button" @click="open = false">Force close</button>
              <button id="configure-sheet" type="button"
                @click="placement = 'block-end'; size = 'lg'; scroll = 'drawer'">Configure sheet</button>
              <output id="requests" x-text="JSON.stringify(requests)"></output>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {"save_attrs": {"id": "save-drawer"}}

    return str(Page())


def _load(page: Any) -> tuple[list[str], list[str]]:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("[data-citry-drawer-initialized]")
    return console_errors, page_errors


def _trigger(page: Any):
    return page.get_by_role("button", name="Edit field note")


def test_drawer_controlled_open_close_focus_and_form(page: Any) -> None:
    console_errors, page_errors = _load(page)
    trigger = _trigger(page)
    trigger.click()
    page.wait_for_function("document.querySelector('#field-drawer').matches(':modal')")
    drawer = page.locator("#field-drawer")

    assert drawer.get_attribute("data-open") == ""
    assert trigger.get_attribute("aria-expanded") == "true"
    assert page.locator("#drawer-name").evaluate("element => element === document.activeElement") is True
    assert page.evaluate("document.documentElement.style.overflow") == "hidden"
    assert page.evaluate("JSON.parse(document.querySelector('#requests').textContent).at(-1)") == [
        True,
        "trigger",
        True,
        "",
        False,
    ]

    page.get_by_role("button", name="Chart").click()
    page.wait_for_function("!document.querySelector('#field-drawer').open")
    assert page.evaluate("JSON.parse(document.querySelector('#requests').textContent).at(-1)") == [
        False,
        "native",
        True,
        "charted",
        False,
    ]
    page.wait_for_function("document.querySelector('[data-citry-drawer-trigger]') === document.activeElement")
    assert trigger.evaluate("element => element === document.activeElement") is True
    assert page.evaluate("document.documentElement.style.overflow") == ""
    assert console_errors == []
    assert page_errors == []


def test_drawer_uncontrolled_native_form_close_is_not_forced(page: Any) -> None:
    console_errors, page_errors = _load(page)
    page.get_by_role("button", name="Native close drawer").click()
    page.wait_for_function("document.querySelector('#native-drawer').matches(':modal')")
    page.get_by_role("button", name="Complete native").click()
    page.wait_for_function("!document.querySelector('#native-drawer').open")

    assert page.evaluate("JSON.parse(document.querySelector('#requests').textContent).at(-1)") == [
        False,
        "native",
        False,
        "done",
        False,
    ]
    assert console_errors == []
    assert page_errors == []


def test_drawer_declined_request_and_configuration_update(page: Any) -> None:
    console_errors, page_errors = _load(page)
    page.locator("#toggle-accept").click()
    _trigger(page).click()
    assert page.locator("#field-drawer").evaluate("element => element.open") is False
    assert page.evaluate("JSON.parse(document.querySelector('#requests').textContent).at(-1).slice(0, 3)") == [
        True,
        "trigger",
        True,
    ]

    page.locator("#toggle-accept").click()
    page.locator("#configure-sheet").click()
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#field-drawer').open")
    drawer = page.locator("#field-drawer")
    assert drawer.get_attribute("data-placement") == "block-end"
    assert drawer.get_attribute("data-size") == "lg"
    assert drawer.get_attribute("data-scroll") == "drawer"
    assert drawer.evaluate("element => getComputedStyle(element).inlineSize") == "1280px"
    assert console_errors == []
    assert page_errors == []


def test_drawer_external_native_close_is_forced_and_latches_controlled_true(page: Any) -> None:
    console_errors, page_errors = _load(page)
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#field-drawer').matches(':modal')")
    page.locator("body").evaluate("element => { element._x_dataStack[0].accept = false; }")
    page.locator("#field-drawer").evaluate("element => element.close()")
    page.wait_for_function("!document.querySelector('#field-drawer').open")

    assert page.evaluate("JSON.parse(document.querySelector('#requests').textContent).at(-1)") == [
        False,
        "native",
        True,
        "",
        True,
    ]
    page.locator("#configure-sheet").click()
    assert page.locator("#field-drawer").evaluate("element => element.open") is False

    page.locator("#force-close").click()
    page.locator("#force-open").click()
    page.wait_for_function("document.querySelector('#field-drawer').matches(':modal')")
    assert console_errors == []
    assert page_errors == []


def test_drawer_settled_anatomy_fails_closed_and_requires_a_new_open_edge(page: Any) -> None:
    console_errors, page_errors = _load(page)
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#field-drawer').matches(':modal')")
    page.locator("body").evaluate("element => { element._x_dataStack[0].accept = false; }")
    page.locator('[data-citry-ui-part="title"]').first.evaluate(
        "element => element.insertAdjacentHTML('beforeend', '<a href=\"#bad\">bad</a>')"
    )
    page.wait_for_function("!document.querySelector('#field-drawer').open")

    assert page.locator("[data-citry-drawer-initialized]").count() == 1
    assert page.evaluate("JSON.parse(document.querySelector('#requests').textContent).at(-1).slice(0, 3)") == [
        False,
        "ancestor",
        True,
    ]
    assert page.evaluate("JSON.parse(document.querySelector('#requests').textContent).at(-1).at(-1)") is True

    page.locator('[data-citry-ui-part="title"] a').first.evaluate("element => element.remove()")
    page.wait_for_timeout(50)
    assert page.locator("#field-drawer").evaluate("element => element.open") is False
    page.locator("#force-close").click()
    page.locator("#force-open").click()
    page.wait_for_function("document.querySelector('#field-drawer').matches(':modal')")
    assert len(console_errors) == 1
    assert "settled anatomy is invalid" in console_errors[0]
    assert page_errors == []


def test_drawer_escape_action_and_tab_loop(page: Any) -> None:
    console_errors, page_errors = _load(page)
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#field-drawer').open")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#field-drawer').open")
    assert page.evaluate("JSON.parse(document.querySelector('#requests').textContent).at(-1)[1]") == "escape"

    _trigger(page).click()
    page.wait_for_function("document.querySelector('#field-drawer').open")
    page.locator("#save-drawer").focus()
    page.keyboard.press("Tab")
    assert (
        page.get_by_role("button", name="Close", exact=True).evaluate("element => element === document.activeElement")
        is True
    )
    page.get_by_role("button", name="Cancel").click()
    page.wait_for_function("!document.querySelector('#field-drawer').open")
    assert page.evaluate("JSON.parse(document.querySelector('#requests').textContent).at(-1)[1]") == "action"
    assert console_errors == []
    assert page_errors == []


def test_drawer_geometry_rtl_theme_and_accessibility(page: Any) -> None:
    console_errors, page_errors = _load(page)
    page.locator("body").evaluate("element => { element.dir = 'rtl'; element.style.colorScheme = 'dark'; }")
    _trigger(page).click()
    page.wait_for_function("document.querySelector('#field-drawer').open")
    drawer = page.locator("#field-drawer")
    geometry = drawer.evaluate(
        """element => {
          const rect = element.getBoundingClientRect();
          return {left: rect.left, right: rect.right, width: rect.width, viewport: innerWidth};
        }"""
    )
    assert geometry["left"] == 0
    assert geometry["width"] <= geometry["viewport"]
    assert drawer.evaluate("element => getComputedStyle(element).colorScheme") == "dark"

    axe_path = Path("node_modules/axe-core/axe.min.js").resolve()
    assert axe_path.is_file()
    page.add_script_tag(path=str(axe_path))
    violations = page.evaluate(
        """async () => (await axe.run(document)).violations.filter(
          violation => violation.impact === 'serious' || violation.impact === 'critical'
        )"""
    )
    assert violations == []
    assert console_errors == []
    assert page_errors == []
