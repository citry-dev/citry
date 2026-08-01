"""Validate the authored Blog tree through its strict catalog contract."""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.blog import BlogCatalogError, load_blog_catalog
from docs_site._internal.guards.base import GuardResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    """Report the catalog's first source-located validation error."""
    try:
        load_blog_catalog(ctx.content_dir)
    except BlogCatalogError as exc:
        try:
            source = exc.source.resolve().relative_to(ctx.content_dir.resolve()).as_posix()
        except ValueError:
            source = str(exc.source)
        yield GuardResult.error(
            guard="blog",
            message=exc.message,
            source=source,
            line=exc.line,
        )
