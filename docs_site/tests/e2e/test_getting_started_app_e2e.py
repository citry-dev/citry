"""Browser coverage for the locally mounted getting-started tutorial app."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def _call_response(response: Any) -> bool:
    return response.request.method == "POST" and "/citry/ext/events/call" in response.url


def test_finished_crud_tutorial_isolates_rows_and_syncs_both_filters(
    page: Any,
    getting_started_app_url: str,
) -> None:
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(getting_started_app_url, wait_until="networkidle")
    rows = page.locator(".task-row")
    first = rows.nth(0)
    second = rows.nth(1)

    first.locator("input").fill("no")
    with page.expect_response(_call_response) as invalid_call:
        first.get_by_role("button", name="Save").click()
    assert invalid_call.value.status == 200
    expect(first.get_by_role("alert")).to_have_text("Use at least three characters.")

    second.locator("input").fill("Send the revised invitation")
    with page.expect_response(_call_response) as valid_call:
        second.get_by_role("button", name="Save").click()
    assert valid_call.value.status == 200
    expect(first.get_by_role("alert")).to_have_text("Use at least three characters.")
    expect(second.get_by_role("alert")).to_be_hidden()

    controls = page.locator(".task-list > button")
    expect(controls).to_have_text(["Hide completed tasks", "Hide completed tasks"])
    controls.nth(0).click()
    expect(page.locator(".task-row")).to_have_count(2)
    expect(page.locator(".task-list > button")).to_have_text(["Show all tasks", "Show all tasks"])

    page.locator(".task-list > button").nth(1).click()
    expect(page.locator(".task-row")).to_have_count(3)
    expect(page.locator(".task-list > button")).to_have_text(["Hide completed tasks", "Hide completed tasks"])
    assert page_errors == []


def test_finished_crud_tutorial_displays_the_calling_rows_saved_event(
    page: Any,
    getting_started_app_url: str,
) -> None:
    page.goto(getting_started_app_url, wait_until="networkidle")
    second = page.locator(".task-row").nth(1)
    second.locator("input").fill("Send the revised invitation")
    with page.expect_response(_call_response):
        second.get_by_role("button", name="Save").click()
    expect(second.locator("output")).to_have_text("Saved task 2: Send the revised invitation")


def test_welcome_live_snippet_runs_state_and_dispatch_on_local_runtime(
    page: Any,
    getting_started_app_url: str,
) -> None:
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(getting_started_app_url + "/welcome", wait_until="networkidle")
    output = page.locator(".welcome-card output")
    expect(output).to_have_text("0")

    page.get_by_role("button", name="Say hello from Python").click()
    expect(output).to_have_text("1")
    page.get_by_role("button", name="Say hello from Python").click()
    expect(output).to_have_text("2")

    assert page_errors == []
