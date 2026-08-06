"""Render the error-fallback example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry


def test_error_fallback_example_page_renders() -> None:
    html = str(get_example_registry()["error_fallback"].page_cls())
    # The healthy boundary renders its widget.
    assert "<strong>Healthy widget</strong>" in html
    # The failing widget raises during render, so its boundary shows the fallback
    # text and the widget's own content never reaches the page.
    assert "Could not load this widget." in html
    assert "Failing widget" not in html
