"""
Crawl and indexing files written after the page build: sitemap, robots, indexing.

These three root-level files tell search engines what to crawl and index. They
are built from the list of pages the build already produced (each page's clean
URL, canonical, and whether it asked not to be indexed), so there is no second
pass over the written HTML.

What gets listed: the sitemap lists layout pages (content or reference, not a
live-demo page) that are not marked ``noindex``. The indexing manifest is a
wider audit: it lists every content and reference page the build recorded,
including any marked ``noindex``, with each page's real robots directive.
(Generated pages written outside that record list, such as the 404 page, are in
neither file.) The robots file allows everything, disallows the ``/v/`` trees of
old doc versions (so search engines index only the current release), names a few
AI crawlers explicitly so the stance is visible, and points at the sitemap.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape

from docs_site._internal.config import config as default_config
from docs_site._internal.git_metadata import get_page_git_meta
from docs_site._internal.project import current_docs_project
from docs_site._internal.versioning import load_manifest, select_indexed_versions

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from docs_site._internal.build import PageRecord


@dataclass
class SeoOutcome:
    """How many URLs the sitemap listed, pages the manifest covered, versions robots hid."""

    sitemap_urls: int
    # The manifest counts every recorded doc page, including noindex ones, so
    # this is not the number of pages search engines will actually index.
    manifest_pages: int
    # Old doc versions robots.txt tells crawlers to skip (a Disallow line each).
    disallowed_versions: int = 0


def generate_seo_files(
    records: list[PageRecord],
    output_dir: Path,
    *,
    site_url: str,
    version: str,
    generated_at: datetime,
    repo_root: Path,
    versions_root: Path | None = None,
) -> SeoOutcome:
    """
    Write sitemap.xml, robots.txt, and meta/indexing.json into a built site.

    ``versions_root`` is the committed docs version tree whose ``versions.json``
    drives the robots.txt old-version disallow list; it defaults to the configured
    versions dir. No manifest means no disallows (the single-version state).
    """
    base = site_url.rstrip("/")
    sitemap_urls = write_sitemap(records, output_dir, site_url=base, repo_root=repo_root)
    indexed = write_indexing_manifest(records, output_dir, site_url=base, version=version, generated_at=generated_at)
    disallowed = write_robots(output_dir, site_url=base, versions_root=versions_root)
    return SeoOutcome(sitemap_urls=sitemap_urls, manifest_pages=indexed, disallowed_versions=disallowed)


def _indexable(records: list[PageRecord]) -> list[PageRecord]:
    """Layout pages that should be crawled: a doc page that did not opt out of indexing."""
    return [r for r in records if r.is_doc_page and not r.noindex]


def _loc_for(record: PageRecord, site_url: str) -> str:
    """The page's absolute URL (its canonical, or one built from the site URL)."""
    return record.canonical or f"{site_url}/{record.url}"


def _priority_for(url: str) -> float:
    """Sitemap <priority> for a clean URL: home is 1.0, sections per the rules, else 0.5."""
    path = url.strip("/")
    if not path:
        return 1.0
    for prefix, priority in current_docs_project().settings.seo.priorities:
        if path == prefix or path.startswith(prefix + "/"):
            return priority
    return 0.5


def _git_lastmod(page: PageRecord, repo_root: Path) -> str:
    """The page's editorial or git date (YYYY-MM-DD), or "" when unknown."""
    if page.editorial_updated is not None:
        return page.editorial_updated.date().isoformat()
    if page.source_md is None:
        return ""
    meta = get_page_git_meta(repo_root, page.source_md)
    return meta.last_updated.date().isoformat() if meta.last_updated else ""


def write_sitemap(records: list[PageRecord], output_dir: Path, *, site_url: str, repo_root: Path) -> int:
    """Write sitemap.xml listing every indexable URL. Returns the URL count."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    pages = sorted(_indexable(records), key=lambda r: r.url)
    for page in pages:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(_loc_for(page, site_url))}</loc>")
        lastmod = _git_lastmod(page, repo_root)
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <priority>{_priority_for(page.url):.1f}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (output_dir / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(pages)


def write_indexing_manifest(
    records: list[PageRecord],
    output_dir: Path,
    *,
    site_url: str,
    version: str,
    generated_at: datetime,
) -> int:
    """
    Write meta/indexing.json: an audit of the recorded doc pages.

    Unlike the sitemap, this lists all content and reference pages the build
    recorded (including any marked ``noindex``) and records each page's real
    robots directive. Generated pages written outside the record list (such as
    the 404 page) are not included. Returns the page count.
    """
    pages = []
    for page in sorted((r for r in records if r.is_doc_page), key=lambda r: r.url):
        loc = _loc_for(page, site_url)
        # The page's real robots directive (the same value the page's own
        # <meta name="robots"> carries), so the manifest records what will
        # actually be indexed rather than assuming every page is.
        robots = "noindex,follow" if page.noindex else "index,follow"
        pages.append({"url": loc, "canonical": page.canonical or loc, "robots": robots})
    data = {"generated_at": generated_at.date().isoformat(), "version": version, "pages": pages}
    meta_dir = output_dir / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "indexing.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return len(pages)


def _disallowed_versions(versions_root: Path) -> list[str]:
    """
    The old doc versions crawlers should skip: every version in the manifest
    outside the kept-indexed set (the newest few plus the ``latest`` alias).

    Newest-first, so the emitted Disallow lines are deterministic. An absent or
    empty manifest yields none (the single-version state, before any old versions
    exist).
    """
    manifest = load_manifest(versions_root)
    keep_recent = current_docs_project().versions.index_keep_recent
    kept = set(select_indexed_versions(manifest, keep_recent=keep_recent))
    return [str(info.version) for info in manifest if str(info.version) not in kept]


def write_robots(output_dir: Path, *, site_url: str, versions_root: Path | None = None) -> int:
    """
    Write robots.txt and return the number of old versions it disallowed.

    Allows every crawler, disallows each old ``/v/<version>/`` tree, and points
    at the sitemap. ``versions_root`` (the committed docs version tree) defaults
    to the configured versions dir.
    """
    root = versions_root if versions_root is not None else default_config.versions_dir
    disallowed = _disallowed_versions(root)

    lines = ["User-agent: *", "Allow: /"]
    lines += [f"Disallow: /v/{version}/" for version in disallowed]
    lines += ["", f"Sitemap: {site_url}/sitemap.xml"]
    (output_dir / "robots.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(disallowed)
