"""Browser tests for the production Accordion contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _accordion_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.accordion-brand) {
            --cui-accordion-radius: 20px;
            --cui-accordion-trigger-open-color: rgb(88 28 135);
          }

          :where(.accordion-part[data-citry-ui-part="accordion"]) {
            --cui-accordion-panel-padding-inline: 24px;
          }

          :where(.accordion-narrow) {
            inline-size: 9rem;
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
              x-init="Alpine.store('accordionTest', {
                events: [],
                nativeClicks: 0,
                nativeKeys: 0,
                floorDisabled: false,
                collapsible: true,
                controlled: 'floor',
                multiple: ['canopy'],
                variant: 'outline',
                size: 'md',
                indicator: true,
                indicatorPosition: 'end',
              })"
            >
              <button id="before" type="button">Before</button>
              <form id="forest-form">
                <c-CAccordion
                  id="guide"
                  value="canopy"
                  region
                  class_="accordion-brand accordion-part accordion-narrow"
                  $c-props="{
                    collapsible: $store.accordionTest.collapsible,
                    variant: $store.accordionTest.variant,
                    size: $store.accordionTest.size,
                    indicator: $store.accordionTest.indicator,
                    indicatorPosition: $store.accordionTest.indicatorPosition,
                    onValueChange: (next, detail) => $store.accordionTest.events.push({next, detail}),
                  }"
                >
                <c-CAccordionItem value="canopy" actions_label="Canopy actions">
                  <c-fill name="title">Canopy</c-fill>
                  <c-fill name="actions">
                    <button id="bookmark" type="button">Bookmark</button>
                  </c-fill>
                  <c-fill name="default">
                    <input id="canopy-note" name="note" value="moss" />
                    <c-CAccordion id="nested" value="owl" heading_level="4">
                      <c-CAccordionItem value="owl">
                        <c-fill name="title">Tawny owl</c-fill>
                        <c-fill name="default">Nocturnal hunter</c-fill>
                      </c-CAccordionItem>
                    </c-CAccordion>
                  </c-fill>
                </c-CAccordionItem>
                <c-CAccordionItem
                  value="floor"
                  c-trigger_attrs="{
                    '@click.stop': '$store.accordionTest.nativeClicks += 1',
                    '@keydown.stop': '$store.accordionTest.nativeKeys += 1',
                  }"
                  $c-props="{disabled: $store.accordionTest.floorDisabled}"
                >
                  <c-fill name="title">Forest floor</c-fill>
                  <c-fill name="default">Ferns and fungi</c-fill>
                </c-CAccordionItem>
                <c-CAccordionItem value="understory">
                  <c-fill name="title">
                    understoryunderstoryunderstoryunderstoryunderstory
                  </c-fill>
                  <c-fill name="default">Young trees</c-fill>
                </c-CAccordionItem>
                </c-CAccordion>
              </form>

              <c-CAccordion
                id="controlled"
                value="canopy"
                $c-props="{
                  value: $store.accordionTest.controlled,
                  onValueChange: next => $store.accordionTest.controlled = next,
                }"
              >
                <c-CAccordionItem value="canopy">
                  <c-fill name="title">Controlled canopy</c-fill>
                  <c-fill name="default">Upper layer</c-fill>
                </c-CAccordionItem>
                <c-CAccordionItem value="floor">
                  <c-fill name="title">Controlled floor</c-fill>
                  <c-fill name="default">Lower layer</c-fill>
                </c-CAccordionItem>
              </c-CAccordion>

              <c-CAccordion
                id="multiple"
                multiple
                c-value="['canopy']"
                $c-props="{value: $store.accordionTest.multiple}"
              >
                <c-CAccordionItem value="canopy">
                  <c-fill name="title">Multiple canopy</c-fill>
                  <c-fill name="default">Upper layer</c-fill>
                </c-CAccordionItem>
                <c-CAccordionItem value="floor">
                  <c-fill name="title">Multiple floor</c-fill>
                  <c-fill name="default">Lower layer</c-fill>
                </c-CAccordionItem>
              </c-CAccordion>

              <fieldset id="native-fieldset">
                <legend>Native ownership</legend>
                <c-CAccordion id="fieldset-guide">
                  <c-CAccordionItem value="field">
                    <c-fill name="title">Fieldset item</c-fill>
                    <c-fill name="default">Fieldset panel</c-fill>
                  </c-CAccordionItem>
                </c-CAccordion>
              </fieldset>
              <button id="after" type="button">After</button>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _events_accordion_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-accordion-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class WorkspaceAccordion(Component):
        citry = app

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return WorkspaceAccordion(step=state.step)

        template = """
          <section data-workspace-accordion>
            <button
              class="advance-accordion"
              type="button"
              @c-click="advance"
            >
              Advance
            </button>
            <c-CAccordion
              #c-key="'events-accordion'"
              id="events-accordion"
              c-collapsible="False"
              $c-props="{
                onValueChange: (value, detail) => {
                  window.__accordionChange = {
                    value,
                    detail: structuredClone(detail),
                  };
                  if (window.__accordionMutateDetails) {
                    detail.removedValues.length = 0;
                  }
                },
              }"
            >
              <c-for each="item in items">
                <c-CAccordionItem
                  c-value="item['value']"
                  c-actions_label="'Forest floor actions' if item['value'] == 'floor' else None"
                >
                  <c-fill name="title">{{ item["label"] }}</c-fill>
                  <c-if cond="item['value'] == 'floor'">
                    <c-fill name="actions">
                      <button id="events-floor-action" type="button">Mark floor</button>
                    </c-fill>
                  </c-if>
                  <c-fill name="default">
                    {{ item["label"] }} panel
                    <c-if cond="item['value'] == 'floor'">
                      <input id="events-floor-input" aria-label="Floor note" />
                      <c-CAccordion id="events-nested" heading_level="4">
                        <c-CAccordionItem value="moss">
                          <c-fill name="title">Moss layer</c-fill>
                          <c-fill name="default">Nested moss details</c-fill>
                        </c-CAccordionItem>
                      </c-CAccordion>
                    </c-if>
                  </c-fill>
                </c-CAccordionItem>
              </c-for>
            </c-CAccordion>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            all_items = {
                "canopy": {"value": "canopy", "label": "Canopy"},
                "floor": {"value": "floor", "label": "Forest floor"},
                "understory": {"value": "understory", "label": "Understory"},
            }
            order = (
                ("canopy", "floor", "understory")
                if kwargs.step == 0
                else ("understory", "floor", "canopy")
                if kwargs.step == 1
                else ("understory", "canopy")
            )
            return {"items": tuple(all_items[value] for value in order)}

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
              <c-workspace-accordion />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def _canonical_value_page() -> str:
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
            <body
              x-data
              x-init="Alpine.store('accordionCanonical', {
                single: undefined,
                multiple: undefined,
              })"
            >
              <c-CAccordion
                id="canonical-single"
                c-value="first"
                $c-props="{value: $store.accordionCanonical.single}"
              >
                <c-CAccordionItem c-value="first">
                  <c-fill name="title">Mist trail</c-fill>
                  <c-fill name="default">Single canonical value</c-fill>
                </c-CAccordionItem>
                <c-CAccordionItem c-value="second">
                  <c-fill name="title">Root trail</c-fill>
                  <c-fill name="default">Second canonical value</c-fill>
                </c-CAccordionItem>
              </c-CAccordion>
              <c-CAccordion
                id="canonical-multiple"
                multiple
                c-value="[first]"
                $c-props="{value: $store.accordionCanonical.multiple}"
              >
                <c-CAccordionItem c-value="first">
                  <c-fill name="title">Multiple mist trail</c-fill>
                  <c-fill name="default">First multiple value</c-fill>
                </c-CAccordionItem>
                <c-CAccordionItem c-value="second">
                  <c-fill name="title">Multiple root trail</c-fill>
                  <c-fill name="default">Second multiple value</c-fill>
                </c-CAccordionItem>
              </c-CAccordion>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {"first": "mist\ntrail", "second": "root\ntrail"}

    return str(Page())


