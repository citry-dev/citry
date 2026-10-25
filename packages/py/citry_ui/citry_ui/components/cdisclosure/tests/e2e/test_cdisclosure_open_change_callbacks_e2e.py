"""Browser evidence that Disclosure examples act on what `onOpenChange` reports."""

from __future__ import annotations

import importlib
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import expect

from citry import Component
from citry import citry as default_citry

pytestmark = pytest.mark.e2e


class DisclosurePreviewDocument(Component):
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
    module = importlib.import_module(f"citry_ui.components.cdisclosure.snippets.{name}")
    html = DisclosurePreviewDocument(title=name, content=module.preview).render().serialize()
    base = serve_citry_ui_live(default_citry, html)
    page.goto(base + "/", wait_until="networkidle")
    page.wait_for_selector("[data-citry-disclosure-initialized]")
    return errors


def test_controlled_disclosure_example_logs_each_request_and_applies_only_accepted_ones(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "controlled_open")
    trigger = page.get_by_role("button", name="Advanced logging")
    # The third field of the status line is "Last", the most recent request.
    last = page.locator(".controlled-disclosure output span").nth(2)

    # A declined request is logged, but the owner keeps the panel closed.
    page.get_by_label("Accept trigger requests").uncheck()
    trigger.click()
    expect(last).to_have_text("activation: open")
    # Give a wrongly accepted request time to expand the panel.
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
    assert trigger.get_attribute("aria-expanded") == "false"

    page.get_by_label("Accept trigger requests").check()
    trigger.click()
    expect(trigger).to_have_attribute("aria-expanded", "true")
    trigger.click()
    expect(last).to_have_text("activation: closed")
    expect(trigger).to_have_attribute("aria-expanded", "false")

    # After release the Disclosure commits requests itself, and the handler
    # still logs them.
    page.get_by_role("button", name="Release control").click()
    trigger.click()
    expect(trigger).to_have_attribute("aria-expanded", "true")
    expect(last).to_have_text("activation: open")
    assert errors == []
