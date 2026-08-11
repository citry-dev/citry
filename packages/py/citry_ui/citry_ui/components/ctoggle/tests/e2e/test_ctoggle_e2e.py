"""Browser evidence for standalone and grouped Toggle ownership."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry_ui.components._context import FORM_CONTEXT_KEY

pytestmark = pytest.mark.e2e


def _toggle_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class DisabledFormContext(Component):
        citry = app
        template = "<div data-test-form-context><c-slot /></div>"
        js = """
          $component({
            init: ({reactive, provide, effect}) => {
              const context = reactive({disabled: true, readonly: false});
              provide(Symbol.for("citry-ui:form"), context);
              const stop = effect(() => {
                context.disabled = Alpine.store("toggleTest").formContextDisabled;
              });
              return () => stop?.();
            },
          })
        """

        def template_data(self, kwargs, slots):
            self.provide(
                FORM_CONTEXT_KEY,
                form_id="disabled-form",
                disabled=True,
                readonly=False,
            )
            return {}

    app.register(DisabledFormContext)

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
              x-init="Alpine.store('toggleTest', {
                single: 'sky',
                changes: [],
                itemClicked: false,
                itemDisabled: false,
                groupVariant: 'outline',
                groupSize: 'md',
                formLocalDisabled: false,
                formContextDisabled: true
              })"
            >
              <c-CToggle c-attrs="{'id': 'standalone'}">Grid</c-CToggle>
              <c-CToggleGroup
                label="View"
                value="sky"
                c-mandatory="True"
                c-attrs="{'id': 'single'}"
                $c-props="{
                  value: $store.toggleTest.single,
                  variant: $store.toggleTest.groupVariant,
                  size: $store.toggleTest.groupSize,
                  onValueChange: (value, detail) => {
                    $store.toggleTest.changes.push(detail);
                    $store.toggleTest.single = value;
                  }
                }"
              >
                <c-CToggle value="sky">Sky</c-CToggle>
                <c-CToggle
                  value="map"
                  @click.stop="$store.toggleTest.itemClicked = true"
                  $c-props="{disabled: $store.toggleTest.itemDisabled}"
                >Map</c-CToggle>
              </c-CToggleGroup>
              <c-CToggleGroup
                label="Layers"
                c-multiple="True"
                c-value="['stars']"
                c-attrs="{'id': 'multiple'}"
              >
                <c-CToggle value="stars">Stars</c-CToggle>
                <c-CToggle value="labels">Labels</c-CToggle>
              </c-CToggleGroup>
              <c-DisabledFormContext>
                <c-CToggle
                  c-attrs="{'id': 'form-standalone'}"
                  $c-props="{disabled: $store.toggleTest.formLocalDisabled}"
                >Form-owned standalone</c-CToggle>
                <c-CToggleGroup
                  label="Form-owned group"
                  c-attrs="{'id': 'form-group'}"
                  $c-props="{disabled: $store.toggleTest.formLocalDisabled}"
                >
                  <c-CToggle value="form-item">Form item</c-CToggle>
                </c-CToggleGroup>
              </c-DisabledFormContext>
            </body>
          </html>
        """

    return str(Page())


def test_standalone_and_grouped_activation_follow_pressed_ownership(page: Any) -> None:
    page.set_content(_toggle_page(), wait_until="load")
    page.wait_for_selector("#single[data-citry-toggle-group-initialized]")

    standalone = page.locator("#standalone")
    standalone.click()
    assert standalone.get_attribute("aria-pressed") == "true"

    page.locator("#single").get_by_role("button", name="Map").click()
    page.wait_for_function("Alpine.store('toggleTest').single === 'map'")
    assert page.locator("#single").get_by_role("button", name="Sky").get_attribute("aria-pressed") == "false"
    assert page.locator("#single").get_by_role("button", name="Map").get_attribute("aria-pressed") == "true"
    assert page.evaluate("Alpine.store('toggleTest').itemClicked") is True
    assert page.evaluate("Alpine.store('toggleTest').changes.at(-1).previousValue") == "sky"

    labels = page.locator("#multiple").get_by_role("button", name="Labels")
    labels.click()
    assert labels.get_attribute("aria-pressed") == "true"


def test_group_and_item_disabled_state_stay_synchronized(page: Any) -> None:
    page.set_content(_toggle_page(), wait_until="load")
    page.wait_for_selector("#single[data-citry-toggle-group-initialized]")
    item = page.locator("#single").get_by_role("button", name="Map")

    page.evaluate("Alpine.store('toggleTest').itemDisabled = true")
    page.wait_for_function("document.querySelector('#single button[data-value=map]').disabled")
    assert item.get_attribute("data-disabled") is not None

    page.evaluate("Alpine.store('toggleTest').itemDisabled = false")
    page.wait_for_function("!document.querySelector('#single button[data-value=map]').disabled")
    assert item.get_attribute("data-disabled") is None

    page.evaluate("Object.assign(Alpine.store('toggleTest'), {groupVariant: 'soft', groupSize: 'lg'})")
    page.wait_for_function("document.querySelector('#single button[data-value=map]').dataset.variant === 'soft'")
    assert page.locator("#single [data-citry-ui-part='toggle'][data-size='lg']").count() == 2


def test_enclosing_form_disabled_context_cannot_be_cleared_by_client_props(page: Any) -> None:
    page.set_content(_toggle_page(), wait_until="load")
    page.wait_for_selector("#form-group[data-citry-toggle-group-initialized]")

    standalone = page.locator("#form-standalone")
    group = page.locator("#form-group")
    item = group.get_by_role("button", name="Form item")
    assert standalone.is_disabled()
    assert item.is_disabled()
    assert group.get_attribute("data-disabled") is not None

    page.evaluate("Alpine.store('toggleTest').formLocalDisabled = true")
    page.evaluate("Alpine.store('toggleTest').formLocalDisabled = false")
    page.wait_for_timeout(50)
    assert standalone.is_disabled()
    assert item.is_disabled()
    assert group.get_attribute("data-disabled") is not None

    page.evaluate("Alpine.store('toggleTest').formContextDisabled = false")
    page.wait_for_function("!document.querySelector('#form-standalone').disabled")
    assert item.is_enabled()
    assert group.get_attribute("data-disabled") is None
