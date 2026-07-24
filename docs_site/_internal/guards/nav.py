"""
Check that ``_nav.yml`` and the content pages agree with each other.

Catches two-way drift between ``content/`` and ``_nav.yml``:

- A ``_nav.yml`` entry whose page does not exist on disk -> error (dead nav
  link).
- A content page that no ``_nav.yml`` entry points at -> warning (orphan page),
  apart from the home page and the generated ``reference/`` and ``examples/``
  pages, which are never listed in ``_nav.yml``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.nav import load_nav
from docs_site._internal.paths import md_to_url

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Content pages that legitimately live outside the sidebar nav. The home page
# is the landing page, and anything under these prefixes is generated at build
# time rather than hand-listed in ``_nav.yml``.
_OMIT_PREFIXES = ("reference/", "examples/")


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

    # The set of clean URLs backed by an actual content markdown file.
    content_urls = {_norm(md_to_url(md.relative_to(content_dir))) for md in content_dir.rglob("*.md")}

    # 1. Every nav entry must resolve to an existing content page.
    for url in sorted(nav_urls):
        if url not in content_urls:
            yield GuardResult.error(
                guard="nav",
                message=f"_nav.yml entry points at a missing page: /{url}/",
                source=nav_path.name,
            )

    # 2. Every content page should appear in the nav (orphans are warnings),
    # apart from the home page and the generated reference/examples pages.
    for md in sorted(content_dir.rglob("*.md")):
        rel = md.relative_to(content_dir)
        url = _norm(md_to_url(rel))
        if _is_omitted(url):
            continue
        if url not in nav_urls:
            yield GuardResult.warning(
                guard="nav",
                message="Page is not referenced in _nav.yml (orphan)",
                source=rel.as_posix(),
            )
