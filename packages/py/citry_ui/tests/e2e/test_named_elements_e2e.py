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

# Form members Citry UI reads while it walks up from a component, each hidden by
# a named field in the form that holds the components.
FORM_MEMBERS = [
    "parentElement",
    "parentNode",
    "getRootNode",
    "assignedSlot",
    "matches",
    "hasAttribute",
    "closest",
    "contains",
]

# The pages hide `document.querySelector` too, so the test finds elements through `Document.prototype`.
_FIND = "Document.prototype.querySelector.bind(document)"


def _page(names: list[str], fields: list[str]) -> str:
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
                "fields": fields,
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
              <form
                style="padding: 120px"
                onsubmit="return false"
              >
                <input
                  c-for="field in fields"
                  c-name="field"
                  type="hidden"
                >
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
                <c-CAccordion value="canopy">
                  <c-CAccordionItem value="canopy">
                    <c-fill name="title">Canopy</c-fill>
                    <c-fill name="default">Crowns collect the light.</c-fill>
                  </c-CAccordionItem>
                  <c-CAccordionItem value="floor">
                    <c-fill name="title">Floor</c-fill>
                    <c-fill name="default">Fungi return wood to the soil.</c-fill>
                  </c-CAccordionItem>
                </c-CAccordion>
                <c-CSelect
                  class_="named-select"
                  c-options="options"
                  placeholder="Choose a planet"
                  c-trigger_attrs="{'aria-label': 'Planet'}"
                />
              </form>
            </body>
          </html>
        """

    return str(Page().render().serialize())


def _click(page: Any, selector: str) -> None:
    # Playwright's own locators walk up the page through the same members a named
    # form field hides, so the test finds the element itself and clicks its middle.
    x, y = page.evaluate(
        f"""() => {{
          const rect = {_FIND}({selector!r}).getBoundingClientRect();
          return [rect.x + rect.width / 2, rect.y + rect.height / 2];
        }}"""
    )
    page.mouse.click(x, y)


def _expanded(page: Any, trigger_class: str, value: str) -> None:
    page.wait_for_function(f"() => {_FIND}('.{trigger_class}').getAttribute('aria-expanded') === '{value}'")


# The page without named elements is the control: a failure there is not about names.
@pytest.mark.parametrize(
    ("names", "fields"),
    [([], []), (DOCUMENT_MEMBERS, []), ([], FORM_MEMBERS)],
    ids=["control", "document-names", "form-field-names"],
)
def test_overlays_work_when_data_names_document_members(page: Any, names: list[str], fields: list[str]) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    # A component whose script stopped never opens, so fail in seconds.
    page.set_default_timeout(5000)
    page.set_content(_page(names, fields), wait_until="load")
    page.wait_for_function(f"() => {_FIND}('.named-select[data-citry-select-initialized]') !== null")

    # Menu: opens on click, moves focus to an item from the keyboard, closes on Escape.
    _click(page, ".menu-trigger")
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
        _click(page, f".{trigger}")
        _expanded(page, trigger, "true")
        page.keyboard.press("Escape")
        _expanded(page, trigger, "false")

    # Select: opens, picks an option, and shows it.
    _click(page, '.named-select [role="combobox"]')
    page.wait_for_function(f"""() => {_FIND}('.named-select [role="option"][data-value="mars"]')?.checkVisibility()""")
    _click(page, '.named-select [role="option"][data-value="mars"]')
    page.wait_for_function(f"() => {_FIND}('.named-select select')?.value === 'mars'")
    shown = page.evaluate(f"""() => {_FIND}('.named-select [data-citry-ui-part="value"]').textContent""")
    assert shown.strip() == "Mars"
    assert errors == []
