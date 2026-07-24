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
    "TechArticle": ("headline",),
}


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    index = ctx.site_index
    if index is None:
        return

    for page in index.pages:
        if not page.is_doc_page or page.is_redirect_stub:
            continue
        for block in page.jsonld_blocks:
            yield from _check_block(block, source=page.label)


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