def _large_accordion_page(count: int) -> str:
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
              <c-CAccordion id="large-accordion">
                <c-for each="item in items">
                  <c-CAccordionItem c-value="item">
                    <c-fill name="title">{{ item }}</c-fill>
                    <c-fill name="default">Panel {{ item }}</c-fill>
                  </c-CAccordionItem>
                </c-for>
              </c-CAccordion>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {"items": tuple(f"item-{index}" for index in range(count))}

    return str(Page())


@pytest.fixture
def accordion_page(page: Any):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_accordion_page())
    page.wait_for_function(
        """() => {
          const roots = [...document.querySelectorAll('[data-citry-accordion-root]')];
          const items = [...document.querySelectorAll('[data-citry-accordion-item]')];
          return roots.length === 5
            && items.length === 9
            && roots.every(root => root.hasAttribute('data-citry-accordion-initialized'))
            && items.every(item => item.hasAttribute('data-citry-accordion-item-initialized'));
        }"""
    )
    page.wait_for_timeout(30)
    return page, errors


def _direct_triggers(root):
    return root.locator(
        ":scope > [data-citry-accordion-item] "
        '> [data-citry-ui-part="accordion-header"] '
        '> [data-citry-ui-part="accordion-heading"] '
        "> [data-citry-accordion-trigger]"
    )


