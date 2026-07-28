"""Check that the built Atom feed matches the accepted Blog catalog."""

from __future__ import annotations

from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from docs_site._internal.blog import BLOG_FEED_PATH, BlogCatalogError, load_blog_catalog
from docs_site._internal.guards.base import GuardResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    """Require a well-formed, catalog-complete feed exactly when posts exist."""
    index = ctx.site_index
    if index is None:
        return
    try:
        catalog = load_blog_catalog(ctx.content_dir)
    except BlogCatalogError:
        return

    feed_path = index.build_dir / BLOG_FEED_PATH.lstrip("/")
    if not catalog.posts:
        if feed_path.exists():
            yield GuardResult.error(
                guard="blog_feed",
                message="Atom feed exists even though the Blog has no posts",
                source=BLOG_FEED_PATH.lstrip("/"),
            )
        return
    if not feed_path.is_file():
        yield GuardResult.error(
            guard="blog_feed",
            message="Blog posts exist but the Atom feed is missing",
            source=BLOG_FEED_PATH.lstrip("/"),
        )
        return

    try:
        root = ET.parse(feed_path).getroot()  # noqa: S314 - parses the local build artifact under test
    except ET.ParseError as exc:
        yield GuardResult.error(
            guard="blog_feed",
            message=f"Atom feed is not well-formed XML: {exc}",
            source=BLOG_FEED_PATH.lstrip("/"),
        )
        return

    if root.tag != "{http://www.w3.org/2005/Atom}feed":
        yield GuardResult.error(
            guard="blog_feed",
            message="Atom document root is not an Atom feed element",
            source=BLOG_FEED_PATH.lstrip("/"),
        )
        return

    required = ("title", "id", "updated")
    for name in required:
        if not (root.findtext(f"atom:{name}", namespaces=_ATOM_NS) or "").strip():
            yield GuardResult.error(
                guard="blog_feed",
                message=f"Atom feed is missing required {name!r} text",
                source=BLOG_FEED_PATH.lstrip("/"),
            )
    entries = root.findall("atom:entry", _ATOM_NS)
    if len(entries) != min(len(catalog.posts), 20):
        yield GuardResult.error(
            guard="blog_feed",
            message=(f"Atom feed has {len(entries)} entries; expected {min(len(catalog.posts), 20)}"),
            source=BLOG_FEED_PATH.lstrip("/"),
        )
    for entry in entries:
        missing = [
            name
            for name in ("title", "id", "published", "updated", "summary", "author")
            if entry.find(f"atom:{name}", _ATOM_NS) is None
        ]
        link = entry.find("atom:link[@rel='alternate']", _ATOM_NS)
        if missing or link is None or not link.attrib.get("href"):
            details = ", ".join(missing) if missing else "alternate link"
            yield GuardResult.error(
                guard="blog_feed",
                message=f"Atom entry is missing required content: {details}",
                source=BLOG_FEED_PATH.lstrip("/"),
            )
