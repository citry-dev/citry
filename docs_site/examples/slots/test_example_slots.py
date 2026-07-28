"""Render the slots example page and lock stable, example-specific substrings."""

from docs_site._internal.examples import get_example_registry


def test_slots_example_page_renders() -> None:
    html = str(get_example_registry()["slots"].page_cls())
    # The first panel fills the header slot from the caller.
    assert "Project settings" in html
    # The second panel omits the footer slot, so its slot fallback shows instead.
    assert '<span class="slot-panel__fallback">No actions available</span>' in html