def test_uncontrolled_activation_callback_focus_and_nested_isolation(accordion_page):
    page, errors = accordion_page
    root = page.locator("#guide")
    triggers = _direct_triggers(root)
    canopy, floor, understory = (triggers.nth(index) for index in range(3))

    assert canopy.get_attribute("aria-expanded") == "true"
    floor.click()
    page.wait_for_timeout(220)
    assert canopy.get_attribute("aria-expanded") == "false"
    assert floor.get_attribute("aria-expanded") == "true"
    event = page.evaluate("Alpine.store('accordionTest').events.at(-1)")
    assert event["next"] == "floor"
    assert event["detail"]["source"] == "activation"
    assert event["detail"]["itemValue"] == "floor"
    assert event["detail"]["removedValues"] == []
    assert page.evaluate("Alpine.store('accordionTest').nativeClicks") == 1

    floor.focus()
    floor.press("ArrowDown")
    assert understory.evaluate("element => element === document.activeElement")
    assert page.evaluate("Alpine.store('accordionTest').nativeKeys") == 1
    understory.press("Home")
    assert canopy.evaluate("element => element === document.activeElement")

    nested = page.locator("#nested")
    nested_trigger = _direct_triggers(nested).first
    assert nested_trigger.get_attribute("aria-expanded") == "true"
    canopy.click()
    page.wait_for_timeout(220)
    assert nested_trigger.get_attribute("aria-expanded") == "true"
    assert errors == []


def test_owned_capture_handlers_survive_trigger_stop_modifiers(accordion_page):
    page, errors = accordion_page
    root = page.locator("#guide")
    floor = _direct_triggers(root).nth(1)

    floor.focus()
    floor.press("Enter")
    page.wait_for_timeout(220)
    assert floor.get_attribute("aria-expanded") == "true"
    floor.press("Space")
    page.wait_for_timeout(220)
    assert floor.get_attribute("aria-expanded") == "false"
    assert page.evaluate("Alpine.store('accordionTest').nativeClicks") == 2
    assert page.evaluate("Alpine.store('accordionTest').nativeKeys") == 2
    assert errors == []


def test_controlled_single_and_multiple_value_shapes(accordion_page):
    page, errors = accordion_page
    controlled = page.locator("#controlled")
    controlled_triggers = _direct_triggers(controlled)
    assert controlled_triggers.nth(1).get_attribute("aria-expanded") == "true"
    controlled_triggers.first.click()
    page.wait_for_timeout(220)
    assert page.evaluate("Alpine.store('accordionTest').controlled") == "canopy"
    assert controlled_triggers.first.get_attribute("aria-expanded") == "true"

    multiple = page.locator("#multiple")
    multiple_triggers = _direct_triggers(multiple)
    page.evaluate("Alpine.store('accordionTest').multiple = ['canopy', 'floor']")
    page.wait_for_timeout(220)
    assert multiple_triggers.first.get_attribute("aria-expanded") == "true"
    assert multiple_triggers.nth(1).get_attribute("aria-expanded") == "true"
    page.evaluate("Alpine.store('accordionTest').multiple = null")
    page.wait_for_timeout(220)
    assert multiple_triggers.first.get_attribute("aria-expanded") == "false"
    assert multiple_triggers.nth(1).get_attribute("aria-expanded") == "false"
    assert errors == []


def test_noncollapsible_noop_programmatic_activation_and_panel_focus_recovery(accordion_page):
    page, errors = accordion_page
    root = page.locator("#guide")
    triggers = _direct_triggers(root)
    canopy = triggers.first
    floor = triggers.nth(1)

    page.evaluate("Alpine.store('accordionTest').collapsible = false")
    page.wait_for_timeout(30)
    assert canopy.get_attribute("aria-disabled") == "true"
    event_count = page.evaluate("Alpine.store('accordionTest').events.length")
    canopy.evaluate("element => element.click()")
    page.wait_for_timeout(30)
    assert page.evaluate("Alpine.store('accordionTest').events.length") == event_count
    assert canopy.get_attribute("aria-expanded") == "true"

    page.locator("#canopy-note").focus()
    floor.evaluate("element => element.click()")
    page.wait_for_timeout(220)
    assert canopy.evaluate("element => element === document.activeElement")
    event = page.evaluate("Alpine.store('accordionTest').events.at(-1)")
    assert event["detail"]["source"] == "activation"
    assert floor.get_attribute("aria-disabled") == "true"

    entries = page.evaluate("Array.from(new FormData(document.querySelector('#forest-form')).entries())")
    assert ["note", "moss"] in entries
    assert errors == []


