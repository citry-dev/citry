"""Browser evidence that Dialog examples act on what `onOpenChange` reports."""

from __future__ import annotations

import importlib
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import expect

from citry import Component
from citry import citry as default_citry

pytestmark = pytest.mark.e2e


class DialogPreviewDocument(Component):
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
    module = importlib.import_module(f"citry_ui.components.cdialog.snippets.{name}")
    html = DialogPreviewDocument(title=name, content=module.preview).render().serialize()
    base = serve_citry_ui_live(default_citry, html)
    page.goto(base + "/", wait_until="networkidle")
    page.wait_for_selector("[data-citry-dialog-initialized]")
    return errors


def test_controlled_dialog_example_logs_each_request_and_opens_only_when_accepted(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_example(page, serve_citry_ui_live, "controlled_dialog")
    dialog = page.locator('[data-citry-ui-part="dialog"]')
    trigger = page.get_by_role("button", name="Request flight plan")
    last_reason = page.locator(".controlled-dialog__status strong")

    # The owner starts by declining, so the request is logged but the
    # Dialog stays closed.
    trigger.click()
    expect(last_reason).to_have_text("trigger")
    # Give a wrongly accepted request time to open the Dialog.
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
    assert dialog.evaluate("element => element.open") is False

    page.get_by_label("Accept Dialog requests").check()
    trigger.click()
    page.wait_for_function("document.querySelector('[data-citry-ui-part=\"dialog\"]').open")

    dialog.get_by_role("button", name="Request close").click()
    expect(last_reason).to_have_text("action")
    page.wait_for_function("!document.querySelector('[data-citry-ui-part=\"dialog\"]').open")
    assert errors == []


def test_dialog_quality_scenario_records_the_latest_open_change(page: Any, open_scenario: Any) -> None:
    open_scenario("dialog.states")
    page.get_by_role("button", name="Open observatory log").click()
    page.wait_for_function("document.querySelector('#quality-dialog').open")
    assert page.evaluate("window.__qualityDialogChange") == {"open": True, "reason": "trigger"}

    page.locator("#quality-dialog").get_by_role("button", name="Cancel", exact=True).click()
    page.wait_for_function("!document.querySelector('#quality-dialog').open")
    assert page.evaluate("window.__qualityDialogChange") == {"open": False, "reason": "action"}
