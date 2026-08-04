"""
Release-notes generator: CHANGELOG.md -> a "/releases/" index plus one page
per version.

The repo-root CHANGELOG.md is the single source of truth. This splits it into
one section per ``## version`` heading and, at build time, renders each as its
own page (``/releases/<slug>/``) with an index that links them newest-first,
mirroring how the django-components docs present release notes. citry will
accumulate many versions, so per-version pages (not one long page) keep each
release addressable and the index scannable.

Adapted from the django-components docs generator
(``apps/docs/build/release_notes.py``); the mkdocs staging-file machinery is
dropped because citry's builder renders generated pages directly (see
``build._build_releases`` and ``serve``), the same way the API reference does.

Release bodies routinely *show* citry template syntax (for example ``<c-raw>``
or ``{{ ... }}``). These pages are rendered with the citry template pass turned
off (``render_page(..., run_citry_pass=False)``) so that syntax is not executed.
As with every docs page, code and tags in the changelog belong in backticks (the
project's changelog convention); backticked spans render as literal code, while
the markdown pass escapes stray angle brackets on its own.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from docs_site._internal.nav import NavItem

if TYPE_CHECKING:
    from collections.abc import Collection

# A version section begins at a "## ..." heading (at the start of a line).
_SECTION_HEAD = re.compile(r"^##\s+")

# A release may carry its date as an italic line in the body, e.g. "_30 Jun 2026_"
# or "_30 June 2026_" or ISO "_2026-06-30_"; all render as ISO in the title. The
# month is matched loosely (any letters) and validated by strptime, so a phrase
# that merely looks like a date but is not one is left in the body untouched
# rather than aborting the build.
_DATE_PATTERNS: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...] = (
    (re.compile(r"_(\d{1,2}\s+[A-Za-z]+\s+\d{4})_"), ("%d %b %Y", "%d %B %Y")),
    (re.compile(r"_(\d{4}-\d{2}-\d{2})_"), ("%Y-%m-%d",)),
)

_HEADING = re.compile(r"^(#{1,6})(\s.*)$")
_FENCE = re.compile(r"^\s*(```+|~~~+)")


@dataclass(frozen=True)
class Release:
    """One version's release notes."""

    slug: str  # URL-safe version, e.g. "v0.2.0", "unreleased"
    title: str  # display title / page H1, e.g. "v0.1.0 (2026-06-30)"
    body: str  # markdown body, without the "## version" heading line


def _split_sections(text: str) -> list[str]:
    """
    Split changelog text into one chunk per ``## version`` section.

    A ``## `` line only starts a new section when it is not inside a fenced code
    block, so a release body that shows markdown with its own ``## `` headings is
    not torn apart. The text before the first version heading (the title and any
    preamble) is dropped.
    """
    sections: list[str] = []
    current: list[str] | None = None
    in_fence = False
    fence_char = ""
    for line in text.split("\n"):
        fence = _FENCE.match(line)
        if fence:
            char = fence.group(1)[0]
            if not in_fence:
                in_fence, fence_char = True, char
            elif char == fence_char:
                in_fence = False
        elif not in_fence and _SECTION_HEAD.match(line):
            if current is not None:
                sections.append("\n".join(current))
            current = [line]
            continue
        if current is not None:
            current.append(line)
    if current is not None:
        sections.append("\n".join(current))
    return sections


def _body_headings(lines: list[str]) -> list[tuple[int, int]]:
    """(line index, heading level) for each ATX heading not inside a fenced block."""
    headings: list[tuple[int, int]] = []
    in_fence = False
    fence_char = ""
    for i, line in enumerate(lines):
        fence = _FENCE.match(line)
        if fence:
            char = fence.group(1)[0]
            if not in_fence:
                in_fence, fence_char = True, char
            elif char == fence_char:
                in_fence = False
            continue
        if in_fence:
            continue
        heading = _HEADING.match(line)
        if heading:
            headings.append((i, len(heading.group(1))))
    return headings


