"""Render the control-flow example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry


def test_control_flow_example_page_renders() -> None:
    html = str(get_example_registry()["control_flow"].page_cls())
    # A done task takes the c-if branch (struck-through text).
    assert '<span class="tasklist__text tasklist__text--done">Write the docs example</span>' in html
    # The empty "Someday" list falls through to the c-empty branch.
    assert '<li class="tasklist__item tasklist__item--empty">Nothing to do yet.</li>' in html
