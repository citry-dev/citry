"""
Cross-version link guard (parity row 5b.15).

Asserts that every relative ``<a href>`` in ``docs_site/versions/`` resolves to a
real built page - both links within one version and links that cross from one
version's subtree into another. Because every version is persisted to the repo, a
``0.2.0/.. -> 0.1.0/..`` link is just a filesystem path that must exist.

It reuses the same ``SiteIndex`` parser and clean-URL resolver the ``internal_link``
guard uses, pointed at the whole versions tree so cross-version links resolve
against one unified index. What it skips is version-tree specific:

- absolute (``/...``) links - they resolve against the deploy site root, not a
  single version subtree, so they cannot be checked here;
- non-page assets (``.md`` companions, images) - mirrors ``internal_link``, via an
  explicit suffix allowlist so clean-URL version dirs like ``0.1.0/`` (whose
  trailing ``.0`` reads like a file extension) are still checked.

External / anchor / mailto links are skipped via the shared ``LinkRef`` flags.
Runs only when ``ctx.versions_dir`` is set.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.site_index import SiteIndex
from docs_site._internal.versioning import is_frozen_import

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Non-page targets to skip (raw markdown companions, images, other assets). An
# explicit allowlist - not "any non-.html suffix" - so links to clean-URL version
# dirs like `0.1.0/`, whose `.0` looks like an extension, are still checked.
_NON_PAGE_SUFFIXES = frozenset(
    {
        ".md",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        ".ico",
        ".css",
        ".js",
        ".json",
        ".txt",
        ".xml",
        ".pdf",
        ".zip",
        ".woff",
        ".woff2",
        ".ttf",
    }
)


def _is_non_page_asset(target: str) -> bool:
    return PurePosixPath(target.rstrip("/")).suffix.lower() in _NON_PAGE_SUFFIXES


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    root = ctx.versions_dir
    if root is None or not root.is_dir():
        return

    # One index over the whole tree: cross-version links resolve against it the
    # same way the browser resolves a relative href from a clean-URL page.
    index = SiteIndex(root)
    # A frozen import is historical HTML we never rebuild (old theme templates,
    # long-dead relative links), so we do not link-check it - only versions we
    # build ourselves. Cache the per-version verdict.
    frozen_verdict: dict[str, bool] = {}

    def _is_frozen(version: str) -> bool:
        if version not in frozen_verdict:
            frozen_verdict[version] = is_frozen_import(root / version)
        return frozen_verdict[version]

    for page in index.pages:
        parts = PurePosixPath(page.rel_path).parts
        if parts and _is_frozen(parts[0]):
            continue
        for link in page.links:
            if link.is_external or link.is_anchor_only or not link.target:
                continue
            if link.target.startswith("/") or _is_non_page_asset(link.target):
                continue
            if index.resolve_link(page.rel_path, link.target) is None:
                yield GuardResult.error(
                    guard="cross_version_link",
                    message=f"Broken link {link.href!r}: target not found on disk",
                    source=page.label,
                )
