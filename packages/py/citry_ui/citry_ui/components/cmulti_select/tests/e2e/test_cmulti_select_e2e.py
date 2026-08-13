"""Browser evidence for MultiSelect interaction, forms, and overlays."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry_ui import CMultiSelectOption

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate the repository root for MultiSelect browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = ".primary-multi { inline-size: 20rem; }"
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8">
          <title>MultiSelect evidence</title><c-css /></head>
          <body x-data>
            <form
              id="planet-form"
              @submit.prevent="$store.multi.submits = Array.from(new FormData($event.target).entries())"
            >
              <c-CMultiSelect
                class_="primary-multi"
                c-options="options"
                placeholder="Choose planets"
                name="planet"
                c-value="['earth']"
                required
                c-trigger_attrs="{'aria-label': 'Planets'}"
                $c-props="{
                  value: $store.multi.value,
                  open: $store.multi.open,
                  disabled: $store.multi.disabled,
                  readonly: $store.multi.readonly,
                  loop: $store.multi.loop,
                  closeOnSelect: $store.multi.closeOnSelect,
                  variant: $store.multi.variant,
                  size: $store.multi.size,
                  onValueChange: (next, detail) => {
                    $store.multi.values.push([next, detail.previousValue, detail.source, detail.controlled]);
                    if ($store.multi.accept) $store.multi.value = next;
                  },
                  onOpenChange: (next, detail) => {
                    $store.multi.opens.push([next, detail.reason, detail.controlled, detail.forced]);
                    if ($store.multi.acceptOpen) $store.multi.open = next;
                  },
                }"
              />
              <button id="submit" type="submit">Submit</button>
              <button id="reset" type="reset">Reset</button>
            </form>
            <fieldset id="locked" disabled>
              <legend>Locked</legend>
              <c-CMultiSelect
                class_="locked-multi"
                c-options="options"
                placeholder="Choose"
                c-trigger_attrs="{'aria-label': 'Locked planets'}"
              />
            </fieldset>
            <c-CMultiSelect
              class_="exact-multi"
              c-options="exact_options"
              c-value="exact_values"
              placeholder="Exact"
              c-trigger_attrs="{'aria-label': 'Exact values'}"
              $c-props="{value: $store.multi.exact}"
            />
            <dialog id="modal"><button autofocus type="button">Modal action</button></dialog>
          </body></html>
        """
        js = """
          Alpine.store('multi', {
            value:['earth'], open:undefined, disabled:false, readonly:false, loop:false,
            closeOnSelect:false, variant:'outline', size:'md', accept:false, acceptOpen:false,
            values:[], opens:[], submits:[],
            exact:[' alpha ', 'line\\nfeed'],
          });
        """

        def template_data(self, kwargs, slots):
            return {
                "options": [
                    CMultiSelectOption("earth", "Earth"),
                    CMultiSelectOption("mars", "Mars", "The red planet", group="Rocky"),
                    CMultiSelectOption("venus", "Venus", disabled=True, group="Rocky"),
                    CMultiSelectOption("jupiter", "Jupiter", group="Gas giants"),
                ],
                "exact_options": [
                    CMultiSelectOption(" alpha ", "Spaced"),
                    CMultiSelectOption("line\nfeed", "Line feed"),
                ],
                "exact_values": (" alpha ", "line\nfeed"),
            }

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector(".primary-multi[data-citry-multi-select-initialized]")
    return errors


def _control(page: Any) -> Any:
    return page.locator('.primary-multi [role="combobox"]')


def _option(page: Any, value: str) -> Any:
    return page.locator(f'.primary-multi [role="option"][data-value="{value}"]')


def _chips(page: Any) -> list[str]:
    return [value.strip() for value in _control(page).locator('[data-citry-ui-part="chip"]').all_text_contents()]


def test_controlled_values_reject_accept_release_and_popup_stays_open(page: Any) -> None:
    errors = _load(page)
    control = _control(page)
    control.click()
    _option(page, "mars").click()
    assert control.get_attribute("aria-expanded") == "true"
    assert _chips(page) == ["Earth"]
    assert page.evaluate("Alpine.store('multi').values.at(-1)") == [
        ["earth", "mars"],
        ["earth"],
        "pointer",
        True,
    ]

    page.evaluate("Alpine.store('multi').accept = true")
    _option(page, "mars").click()
    page.wait_for_function("document.querySelectorAll('.primary-multi [data-citry-ui-part=chip]').length === 2")
    assert _chips(page) == ["Earth", "Mars"]

    page.evaluate("Alpine.store('multi').value = undefined")
    _option(page, "jupiter").click()
    assert _chips(page) == ["Earth", "Mars", "Jupiter"]
    assert errors == []


