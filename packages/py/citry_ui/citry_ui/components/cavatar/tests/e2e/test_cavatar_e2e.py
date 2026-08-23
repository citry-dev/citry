"""Browser evidence for the Avatar contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e

PORTRAIT = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3E"
    "%3Crect width='8' height='8' fill='%230f766e'/%3E%3C/svg%3E"
)


def _avatar_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <style>.selector [data-citry-ui-part="fallback"] { letter-spacing: 4px; }</style>
              <c-css />
            </head>
            <body
              x-data
              x-init="Alpine.store('avatarTest', {
                source: null,
                alt: 'Reactive guide',
                variant: 'soft',
                statuses: []
              })"
            >
              <c-CAvatar c-src="portrait" alt="Loaded guide" c-attrs="{'id': 'loaded'}">LG</c-CAvatar>
              <c-CAvatar
                src="/definitely-missing-avatar.png"
                alt="Missing guide"
                c-attrs="{'id': 'missing'}"
              >MG</c-CAvatar>
              <div class="selector" style="--cui-avatar-size:64px; --cui-avatar-radius:12px">
                <c-CAvatar alt="Styled guide" c-attrs="{'id': 'styled'}">SG</c-CAvatar>
              </div>
              <c-CAvatar
                alt="Reactive guide"
                c-attrs="{'id': 'reactive'}"
                $c-props="{
                  src: $store.avatarTest.source,
                  alt: $store.avatarTest.alt,
                  variant: $store.avatarTest.variant,
                  onStatusChange: detail => $store.avatarTest.statuses.push(detail.status)
                }"
              >RG</c-CAvatar>
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {"portrait": PORTRAIT}

    return str(Page())


def test_loading_error_and_accessible_semantics_settle(page: Any) -> None:
    page.set_content(_avatar_page(), wait_until="load")
    page.wait_for_selector("#loaded[data-citry-avatar-initialized]")
    page.wait_for_function("document.querySelector('#loaded').dataset.status === 'loaded'")
    page.wait_for_function("document.querySelector('#missing').dataset.status === 'error'")

    assert page.locator("#loaded").get_attribute("role") == "img"
    assert page.locator("#loaded").get_attribute("aria-label") == "Loaded guide"
    assert page.locator("#loaded [data-citry-ui-part='image']").get_attribute("alt") == ""
    assert page.locator("#missing [data-citry-ui-part='image']").is_hidden()
    assert page.locator("#missing [data-citry-ui-part='fallback']").is_visible()


def test_reactive_source_name_variant_and_status_callback(page: Any) -> None:
    page.set_content(_avatar_page(), wait_until="load")
    page.wait_for_selector("#reactive[data-citry-avatar-initialized]")
    reactive = page.locator("#reactive")

    assert reactive.get_attribute("data-status") == "fallback"
    page.evaluate(
        "Object.assign(Alpine.store('avatarTest'), {"
        "source: '/missing-reactive-avatar.png', alt: 'Marsh oracle', variant: 'solid'"
        "})"
    )
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'error'")
    assert reactive.get_attribute("aria-label") == "Marsh oracle"
    assert reactive.get_attribute("data-variant") == "solid"
    assert page.evaluate(
        "Alpine.store('avatarTest').statuses.includes('loading') "
        "&& Alpine.store('avatarTest').statuses.includes('error')"
    )
    page.evaluate("Alpine.store('avatarTest').source = null")
    page.wait_for_function("document.querySelector('#reactive').dataset.status === 'fallback'")
    image_src = reactive.locator("[data-citry-ui-part='image']").get_attribute("src")
    assert image_src is not None
    assert image_src.startswith("data:image/gif;base64,")


def test_public_variables_and_selector_overrides_compute(page: Any) -> None:
    page.set_content(_avatar_page(), wait_until="load")
    styled = page.locator("#styled")
    assert styled.evaluate("el => getComputedStyle(el).inlineSize") == "64px"
    assert styled.evaluate("el => getComputedStyle(el).borderRadius") == "12px"
    assert (
        styled.locator("[data-citry-ui-part='fallback']").evaluate("el => getComputedStyle(el).letterSpacing") == "4px"
    )


def test_forced_colors_keeps_a_visible_boundary(page: Any) -> None:
    page.set_content(_avatar_page(), wait_until="load")
    page.emulate_media(forced_colors="active")
    assert page.locator("#styled").evaluate("el => getComputedStyle(el).borderColor") == "rgb(0, 0, 0)"
