"""Private authoritative bytes for resources served by Citry routes."""

from __future__ import annotations

from dataclasses import dataclass

from citry.util.routing import RouteResponse

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
``css_data()`` or ``js_data()`` is public to anyone who has its URL, so those
methods must not return secrets. Routes that run events, read request data, or answer per user must not
send it. The value does not depend on the request's ``Origin``, so the
response needs no ``Vary`` header.
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
