"""Nested template attributes retain their authored Vue lexical scope."""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e


def test_nested_template_uses_caller_vue_scope(page, serve_document) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    app = Citry(autodiscover=False)

    class Card(Component):
        citry = app
        template = "<article>{{ body }}</article>"

        def template_data(self, kwargs, slots):
            return {"body": kwargs["body"]}

        def js_data(self, kwargs, slots):
            return {"label": "card"}

    class Page(Component):
        citry = app
        template = "<c-Card c-body=\"<button class='lexical' v-text='label' @click='label += `!`'></button>\" />"

        def js_data(self, kwargs, slots):
            return {"label": "page"}

    page.goto(serve_document(Page().render().serialize()))
    button = page.locator("button.lexical")
    assert button.text_content() == "page"
    button.click()
    assert button.text_content() == "page!"
    assert errors == []


def test_nested_template_inside_supplied_slot_keeps_page_scope(page, serve_document) -> None:
    app = Citry(autodiscover=False)

    class Card(Component):
        citry = app
        template = "<article>{{ body }}</article>"

        def template_data(self, kwargs, slots):
            return {"body": kwargs["body"]}

        def js_data(self, kwargs, slots):
            return {"label": "card"}

    class Shell(Component):
        citry = app
        template = "<main><c-slot /></main>"

    class Page(Component):
        citry = app
        template = "<c-Shell><c-Card c-body=\"<span class='nested' v-text='label'></span>\" /></c-Shell>"

        def js_data(self, kwargs, slots):
            return {"label": "page"}

    page.goto(serve_document(Page().render().serialize()))
    assert page.locator("span.nested").text_content() == "page"
