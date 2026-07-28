"""Load the authored navigation tree and hydrate declared generated sources."""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.nav import SCOPE_SITE, NavItem, NavTree, load_nav, resolve_nav_sources
from docs_site._internal.reference_pages import reference_nav_items
from docs_site._internal.release_notes import parse_changelog, releases_nav_items

if TYPE_CHECKING:
    from pathlib import Path

    from docs_site._internal.blog import BlogCatalog
    from docs_site._internal.config import DocsConfig


def load_site_nav(
    config: DocsConfig,
    *,
    blog_catalog: BlogCatalog | None = None,
    include_site_content: bool = True,
) -> NavTree:
    """Load ``_nav.yml`` with Reference and Release pages filled in place."""
    return load_site_nav_from_paths(
        nav_path=config.content_dir / "_nav.yml",
        repo_root=config.repo_root,
        blog_catalog=blog_catalog,
        include_site_content=include_site_content,
    )


def load_site_nav_from_paths(
    *,
    nav_path: Path,
    repo_root: Path,
    blog_catalog: BlogCatalog | None = None,
    include_site_content: bool = True,
) -> NavTree:
    """Load and hydrate navigation from explicit repository paths."""
    tree = load_nav(nav_path)

    def includes(source: str) -> bool:
        return include_site_content or tree.scope_for_source(source) != SCOPE_SITE

    release_items: list[NavItem] | None = None
    changelog = repo_root / "CHANGELOG.md"
    if includes("releases") and changelog.is_file():
        releases = parse_changelog(changelog.read_text(encoding="utf-8"))
        release_items = releases_nav_items(releases)
    elif not includes("releases"):
        release_items = tree.fallback_items_for_source("releases")

    blog_items: list[NavItem] | None = None
    if tree.has_source("blog"):
        if not includes("blog"):
            # A snapshot keeps the declared root-site escape link without
            # reading or validating the current generated content source.
            blog_items = tree.fallback_items_for_source("blog")
        elif blog_catalog is None:
            # Import lazily so ordinary navigation parsing remains independent
            # of the Blog content model.
            from docs_site._internal.blog import load_blog_catalog  # noqa: PLC0415

            blog_catalog = load_blog_catalog(nav_path.parent)
        if blog_catalog is not None:
            blog_items = blog_catalog.nav_items()

    reference_items = reference_nav_items() if includes("reference") else tree.fallback_items_for_source("reference")

    return resolve_nav_sources(
        tree,
        {
            "blog": blog_items,
            "reference": reference_items,
            "releases": release_items,
        },
    )
