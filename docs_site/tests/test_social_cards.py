"""Tests for per-page social-card generation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from docs_site._internal import social_cards
from docs_site._internal.build import PageRecord
from docs_site._internal.components.doc_page import default_og_image_url
from docs_site._internal.components.og_card import OgCard
from docs_site._internal.nav import NavTree
from docs_site._internal.social_cards import generate_social_cards, og_image_rel

_SITE = "https://x.test"


def _doc_html(og_url: str) -> str:
    return (
        f"<!DOCTYPE html><html><head>"
        f'<meta property="og:image" content="{og_url}">'
        f'<meta property="twitter:image" content="{og_url}">'
        f"</head><body><h1>X</h1></body></html>"
    )


def _record(url: str, **kw: Any) -> PageRecord:
    fields: dict[str, Any] = {
        "canonical": f"{_SITE}/{url}",
        "title": url or "Home",
        "description": "A page.",
        "noindex": False,
        "is_doc_page": True,
        "source_md": None,
        "markdown_body": "",
    }
    fields.update(kw)
    return PageRecord(url=url, **fields)


def _fake_render(cards: list, cache_dir: Path, _log: Any) -> tuple[int, str]:
    """Stand in for the headless-browser render by writing a placeholder PNG per card."""
    for card in cards:
        (cache_dir / f"{card.digest}.png").write_bytes(b"\x89PNG placeholder")
    return len(cards), ""


def test_og_card_renders_standalone() -> None:
    html = str(OgCard(title="Components", description="Renders a template.", section="Concepts"))
    assert "<!DOCTYPE html>" in html
    assert "Concepts" in html
    assert "Components" in html
    assert "Renders a template." in html


def test_og_image_rel_maps_url_to_png() -> None:
    assert og_image_rel("") == "og/index.png"
    assert og_image_rel("concepts/components/") == "og/concepts/components.png"


def test_skips_cleanly_without_a_browser(tmp_path: Path, monkeypatch: Any) -> None:
    # Force the optional playwright import to fail so the no-browser path runs
    # deterministically whether or not playwright is installed (the e2e test group
    # installs it). A None entry in sys.modules makes the import raise ImportError.
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)

    out = tmp_path / "site"
    out.mkdir()
    default = default_og_image_url(_SITE)
    page = out / "index.html"
    page.write_text(_doc_html(default), encoding="utf-8")

    outcome = generate_social_cards(out, [_record("")], NavTree(), site_url=_SITE, cache_dir=tmp_path / "cache")

    # Playwright/Chromium is not available here, so nothing is placed and the
    # page keeps its default OG image.
    assert outcome.placed == 0
    assert outcome.skipped_reason in {"playwright-missing", "chromium-missing"}
    assert default in page.read_text(encoding="utf-8")


def test_places_card_and_rewrites_og_image(tmp_path: Path, monkeypatch) -> None:
    out = tmp_path / "site"
    (out / "guide").mkdir(parents=True)
    default = default_og_image_url(_SITE)
    page = out / "guide" / "index.html"
    page.write_text(_doc_html(default), encoding="utf-8")
    monkeypatch.setattr(social_cards, "_render_cards", _fake_render)

    outcome = generate_social_cards(out, [_record("guide/")], NavTree(), site_url=_SITE, cache_dir=tmp_path / "cache")

    assert outcome.placed == 1
    assert (out / "og" / "guide.png").is_file()
    html = page.read_text(encoding="utf-8")
    assert f"{_SITE}/og/guide.png" in html  # og:image and twitter:image rewritten
    assert default not in html


def test_custom_og_image_page_is_left_untouched(tmp_path: Path) -> None:
    out = tmp_path / "site"
    out.mkdir()
    custom = f"{_SITE}/static/img/custom.png"  # not the site default
    page = out / "index.html"
    page.write_text(_doc_html(custom), encoding="utf-8")

    outcome = generate_social_cards(out, [_record("")], NavTree(), site_url=_SITE, cache_dir=tmp_path / "cache")

    assert outcome.eligible == 0  # the default URL is absent, so the page is skipped
    assert custom in page.read_text(encoding="utf-8")


def test_noindex_page_is_skipped(tmp_path: Path) -> None:
    out = tmp_path / "site"
    out.mkdir()
    page = out / "index.html"
    page.write_text(_doc_html(default_og_image_url(_SITE)), encoding="utf-8")

    outcome = generate_social_cards(
        out, [_record("", noindex=True)], NavTree(), site_url=_SITE, cache_dir=tmp_path / "cache"
    )

    assert outcome.eligible == 0


def test_prune_drops_unused_cache_entries(tmp_path: Path, monkeypatch) -> None:
    out = tmp_path / "site"
    out.mkdir()
    page = out / "index.html"
    page.write_text(_doc_html(default_og_image_url(_SITE)), encoding="utf-8")
    cache = tmp_path / "cache"
    cache.mkdir()
    stale = cache / "deadbeef.png"
    stale.write_bytes(b"old")
    monkeypatch.setattr(social_cards, "_render_cards", _fake_render)

    generate_social_cards(out, [_record("")], NavTree(), site_url=_SITE, cache_dir=cache)

    assert not stale.exists()  # the unreferenced card was pruned
