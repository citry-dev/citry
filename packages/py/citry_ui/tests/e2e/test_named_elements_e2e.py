"""
Browser tests: an element `name` chosen by data does not stop Citry UI overlays.

A browser makes a `form`, `img`, `iframe`, `embed` or `object` with a `name` a
property of `document` that hides the document's built-in member of that name,
so `<form name="activeElement">` makes `document.activeElement` that form. A
page whose data picks such a value could otherwise stop a menu, popover,
dialog or select from opening, moving focus or closing. The page names the
document members the menu, popover, dialog and select read, and each
component must still open and close from the keyboard and the mouse.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component, Markup
from citry_ui import CSelectOption

pytestmark = pytest.mark.e2e

# Document members the menu, popover, dialog and select read, each taken by named elements in the page.
DOCUMENT_MEMBERS = [
    "activeElement",
    "addEventListener",
    "body",
    "createElement",
    "createElementNS",
    "createRange",
    "currentScript",
    "defaultView",
    "documentElement",
    "elementFromPoint",
    "elementsFromPoint",
    "getElementById",
    "getSelection",
    "head",
    "hidden",
    "host",
    "querySelector",
    "querySelectorAll",
    "removeEventListener",
]

# The pages hide `document.querySelector` too, so the test finds elements through `Document.prototype`.
_FIND = "Document.prototype.querySelector.bind(document)"


def _page(names: list[str]) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Named(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"names": names}

        # The template binds each data value to a `name`, the way an app binds a
        # field name, and the elements come before every component script.
        template = """
            <form
              c-for="name in names"
              c-name="name"
            ></form>
            <img
              c-for="name in names"
              c-name="name"
              src="data:,"
            >
        """

    class Page(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {
                "options": [CSelectOption("earth", "Earth"), CSelectOption("mars", "Mars")],
                # Written into the page as HTML, ahead of every component script.
                "named": Markup(str(Named().render())),  # noqa: S704 - Citry rendered and escaped it
            }

        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              {{ named }}
              <main style="padding: 120px">
                <c-CMenu>
                  <c-fill
                    name="activator"
                    data="{ activator_attrs }"
                  >
                    <c-CButton
                      class_="menu-trigger"
                      c-attrs="activator_attrs"
                    >
                      Menu
                    </c-CButton>
                  </c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="rename">Rename</c-CMenuItem>
                    <c-CMenuItem value="archive">Archive</c-CMenuItem>
                  </c-fill>
                </c-CMenu>
                <c-CPopover>
                  <c-fill
                    name="activator"
                    data="{ activator_attrs }"
                  >
                    <c-CButton
                      class_="popover-trigger"
                      c-attrs="activator_attrs"
                    >
                      Popover
                    </c-CButton>
                  </c-fill>
                  <c-fill name="title">Europa</c-fill>
                  <c-fill name="default">An ocean world.</c-fill>
                </c-CPopover>
                <c-CDialog>
                  <c-fill
                    name="activator"
                    data="{ activator_attrs }"
                  >
                    <c-CButton
                      class_="dialog-trigger"
                      c-attrs="activator_attrs"
                    >
                      Dialog
                    </c-CButton>
                  </c-fill>
                  <c-fill name="title">Mare Imbrium</c-fill>
                  <c-fill name="default">A lunar basin.</c-fill>
                </c-CDialog>
                <c-CSelect
                  class_="named-select"
                  c-options="options"
                  placeholder="Choose a planet"
                  c-trigger_attrs="{'aria-label': 'Planet'}"
                />
              </main>
            </body>
          </html>
        """

    return str(Page().render().serialize())


def _expanded(page: Any, trigger_class: str, value: str) -> None:
    page.wait_for_function(f"() => {_FIND}('.{trigger_class}').getAttribute('aria-expanded') === '{value}'")


# The page without named elements is the control: a failure there is not about names.
@pytest.mark.parametrize("names", [[], DOCUMENT_MEMBERS], ids=["control", "named"])
def test_overlays_work_when_data_names_document_members(page: Any, names: list[str]) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    # A component whose script stopped never opens, so fail in seconds.
    page.set_default_timeout(5000)
    page.set_content(_page(names), wait_until="load")
    page.wait_for_selector(".named-select[data-citry-select-initialized]")

    # Menu: opens on click, moves focus to an item from the keyboard, closes on Escape.
    page.locator(".menu-trigger").click()
    _expanded(page, "menu-trigger", "true")
    page.keyboard.press("ArrowDown")
    page.wait_for_function(
        "() => Object.getOwnPropertyDescriptor(Document.prototype, 'activeElement').get.call(document)"
        "?.getAttribute('role') === 'menuitem'"
    )
    page.keyboard.press("Escape")
    _expanded(page, "menu-trigger", "false")

    # Popover and dialog: open on click, close on Escape.
    for trigger in ("popover-trigger", "dialog-trigger"):
        page.locator(f".{trigger}").click()
        _expanded(page, trigger, "true")
        page.keyboard.press("Escape")
        _expanded(page, trigger, "false")

    # Select: opens, picks an option, and shows it.
    control = page.locator('.named-select [role="combobox"]')
    control.click()
    page.locator('.named-select [role="option"][data-value="mars"]').click()
    page.wait_for_function(f"() => {_FIND}('.named-select select')?.value === 'mars'")
    assert control.locator('[data-citry-ui-part="value"]').text_content().strip() == "Mars"
    assert errors == []
