"""Tests for the API-reference category pages, build, and dev-server routes."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from docs_site._internal.build import build_site
from docs_site._internal.config import DocsConfig
from docs_site._internal.pipeline import render_page
from docs_site._internal.reference import extract_symbol, public_entrypoints
from docs_site._internal.reference_pages import CATEGORIES, category, reference_nav_items, reference_page_markdown
from docs_site._internal.serve import create_app


def test_every_category_symbol_resolves() -> None:
    # Guards against a typo in the (hand-written) category symbol lists.
    missing = [
        symbol
        for cat in CATEGORIES
        if cat.source == "griffe"
        for symbol in cat.symbols
        if extract_symbol(symbol) is None
    ]
    assert missing == []


def test_every_reference_page_stays_pending_human_review() -> None:
    items = reference_nav_items()

    assert items[0].title == "Overview"
    assert all(item.needs_review for item in items)
    assert all("🚧" not in item.title for item in items)


def test_public_entrypoints_are_the_three_shapes() -> None:
    # The public API is exactly three entrypoint shapes: the root package,
    # each citry.contrib module, and each citry.ext extension package.
    assert public_entrypoints() == [
        "citry",
        "citry.contrib.asgi",
        "citry.contrib.caches",
        "citry.contrib.django",
        "citry.contrib.fastapi",
        "citry.contrib.flask",
        "citry.contrib.wsgi",
        "citry.ext.cache",
        "citry.ext.debug",
        "citry.ext.dependencies",
        "citry.ext.events",
    ]


def test_categories_cover_the_public_api() -> None:
    # Every name a public entrypoint exports must be rendered on some
    # reference page, either under the entrypoint's own path or as the root
    # re-export. The reference is the enforcement of the public-API rule, so
    # a new export without a page fails here.
    covered = {s for cat in CATEGORIES if cat.source == "griffe" for s in cat.symbols}
    uncovered = [
        f"{entrypoint}.{name}"
        for entrypoint in public_entrypoints()
        for name in importlib.import_module(entrypoint).__all__
        if f"{entrypoint}.{name}" not in covered and f"citry.{name}" not in covered
    ]
    assert uncovered == [], f"public names with no reference page: {uncovered}"


def test_every_public_entrypoint_declares_all() -> None:
    # Public __init__ files are pure re-export surfaces; __all__ is how an
    # entrypoint says what it exports, so every entrypoint must declare one.
    missing = [e for e in public_entrypoints() if not hasattr(importlib.import_module(e), "__all__")]
    assert missing == []


def test_component_public_class_members_are_visible_to_reference_extraction() -> None:
    assert extract_symbol("citry.Component.class_id") is not None
    assert extract_symbol("citry.Component.definition_id") is not None
    assert extract_symbol("citry.Component.State") is not None
    events = extract_symbol("citry.Component.Events")
    assert events is not None
    assert "Optional server event handlers" in events.description
    assert extract_symbol("citry.Citry.engine_id") is not None
    assert extract_symbol("citry.Citry.inspect_component") is not None
    assert extract_symbol("citry.Citry.inspect_components") is not None


def test_page_markdown_uses_the_right_directive() -> None:
    attrs = reference_page_markdown(category("attributes"))
    assert "# HTML attributes" in attrs
    assert '<c-docstring path="citry.format_attrs" />' in attrs

    with pytest.raises(ValueError, match="authored"):
        reference_page_markdown(category("builtins"))
    with pytest.raises(ValueError, match="authored"):
        reference_page_markdown(category("browser-apis"))


def test_builtin_directive_renders() -> None:
    html = render_page('<c-builtin tag="provide" c-level="3" />').html
    assert "&lt;c-provide&gt;" in html  # the tag name, escaped
    assert '<h3 id="c-provide"' in html
    assert "<c-builtin" not in html


def test_unknown_builtin_shows_error() -> None:
    html = render_page('<c-builtin tag="nope" />').html
    assert "Unknown built-in: nope" in html


def test_build_writes_reference_pages(tmp_path: Path) -> None:
    out = tmp_path / "site"
    outcome = build_site(config=DocsConfig(site_dir=out))
    generated = sum(not cat.authored for cat in CATEGORIES)
    assert outcome.reference == generated + 1  # generated categories plus index
    assert (out / "reference" / "index.html").is_file()
    component_page = out / "reference" / "component" / "index.html"
    assert component_page.is_file()
    component_html = component_page.read_text(encoding="utf-8")
    assert "<code>Component</code>" in component_html
    assert "id=citry-component-events" in component_html
    assert "Optional server event handlers" in component_html

    # Each authored category owns one record and a Markdown companion. The
    # generated pass must not overwrite or duplicate either one.
    for slug in ("browser-apis", "builtins"):
        records = [record for record in outcome.records if record.url == f"reference/{slug}/"]
        assert len(records) == 1
        assert records[0].source_md is not None
        assert records[0].source_md.name == f"{slug}.md"
        assert (out / "reference" / slug / "index.md").is_file()


def test_serve_reference_routes(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "reference").mkdir()
    (content / "reference" / "builtins.md").write_text(
        "# Built-in tags\n\nAuthored marker.\n",
        encoding="utf-8",
    )
    (content / "reference" / "browser-apis.md").write_text(
        "# Browser APIs\n\nBrowser marker.\n",
        encoding="utf-8",
    )
    config = DocsConfig(content_dir=content, site_dir=tmp_path / "site", repo_root=tmp_path)
    client = TestClient(create_app(config=config))

    assert client.get("/reference/").status_code == 200
    page = client.get("/reference/nodes/")
    assert page.status_code == 200
    assert "Nodes" in page.text
    builtins = client.get("/reference/builtins/")
    assert builtins.status_code == 200
    assert "Authored marker." in builtins.text
    browser = client.get("/reference/browser-apis/")
    assert browser.status_code == 200
    assert "Browser marker." in browser.text
    assert client.get("/reference/nope/").status_code == 404
