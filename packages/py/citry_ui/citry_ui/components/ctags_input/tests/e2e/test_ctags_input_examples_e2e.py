"""Browser evidence that the TagsInput examples store tags and drafts the way their callbacks direct."""

from __future__ import annotations

import importlib
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import expect

from citry import Component
from citry import citry as default_citry

pytestmark = pytest.mark.e2e

_ALL_TAGS_INPUTS_STARTED = """() => [...document.querySelectorAll('[data-citry-ui-part="tags-input"]')]
  .every(root => root.hasAttribute('data-citry-tags-input-initialized'))"""


class TagsInputPreviewDocument(Component):
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
    module = importlib.import_module(f"citry_ui.components.ctags_input.snippets.{name}")
    html = TagsInputPreviewDocument(title=name, content=module.preview).render().serialize()
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(serve_citry_ui_live(default_citry, html) + "/", wait_until="networkidle")
    # Typing before an editor starts would bypass its callbacks.
    page.wait_for_function(_ALL_TAGS_INPUTS_STARTED)
    return errors


def _editor(page: Any, label: str) -> Any:
    # The hidden native select repeats the editor's label, so ask for the
    # text box by role.
    return page.get_by_role("textbox", name=label)


def _committed(label: str) -> str:
    # The hidden native select carries the committed tags the form submits.
    return f'.cui-tags-input:has(input[aria-label="{label}"]) [data-citry-tags-input-native] option:checked'


def _tags(page: Any, label: str) -> list[str]:
    return page.locator(_committed(label)).evaluate_all("options => options.map(option => option.value)")


def _wait_for_tags(page: Any, label: str, count: int) -> None:
    # The owner's accepted value reaches the editor on a later Vue update,
    # so wait for it before reading the committed tags.
    page.wait_for_function(
        "([selector, count]) => document.querySelectorAll(selector).length === count",
        arg=[_committed(label), count],
    )


def test_controlled_axes_draft_value_and_full_ownership_follow_the_owner(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "controlled_axes")
    articles = page.locator(".tags-input-controlled article")

    # Controlled draft: the editor keeps typed text only because the owner
    # stores it, and the owner reports each draft it stored.
    draft_editor = _editor(page, "Draft-owned labels")
    draft_editor.fill("reef")
    expect(articles.nth(1).locator("output")).to_have_text("Draft: reef")
    expect(draft_editor).to_have_value("reef")

    # Controlled tags: a request is logged, but applied only once accepted.
    value_editor = _editor(page, "Value-owned labels")
    value_editor.fill("beta")
    value_editor.press("Enter")
    expect(articles.nth(2).locator("output")).to_have_text('Requested ["alpine","beta"]')
    assert _tags(page, "Value-owned labels") == ["alpine"]
    page.get_by_label("Accept the next value request").check()
    value_editor.press("Enter")
    _wait_for_tags(page, "Value-owned labels", 2)
    assert _tags(page, "Value-owned labels") == ["alpine", "beta"]

    # Both axes controlled: the owner accepts the tags and refills the
    # emptied draft with its own note.
    full_editor = _editor(page, "Fully controlled labels")
    expect(full_editor).to_have_value("harbor")
    full_editor.press("Enter")
    expect(articles.nth(3).locator("output")).to_have_text('Accepted ["alpine","harbor"]')
    _wait_for_tags(page, "Fully controlled labels", 2)
    assert _tags(page, "Fully controlled labels") == ["alpine", "harbor"]
    expect(full_editor).to_have_value("owner note")
    assert errors == []


def test_morph_and_cleanup_stores_requested_tags_only_while_controlled(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "morph_and_cleanup")
    editor = _editor(page, "Morph labels")
    assert _tags(page, "Morph labels") == ["server-one", "server-two"]

    page.get_by_role("button", name="Toggle controlled handoff").click()
    _wait_for_tags(page, "Morph labels", 1)
    assert _tags(page, "Morph labels") == ["owner-one"]

    expect(editor).to_have_value("unfinished")
    editor.press("Enter")
    _wait_for_tags(page, "Morph labels", 2)
    assert _tags(page, "Morph labels") == ["owner-one", "unfinished"]
    assert errors == []
