"""Cross-family browser evidence from the shared Phase 7.5 scenarios."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry_ui.quality.accessibility import AXE_INCOMPLETE_DISPOSITIONS
from citry_ui.quality.routes import render_scenario
from citry_ui.quality.scenarios import SCENARIOS, QualityTool

pytestmark = pytest.mark.e2e

_BROWSER_SCENARIOS = tuple(scenario for scenario in SCENARIOS if QualityTool.BROWSER in scenario.tools)


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the e2e test path."
    raise RuntimeError(msg)


def _axe_findings(page: Any) -> dict[str, list[dict[str, object]]]:
    result = page.evaluate(
        """async () => {
          const result = await axe.run(document, {
            resultTypes: ['violations', 'incomplete'],
          });
          return {
            violations: result.violations.filter(
              (finding) => finding.impact === 'serious' || finding.impact === 'critical',
            ),
            incomplete: result.incomplete.map((finding) => ({
              id: finding.id,
              impact: finding.impact,
              nodes: finding.nodes.length,
            })),
          };
        }"""
    )
    return result


def _with_external_css(html: str, css: str, *, after_citry: bool) -> str:
    stylesheet = f'<style data-quality-external-css="">{css}</style>'
    if after_citry:
        return html.replace("</head>", stylesheet + "</head>", 1)
    first_citry_style = html.find('<style data-citry-css-class="')
    if first_citry_style < 0:
        msg = "Rendered scenario did not contain a Citry stylesheet."
        raise RuntimeError(msg)
    return html[:first_citry_style] + stylesheet + html[first_citry_style:]


def _activate_representative_state(page: Any, scenario_id: str) -> None:
    if scenario_id == "accordion.states":
        page.get_by_role("button", name="Understory").click()
        return
    if scenario_id == "disclosure.states":
        page.get_by_role("button", name="System requirements").click()
        return
    if scenario_id == "alert.states":
        page.get_by_role("button", name="Mark synchronized").click()
        return
    if scenario_id == "button.states":
        page.get_by_role("button", name="Client-controlled loading").click()
        return
    if scenario_id == "field-input.states":
        page.get_by_role("textbox", name="Controlled species note").fill("x")
        return
    if scenario_id == "progress.states":
        page.locator('[data-quality-state="controlled"] button').click()
        return
    if scenario_id == "spinner.states":
        page.locator('[data-quality-state="controlled"] button').click()
        return
    if scenario_id == "radio.states":
        page.locator('[data-quality-state="controlled"] button').click()
        return
    if scenario_id == "switch.states":
        page.locator('[data-quality-state="controlled"] button').click()
        return
    if scenario_id == "form.states":
        page.get_by_role("button", name="Submit", exact=True).click()
        return
    if scenario_id == "textarea.states":
        page.get_by_role("button", name="Release controlled value").click()
        page.get_by_role("button", name="Reset journal").click()
        return
    if scenario_id == "native-select.states":
        page.get_by_role("button", name="Release controlled value").click()
        page.get_by_role("button", name="Reset survey").click()
        return
    if scenario_id == "checkbox.states":
        page.get_by_role("button", name="Release controlled state").click()
        page.get_by_role("button", name="Reset checklist").click()
        return
    if scenario_id == "tabs.overview":
        page.get_by_role("tab", name="Notifications").click()
        return
    if scenario_id == "dialog.states":
        page.get_by_role("button", name="Open observatory log").click()
        page.wait_for_function("document.querySelector('#quality-dialog').open")
        return
    if scenario_id == "alert-dialog.states":
        page.get_by_role("button", name="Delete project").click()
        page.wait_for_function("document.querySelector('#quality-delete-project').open")
        return
    if scenario_id == "popover.states":
        page.get_by_role("button", name="Inspect Europa").click()
        page.wait_for_function("document.querySelector('#quality-popover').matches(':popover-open')")
        return
    if scenario_id == "drawer.states":
        page.get_by_role("button", name="Edit observatory note").click()
        page.wait_for_function("document.querySelector('#quality-drawer').matches(':modal')")
        return
    if scenario_id == "tooltip.states":
        page.get_by_role("button", name="Europa").focus()
        page.wait_for_function("document.querySelector('#quality-tooltip').matches(':popover-open')")
        return
    if scenario_id == "menu.states":
        page.get_by_role("button", name="Open archive index").click()
        page.wait_for_function("document.querySelector('#quality-menu').matches(':popover-open')")
        return
    if scenario_id == "navigation-menu.states":
        page.get_by_role("button", name="المزيد").click()
        page.wait_for_function(
            "document.querySelector('[data-value=rtl-more][data-citry-navigation-menu-trigger]')"
            ".getAttribute('aria-expanded') === 'true'"
        )
        return
    if scenario_id == "carousel.states":
        carousel = page.get_by_role("region", name="Featured stories")
        carousel.get_by_role("button", name="Next slide").click()
        page.wait_for_function("document.querySelector('[aria-label=\"Featured stories\"]').dataset.index === '1'")
        return
    if scenario_id == "toast.states":
        page.get_by_role("button", name="Add notification").click()
        page.get_by_role("button", name="Retry").click()
        return
    if scenario_id == "combobox.states":
        page.get_by_role("combobox", name="Remote catalog").fill("Vega")
        page.wait_for_timeout(50)
        return
    if scenario_id == "toggle.states":
        page.get_by_role("button", name="Standalone pressed").click()
        return
    if scenario_id == "pagination.states":
        page.locator('[data-citry-ui-part="pagination"]').nth(1).get_by_role("button", name="Next page").click()
        return
    if scenario_id == "workflow.repeatable-contacts":
        page.get_by_role("button", name="Add contact").click()
        return
    if scenario_id == "composition.orbit-access":
        page.get_by_role("textbox", name="Full name").fill("Lin Chen")
        return
    if scenario_id == "composition.ledger-dashboard":
        page.get_by_role("button", name="Create report").click()
        page.wait_for_function("document.querySelector('#ledger-report-dialog').open")


@pytest.mark.parametrize("scenario", _BROWSER_SCENARIOS, ids=lambda scenario: scenario.id)
def test_shared_scenario_semantics_and_active_state_have_no_high_impact_axe_findings(
    page: Any,
    scenario: Any,
) -> None:
    console_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.set_content(render_scenario(scenario.id), wait_until="load")
    page.wait_for_selector(scenario.ready_selector, state="attached")
    if scenario.id == "textarea.states":
        assert page.locator(".cui-textarea").count() == 13
        assert page.locator(".cui-textarea[data-citry-textarea-initialized]").count() == 13
    if scenario.id == "native-select.states":
        assert page.locator(".cui-native-select").count() == 11
        assert page.locator(".cui-native-select[data-citry-native-select-initialized]").count() == 11
    if scenario.id == "checkbox.states":
        assert page.locator(".cui-checkbox").count() == 12
        assert page.locator(".cui-checkbox[data-citry-checkbox-initialized]").count() == 12
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before Citry UI axe tests"
    page.add_script_tag(path=str(axe_path))

    initial = _axe_findings(page)
    assert initial["violations"] == []

    _activate_representative_state(page, scenario.id)
    active = _axe_findings(page)
    assert active["violations"] == []
    if scenario.id in {
        "accordion.states",
        "disclosure.states",
        "alert.states",
        "alert-dialog.states",
        "textarea.states",
        "native-select.states",
        "checkbox.states",
        "toggle.states",
        "pagination.states",
        "menu.states",
        "navigation-menu.states",
        "carousel.states",
        "drawer.states",
        "toast.states",
    }:
        assert console_errors == []
    incomplete_rules = {finding["id"] for group in (initial["incomplete"], active["incomplete"]) for finding in group}
    assert incomplete_rules <= AXE_INCOMPLETE_DISPOSITIONS.keys()

    # The compact record makes axe's manual-review surface visible in test
    # output without pretending automation can resolve it.
    page.evaluate(
        "findings => { window.__citryUiAxeIncomplete = findings; }",
        {"initial": initial["incomplete"], "active": active["incomplete"]},
    )


def test_accordion_quality_form_continuity_and_brand_contrast(page: Any) -> None:
    page.set_content(render_scenario("accordion.states"), wait_until="load")
    page.wait_for_selector('[data-quality-states~="brand-fern"][data-citry-accordion-initialized]')
    form = page.locator("#accordion-quality-form")
    control = form.locator('[name="ridge-note"]')
    assert form.locator('[data-value="upland"] button').get_attribute("aria-expanded") == "false"
    assert page.evaluate("Array.from(new FormData(document.querySelector('#accordion-quality-form')).entries())") == [
        ["ridge-note", "Dry trail"]
    ]
    control.evaluate("element => element.value = 'Changed trail'")
    form.evaluate("element => element.reset()")
    assert control.input_value() == "Dry trail"

    contrast_script = """() => {
      const channels = (value) => {
        const numbers = value.match(/[0-9.]+/g).map(Number);
        return value.startsWith('color(srgb')
          ? numbers.slice(0, 3)
          : numbers.slice(0, 3).map((channel) => channel / 255);
      };
      const luminance = (value) => channels(value)
        .map((channel) => channel <= 0.04045
          ? channel / 12.92
          : ((channel + 0.055) / 1.055) ** 2.4)
        .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
      return ['brand-fern', 'brand-river'].map((brand) => {
        const root = document.querySelector(`[data-quality-states~="${brand}"]`);
        const trigger = root.querySelector('[data-citry-accordion-trigger]');
        const foreground = luminance(getComputedStyle(trigger).color);
        const background = luminance(getComputedStyle(root).backgroundColor);
        return (Math.max(foreground, background) + 0.05)
          / (Math.min(foreground, background) + 0.05);
      });
    }"""
    for color_scheme in ("light", "dark"):
        page.emulate_media(color_scheme=color_scheme)
        assert all(ratio >= 4.5 for ratio in page.evaluate(contrast_script))


def test_disclosure_quality_form_continuity_and_brand_contrast(page: Any) -> None:
    page.set_content(render_scenario("disclosure.states"), wait_until="load")
    page.wait_for_selector('[data-quality-states~="brand-orchard"][data-citry-disclosure-initialized]')
    form = page.locator("#disclosure-quality-form")
    control = form.locator('[name="email"]')
    trigger = form.get_by_role("button", name="Notification settings")
    control.fill("changed@example.com")
    trigger.click()
    assert trigger.get_attribute("aria-expanded") == "false"
    assert page.evaluate("Array.from(new FormData(document.querySelector('#disclosure-quality-form')).entries())") == [
        ["email", "changed@example.com"]
    ]
    trigger.click()
    assert control.input_value() == "changed@example.com"
    form.evaluate("element => element.reset()")
    assert control.input_value() == "ops@example.com"

    contrast_script = """() => {
      const rgba = (value) => {
        const numbers = value.match(/[0-9.]+/g).map(Number);
        const channels = value.startsWith('color(srgb')
          ? numbers.slice(0, 3)
          : numbers.slice(0, 3).map((channel) => channel / 255);
        return [...channels, numbers[3] ?? 1];
      };
      const composite = (front, back) => [
        ...front.slice(0, 3).map(
          (channel, index) => channel * front[3] + back[index] * (1 - front[3]),
        ),
        1,
      ];
      const luminance = (value) => value.slice(0, 3)
        .map((channel) => channel <= 0.04045
          ? channel / 12.92
          : ((channel + 0.055) / 1.055) ** 2.4)
        .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
      return ['brand-orchard', 'brand-harbor'].map((brand) => {
        const root = document.querySelector(`[data-quality-states~="${brand}"]`);
        const trigger = root.querySelector('[data-citry-ui-part="disclosure-trigger"]');
        const triggerStyle = getComputedStyle(trigger);
        const rootBackground = rgba(getComputedStyle(root).backgroundColor);
        const triggerBackground = composite(rgba(triggerStyle.backgroundColor), rootBackground);
        const foreground = luminance(composite(rgba(triggerStyle.color), triggerBackground));
        const background = luminance(triggerBackground);
        return (Math.max(foreground, background) + 0.05)
          / (Math.min(foreground, background) + 0.05);
      });
    }"""
    for color_scheme in ("light", "dark"):
        page.emulate_media(color_scheme=color_scheme)
        assert all(ratio >= 4.5 for ratio in page.evaluate(contrast_script))


def test_menu_quality_form_safety_native_disabledness_and_brand_contrast(page: Any) -> None:
    page.set_content(render_scenario("menu.states"), wait_until="load")
    page.wait_for_selector("#quality-menu[data-citry-menu-initialized]", state="attached")

    page.get_by_role("button", name="Open archive index").click()
    page.get_by_role("menuitem", name="Copy citation").click()
    assert page.locator("#quality-menu").evaluate("element => element.matches(':popover-open')")
    assert page.locator("form output").text_content() == "Submits: 0"
    assert page.evaluate("Array.from(new FormData(document.querySelector('.menu-quality form')).entries())") == []

    disabled_trigger = page.get_by_role("button", name="Desk commands")
    assert disabled_trigger.evaluate("element => element.matches(':disabled')") is True
    disabled_trigger.evaluate("element => element.click()")
    assert page.locator("#quality-disabled-menu").evaluate("element => element.matches(':popover-open')") is False

    contrast_script = """() => {
      const channels = (value) => value.match(/[0-9.]+/g).slice(0, 3).map(Number)
        .map((channel) => channel / 255);
      const luminance = (value) => channels(value)
        .map((channel) => channel <= 0.04045
          ? channel / 12.92
          : ((channel + 0.055) / 1.055) ** 2.4)
        .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
      return ['brand-moon', 'brand-ember'].map((brand) => {
        const surface = document.querySelector(`[data-quality-states~="${brand}"]`);
        const foreground = luminance(getComputedStyle(surface).color);
        const background = luminance(getComputedStyle(surface).backgroundColor);
        return (Math.max(foreground, background) + 0.05)
          / (Math.min(foreground, background) + 0.05);
      });
    }"""
    for color_scheme in ("light", "dark"):
        page.emulate_media(color_scheme=color_scheme)
        assert all(ratio >= 4.5 for ratio in page.evaluate(contrast_script))


@pytest.mark.parametrize("scenario_id", ["composition.orbit-access", "composition.ledger-dashboard"])
@pytest.mark.parametrize("framework", ["bootstrap", "tailwind"])
@pytest.mark.parametrize("after_citry", [False, True], ids=("framework-first", "framework-last"))
def test_representative_compositions_coexist_with_pinned_framework_css(
    page: Any,
    scenario_id: str,
    framework: str,
    after_citry: bool,
) -> None:
    root = _repository_root()
    css_path = (
        root / "node_modules" / "bootstrap" / "dist" / "css" / "bootstrap.min.css"
        if framework == "bootstrap"
        else root / "packages" / "py" / "citry_ui" / "citry_ui" / "quality" / "css" / ".generated" / "tailwind.css"
    )
    assert css_path.is_file(), "run `pnpm install` and `pnpm run citry-ui:quality-css` first"
    html = _with_external_css(
        render_scenario(scenario_id),
        css_path.read_text(encoding="utf-8"),
        after_citry=after_citry,
    )
    scenario = next(scenario for scenario in SCENARIOS if scenario.id == scenario_id)
    page.set_content(html, wait_until="load")
    page.wait_for_selector(scenario.ready_selector)

    if scenario_id == "composition.orbit-access":
        control = page.get_by_role("button", name="Request access")
        assert page.get_by_role("textbox", name="Full name").is_visible()
    else:
        control = page.get_by_role("tab", name="Overview")
        assert page.get_by_role("table", name="Active delivery work").is_visible()

    assert control.is_visible()
    assert control.evaluate("element => element.getBoundingClientRect().height >= 24") is True
    assert control.evaluate("element => getComputedStyle(element).boxSizing") == "border-box"
