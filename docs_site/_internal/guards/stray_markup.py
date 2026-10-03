"""
Stray-paragraph guard.

Fails the build when the markdown pass wrapped raw HTML in paragraph tags: an
empty ``<p></p>``, or a ``<p>`` opened right before a ``<div>``, ``<section>`` or
``<template>`` tag or its closing tag. A reader sees an unexplained gap, and content
after the break can move out of the element that styles it.

The usual cause is generated component markup that the pass tries to read as
Markdown. It gives up around preformatted code and around a ``<button>`` that
wraps block content, then wraps what follows in paragraphs. Components that
inject markup avoid this with ``flatten_for_markdown``; authored HTML avoids it
by keeping the whole block flush left with no blank lines inside it.

The check covers the page body and the HTML a page ships for Vue to build in
the browser, which is where the landing page keeps its content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.site_index import source_markdown

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Enough of the offending markup to find it, without flooding the report.
_MAX_REPORTED = 3


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    index = ctx.site_index
    if index is None:
        return

    for page in index.pages:
        if page.is_redirect_stub or not page.stray_markup:
            continue

        shown = page.stray_markup[:_MAX_REPORTED]
        extra = len(page.stray_markup) - len(shown)
        detail = "; ".join(repr(markup) for markup in shown)
        if extra > 0:
            detail += f"; and {extra} more"
        # The generated markup has no source line of its own, so name the
        # Markdown file whose raw HTML or component tag produced it.
        source = source_markdown(page, ctx.content_dir)
        yield GuardResult.error(
            guard="stray_markup",
            message=(
                f"Page wraps raw HTML in stray paragraph tags: {detail}. Keep raw HTML "
                "blocks flush left with no blank lines, and pass generated component "
                "markup through flatten_for_markdown."
            ),
            source=str(source) if source is not None else page.label,
        )
