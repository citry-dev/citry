# ruff: noqa: S101
"""Exercise the counters through their declared browser controls."""

import httpx
from playwright.sync_api import Locator, Page, expect


def value(page: Page, identifier: str) -> Locator:
    return page.locator(f"#{identifier} [data-role=value]")


def click(page: Page, identifier: str, action: str) -> None:
    page.locator(f"#{identifier} button[data-action={action}]").click()


def test_initial_html_and_runtime(page: Page, server_url: str) -> None:
    with httpx.Client(trust_env=False) as client:
        response = client.get(server_url)
    assert response.status_code == 200
    # JavaScript-disabled parsing proves the initial text came from Python.
    context = page.context.browser.new_context(java_script_enabled=False)
    static_page = context.new_page()
    static_page.set_content(response.text)
    expect(value(static_page, "counter-a")).to_have_text("2")
    expect(value(static_page, "counter-b")).to_have_text("10")
    context.close()
    assert page.evaluate("typeof window.Alpine !== 'undefined'")


def test_independent_changes_reset_and_negative_values(page: Page) -> None:
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    click(page, "counter-a", "increment")
    click(page, "counter-a", "increment")
    expect(value(page, "counter-a")).to_have_text("4")
    expect(value(page, "counter-b")).to_have_text("10")
    click(page, "counter-b", "decrement")
    expect(value(page, "counter-b")).to_have_text("9")
    expect(value(page, "counter-a")).to_have_text("4")
    click(page, "counter-a", "reset")
    expect(value(page, "counter-a")).to_have_text("2")
    expect(value(page, "counter-b")).to_have_text("9")
    for _ in range(3):
        click(page, "counter-a", "decrement")
    expect(value(page, "counter-a")).to_have_text("-1")
    click(page, "counter-b", "reset")
    expect(value(page, "counter-b")).to_have_text("10")
    assert not requests, f"Counter interactions sent HTTP requests: {requests}"


def test_reload_and_page_isolation(page: Page, server_url: str) -> None:
    click(page, "counter-a", "increment")
    expect(value(page, "counter-a")).to_have_text("3")
    other = page.context.new_page()
    other.goto(server_url, wait_until="networkidle")
    expect(value(other, "counter-a")).to_have_text("2")
    click(other, "counter-b", "increment")
    expect(value(other, "counter-b")).to_have_text("11")
    expect(value(page, "counter-b")).to_have_text("10")
    other.close()
    page.reload(wait_until="networkidle")
    expect(value(page, "counter-a")).to_have_text("2")
    expect(value(page, "counter-b")).to_have_text("10")
