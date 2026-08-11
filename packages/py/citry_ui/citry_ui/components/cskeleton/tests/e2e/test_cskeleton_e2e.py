from __future__ import annotations

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
          <!doctype html><html><head>
            <style>.override [data-citry-ui-part="line"] { border-radius: 3px; }</style>
            <c-css />
          </head><body>
            <div class="override" style="--cui-skeleton-background:rgb(15 118 110)">
              <c-CSkeleton c-attrs="{'id': 'text'}" kind="text" c-lines="3" width="240px" />
            </div>
            <c-CSkeleton c-attrs="{'id': 'circle'}" kind="circle" width="48px" animation="wave" />
          </body></html>
        """

    return str(Page())


def test_geometry_public_overrides_and_decorative_semantics(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    text = page.locator("#text")
    circle = page.locator("#circle")
    assert text.get_attribute("aria-hidden") == "true"
    assert text.locator('[data-citry-ui-part="line"]').count() == 3
    assert text.evaluate("el => getComputedStyle(el).inlineSize") == "240px"
    assert (
        text.locator('[data-citry-ui-part="line"]').first.evaluate("el => getComputedStyle(el).backgroundColor")
        == "rgb(15, 118, 110)"
    )
    assert (
        text.locator('[data-citry-ui-part="line"]').first.evaluate("el => getComputedStyle(el).borderRadius") == "3px"
    )
    assert circle.evaluate("el => el.getBoundingClientRect().width === el.getBoundingClientRect().height")


def test_reduced_motion_disables_animation(page: Any) -> None:
    page.emulate_media(reduced_motion="reduce")
    page.set_content(_page(), wait_until="load")
    assert page.locator("#circle").evaluate("el => getComputedStyle(el, '::after').animationName") == "none"