def test_invalid_client_episode_deduplicates_until_recovery(accordion_page):
    page, errors = accordion_page
    controlled = page.locator("#controlled")
    triggers = _direct_triggers(controlled)

    page.evaluate("Alpine.store('accordionTest').controlled = 42")
    page.wait_for_timeout(30)
    page.evaluate("Alpine.store('accordionTest').controlled = []")
    page.wait_for_timeout(30)
    assert sum("CAccordion value received invalid client value" in error for error in errors) == 1
    assert triggers.nth(1).get_attribute("aria-expanded") == "true"
    page.evaluate("Alpine.store('accordionTest').controlled = 'canopy'")
    page.wait_for_timeout(30)
    page.evaluate("Alpine.store('accordionTest').controlled = 42")
    page.wait_for_timeout(30)
    assert sum("CAccordion value received invalid client value" in error for error in errors) == 2


def test_client_values_share_server_newline_and_nul_canonicalization(page: Any):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.set_content(_canonical_value_page())
    page.wait_for_function("document.querySelectorAll('[data-citry-accordion-initialized]').length === 2")
    single = page.locator("#canonical-single")
    multiple = page.locator("#canonical-multiple")
    single_triggers = _direct_triggers(single)
    multiple_triggers = _direct_triggers(multiple)

    page.evaluate(
        "value => Alpine.store('accordionCanonical').single = value",
        "root\rtrail",
    )
    page.evaluate(
        "value => Alpine.store('accordionCanonical').multiple = value",
        ["mist\r\ntrail", "root\rtrail"],
    )
    page.wait_for_timeout(30)
    assert single_triggers.nth(1).get_attribute("aria-expanded") == "true"
    assert multiple_triggers.first.get_attribute("aria-expanded") == "true"
    assert multiple_triggers.nth(1).get_attribute("aria-expanded") == "true"

    page.evaluate(
        "value => Alpine.store('accordionCanonical').multiple = value",
        ["mist\rtrail", "mist\ntrail"],
    )
    page.wait_for_timeout(30)
    page.evaluate(
        "value => Alpine.store('accordionCanonical').multiple = value",
        ["mist\u0000trail"],
    )
    page.wait_for_timeout(30)
    value_errors = [error for error in errors if "CAccordion value received invalid client value" in error]
    assert len(value_errors) == 1
    assert multiple_triggers.first.get_attribute("aria-expanded") == "true"
    assert multiple_triggers.nth(1).get_attribute("aria-expanded") == "true"

    page.evaluate(
        "value => Alpine.store('accordionCanonical').multiple = value",
        ["mist\ntrail"],
    )
    page.wait_for_timeout(30)
    page.evaluate(
        "value => Alpine.store('accordionCanonical').multiple = value",
        ["root\u0000trail"],
    )
    page.wait_for_timeout(30)
    value_errors = [error for error in errors if "CAccordion value received invalid client value" in error]
    assert len(value_errors) == 2


def test_initial_item_registration_coalesces_one_root_reconciliation(page: Any):
    page.set_content(_large_accordion_page(100))
    root = page.locator("#large-accordion")
    root.wait_for()
    page.wait_for_function(
        "document.querySelectorAll('#large-accordion [data-citry-accordion-item-initialized]').length === 100"
    )
    page.wait_for_timeout(30)

    assert root.evaluate("element => element.__citryUiAccordionRuntime.reconciliations") == 1


