"""
Check that every JSON-LD block on a page is valid and complete.

The pages emit ``<script type="application/ld+json">`` blocks (a BreadcrumbList
on every page, a TechArticle on content pages). Each must be well-formed JSON
and carry the fields search engines need for rich results: malformed JSON-LD
silently drops the page from rich-result eligibility, so a broken block is an
error and a missing recommended field is a warning. This checks structure
(parses, ``@context`` / ``@type`` present, the per-type required keys) without a
full schema.org validator.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Required keys per @type. Absence is a warning (the block still parses, but the
# rich result is weaker or ineligible).
REQUIRED_KEYS: dict[str, tuple[str, ...]] = {
    "BreadcrumbList": ("itemListElement",),
    "BlogPosting": (
        "headline",
        "description",
        "datePublished",
        "dateModified",
        "author",
        "publisher",
        "mainEntityOfPage",
        "url",
        "image",
    ),
    "TechArticle": ("headline",),
}


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    index = ctx.site_index
    if index is None:
        return

    for page in index.pages:
        if not page.is_doc_page or page.is_redirect_stub:
            continue
        types: list[str] = []
        for block in page.jsonld_blocks:
            yield from _check_block(block, source=page.label)
            try:
                parsed = json.loads(block)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(parsed, dict) and isinstance(parsed.get("@type"), str):
                types.append(parsed["@type"])

        if page.url.startswith("/blog/") and page.url != "/blog/":
            posting_count = types.count("BlogPosting")
            if posting_count != 1:
                yield GuardResult.error(
                    guard="json_ld",
                    message=f"Blog post must emit exactly one BlogPosting block (found {posting_count})",
                    source=page.label,
                )
            if "TechArticle" in types:
                yield GuardResult.error(
                    guard="json_ld",
                    message="Blog post must not emit TechArticle structured data",
                    source=page.label,
                )


def _check_block(block: str, *, source: str) -> Iterator[GuardResult]:
    try:
        data = json.loads(block)
    except (json.JSONDecodeError, ValueError) as e:
        yield GuardResult.error(guard="json_ld", message=f"Malformed JSON-LD block: {e}", source=source)
        return

    if not isinstance(data, dict):
        yield GuardResult.error(
            guard="json_ld",
            message=f"JSON-LD block is not an object (got {type(data).__name__})",
            source=source,
        )
        return

    if data.get("@context") != "https://schema.org":
        yield GuardResult.warning(
            guard="json_ld",
            message=f"JSON-LD @context is not https://schema.org (got {data.get('@context')!r})",
            source=source,
        )

    type_name = data.get("@type")
    if not type_name:
        yield GuardResult.error(guard="json_ld", message="JSON-LD block is missing @type", source=source)
        return

    for key in REQUIRED_KEYS.get(type_name, ()):
        if not data.get(key):
            yield GuardResult.warning(
                guard="json_ld",
                message=f"{type_name} JSON-LD is missing recommended field {key!r}",
                source=source,
            )

    if type_name == "BreadcrumbList":
        yield from _check_breadcrumb_items(data.get("itemListElement"), source=source)


def _check_breadcrumb_items(value: object, *, source: str) -> Iterator[GuardResult]:
    if not isinstance(value, list):
        yield GuardResult.error(
            guard="json_ld",
            message="BreadcrumbList itemListElement must be a list",
            source=source,
        )
        return

    if len(value) < 2:
        yield GuardResult.error(
            guard="json_ld",
            message="BreadcrumbList must contain at least two items",
            source=source,
        )

    last = len(value) - 1
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            yield GuardResult.error(
                guard="json_ld",
                message=f"Breadcrumb item {index} is not an object",
                source=source,
            )
            continue
        required = ("position", "name") if index - 1 == last else ("position", "name", "item")
        for key in required:
            if item.get(key) in (None, ""):
                yield GuardResult.error(
                    guard="json_ld",
                    message=f"Breadcrumb item {index} is missing required field {key!r}",
                    source=source,
                )
        position = item.get("position")
        if position not in (None, "") and (type(position) is not int or position != index):
            yield GuardResult.error(
                guard="json_ld",
                message=f"Breadcrumb item {index} has position {position!r}; expected {index}",
                source=source,
            )
