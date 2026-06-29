"""Tests for the static-site build (walk content -> write clean-URL HTML)."""

from __future__ import annotations

from pathlib import Path

import pytest

from docs_site.build import build_site
from docs_site.config import DocsConfig


def _config(tmp_path: Path) -> tuple[DocsConfig, Path, Path]:
    content = tmp_path / "content"
    content.mkdir()
    out = tmp_path / "site"
    return DocsConfig(content_dir=content, site_dir=out, repo_root=tmp_path), content, out


def test_build_writes_clean_urls(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    (content / "index.md").write_text("---\ntitle: Home\n---\n\nHome page.\n", encoding="utf-8")
    (content / "guide").mkdir()
    (content / "guide" / "intro.md").write_text("# Intro\n\nIntro body.\n", encoding="utf-8")

    outcome = build_site(config=config)

    assert outcome.built == 2
    assert outcome.failed == 0
    # index.md -> /  ; guide/intro.md -> /guide/intro/
    assert (out / "index.html").is_file()
    intro = out / "guide" / "intro" / "index.html"
    assert intro.is_file()
    assert "Intro body." in intro.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in intro.read_text(encoding="utf-8")


def test_build_copies_non_markdown_assets(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "img").mkdir()
    (content / "img" / "logo.svg").write_text("<svg></svg>", encoding="utf-8")

    build_site(config=config)

    assert (out / "img" / "logo.svg").read_text(encoding="utf-8") == "<svg></svg>"


def test_build_copies_static_assets(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    static_css = tmp_path / "static" / "css"
    static_css.mkdir(parents=True)
    (static_css / "site.css").write_text("body{}", encoding="utf-8")
    # base_dir points at tmp so the build finds tmp/static.
    config = DocsConfig(content_dir=content, site_dir=tmp_path / "site", repo_root=tmp_path, base_dir=tmp_path)

    build_site(config=config)

    assert (config.site_dir / "static" / "css" / "site.css").read_text(encoding="utf-8") == "body{}"


def test_build_records_failures_without_aborting(tmp_path: Path, monkeypatch) -> None:
    config, content, out = _config(tmp_path)
    (content / "ok.md").write_text("# Fine\n", encoding="utf-8")
    (content / "bad.md").write_text("BOOM\n", encoding="utf-8")

    # Make rendering raise for one page; the build must record it and still
    # produce the other. (Once Pass 1 expands directives, a bad directive is a
    # real source of this; here we drive the mechanism directly.)
    import docs_site.build as build_mod

    real_render = build_mod.render_page

    def fake_render(source, **kwargs):
        if "BOOM" in source:
            raise RuntimeError("kaboom")
        return real_render(source, **kwargs)

    monkeypatch.setattr(build_mod, "render_page", fake_render)

    outcome = build_site(config=config)

    assert outcome.built == 1
    assert outcome.failed == 1
    assert (out / "ok" / "index.html").is_file()
    assert outcome.errors
    assert outcome.errors[0][0] == "bad.md"


def test_build_refuses_unsafe_output(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    # Clearing the content dir itself would delete the sources.
    with pytest.raises(ValueError, match="unsafe output"):
        build_site(config=config, output_dir=content)