def test_item_disabled_region_actions_and_native_fieldset_dominance(accordion_page):
    page, errors = accordion_page
    root = page.locator("#guide")
    triggers = _direct_triggers(root)
    floor = triggers.nth(1)
    page.evaluate("Alpine.store('accordionTest').floorDisabled = true")
    page.wait_for_timeout(30)
    assert floor.is_disabled()
    assert floor.get_attribute("data-disabled") == ""
    triggers.first.focus()
    triggers.first.press("ArrowDown")
    assert triggers.nth(2).evaluate("element => element === document.activeElement")

    panels = root.locator(":scope > [data-citry-accordion-item] > [data-citry-accordion-panel]")
    assert panels.first.get_attribute("role") == "region"
    assert panels.first.get_attribute("aria-labelledby") == triggers.first.get_attribute("id")
    actions = root.locator(':scope [data-citry-ui-part="accordion-actions"]').first
    assert actions.get_attribute("role") == "group"
    assert actions.get_attribute("aria-label") == "Canopy actions"

    fieldset = page.locator("#native-fieldset")
    fieldset_root = page.locator("#fieldset-guide")
    fieldset_trigger = _direct_triggers(fieldset_root).first
    fieldset.evaluate("element => element.disabled = true")
    page.wait_for_timeout(30)
    assert fieldset_trigger.is_disabled()
    assert fieldset_root.get_attribute("data-disabled") == ""
    fieldset.evaluate("element => element.disabled = false")
    page.wait_for_timeout(30)
    assert not fieldset_trigger.is_disabled()
    assert fieldset_root.get_attribute("data-disabled") is None

    legend = fieldset.locator(":scope > legend").first
    legend.evaluate("(element, root) => element.append(root)", fieldset_root.element_handle())
    fieldset.evaluate("element => element.disabled = true")
    page.wait_for_timeout(30)
    assert not fieldset_trigger.is_disabled()
    fieldset.evaluate(
        """element => {
          const legend = document.createElement('legend');
          legend.textContent = 'Earlier legend';
          element.prepend(legend);
        }"""
    )
    page.wait_for_timeout(30)
    assert fieldset_trigger.is_disabled()
    assert fieldset_root.get_attribute("data-disabled") == ""
    fieldset.locator(":scope > legend").first.evaluate("element => element.remove()")
    page.wait_for_timeout(30)
    assert not fieldset_trigger.is_disabled()
    assert fieldset_root.get_attribute("data-disabled") is None
    assert errors == []


def test_opening_animation_starts_between_closed_and_natural_height(accordion_page):
    page, errors = accordion_page
    root = page.locator("#guide")
    floor_trigger = _direct_triggers(root).nth(1)
    floor_panel = root.locator(':scope > [data-value="floor"] > [data-citry-accordion-panel]')
    root.evaluate("element => element.style.setProperty('--cui-accordion-duration', '1000ms')")

    floor_trigger.click()
    page.wait_for_timeout(100)
    geometry = floor_panel.evaluate(
        """element => ({
          height: element.getBoundingClientRect().height,
          natural: element.scrollHeight,
          overflow: getComputedStyle(element).overflow,
        })"""
    )
    assert 0 < geometry["height"] < geometry["natural"]
    assert geometry["overflow"] == "clip"
    assert errors == []


def test_public_styling_narrow_layout_rtl_print_and_rapid_reversal(accordion_page):
    page, errors = accordion_page
    root = page.locator("#guide")
    triggers = _direct_triggers(root)
    panel = root.locator(':scope > [data-value="floor"] > [data-citry-accordion-panel]')

    assert root.evaluate("element => getComputedStyle(element).borderRadius") == "20px"
    assert triggers.first.evaluate("element => getComputedStyle(element).borderStartStartRadius") == "20px"
    assert triggers.first.evaluate("element => getComputedStyle(element).borderStartEndRadius") == "0px"
    assert triggers.nth(2).evaluate("element => getComputedStyle(element).borderEndStartRadius") == "20px"
    assert triggers.nth(2).evaluate("element => getComputedStyle(element).borderEndEndRadius") == "20px"
    assert (
        panel.locator(':scope > [data-citry-ui-part="accordion-body"]').evaluate(
            "element => getComputedStyle(element).paddingInlineStart"
        )
        == "24px"
    )
    assert root.evaluate("element => element.scrollWidth <= element.clientWidth") is True
    page.evaluate("Object.assign(Alpine.store('accordionTest'), {indicatorPosition: 'start', size: 'lg'})")
    page.wait_for_timeout(30)
    assert root.get_attribute("data-indicator-pos") == "start"
    assert root.get_attribute("data-size") == "lg"
    page.evaluate("Alpine.store('accordionTest').variant = 'soft'")
    page.wait_for_timeout(30)
    assert root.evaluate("element => getComputedStyle(element).backgroundColor") != "rgba(0, 0, 0, 0)"
    assert (
        root.locator(":scope > [data-citry-accordion-item]").first.evaluate(
            "element => getComputedStyle(element).backgroundColor"
        )
        == "rgba(0, 0, 0, 0)"
    )
    page.evaluate("Alpine.store('accordionTest').variant = 'separated'")
    page.wait_for_timeout(30)
    assert triggers.nth(2).evaluate(
        """element => {
          const style = getComputedStyle(element);
          return [
            style.borderStartStartRadius,
            style.borderStartEndRadius,
            style.borderEndStartRadius,
            style.borderEndEndRadius,
          ];
        }"""
    ) == ["20px", "20px", "20px", "20px"]

    triggers.nth(1).click()
    triggers.nth(2).click()
    triggers.first.click()
    page.wait_for_timeout(260)
    assert triggers.first.get_attribute("aria-expanded") == "true"
    assert (
        root.locator(':scope > [data-citry-accordion-item] > [data-citry-accordion-panel][data-state="open"]').count()
        == 1
    )
    assert (
        root.locator(
            ':scope > [data-citry-accordion-item] > [data-citry-accordion-panel][style*="block-size"]'
        ).count()
        == 0
    )

    page.emulate_media(media="print")
    assert root.locator("[data-citry-accordion-panel]").evaluate_all(
        "elements => elements.every(element => getComputedStyle(element).display !== 'none')"
    )
    assert errors == []


