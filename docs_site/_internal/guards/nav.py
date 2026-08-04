"""
Check that ``_nav.yml`` and the content pages agree with each other.

Catches two-way drift between ``content/`` and ``_nav.yml``:

- A ``_nav.yml`` entry whose page does not exist on disk -> error (dead nav
  link).
- A content page that no authored entry or generated source reaches -> warning.
- A resolved navigation entry absent from the built site -> error.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from docs_site._internal.blog import BLOG_INDEX_PATH, BlogCatalogError, load_blog_catalog
from docs_site._internal.guards.base import GuardResult
from docs_site._internal.nav import load_nav
from docs_site._internal.paths import md_to_url
from docs_site._internal.project import current_docs_project
from docs_site._internal.site_nav import load_site_nav_from_paths
from docs_site._internal.ui_library_projection import ui_library_nav_items

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Content pages that legitimately live outside the authored sidebar nav. The
# home page is the landing page; Reference navigation is generated from the
# category registry, including its authored categories.
_OMIT_PREFIXES = ("reference/",)


def _norm(url: str) -> str:
    """Drop leading/trailing slashes so nav and content URLs compare the same."""
    return url.strip("/")


def _is_omitted(url: str) -> bool:
    """True for pages that are allowed to be absent from ``_nav.yml``."""
    return url == "" or url.startswith(_OMIT_PREFIXES)


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    nav_path = ctx.nav_path
    if not nav_path.is_file():
        return

    content_dir = ctx.content_dir
    tree = load_nav(nav_path)
    nav_urls: set[str] = {_norm(item.path) for item in tree.flat_pages() if item.path}
    declared_sources = {area.source for area in tree.areas if area.source} | {
        group.source for area in tree.areas for group in area.groups if group.source
    }

    try:
        blog_catalog = load_blog_catalog(content_dir)
    except BlogCatalogError:
        # The Blog guard reports the source-located validation error. Continue
        # checking authored nav entries, but do not emit derivative Blog drift.
        blog_catalog = None

    coverage_urls = set(nav_urls)
    if blog_catalog is not None and "blog" in declared_sources:
        coverage_urls.update(_norm(item.path) for item in blog_catalog.nav_items())
    if "ui_library" in declared_sources:
        project = ctx.project or current_docs_project()
        coverage_urls.update(
            _norm(item.path)
            for item in ui_library_nav_items(
                project.ui_library,
                repo_root=ctx.repo_root,
                content_dir=ctx.content_dir,
            )
        )

    # The set of clean URLs backed by an actual content markdown file.
    content_urls: set[str] = set()
    for md in content_dir.rglob("*.md"):
        if blog_catalog is not None and (post := blog_catalog.post_for_source(md)) is not None:
            content_urls.add(_norm(post.public_path))
        else:
            content_urls.add(_norm(md_to_url(md.relative_to(content_dir))))

    # 1. Every nav entry must resolve to an existing content page.
    for url in sorted(nav_urls):
        if url not in content_urls:
            yield GuardResult.error(
                guard="nav",
                message=f"_nav.yml entry points at a missing page: /{url}/",
                source=nav_path.name,
            )

    # 2. Every content page should appear in the nav (orphans are warnings),
    # apart from the home page and Reference pages.
    for md in sorted(content_dir.rglob("*.md")):
        rel = md.relative_to(content_dir)
        post = blog_catalog.post_for_source(md) if blog_catalog is not None else None
        url = _norm(post.public_path if post else md_to_url(rel))
        if _is_omitted(url):
            continue
        if url not in coverage_urls:
            yield GuardResult.warning(
                guard="nav",
                message="Page is not referenced in _nav.yml (orphan)",
                source=rel.as_posix(),
            )

    # Generated sources are only knowable after hydration. On post-build runs,
    # verify that every resolved entry exists in the output as well.
    if ctx.site_index is None:
        return

    generated_roots = {
        "blog": PurePosixPath(BLOG_INDEX_PATH.lstrip("/")) / "index.html",
        "reference": PurePosixPath("reference/index.html"),
        "releases": PurePosixPath("releases/index.html"),
    }
    for source, root_page in generated_roots.items():
        if root_page in ctx.site_index.built_page_paths and source not in declared_sources:
            yield GuardResult.error(
                guard="nav",
                message=(f"Built pages from navigation source {source!r} are not declared in _nav.yml"),
                source=nav_path.name,
            )

    if blog_catalog is None and "blog" in declared_sources:
        return
    resolved = load_site_nav_from_paths(
        nav_path=nav_path,
        repo_root=ctx.repo_root,
        blog_catalog=blog_catalog,
        project=ctx.project or current_docs_project(),
    )
    for item in resolved.flat_pages():
        url = _norm(item.path)
        rel = PurePosixPath("index.html") if not url else PurePosixPath(url) / "index.html"
        if rel not in ctx.site_index.built_page_paths:
            yield GuardResult.error(
                guard="nav",
                message=(f"Resolved navigation entry is missing from the built site: {item.path}"),
                source=nav_path.name,
            )
