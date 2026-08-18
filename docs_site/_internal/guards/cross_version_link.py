"""
Cross-version link guard (parity row 5b.15).

Asserts that every relative ``<a href>`` in ``docs_site/versions/`` resolves to a
real built page - both links within one version and links that cross from one
version's subtree into another. Because every version is persisted to the repo, a
``0.2.0/.. -> 0.1.0/..`` link is just a filesystem path that must exist.

It reuses the same ``SiteIndex`` parser and clean-URL resolver the ``internal_link``
guard uses, pointed at the whole versions tree so cross-version links resolve
against one unified index. Absolute ``/v/<version>/...`` links are resolved
against that tree. Other root-absolute page links are allowed only when
``_nav.yml`` declares them site-scoped; a versioned target that escaped the
snapshot prefix is an error. Non-page assets (``.md`` companions, images) are
skipped via an explicit suffix allowlist so clean-URL version dirs like
``0.1.0/`` (whose trailing ``.0`` reads like a file extension) are still checked.

External / anchor / mailto links are skipped via the shared ``LinkRef`` flags.
Runs only when ``ctx.versions_dir`` is set.
"""

from __future__ import annotations

import json
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.site_index import SiteIndex, is_isolated_preview_page, strip_base_path
from docs_site._internal.nav import SCOPE_SITE, load_nav
from docs_site._internal.versioning import BUILD_INFO_NAME, is_frozen_import

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
        ".yml",
        ".yaml",
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
    nav_tree = load_nav(ctx.nav_path)
    # A frozen import is historical HTML we never rebuild (old theme templates,
    # long-dead relative links), so we do not link-check it - only versions we
    # build ourselves. Cache the per-version verdict.
    frozen_verdict: dict[str, bool] = {}
    site_routes: dict[str, tuple[str, ...] | None] = {}

    def _is_frozen(version: str) -> bool:
        if version not in frozen_verdict:
            frozen_verdict[version] = is_frozen_import(root / version)
        return frozen_verdict[version]

    def _site_patterns(version: str) -> tuple[str, ...] | None:
        if version in site_routes:
            return site_routes[version]
        try:
            data = json.loads((root / version / BUILD_INFO_NAME).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            site_routes[version] = None
            return None
        raw = data.get("site_routes")
        patterns = tuple(raw) if isinstance(raw, list) and all(isinstance(item, str) for item in raw) else None
        site_routes[version] = patterns
        return patterns

    for page in index.pages:
        if is_isolated_preview_page(page):
            continue
        parts = PurePosixPath(page.rel_path).parts
        version = parts[0] if parts else ""
        if version and _is_frozen(version):
            continue
        for link in page.links:
            if link.is_external or link.is_anchor_only or not link.target:
                continue
            target_path = strip_base_path(link.target, ctx.base_path)
            if _is_non_page_asset(target_path):
                continue
            if target_path.startswith("/v/"):
                target = "/" + target_path.removeprefix("/v/")
                if index.resolve_link(page.rel_path, target) is None:
                    yield GuardResult.error(
                        guard="cross_version_link",
                        message=f"Broken link {link.href!r}: target not found on disk",
                        source=page.label,
                    )
                continue
            if target_path.startswith("/"):
                patterns = _site_patterns(version)
                is_site = (
                    _matches_site_route(target_path, patterns)
                    if patterns is not None
                    else nav_tree.scope_for_url(target_path) == SCOPE_SITE
                )
                if not is_site:
                    yield GuardResult.error(
                        guard="cross_version_link",
                        message=(
                            f"Versioned root link {link.href!r} escapes its snapshot; expected a /v/<version>/ target"
                        ),
                        source=page.label,
                    )
                continue
            if index.resolve_link(page.rel_path, link.target) is None:
                yield GuardResult.error(
                    guard="cross_version_link",
                    message=f"Broken link {link.href!r}: target not found on disk",
                    source=page.label,
                )


def _matches_site_route(target: str, patterns: tuple[str, ...]) -> bool:
    normalized = "/" + target.strip("/")
    for pattern in patterns:
        if pattern.endswith("/*"):
            prefix = pattern[:-2].rstrip("/")
            if normalized == prefix or normalized.startswith(f"{prefix}/"):
                return True
        elif normalized == "/" + pattern.strip("/"):
            return True
    return False
