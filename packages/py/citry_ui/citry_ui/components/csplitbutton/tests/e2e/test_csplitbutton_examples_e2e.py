"""Browser evidence that the SplitButton examples act on what their callbacks report."""

from __future__ import annotations

import importlib
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import expect

from citry import Component
from citry import citry as default_citry

pytestmark = pytest.mark.e2e


class SplitButtonPreviewDocument(Component):
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
    module = importlib.import_module(f"citry_ui.components.csplitbutton.snippets.{name}")
    html = SplitButtonPreviewDocument(title=name, content=module.preview).render().serialize()
    page.goto(serve_citry_ui_live(default_citry, html) + "/", wait_until="networkidle")
    # A click sent before every root Menu starts would reach plain HTML. A Menu
    # moved into a shadow root is out of reach here, and no test uses it.
    page.wait_for_function(
        """() => {
          const menus = [...document.querySelectorAll('[data-citry-menu-root]')];
          return menus.length > 0 && menus.every(menu => menu.hasAttribute('data-citry-menu-initialized'));
        }"""
    )
    return errors


def _next_frames(page: Any) -> None:
    # Give a wrongly accepted request time to change the Menu.
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")


def test_controlled_menu_example_logs_requests_and_applies_them_only_when_accepted(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "controlled_menu")
    trigger = page.get_by_role("button", name="More publication actions")
    menu = page.get_by_role("menu", name="More publication actions")
    output = page.locator(".split-button-controlled output")

    trigger.click()
    menu.wait_for(state="visible")
    expect(output).to_have_text("Ownership: controlled · Last reason: trigger", use_inner_text=True)
    page.keyboard.press("Escape")
    menu.wait_for(state="hidden")
    expect(output).to_have_text("Ownership: controlled · Last reason: escape", use_inner_text=True)

    # A declined request is logged, but the owner keeps the Menu as is.
    page.get_by_label("Accept Menu requests").uncheck()
    trigger.click()
    expect(output).to_have_text("Ownership: controlled · Last reason: trigger", use_inner_text=True)
    _next_frames(page)
    assert menu.is_hidden()
    page.get_by_role("button", name="Show", exact=True).click()
    menu.wait_for(state="visible")
    page.keyboard.press("Escape")
    expect(output).to_have_text("Ownership: controlled · Last reason: escape", use_inner_text=True)
    _next_frames(page)
    assert menu.is_visible()

    # After release the Menu applies its own requests.
    page.get_by_role("button", name="Release control").click()
    expect(output).to_contain_text("Ownership: released")
    page.keyboard.press("Escape")
    menu.wait_for(state="hidden")
    trigger.click()
    menu.wait_for(state="visible")
    expect(output).to_have_text("Ownership: released · Last reason: trigger", use_inner_text=True)
    assert errors == []


def test_layers_example_logs_menu_actions_and_opens_the_dialog_for_provenance(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "layers_and_dialog")
    trigger = page.get_by_role("button", name="More clipped specimen actions")
    menu = page.get_by_role("menu", name="More clipped specimen actions")
    output = page.locator(".split-button-layer-demo > output")
    dialog = page.get_by_role("dialog", name="Specimen provenance")

    # A submenu action is logged and leaves the Dialog closed.
    trigger.click()
    menu.wait_for(state="visible")
    menu.get_by_role("menuitem", name="Archive destination").click()
    page.get_by_role("menuitem", name="Herbarium archive").click()
    menu.wait_for(state="hidden")
    expect(output).to_have_text("herbarium-archive")
    _next_frames(page)
    assert dialog.is_hidden()

    trigger.click()
    menu.wait_for(state="visible")
    menu.get_by_role("menuitem", name="Open provenance Dialog").click()
    dialog.wait_for(state="visible")
    expect(output).to_have_text("open-provenance")
    assert errors == []
