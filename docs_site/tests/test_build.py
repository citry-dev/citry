"""Tests for the static-site build (walk content -> write clean-URL HTML)."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from docs_site._internal.build import BuildOutcome, build_site
from docs_site._internal.config import DocsConfig


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

    # minify=False so the doctype assert below sees the rendered markup, not
    # the shrunk form (the default build lowercases <!doctype> and drops quotes).
    outcome = build_site(config=config, minify=False)

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
    # produce the other. (Once Pass 1 expands the custom <c-*> tags, a bad tag is a
    # real source of this; here we drive the mechanism directly.)
    import docs_site._internal.build as build_mod

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


def test_build_writes_404_and_runtime(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")

    outcome = build_site(config=config)

    not_found = out / "404.html"
    assert outcome.not_found
    assert not_found.is_file()
    text = not_found.read_text(encoding="utf-8")
    assert "Page not found" in text
    assert "noindex" in text  # the 404 must not be indexed

    # The 404 offers three ways forward. The search trigger opens the same modal
    # search.js wires on every [data-search-open]; substrings only, since the
    # minifier drops attribute quotes and reorders attributes.
    assert "data-search-open" in text
    assert "djc-notfound__search" in text
    assert "Search the documentation" in text
    # The four popular destinations (real built pages the internal_link guard checks).
    assert "/getting-started/installation/" in text
    assert "/getting-started/your-first-component/" in text
    assert "/concepts/components/" in text
    assert "/reference/" in text
    # And a link to report a page that has moved.
    assert "https://github.com/citry-dev/citry/issues" in text

    # The client runtime is written where pages reference it (/citry/citry.js).
    runtime = out / "citry" / "citry.js"
    assert outcome.runtime == runtime
    assert runtime.is_file()
    assert runtime.stat().st_size > 0
    events_runtime = out / "citry" / "ext" / "events" / "runtime.js"
    assert events_runtime.is_file()
    assert events_runtime.stat().st_size > 0


def test_build_records_doc_pages(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    (content / "index.md").write_text(
        "---\ntitle: Home\ndescription: The home page.\n---\n\n# Home\n", encoding="utf-8"
    )

    outcome = build_site(config=config)

    by_url = {r.url: r for r in outcome.records}
    assert "" in by_url  # the home page's clean URL is ""
    home = by_url[""]
    assert home.is_doc_page
    assert home.title == "Home"
    assert home.description == "The home page."
    assert home.source_md is not None


def test_build_minifies_by_default(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n\nA paragraph with     many     spaces.\n", encoding="utf-8")

    small = build_site(config=config, output_dir=tmp_path / "small", minify=True)
    large = build_site(config=config, output_dir=tmp_path / "large", minify=False)

    assert small.minified > 0
    assert large.minified == 0
    small_html = (tmp_path / "small" / "index.html").read_text(encoding="utf-8")
    large_html = (tmp_path / "large" / "index.html").read_text(encoding="utf-8")
    assert len(small_html) < len(large_html)


def test_build_generates_social_cards_from_a_running_event_loop(tmp_path: Path) -> None:
    # Regression: the social-card step drives Playwright's *sync* API, which
    # refuses to start when an asyncio event loop is already running in the
    # calling thread. That happens when a host app builds from within async code,
    # and in this suite when the browser e2e tests run first and leave their
    # session-scoped sync-Playwright fixture (and its loop) open on the main
    # thread. The render must run in its own thread and succeed regardless.
    pytest.importorskip("playwright")
    content = tmp_path / "content"
    content.mkdir()
    (content / "index.md").write_text("---\ntitle: Loop card\n---\n\n# Loop card\n", encoding="utf-8")
    # A fresh base_dir means an empty OG cache, so a card is actually rendered
    # this run (not copied from a prior run's cache) and the sync-Playwright path
    # is exercised under the running loop.
    config = DocsConfig(content_dir=content, site_dir=tmp_path / "site", repo_root=tmp_path, base_dir=tmp_path)

    async def _build() -> BuildOutcome:
        # A loop is now running in the calling thread: the failure condition.
        return build_site(config=config, social_cards=True)

    def _build_in_fresh_loop() -> BuildOutcome:
        # Start the loop in a fresh thread. A brand-new thread has no running loop,
        # so asyncio.run works here even when the pytest main thread already holds a
        # sync-Playwright loop open (as it does once the e2e tests have run), which
        # is what makes this reproduce the bug in any test order.
        return asyncio.run(_build())

    with ThreadPoolExecutor(max_workers=1) as pool:
        outcome = pool.submit(_build_in_fresh_loop).result()

    # The build must not raise "Sync API inside the asyncio loop"; when a browser
    # is available the card is rendered and placed from within the running loop.
    if not outcome.social_cards_skipped:
        assert outcome.social_cards_placed >= 1


def test_build_writes_md_companions(tmp_path: Path) -> None:
    # site_url is pinned so the companion `url:` is env-stable (independent of
    # DOCS_SITE_URL); everything else mirrors the clean-URL build test.
    content = tmp_path / "content"
    content.mkdir()
    out = tmp_path / "site"
    config = DocsConfig(content_dir=content, site_dir=out, repo_root=tmp_path, site_url="https://citry.dev/")
    (content / "index.md").write_text(
        "---\ntitle: Home\ndescription: The home page.\n---\n\nHome page.\n", encoding="utf-8"
    )
    (content / "guide").mkdir()
    (content / "guide" / "intro.md").write_text("# Intro\n\nIntro body.\n", encoding="utf-8")

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    # One `.md` companion per built content page, beside its index.html.
    assert outcome.built == 2
    assert outcome.companions == 2

    # guide/intro.md serves at /guide/intro/, so its companion sits at
    # guide/intro/index.md. Its front matter carries the title (taken from the
    # H1), the resolved canonical, and the description (this page sets none in
    # front matter, so it is derived from the first paragraph); the body is the
    # expanded markdown.
    companion = out / "guide" / "intro" / "index.md"
    assert companion.is_file()
    assert companion.read_text(encoding="utf-8") == (
        '---\ntitle: Intro\nurl: https://citry.dev/guide/intro/\ndescription: "Intro body."\n---\n'
        "# Intro\n\nIntro body.\n"
    )

    # The home page's companion sits at the site root, and its front matter also
    # carries the (quoted) description from the page's own front matter.
    home_companion = out / "index.md"
    assert home_companion.is_file()
    assert home_companion.read_text(encoding="utf-8") == (
        '---\ntitle: Home\nurl: https://citry.dev/\ndescription: "The home page."\n---\nHome page.'
    )


def test_build_expands_snippets_in_markdown_outputs(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    out = tmp_path / "site"
    config = DocsConfig(
        base_dir=tmp_path,
        content_dir=content,
        site_dir=out,
        repo_root=tmp_path,
        site_url="https://citry.dev/",
    )
    (content / "_nav.yml").write_text("sections:\n- label: Home\n  path: /\n", encoding="utf-8")
    (tmp_path / "snippet.py").write_text(
        "# --8<-- [start:example]\nclass IncludedFromSnippet:\n    pass\n# --8<-- [end:example]\n",
        encoding="utf-8",
    )
    (content / "index.md").write_text(
        '---\ntitle: Home\n---\n\n```citry\n--8<-- "snippet.py:example"\n```\n',
        encoding="utf-8",
    )

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    assert outcome.failed == 0
    for output in (out / "index.md", out / "llms-full.txt"):
        text = output.read_text(encoding="utf-8")
        assert "class IncludedFromSnippet:" in text
        assert '--8<-- "snippet.py:example"' not in text


def test_build_refuses_unsafe_output(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    # Clearing the content dir itself would delete the sources.
    with pytest.raises(ValueError, match="unsafe output"):
        build_site(config=config, output_dir=content)
