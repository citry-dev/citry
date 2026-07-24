"""
Rewrite root-absolute URLs for a subpath deploy (e.g. GitHub project Pages).

The page chrome emits URLs from the site root (``/static/...``, ``/reference/...``,
``/llms.txt``), which assume the site is served at the domain root. When the site
is deployed under a subpath such as ``/citry/``, those URLs need that prefix.
This final pass rewrites the URL-bearing attributes in the built HTML and makes
sure each page carries the ``djc-base-path`` meta tag the search script reads to
prefix result links.

It does nothing when no base path is set (the default), so a root-served build is
untouched. It runs last, after every other step that writes HTML, and is safe to
run twice: a value already under the base path is left alone.

Note: the build serves Citry's runtime under the ``/citry`` mount prefix. If the
deploy base path is also ``/citry`` (a project-Pages repo named "citry"), the
already-under-base guard skips the runtime URL, which is correct only for the
chrome URLs. Pages with component JavaScript would need the runtime prefix and
the base path kept distinct; the shipped pages have no component JavaScript, so
this does not bite yet.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# URL-bearing attributes whose root-absolute values move under the base path.
_URL_ATTRS = (
    "href",
    "src",
    "action",
    "formaction",
    "poster",
    "data-pagefind-path",
)


def _compile(base: str) -> re.Pattern[str]:
    # Matches `attr=/x` or `attr="/x"` / `attr='/x'`, but NOT `//host`
    # (protocol-relative), NOT a full URL (those start with a scheme, not `/`),
    # and NOT a value already under the base path (the re-run guard).
    already = re.escape(base.lstrip("/"))
    attrs = "|".join(_URL_ATTRS)
    return re.compile(rf'(\b(?:{attrs})=)(["\']?)/(?!/)(?!{already}/)')


def apply_base_path(output_dir: Path, base: str) -> int:
    """
    Prefix root-absolute URL attributes in every ``*.html`` under ``output_dir``
    with ``base`` (e.g. ``/citry``) and make sure the base-path meta tag is set.
    Returns the number of files changed. A no-op when ``base`` is empty.
    """
    if not base:
        return 0

    pattern = _compile(base)
    replacement = rf"\1\2{base}/"
    meta = f'<head><meta name="djc-base-path" content="{base}">'
    changed = 0
    for html in output_dir.rglob("*.html"):
        text = html.read_text(encoding="utf-8")
        new = pattern.sub(replacement, text)
        # So base-path-aware JS (the search result links) can read the prefix.
        if "djc-base-path" not in new:
            new = new.replace("<head>", meta, 1)
        if new != text:
            html.write_text(new, encoding="utf-8")
            changed += 1
    return changed
