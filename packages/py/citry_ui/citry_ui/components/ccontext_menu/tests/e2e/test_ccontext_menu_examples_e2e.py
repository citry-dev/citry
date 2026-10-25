"""Browser evidence that the ContextMenu examples act on what their callbacks report."""

from __future__ import annotations

import importlib
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import expect

from citry import Component
from citry import citry as default_citry

pytestmark = pytest.mark.e2e


class ContextMenuPreviewDocument(Component):
    citry = default_citry

    class Kwargs:
        title: str
        content: object

    class Slots:
        pass

    template = """
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>{{ title }}</title>
          <c-css />
        </head>
        <body>
          <main>{{ content }}</main>
          <c-js />
        </body>
      </html>
    """

    def template_data(self, kwargs: Kwargs, _slots: Slots) -> dict[str, object]:
        return {"title": kwargs.title, "content": kwargs.content}


def _open_example(page: Any, serve_citry_ui_live: Any, name: str) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    # Each test renders the shipped example module directly, so it does not
    # depend on where the docs page places that example.
    module = importlib.import_module(f"citry_ui.components.ccontext_menu.snippets.{name}")
    html = ContextMenuPreviewDocument(title=name, content=module.preview).render().serialize()
    page.goto(serve_citry_ui_live(default_citry, html) + "/", wait_until="networkidle")
    # A right click sent before every ContextMenu starts would reach the
    # browser's own menu instead of the component.
    page.wait_for_function(
        """() => {
          const roots = document.querySelectorAll('[data-citry-ui-part="context-menu"]');
          const ready = document.querySelectorAll(
            '[data-citry-ui-part="context-menu"][data-citry-context-menu-initialized]',
          );
          return roots.length > 0 && ready.length === roots.length;
        }"""
    )
    return errors


def _record_next_contextmenu(target: Any) -> None:
    # The target's own listener runs after the component's capture listener,
    # so it sees whether the component claimed the request. It also records
    # the event's point, which the callback should receive unchanged.
    target.evaluate(
        """target => {
          window.__contextEvent = null;
          target.addEventListener('contextmenu', event => {
            window.__contextEvent = {
              prevented: event.defaultPrevented,
              point: `${Math.round(event.clientX)}, ${Math.round(event.clientY)}`,
            };
          }, {once: true});
        }"""
    )


def _recorded_contextmenu(page: Any) -> dict[str, Any]:
    page.wait_for_function("window.__contextEvent !== null")
    return page.evaluate("window.__contextEvent")


def _next_frames(page: Any) -> None:
    # Give a wrongly accepted request time to open the menu.
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")


def test_controlled_open_example_claims_refuses_breaks_and_releases_requests(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "controlled_open")
    target = page.locator(".context-menu-controlled__target")
    menu = page.get_by_role("menu", name="Diagram actions")
    output = page.locator(".context-menu-controlled output")

    # An accepted claim opens the menu and blocks the browser's own menu.
    _record_next_contextmenu(target)
    target.click(button="right", position={"x": 30, "y": 20})
    event = _recorded_contextmenu(page)
    menu.wait_for(state="visible")
    assert event["prevented"] is True
    expect(output).to_have_text(
        f"State: controlled open; request: contextmenu; candidate: {event['point']}",
        use_inner_text=True,
    )

    # The owner always accepts a close.
    page.keyboard.press("Escape")
    menu.wait_for(state="hidden")
    expect(output).to_contain_text("State: controlled closed; request: escape")

    # A refused claim records the request but leaves the browser's menu.
    page.get_by_label("Claim requests").uncheck()
    _record_next_contextmenu(target)
    target.click(button="right", position={"x": 40, "y": 24})
    event = _recorded_contextmenu(page)
    assert event["prevented"] is False
    expect(output).to_have_text(
        f"State: controlled closed; request: contextmenu; candidate: {event['point']}",
        use_inner_text=True,
    )
    _next_frames(page)
    assert menu.is_hidden()
    # Seen in headless Chromium: after a refused request, the next right
    # click on this target does not reach the callback until a plain left
    # click lands on the page. Checking a box does not count.
    output.click()

    # Claiming without opening is a broken claim: the menu stays closed and
    # the component reports it once.
    page.get_by_label("Claim requests").check()
    page.get_by_label("Break the claim").check()
    _record_next_contextmenu(target)
    # The component reports the broken claim from a later task.
    with page.expect_console_message(lambda message: "claim was not committed" in message.text):
        target.click(button="right", position={"x": 50, "y": 28})
    event = _recorded_contextmenu(page)
    assert event["prevented"] is True
    expect(output).to_contain_text(f"candidate: {event['point']}")
    _next_frames(page)
    assert menu.is_hidden()
    expect(output).to_contain_text("State: controlled closed")
    broken = [message for message in errors if "claim was not committed" in message]
    assert len(broken) == 1
    errors.remove(broken[0])

    # After release the menu opens on its own, with no claim.
    page.get_by_label("Break the claim").uncheck()
    page.get_by_role("button", name="Release control").click()
    _record_next_contextmenu(target)
    target.click(button="right", position={"x": 60, "y": 32})
    event = _recorded_contextmenu(page)
    menu.wait_for(state="visible")
    # The new point shows that the callback still ran after release.
    expect(output).to_have_text(
        f"State: uncontrolled; request: contextmenu; candidate: {event['point']}",
        use_inner_text=True,
    )
    assert errors == []


