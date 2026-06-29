"""Tests for example discovery, the ``<c-example />`` directive, and pre-render."""

from __future__ import annotations

from pathlib import Path

from docs_site.build import build_site
from docs_site.config import DocsConfig
from docs_site.examples import _discover_examples, get_example_registry, render_example_card
from docs_site.pipeline import render_page


def test_registry_discovers_card_example() -> None:
    registry = get_example_registry()
    assert "card" in registry
    info = registry["card"]
    assert info.page_cls.__name__ == "CardPage"
    assert info.example_dir.name == "card"


def test_render_example_card_has_tabs_iframe_and_source() -> None:
    info = get_example_registry()["card"]
    html = render_example_card("card", info)
    assert 'class="tabbed-set example-card"' in html
    assert 'src="/examples/card/"' in html
    assert ">Live demo</label>" in html
    assert ">Component</label>" in html
    assert 'class="highlight"' in html  # the source is Pygments-highlighted


def test_example_directive_expands_in_a_page() -> None:
    html = render_page('# Examples\n\n<c-example name="card" />\n').html
    assert "tabbed-set example-card" in html
    assert 'src="/examples/card/"' in html
    assert "<c-example" not in html  # the directive was expanded


def test_unknown_example_shows_inline_error() -> None:
    html = render_page('<c-example name="nope" />').html
    assert "Unknown example: nope" in html


def test_discover_empty_dir_is_empty(tmp_path: Path) -> None:
    assert _discover_examples(tmp_path) == {}


def test_build_pre_renders_example_demo(tmp_path: Path) -> None:
    # A full build (real content + examples) writes the standalone demo page.
    out = tmp_path / "site"
    outcome = build_site(config=DocsConfig(site_dir=out))
    assert outcome.examples >= 1
    demo = out / "examples" / "card" / "index.html"
    assert demo.is_file()
    demo_html = demo.read_text(encoding="utf-8")
    assert 'class="demo-card"' in demo_html  # the component rendered
    assert ".demo-card" in demo_html  # and its CSS was injected
