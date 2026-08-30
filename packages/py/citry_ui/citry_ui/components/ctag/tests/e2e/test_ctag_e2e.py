"""Browser evidence for Tag collection ownership and keyboard behavior."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for Tag browser tests.")


def _tag_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><title>Tag contract</title><c-css /></head>
            <body
              x-data="{accept: false, fieldsetDisabled: false}"
              x-init="Alpine.store('tagTest', {
                selected: 'alpha', events: [], itemDisabled: false,
                variant: 'soft', size: 'md'
              })"
            >
              <c-CTagGroup
                label="Controlled topics"
                selection_mode="single"
                actionable
                removable
                id="controlled"
                $c-props="{
                  value: $store.tagTest.selected,
                  variant: $store.tagTest.variant,
                  size: $store.tagTest.size,
                  onValueChange: (value, detail) => {
                    $store.tagTest.events.push(['value', value, detail.previousValue]);
                    if (accept) $store.tagTest.selected = value;
                  },
                  onAction: (value) => $store.tagTest.events.push(['action', value]),
                  onRemove: (values, detail) => $store.tagTest.events.push([
                    'remove', values.join(','), detail.source
                  ])
                }"
              >
                <c-CTag value="alpha">Alpha</c-CTag>
                <c-CTag value="beta" $c-props="{disabled: $store.tagTest.itemDisabled}">Beta</c-CTag>
                <c-CTag value="gamma">Gamma</c-CTag>
              </c-CTagGroup>

              <c-CTagGroup
                label="Amenities"
                selection_mode="multiple"
                c-value="['wifi']"
                removable
                id="uncontrolled"
                $c-props="{
                  onRemove: (values, detail) => $store.tagTest.events.push([
                    'remove', values.join(','), detail.source
                  ])
                }"
              >
                <c-CTag value="wifi">Wi-Fi</c-CTag>
                <c-CTag value="parking">Parking</c-CTag>
                <c-CTag value="pool">Pool</c-CTag>
              </c-CTagGroup>

              <fieldset id="native-fieldset" x-bind:disabled="fieldsetDisabled">
                <legend>Native ownership</legend>
                <c-CTagGroup
                  label="Fieldset topics"
                  selection_mode="single"
                  value="one"
                  id="fieldset-group"
                >
                  <c-CTag value="one">One</c-CTag>
                  <c-CTag value="two">Two</c-CTag>
                </c-CTagGroup>
              </fieldset>

              <c-CTagGroup label="Descriptive" id="descriptive">
                <c-CTag value="plain">Plain label</c-CTag>
              </c-CTagGroup>
              <button id="after" type="button">After</button>
            </body>
          </html>
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_tag_page(), wait_until="load")
    page.wait_for_selector("#controlled[data-citry-tag-group-initialized]")
    page.wait_for_function("document.querySelectorAll('#controlled [data-citry-tag-initialized]').length === 3")
    return errors


def test_controlled_selection_action_order_and_reactive_presentation(page: Any) -> None:
    errors = _load(page)
    controlled = page.locator("#controlled")
    alpha = controlled.get_by_role("row", name="Alpha")
    beta = controlled.get_by_role("row", name="Beta")

    beta.click()
    page.wait_for_function("Alpine.store('tagTest').events.length === 2")
    assert page.evaluate("Alpine.store('tagTest').events") == [
        ["value", "beta", "alpha"],
        ["action", "beta"],
    ]
    assert alpha.get_attribute("aria-selected") == "true"
    assert beta.get_attribute("aria-selected") == "false"

    page.evaluate("Alpine.$data(document.body).accept = true")
    beta.click()
    page.wait_for_function("Alpine.store('tagTest').selected === 'beta'")
    page.wait_for_function("document.querySelector('#controlled [data-value=beta]').hasAttribute('data-selected')")
    assert beta.get_attribute("aria-selected") == "true"

    page.evaluate("Object.assign(Alpine.store('tagTest'), {variant: 'outline', size: 'lg'})")
    page.wait_for_function("document.querySelector('#controlled').dataset.size === 'lg'")
    assert controlled.get_attribute("data-variant") == "outline"
    assert controlled.locator('[data-citry-ui-part="tag"][data-size="lg"]').count() == 3
    assert errors == []


def test_roving_keyboard_typeahead_remove_button_and_selected_delete(page: Any) -> None:
    errors = _load(page)
    group = page.locator("#uncontrolled")
    wifi = group.get_by_role("row", name="Wi-Fi")
    parking = group.get_by_role("row", name="Parking")
    pool = group.get_by_role("row", name="Pool")

    wifi.focus()
    page.keyboard.press("ArrowRight")
    assert parking.evaluate("element => element === document.activeElement")
    page.keyboard.press("End")
    assert pool.evaluate("element => element === document.activeElement")
    page.keyboard.press("w")
    assert wifi.evaluate("element => element === document.activeElement")

    page.keyboard.press("Tab")
    remove = group.get_by_role("button", name="Remove Wi-Fi")
    assert remove.evaluate("element => element === document.activeElement")
    page.keyboard.press("Shift+Tab")
    assert wifi.evaluate("element => element === document.activeElement")

    page.keyboard.press("Delete")
    page.wait_for_function("Alpine.store('tagTest').events.some((event) => event[0] === 'remove')")
    assert page.evaluate("Alpine.store('tagTest').events.at(-1)") == [
        "remove",
        "wifi",
        "delete-key",
    ]
    assert errors == []


def test_item_and_native_fieldset_disabled_states_dominate_activation(page: Any) -> None:
    errors = _load(page)
    controlled = page.locator("#controlled")
    beta = controlled.get_by_role("row", name="Beta")
    page.evaluate("Alpine.store('tagTest').itemDisabled = true")
    page.wait_for_function(
        "document.querySelector('#controlled [data-value=beta]').getAttribute('aria-disabled') === 'true'"
    )
    before = page.evaluate("Alpine.store('tagTest').events.length")
    beta.click(force=True)
    page.wait_for_timeout(30)
    assert page.evaluate("Alpine.store('tagTest').events.length") == before

    page.locator("#fieldset-group").get_by_role("row", name="One").focus()
    page.evaluate("Alpine.$data(document.body).fieldsetDisabled = true")
    page.wait_for_function("document.querySelector('#fieldset-group').hasAttribute('data-disabled')")
    assert page.locator("#fieldset-group").get_by_role("row", name="One").get_attribute("tabindex") == "-1"
    assert page.locator("#fieldset-group [data-citry-ui-part='list']").evaluate(
        "element => element === document.activeElement"
    )
    page.evaluate("Alpine.$data(document.body).fieldsetDisabled = false")
    page.wait_for_function("!document.querySelector('#fieldset-group').hasAttribute('data-disabled')")
    assert errors == []


def test_roles_css_environment_and_axe_are_clean(page: Any) -> None:
    errors = _load(page)
    assert page.locator("#descriptive").get_attribute("data-selection-mode") == "none"
    assert page.locator("#descriptive [role=list]").count() == 1
    assert page.locator("#controlled [role=grid]").count() == 1
    page.emulate_media(reduced_motion="reduce")
    assert (
        page.locator("#controlled [data-citry-ui-part=tag]").first.evaluate(
            "element => getComputedStyle(element).transitionDuration"
        )
        == "0s"
    )
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file()
    page.add_script_tag(path=str(axe_path))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes: ['violations']})).violations
          .filter((item) => ['serious', 'critical'].includes(item.impact))
          .map((item) => item.id)"""
    )
    assert violations == []
    assert errors == []
