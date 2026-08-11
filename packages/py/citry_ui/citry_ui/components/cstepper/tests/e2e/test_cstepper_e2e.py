"""Browser evidence for Stepper state and native navigation."""

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
    raise RuntimeError("Could not locate repository root for Stepper browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          .brand-stepper { --cui-stepper-radius: 19px; --cui-stepper-active-color: rgb(127 86 217); }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8"><title>Stepper evidence</title><c-css /></head>
            <body x-data>
              <form id="workflow-form" @submit.prevent="$store.stepper.submits += 1">
                <c-CStepper
                  label="Controlled workflow"
                  c-active="1"
                  interactive
                  class_="brand-stepper"
                  $c-props="{
                    active: $store.stepper.active,
                    linear: $store.stepper.linear,
                    orientation: $store.stepper.orientation,
                    variant: $store.stepper.variant,
                    size: $store.stepper.size,
                    onActiveChange: (next, detail) => {
                      $store.stepper.events.push([next, detail.previousActive, detail.controlled]);
                      if ($store.stepper.accept) $store.stepper.active = next;
                    },
                  }"
                >
                  <c-CStep>Profile</c-CStep>
                  <c-CStep>
                    <c-fill name="default">Security</c-fill>
                    <c-fill name="description">Protect the account</c-fill>
                  </c-CStep>
                  <c-CStep>Review</c-CStep>
                </c-CStepper>
                <button id="submit" type="submit">Submit</button>
              </form>

              <fieldset id="fieldset" disabled>
                <legend>Disabled workflow</legend>
                <c-CStepper label="Fieldset workflow" interactive c-linear="False">
                  <c-CStep>One</c-CStep><c-CStep>Two</c-CStep>
                </c-CStepper>
              </fieldset>

              <div dir="rtl" style="inline-size:150px">
                <c-CStepper label="RTL workflow" c-active="1" variant="outline">
                  <c-CStep>بدايةطويلةجدا</c-CStep><c-CStep error>نهايةطويلةجدا</c-CStep>
                </c-CStepper>
              </div>
            </body>
          </html>
        """
        js = """
          Alpine.store('stepper', {
            active: 1, linear: true, orientation: 'horizontal', variant: 'plain', size: 'md',
            accept: false, events: [], submits: 0,
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector('[aria-label="Controlled workflow"][data-citry-stepper-initialized]')
    return errors


def test_controlled_linear_navigation_form_safety_and_acceptance(page: Any) -> None:
    errors = _load(page)
    root = page.locator('[aria-label="Controlled workflow"]')
    triggers = root.locator('[data-citry-ui-part="trigger"]')
    assert triggers.nth(2).is_disabled()
    triggers.nth(0).click()
    assert root.get_attribute("data-active") == "1"
    assert page.evaluate("Alpine.store('stepper').events") == [[0, 1, True]]
    assert page.evaluate("Alpine.store('stepper').submits") == 0

    page.evaluate("Object.assign(Alpine.store('stepper'), {accept: true, linear: false})")
    page.wait_for_function(
        """!document.querySelector(
          '[aria-label="Controlled workflow"] [data-citry-ui-part="step"]:last-child button'
        ).disabled"""
    )
    triggers.nth(2).click()
    page.wait_for_function("document.querySelector('[aria-label=\"Controlled workflow\"]').dataset.active === '2'")
    assert triggers.nth(2).get_attribute("aria-current") == "step"
    assert page.evaluate("Alpine.store('stepper').submits") == 0
    assert errors == []


def test_reactive_configuration_fieldset_and_public_css(page: Any) -> None:
    errors = _load(page)
    root = page.locator('[aria-label="Controlled workflow"]')
    page.evaluate("Object.assign(Alpine.store('stepper'), {orientation:'vertical', variant:'outline', size:'lg'})")
    page.wait_for_function("document.querySelector('[aria-label=\"Controlled workflow\"]').dataset.size === 'lg'")
    assert root.get_attribute("data-orientation") == "vertical"
    assert root.get_attribute("data-variant") == "outline"
    assert root.evaluate("element => getComputedStyle(element).borderRadius") == "19px"

    fieldset_root = page.locator('[aria-label="Fieldset workflow"]')
    assert fieldset_root.locator("button").nth(0).is_disabled()
    page.locator("#fieldset").evaluate("element => element.disabled = false")
    page.wait_for_function("!document.querySelector('[aria-label=\"Fieldset workflow\"] button').disabled")
    assert fieldset_root.locator("button").nth(1).is_enabled()
    assert errors == []


def test_structure_recovery_narrow_rtl_environment_and_axe(page: Any) -> None:
    errors = _load(page)
    root = page.locator('[aria-label="Controlled workflow"]')
    label = root.locator('[data-citry-ui-part="label"]').nth(0)
    label.evaluate("element => element.append(document.createElement('input'))")
    page.wait_for_function(
        """!document.querySelector('[aria-label="Controlled workflow"]')
          .hasAttribute('data-citry-stepper-initialized')"""
    )
    assert root.locator("button").nth(0).is_disabled()
    assert any("CStepper structure" in error for error in errors)
    label.locator("input").evaluate("element => element.remove()")
    page.wait_for_selector('[aria-label="Controlled workflow"][data-citry-stepper-initialized]')

    rtl = page.locator('[aria-label="RTL workflow"]')
    assert rtl.evaluate("element => element.scrollWidth <= element.clientWidth")
    page.emulate_media(reduced_motion="reduce")
    assert (
        root.locator('[data-citry-ui-part="indicator"]')
        .nth(0)
        .evaluate("element => parseFloat(getComputedStyle(element).transitionDuration)")
        <= 0.001
    )
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
