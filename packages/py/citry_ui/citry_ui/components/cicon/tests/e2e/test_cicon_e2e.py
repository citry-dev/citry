"""Browser tests for the production CIcon contract."""

from __future__ import annotations

from typing import Any

import pytest
from markupsafe import Markup

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _icon_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

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
              <p id="decorative-line">
                <c-CIcon name="leaf" size="sm" />
                Native fern
              </p>
              <c-CIcon
                name="success"
                label="Specimen verified"
                size="lg"
              />
              <div
                id="custom-icon"
                style="color: rgb(21, 128, 61); --cui-icon-size: 32px; --cui-icon-stroke-width: 1.5"
              >
                <c-CIcon name="leaf" />
              </div>
              <div id="rtl-icons" dir="rtl">
                <c-CIcon name="arrow-left" />
                <c-CIcon name="back" />
                <c-CIcon name="forward" />
                <c-CIcon name="next" />
              </div>
            </body>
          </html>
        """

    return str(Page())


def test_icon_semantics_and_focus_contract(page: Any):
    page.set_content(_icon_page(), wait_until="load")

    meaningful = page.get_by_role("img", name="Specimen verified")
    assert meaningful.count() == 1
    assert meaningful.get_attribute("focusable") == "false"
    assert page.locator('#decorative-line [data-name="leaf"]').get_attribute("aria-hidden") == "true"
    assert page.locator('[data-citry-ui-part="icon"][tabindex]').count() == 0


def test_icon_inherits_color_and_public_size_and_stroke_overrides(page: Any):
    page.set_content(_icon_page(), wait_until="load")
    icon = page.locator('#custom-icon [data-citry-ui-part="icon"]')

    assert icon.evaluate("element => getComputedStyle(element).color") == "rgb(21, 128, 61)"
    assert icon.evaluate("element => getComputedStyle(element).width") == "32px"
    assert icon.evaluate("element => getComputedStyle(element).height") == "32px"
    assert icon.evaluate("element => getComputedStyle(element).strokeWidth") == "1.5px"


def test_only_logical_direction_names_mirror_in_rtl(page: Any):
    page.set_content(_icon_page(), wait_until="load")

    physical = page.locator('#rtl-icons [data-name="arrow-left"] .cui-icon__glyph')
    logical = page.locator('#rtl-icons [data-name="back"] .cui-icon__glyph')

    assert physical.evaluate("element => getComputedStyle(element).transform") == "none"
    assert logical.evaluate("element => getComputedStyle(element).transform") != "none"


def test_trusted_markup_cannot_create_an_executable_svg_attribute(page: Any):
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    hostile = citry_ui.CIcon(
        name="leaf",
        label=Markup('good" onload="window.__iconPwned=true'),
    )

    with pytest.raises(ValueError, match="trusted HTML"):
        str(hostile.render(citry=app))

    page.set_content(_icon_page(), wait_until="load")
    assert page.evaluate("window.__iconPwned") is None
