"""Render the slots example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry
from lxml import html as lxml_html


def test_slots_example_page_renders() -> None:
    html = str(get_example_registry()["slots"].page_cls())
    # The first panel fills the header slot from the caller.
    assert "Project settings" in html
    # The second panel omits the footer slot, so its slot fallback shows instead.
    # The template puts the text on its own indented line, so compare it
    # without the whitespace around it.
    document = lxml_html.document_fromstring(html)
    fallbacks = document.find_class("slot-panel__fallback")
    assert [node.text_content().strip() for node in fallbacks] == ["No actions available"]
