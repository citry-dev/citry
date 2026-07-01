"""
Cross-browser e2e for the ``document`` strategy (everything inlined on one page).

Proves the client runtime actually works in a real browser: a component's JS
runs and receives its ``js_data``, and its CSS applies with the injected
``css_data`` variables. Run across chromium/firefox/webkit via pytest-playwright's
``--browser`` flag. This is a lean starter suite; more cases can grow from the
patterns in tests/_djc_tests.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _build_page() -> type[Component]:
    c = Citry()

    class Widget(Component):
        citry = c
        template = '<div class="widget">hi</div>'
        js = "$onComponent(({ els, data }) => { els[0].setAttribute('data-label', data.label); });"
        css = ".widget { color: var(--accent); }"

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"label": "ran"}

        def css_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"accent": "rgb(12, 34, 56)"}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><c-css /></head>
            <body>
              <c-widget />
              <c-js />
            </body>
          </html>
        """

    return Page


def test_component_js_runs_and_receives_data(page: Any, serve_document: Any) -> None:
    html = _build_page()().render().serialize(deps_strategy="document")
    page.goto(serve_document(html))
    page.wait_for_function("document.querySelector('.widget')?.dataset.label === 'ran'")
    assert page.locator(".widget").get_attribute("data-label") == "ran"


def test_component_css_applies_with_injected_vars(page: Any, serve_document: Any) -> None:
    html = _build_page()().render().serialize(deps_strategy="document")
    page.goto(serve_document(html))
    color = page.eval_on_selector(".widget", "el => getComputedStyle(el).color")
    assert color == "rgb(12, 34, 56)"
