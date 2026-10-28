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
by keeping the whole block flush left with no blank lines inside it. A fenced
code block followed on the very next line by text, such as the next list
item, gets wrapped in a paragraph the same way; a blank line after the
closing fence avoids it.

The report names the Markdown file, or CHANGELOG.md for a release-notes page,
and, when that text appears in the file, the line holding the text after the
first stray tag on the page.

The check covers the page body and the HTML a page ships for Vue to build in
the browser, which is where the landing page keeps its content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.site_index import source_line, source_markdown

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
        detail = "; ".join(repr(stray.markup) for stray in shown)
        if extra > 0:
            detail += f"; and {extra} more"
        # The stray tags have no source line of their own, but the text right
        # after the first one usually comes straight from the Markdown file.
        source = source_markdown(page, ctx.content_dir, ctx.repo_root)
        following = shown[0].following_text
        line = source_line(source, following, page) if source is not None and following else None
        where = f" The first one comes just before {following[:80]!r}." if following else ""
        yield GuardResult.error(
            guard="stray_markup",
            message=(
                f"The Markdown pass wrapped HTML in stray paragraph tags: {detail}.{where} Keep raw "
                "HTML blocks flush left with no blank lines, leave a blank line after a "
                "code block's closing fence, indent a code block inside a list item by 4 "
                "spaces, and pass generated component markup through flatten_for_markdown."
            ),
            source=str(source) if source is not None else page.label,
            line=line,
        )
