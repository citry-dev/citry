"""
Warn when a Citry code block highlights with an error token.

The ``citry`` and ``citry-html`` lexers follow the template grammar's rules
for tags, quoted values, and nested templates, so an error token in a
published example almost always means the example is not valid Citry: the browser shows a red box around the character, and a reader
who copies the snippet gets a parse error. A typical case is a nested template
whose inner attribute reuses the outer value's quote, which ends the outer
value early.

The guard lexes every closed ``citry`` and ``citry-html`` fence. A snippet
include inside such a fence (``--8<-- "path"`` or the block form) is lexed as
a separate file with the fence's language and reported at the include line.
A ``:section`` selector is dropped, so the whole included file is lexed.
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from pygments.lexers import get_lexer_by_name
from pygments.token import Error

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.fence_validator import _source_files, scan_fences
from docs_site._internal.guards.snippet_path import _SNIPPET_BLOCK_DELIM, iter_snippet_refs

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from docs_site._internal.guards.base import GuardContext

# The languages whose lexers this project owns. Other lexers come from
# Pygments itself and flag syntax that is foreign to them, which is not a docs bug.
_CITRY_LANGS = frozenset({"citry", "citry-html"})


def _first_error(lang: str, source: str) -> tuple[int, str] | None:
    """Return the 0-based line and text of the first error token, if any."""
    for offset, token, value in get_lexer_by_name(lang).get_tokens_unprocessed(source):
        if token in Error:
            return source.count("\n", 0, offset), value
    return None


def _snippet_text(repo_root: Path, raw_path: str) -> str | None:
    """Read the whole included file; a ``:section`` selector after the path is dropped."""
    for candidate in (raw_path, raw_path.split(":", 1)[0]):
        path = repo_root / candidate
        if path.is_file():
            return path.read_text(encoding="utf-8")
    # A missing target is reported by the snippet_path guard.
    return None


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    for label, text in _source_files(ctx):
        for fence in scan_fences(text):
            if not fence.closed or fence.lang not in _CITRY_LANGS:
                continue
            body_lines = fence.body.split("\n")
            for body_line, raw_path in iter_snippet_refs(fence.body):
                # The include is not code, so blank it in the fence body (keeping
                # line numbers) and lex the included file on its own.
                body_lines[body_line - 1] = ""
                included = _snippet_text(ctx.repo_root, raw_path)
                found = _first_error(fence.lang, included) if included is not None else None
                if found is not None:
                    yield _result(label, fence.open_line + body_line, fence.lang, found[1], raw_path)
            # The bare --8<-- lines that open and close a block include are
            # not code either.
            body_lines = ["" if _SNIPPET_BLOCK_DELIM.match(line) else line for line in body_lines]
            # A fence nested in a list or admonition carries a shared indent on
            # every line; the lexer needs the code without it, as the reader sees it.
            found = _first_error(fence.lang, textwrap.dedent("\n".join(body_lines)))
            if found is not None:
                yield _result(label, fence.open_line + 1 + found[0], fence.lang, found[1], None)


def _result(label: str, line: int, lang: str, value: str, snippet: str | None) -> GuardResult:
    where = f" in included snippet {snippet!r}" if snippet else ""
    return GuardResult.warning(
        guard="citry_highlight",
        message=(
            f"The {lang} lexer marks {value!r} as an error{where}, so the example is "
            "probably not valid Citry. Highlighting broke here; the cause is often a "
            "quote or tag a few lines earlier."
        ),
        source=label,
        line=line,
    )
