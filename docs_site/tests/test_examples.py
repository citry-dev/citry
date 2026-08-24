"""Tests for example discovery, the ``<c-example />`` directive, and pre-render."""

from __future__ import annotations

from pathlib import Path

from docs_site._internal.build import build_site
from docs_site._internal.components.example_card import ExampleCard
from docs_site._internal.config import DocsConfig
from docs_site._internal.examples import (
    _discover_examples,
    get_example_by_slug,
    get_example_registry,
)
from docs_site._internal.pipeline import render_page


def test_registry_discovers_card_example() -> None:
    registry = get_example_registry()
    assert "card" in registry
    info = registry["card"]
    assert info.page_cls.__name__ == "CardPage"
    assert info.example_dir.name == "card"
    assert info.public_slug == "card"
    assert info.canonical_source == "examples/card.md"
    assert get_example_by_slug("control-flow").name == "control_flow"


def test_example_card_renders_tabs_iframe_and_source() -> None:
    import re

    info = get_example_registry()["card"]
    html = str(ExampleCard(name="card", info=info))
    assert 'class="tabbed-set example-card"' in html
    assert "data-pagefind-ignore" in html
    assert 'src="/examples/card/demo/"' in html
    assert 'title="Card example live demo"' in html
    assert 'sandbox="allow-forms allow-scripts allow-same-origin"' in html
    assert "example-demo-frame--theme-sync" in html
    assert "Live demo" in html
    assert "Component" in html
    assert 'class="highlight"' in html  # the source is Pygments-highlighted
    assert '<span class="nt">c-slot</span>' in html
    assert '<span class="nb">c-slot</span>' not in html
    assert html.index("Component") < html.index("Live demo")
    assert 'role="tablist"' in html
    assert html.count('role="tab"') == 3
    assert html.count('role="tabpanel"') == 3
    assert 'aria-selected="true"' in html
    assert 'tabindex="0"' in html
    # Each input id is matched by its label's `for` (set via c-id / c-bind), and
    # the three ids are distinct.
    input_ids = re.findall(r'<input[^>]*\bid="([^"]+)"', html)
    label_fors = re.findall(r'<label[^>]*\bfor="([^"]+)"', html)
    assert len(input_ids) == 3
    assert input_ids == label_fors
    assert len(set(input_ids)) == 3

    tabs_info = get_example_registry()["tabs"]
    tabs_html = str(ExampleCard(name="tabs", info=tabs_info))
    assert 'title="Tabs example live demo"' in tabs_html
    assert "example-demo-frame--theme-sync" not in tabs_html


def test_two_cards_for_same_example_get_distinct_ids() -> None:
    import re

    # The same example twice must not duplicate radio, tab, or panel ids.
    html = render_page('<c-example name="card" />\n\n<c-example name="card" />').html
    ids = re.findall(r'id="(__tabbed_ex_card_[^"]+)"', html)
    assert len(ids) == 18  # two cards, with three radio/tab/panel triplets each
    assert len(set(ids)) == 18  # all distinct


def test_example_directive_expands_in_a_page() -> None:
    result = render_page('# Examples\n\n<c-example name="card" />\n')
    html = result.html
    assert "tabbed-set example-card" in html
    assert 'src="/examples/card/demo/"' in html
    assert "<c-example" not in html  # the directive was expanded
    assert "### Component" in result.markdown_body
    assert "class Card(Component):" in result.markdown_body
    assert "[Open the live result](/examples/card/demo/)" in result.markdown_body
    assert "<iframe" not in result.markdown_body
    assert "tabbed-set" not in result.markdown_body
    assert 'class="highlight"' not in result.markdown_body
    assert "docs-example:" not in result.markdown_body


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
    recipe = out / "examples" / "card" / "index.html"
    assert recipe.is_file()
    assert "citry docs builder" in recipe.read_text(encoding="utf-8")

    demo = out / "examples" / "card" / "demo" / "index.html"
    assert demo.is_file()
    demo_html = demo.read_text(encoding="utf-8")
    assert 'class="demo-card"' in demo_html  # the component rendered
    assert ".demo-card" in demo_html  # and its CSS was injected

    companion = (out / "examples" / "card" / "index.md").read_text(encoding="utf-8")
    assert "class Card(Component):" in companion
    assert "[Open the live result](/examples/card/demo/)" in companion
    assert "<iframe" not in companion
    assert "tabbed-set" not in companion

    llms = (out / "llms.txt").read_text(encoding="utf-8")
    assert "https://citry.dev/examples/card/index.md" in llms
