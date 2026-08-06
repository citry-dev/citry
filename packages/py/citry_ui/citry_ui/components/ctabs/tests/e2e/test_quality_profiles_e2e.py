"""Bounded Phase 7.5 quality profiles for the shared Tabs scenario."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry_ui.quality.routes import render_scenario

pytestmark = pytest.mark.e2e


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the e2e test path."
    raise RuntimeError(msg)


def _load_tabs(page: Any, html: str) -> None:
    page.set_content(html, wait_until="load")
    page.wait_for_function(
        "document.querySelector('[data-citry-tabs-root]')?.hasAttribute('data-citry-tabs-initialized')"
    )


def _with_external_css(html: str, css: str, *, after_citry: bool) -> str:
    stylesheet = f'<style data-quality-external-css="">{css}</style>'
    if after_citry:
        return html.replace("</head>", stylesheet + "</head>", 1)
    first_citry_style = html.find('<style data-citry-css-class="')
    if first_citry_style < 0:
        msg = "Rendered scenario did not contain a Citry stylesheet."
        raise RuntimeError(msg)
    return html[:first_citry_style] + stylesheet + html[first_citry_style:]


def test_tabs_overview_accessibility_and_keyboard_contract(page: Any) -> None:
    _load_tabs(page, render_scenario("tabs.overview"))

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
    html = _with_external_css(
        render_scenario("tabs.overview"),
        css_path.read_text(encoding="utf-8"),
        after_citry=after_citry,
    )
    _load_tabs(page, html)

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
