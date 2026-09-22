"""Browser checks for the mounted landing page and its shared document chrome."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from docs_site._internal.project import default_docs_project

pytestmark = pytest.mark.e2e


def test_landing_page_mounts_shared_chrome_and_both_social_rows(page: Any, local_docs_site_url: str) -> None:
    """The prepared shell must mount the same header and footer users see elsewhere."""
    page_errors: list[str] = []
    console_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(error.stack or str(error)))
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    response = page.goto(local_docs_site_url + "/", wait_until="networkidle")

    assert response is not None
    assert response.status == 200
    try:
        page.locator("main#landing-main").wait_for(timeout=10_000)
    except PlaywrightTimeoutError:
        pytest.fail(f"landing page did not mount: {page_errors=}, {console_errors=}, {page.content()[:500]=}")

    assert page.locator("body.citry-landing-page").count() == 1
    assert page.locator("header.djc-header").count() == 1
    nav = page.locator("nav[aria-label='Primary navigation']")
    assert nav.count() == 1
    assert nav.locator('a[href="/docs/"]').count() == 1
    assert page.locator("#landing-main .landing-hero").count() == 1

    assert page.locator("nav[aria-label='Section navigation']").count() == 0
    assert page.locator("aside#djc-toc").count() == 0
    assert page.locator("nav.djc-breadcrumbs").count() == 0
    assert page.locator(".djc-layout").count() == 0

    rows = page.locator(".social-links")
    assert rows.count() == 2
    settings = default_docs_project().settings
    expected_labels = ["GitHub", "PyPI", "Discord"]
    expected_urls = [settings.repository.url, settings.pypi_url, settings.discord_url]
    for row_index in range(rows.count()):
        links = rows.nth(row_index).locator("a.social-links__link")
        assert links.count() == 3
        assert [links.nth(index).get_attribute("aria-label") for index in range(3)] == expected_labels
        assert [links.nth(index).get_attribute("href") for index in range(3)] == expected_urls
        assert [links.nth(index).get_attribute("rel") for index in range(3)] == ["noopener"] * 3

    assert not page_errors
    assert not console_errors
