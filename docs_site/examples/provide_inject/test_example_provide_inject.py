"""Render the provide/inject example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry


def test_provide_inject_example_page_renders() -> None:
    html = str(get_example_registry()["provide_inject"].page_cls())
    # Each button's label comes from the injected theme, not a prop: the outer
    # "Ocean" theme, then the nested "Forest" theme that overrides it.
    assert "Ocean: Save" in html
    assert "Forest: Publish" in html
