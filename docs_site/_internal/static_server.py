"""
HTTP behavior shared by local previews of the assembled docs site.

Prepared Vue assets are content addressed and public.  Sandboxed preview frames
have an opaque (``null``) origin, so browsers require an explicit CORS response
header before they can load those assets while retaining their SRI checks.  Keep
the exception limited to the two generated asset namespaces; event endpoints
and ordinary site files remain same-origin-only.
"""

from __future__ import annotations

import re
from http.server import SimpleHTTPRequestHandler
from urllib.parse import urlsplit

_PREPARED_ASSET_PATH = re.compile(r"^/citry/ext/events/(?:assets/[0-9a-f]{64}\.css|definitions/[0-9a-f]{64}\.js)$")


def headers_for_static_path(path: str) -> tuple[tuple[str, str], ...]:
    """Return the minimal headers needed for a public prepared asset path."""
    if _PREPARED_ASSET_PATH.fullmatch(urlsplit(path).path):
        return (("Access-Control-Allow-Origin", "*"),)
    return ()


class StaticSiteHandler(SimpleHTTPRequestHandler):
    """Serve a built site while preserving the prepared-asset CORS contract."""

    def end_headers(self) -> None:
        for name, value in headers_for_static_path(self.path):
            self.send_header(name, value)
        super().end_headers()
