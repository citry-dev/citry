"""Private authoritative bytes for resources served by Citry routes."""

from __future__ import annotations

from dataclasses import dataclass
from email.message import Message
from functools import cache

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
``css_data()`` is public to anyone who has its URL, so that
method must not return secrets. Routes that run events, read request data, or answer per user must not
send it. The value does not depend on the request's ``Origin``, so the
response needs no ``Vary`` header.
"""

JAVASCRIPT_CONTENT_TYPE = "text/javascript; charset=utf-8"
CSS_CONTENT_TYPE = "text/css; charset=utf-8"
r"""
The ``Content-Type`` of every JavaScript and CSS file Citry serves.

Citry sends these files as UTF-8. With no charset in the header, the browser
decodes the file with the encoding of the page that links it. On a page in
GBK or Big5, the browser reads the backslash in ``\"`` inside a ``css_data()``
string as the second byte of a two-byte character, so the quote after it ends
the string.
"""

_JAVASCRIPT_MEDIA_TYPES = frozenset(
    {"application/javascript", "application/x-javascript", "application/ecmascript", "application/x-ecmascript"}
)


@cache
def _lacks_utf8_charset(content_type: str) -> bool:
    """Whether ``content_type`` names a text or JavaScript file without saying ``charset=utf-8``."""
    # The standard library reads the parameters the way a browser does: a quoted value
    # that holds "charset=utf-8" or a parameter named "x-charset" does not count.
    header = Message()
    header["Content-Type"] = content_type
    media_type = header.get_content_type()
    if not (media_type.startswith("text/") or media_type in _JAVASCRIPT_MEDIA_TYPES):
        return False
    return header.get_content_charset() != "utf-8"


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

    def __post_init__(self) -> None:
        # A string body is sent as UTF-8. A text or JavaScript type that does not say so
        # leaves the browser to decode the file with the linking page's encoding. Citry builds
        # every script and stylesheet it serves through this class, so a route that forgets
        # the charset fails in the tests instead of shipping.
        if _lacks_utf8_charset(self.content_type):
            msg = (
                f"The content type {self.content_type!r} of a served text or JavaScript file does not say "
                "charset=utf-8, so the browser would decode the file with the encoding of the page that "
                "links it. Add '; charset=utf-8'."
            )
            raise ValueError(msg)

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
