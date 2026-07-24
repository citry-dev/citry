"""
Pygments lexer-alias guard.

A fenced code block whose language is not a registered Pygments lexer (a typo
like ```pythn) silently falls back to plain text when the site renders, so you
just get unstyled output. Here it is a build error instead, so typos surface
at build time rather than as quietly broken highlighting.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.fence_validator import _source_files, scan_fences

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Info-strings we intentionally pass through to the browser instead of Pygments
# (diagram languages, plain-text markers). Grows as new ones are introduced.
ALLOWED_NON_LEXER_LANGS = {
    "",
    "text",
    "plain",
    "console",
    "shell-session",
    "mermaid",
}


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    for label, text in _source_files(ctx):
        for fence in scan_fences(text):
            if not fence.closed:
                continue  # the fence_validator guard owns unclosed fences
            lang = fence.lang
            if lang in ALLOWED_NON_LEXER_LANGS:
                continue
            try:
                get_lexer_by_name(lang)
            except ClassNotFound:
                yield GuardResult.error(
                    guard="lexer_alias",
                    message=f"Unknown code-fence language: {lang!r}",
                    source=label,
                    line=fence.open_line,
                )
