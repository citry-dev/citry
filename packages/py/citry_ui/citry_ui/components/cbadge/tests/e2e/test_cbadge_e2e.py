"""Browser evidence for the production Badge contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _badge_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <style>
                .part-override [data-citry-ui-part="label"] {
                  letter-spacing: 3px;
                }
              </style>
              <c-css />
            </head>
            <body>
              <c-CBadge c-attrs="{'id': 'default'}">Ready</c-CBadge>
              <c-CBadge c-attrs="{'id': 'solid'}" variant="solid" intent="primary">Active</c-CBadge>
              <c-CBadge c-attrs="{'id': 'outline'}" variant="outline" intent="danger">Restricted</c-CBadge>
              <c-CBadge c-attrs="{'id': 'small'}" size="sm">Small</c-CBadge>
              <c-CBadge c-attrs="{'id': 'large-pill'}" size="lg" shape="pill">Large</c-CBadge>
              <div
                style="--cui-badge-background: rgb(240 231 255);
                  --cui-badge-foreground: rgb(76 29 117);
                  --cui-badge-radius: 7px"
              >
                <c-CBadge c-attrs="{'id': 'brand'}">Quartz</c-CBadge>
              </div>
              <div class="part-override"><c-CBadge c-attrs="{'id': 'part'}">Spaced</c-CBadge></div>
              <div style="inline-size: 120px">
                <c-CBadge c-attrs="{'id': 'long'}">Exceptionallylongunbrokenspecimenidentifier</c-CBadge>
              </div>
              <div dir="rtl"><c-CBadge c-attrs="{'id': 'rtl'}" intent="success">عينة موثقة</c-CBadge></div>
              <c-CBadge c-attrs="{'id': 'icons'}">
                <c-fill name="start"><c-CIcon name="check" /></c-fill>
                <c-fill name="default">Verified</c-fill>
                <c-fill name="end"><c-CIcon name="leaf" /></c-fill>
              </c-CBadge>
            </body>
          </html>
        """

    return str(Page())


def _vue_binding_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html><head><c-css /></head><body>
            <main>
              <c-CBadge
                c-attrs="{'id': 'vue-badge', 'class': 'server-badge', 'style': '--server-token: 7'}"
                :class="{active: active}"
                :style="{'--vue-token': active ? '9' : '3'}"
                :disabled="disabled"
                @click="active = !active; disabled = !disabled"
              >Reactive badge</c-CBadge>
              <c-CSkeleton
                c-attrs="{'id': 'vue-skeleton', 'class': 'server-skeleton'}"
                kind="circle"
                width="24px"
                :class="{active: active}"
              />
            </main>
            <c-js />
          </body></html>
        """
        js = "$component({data(){return {active:false,disabled:false};}});"

    return Page().render().serialize()


def test_badge_is_neutral_inline_content_with_optional_parts(page: Any) -> None:
    page.set_content(_badge_page(), wait_until="load")

    root = page.locator("#default")
    assert root.evaluate("el => el.tagName") == "SPAN"
    assert root.get_attribute("role") is None
    assert root.get_attribute("tabindex") is None
    assert root.evaluate("el => getComputedStyle(el).display") == "inline-flex"
    assert page.get_by_text("Ready", exact=True).count() == 1
    assert page.locator("#icons > [data-citry-ui-part='start']").count() == 1
    assert page.locator("#icons > [data-citry-ui-part='end']").count() == 1


def test_variants_sizes_shapes_and_public_overrides_compute(page: Any) -> None:
    page.set_content(_badge_page(), wait_until="load")

    assert page.locator("#solid").evaluate("el => getComputedStyle(el).backgroundColor") == "rgb(29, 78, 216)"
    assert page.locator("#solid").evaluate("el => getComputedStyle(el).color") == "rgb(255, 255, 255)"
    assert page.locator("#outline").evaluate("el => getComputedStyle(el).backgroundColor") == "rgba(0, 0, 0, 0)"
    assert page.locator("#outline").evaluate("el => getComputedStyle(el).borderTopColor") == "rgb(127, 29, 29)"
    assert page.locator("#small").evaluate("el => getComputedStyle(el).minHeight") == "20px"
    assert page.locator("#large-pill").evaluate("el => getComputedStyle(el).minHeight") == "28px"
    assert page.locator("#large-pill").evaluate("el => getComputedStyle(el).borderRadius") == "999px"
    assert page.locator("#brand").evaluate("el => getComputedStyle(el).backgroundColor") == "rgb(240, 231, 255)"
    assert page.locator("#brand").evaluate("el => getComputedStyle(el).borderRadius") == "7px"
    assert (
        page.locator("#part > [data-citry-ui-part='label']").evaluate("el => getComputedStyle(el).letterSpacing")
        == "3px"
    )


def test_long_content_wraps_and_rtl_remains_logical(page: Any) -> None:
    page.set_content(_badge_page(), wait_until="load")

    geometry = page.locator("#long").evaluate("el => ({client: el.clientWidth, scroll: el.scrollWidth})")
    assert geometry["scroll"] <= geometry["client"]
    assert page.locator("#rtl").evaluate("el => getComputedStyle(el).direction") == "rtl"


def test_forced_colors_and_print_keep_a_visible_boundary(page: Any) -> None:
    page.set_content(_badge_page(), wait_until="load")

    root = page.locator("#solid")
    page.emulate_media(forced_colors="active")
    assert root.evaluate("el => getComputedStyle(el).borderTopStyle") == "solid"
    assert root.evaluate("el => getComputedStyle(el).borderTopColor") == "rgb(0, 0, 0)"
    page.emulate_media(forced_colors="none", media="print")
    assert root.evaluate("el => getComputedStyle(el).backgroundColor") == "rgba(0, 0, 0, 0)"
    assert root.evaluate("el => getComputedStyle(el).borderTopStyle") == "solid"


def test_authored_vue_bindings_fall_through_without_clobbering_component_metadata(page: Any) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_vue_binding_page(), wait_until="load")

    badge = page.locator("#vue-badge")
    skeleton = page.locator("#vue-skeleton")
    assert "cui-badge" in (badge.get_attribute("class") or "")
    assert "server-badge" in (badge.get_attribute("class") or "")
    assert badge.get_attribute("data-variant") == "soft"
    assert badge.get_attribute("style") is not None
    assert "--server-token: 7" in (badge.get_attribute("style") or "")
    # `disabled` has no native semantics on this passive span; Vue forwards its
    # current value as an ordinary consumer attribute.
    assert badge.get_attribute("disabled") == "false"
    assert skeleton.get_attribute("data-kind") == "circle"

    badge.click()
    page.wait_for_function("document.querySelector('#vue-badge').classList.contains('active')")
    assert "cui-badge" in (badge.get_attribute("class") or "")
    assert "server-badge" in (badge.get_attribute("class") or "")
    assert badge.get_attribute("data-variant") == "soft"
    assert badge.get_attribute("disabled") == "true"
    assert "--server-token: 7" in (badge.get_attribute("style") or "")
    assert "--vue-token: 9" in (badge.get_attribute("style") or "")
    assert "active" in (skeleton.get_attribute("class") or "")
    assert "cui-skeleton" in (skeleton.get_attribute("class") or "")
    assert skeleton.get_attribute("data-kind") == "circle"
    assert errors == []
