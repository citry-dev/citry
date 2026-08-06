"""Render the tabs example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry


def test_tabs_example_page_renders() -> None:
    html = str(get_example_registry()["tabs"].page_cls())
    # The first tab renders active; the non-active panels render hidden.
    assert 'role="tablist" aria-label="Example sections"' in html
    assert 'role="tab" aria-controls="demo-tabs-' in html
    assert 'aria-selected="true" tabindex="0" data-active="true" data-index="0"' in html
    assert "Overview" in html
    assert 'role="tabpanel" tabindex="0"' in html
    assert 'data-index="1" hidden' in html
    # Tabs and panels are connected for assistive technology, and the shipped
    # script supports the standard horizontal-tab keyboard controls.
    assert 'aria-labelledby="demo-tabs-' in html
    assert 'event.key === "ArrowRight"' in html
    assert 'event.key === "Home"' in html
