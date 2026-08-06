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
from dataclasses import dataclass
from html import escape
from typing import TYPE_CHECKING

from docs_site._internal.config_loading import (
    DocsConfigError,
    load_yaml,
    require_keys,
    require_list,
    require_mapping,
    require_str,
)

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class RedirectCatalog:
    """Validated old-to-new clean URL mappings."""

    redirects: tuple[tuple[str, str], ...]

    def as_dict(self) -> dict[str, str]:
        return dict(self.redirects)


def load_redirect_catalog(path: Path) -> RedirectCatalog:
    """Load redirects and reject cycles, chains, collisions, and unsafe URLs."""
    root = require_mapping(load_yaml(path), str(path))
    require_keys(root, str(path), required={"redirects"})
    rows = require_list(root["redirects"], "redirects")
    redirects: dict[str, str] = {}
    for index, raw in enumerate(rows):
        label = f"redirects[{index}]"
        item = require_mapping(raw, label)
        require_keys(item, label, required={"from", "to"})
        old = _clean_path(item["from"], f"{label}.from")
        new = _clean_path(item["to"], f"{label}.to")
        if old == new:
            raise DocsConfigError(f"{label} cannot redirect a path to itself")
        if old in redirects:
            raise DocsConfigError(f"redirect source is duplicated: {old}")
        redirects[old] = new
    destinations = set(redirects.values())
    chains = set(redirects).intersection(destinations)
    if chains:
        raise DocsConfigError(
            "redirect destinations may not themselves redirect; collapse chain(s): " + ", ".join(sorted(chains))
        )
    return RedirectCatalog(redirects=tuple(redirects.items()))


def _clean_path(value: object, label: str) -> str:
    path = require_str(value, label)
    if not path.startswith("/") or not path.endswith("/") or "//" in path:
        raise DocsConfigError(f"{label} must have one leading and one trailing slash")
    unsafe = any(
        char.isspace() or ord(char) < 32 or ord(char) == 127 or char in {'"', "'", "%", ":", "<", ">", "\\"}
        for char in path
    )
    if unsafe or any(part in {".", ".."} for part in path.split("/")) or "?" in path or "#" in path:
        raise DocsConfigError(f"{label} must be a safe clean URL without query or fragment")
    return path


def validate_redirect_routes(
    catalog: RedirectCatalog,
    current_paths: set[str],
    *,
    occupied_paths: set[str] | None = None,
) -> None:
    """Require old routes to be vacant and destinations to be published routes."""
    normalized = {f"/{path.strip('/')}/" if path.strip("/") else "/" for path in current_paths}
    occupied = {f"/{path.strip('/')}/" if path.strip("/") else "/" for path in (occupied_paths or current_paths)}
    for old, new in catalog.redirects:
        if old in occupied:
            raise DocsConfigError(f"redirect source collides with a current page: {old}")
        if new not in normalized:
            raise DocsConfigError(f"redirect destination is not in current navigation: {new}")


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


def emit_redirects(output_dir: Path, *, site_url: str, redirects: dict[str, str]) -> int:
    """Write a redirect stub for every explicitly supplied mapping."""
    site_url = site_url.rstrip("/")
    for old, new in redirects.items():
        stub = output_dir / old.strip("/") / "index.html"
        stub.parent.mkdir(parents=True, exist_ok=True)
        # A relative href from the stub's directory to the target keeps working
        # under a subpath deploy; the canonical is absolute.
        target_dir = output_dir / new.strip("/")
        href = os.path.relpath(target_dir, stub.parent).replace(os.sep, "/") + "/"
        stub.write_text(
            _TEMPLATE.format(
                canonical=escape(f"{site_url}{new}", quote=True),
                href=escape(href, quote=True),
                href_json=json.dumps(href),
            ),
            encoding="utf-8",
        )
    return len(redirects)
