"""
Check that every snippet include points at a real file.

The docs use pymdownx-style ``--8<-- "path"`` includes to pull in shared
fragments. Block includes put unquoted paths between two bare ``--8<--``
delimiters. This guard scans the markdown source and reports an include whose
target file does not exist, so a broken include is caught up front with its
source line instead of failing mid-build.

Paths resolve against the repo root (``ctx.repo_root``), the same base the
build pipeline uses.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.fence_validator import _source_files

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Single-line form: --8<-- "path"   (optionally followed by :section markers).
# A leading semicolon escapes the marker in pymdownx and is documentation, not
# a filesystem reference, so it deliberately does not match here.
_SNIPPET_LINE = re.compile(r'^\s*-{2}8<-{2}\s+"(?P<path>[^"]+)"\s*$')
# Block-form delimiter line: a bare --8<-- on its own line toggles a block of
# unquoted paths. Pymdown treats each non-empty, non-comment line in the block
# as a path; quotes are only stripped from the single-line form.
_SNIPPET_BLOCK_DELIM = re.compile(r"^\s*-{2}8<-{2}\s*$")


def iter_snippet_refs(text: str) -> Iterator[tuple[int, str]]:
    """Yield (line_number, raw_path) for every snippet reference in the source."""
    in_block = False
    for lineno, line in enumerate(text.split("\n"), start=1):
        if in_block:
            if _SNIPPET_BLOCK_DELIM.match(line):
                in_block = False
                continue
            raw_path = line.strip()
            if raw_path and not raw_path.startswith(";"):
                yield lineno, raw_path
            continue
        m = _SNIPPET_LINE.match(line)
        if m:
            yield lineno, m.group("path")
        elif _SNIPPET_BLOCK_DELIM.match(line):
            in_block = True


def _resolve(ctx: GuardContext, raw_path: str) -> bool:
    """True if the snippet target exists under the repo root."""
    # Strip a trailing ":section" / ":start:end" selector if the bare path
    # alone doesn't exist (pymdownx allows section/line selectors after the path).
    candidates = [raw_path]
    if ":" in raw_path:
        candidates.append(raw_path.split(":", 1)[0])
    return any((ctx.repo_root / cand).is_file() for cand in candidates)


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    for label, text in _source_files(ctx):
        for lineno, raw_path in iter_snippet_refs(text):
            if not _resolve(ctx, raw_path):
                yield GuardResult.error(
                    guard="snippet_path",
                    message=f"Snippet target not found: {raw_path!r}",
                    source=label,
                    line=lineno,
                )
