"""Bounded Phase 7.5 quality profiles for the shared Tabs scenario."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the e2e test path."
    raise RuntimeError(msg)


def _wait_for_tabs(page: Any) -> None:
    page.wait_for_function(
        "document.querySelector('[data-citry-tabs-root]')?.hasAttribute('data-citry-tabs-initialized')"
    )


def test_tabs_overview_accessibility_and_keyboard_contract(page: Any, open_scenario: Any) -> None:
    open_scenario("tabs.overview")
    _wait_for_tabs(page)

    tab_list = page.get_by_role("tablist", name="Account settings")
    tabs = tab_list.get_by_role("tab")
    assert tabs.count() == 3
    assert tab_list.is_visible()
    assert page.get_by_role("tab", name="Billing").is_disabled()

    account = page.get_by_role("tab", name="Account")
    account.focus()
    account.press("ArrowRight")
    notifications = page.get_by_role("tab", name="Notifications")
    assert notifications.get_attribute("aria-selected") == "true"
    assert page.get_by_role("tabpanel", name="Notifications").is_visible()
    assert page.locator("#tabs-overview-selection").text_content() == "notifications"

    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` at the repository root before Citry UI axe tests"
    page.add_script_tag(path=str(axe_path))
    violations = page.evaluate(
        """async () => {
          const result = await axe.run(document, { resultTypes: ['violations'] });
          return result.violations.filter(
            (violation) => violation.impact === 'serious' || violation.impact === 'critical',
          );
        }"""
    )
    assert violations == []


@pytest.mark.parametrize(
    ("framework", "after_citry"),
    [
        ("bootstrap", False),
        ("bootstrap", True),
        ("tailwind", False),
        ("tailwind", True),
    ],
)
def test_tabs_remains_operable_with_real_framework_css(
    page: Any,
    open_scenario: Any,
    framework: str,
    after_citry: bool,
) -> None:
    root = _repository_root()
    css_path = (
        root / "node_modules" / "bootstrap" / "dist" / "css" / "bootstrap.min.css"
        if framework == "bootstrap"
        else root / "packages" / "py" / "citry_ui" / "citry_ui" / "quality" / "css" / ".generated" / "tailwind.css"
    )
    assert css_path.is_file(), "run `pnpm install` and `pnpm run citry-ui:quality-css` before CSS coexistence tests"
    # The fixture places the framework stylesheet and fails unless it lands
    # on the requested side of every Citry stylesheet.
    open_scenario(
        "tabs.overview",
        framework_css=css_path.read_text(encoding="utf-8"),
        framework_css_after_citry=after_citry,
    )
    _wait_for_tabs(page)

    tab_list = page.get_by_role("tablist", name="Account settings")
    root_part = tab_list.locator("xpath=..")
    notifications = page.get_by_role("tab", name="Notifications")
    assert root_part.is_visible()
    assert tab_list.is_visible()
    assert notifications.is_visible()
    assert notifications.evaluate("element => element.getBoundingClientRect().height >= 24") is True

    notifications.click()
    assert notifications.get_attribute("aria-selected") == "true"
    assert page.get_by_role("tabpanel", name="Notifications").is_visible()
    assert page.get_by_role("tabpanel", name="Account").is_hidden()
