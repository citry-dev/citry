"""Regression coverage for the public output-caching guide."""

from __future__ import annotations

from docs_site._internal.config import config
from docs_site._internal.paths import md_to_url
from docs_site._internal.pipeline import render_page

_SOURCE_PATH = config.content_dir / "advanced" / "caching.md"


def test_guide_covers_every_phase_five_example_and_rejects_the_old_claim() -> None:
    source = _SOURCE_PATH.read_text(encoding="utf-8")

    assert "There is no per-component caching opt-in" not in source
    for expected in (
        "class ProductCard(Component):",
        'key="account-menu"',
        'c-vary="[current_user.id, locale]"',
        "class PersonalizedPanel(Component):",
        "component_cache_key(",
        "fragment_cache_key(",
        'version = "product-card-v2"',
        '"default_variation_slot_source": "not-applicable"',
    ):
        assert expected in source


def test_guide_renders_with_cache_tags_kept_as_example_text() -> None:
    source = _SOURCE_PATH.read_text(encoding="utf-8")

    html = render_page(
        source,
        current_path=md_to_url(_SOURCE_PATH.relative_to(config.content_dir)),
        source_path=_SOURCE_PATH,
        wrap_in_layout=False,
    ).html

    assert "Cache a component" in html
    assert "account-menu" in html
    assert "default_variation_slot_source" in html
