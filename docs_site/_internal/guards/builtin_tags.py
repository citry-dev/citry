"""Check the authored Built-in tags page against Citry's reserved tags."""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING

from citry.component_registry import (
    BUILTIN_COMPONENT_NAMES,
    STRUCTURAL_TAG_NAMES,
)
from docs_site._internal.guards.base import GuardResult
from docs_site._internal.reference import extract_builtin
from docs_site._internal.reference_pages import category

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

_DIRECTIVE_RE = re.compile(r"<c-builtin\b(?P<attrs>[^>]*)/?>")
_TAG_ATTR_RE = re.compile(r"""\btag=["'](?P<tag>[^"']+)["']""")
_ANCHOR_RE = re.compile(r"""<h[2-6]\s+id=["']c-(?P<tag>[a-z0-9-]+)["']>""")


def _line(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    """Require one documented, stable anchor for every public built-in tag."""
    path = ctx.content_dir / "reference" / "builtins.md"
    if not path.is_file():
        yield GuardResult.error(
            guard="builtin_tags",
            message="The authored Built-in tags reference page is missing.",
            source=str(path),
        )
        return

    source = path.read_text(encoding="utf-8")
    directives: list[tuple[str, int]] = []
    for match in _DIRECTIVE_RE.finditer(source):
        tag_match = _TAG_ATTR_RE.search(match.group("attrs"))
        if tag_match is not None:
            directives.append((tag_match.group("tag"), match.start()))

    anchors = [(match.group("tag"), match.start()) for match in _ANCHOR_RE.finditer(source)]
    runtime_counts = Counter(tag for tag, _offset in directives)
    structural_counts = Counter(tag for tag, _offset in anchors)

    for tag in sorted(BUILTIN_COMPONENT_NAMES):
        count = runtime_counts[tag]
        if count != 1:
            yield GuardResult.error(
                guard="builtin_tags",
                message=(f"Expected one <c-builtin> entry for <c-{tag}>; found {count}."),
                source=str(path),
            )
        data = extract_builtin(tag)
        if data is None or data.anchor != f"c-{tag}":
            yield GuardResult.error(
                guard="builtin_tags",
                message=f"Built-in <c-{tag}> does not resolve to anchor #c-{tag}.",
                source=str(path),
            )

    for tag in sorted(STRUCTURAL_TAG_NAMES):
        count = structural_counts[tag]
        if count != 1:
            yield GuardResult.error(
                guard="builtin_tags",
                message=(f"Expected one explicit #c-{tag} heading anchor; found {count}."),
                source=str(path),
            )

    for tag, offset in directives:
        if tag not in BUILTIN_COMPONENT_NAMES:
            yield GuardResult.error(
                guard="builtin_tags",
                message=f"Unexpected runtime built-in entry: <c-{tag}>.",
                source=str(path),
                line=_line(source, offset),
            )

    for tag, offset in anchors:
        if tag not in STRUCTURAL_TAG_NAMES:
            yield GuardResult.error(
                guard="builtin_tags",
                message=f"Unexpected structural-tag anchor: #c-{tag}.",
                source=str(path),
                line=_line(source, offset),
            )

    builtins = category("builtins")
    expected = BUILTIN_COMPONENT_NAMES | STRUCTURAL_TAG_NAMES
    configured = set(builtins.symbols) if builtins is not None else set()
    if configured != expected:
        yield GuardResult.error(
            guard="builtin_tags",
            message=("The Built-in tags Reference category does not match Citry's reserved public tag names."),
            source="reference_pages.py",
        )
