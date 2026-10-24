"""
Validate the authored Blog tree: its strict catalog contract, and its links.

A blog post is dated and is read long after it was written, so a link from it
to ``main`` on GitHub would drift away from what the post described and break
once the file moves. Every file, folder, or raw-download link from a post into
the repository must name a commit SHA or release tag; "edit this page" links
(``edit/main/``) are allowed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.release_links import main_links

from docs_site._internal.blog import BlogCatalogError, load_blog_catalog
from docs_site._internal.guards.base import GuardResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    """Report the catalog's first source-located validation error, then every link to main in a post."""
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

    yield from _main_links_in_posts(ctx)


def _main_links_in_posts(ctx: GuardContext) -> Iterator[GuardResult]:
    """Report each line of a blog post that links to ``main`` on GitHub."""
    blog_dir = ctx.content_dir / "blog"
    if not blog_dir.is_dir():
        return
    for post in sorted(blog_dir.rglob("*.md")):
        source = post.relative_to(ctx.content_dir).as_posix()
        for number, line in enumerate(post.read_text(encoding="utf-8").splitlines(), start=1):
            for link in main_links(line):
                yield GuardResult.error(
                    guard="blog",
                    message=(
                        f"links to main: {link}; link to a commit SHA or release tag "
                        "that shows what the post describes"
                    ),
                    source=source,
                    line=number,
                )
