"""
Code-block language-tag guard.

Flags fenced code blocks that declare no language at all (an opening fence with
an empty info-string). A language tag drives syntax highlighting and helps the
`.md` companion / LLM consumers; an untagged block renders as unstyled text.

This is the source-side complement to the lexer-alias guard: lexer_alias
checks that a *declared* language is real; code_lang checks that a language is
*declared* in the first place.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.fence_validator import _source_files, scan_fences

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    for label, text in _source_files(ctx):
        for fence in scan_fences(text):
            if fence.closed and not fence.info_string:
                yield GuardResult.warning(
                    guard="code_lang",
                    message="Code fence has no language tag (use ```text for plain output)",
                    source=label,
                    line=fence.open_line,
                )
