"""Browser evidence that the shipped Tabs examples show and apply selection."""

from __future__ import annotations

import importlib
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import expect

from citry import Component
from citry import citry as default_citry

pytestmark = pytest.mark.e2e


class TabsPreviewDocument(Component):
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


def _open_preview(page: Any, serve_citry_ui_live: Any, name: str) -> list[str]:
    # The snippet module registers Citry UI on the default app and exposes the
    # example as `preview`, the same object the docs page renders.
    module = importlib.import_module(f"citry_ui.components.ctabs.snippets.{name}")
    html = TabsPreviewDocument(title=name, content=module.preview).render().serialize()
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(serve_citry_ui_live(default_citry, html) + "/", wait_until="networkidle")
    # A key press sent before every Tabs root starts would reach plain HTML.
    page.wait_for_function(
        "[...document.querySelectorAll('[data-citry-tabs-root]')].every("
        "root => root.hasAttribute('data-citry-tabs-initialized'))"
    )
    return errors


def test_controlled_selection_records_every_request_and_applies_it_only_when_allowed(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "controlled_selection")
    status = page.locator(".tabs-controlled__status")

    page.get_by_label("Apply requests from Tabs").uncheck()
    page.get_by_role("tab", name="Europa").click()
    request = status.locator("dd").nth(1)
    # The "via" line stays hidden until the callback stores
    # `detail.source`, so the visible text proves both arguments arrived.
    expect(request).to_have_text("europa via pointer", use_inner_text=True)
    expect(page.get_by_role("tab", name="Mercury")).to_have_attribute("aria-selected", "true")
    expect(status.locator("dd").first).to_have_text("mercury")

    page.get_by_label("Apply requests from Tabs").check()
    page.get_by_role("tab", name="Titan").click()
    expect(page.get_by_role("tab", name="Titan")).to_have_attribute("aria-selected", "true")
    expect(status.locator("dd").first).to_have_text("titan")
    expect(request).to_have_text("titan via pointer", use_inner_text=True)
    assert errors == []


def test_keyboard_activation_outputs_follow_automatic_and_manual_selection(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "keyboard_activation")
    automatic_card = page.locator(".tabs-activation__card").first
    manual_card = page.locator(".tabs-activation__card--manual")

    automatic_tabs = page.get_by_role("tablist", name="Automatic probe data").get_by_role("tab")
    automatic_tabs.first.focus()
    page.keyboard.press("ArrowRight")
    expect(automatic_card.locator("output")).to_have_text("surface")

    manual_tabs = page.get_by_role("tablist", name="Manual probe data").get_by_role("tab")
    manual_tabs.first.focus()
    page.keyboard.press("ArrowRight")
    # Manual activation only moves focus, so the output must not change yet.
    expect(manual_tabs.nth(1)).to_be_focused()
    expect(manual_card.locator("output")).to_have_text("orbit")
    page.keyboard.press("Enter")
    expect(manual_card.locator("output")).to_have_text("surface")
    assert errors == []


def test_night_sky_guide_shows_the_selected_topic(page: Any, serve_citry_ui_live: Any) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "night_sky_guide")
    topic = page.locator(".night-sky-guide header output")
    expect(topic).to_have_text("planets")

    page.get_by_role("tab", name="Nebulae").click()
    expect(topic).to_have_text("nebulae")
    assert errors == []
