"""
Structured-headings guard.

Checks that heading levels never jump by more than one when descending (for
example an ``##`` followed directly by ``####`` skips ``###``). Skips break the
document outline that screen readers and the ``.md`` companion rely on. Only
DocPage content is checked.
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
        prev_level = 0
        for heading in page.headings:
            if prev_level and heading.level > prev_level + 1:
                label = heading.text or heading.id or "(untitled)"
                yield GuardResult.warning(
                    guard="headings",
                    message=f"Heading level jumps from h{prev_level} to h{heading.level}: {label!r}",
                    source=page.label,
                )
            prev_level = heading.level
