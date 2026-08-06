"""
Unrendered-Markdown guard.

Fails the build when a page shows Markdown source to the reader: a literal
``### Heading`` or ``[text](url)`` in visible text means the markdown pass
skipped a block it was meant to render.

The usual cause is a raw HTML wrapper without ``markdown="1"``. python-markdown
treats such a block as opaque, so a nested ``markdown="1"`` never fires and
every heading, bullet, and link inside it reaches the reader as source. The page
still builds, links inside it silently stop being links, and no other guard
notices, which is why this one exists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Enough of the offending text to find it, without flooding the report.
_MAX_REPORTED = 3


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    index = ctx.site_index
    if index is None:
        return

    for page in index.pages:
        if page.is_redirect_stub or not page.markdown_leaks:
            continue

        shown = page.markdown_leaks[:_MAX_REPORTED]
        extra = len(page.markdown_leaks) - len(shown)
        detail = "; ".join(repr(line) for line in shown)
        if extra > 0:
            detail += f"; and {extra} more line(s)"
        yield GuardResult.error(
            guard="rendered_markdown",
            message=(
                f"Page shows Markdown source instead of rendered HTML: {detail}. "
                'A wrapper element around this content is missing markdown="1", '
                "so the markdown pass skipped everything inside it."
            ),
            source=page.label,
        )
