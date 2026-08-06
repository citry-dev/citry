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
    if scenario_id == "button.states":
        page.get_by_role("button", name="Client-controlled loading").click()
        return
    if scenario_id == "field-input.states":
        page.get_by_role("textbox", name="Controlled species note").fill("x")
        return
    if scenario_id == "form.states":
        page.get_by_role("button", name="Submit", exact=True).click()
        return
    if scenario_id == "tabs.overview":
        page.get_by_role("tab", name="Notifications").click()
        return
    if scenario_id == "dialog.states":
        page.get_by_role("button", name="Open observatory log").click()
        page.wait_for_function("document.querySelector('#quality-dialog').open")
        return
    if scenario_id == "combobox.states":
        page.get_by_role("combobox", name="Remote catalog").fill("Vega")
        page.wait_for_timeout(50)
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
    page.set_content(render_scenario(scenario.id), wait_until="load")
    page.wait_for_selector(scenario.ready_selector)
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before Citry UI axe tests"
    page.add_script_tag(path=str(axe_path))

    initial = _axe_findings(page)
    assert initial["violations"] == []

    _activate_representative_state(page, scenario.id)
    active = _axe_findings(page)
    assert active["violations"] == []
    incomplete_rules = {finding["id"] for group in (initial["incomplete"], active["incomplete"]) for finding in group}
    assert incomplete_rules <= AXE_INCOMPLETE_DISPOSITIONS.keys()

    # The compact record makes axe's manual-review surface visible in test
    # output without pretending automation can resolve it.
    page.evaluate(
        "findings => { window.__citryUiAxeIncomplete = findings; }",
        {"initial": initial["incomplete"], "active": active["incomplete"]},
    )


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