def test_focus_example_actions_disable_remove_and_keep_the_nested_button(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "focus_and_keyboard")
    row = page.locator(".context-menu-focus__row")
    menu = page.get_by_role("menu", name="Focusable row actions")
    nested = row.get_by_role("button", name="Nested action")

    def choose(name: str) -> None:
        row.click(button="right", position={"x": 8, "y": 8})
        menu.wait_for(state="visible")
        menu.get_by_role("menuitem", name=name).click()
        menu.wait_for(state="hidden")

    # An action the callback does not handle changes nothing.
    choose("Rename")
    expect(page.locator(".context-menu-focus output")).to_have_text("closed by action")
    expect(nested).to_be_enabled()

    choose("Disable nested return target")
    expect(nested).to_be_disabled()

    choose("Remove nested return target")
    expect(nested).to_have_count(0)

    page.get_by_role("button", name="Restore nested Button").click()
    expect(nested).to_be_enabled()
    assert errors == []


def test_positioning_example_records_accepted_point_and_invocation(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "positioning_and_rtl")
    target = page.locator(".context-menu-positioning__target.is-top-start")
    menu = page.get_by_role("menu", name="Top start actions")
    output = page.locator(".context-menu-positioning__controls output").first

    _record_next_contextmenu(target)
    # The target starts right to left, so it sits in the top end corner
    # under the "Top end" target. Its top strip stays uncovered.
    target.click(button="right", position={"x": 10, "y": 8})
    event = _recorded_contextmenu(page)
    menu.wait_for(state="visible")
    expect(output).to_have_text(f"Accepted point: {event['point']}; invocation: pointer")

    # A close request leaves the last accepted point on screen.
    page.keyboard.press("Escape")
    menu.wait_for(state="hidden")
    expect(output).to_have_text(f"Accepted point: {event['point']}; invocation: pointer")

    # A keyboard request reports its own reason.
    target.focus()
    page.keyboard.press("Shift+F10")
    menu.wait_for(state="visible")
    expect(output).to_contain_text("; invocation: keyboard")
    assert errors == []


def test_positioning_example_owner_state_follows_the_controlled_menu(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "positioning_and_rtl")
    target = page.locator(".context-menu-positioning__target.is-bottom-end")
    menu = page.get_by_role("menu", name="Bottom end actions")
    output = page.locator(".context-menu-positioning__controls output").first

    # The callback opens owner state and claims the request in one turn.
    _record_next_contextmenu(target)
    target.click(button="right", position={"x": 16, "y": 10})
    event = _recorded_contextmenu(page)
    menu.wait_for(state="visible")
    assert event["prevented"] is True
    expect(output).to_have_text(f"Accepted point: {event['point']}; invocation: pointer")

    # The menu is controlled, so it closes only because the callback writes
    # the close into owner state.
    page.keyboard.press("Escape")
    menu.wait_for(state="hidden")
    expect(output).to_have_text(f"Accepted point: {event['point']}; invocation: pointer")

    # Owner state reads closed, so opening it from the owner opens the menu.
    page.get_by_role("button", name="Open from owner state").click()
    menu.wait_for(state="visible")
    expect(output).to_contain_text("; invocation: external")
    assert errors == []


def test_touch_example_records_accepted_closed_and_refused_requests(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "touch_and_pen")
    card = page.locator("[data-context-menu-touch-target]")
    menu = page.get_by_role("menu", name="Touch card actions")
    state = page.locator(".context-menu-touch__controls output")
    log = page.locator(".context-menu-touch ol li")

    card.click(button="right")
    menu.wait_for(state="visible")
    expect(state).to_have_text("State: accepted; primary clicks: 0", use_inner_text=True)
    expect(log.first).to_have_text("accepted contextmenu")

    page.keyboard.press("Escape")
    menu.wait_for(state="hidden")
    expect(state).to_have_text("State: idle; primary clicks: 0", use_inner_text=True)
    expect(log).to_have_text(["closed escape", "accepted contextmenu"])

    # The scrollable card is held closed, so its callback refuses the request
    # and the browser keeps its own menu.
    scroll_card = page.locator("[data-context-menu-scroll-target]")
    _record_next_contextmenu(scroll_card)
    scroll_card.click(button="right")
    event = _recorded_contextmenu(page)
    assert event["prevented"] is False
    expect(state).to_have_text("State: controlled refused; primary clicks: 0", use_inner_text=True)
    expect(log.first).to_have_text("refused contextmenu")
    _next_frames(page)
    assert page.get_by_role("menu", name="Scrollable card actions").is_hidden()
    assert errors == []
