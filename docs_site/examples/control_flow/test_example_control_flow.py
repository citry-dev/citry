"""Render the control-flow example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry
from lxml import html as lxml_html


def _texts(page_html: str, class_name: str) -> list[str]:
    # The template puts element text on its own indented line, so compare
    # the text without the whitespace around it.
    document = lxml_html.document_fromstring(page_html)
    return [node.text_content().strip() for node in document.find_class(class_name)]


def test_control_flow_example_page_renders() -> None:
    html = str(get_example_registry()["control_flow"].page_cls())
    # A done task takes the c-if branch (struck-through text).
    assert _texts(html, "tasklist__text--done") == ["Write the docs example"]
    # The empty "Someday" list falls through to the c-empty branch.
    assert _texts(html, "tasklist__item--empty") == ["Nothing to do yet."]
