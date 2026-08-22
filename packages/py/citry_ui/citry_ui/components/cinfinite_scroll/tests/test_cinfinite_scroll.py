# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CInfiniteScroll


def _render(source: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>"

    return str(Page())


def test_schema_registration_and_server_fallback() -> None:
    assert [item.name for item in fields(CInfiniteScroll.Kwargs)] == [
        "id",
        "aria_label",
        "has_more",
        "loading",
        "error",
        "disabled",
        "auto",
        "root_margin",
        "threshold",
        "action_name",
        "action_value",
        "load_more_label",
        "retry_label",
        "loading_label",
        "error_label",
        "end_label",
        "class_",
        "style",
        "attrs",
    ]
    assert CInfiniteScroll in citry_ui.COMPONENTS
    html = _render(
        '<form><c-CInfiniteScroll id="feed" aria_label="Feed" action_name="feed_action"><ol><li>A</li></ol></c-CInfiniteScroll></form>'
    )
    assert "<ol><li>A</li></ol>" in html
    assert 'role="region"' in html
    assert 'aria-label="Feed"' in html
    assert 'name="feed_action"' in html
    assert 'value="load-more"' in html
    assert "formnovalidate" in html
    assert ">Load more</span>" in html


def test_loading_error_end_and_explicit_labels() -> None:
    loading = _render('<c-CInfiniteScroll c-loading="True"><p>A</p></c-CInfiniteScroll>')
    assert 'aria-busy="true"' in loading
    assert 'aria-busy="true" data-citry-ui-part="content"' in loading
    assert "data-loading" in loading
    error = _render(
        '<c-CInfiniteScroll c-error="True" retry_label="Retry now" error_label="Offline"><p>A</p></c-CInfiniteScroll>'
    )
    assert "data-error" in error
    assert "Retry now" in error
    assert "Offline" in error
    end = _render('<c-CInfiniteScroll c-has_more="False"><p>A</p></c-CInfiniteScroll>')
    assert "data-end" in end
    assert "No more results" in end


@pytest.mark.parametrize(
    ("source", "match"),
    [
        ('<c-CInfiniteScroll c-threshold="2" />', "between 0 and 1"),
        ('<c-CInfiniteScroll root_margin=" " />', "nonempty"),
        ('<c-CInfiniteScroll c-auto="1" />', "must be a bool"),
        ("<c-CInfiniteScroll c-attrs=\"{'aria-busy':'true'}\" />", "owned attribute"),
    ],
)
def test_invalid_inputs_fail(source: str, match: str) -> None:
    with pytest.raises((TypeError, ValueError), match=match):
        _render(source)


def test_assets_docs_and_translation_reference_cover_contract() -> None:
    root = Path(__file__).parents[1]
    js = (root / "runtime.source.js").read_text(encoding="utf8")
    css = (root / "runtime.source.css").read_text(encoding="utf8")
    guide = (root / "api.md").read_text(encoding="utf8")
    reference = (root / "api.yml").read_text(encoding="utf8")
    for fragment in ("IntersectionObserver", "MutationObserver", "onLoadMore", "removeEventListener", "disconnect"):
        assert fragment in js
    for fragment in ("prefers-reduced-motion", "forced-colors", "@media print"):
        assert fragment in css
    assert guide.count("<c-ui-demo ") == 6
    for suffix in ("load-more", "retry", "loading", "error", "end"):
        assert f"citry-ui-infinite-scroll-{suffix}" in reference
