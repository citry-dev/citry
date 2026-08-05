"""
Anchor guard.

For every ``<a href="...#fragment">``, the fragment must exist as an ``id=`` (or
a legacy ``<a name=>``) on the destination page. Same-page (``#foo``) links are
checked against the current page; cross-page links are checked against the page
the link resolves to.

Severity is WARNING: a broken anchor still loads the page, just at the wrong
scroll position, so it fails the build only under ``--strict``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.site_index import strip_base_path

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext
    from docs_site._internal.guards.site_index import PageRecord


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    index = ctx.site_index
    if index is None:
        return

    for page in index.pages:
        for link in page.links:
            if not link.anchor:
                continue

            target_page: PageRecord | None
            if link.is_anchor_only:
                target_page = page
            elif link.is_external:
                continue
            else:
                resolved = index.resolve_link(page.rel_path, strip_base_path(link.target, ctx.base_path))
                target_page = index.get_page(resolved)
                if target_page is None:
                    continue  # the internal_link guard owns the missing target

            if link.anchor not in target_page.anchors and link.anchor not in target_page.name_aliases:
                yield GuardResult.warning(
                    guard="anchor",
                    message=f"Broken anchor: {link.href!r} (no id={link.anchor!r} on target)",
                    source=page.label,
                )
