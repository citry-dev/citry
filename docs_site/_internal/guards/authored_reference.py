"""Check declared non-Python APIs against their authored Reference pages."""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.project import current_docs_project

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

_ANCHOR_RE = re.compile(
    r"<h[2-6]\b[^>]*\bid=[\"'](?P<anchor>[a-z0-9-]+)[\"'][^>]*>",
)


def _line(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    """Require one stable heading anchor for each declared authored API."""
    seen_keys: dict[str, str] = {}
    project = ctx.project or current_docs_project()
    for cat in project.reference.categories:
        for entry in cat.entries:
            for key in (entry.key, *entry.aliases):
                previous = seen_keys.get(key)
                if previous is not None:
                    yield GuardResult.error(
                        guard="authored_reference",
                        message=(f"Reference key {key!r} belongs to both {previous!r} and {cat.slug!r}."),
                        source="reference.yml",
                    )
                else:
                    seen_keys[key] = cat.slug

        if cat.source != "authored":
            continue

        path = ctx.content_dir / "reference" / f"{cat.slug}.md"
        if not path.is_file():
            yield GuardResult.error(
                guard="authored_reference",
                message=f"The authored {cat.title} Reference page is missing.",
                source=str(path),
            )
            continue

        source = path.read_text(encoding="utf-8")
        anchors = [(match.group("anchor"), match.start()) for match in _ANCHOR_RE.finditer(source)]
        counts = Counter(anchor for anchor, _offset in anchors)
        declared = Counter(entry.anchor for entry in cat.entries)
        expected = set(declared)

        for anchor, count in declared.items():
            if count == 1:
                continue
            yield GuardResult.error(
                guard="authored_reference",
                message=(f"Reference category {cat.slug!r} declares anchor #{anchor} {count} times."),
                source="reference.yml",
            )

        for entry in cat.entries:
            count = counts[entry.anchor]
            if count != 1:
                yield GuardResult.error(
                    guard="authored_reference",
                    message=(f"Expected one heading anchor #{entry.anchor} for {entry.key}; found {count}."),
                    source=str(path),
                )

        for anchor, offset in anchors:
            if anchor in expected:
                continue
            yield GuardResult.error(
                guard="authored_reference",
                message=f"Unexpected authored Reference anchor: #{anchor}.",
                source=str(path),
                line=_line(source, offset),
            )
