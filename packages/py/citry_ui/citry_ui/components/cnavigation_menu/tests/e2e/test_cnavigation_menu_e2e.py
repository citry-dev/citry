"""Browser evidence for NavigationMenu behavior."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8"><title>NavigationMenu evidence</title><c-css /></head>
          <body x-data>
            <c-CNavigationMenu
              label="Main navigation" id="main-nav" c-delay="40" c-close_delay="80"
              $c-props="{
                value:$store.navigation.controlled ? $store.navigation.value : undefined,
                disabled:$store.navigation.disabled,
                orientation:$store.navigation.orientation,
                loop:$store.navigation.loop,
                variant:$store.navigation.variant,
                size:$store.navigation.size,
                onValueChange:(next, detail) => {
                  $store.navigation.requests.push([next, detail.reason, detail.controlled, detail.forced]);
                  if ($store.navigation.accept) $store.navigation.value = next;
                },
              }"
            >
              <c-CNavigationMenuLink href="#home" c-current="True">Home</c-CNavigationMenuLink>
              <c-CNavigationMenuItem value="products">
                <c-fill name="label">Products</c-fill>
                <c-fill name="default"><a id="product-a" href="#product-a">Product A</a><button type="button">Compare</button></c-fill>
              </c-CNavigationMenuItem>
              <c-CNavigationMenuItem value="resources">
                <c-fill name="label">Resources</c-fill>
                <c-fill name="default"><a href="#docs">Documentation</a></c-fill>
              </c-CNavigationMenuItem>
              <c-CNavigationMenuLink href="#about">About</c-CNavigationMenuLink>
            </c-CNavigationMenu>
            <button id="outside" type="button">Outside</button>
            <c-js />
          </body></html>
        """
        js = """
          Alpine.store('navigation', {
            controlled:false, value:null, accept:false, disabled:false,
            orientation:'horizontal', loop:false, variant:'plain', size:'md', requests:[],
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#main-nav[data-citry-navigation-menu-initialized]")
    return errors


def test_native_click_keyboard_escape_link_and_outside(page: Any) -> None:
    errors = _load(page)
    products = page.get_by_role("button", name="Products")
    products.dispatch_event("click")
    assert products.get_attribute("aria-expanded") == "true"
    assert page.locator("#product-a").is_visible()
    products.press("ArrowDown")
    assert page.locator("#product-a").evaluate("element => element === document.activeElement") is True
    page.keyboard.press("Escape")
    assert products.get_attribute("aria-expanded") == "false"
    assert products.evaluate("element => element === document.activeElement") is True

    products.dispatch_event("click")
    page.locator("#outside").click()
    assert products.get_attribute("aria-expanded") == "false"
    assert errors == []


def test_arrow_navigation_rtl_loop_hover_and_touch_policy(page: Any) -> None:
    errors = _load(page)
    home = page.get_by_role("link", name="Home")
    products = page.get_by_role("button", name="Products")
    resources = page.get_by_role("button", name="Resources")
    home.focus()
    home.press("ArrowRight")
    assert products.evaluate("element => element === document.activeElement") is True
    products.press("End")
    assert page.get_by_role("link", name="About").evaluate("element => element === document.activeElement") is True

    page.locator("#main-nav").evaluate("element => element.dir = 'rtl'")
    products.focus()
    products.press("ArrowLeft")
    assert resources.evaluate("element => element === document.activeElement") is True
    resources.dispatch_event("pointerover", {"pointerType": "mouse", "relatedTarget": None})
    page.wait_for_function(
        "document.querySelector('[data-value=resources][data-citry-navigation-menu-trigger]').getAttribute('aria-expanded') === 'true'"
    )
    products.dispatch_event("pointerover", {"pointerType": "touch", "relatedTarget": None})
    page.wait_for_timeout(60)
    assert products.get_attribute("aria-expanded") == "false"
    assert errors == []


def test_controlled_reject_accept_release_and_disabled_force(page: Any) -> None:
    errors = _load(page)
    products = page.get_by_role("button", name="Products")
    page.evaluate("Alpine.store('navigation').controlled = true")
    products.click()
    assert products.get_attribute("aria-expanded") == "false"
    assert page.evaluate("Alpine.store('navigation').requests.at(-1)") == ["products", "trigger", True, False]
    page.evaluate("Object.assign(Alpine.store('navigation'), {accept:true, value:'products'})")
    page.wait_for_function(
        "document.querySelector('[data-value=products][data-citry-navigation-menu-trigger]').getAttribute('aria-expanded') === 'true'"
    )
    page.evaluate("Alpine.store('navigation').controlled = false")
    page.wait_for_function(
        "document.querySelector('[data-value=products][data-citry-navigation-menu-trigger]').getAttribute('aria-expanded') === 'true'"
    )
    page.evaluate("Alpine.store('navigation').controlled = true")
    page.evaluate("Alpine.store('navigation').disabled = true")
    page.wait_for_function(
        "document.querySelector('[data-value=products][data-citry-navigation-menu-trigger]').getAttribute('aria-expanded') === 'false'"
    )
    assert page.evaluate("Alpine.store('navigation').requests.at(-1).slice(1)") == ["disabled", True, True]
    assert errors == []


def test_horizontal_panel_clamps_to_the_visual_viewport(page: Any) -> None:
    page.set_viewport_size({"width": 360, "height": 700})
    errors = _load(page)
    page.get_by_role("button", name="Resources").dispatch_event("click")
    panel = page.locator('[data-value="resources"][data-citry-navigation-menu-panel]')
    page.wait_for_function(
        "document.querySelector('[data-value=resources][data-citry-navigation-menu-panel]')"
        ".style.getPropertyValue('--_cui-navigation-menu-panel-shift') !== ''"
    )
    bounds = panel.bounding_box()
    assert bounds["x"] >= 15
    assert bounds["x"] + bounds["width"] <= 345
    assert page.evaluate("document.documentElement.scrollWidth === document.documentElement.clientWidth") is True
    assert errors == []


def test_theme_size_environment_and_axe(page: Any) -> None:
    errors = _load(page)
    page.evaluate("Object.assign(Alpine.store('navigation'), {variant:'surface', size:'lg', orientation:'vertical'})")
    nav = page.locator("#main-nav")
    page.wait_for_function("document.querySelector('#main-nav').dataset.size === 'lg'")
    assert nav.get_attribute("data-variant") == "surface"
    assert nav.get_attribute("data-orientation") == "vertical"
    page.emulate_media(forced_colors="active")
    resources = page.get_by_role("button", name="Resources")
    resources.click()
    panel = page.locator('[data-value="resources"][data-citry-navigation-menu-panel]')
    assert panel.evaluate("element => getComputedStyle(element).borderStyle") == "solid"
    page.emulate_media(media="print")
    assert (
        page.locator('[data-value="resources"][data-citry-navigation-menu-trigger]').evaluate(
            "element => getComputedStyle(element.parentElement).display"
        )
        == "none"
    )
    page.emulate_media(media="screen", forced_colors="none")

    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert errors == []
