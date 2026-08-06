"""Render the recursion example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry


def test_recursion_example_page_renders() -> None:
    html = str(get_example_registry()["recursion"].page_cls())
    # A leaf three levels deep proves the self-rendering node descended the tree.
    assert "advanced.md" in html
    # The nine-node tree draws one tree-node root per node.
    assert html.count('class="tree-node"') == 9
