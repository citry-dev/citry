"""
External Sphinx inventories, so the API reference can link into Python's docs.

When a reference page mentions a standard-library type (``Mapping``, ``Any``,
``Path``, ...), we want the name to link to the matching page on
docs.python.org instead of rendering as plain text. Every Sphinx-built site
publishes an ``objects.inv`` file that maps each documented name to its URL;
this module downloads that file, parses it, and exposes the merged
``name -> URL`` map through :func:`external_inventory`.

The network is optional. If the inventory cannot be fetched (offline, or CI
with no outbound access) the map is simply empty and those names render
unlinked, so a build never fails because docs.python.org is unreachable. A
successful download is cached under the system temp directory so repeat builds
skip the request.

(The reverse direction, publishing citry's own inventory so other sites can
link into ours, lives in :mod:`docs_site._internal.crossrefs`.)
"""

from __future__ import annotations

import hashlib
import re
import tempfile
import urllib.request
import zlib
from functools import lru_cache
from pathlib import Path

# Pinned to one version so generated links stay stable regardless of the
# reader's own Python; bump deliberately when we move the docs to a new release.
_PYTHON_DOCS = "https://docs.python.org/3.13/"
_INVENTORIES = ((_PYTHON_DOCS + "objects.inv", _PYTHON_DOCS),)

_INV_LINE = re.compile(r"^(?P<name>.+?)\s+\S+:\S+\s+-?\d+\s+(?P<uri>\S+)\s+.*$")


def parse_objects_inv(data: bytes, base_url: str) -> dict[str, str]:
    """Parse a Sphinx v2 ``objects.inv`` payload into a ``name -> absolute URL`` map."""
    # The header is four newline-terminated plaintext lines; the rest is zlib-compressed.
    parts = data.split(b"\n", 4)
    if len(parts) < 5 or not parts[0].startswith(b"# Sphinx inventory version 2"):
        return {}
    try:
        payload = zlib.decompress(parts[4]).decode("utf-8")
    except zlib.error:
        return {}

    base = base_url.rstrip("/") + "/"
    result: dict[str, str] = {}
    for line in payload.splitlines():
        match = _INV_LINE.match(line)
        if not match:
            continue
        name = match.group("name")
        # A trailing "$" in the URI is shorthand for the object's own name.
        uri = match.group("uri").replace("$", name)
        result.setdefault(name, base + uri)
    return result


def _cache_dir() -> Path:
    path = Path(tempfile.gettempdir()) / "citry-docs-inventories"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_one(url: str, base_url: str) -> dict[str, str]:
    cache_file = _cache_dir() / (hashlib.sha256(url.encode()).hexdigest()[:16] + ".inv")
    if cache_file.is_file():
        return parse_objects_inv(cache_file.read_bytes(), base_url)
    try:
        with urllib.request.urlopen(url, timeout=15) as response:  # noqa: S310 - pinned https doc URL
            data = response.read()
    except Exception:  # noqa: BLE001 - offline-safe: any fetch failure yields {}, never a broken build
        return {}
    parsed = parse_objects_inv(data, base_url)
    # Cache only a genuine inventory, so a captive-portal or proxy error page
    # (served as HTTP 200 HTML) is not stored and replayed as an empty map on
    # every later build.
    if parsed:
        cache_file.write_bytes(data)
    return parsed


@lru_cache(maxsize=1)
def external_inventory() -> dict[str, str]:
    """Merged ``name -> URL`` map for the external Python-stdlib documentation."""
    merged: dict[str, str] = {}
    for url, base_url in _INVENTORIES:
        for name, target in _load_one(url, base_url).items():
            merged.setdefault(name, target)
    return merged
