"""Browser evidence for Listbox interaction and accessibility."""

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
    raise RuntimeError("Could not locate repository root for Listbox browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          .brand-listbox {
            --cui-listbox-radius: 19px;
            --cui-listbox-selected-background: rgb(92 45 145);
            --cui-listbox-selected-foreground: white;
          }
        """
        template = """
          <!doctype html>
          <html lang="en"><head><meta charset="utf-8"><title>Listbox evidence</title><c-css /></head>
          <body x-data>
            <c-CListbox
              label="People"
              value="ada"
              class_="brand-listbox"
              variant="outline"
              $c-props="{
                value: $store.listbox.value,
                mandatory: $store.listbox.mandatory,
                disabled: $store.listbox.disabled,
                loop: $store.listbox.loop,
                variant: $store.listbox.variant,
                size: $store.listbox.size,
                onValueChange: (next, detail) => {
                  $store.listbox.events.push([next, detail.previousValue, detail.source, detail.controlled]);
                  if ($store.listbox.accept) $store.listbox.value = next;
                },
              }"
            >
              <c-CListboxOption value="ada" text_value="Ada Lovelace">
                <c-fill name="start"><span>AL</span></c-fill>
                <c-fill name="default">Ada Lovelace</c-fill>
                <c-fill name="description">Analytical engine</c-fill>
                <c-fill name="end">Available</c-fill>
              </c-CListboxOption>
              <c-CListboxOption value="grace">Grace Hopper</c-CListboxOption>
              <c-CListboxOption value="disabled" disabled>Disabled person</c-CListboxOption>
              <c-CListboxGroup label="Contemporary">
                <c-CListboxOption value="margaret">Margaret Hamilton</c-CListboxOption>
                <c-CListboxOption value="radia">Radia Perlman</c-CListboxOption>
              </c-CListboxGroup>
            </c-CListbox>

            <c-CListbox
              label="Topics"
              multiple
              mandatory
              c-value="['accessibility']"
              class_="multiple-listbox"
              $c-props="{
                value: $store.listbox.multiple,
                onValueChange: (next, detail) => {
                  $store.listbox.multipleEvents.push([next, detail.selected, detail.source]);
                  $store.listbox.multiple = next;
                },
              }"
            >
              <c-CListboxOption value="accessibility">Accessibility</c-CListboxOption>
              <c-CListboxOption value="performance">Performance</c-CListboxOption>
              <c-CListboxOption value="security">Security</c-CListboxOption>
            </c-CListbox>

            <fieldset id="fieldset" disabled>
              <legend>Locked</legend>
              <c-CListbox label="Locked list" class_="locked-listbox">
                <c-CListboxOption value="a">A</c-CListboxOption>
                <c-CListboxOption value="b">B</c-CListboxOption>
              </c-CListbox>
            </fieldset>

            <div dir="rtl" style="inline-size:130px">
              <c-CListbox label="RTL people" class_="rtl-listbox" variant="soft">
                <c-CListboxOption value="long">عنصرطويلللغايةبدونمسافات</c-CListboxOption>
                <c-CListboxOption value="second">عنصرثانطويلللغايةبدونمسافات</c-CListboxOption>
              </c-CListbox>
            </div>
          </body></html>
        """
        js = """
          Alpine.store('listbox', {
            value: 'ada', accept: false, mandatory: false, disabled: false, loop: false,
            variant: 'outline', size: 'md', events: [],
            multiple: ['accessibility'], multipleEvents: [],
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector(".brand-listbox[data-citry-listbox-initialized]")
    page.wait_for_selector(".multiple-listbox[data-citry-listbox-initialized]")
    return errors


def _option(page: Any, selector: str, value: str) -> Any:
    return page.locator(f'{selector} [role="option"][data-value="{value}"]')


def test_controlled_single_rejection_acceptance_release_and_configuration(page: Any) -> None:
    errors = _load(page)
    grace = _option(page, ".brand-listbox", "grace")
    grace.click()
    assert grace.get_attribute("aria-selected") == "false"
    assert page.evaluate("Alpine.store('listbox').events")[-1] == ["grace", "ada", "pointer", True]

    page.evaluate("Alpine.store('listbox').accept = true")
    grace.click()
    page.wait_for_function(
        "document.querySelector('.brand-listbox [data-value=grace]').getAttribute('aria-selected') === 'true'"
    )
    page.evaluate("Alpine.store('listbox').value = undefined")
    page.wait_for_timeout(20)
    _option(page, ".brand-listbox", "margaret").click()
    assert _option(page, ".brand-listbox", "margaret").get_attribute("aria-selected") == "true"

    page.evaluate(
        """Object.assign(Alpine.store('listbox'), {
          disabled: true, variant: 'soft', size: 'lg', loop: true
        })"""
    )
    page.wait_for_function("document.querySelector('.brand-listbox').dataset.size === 'lg'")
    root = page.locator(".brand-listbox")
    assert root.get_attribute("data-variant") == "soft"
    assert root.get_attribute("data-disabled") == ""
    _option(page, ".brand-listbox", "ada").click(force=True)
    assert _option(page, ".brand-listbox", "ada").get_attribute("aria-selected") == "false"
    assert errors == []


def test_keyboard_typeahead_multiple_mandatory_and_disabled_options(page: Any) -> None:
    errors = _load(page)
    ada = _option(page, ".brand-listbox", "ada")
    ada.focus()
    ada.press("ArrowDown")
    grace = _option(page, ".brand-listbox", "grace")
    assert grace.evaluate("element => document.activeElement === element")
    grace.press("ArrowDown")
    assert _option(page, ".brand-listbox", "margaret").evaluate("element => document.activeElement === element")
    _option(page, ".brand-listbox", "margaret").press("r")
    assert _option(page, ".brand-listbox", "radia").evaluate("element => document.activeElement === element")
    _option(page, ".brand-listbox", "radia").press("Home")
    assert ada.evaluate("element => document.activeElement === element")
    ada.press("End")
    assert _option(page, ".brand-listbox", "radia").evaluate("element => document.activeElement === element")

    selected = _option(page, ".multiple-listbox", "accessibility")
    selected.click()
    assert selected.get_attribute("aria-selected") == "true"
    assert page.evaluate("Alpine.store('listbox').multipleEvents") == []
    performance = _option(page, ".multiple-listbox", "performance")
    performance.press(" ")
    page.wait_for_function(
        "document.querySelector('.multiple-listbox [data-value=performance]').getAttribute('aria-selected') === 'true'"
    )
    selected.click()
    page.wait_for_function(
        """document.querySelector('.multiple-listbox [data-value=accessibility]')
          .getAttribute('aria-selected') === 'false'"""
    )
    assert page.evaluate("Alpine.store('listbox').multiple") == ["performance"]
    assert errors == []


def test_focused_option_disable_and_removal_move_to_nearest_survivor(page: Any) -> None:
    errors = _load(page)
    grace = _option(page, ".brand-listbox", "grace")
    grace.focus()
    grace.evaluate("element => element.setAttribute('data-cui-listbox-option-disabled', '')")
    page.wait_for_function("document.querySelector('.brand-listbox [data-value=ada]') === document.activeElement")

    margaret = _option(page, ".brand-listbox", "margaret")
    margaret.focus()
    margaret.evaluate("element => element.remove()")
    page.wait_for_function("document.querySelector('.brand-listbox [data-value=radia]') === document.activeElement")
    assert errors == []


def test_fieldset_fail_closed_environment_narrow_rtl_and_axe(page: Any) -> None:
    errors = _load(page)
    assert _option(page, ".locked-listbox", "a").get_attribute("tabindex") == "-1"
    page.locator("#fieldset").evaluate("element => element.disabled = false")
    page.wait_for_function("document.querySelector('.locked-listbox [role=option]').tabIndex === 0")

    label = page.locator('.brand-listbox [data-citry-ui-part="listbox-option-label"]').first
    label.evaluate(
        """element => {
          const link = document.createElement('a');
          link.href='#late'; link.textContent='late'; element.append(link);
        }"""
    )
    page.wait_for_function("!document.querySelector('.brand-listbox').hasAttribute('data-citry-listbox-initialized')")
    assert page.locator('.brand-listbox [role="listbox"]').evaluate("element => element.inert")
    assert any("CListbox structure" in error for error in errors)
    label.locator("a").evaluate("element => element.remove()")
    page.wait_for_selector(".brand-listbox[data-citry-listbox-initialized]")

    rtl = page.locator(".rtl-listbox")
    assert rtl.evaluate("element => element.scrollWidth <= element.clientWidth")
    assert (
        page.locator('.brand-listbox [role="listbox"]').evaluate("element => getComputedStyle(element).borderRadius")
        == "19px"
    )
    page.emulate_media(reduced_motion="reduce")
    assert (
        page.locator('.brand-listbox [data-citry-ui-part="listbox-indicator"]').first.evaluate(
            "element => parseFloat(getComputedStyle(element).transitionDuration) || 0"
        )
        <= 0.001
    )
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert [error for error in errors if "CListbox structure" not in error] == []
