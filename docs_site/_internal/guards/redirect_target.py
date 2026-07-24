"""
Check that every redirect stub points at a page that exists.

A redirect stub (a ``<meta http-equiv="refresh">`` page from ``redirects.py``)
forwards an old URL to a new one. If the target does not resolve in the built
site, the redirect lands on a 404, so an unresolvable target is an error. Citry
emits no redirect stubs yet, so this is a no-op until the first page moves.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    index = ctx.site_index
    if index is None:
        return

    for page in index.pages:
        if not page.is_redirect_stub:
            continue
        target = (page.redirect_target or "").strip()
        if not target:
            yield GuardResult.error(
                guard="redirect_target", message="Redirect stub has no target URL", source=page.label
            )
            continue
        # External / absolute redirects are out of scope (we do not emit them).
        if target.startswith(("http://", "https://", "//")):
            continue
        path, _, _ = target.partition("#")
        path, _, _ = path.partition("?")
        if index.resolve_link(page.rel_path, path) is None:
            yield GuardResult.error(
                guard="redirect_target",
                message=f"Redirect target does not resolve to a built page: {target!r}",
                source=page.label,
            )
