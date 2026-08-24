"""Tests for the URL <-> content-file path mapping (docs_site._internal.paths)."""

from __future__ import annotations

from pathlib import Path

from docs_site._internal.paths import clean_url_to_companion_url, md_companion_path


def test_md_companion_path_slug_cases() -> None:
    out = Path("/site")
    # A flat page: foo.md serves at /foo/, so its companion sits beside the
    # page's index.html under the same clean-URL directory.
    assert md_companion_path(out, Path("guide/intro.md")) == out / "guide" / "intro" / "index.md"
    # A directory index: bar/index.md serves at /bar/, companion stays in place.
    assert md_companion_path(out, Path("guide/index.md")) == out / "guide" / "index.md"
    # The home page: index.md serves at /, companion at the site root.
    assert md_companion_path(out, Path("index.md")) == out / "index.md"


def test_clean_url_to_companion_url() -> None:
    assert clean_url_to_companion_url("/") == "/index.md"
    assert clean_url_to_companion_url("/guide/intro/") == "/guide/intro/index.md"
