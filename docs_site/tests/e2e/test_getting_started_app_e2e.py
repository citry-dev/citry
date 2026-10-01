"""
Browser coverage for every getting-started tutorial step.

Each step's files run in a real server (see getting_started_app.py), and each
test does what the step asks the reader to do, so a step that stops working
fails here. The earlier, browser-only steps run from the `live` server.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

# Every step must run without a browser error, so each test checks for one.
pytestmark = [pytest.mark.e2e, pytest.mark.usefixtures("page_errors")]


def _call_response(response: Any) -> bool:
    return response.request.method == "POST" and "/citry/ext/events/call" in response.url


@pytest.fixture
def page_errors(page: Any) -> Iterator[list[str]]:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    yield errors
    assert errors == []


def test_step3_reading_list_renders_one_item_per_book(page: Any, getting_started_urls: dict[str, str]) -> None:
    page.goto(getting_started_urls["live"] + "/reading_list", wait_until="networkidle")
    expect(page.locator("li")).to_have_count(3)
    expect(page.locator("ul")).to_have_attribute("data-count", "3")


def test_step5_reading_panel_fills_both_slots(page: Any, getting_started_urls: dict[str, str]) -> None:
    page.goto(getting_started_urls["live"] + "/reading_panel", wait_until="networkidle")
    panels = page.locator(".reading-panel")
    expect(panels).to_have_count(2)
    # The first panel keeps the footer fallback; the second fills the footer.
    expect(panels.nth(0).locator("footer button")).to_have_count(0)
    expect(panels.nth(1).locator("footer button")).to_have_count(1)


def test_step6_click_counters_count_independently(page: Any, getting_started_urls: dict[str, str]) -> None:
    page.goto(getting_started_urls["live"] + "/click_counters", wait_until="networkidle")
    first, second = page.locator(".counter").nth(0), page.locator(".counter").nth(1)
    first.click()
    first.click()
    expect(first.locator(".counter__count")).to_have_text("2")
    expect(second.locator(".counter__count")).to_have_text("0")


@pytest.mark.parametrize(("server", "path"), [("live", "/connected_components"), ("8", "/")])
def test_step7_and_step8_child_button_changes_the_parent_choice(
    page: Any, getting_started_urls: dict[str, str], server: str, path: str
) -> None:
    # Step 8 serves step 7's components through FastAPI unchanged.
    page.goto(getting_started_urls[server] + path, wait_until="networkidle")
    choice = page.locator(".choice-picker__value")
    expect(choice).to_have_text("Ocean")
    page.locator(".choice-button").click()
    expect(choice).to_have_text("Forest")
    page.locator(".choice-button").click()
    expect(choice).to_have_text("Ocean")


def _load_choices(page: Any) -> None:
    with page.expect_response(_call_response) as call:
        page.get_by_role("button", name="Load choices").click()
    assert call.value.status == 200


def test_step9_click_loads_choices_from_python(page: Any, getting_started_urls: dict[str, str]) -> None:
    page.goto(getting_started_urls["9"], wait_until="networkidle")
    choice = page.locator(".choice-picker__value")
    expect(choice).to_be_hidden()
    _load_choices(page)
    expect(choice).to_have_text("Ocean")
    page.locator(".choice-button").click()
    expect(choice).to_have_text("Forest")


def test_step10_state_alternates_the_loaded_batch(page: Any, getting_started_urls: dict[str, str]) -> None:
    page.goto(getting_started_urls["10"], wait_until="networkidle")
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


@pytest.mark.xfail(
    strict=True,
    reason=(
        "A `state` action carries only the signed token, not the public State values, so `$state` "
        "keeps its first value until the component renders again."
    ),
)
def test_step10_counter_shows_the_state_python_advanced(page: Any, getting_started_urls: dict[str, str]) -> None:
    page.goto(getting_started_urls["10"], wait_until="networkidle")
    counter = page.locator("p output").first
    expect(counter).to_have_text("0")
    _load_choices(page)
    expect(counter).to_have_text("1", timeout=2_000)
    _load_choices(page)
    expect(counter).to_have_text("2", timeout=2_000)


def _submit_email(page: Any, email: str) -> None:
    page.get_by_label("Work email").fill(email)
    with page.expect_response(_call_response) as call:
        page.get_by_role("button", name="Send request").click()
    assert call.value.status == 200


def test_step11_form_shows_the_field_error_then_the_accepted_address(
    page: Any, getting_started_urls: dict[str, str]
) -> None:
    page.goto(getting_started_urls["11"], wait_until="networkidle")
    error = page.locator(".signup-form__error")
    _submit_email(page, "ada@elsewhere.test")
    expect(error).to_have_text("Use an @example.com address.")
    # The visitor's input survives the error.
    expect(page.get_by_label("Work email")).to_have_value("ada@elsewhere.test")

    _submit_email(page, "ada@example.com")
    expect(error).to_be_hidden()
    expect(page.locator("p[role=status]")).to_contain_text("ada@example.com")


def test_step12_python_renders_the_form_again_as_a_confirmation(
    page: Any, getting_started_urls: dict[str, str]
) -> None:
    page.goto(getting_started_urls["12"], wait_until="networkidle")
    _submit_email(page, "ada@elsewhere.test")
    expect(page.locator(".signup-form__error")).to_have_text("Use an @example.com address.")

    # Screen readers announce the confirmation only if the live region that
    # receives it was already on the page, so remember the element.
    page.evaluate("window.__liveRegion = document.querySelector('[aria-live]')")
    _submit_email(page, "ada@example.com")
    confirmation = page.locator("[aria-live] .confirmation")
    expect(confirmation).to_contain_text("ada@example.com")
    expect(page.locator("form")).to_have_count(0)
    assert page.evaluate("document.querySelector('[aria-live]') === window.__liveRegion")
    # The confirmation's CSS and Vue data arrived with the response.
    assert confirmation.evaluate("element => getComputedStyle(element).borderTopStyle") == "solid"
    expect(page.locator(".confirmation__status")).to_contain_text("ada@example.com")


def test_step13_crud_tutorial_isolates_rows_and_syncs_both_filters(
    page: Any, getting_started_urls: dict[str, str]
) -> None:
    page.goto(getting_started_urls["13"], wait_until="networkidle")
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


def test_welcome_live_snippet_runs_state_and_dispatch_on_local_runtime(
    page: Any, getting_started_urls: dict[str, str]
) -> None:
    page.goto(getting_started_urls["live"] + "/welcome", wait_until="networkidle")
    output = page.locator(".welcome-card output")
    expect(output).to_have_text("0")

    page.get_by_role("button", name="Say hello from Python").click()
    expect(output).to_have_text("1")
    page.get_by_role("button", name="Say hello from Python").click()
    expect(output).to_have_text("2")
