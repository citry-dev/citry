"""Validate the Community package catalog and its two page projections."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import yaml

from docs_site._internal.community_packages import (
    CommunityPackageCatalogError,
    load_community_package_catalog,
)
from docs_site._internal.guards.base import GuardResult
from docs_site._internal.nav import SCOPE_SITE, load_nav

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext


_PAGE_CATEGORIES = {
    "community/extensions.md": "extension",
    "community/ui-libraries.md": "ui_library",
}
_DIRECTIVE_RE = re.compile(r"<c-community-packages\s+category=[\"'](?P<category>[^\"']+)[\"']\s*/>")
_HTML_COMMENT_RE = re.compile(r"<!--.*?(?:-->|$)", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"(?P<ticks>`+).*?(?P=ticks)", re.DOTALL)


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    """Report invalid catalog data and mismatched page directives."""
    present_pages = {
        relative: category for relative, category in _PAGE_CATEGORIES.items() if (ctx.content_dir / relative).is_file()
    }
    if not present_pages:
        return

    catalog_path = (
        ctx.project.runtime.community_packages_data
        if ctx.project is not None
        else ctx.content_dir.parent / "data" / "community_packages.yml"
    )
    try:
        load_community_package_catalog(catalog_path)
    except CommunityPackageCatalogError as exc:
        try:
            source = exc.source.resolve().relative_to(ctx.content_dir.parent.resolve()).as_posix()
        except ValueError:
            source = str(exc.source)
        yield GuardResult.error(
            guard="community_packages",
            message=exc.message,
            source=source,
            line=exc.line,
        )
        return

    if ctx.nav_path.is_file():
        try:
            nav_tree = load_nav(ctx.nav_path)
        except (OSError, TypeError, ValueError, yaml.YAMLError):
            # The navigation guard reports malformed navigation with its own
            # source context. Avoid a derivative finding here.
            nav_tree = None
        if nav_tree is not None:
            wrong_scope = [
                f"/{relative.removesuffix('.md')}/"
                for relative in _PAGE_CATEGORIES
                if nav_tree.scope_for_url(f"/{relative.removesuffix('.md')}/") != SCOPE_SITE
            ]
            if wrong_scope:
                yield GuardResult.error(
                    guard="community_packages",
                    message=("Community package pages must remain site-scoped: " + ", ".join(wrong_scope)),
                    source=ctx.nav_path.name,
                )

    for relative, category in present_pages.items():
        page = ctx.content_dir / relative
        source = page.read_text(encoding="utf-8")
        visible_source = _without_markdown_code(source)
        matches = list(_DIRECTIVE_RE.finditer(visible_source))
        matching = [match for match in matches if match.group("category") == category]
        if len(matches) == 1 and len(matching) == 1:
            continue
        line = source.count("\n", 0, matches[0].start()) + 1 if matches else 1
        yield GuardResult.error(
            guard="community_packages",
            message=(f"Page must contain exactly one Community package directive for category {category!r}"),
            source=relative,
            line=line,
        )


def _without_markdown_code(source: str) -> str:
    """Mask code and comments while preserving source offsets and line numbers."""
    lines: list[str] = []
    fence_character = ""
    fence_length = 0
    for line in source.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        opening = re.match(r"^ {0,3}(?P<marker>`{3,}|~{3,})", content)
        if fence_character:
            lines.append(_mask_non_newline(line))
            if re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
                content,
            ):
                fence_character = ""
                fence_length = 0
            continue
        if opening is not None:
            marker = opening.group("marker")
            fence_character = marker[0]
            fence_length = len(marker)
            lines.append(_mask_non_newline(line))
            continue
        if content.startswith(("    ", "\t")):
            lines.append(_mask_non_newline(line))
            continue
        lines.append(line)

    visible = "".join(lines)
    visible = _HTML_COMMENT_RE.sub(lambda match: _mask_non_newline(match.group()), visible)
    return _INLINE_CODE_RE.sub(lambda match: _mask_non_newline(match.group()), visible)


def _mask_non_newline(value: str) -> str:
    return "".join(character if character in "\r\n" else " " for character in value)
