"""Browser tests for the production CCard contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _card_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.card-brand) {
            --cui-card-background: rgb(255 250 240);
            --cui-card-foreground: rgb(61 51 40);
            --cui-card-border-color: rgb(122 91 58);
            --cui-card-radius: 20px;
            --cui-card-padding: 18px;
            --cui-card-actions-gap: 7px;
          }

          :where(#root-override) {
            --cui-card-background: rgb(24 34 53);
            --cui-card-foreground: rgb(231 238 252);
          }

          :where(.studio-brand) {
            color-scheme: dark;
            --cui-card-background: rgb(13 20 33);
            --cui-card-foreground: rgb(231 238 252);
            --cui-card-border-color: rgb(96 122 165);
            --cui-card-radius: 6px;
          }

          :where(.escape-probe) {
            position: absolute;
            inset-inline-start: 110%;
            inline-size: 8rem;
          }

          :where(.media-probe) {
            inline-size: 200%;
            block-size: 3rem;
            background: red;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <style>
                .consumer-before {
                  display: grid;
                  position: relative;
                  overflow: hidden;
                }

                .part-override [data-citry-ui-part="body"] {
                  padding: 27px;
                }
              </style>
              <c-css />
              <style>
                .consumer-after {
                  display: grid;
                  position: relative;
                  overflow: hidden;
                }
              </style>
            </head>
            <body>
              <div class="card-brand" style="position: relative; width: 22rem">
                <c-CCard
                  c-attrs="{'id': 'root-override'}"
                  variant="outline"
                  size="sm"
                  c-header_actions_attrs="{'role': 'group', 'aria-label': 'Header actions'}"
                  c-actions_attrs="{'role': 'group', 'aria-label': 'Footer actions'}"
                >
                  <c-fill name="media"><div class="media-probe">Media</div></c-fill>
                  <c-fill name="header"><h1>Reading chair</h1></c-fill>
                  <c-fill name="header_actions"><button type="button">Save</button></c-fill>
                  <c-fill name="default">
                    Body
                    <button class="escape-probe" type="button">Escaping control</button>
                    <c-CCard variant="subtle"><c-fill name="default">Nested Card</c-fill></c-CCard>
                  </c-fill>
                  <c-fill name="footer">In stock</c-fill>
                  <c-fill name="actions">
                    <button type="button">Buy</button>
                    <button type="button">Compare</button>
                  </c-fill>
                </c-CCard>
              </div>
              <c-CCard
                size="lg"
                c-attrs="{'id': 'large-card'}"
              >
                <c-fill name="default">Large</c-fill>
              </c-CCard>
              <div class="studio-brand">
                <c-CCard c-attrs="{'id': 'dark-card'}">
                  <c-fill name="default">Dark</c-fill>
                </c-CCard>
              </div>
              <c-CCard class_="consumer-before" c-attrs="{'id': 'consumer-before'}">
                <c-fill name="default">Consumer CSS before Citry UI</c-fill>
              </c-CCard>
              <c-CCard class_="consumer-after" c-attrs="{'id': 'consumer-after'}">
                <c-fill name="default">Consumer CSS after Citry UI</c-fill>
              </c-CCard>
              <c-CCard c-attrs="{'id': 'header-only'}">
                <c-fill name="header"><strong>Header only</strong></c-fill>
              </c-CCard>
              <c-CCard c-attrs="{'id': 'actions-only'}">
                <c-fill name="actions"><button type="button">Continue</button></c-fill>
              </c-CCard>
              <c-CCard class_="part-override" c-attrs="{'id': 'part-override'}">
                <c-fill name="default">Part override</c-fill>
              </c-CCard>
              <c-CCard
                c-style="{'--cui-card-radius': '40px'}"
                c-attrs="{'id': 'media-only'}"
              >
                <c-fill name="media"><div class="media-probe">Media only</div></c-fill>
              </c-CCard>
            </body>
          </html>
        """

    return str(Page())


def test_card_semantics_anatomy_and_focus_are_native(page: Any):
    page.set_content(_card_page(), wait_until="load")

    root = page.locator("#root-override")
    assert root.evaluate("element => element.tagName") == "DIV"
    assert root.get_attribute("role") is None
    assert root.get_attribute("tabindex") is None
    assert root.locator(':scope > [data-citry-ui-part="media"]').count() == 1
    assert root.locator(':scope > [data-citry-ui-part="header"]').count() == 1
    assert root.locator(':scope > [data-citry-ui-part="body"]').count() == 1
    assert root.locator(':scope > [data-citry-ui-part="footer"]').count() == 1
    assert page.get_by_role("group", name="Header actions").count() == 1
    assert page.get_by_role("group", name="Footer actions").count() == 1
    assert root.locator('[data-citry-ui-part="header-content"]').count() == 0


def test_public_variables_override_variant_and_size_fallbacks(page: Any):
    page.set_content(_card_page(), wait_until="load")

    root = page.locator("#root-override")
    body = root.locator(':scope > [data-citry-ui-part="body"]')
    actions = root.locator('[data-citry-ui-part="actions"]')
    assert root.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(24, 34, 53)"
    assert root.evaluate("element => getComputedStyle(element).color") == "rgb(231, 238, 252)"
    assert root.evaluate("element => getComputedStyle(element).borderRadius") == "20px"
    assert body.evaluate("element => getComputedStyle(element).paddingTop") == "18px"
    assert actions.evaluate("element => getComputedStyle(element).columnGap") == "7px"
    assert actions.evaluate("element => getComputedStyle(element).display") == "flex"
    assert (
        page.locator("#large-card > [data-citry-ui-part='body']").evaluate(
            "element => getComputedStyle(element).paddingTop"
        )
        == "20px"
    )


