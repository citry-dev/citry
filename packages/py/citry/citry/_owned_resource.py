"""Private authoritative bytes for resources served by Citry routes."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from typing import TYPE_CHECKING

from citry.util.routing import RouteResponse

if TYPE_CHECKING:
    from citry.util.routing import RouteRequest

PUBLIC_ASSET_CORS_HEADERS: tuple[tuple[str, str], ...] = (("Access-Control-Allow-Origin", "*"),)
"""
Headers that let any page read one of Citry's public JS or CSS files.

Citry puts ``integrity`` and ``crossorigin="anonymous"`` on the files it
serves itself. A browser checks ``integrity`` only on a response it may read,
and a page with an opaque origin (a sandboxed iframe without
``allow-same-origin``) counts every request as cross-origin, so without this
header the browser blocks the file and the page never starts.

The wildcard is safe for these routes only: they answer ``GET`` without reading
cookies, sessions, or any other request data, so the response does not depend
on who asks, and browsers never share a response to a credentialed request
that carries a wildcard. The header therefore lets a page read only what an
anonymous request for the same URL returns. A file built from one render's
``css_data()`` is public to anyone who has its URL, so that
method must not return secrets. Routes that run events, read request data, or answer per user must not
send it. The value does not depend on the request's ``Origin``, so the
response needs no ``Vary`` header.
"""

IMMUTABLE_CACHE_CONTROL = "public, max-age=31536000, immutable"
"""
The ``Cache-Control`` value for a file whose URL carries a hash of its content.

The URL changes whenever the content does, so the browser may keep the file
for a year and use it without asking the server again.
"""

REVALIDATE_CACHE_CONTROL = "no-cache"
"""
The ``Cache-Control`` value for a file served at a URL that stays the same
when its content changes, such as ``citry.js``.

The browser may keep a copy, but it must ask the server before each use. It
sends the copy's ``ETag`` back, and the server answers ``304 Not Modified``
with no body while the content is unchanged, so an upgrade reaches the
browser on its next page load and an unchanged file is not downloaded again.
"""

OWNED_ASSET_CROSSORIGIN = "anonymous"
"""
The ``crossorigin`` value Citry puts on every tag that fetches its own files.

It pairs with ``integrity``: the browser checks the digest only on a CORS
response. ``anonymous`` sends no cookies to another origin, which is all a
public file needs, and it keeps cookies on same-origin requests, so
same-origin pages still send their cookies. A preload hint and the tag it prepares must carry the
same value, or the browser downloads the file twice.
"""


@dataclass(frozen=True, slots=True)
class _OwnedResource:
    """One URL and the exact response body Citry owns at that URL."""

    url: str
    content: str | bytes
    content_type: str
    headers: tuple[tuple[str, str], ...] = ()

    @property
    def body(self) -> bytes:
        """Return the bytes sent by every Citry web adapter."""
        return self.content.encode() if isinstance(self.content, str) else self.content

    def response(self) -> RouteResponse:
        """Build the route response without changing the content representation."""
        # Every owned resource is a public JS or CSS file, and the browser
        # needs the CORS header to check the integrity Citry puts on it.
        return RouteResponse(
            content=self.content,
            content_type=self.content_type,
            headers=(*PUBLIC_ASSET_CORS_HEADERS, *self.headers),
        )

    def immutable_response(self) -> RouteResponse:
        """Build the response for a URL that carries a hash of this content."""
        return RouteResponse(
            content=self.content,
            content_type=self.content_type,
            headers=(*PUBLIC_ASSET_CORS_HEADERS, *self.headers, ("Cache-Control", IMMUTABLE_CACHE_CONTROL)),
        )

    def revalidated_response(self, request: RouteRequest | None) -> RouteResponse:
        """
        Build the response for a URL whose content can change, answering ``304`` for a current copy.

        ``request`` is ``None`` when a caller runs the handler without an
        adapter; the response is then always the full file.
        """
        etag = _etag(self.content)
        # The 304 repeats the caching headers, so the browser keeps applying
        # them to the copy it already holds.
        headers = (
            *PUBLIC_ASSET_CORS_HEADERS,
            *self.headers,
            ("Cache-Control", REVALIDATE_CACHE_CONTROL),
            ("ETag", etag),
        )
        if request is not None and _etag_matches(request.headers.get("if-none-match", ""), etag):
            return RouteResponse(content=b"", content_type=self.content_type, status=304, headers=headers)
        return RouteResponse(content=self.content, content_type=self.content_type, headers=headers)


@lru_cache(maxsize=64)
def _etag(content: str | bytes) -> str:
    """Return the tag for one file's content, kept so ``citry.js`` is not hashed again on each request."""
    body = content.encode() if isinstance(content, str) else content
    return f'"{sha256(body).hexdigest()[:32]}"'


def _etag_matches(if_none_match: str, etag: str) -> bool:
    """Return whether an ``If-None-Match`` header names ``etag``, using the weak comparison HTTP requires."""
    for candidate in if_none_match.split(","):
        tag = candidate.strip()
        # `*` matches any current file. A proxy that compresses the body
        # may mark the tag weak (`W/"..."`), which still names the same
        # content for this comparison.
        if tag == "*" or tag.removeprefix("W/") == etag:
            return True
    return False
