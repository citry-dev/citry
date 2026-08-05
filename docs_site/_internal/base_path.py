"""
Rewrite root-absolute URLs for a subpath deploy (e.g. GitHub project Pages).

The page chrome emits URLs from the site root (``/static/...``, ``/reference/...``,
``/llms.txt``), which assume the site is served at the domain root. When the site
is deployed under a subpath such as ``/citry/``, those URLs need that prefix.
This final pass rewrites the URL-bearing attributes in the built HTML and makes
sure each page carries the ``djc-base-path`` meta tag the search script reads to
prefix result links.

It does nothing when no base path is set (the default), so a root-served build is
untouched. It runs last, after every other step that writes HTML, and marks each
document after rewriting it so a second run is a no-op. Idempotence belongs to
the document, not an individual URL: an output-root path can legitimately start
with the same segment as the deployment base, such as the ``/citry/citry.js``
runtime under a ``/citry`` project-Pages deployment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.html_rewrite import (
    StartTag,
    append_attribute,
    parse_start_tags,
    rewrite_attribute_values,
    rewrite_start_tags,
)

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
    "data-fragment-url",
)
_APPLIED_ATTR = "data-djc-base-path-applied"


def apply_base_path(output_dir: Path, base: str) -> int:
    """
    Prefix root-absolute URL attributes in every ``*.html`` under ``output_dir``
    with ``base`` (e.g. ``/citry``) and make sure the base-path meta tag is set.
    Returns the number of files changed. A no-op when ``base`` is empty.
    """
    if not base:
        return 0
    if not base.startswith("/") or base == "/" or base.endswith("/"):
        raise ValueError("base path must be empty or start with / without ending in /")

    meta = f'<meta name="djc-base-path" content="{base}" {_APPLIED_ATTR}="{base}">'
    changed = 0
    for html in output_dir.rglob("*.html"):
        text = html.read_text(encoding="utf-8")
        tags = parse_start_tags(text)
        applied_base = _applied_base_path(tags)
        if applied_base is not None:
            if applied_base != base:
                raise ValueError(f"HTML was already rewritten for base path {applied_base!r}; cannot apply {base!r}")
            continue
        has_base_meta = any(_is_base_path_meta(tag) for tag in tags)

        def rewrite_tag(tag: StartTag, *, has_base_meta: bool = has_base_meta) -> str:
            rewritten = rewrite_attribute_values(
                tag.source,
                lambda name, value: _prefix_url(name, value, base),
            )
            if _is_base_path_meta(tag):
                attrs = dict(tag.attrs)
                if "content" in attrs:
                    rewritten = rewrite_attribute_values(
                        rewritten,
                        lambda name, value: base if name == "content" else value,
                    )
                else:
                    rewritten = append_attribute(rewritten, f'content="{base}"')
                if _APPLIED_ATTR not in attrs:
                    rewritten = append_attribute(rewritten, f'{_APPLIED_ATTR}="{base}"')
                return rewritten
            if tag.name == "head" and not has_base_meta:
                return rewritten + meta
            return rewritten

        new = rewrite_start_tags(text, rewrite_tag)
        if new != text:
            html.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def _prefix_url(name: str, value: str, base: str) -> str:
    if name not in _URL_ATTRS or not value.startswith("/") or value.startswith("//"):
        return value
    return f"{base}{value}"


def _is_base_path_meta(tag: StartTag) -> bool:
    attrs = dict(tag.attrs)
    return tag.name == "meta" and (attrs.get("name") or "").casefold() == "djc-base-path"


def _applied_base_path(tags: tuple[StartTag, ...]) -> str | None:
    """Return the deployment base recorded by an earlier rewrite, if present."""
    for tag in tags:
        if not _is_base_path_meta(tag):
            continue
        attrs = dict(tag.attrs)
        applied = attrs.get(_APPLIED_ATTR)
        if applied is not None:
            return applied
    return None
