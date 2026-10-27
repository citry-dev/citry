"""Browser evidence that the Menu examples act on what `onOpenChange` reports."""

from __future__ import annotations

import importlib
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import expect

from citry import Component
from citry import citry as default_citry

pytestmark = pytest.mark.e2e


class MenuPreviewDocument(Component):
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
    module = importlib.import_module(f"citry_ui.components.cmenu.snippets.{name}")
    html = MenuPreviewDocument(title=name, content=module.preview).render().serialize()
    page.goto(serve_citry_ui_live(default_citry, html) + "/", wait_until="networkidle")
    # A click sent before the Menu starts would reach plain HTML.
    page.wait_for_selector("[data-citry-menu-initialized]", state="attached")
    return errors


def test_controlled_menu_example_logs_each_request_and_declines_while_locked(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "controlled_open")
    trigger = page.get_by_role("button", name="Controlled grimoire")
    menu = page.locator('[role="menu"]')
    output = page.locator(".archive-controlled-demo output")

    trigger.click()
    menu.wait_for(state="visible")
    expect(output).to_have_text("Last request: trigger")
    page.keyboard.press("Escape")
    menu.wait_for(state="hidden")
    expect(output).to_have_text("Last request: escape")

    # The docs page sends its preview controls as this window event.
    page.evaluate(
        """() => window.dispatchEvent(new CustomEvent('citry-ui-preview-controls', {
          detail: {locked: true},
        }))"""
    )
    # While locked, the request is logged but the owner keeps it closed.
    trigger.click()
    expect(output).to_have_text("Last request: trigger")
    # Give a wrongly accepted request time to open the Menu.
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
    assert menu.is_hidden()
    assert errors == []