def _promote_body_headings(body: str) -> str:
    """
    Shift a release body's headings so its shallowest sits at H2 (under the page H1).

    A version's notes come from CHANGELOG.md as ``### Feat`` etc. under a
    ``## version`` heading. On its own page the version becomes the H1, so the
    body headings are re-levelled to start at H2: a shallowest of H3 is promoted
    up, and a stray H1 in a body is demoted down, so the page never skips or
    repeats a level. Relative depth is preserved and levels are clamped to
    H1-H6. Headings inside code fences are left alone.
    """
    lines = body.split("\n")
    headings = _body_headings(lines)
    if not headings:
        return body
    shift = min(level for _, level in headings) - 2
    if shift == 0:
        return body
    for i, level in headings:
        rest = _HEADING.match(lines[i]).group(2)  # type: ignore[union-attr]
        new_level = max(1, min(6, level - shift))
        lines[i] = "#" * new_level + rest
    return "\n".join(lines)


def _slugify(heading: str) -> str:
    """A clean, URL-safe slug from a version heading (e.g. 'v0.2.0', 'unreleased')."""
    slug = re.sub(r"[^a-z0-9.]+", "-", heading.lower()).strip("-")
    return slug or "release"


def _try_parse_date(raw: str, formats: tuple[str, ...]) -> datetime | None:
    """Parse ``raw`` with the first matching format, or None if none apply."""
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)  # noqa: DTZ007 - date only, no tz in source
        except ValueError:
            continue
    return None


def parse_changelog(text: str, *, exclude: Collection[str] | None = None) -> list[Release]:
    """
    Split CHANGELOG.md text into one :class:`Release` per ``## version`` section.

    Sections are returned in file order (newest-first, as the changelog is
    written). Slugs are made unique so two headings that normalize to the same
    string still get distinct pages. Headings in ``exclude`` (defaulting to
    ``settings.yml``) are dropped entirely: no page, index entry, or
    sidebar item - so a version can be hidden from the docs without touching the
    changelog.
    """
    if exclude is None:
        from docs_site._internal.project import current_docs_project  # noqa: PLC0415

        exclude = current_docs_project().settings.excluded_releases
    releases: list[Release] = []
    seen_slugs: dict[str, int] = {}
    for chunk in _split_sections(text):
        stripped = chunk.strip()
        if not stripped:
            continue
        header_line, _, body = stripped.partition("\n")
        body = body.strip()
        heading = header_line.removeprefix("##").strip()
        if heading in exclude:
            continue

        # Pull a valid release date out of the body and into the title, if present.
        title = heading
        for pattern, formats in _DATE_PATTERNS:
            match = pattern.search(body)
            if match:
                parsed = _try_parse_date(match.group(1), formats)
                if parsed is not None:
                    body = body.replace(match.group(0), "").strip()
                    title = f"{heading} ({parsed:%Y-%m-%d})"
                break

        # Unique slug: a second heading that normalizes to an existing slug gets
        # a numeric suffix so it does not overwrite the first release's page.
        slug = _slugify(heading)
        seen_slugs[slug] = seen_slugs.get(slug, 0) + 1
        if seen_slugs[slug] > 1:
            slug = f"{slug}-{seen_slugs[slug]}"

        releases.append(Release(slug=slug, title=title, body=body))

    return releases


def release_page_markdown(release: Release) -> str:
    """The full source for one version's page: front matter, the title H1, then the body."""
    body = _promote_body_headings(release.body)
    return (
        "---\n"
        f"title: {release.title}\n"
        f"description: What changed in citry {release.title}.\n"
        "---\n\n"
        f"# {release.title}\n\n"
        f"{body}\n"
    )


def release_index_markdown(releases: list[Release]) -> str:
    """The source for the ``/releases/`` index: a newest-first list of version links."""
    lines = [
        "---",
        "title: Release notes",
        "description: Release notes for every version of citry, newest first.",
        "---",
        "",
        "# Release notes",
        "",
        "What changed in each version of citry, newest first. Pick a version for its full notes.",
        "",
    ]
    # Relative clean URLs: "v0.2.0/" resolves under /releases/ to /releases/v0.2.0/.
    lines.extend(f"- [{release.title}]({release.slug}/)" for release in releases)
    return "\n".join(lines) + "\n"


def releases_nav_items(releases: list[Release]) -> list[NavItem]:
    """The pages supplied by ``source: releases`` in navigation."""
    items = [NavItem(title="Overview", path="/releases/")]
    items.extend(
        NavItem(
            title=release.title,
            path=f"/releases/{release.slug}/",
        )
        for release in releases
    )
    return items
