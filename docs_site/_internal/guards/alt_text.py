"""
Image alt-text guard.

Warns when a content ``<img>`` on a documentation page has missing or empty alt
text, which screen readers, broken-image fallbacks, and AI consumers all rely
on. Only DocPage content (the rendered documentation and reference pages) is
checked.
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
        if not page.is_doc_page or page.is_redirect_stub:
            continue
        for img in page.images:
            if not img.alt:  # None (missing) or "" (empty)
                yield GuardResult.warning(
                    guard="alt_text",
                    message=f"Image missing alt text: {img.src!r}",
                    source=page.label,
                )
