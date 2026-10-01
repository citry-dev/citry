"""
Browser coverage for the getting-started steps that have runnable files.

Each step's files run in a real server (see getting_started_app.py), and each
test does what the step asks the reader to do, so a step that stops working
fails here. The browser-only steps 3, 5, 6, and 7 run from the `live` server;
steps 8 to 13 each run in their own. Steps 1 and 4 show code only inside the
page, and the step 2 card example has its own tests beside it in
docs_site/examples/card.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def _call_response(response: Any) -> bool:
    return response.request.method == "POST" and "/citry/ext/events/call" in response.url


def _open(page: Any, url: str) -> list[str]:
    # Every step must run without a browser error, so each test collects them
    # and checks the list in its own body, where an expected failure covers it.
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url, wait_until="networkidle")
    return errors


def test_step3_reading_list_renders_one_item_per_book(page: Any, getting_started_urls: dict[str, str]) -> None:
    errors = _open(page, getting_started_urls["live"] + "/reading_list")
    expect(page.locator("li")).to_have_count(3)
    expect(page.locator("ul")).to_have_attribute("data-count", "3")
    assert errors == []


def test_step5_reading_panel_fills_both_slots(page: Any, getting_started_urls: dict[str, str]) -> None:
    errors = _open(page, getting_started_urls["live"] + "/reading_panel")
    panels = page.locator(".reading-panel")
    expect(panels).to_have_count(2)
    # The first panel keeps the footer fallback; the second fills the footer.
    expect(panels.nth(0).locator("footer button")).to_have_count(0)
    expect(panels.nth(1).locator("footer button")).to_have_count(1)
    assert errors == []


def test_step6_click_counters_count_independently(page: Any, getting_started_urls: dict[str, str]) -> None:
    errors = _open(page, getting_started_urls["live"] + "/click_counters")
    first, second = page.locator(".counter").nth(0), page.locator(".counter").nth(1)
    first.click()
    first.click()
    expect(first.locator(".counter__count")).to_have_text("2")
    expect(second.locator(".counter__count")).to_have_text("0")
    assert errors == []


@pytest.mark.parametrize(("server", "path"), [("live", "/connected_components"), ("8", "/")])
def test_step7_and_step8_child_button_changes_the_parent_choice(
    page: Any, getting_started_urls: dict[str, str], server: str, path: str
) -> None:
    # Step 8 serves step 7's components through FastAPI unchanged.
    errors = _open(page, getting_started_urls[server] + path)
    choice = page.locator(".choice-picker__value")
    expect(choice).to_have_text("Ocean")
    page.locator(".choice-button").click()
    expect(choice).to_have_text("Forest")
    page.locator(".choice-button").click()
    expect(choice).to_have_text("Ocean")
    assert errors == []


def _load_choices(page: Any) -> None:
    with page.expect_response(_call_response) as call:
        page.get_by_role("button", name="Load choices").click()
    assert call.value.status == 200


def test_step9_click_loads_choices_from_python(page: Any, getting_started_urls: dict[str, str]) -> None:
    errors = _open(page, getting_started_urls["9"])
    choice = page.locator(".choice-picker__value")
    expect(choice).to_be_hidden()
    _load_choices(page)
    expect(choice).to_have_text("Ocean")
    page.locator(".choice-button").click()
    expect(choice).to_have_text("Forest")
    assert errors == []


def test_step10_state_alternates_the_loaded_batch(page: Any, getting_started_urls: dict[str, str]) -> None:
    errors = _open(page, getting_started_urls["10"])
    choice = page.locator(".choice-picker__value")
    _load_choices(page)
    expect(choice).to_have_text("Ocean")
    page.locator(".choice-button").click()
    expect(choice).to_have_text("Forest")
    # Python read the advanced State, so the second call loads the next batch.
    _load_choices(page)
    expect(choice).to_have_text("History")
    page.locator(".choice-button").click()
    expect(choice).to_have_text("Science")
    assert errors == []


def test_step10_counter_shows_the_state_python_advanced(page: Any, getting_started_urls: dict[str, str]) -> None:
    errors = _open(page, getting_started_urls["10"])
    counter = page.locator("p output").first
    expect(counter).to_have_text("0")
    _load_choices(page)
    expect(counter).to_have_text("1", timeout=2_000)
    _load_choices(page)
    expect(counter).to_have_text("2", timeout=2_000)
    assert errors == []


def _submit_email(page: Any, email: str) -> None:
    page.get_by_label("Work email").fill(email)
    with page.expect_response(_call_response) as call:
        page.get_by_role("button", name="Send request").click()
    assert call.value.status == 200


def test_step11_form_shows_the_field_error_then_the_accepted_address(
    page: Any, getting_started_urls: dict[str, str]
) -> None:
    errors = _open(page, getting_started_urls["11"])
    error = page.locator(".signup-form__error")
    _submit_email(page, "ada@elsewhere.test")
    expect(error).to_have_text("Use an @example.com address.")
    # The visitor's input survives the error.
    expect(page.get_by_label("Work email")).to_have_value("ada@elsewhere.test")

    _submit_email(page, "ada@example.com")
    expect(error).to_be_hidden()
    expect(page.locator("p[role=status]")).to_contain_text("ada@example.com")
    assert errors == []


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="type-changing Render, #164")
def test_step12_python_replaces_the_form_with_a_confirmation(page: Any, getting_started_urls: dict[str, str]) -> None:
    errors = _open(page, getting_started_urls["12"])
    _submit_email(page, "ada@elsewhere.test")
    expect(page.locator(".signup-form__error")).to_have_text("Use an @example.com address.")

    _submit_email(page, "ada@example.com")
    confirmation = page.locator(".confirmation")
    try:
        expect(confirmation).to_contain_text("ada@example.com", timeout=3_000)
    except AssertionError:
        # Only the browser's type-change rejection is the expected failure;
        # anything else fails the test outright instead of hiding behind it.
        if not any("cannot replace component" in error for error in errors):
            msg = f"step 12 failed without the type-change rejection; page errors: {errors}"
            raise RuntimeError(msg) from None
        raise
    expect(page.locator("form")).to_have_count(0)
    # The confirmation's CSS and Vue data arrived with the response.
    assert confirmation.evaluate("element => getComputedStyle(element).borderTopStyle") == "solid"
    expect(page.locator(".confirmation__status")).to_contain_text("ada@example.com")
    assert errors == []


def test_step13_crud_tutorial_isolates_rows_and_syncs_both_filters(
    page: Any, getting_started_urls: dict[str, str]
) -> None:
    errors = _open(page, getting_started_urls["13"])
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
    expect(second.locator("output")).to_have_text("Saved task 2: Send the revised invitation")

    controls = page.locator(".task-list > button")
    expect(controls).to_have_text(["Hide completed tasks", "Hide completed tasks"])
    controls.nth(0).click()
    expect(page.locator(".task-row")).to_have_count(2)
    expect(page.locator(".task-list > button")).to_have_text(["Show all tasks", "Show all tasks"])

    page.locator(".task-list > button").nth(1).click()
    expect(page.locator(".task-row")).to_have_count(3)
    expect(page.locator(".task-list > button")).to_have_text(["Hide completed tasks", "Hide completed tasks"])
    assert errors == []


def test_welcome_live_snippet_runs_state_and_dispatch_on_local_runtime(
    page: Any, getting_started_urls: dict[str, str]
) -> None:
    errors = _open(page, getting_started_urls["live"] + "/welcome")
    output = page.locator(".welcome-card output")
    expect(output).to_have_text("0")

    page.get_by_role("button", name="Say hello from Python").click()
    expect(output).to_have_text("1")
    page.get_by_role("button", name="Say hello from Python").click()
    expect(output).to_have_text("2")
    assert errors == []
