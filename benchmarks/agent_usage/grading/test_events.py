# ruff: noqa: S101
"""Observe server responses and the plan chooser after each interaction."""

from playwright.sync_api import Page, expect

PLANS = {"starter": ("Starter", 12), "team": ("Team", 29), "scale": ("Scale", 79)}


def assert_plan(page: Page, key: str) -> None:
    label, price = PLANS[key]
    expect(page.locator("#selected-plan")).to_have_text(label)
    expect(page.locator("#selected-price")).to_have_text(f"${price} / month")
    for plan in PLANS:
        expect(page.locator(f"button[data-plan={plan}]")).to_have_attribute(
            "aria-pressed", "true" if plan == key else "false"
        )


def choose(page: Page, key: str) -> None:
    current_url = page.url
    with page.expect_response(
        lambda response: "/citry/" in response.url and response.request.method == "POST"
    ) as received:
        page.locator(f"button[data-plan={key}]").click()
    response = received.value
    assert response.ok
    # A rendered event response distinguishes server work from a local text swap.
    body = response.text()
    assert "selected-plan" in body
    assert PLANS[key][0] in body
    assert "selected-price" in body
    assert str(PLANS[key][1]) in body
    assert_plan(page, key)
    assert page.url == current_url


def test_initial_selection(page: Page) -> None:
    assert_plan(page, "starter")


def test_server_events_and_repeated_choices(page: Page) -> None:
    for key in ["team", "scale", "scale", "starter", "team"]:
        choose(page, key)


def test_choices_are_independent_per_page(page: Page, server_url: str) -> None:
    choose(page, "scale")
    other = page.context.new_page()
    other.goto(server_url, wait_until="networkidle")
    assert_plan(other, "starter")
    choose(other, "team")
    assert_plan(page, "scale")
    other.close()
    page.reload(wait_until="networkidle")
    assert_plan(page, "starter")