def test_keyboard_typeahead_disabled_options_close_on_select_and_tab(page: Any) -> None:
    errors = _load(page)
    control = _control(page)
    page.evaluate("Alpine.store('multi').value = undefined")
    control.focus()
    control.press("ArrowUp")
    assert control.get_attribute("aria-expanded") == "true"
    assert control.get_attribute("aria-activedescendant") == _option(page, "earth").get_attribute("id")
    control.press("Home")
    control.press("ArrowDown")
    assert control.get_attribute("aria-activedescendant") == _option(page, "mars").get_attribute("id")
    control.press("ArrowDown")
    assert control.get_attribute("aria-activedescendant") == _option(page, "jupiter").get_attribute("id")
    control.press("m")
    control.press("Enter")
    assert "Mars" in _chips(page)
    page.evaluate("Alpine.store('multi').closeOnSelect = true")
    control.press("Enter")
    page.wait_for_function("document.querySelector('.primary-multi [role=combobox]').ariaExpanded === 'false'")
    control.click()
    control.press("Tab")
    page.wait_for_function("document.querySelector('.primary-multi [role=combobox]').ariaExpanded === 'false'")
    assert errors == []


def test_native_repeated_form_reset_readonly_fieldset_and_modal_safety(page: Any) -> None:
    errors = _load(page)
    control = _control(page)
    page.evaluate("Alpine.store('multi').value = undefined")
    control.click()
    _option(page, "mars").click()
    control.press("Escape")
    page.locator("#submit").click()
    assert page.evaluate("Alpine.store('multi').submits") == [["planet", "earth"], ["planet", "mars"]]
    page.locator("#reset").click()
    page.wait_for_function("document.querySelectorAll('.primary-multi [data-citry-ui-part=chip]').length === 1")
    assert _chips(page) == ["Earth"]

    page.evaluate("Alpine.store('multi').readonly = true")
    page.locator("#submit").click()
    assert page.evaluate("Alpine.store('multi').submits") == [["planet", "earth"]]
    control.click()
    assert control.get_attribute("aria-expanded") == "false"

    locked = page.locator('.locked-multi [role="combobox"]')
    assert locked.is_disabled()
    page.locator("#locked").evaluate("element => element.disabled = false")
    page.wait_for_function("!document.querySelector('.locked-multi [role=combobox]').disabled")
    locked.click()
    assert locked.get_attribute("aria-expanded") == "true"

    page.evaluate("Alpine.store('multi').readonly = false")
    control.click()
    page.locator("#modal").evaluate("element => element.showModal()")
    page.wait_for_function("document.querySelector('.primary-multi [role=combobox]').ariaExpanded === 'false'")
    assert page.evaluate("Alpine.store('multi').opens.at(-1).slice(1)") == ["ancestor", False, True]
    assert errors == []


def test_canceled_reset_after_target_listener_preserves_multiselect_state(page: Any) -> None:
    errors = _load(page)
    page.evaluate("Alpine.store('multi').value = undefined")
    control = _control(page)
    control.click()
    _option(page, "mars").click()
    control.press("Escape")
    page.evaluate(
        """() => document.querySelector('#planet-form')
          .addEventListener('reset', event => event.preventDefault(), {once:true})"""
    )
    page.locator("#reset").click()
    page.wait_for_timeout(50)
    assert _chips(page) == ["Earth", "Mars"]
    assert errors == []


def test_exact_whitespace_and_line_feed_values_remain_selected(page: Any) -> None:
    errors = _load(page)
    selected = page.locator(".exact-multi select option:checked").evaluate_all(
        "options => options.map(option => option.value)"
    )
    assert selected == [" alpha ", "line\nfeed"]
    assert page.locator(".exact-multi [data-citry-ui-part=chip]").count() == 2
    assert errors == []


def test_css_geometry_reduced_motion_and_axe(page: Any) -> None:
    errors = _load(page)
    control = _control(page)
    control.click()
    popup = page.locator('.primary-multi [data-citry-ui-part="popup"]')
    assert abs(popup.bounding_box()["width"] - control.bounding_box()["width"]) < 1.5
    page.emulate_media(reduced_motion="reduce")
    assert (
        popup.evaluate(
            "element => parseFloat(getComputedStyle(element).getPropertyValue('--_cui-multi-select-duration')) || 0"
        )
        == 0
    )
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert errors == []
