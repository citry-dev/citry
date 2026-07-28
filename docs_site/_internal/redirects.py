"""
Redirect stubs for pages that have moved.

When a page's URL changes, a link or bookmark to the old address should still
land the visitor on the new page. For each moved URL this writes a tiny HTML
page at the old path that forwards to the new one three ways at once: a
``<meta http-equiv="refresh">`` (works without JavaScript, for crawlers and
assistive tools), a ``location.replace()`` script (faster in a browser, and it
replaces history so the back button skips the dead URL), and a
``<link rel="canonical">`` plus ``noindex`` so search engines treat the new URL
as the real one and keep the stub itself out of results.

The forwarding href is written relative to the stub, so it keeps working when
the site is deployed under a subpath; the canonical stays absolute.

The map stays empty until a published URL moves or merges. Add the old and new
clean paths together when that happens.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# Old clean URL path -> new clean URL path (each with a leading and trailing
# slash).
REDIRECTS: dict[str, str] = {}

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Redirecting...</title>
<link rel="canonical" href="{canonical}">
<meta http-equiv="refresh" content="0; url={href}">
<meta name="robots" content="noindex,follow">
</head>
<body>
<p>This page has moved. <a href="{href}">Continue to the new page</a>.</p>
<script>window.location.replace({href_json});</script>
</body>
</html>
"""


def emit_redirects(output_dir: Path, *, site_url: str, redirects: dict[str, str] | None = None) -> int:
    """Write a redirect stub for every entry in ``redirects`` (defaults to ``REDIRECTS``). Returns the count."""
    redirects = REDIRECTS if redirects is None else redirects
    site_url = site_url.rstrip("/")
    for old, new in redirects.items():
        stub = output_dir / old.strip("/") / "index.html"
        stub.parent.mkdir(parents=True, exist_ok=True)
        # A relative href from the stub's directory to the target keeps working
        # under a subpath deploy; the canonical is absolute.
        target_dir = output_dir / new.strip("/")
        href = os.path.relpath(target_dir, stub.parent).replace(os.sep, "/") + "/"
        stub.write_text(
            _TEMPLATE.format(canonical=f"{site_url}{new}", href=href, href_json=json.dumps(href)),
            encoding="utf-8",
        )
    return len(redirects)
