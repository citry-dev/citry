"""Tests for example discovery, the ``<c-example />`` directive, and pre-render."""

from __future__ import annotations

from pathlib import Path

from docs_site._internal.build import build_site
from docs_site._internal.components.example_card import ExampleCard
from docs_site._internal.config import DocsConfig
from docs_site._internal.examples import _discover_examples, get_example_registry
from docs_site._internal.pipeline import render_page


def test_registry_discovers_card_example() -> None:
    registry = get_example_registry()
    assert "card" in registry
    info = registry["card"]
    assert info.page_cls.__name__ == "CardPage"
    assert info.example_dir.name == "card"


def test_example_card_renders_tabs_iframe_and_source() -> None:
    import re

    info = get_example_registry()["card"]
    html = str(ExampleCard(name="card", info=info))
    assert 'class="tabbed-set example-card"' in html
    assert 'src="/examples/card/"' in html
    assert ">Live demo</label>" in html
    assert ">Component</label>" in html
    assert 'class="highlight"' in html  # the source is Pygments-highlighted
    # Each input id is matched by its label's `for` (set via c-id / c-bind), and
    # the three ids are distinct.
    input_ids = re.findall(r'<input[^>]*\bid="([^"]+)"', html)
    label_fors = re.findall(r'<label[^>]*\bfor="([^"]+)"', html)
    assert len(input_ids) == 3
    assert input_ids == label_fors
    assert len(set(input_ids)) == 3


def test_two_cards_for_same_example_get_distinct_ids() -> None:
    import re

    # The same example twice on one page must not produce duplicate radio ids.
    html = render_page('<c-example name="card" />\n\n<c-example name="card" />').html
    ids = re.findall(r'id="(__tabbed_ex_card_[^"]+)"', html)
    assert len(ids) == 6  # two cards, three radios each
    assert len(set(ids)) == 6  # all distinct


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
    # minify=False keeps the output unminified so the structural asserts below
    # match the rendered markup rather than the shrunk form.
    out = tmp_path / "site"
    outcome = build_site(config=DocsConfig(site_dir=out), minify=False)
    assert outcome.examples >= 1
    demo = out / "examples" / "card" / "index.html"
    assert demo.is_file()
    demo_html = demo.read_text(encoding="utf-8")
    assert 'class="demo-card"' in demo_html  # the component rendered
    assert ".demo-card" in demo_html  # and its CSS was injected
