"""Render the fragments example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry


def test_fragments_example_page_renders() -> None:
    html = str(get_example_registry()["fragments"].page_cls())
    # The page offers a button that fetches the pre-rendered fragment endpoint.
    assert 'id="frag-load"' in html
    assert "Load fragment" in html
    assert 'data-fragment-url="/examples/fragments/demo/widget/"' in html
    assert "fetch(url)" in html
