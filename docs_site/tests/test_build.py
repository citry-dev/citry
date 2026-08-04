"""Tests for the static-site build (walk content -> write clean-URL HTML)."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
import yaml

from docs_site._internal.build import BuildOutcome, build_site
from docs_site._internal.config import DocsConfig
from docs_site._internal.config import config as default_config
from docs_site._internal.config_loading import DocsConfigError
from docs_site._internal.pipeline import render_page
from docs_site._internal.project import load_docs_project


def _default_declarations() -> dict[str, Path]:
    return {
        name: getattr(default_config, name)
        for name in (
            "settings_config",
            "reference_config",
            "ui_library_config",
            "redirects_config",
            "versions_config",
            "people_sources_config",
        )
    }


def _write_blog(content: Path) -> Path:
    """Write a small valid Blog and return its dated post source."""
    nav = content / "_nav.yml"
    if not nav.exists():
        nav.write_text(
            "areas:\n"
            "  - label: Blog\n"
            "    source: blog\n"
            "    scope: site\n"
            "    entry: { title: All posts, path: /blog/ }\n",
            encoding="utf-8",
        )
    blog = content / "blog"
    blog.mkdir()
    (blog / "index.md").write_text(
        "---\ntitle: Blog\ndescription: News from Citry.\n---\n\n<c-blog-list />\n",
        encoding="utf-8",
    )
    post = blog / "2026-07-27-first-post.md"
    post.write_text(
        "---\n"
        "title: First post\n"
        "description: The first Blog post.\n"
        "date: 2026-07-27T09:00:00+02:00\n"
        "updated: 2026-07-27T10:00:00+02:00\n"
        "author: Citry maintainers\n"
        "author_url: https://github.com/citry-dev\n"
        "tags: Citry, project news\n"
        "---\n\n"
        "Opening paragraph.\n\n## Details\n\nDurable guidance lives in [the guide](../guide.md).\n",
        encoding="utf-8",
    )
    return post


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
    config = DocsConfig(
        content_dir=content,
        site_dir=tmp_path / "site",
        repo_root=tmp_path,
        base_dir=tmp_path,
        **_default_declarations(),
    )

    build_site(config=config)

    assert (config.site_dir / "static" / "css" / "site.css").read_text(encoding="utf-8") == "body{}"


def test_redirect_cannot_overwrite_an_orphan_authored_page(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Docs\n    items: [{ title: Home, path: / }]\n",
        encoding="utf-8",
    )
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
    redirects = tmp_path / "redirects.yml"
    redirects.write_text("redirects:\n  - { from: /orphan/, to: / }\n", encoding="utf-8")
    output = tmp_path / "site"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    cfg = DocsConfig(
        content_dir=content,
        site_dir=output,
        redirects_config=redirects,
    )

    with pytest.raises(DocsConfigError, match="collides"):
        build_site(config=cfg, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_ui_projection_preflight_preserves_existing_output(tmp_path: Path) -> None:
    content = tmp_path / "content"
    content.mkdir()
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: UI\n"
        "    items: [{ title: Home, path: / }]\n"
        "    groups:\n"
        "      - label: Components\n"
        "        source: ui_library\n",
        encoding="utf-8",
    )
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (tmp_path / "button.md").write_text("---\ntitle: Button\n---\n\n# Button\n", encoding="utf-8")
    ui_manifest = tmp_path / "ui_library.yml"
    ui_manifest.write_text(
        "components:\n"
        "  - family: button\n"
        "    slug: button\n"
        "    source: button.md\n"
        "    required_headings: ['#### Button inputs']\n",
        encoding="utf-8",
    )
    output = tmp_path / "site"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    cfg = DocsConfig(
        repo_root=tmp_path,
        content_dir=content,
        site_dir=output,
        ui_library_config=ui_manifest,
    )

    with pytest.raises(DocsConfigError, match="title and description"):
        build_site(config=cfg, minify=False, search=False, social_cards=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_custom_repository_identity_reaches_every_generated_surface(tmp_path: Path) -> None:
    settings_source = default_config.settings_config.read_text(encoding="utf-8")
    settings_path = tmp_path / "settings.yml"
    settings_path.write_text(
        settings_source.replace("owner: citry-dev", "owner: acme", 1)
        .replace("name: citry", "name: widgets", 1)
        .replace(
            "url: https://github.com/citry-dev/citry",
            "url: https://github.com/acme/widgets",
            1,
        )
        .replace(
            "issues_url: https://github.com/citry-dev/citry/issues",
            "issues_url: https://github.com/acme/widgets/issues",
            1,
        ),
        encoding="utf-8",
    )
    cfg = DocsConfig(
        site_dir=tmp_path / "site",
        settings_config=settings_path,
        site_url="https://docs.acme.test/",
    )
    project = load_docs_project(cfg)

    outcome = build_site(
        project=project,
        minify=False,
        search=False,
        social_cards=False,
    )
    direct = render_page(
        "Repository: [{{ repo_full_name }}]({{ repo_url }}). Issue #123.",
        project=project,
        wrap_in_layout=False,
    ).html
    home = (outcome.output_dir / "index.html").read_text(encoding="utf-8")
    authored = (outcome.output_dir / "concepts" / "components" / "index.html").read_text(encoding="utf-8")
    generated = (outcome.output_dir / "reference" / "component" / "index.html").read_text(encoding="utf-8")
    not_found = (outcome.output_dir / "404.html").read_text(encoding="utf-8")

    assert outcome.failed == 0
    assert "https://github.com/acme/widgets" in home
    assert "https://github.com/acme/widgets/edit/main/docs_site/content/concepts/components.md" in authored
    assert "https://github.com/acme/widgets/blob/main/packages/py/citry/citry/component.py" in generated
    assert "https://github.com/acme/widgets/issues" in not_found
    assert 'data-search-site-domain="docs.acme.test"' in authored
    assert '<a href="https://github.com/acme/widgets">acme/widgets</a>' in direct
    assert "https://github.com/acme/widgets/issues/123" in direct


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
    config = DocsConfig(
        content_dir=content,
        site_dir=tmp_path / "site",
        repo_root=tmp_path,
        base_dir=tmp_path,
        **_default_declarations(),
    )

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
        **_default_declarations(),
    )
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Docs\n    items:\n      - { title: Home, path: / }\n",
        encoding="utf-8",
    )
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


def test_build_publishes_blog_at_stable_routes_with_feed_and_companions(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    config.site_url = "https://citry.dev/"
    (content / "guide.md").write_text("# Guide\n", encoding="utf-8")
    source = _write_blog(content)

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    assert outcome.failed == 0
    assert outcome.blog_posts == 1
    assert outcome.blog_feed
    assert (out / "blog" / "index.html").is_file()
    post_html = out / "blog" / "first-post" / "index.html"
    assert post_html.is_file()
    assert not (out / "blog" / "2026-07-27-first-post").exists()
    html = post_html.read_text(encoding="utf-8")
    assert "First post" in html
    assert 'href="../../guide/"' in html
    assert 'type="application/atom+xml"' in html

    companion = (out / "blog" / "first-post" / "index.md").read_text(encoding="utf-8")
    assert "url: https://citry.dev/blog/first-post/" in companion
    assert 'date: "2026-07-27T09:00:00+02:00"' in companion
    assert 'updated: "2026-07-27T10:00:00+02:00"' in companion
    assert 'author: "Citry maintainers"' in companion
    assert '  - "project news"' in companion

    record = next(record for record in outcome.records if record.url == "blog/first-post/")
    assert record.source_md == source
    assert record.editorial_updated is not None
    assert record.editorial_updated.isoformat() == "2026-07-27T10:00:00+02:00"

    feed = ET.parse(out / "blog" / "feed.xml").getroot()  # noqa: S314 - parses our serializer output
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entry = feed.find("atom:entry", ns)
    assert entry is not None
    assert entry.findtext("atom:title", namespaces=ns) == "First post"
    assert entry.find("atom:link", ns).attrib["href"] == "https://citry.dev/blog/first-post/"


def test_blog_companion_quotes_catalog_metadata_as_valid_yaml(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    config.site_url = "https://citry.dev/"
    source = _write_blog(content)
    authored = source.read_text(encoding="utf-8")
    authored = authored.replace("title: First post", 'title: "Migration: lessons learned"')
    authored = authored.replace(
        "description: The first Blog post.",
        r"""description: 'A path C:\tmp and a "quote".' """,
    )
    source.write_text(authored, encoding="utf-8")

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    assert outcome.failed == 0
    companion = (out / "blog" / "first-post" / "index.md").read_text(encoding="utf-8")
    metadata = yaml.safe_load(companion.split("---", 2)[1])
    assert metadata["title"] == "Migration: lessons learned"
    assert metadata["description"] == 'A path C:\\tmp and a "quote".'


def test_version_build_excludes_blog_without_validating_current_posts(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    config.versions_dir = tmp_path / "versions"
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Docs\n"
        "    items:\n"
        "      - { title: Home, path: / }\n"
        "  - label: Blog\n"
        "    source: blog\n"
        "    scope: site\n"
        "    entry: { title: All posts, path: /blog/ }\n",
        encoding="utf-8",
    )
    _write_blog(content).write_text("invalid current Blog source", encoding="utf-8")

    outcome = build_site(
        config=config,
        output_dir=out,
        docs_version="1.0.0",
        minify=False,
        search=False,
        social_cards=False,
        update_versions_manifest=False,
    )

    assert outcome.failed == 0
    assert outcome.blog_posts == 0
    assert not outcome.blog_feed
    assert outcome.reference == 0
    assert outcome.releases == 0
    assert not (out / "objects.inv").exists()
    assert not (out / "blog").exists()
    home = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="/blog/"' in home


def test_omitted_scope_rejects_a_site_only_generated_source(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "_nav.yml").write_text(
        "areas:\n  - label: Docs\n    items: [{ title: Home, path: / }]\n  - label: Blog\n    source: blog\n",
        encoding="utf-8",
    )
    _write_blog(content).write_text("invalid current Blog source", encoding="utf-8")

    with pytest.raises(ValueError, match="must use scope 'site'"):
        build_site(
            config=config,
            output_dir=out,
            docs_version="1.0.0",
            minify=False,
            search=False,
            social_cards=False,
            update_versions_manifest=False,
        )


def test_scope_drives_snapshot_pages_assets_links_and_picker(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    config.base_path = "/citry"
    config.versions_dir = tmp_path / "versions"
    guide = content / "guide"
    news = content / "news"
    blog = content / "blog"
    guide.mkdir()
    news.mkdir()
    blog.mkdir()
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (guide / "a.md").write_text(
        "# A\n\n"
        "[B](/guide/b/)\n\n"
        "[News clean](/news/)\n\n"
        "[News source](../news/index.md)\n\n"
        "[Blog source](../blog/2026-07-27-first-post.md)\n\n"
        "![Versioned asset](diagram.svg)\n\n"
        "![Site asset](../news/logo.svg)\n",
        encoding="utf-8",
    )
    (guide / "b.md").write_text("# B\n", encoding="utf-8")
    (guide / "diagram.svg").write_text("<svg>guide</svg>", encoding="utf-8")
    (news / "index.md").write_text("# News\n", encoding="utf-8")
    (news / "draft.md").write_text("<c-this-must-not-render />\n", encoding="utf-8")
    (news / "logo.svg").write_text("<svg>news</svg>", encoding="utf-8")
    (blog / "index.md").write_text("invalid current Blog index", encoding="utf-8")
    (blog / "2026-07-27-first-post.md").write_text("invalid current Blog post", encoding="utf-8")
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Docs\n"
        "    scope: versioned\n"
        "    items: [{ title: Home, path: / }]\n"
        "    groups:\n"
        "      - label: Guides\n"
        "        items:\n"
        "          - { title: A, path: /guide/a/ }\n"
        "          - { title: B, path: /guide/b/ }\n"
        "  - label: News\n"
        "    scope: site\n"
        "    items: [{ title: News, path: /news/ }]\n"
        "  - label: Blog\n"
        "    source: blog\n"
        "    scope: site\n"
        "    entry: { title: All posts, path: /blog/ }\n",
        encoding="utf-8",
    )

    outcome = build_site(
        config=config,
        output_dir=out,
        docs_version="1.2.3",
        minify=False,
        search=False,
        social_cards=False,
        update_versions_manifest=False,
    )

    assert outcome.failed == 0
    assert (out / "guide" / "a" / "index.html").is_file()
    assert (out / "guide" / "diagram.svg").is_file()
    assert not (out / "news").exists()
    html = (out / "guide" / "a" / "index.html").read_text(encoding="utf-8")
    assert 'href="/citry/v/1.2.3/"' in html
    assert 'href="/citry/v/1.2.3/guide/b/"' in html
    assert 'href="/citry/news/"' in html
    assert 'href="/citry/blog/first-post/"' in html
    assert 'href="/news/"' not in html
    assert 'src="../diagram.svg"' in html
    assert 'src="/citry/news/logo.svg"' in html
    assert "djc-version-picker" in html
    not_found = (out / "404.html").read_text(encoding="utf-8")
    assert 'href="/citry/v/1.2.3/getting-started/installation/"' in not_found

    (blog / "index.md").write_text("# Blog\n\n<c-blog-list />\n", encoding="utf-8")
    (blog / "2026-07-27-first-post.md").write_text(
        "---\n"
        "title: First post\n"
        "description: A post.\n"
        "date: 2026-07-27T09:00:00+02:00\n"
        "author: Citry maintainers\n"
        "---\n\nBody.\n",
        encoding="utf-8",
    )
    root_out = tmp_path / "root-site"
    root = build_site(
        config=config,
        output_dir=root_out,
        minify=False,
        search=False,
        social_cards=False,
    )
    assert root.failed == 1  # the deliberately invalid unnaved News draft is read at the root
    news_html = (root_out / "news" / "index.html").read_text(encoding="utf-8")
    assert "djc-version-picker" not in news_html


def test_site_scoped_playground_is_built_only_at_the_root(tmp_path: Path) -> None:
    config, content, root_out = _config(tmp_path)
    config.versions_dir = tmp_path / "versions"
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    (content / "playground.md").write_text(
        "---\ntitle: Try Citry\nlayout: playground\n---\n\nHelp.\n",
        encoding="utf-8",
    )
    (content / "_nav.yml").write_text(
        "areas:\n"
        "  - label: Docs\n"
        "    scope: versioned\n"
        "    items: [{ title: Home, path: / }]\n"
        "  - label: Try it\n"
        "    scope: site\n"
        "    items: [{ title: Playground, path: /playground/ }]\n",
        encoding="utf-8",
    )

    root = build_site(
        config=config,
        output_dir=root_out,
        minify=False,
        search=False,
        social_cards=False,
    )
    snapshot_out = config.versions_dir / "1.2.3"
    snapshot = build_site(
        config=config,
        output_dir=snapshot_out,
        docs_version="1.2.3",
        minify=False,
        search=False,
        social_cards=False,
        update_versions_manifest=False,
    )

    assert root.failed == 0
    assert snapshot.failed == 0
    assert (root_out / "playground" / "index.html").is_file()
    assert not (snapshot_out / "playground").exists()
    snapshot_home = (snapshot_out / "index.html").read_text(encoding="utf-8")
    assert 'href="/playground/"' in snapshot_home
    assert 'href="/v/1.2.3/playground/"' not in snapshot_home


def test_site_scoped_landing_gets_a_version_snapshot_home_redirect(tmp_path: Path) -> None:
    config, content, out = _config(tmp_path)
    config.versions_dir = tmp_path / "versions"
    (content / "index.md").write_text("# Project landing\n", encoding="utf-8")
    (content / "guide.md").write_text("# Versioned guide\n", encoding="utf-8")
    (content / "_nav.yml").write_text(
        "home:\n"
        "  title: Project\n"
        "  path: /\n"
        "  scope: site\n"
        "areas:\n"
        "  - label: Docs\n"
        "    items:\n"
        "      - { title: Guide, path: /guide/ }\n",
        encoding="utf-8",
    )

    outcome = build_site(
        config=config,
        output_dir=out,
        docs_version="1.2.3",
        minify=False,
        search=False,
        social_cards=False,
        update_versions_manifest=False,
    )

    assert outcome.failed == 0
    assert (out / "guide" / "index.html").is_file()
    home = (out / "index.html").read_text(encoding="utf-8")
    assert 'content="0; url=guide/"' in home
    assert 'href="guide/"' in home
    assert "https://citry.dev/v/1.2.3/guide/" in home


def test_build_records_a_blog_post_render_failure(tmp_path: Path, monkeypatch) -> None:
    config, content, out = _config(tmp_path)
    post = _write_blog(content)
    post.write_text(post.read_text(encoding="utf-8").replace("Opening paragraph.", "BOOM"), encoding="utf-8")

    import docs_site._internal.build as build_mod

    real_render = build_mod.render_page

    def fake_render(source, **kwargs):
        if "BOOM" in source:
            raise RuntimeError("post failed")
        return real_render(source, **kwargs)

    monkeypatch.setattr(build_mod, "render_page", fake_render)

    outcome = build_site(config=config, minify=False, search=False, social_cards=False)

    assert outcome.failed == 1
    assert outcome.blog_posts == 0
    assert outcome.errors == [("blog/2026-07-27-first-post.md", "RuntimeError: post failed")]
    assert not (out / "blog" / "first-post" / "index.html").exists()


def test_build_refuses_unsafe_output(tmp_path: Path) -> None:
    config, content, _out = _config(tmp_path)
    (content / "index.md").write_text("# Home\n", encoding="utf-8")
    # Clearing the content dir itself would delete the sources.
    with pytest.raises(ValueError, match="unsafe output"):
        build_site(config=config, output_dir=content)
