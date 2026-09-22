"""Browser proof that Debug wrappers do not replace authored component roots."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.debug import Debug

pytestmark = pytest.mark.e2e


def test_component_callback_preserves_authored_refs_and_root_metadata(page: Any, serve_document: Any) -> None:
    app = Citry(
        extensions=[Debug],
        extensions_defaults={"debug": {"highlight_components": True}},
    )

    class Widget(Component):
        citry = app
        template = """
            <section ref="section" class="widget">one</section><aside ref="aside" class="widget">two</aside>
        """
        js = """
            $component(({ component }) => {
              const els = [component.$refs.section, component.$refs.aside];
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


def test_same_type_instances_and_native_slot_keep_lexical_data_and_refs(page: Any, serve_document: Any) -> None:
    app = Citry(
        extensions=[Debug],
        extensions_defaults={"debug": {"highlight_components": True, "highlight_slots": True}},
    )

    class Card(Component):
        citry = app
        template = """
            <article ref="shell" class="card"><c-slot /></article>
        """
        js = """
            $component(({ component }) => {
              component.$refs.shell.dataset.callback = 'ready';
            });
        """

    class Page(Component):
        citry = app
        template = """
            <!doctype html>
            <html><head></head><body>
              <c-card><span id="slot-one" v-text="message"></span></c-card>
              <c-card><span id="slot-two" v-text="message"></span></c-card>
              <c-js />
            </body></html>
        """
        js = """
            $component({data(){return {message:'parent value'}}});
        """

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(serve_document(Page().render().serialize(deps_strategy="document")))
    page.wait_for_function("document.querySelectorAll('.card[data-callback=ready]').length === 2")

    assert errors == []
    assert page.locator("#slot-one").inner_text() == "parent value"
    assert page.locator("#slot-two").inner_text() == "parent value"
    assert page.locator(".citry-debug-component").count() == 2
    assert page.locator(".citry-debug-slot").count() == 2
    labels = page.locator(".citry-debug-component > .citry-debug-label").all_inner_texts()
    assert sum(label.startswith("Card (") for label in labels) == 2
    assert len({label for label in labels if label.startswith("Card (")}) == 2
    card_definition_ids = page.evaluate(
        """() => {
          const runtimeApp = [...CitryStable._apps.values()][0];
          return [...runtimeApp.occurrences.values()]
            .filter((occurrence) => occurrence.typeKey.startsWith('Card_'))
            .map((occurrence) => occurrence.definitionId);
        }"""
    )
    assert len(card_definition_ids) == 2
    assert len(set(card_definition_ids)) == 1