@pytest.mark.parametrize(
    "focus_target",
    [
        "#events-floor-input",
        "#events-floor-action",
        "#events-nested button",
    ],
)
def test_removal_recovers_focus_from_every_owned_item_surface(
    page: Any,
    serve_citry_ui_live: Any,
    focus_target: str,
) -> None:
    app, html = _events_accordion_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function("window.Citry && Citry.events && Citry.events._internal.alpineStarted")
    page.get_by_role("button", name="Forest floor").click()
    page.wait_for_function("document.querySelector('#events-floor-input')?.offsetParent !== null")
    page.evaluate("() => Citry.events.send(document.querySelector('.advance-accordion'), 'advance', {})")
    page.wait_for_function("document.querySelector('#events-accordion > [data-value]').dataset.value === 'understory'")
    target = page.locator(focus_target)
    target.focus()
    assert target.evaluate("element => element === document.activeElement") is True
    page.evaluate("window.__accordionMutateDetails = true")

    page.evaluate("() => Citry.events.send(document.querySelector('.advance-accordion'), 'advance', {})")
    page.wait_for_function("!document.querySelector('#events-accordion [data-value=floor]')")

    understory = page.get_by_role("button", name="Understory")
    assert understory.evaluate("element => element === document.activeElement") is True


def test_correlated_reorder_preserves_focus_and_removal_uses_one_fallback(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _events_accordion_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function("window.Citry && Citry.events && Citry.events._internal.alpineStarted")
    root = page.locator("#events-accordion")
    floor = page.get_by_role("button", name="Forest floor")
    floor.click()
    page.wait_for_function(
        "document.querySelector('#events-accordion [data-value=floor] button').ariaExpanded === 'true'"
    )
    page.evaluate("window.__accordionChange = null")
    floor.focus()
    page.evaluate("window.__accordionRoot = document.querySelector('#events-accordion')")

    outcome = page.evaluate(
        """() => Citry.events.send(document.querySelector('.advance-accordion'), 'advance', {}).then(
          () => ({ok: true}),
          error => ({ok: false, code: error?.code, message: error?.message}),
        )"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function("document.querySelector('#events-accordion > [data-value]').dataset.value === 'understory'")
    assert page.evaluate("document.querySelector('#events-accordion') === window.__accordionRoot") is True
    assert floor.evaluate("element => element === document.activeElement") is True
    assert floor.get_attribute("aria-expanded") == "true"

    page.evaluate("() => Citry.events.send(document.querySelector('.advance-accordion'), 'advance', {})")
    page.wait_for_function("!document.querySelector('#events-accordion [data-value=floor]')")
    understory = page.get_by_role("button", name="Understory")
    assert understory.get_attribute("aria-expanded") == "true"
    assert understory.evaluate("element => element === document.activeElement") is True
    assert page.evaluate("window.__accordionChange") == {
        "value": "understory",
        "detail": {
            "value": "understory",
            "previousValue": "floor",
            "itemValue": None,
            "removedValues": ["floor"],
            "expanded": False,
            "source": "removal",
        },
    }
    assert root.get_attribute("data-citry-accordion-initialized") == ""
