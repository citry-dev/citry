"""Browser proof that Debug wrappers do not replace authored component roots."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.debug import Debug

pytestmark = pytest.mark.e2e


def test_component_callback_still_receives_authored_roots(page: Any, serve_document: Any) -> None:
    app = Citry(
        extensions=[Debug],
        extensions_defaults={"debug": {"highlight_components": True}},
    )

    class Widget(Component):
        citry = app
        template = """
            <section class="widget">one</section><aside class="widget">two</aside>
        """
        js = """
            $component(({ els }) => {
              els.forEach((el) => {
                el.dataset.authoredRoot = String(el.classList.contains('widget'));
                el.dataset.debugWrapper = String(el.classList.contains('citry-debug'));
                el.dataset.rootCount = String(els.length);
              });
            });
        """

    class Page(Component):
        citry = app
        template = """
            <!doctype html>
            <html><head></head><body><c-widget /><c-js /></body></html>
        """

    html = Page().render().serialize(deps_strategy="document")
    page.goto(serve_document(html))
    page.wait_for_function("document.querySelectorAll('.widget[data-authored-root=true]').length === 2")

    widgets = page.locator(".widget")
    assert widgets.count() == 2
    assert [widgets.nth(index).get_attribute("data-debug-wrapper") for index in range(2)] == ["false", "false"]
    assert [widgets.nth(index).get_attribute("data-root-count") for index in range(2)] == ["2", "2"]
    assert widgets.first.locator("xpath=..").get_attribute("class") == "citry-debug citry-debug-component"