def test_unlayered_consumer_class_overrides_work_before_and_after_component_css(page: Any):
    page.set_content(_card_page(), wait_until="load")

    for card_id in ("#consumer-before", "#consumer-after"):
        card = page.locator(card_id)
        assert card.evaluate("element => getComputedStyle(element).display") == "grid"
        assert card.evaluate("element => getComputedStyle(element).position") == "relative"
        assert card.evaluate("element => getComputedStyle(element).overflow") == "hidden"


def test_card_rows_reserve_tracks_only_for_present_content(page: Any):
    page.set_content(_card_page(), wait_until="load")

    header_only = page.locator("#header-only > [data-citry-ui-part='header']")
    actions_only = page.locator("#actions-only > [data-citry-ui-part='footer']")
    split_header = page.locator("#root-override > [data-citry-ui-part='header']")

    assert header_only.evaluate("element => getComputedStyle(element).gridTemplateColumns.split(' ').length") == 1
    assert actions_only.evaluate("element => getComputedStyle(element).gridTemplateColumns.split(' ').length") == 1
    assert split_header.evaluate("element => getComputedStyle(element).gridTemplateColumns.split(' ').length") == 2

    actions_geometry = actions_only.evaluate(
        """element => {
          const actions = element.querySelector('[data-citry-ui-part="actions"]')
          const button = actions.querySelector('button')
          const rowRect = element.getBoundingClientRect()
          const actionsRect = actions.getBoundingClientRect()
          const buttonRect = button.getBoundingClientRect()
          const padding = parseFloat(getComputedStyle(element).paddingInlineStart)
          return {
            actionsWidth: actionsRect.width,
            buttonStart: buttonRect.left,
            expectedStart: rowRect.left + padding,
            innerWidth: rowRect.width - 2 * padding,
          }
        }"""
    )
    assert abs(actions_geometry["actionsWidth"] - actions_geometry["innerWidth"]) < 1
    assert abs(actions_geometry["buttonStart"] - actions_geometry["expectedStart"]) < 1


def test_public_part_selector_can_override_component_defaults(page: Any):
    page.set_content(_card_page(), wait_until="load")

    body = page.locator("#part-override > [data-citry-ui-part='body']")
    assert body.evaluate("element => getComputedStyle(element).paddingTop") == "27px"


def test_media_only_clips_to_all_card_corners(page: Any):
    page.set_content(_card_page(), wait_until="load")

    media = page.locator("#media-only > [data-citry-ui-part='media']")
    assert media.evaluate("element => getComputedStyle(element).overflow") == "clip"
    assert media.evaluate("element => getComputedStyle(element).borderTopLeftRadius") == "40px"
    assert media.evaluate("element => getComputedStyle(element).borderTopRightRadius") == "40px"
    assert media.evaluate("element => getComputedStyle(element).borderBottomLeftRadius") == "40px"
    assert media.evaluate("element => getComputedStyle(element).borderBottomRightRadius") == "40px"


def test_only_media_clips_and_card_creates_no_positioning_or_stacking_context(page: Any):
    page.set_content(_card_page(), wait_until="load")

    root = page.locator("#root-override")
    media = root.locator(':scope > [data-citry-ui-part="media"]')
    header = root.locator(':scope > [data-citry-ui-part="header"]')
    body = root.locator(':scope > [data-citry-ui-part="body"]')
    footer = root.locator(':scope > [data-citry-ui-part="footer"]')
    assert root.evaluate("element => getComputedStyle(element).position") == "static"
    assert root.evaluate("element => getComputedStyle(element).overflow") == "visible"
    assert root.evaluate("element => getComputedStyle(element).zIndex") == "auto"
    assert media.evaluate("element => getComputedStyle(element).overflow") == "clip"
    assert header.evaluate("element => getComputedStyle(element).overflow") == "visible"
    assert body.evaluate("element => getComputedStyle(element).overflow") == "visible"
    assert footer.evaluate("element => getComputedStyle(element).overflow") == "visible"
    assert page.get_by_role("button", name="Escaping control").is_visible()


def test_nested_card_keeps_its_own_direct_child_anatomy_and_dark_scheme(page: Any):
    page.set_content(_card_page(), wait_until="load")

    nested = page.get_by_text("Nested Card", exact=True).locator('xpath=ancestor::*[@data-citry-ui-part="card"][1]')
    assert nested.get_attribute("data-variant") == "subtle"
    assert nested.locator(':scope > [data-citry-ui-part="body"]').count() == 1
    assert page.locator("#dark-card").evaluate("element => getComputedStyle(element).colorScheme") == "dark"
    assert (
        page.locator("#dark-card").evaluate("element => getComputedStyle(element).backgroundColor")
        == "rgb(13, 20, 33)"
    )
    assert page.locator("#dark-card").evaluate("element => getComputedStyle(element).borderRadius") == "6px"


def test_forced_colors_and_print_remove_decorative_shadow(page: Any):
    page.set_content(_card_page(), wait_until="load")

    card = page.locator("#large-card")
    assert card.evaluate("element => getComputedStyle(element).boxShadow") != "none"
    page.emulate_media(forced_colors="active")
    assert card.evaluate("element => getComputedStyle(element).boxShadow") == "none"
    page.emulate_media(forced_colors="none", media="print")
    assert card.evaluate("element => getComputedStyle(element).boxShadow") == "none"
