"""
Fail when a committed docs version loads a ``/static/`` file that is gone.

A version under ``docs_site/versions/<version>/`` has no static files of its
own. Its pages load images, stylesheets, and scripts from the root site's
``/static/`` folder, which is built from ``docs_site/static/``. Sharing CSS and
JavaScript is on purpose: a style fix reaches every old version. The cost is
that deleting or renaming a file under ``docs_site/static/`` breaks every old
version that still loads it, and nothing else in the build notices, because
the current pages do not mention the file.

This guard reads the ``src``, ``href``, and ``srcset`` attributes of every page
in each built version and fails on a ``/static/...`` path that has no file in
``docs_site/static/``. It parses the HTML, so a path that a code example only
shows as text never counts. A relative path that resolves into ``/static/``
is checked too. A path that only a script, a Vue or Alpine expression, or a
full ``https://`` URL names is not checked. The guard checks that each file
exists, so it cannot tell when a file was changed in place.

Runs only when ``ctx.versions_dir`` is set.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import unquote, urljoin, urlsplit

import lxml.html  # type: ignore[import-untyped]
from lxml.etree import LxmlError  # type: ignore[import-untyped]

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.site_index import strip_base_path
from docs_site._internal.versioning import BUILD_INFO_NAME

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

_STATIC_PREFIX = "/static/"

# The deploy mounts each version below this prefix, so a relative path in a
# snapshot page resolves against it the same way the browser resolves it.
_VERSION_MOUNT = "/v/"

# The attributes that make a browser fetch, or link to, a file. The XPath
# expression keeps only values that could reach /static/, so the many links
# to other pages skip the slower Python checks below.
_SRCSET_ATTRIBUTE = "srcset"
_STATIC_URL_ATTRIBUTES = "//@*[(name()='src' or name()='href' or name()='srcset') and contains(., 'static/')]"

# Files a demo loads while missing on purpose, so the page can show what
# happens when the file fails to load.
_MISSING_ON_PURPOSE = frozenset(
    {
        # The Citry UI image demo of a placeholder and an error state
        # (cimage/snippets/placeholder_and_error.py) points a native <img> at
        # this path so the browser's broken-image handling is visible.
        "/static/img/ui/image/missing-native-observation.jpg",
    }
)


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    root = ctx.versions_dir
    if root is None or not root.is_dir():
        return
    # Each page loads mostly the same few files, so look each one up once.
    present: dict[str, bool] = {}
    # Only built versions carry a stamp; alias dirs such as latest/ hold
    # redirect stubs that point inside the tree.
    for version_dir in sorted(d for d in root.iterdir() if d.is_dir() and (d / BUILD_INFO_NAME).is_file()):
        for page in sorted(version_dir.rglob("*.html")):
            # The parser reads the page's own charset declaration from the bytes.
            data = page.read_bytes()
            # A page that never mentions static/ cannot load a static file.
            if b"static/" not in data:
                continue
            rel_page = page.relative_to(root).as_posix()
            for line, path in _missing_static_paths(data, rel_page, ctx, present):
                yield GuardResult.error(
                    guard="snapshot_static_files",
                    message=(
                        f"loads {path}, which is missing from docs_site/static/; restore the file "
                        "under this name. To change what it shows, save the changed file under a new name"
                    ),
                    source=rel_page,
                    line=line,
                )


def _missing_static_paths(
    data: bytes, rel_page: str, ctx: GuardContext, present: dict[str, bool]
) -> list[tuple[int, str]]:
    """Return ``(line, path)`` for each distinct ``/static/`` path on the page with no file."""
    # The page's own URL, which a relative path is resolved against.
    page_url = _VERSION_MOUNT + rel_page
    missing: list[tuple[int, str]] = []
    reported: set[str] = set()
    for line, url in _page_urls(data):
        path = _static_path(url, page_url, ctx.base_path)
        if path is None or path in reported or path in _MISSING_ON_PURPOSE:
            continue
        if path not in present:
            present[path] = (ctx.static_dir / path.removeprefix(_STATIC_PREFIX)).is_file()
        if not present[path]:
            # One report per path is enough for the reader to fix the page.
            reported.add(path)
            missing.append((line, path))
    return missing


def _static_path(url: str, page_url: str, base_path: str) -> str | None:
    """Return the ``/static/...`` file path a URL loads, or None for any other URL."""
    parts = urlsplit(url)
    # Another site, a data: URI, or a mailto: link is not a file of this site.
    if parts.scheme or parts.netloc:
        return None
    # Keep only the path: the query string and fragment do not name a
    # different file, and the deploy's base path is not part of the path on disk.
    path = strip_base_path(parts.path, base_path)
    if not path:
        return None
    # Resolve a relative path, and any ./ or ../ step, the way the browser does.
    path = urljoin(page_url, path)
    # urljoin drops the leading slash when ../ steps go above the site root,
    # where a browser stays at the root.
    if not path.startswith("/"):
        path = "/" + path
    if not path.startswith(_STATIC_PREFIX):
        return None
    # The file name on disk is the decoded form, as the server reads it.
    return unquote(path)


def _srcset_urls(value: str) -> list[str]:
    """
    Split a ``srcset`` value into its URLs.

    Each candidate is a URL, then optional descriptors such as ``2x`` or
    ``640w``, and a comma ends it. A comma inside a URL is allowed, so this
    reads each URL up to the next whitespace, as the HTML standard does, and
    only a comma after the URL ends the candidate.
    """
    urls: list[str] = []
    position, end = 0, len(value)
    while position < end:
        # Whitespace and commas before a URL separate candidates.
        while position < end and (value[position].isspace() or value[position] == ","):
            position += 1
        start = position
        while position < end and not value[position].isspace():
            position += 1
        url = value[start:position]
        if url.endswith(","):
            # A comma right after the URL ends the candidate, with no descriptors.
            url = url.rstrip(",")
        else:
            # Skip the descriptors up to the comma that ends the candidate; a
            # comma inside parentheses belongs to the descriptor.
            depth = 0
            while position < end and (value[position] != "," or depth):
                if value[position] == "(":
                    depth += 1
                elif value[position] == ")":
                    depth = max(depth - 1, 0)
                position += 1
        if url:
            urls.append(url)
    return urls


def _page_urls(data: bytes) -> list[tuple[int, str]]:
    """
    Return each ``(line, url)`` that a ``src``, ``href``, or ``srcset`` attribute names.

    Only values that mention ``static/`` are returned.

    The HTML parser reads only real attributes, quoted or not. A code example
    shows its markup as escaped text, so a path inside it is never collected.
    """
    try:
        dom = lxml.html.document_fromstring(data)
    except LxmlError:
        # Only a page with no markup at all fails to parse, and it loads nothing.
        return []
    urls: list[tuple[int, str]] = []
    for value in dom.xpath(_STATIC_URL_ATTRIBUTES):
        line = value.getparent().sourceline or 0
        if value.attrname == _SRCSET_ATTRIBUTE:
            urls.extend((line, url) for url in _srcset_urls(value))
        else:
            urls.append((line, value.strip()))
    return urls
