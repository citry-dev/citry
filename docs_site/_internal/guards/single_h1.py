"""
Single-H1 guard.

Each rendered doc page should have exactly one `<h1>`: zero hurts the page
title / outline, more than one hurts SEO and accessibility. Only pages rendered
through DocPage are checked (example demos and redirect stubs are skipped).
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
        count = page.h1_count
        if count != 1:
            yield GuardResult.warning(
                guard="single_h1",
                message=f"Page has {count} <h1> headings (expected exactly 1)",
                source=page.label,
            )
