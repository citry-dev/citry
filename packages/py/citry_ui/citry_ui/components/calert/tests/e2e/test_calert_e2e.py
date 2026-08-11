"""Browser tests for the production Alert contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _alert_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.alert-brand) {
            --cui-alert-radius: 20px;
            --cui-alert-icon-color: rgb(88 28 135);
          }

          :where(.alert-part[data-citry-ui-part="alert"]) {
            --cui-alert-gap: 24px;
          }

          :where(.alert-narrow) {
            inline-size: 8rem;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body
              x-data
              x-init="Alpine.store('alertTest', {
                intent: 'info',
                variant: 'soft',
                size: 'md',
                announce: 'off',
                icon: true,
              })"
            >
              <c-CAlert
                class_="alert-brand alert-part"
                actions_label="Observatory recovery"
                $c-props="{
                  intent: $store.alertTest.intent,
                  variant: $store.alertTest.variant,
                  size: $store.alertTest.size,
                  announce: $store.alertTest.announce,
                  icon: $store.alertTest.icon,
                }"
              >
                <c-fill name="title">Camera link interrupted</c-fill>
                <c-fill name="default">
                  Reconnect before the <a href="#exposure">next exposure</a>.
                </c-fill>
                <c-fill name="actions">
                  <button id="retry-alert" type="button">Retry</button>
                  <a href="#forecast">Open forecast</a>
                </c-fill>
              </c-CAlert>

              <div id="rtl-alert" dir="rtl">
                <c-CAlert icon_name="back" variant="outline">
                  Return to the previous observation
                </c-CAlert>
              </div>

              <div style="color-scheme: dark">
                <c-CAlert class_="dark-alert" intent="success" variant="solid">
                  Archive synchronized
                </c-CAlert>
              </div>

              <c-CAlert class_="alert-narrow" intent="warn">
                observatoryobservatoryobservatoryobservatoryobservatory
              </c-CAlert>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


@pytest.fixture
def alert_page(page: Any):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_alert_page())
    page.wait_for_function(
        """() => {
          const alerts = [...document.querySelectorAll('.cui-alert')];
          return alerts.length === 4
            && alerts.every(root => root.hasAttribute('data-citry-alert-initialized'));
        }"""
    )
    return page, errors


def test_alert_semantics_actions_and_focus_contract(alert_page):
    page, errors = alert_page
    root = page.locator(".cui-alert").first
    content = root.locator(':scope > [data-citry-ui-part="content"]')
    actions = root.locator(':scope > [data-citry-ui-part="actions"]')

    assert root.get_attribute("role") is None
    assert root.get_attribute("tabindex") is None
    assert content.get_attribute("role") is None
    assert actions.get_attribute("role") == "group"
    assert actions.get_attribute("aria-label") == "Observatory recovery"
    page.locator("body").press("Tab")
    assert page.get_by_role("link", name="next exposure").evaluate("element => element === document.activeElement")
    page.keyboard.press("Tab")
    assert page.locator("#retry-alert").evaluate("element => element === document.activeElement")
    page.keyboard.press("Tab")
    assert page.get_by_role("link", name="Open forecast").evaluate("element => element === document.activeElement")
    assert errors == []


def test_client_inputs_update_every_public_surface_and_deduplicate_invalid_episodes(alert_page):
    page, errors = alert_page
    root = page.locator(".cui-alert").first
    content = root.locator(':scope > [data-citry-ui-part="content"]')

    page.evaluate(
        """() => Object.assign(Alpine.store('alertTest'), {
          intent: 'error',
          variant: 'solid',
          size: 'lg',
          announce: 'assertive',
          icon: false,
        })"""
    )
    page.wait_for_timeout(0)
    assert root.get_attribute("data-intent") == "error"
    assert root.get_attribute("data-variant") == "solid"
    assert root.get_attribute("data-size") == "lg"
    assert root.get_attribute("data-announce") == "assertive"
    assert root.get_attribute("data-icon") is None
    assert content.get_attribute("role") == "alert"

    page.evaluate("Alpine.store('alertTest').intent = null")
    page.wait_for_timeout(0)
    page.evaluate("Alpine.store('alertTest').intent = 42")
    page.wait_for_timeout(0)
    page.evaluate("Alpine.store('alertTest').variant = 'outline'")
    page.wait_for_timeout(0)
    page.evaluate("Alpine.store('alertTest').size = 'sm'")
    page.wait_for_timeout(0)
    assert root.get_attribute("data-intent") == "info"
    assert sum("CAlert intent received invalid client value" in error for error in errors) == 1

    page.evaluate("Alpine.store('alertTest').intent = 'success'")
    page.wait_for_timeout(0)
    page.evaluate("Alpine.store('alertTest').intent = null")
    page.wait_for_timeout(0)
    assert sum("CAlert intent received invalid client value" in error for error in errors) == 2


def test_icons_have_one_svg_zero_geometry_when_hidden_and_logical_rtl_behavior(alert_page):
    page, errors = alert_page
    root = page.locator(".cui-alert").first
    indicator = root.locator(':scope > [data-citry-ui-part="indicator"]')
    glyphs = indicator.locator("[data-cui-alert-intent]")

    assert indicator.locator("svg").count() == 1
    assert glyphs.count() == 4
    assert glyphs.filter(has=page.locator("path")).count() >= 1
    assert (
        glyphs.evaluate_all(
            "elements => elements.filter(element => getComputedStyle(element).display !== 'none').length"
        )
        == 1
    )
    page.evaluate("Alpine.store('alertTest').intent = 'error'")
    page.wait_for_timeout(0)
    error_glyph = indicator.locator("[data-cui-alert-intent=error]")
    info_glyph = indicator.locator("[data-cui-alert-intent=info]")
    assert error_glyph.get_attribute("data-cui-alert-hidden") is None
    assert info_glyph.get_attribute("data-cui-alert-hidden") == ""
    assert (
        glyphs.evaluate_all(
            "elements => elements.filter(element => getComputedStyle(element).display !== 'none').length"
        )
        == 1
    )
    hidden_glyphs = indicator.locator("[data-cui-alert-hidden]")
    assert hidden_glyphs.count() == 3
    assert (
        hidden_glyphs.evaluate_all(
            "elements => elements.every(element => element.getBoundingClientRect().width === 0)"
        )
        is True
    )
    page.evaluate("Alpine.store('alertTest').icon = false")
    page.wait_for_timeout(0)
    assert indicator.evaluate("element => getComputedStyle(element).display") == "none"
    assert indicator.evaluate("element => element.getBoundingClientRect().width") == 0

    logical = page.locator("#rtl-alert .cui-alert__glyph--logical")
    assert logical.evaluate("element => getComputedStyle(element).transform") != "none"
    assert errors == []


def test_alert_public_css_hooks_and_environment_contract(alert_page):
    page, errors = alert_page
    root = page.locator(".cui-alert").first
    indicator = root.locator(':scope > [data-citry-ui-part="indicator"]')
    narrow = page.locator(".alert-narrow")

    assert root.evaluate("element => getComputedStyle(element).borderRadius") == "20px"
    assert root.evaluate("element => getComputedStyle(element).columnGap") == "24px"
    assert indicator.evaluate("element => getComputedStyle(element).color") == "rgb(88, 28, 135)"
    assert narrow.evaluate("element => element.scrollWidth <= element.clientWidth") is True
    assert root.evaluate("element => getComputedStyle(element).overflow") == "visible"
    assert root.evaluate("element => getComputedStyle(element).zIndex") == "auto"
    for alert in (root, page.locator(".dark-alert"), page.locator("#rtl-alert .cui-alert")):
        assert alert.evaluate("element => getComputedStyle(element).borderTopWidth") == "1px"
    root.evaluate("element => element.style.setProperty('--cui-alert-border-width', '5px')")
    assert root.evaluate("element => getComputedStyle(element).borderTopWidth") == "5px"

    page.emulate_media(forced_colors="active")
    assert root.evaluate("element => getComputedStyle(element).borderStyle") == "solid"
    forced = root.evaluate(
        """element => {
          const indicator = element.querySelector('[data-citry-ui-part="indicator"]');
          const message = element.querySelector('[data-citry-ui-part="message"]');
          const link = element.querySelector('a');
          return {
            color: getComputedStyle(element).color,
            borderColor: getComputedStyle(element).borderTopColor,
            indicatorColor: getComputedStyle(indicator).color,
            indicatorDisplay: getComputedStyle(indicator).display,
            messageColor: getComputedStyle(message).color,
            linkColor: getComputedStyle(link).color,
          };
        }"""
    )
    assert forced["borderColor"] == forced["color"]
    assert forced["indicatorColor"] == forced["color"]
    assert forced["indicatorDisplay"] != "none"
    assert forced["messageColor"] == forced["color"]
    assert forced["linkColor"] == forced["color"]
    page.emulate_media(forced_colors="none", media="print")
    assert root.evaluate("element => getComputedStyle(element).backgroundColor") in {
        "rgba(0, 0, 0, 0)",
        "transparent",
    }
    printed = root.evaluate(
        """element => {
          const indicator = element.querySelector('[data-citry-ui-part="indicator"]');
          const message = element.querySelector('[data-citry-ui-part="message"]');
          const link = element.querySelector('a');
          return {
            color: getComputedStyle(element).color,
            borderColor: getComputedStyle(element).borderTopColor,
            borderStyle: getComputedStyle(element).borderStyle,
            indicatorDisplay: getComputedStyle(indicator).display,
            messageColor: getComputedStyle(message).color,
            linkColor: getComputedStyle(link).color,
          };
        }"""
    )
    assert printed["borderStyle"] == "solid"
    assert printed["borderColor"] == printed["color"]
    assert printed["indicatorDisplay"] != "none"
    assert printed["messageColor"] == printed["color"]
    assert printed["linkColor"] == printed["color"]
    assert errors == []


def test_long_action_content_wraps_inside_a_narrow_alert(alert_page):
    page, errors = alert_page
    root = page.locator(".cui-alert").first
    action_link = root.locator(':scope > [data-citry-ui-part="actions"] a')
    root.evaluate("element => { element.style.inlineSize = '8rem'; }")
    action_link.evaluate("element => { element.textContent = 'forecastforecastforecastforecastforecastforecast'; }")

    assert action_link.evaluate("element => getComputedStyle(element).overflowWrap") == "anywhere"
    assert root.evaluate("element => element.scrollWidth <= element.clientWidth") is True
    assert errors == []


def test_plain_action_links_follow_alert_foreground_with_solid_contrast(alert_page):
    page, errors = alert_page
    root = page.locator(".cui-alert").first
    action_link = root.locator(':scope > [data-citry-ui-part="actions"] a')
    message_link = root.locator(':scope > [data-citry-ui-part="content"] a')

    for scheme in ("light", "dark"):
        root.evaluate("(element, value) => { element.style.colorScheme = value; }", scheme)
        for intent in ("info", "success", "warn", "error"):
            page.evaluate(
                "([nextIntent]) => Object.assign(Alpine.store('alertTest'), {intent: nextIntent, variant: 'solid'})",
                [intent],
            )
            page.wait_for_function(
                "intent => document.querySelector('.cui-alert')?.dataset.intent === intent",
                arg=intent,
            )
            for link in (message_link, action_link):
                ratio = link.evaluate(
                    """element => {
                  const parse = (value) => value.match(/[0-9.]+/g).slice(0, 3).map(Number);
                  const luminance = (rgb) => {
                    const channels = rgb.map((channel) => {
                      const value = channel / 255;
                      return value <= 0.04045
                        ? value / 12.92
                        : ((value + 0.055) / 1.055) ** 2.4;
                    });
                    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
                  };
                  const foreground = luminance(parse(getComputedStyle(element).color));
                  const background = luminance(parse(getComputedStyle(element.closest('.cui-alert')).backgroundColor));
                  return (Math.max(foreground, background) + 0.05)
                    / (Math.min(foreground, background) + 0.05);
                }"""
                )
                assert ratio >= 4.5, (scheme, intent, ratio)

    assert "underline" in action_link.evaluate("element => getComputedStyle(element).textDecorationLine")
    page.add_style_tag(content=".alert-part a { color: rgb(0 100 0); }")
    assert action_link.evaluate("element => getComputedStyle(element).color") == "rgb(0, 100, 0)"
    assert message_link.evaluate("element => getComputedStyle(element).color") == "rgb(0, 100, 0)"
    assert errors == []
