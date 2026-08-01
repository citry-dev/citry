"""Tests for the crawl/index files: sitemap.xml, robots.txt, meta/indexing.json."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from docs_site._internal.build import PageRecord
from docs_site._internal.seo import AI_BOTS, generate_seo_files, write_robots, write_sitemap
from docs_site._internal.versioning import update_manifest


def _rec(
    url: str,
    *,
    noindex: bool = False,
    is_doc_page: bool = True,
    source_md: Path | None = None,
    editorial_updated: datetime | None = None,
) -> PageRecord:
    return PageRecord(
        url=url,
        canonical=f"https://x.test/{url}",
        title=url or "Home",
        description="",
        noindex=noindex,
        is_doc_page=is_doc_page,
        source_md=source_md,
        markdown_body="",
        editorial_updated=editorial_updated,
    )


def test_sitemap_lists_indexable_pages_with_priority(tmp_path: Path) -> None:
    records = [_rec(""), _rec("concepts/components/"), _rec("draft/", noindex=True), _rec("demo/", is_doc_page=False)]

    count = write_sitemap(records, tmp_path, site_url="https://x.test", repo_root=tmp_path)

    xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert count == 2  # noindex and non-doc pages are excluded
    assert "<loc>https://x.test/</loc>" in xml
    assert "<priority>1.0</priority>" in xml  # the home page
    assert "<loc>https://x.test/concepts/components/</loc>" in xml
    assert "<priority>0.6</priority>" in xml  # a concepts page
    assert "draft" not in xml
    assert "demo" not in xml


def test_sitemap_includes_git_lastmod_for_pages_with_a_source(tmp_path: Path, monkeypatch) -> None:
    import docs_site._internal.seo as seo_mod
    from docs_site._internal.git_metadata import PageGitMeta

    # A page with a source file gets a <lastmod> from git; one without gets none.
    src = tmp_path / "page.md"
    meta = PageGitMeta(created=None, last_updated=datetime(2026, 7, 1, 9, 0, tzinfo=UTC), authors=())
    monkeypatch.setattr(seo_mod, "get_page_git_meta", lambda _root, _path: meta)
    records = [_rec("guide/", source_md=src), _rec("nosrc/")]

    write_sitemap(records, tmp_path, site_url="https://x.test", repo_root=tmp_path)

    xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert "<lastmod>2026-07-01</lastmod>" in xml  # the git date, day-precision
    # The page without a source file has a <loc> but no <lastmod>.
    assert xml.count("<lastmod>") == 1


def test_sitemap_prefers_blog_editorial_date_over_git(tmp_path: Path, monkeypatch) -> None:
    import docs_site._internal.seo as seo_mod

    def fail_if_called(_root, _path):
        raise AssertionError("git metadata must not define a Blog editorial date")

    monkeypatch.setattr(seo_mod, "get_page_git_meta", fail_if_called)
    record = _rec(
        "blog/post/",
        source_md=tmp_path / "post.md",
        editorial_updated=datetime(2026, 7, 27, 10, 0, tzinfo=UTC),
    )

    write_sitemap([record], tmp_path, site_url="https://x.test", repo_root=tmp_path)

    xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert "<lastmod>2026-07-27</lastmod>" in xml


def test_generate_seo_writes_robots_and_indexing(tmp_path: Path) -> None:
    records = [
        _rec(""),
        _rec("concepts/slots/"),
        _rec("draft/", noindex=True),
        _rec("demo/", is_doc_page=False),
    ]

    # An empty versions tree: no old versions, so robots disallows nothing.
    outcome = generate_seo_files(
        records,
        tmp_path,
        site_url="https://x.test/",
        version="1.2.3",
        generated_at=datetime.now(tz=UTC),
        repo_root=tmp_path,
        versions_root=tmp_path / "versions",
    )

    robots = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert "User-agent: *" in robots
    assert "Allow: /" in robots
    assert "Disallow:" not in robots
    assert outcome.disallowed_versions == 0
    assert "Sitemap: https://x.test/sitemap.xml" in robots
    for bot in AI_BOTS:
        assert f"User-agent: {bot}" in robots

    data = json.loads((tmp_path / "meta" / "indexing.json").read_text(encoding="utf-8"))
    assert data["version"] == "1.2.3"
    # The manifest audits every doc page, including the noindex one; the demo
    # page is not a doc page, so it stays out.
    assert outcome.manifest_pages == 3
    robots_by_url = {p["url"]: p["robots"] for p in data["pages"]}
    assert robots_by_url == {
        "https://x.test/": "index,follow",
        "https://x.test/concepts/slots/": "index,follow",
        "https://x.test/draft/": "noindex,follow",
    }


def test_robots_disallows_old_versions(tmp_path: Path) -> None:
    # Four releases with latest on the newest: the newest two (plus latest, which
    # is the newest) stay crawlable, so the older two are disallowed.
    versions_root = tmp_path / "versions"
    update_manifest(versions_root, "1.0.0")
    update_manifest(versions_root, "1.1.0")
    update_manifest(versions_root, "1.2.0")
    update_manifest(versions_root, "1.3.0", aliases=("latest",))

    count = write_robots(tmp_path, site_url="https://x.test", versions_root=versions_root)

    robots = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert count == 2
    # Exactly the two oldest are disallowed, newest-first.
    assert "Disallow: /v/1.1.0/\nDisallow: /v/1.0.0/" in robots
    assert "Disallow: /v/1.2.0/" not in robots
    assert "Disallow: /v/1.3.0/" not in robots
    # The allow-all stance, sitemap pointer, and AI bots still follow the disallows.
    assert robots.startswith("User-agent: *\nAllow: /\nDisallow: /v/1.1.0/")
    assert "Sitemap: https://x.test/sitemap.xml" in robots
    for bot in AI_BOTS:
        assert f"User-agent: {bot}" in robots
