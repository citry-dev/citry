"""Tests for the search wiring: DocPage markup and front-matter flags."""

from __future__ import annotations

from typing import Any

from docs_site._internal.components.doc_page import DocPage
from docs_site._internal.frontmatter import parse_page


def _page(**kwargs: Any) -> str:
    base: dict[str, Any] = {"content_html": "<p>x</p>", "title": "T", "current_path": "p/"}
    base.update(kwargs)
    return str(DocPage(**base))


def test_searchable_page_has_search_ui_and_index_hook() -> None:
    html = _page(searchable=True)
    assert "data-pagefind-body" in html  # the article is in the index
    assert 'class="djc-search-trigger"' in html  # the header trigger
    assert 'data-pagefind-path="/pagefind/pagefind.js"' in html  # the modal
    assert "/static/css/search.css" in html
    assert "/static/js/search.js" in html


def test_non_searchable_page_omits_index_hook() -> None:
    # The article keeps the search UI but is left out of the index.
    assert "data-pagefind-body" not in _page(searchable=False)


def test_boosted_page_emits_weight() -> None:
    assert 'data-pagefind-weight="2.0"' in _page(boost=2.0)
    # The neutral default leaves the attribute off entirely.
    assert "data-pagefind-weight" not in _page(boost=1.0)


def test_base_path_meta_is_emitted() -> None:
    assert '<meta name="djc-base-path" content="/citry"' in _page(base_path="/citry")


def test_frontmatter_parses_searchable_and_boost() -> None:
    # Indexed by default with a neutral boost.
    default = parse_page("# X\n")
    assert default.searchable is True
    assert default.boost == 1.0

    meta = parse_page("---\nsearchable: false\nboost: 2.5\n---\n\n# X\n")
    assert meta.searchable is False
    assert meta.boost == 2.5

    # A malformed boost falls back to the default rather than failing the page.
    assert parse_page("---\nboost: high\n---\n\n# X\n").boost == 1.0
