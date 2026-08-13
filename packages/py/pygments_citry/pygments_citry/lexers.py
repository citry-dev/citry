"""
The ``citry`` lexer: Python, with Citry's four embedded asset languages highlighted.

``CitryPythonLexer`` behaves like Pygments' ``PythonLexer`` but recognises the
four multiline string attributes a Citry component uses and hands each body to
the right language:

- ``template = \"\"\"...\"\"\"`` to the Citry HTML lexer (``<c-*>`` tags, ``{{ }}``, ...),
- ``js = \"\"\"...\"\"\"`` to the JavaScript lexer,
- ``css = \"\"\"...\"\"\"`` to the CSS lexer, and
- ``messages = \"\"\"...\"\"\"`` to the Fluent lexer.

The detection is deliberately simple, matching the upstream ``pygments-djc``:
it fires on any ``template``/``js``/``css``/``messages`` triple-quoted
assignment, even one not on a component class. That is fine for documentation,
where these names almost always mean a component.
"""

from __future__ import annotations

from typing import Any, ClassVar

from fluent.pygments.lexer import FluentLexer
from pygments.lexer import ExtendedRegexLexer, bygroups
from pygments.lexers.css import CssLexer
from pygments.lexers.javascript import JavascriptLexer
from pygments.lexers.python import PythonLexer
from pygments.token import Name, Operator, Punctuation, String, Text

from pygments_citry.citry_html import CitryHtmlLexer

# Matches one exact quote family for `template = """` or the typed form.
# The nine capture groups are highlighted individually by the bygroups action below.
_CAPTURE = r"({name})(\s*)(?:(:)(\s*)([^\s=]+))?(\s*)(=)(\s*)({quote})"

# Highlights the nine groups of _CAPTURE. Reused for all four openers, which
# differ only in the attribute name and the state they push.
_OPENER = bygroups(
    Name.Variable,  # the asset attribute name
    Text,
    Punctuation,  # the ':' of an optional type annotation
    Text,
    Name.Class,  # the annotation type, if present
    Text,
    Operator,  # the '='
    Text,
    String.Doc,  # the opening triple quote
)


def _dedented_tokens(embedded: Any, source: str) -> list[tuple[int, Any, str]]:
    """Lex an indented asset while keeping every token at its Python offset."""
    lines = source.splitlines(keepends=True)
    prefixes = [line[: len(line) - len(line.lstrip())] for line in lines if line.strip()]
    margin = min(prefixes, key=len, default="")
    while margin and not all(prefix.startswith(margin) for prefix in prefixes):
        margin = margin[:-1]

    normalized_lines: list[str] = []
    removed_by_line: list[int] = []
    for line in lines:
        body = line.rstrip("\r\n")
        line_break = line[len(body) :]
        removed = len(body) if not body.strip() else len(margin)
        normalized_lines.append(f"{body[removed:]}{line_break}")
        removed_by_line.append(removed)
    dedented = "".join(normalized_lines)
    if dedented == source:
        return list(embedded.get_tokens_unprocessed(source))

    source_positions: list[int] = []
    removed_prefixes: list[tuple[int, Any, str]] = []
    source_offset = 0
    for original_line, removed in zip(lines, removed_by_line, strict=True):
        if removed:
            removed_prefixes.append((source_offset, Text, original_line[:removed]))
        source_positions.extend(range(source_offset + removed, source_offset + len(original_line)))
        source_offset += len(original_line)

    tokens = removed_prefixes
    for offset, token, value in embedded.get_tokens_unprocessed(dedented):
        value_offset = 0
        while value_offset < len(value):
            dedented_start = offset + value_offset
            source_start = source_positions[dedented_start]
            value_end = value_offset + 1
            while value_end < len(value):
                previous = source_positions[offset + value_end - 1]
                current = source_positions[offset + value_end]
                if current != previous + 1:
                    break
                value_end += 1
            source_end = source_positions[offset + value_end - 1] + 1
            tokens.append((source_start, token, source[source_start:source_end]))
            value_offset = value_end
    return sorted(tokens, key=lambda item: item[0])


def _embedded_string_state(
    delimiter: str,
    lexer: type[Any],
    *,
    dedent: bool = False,
) -> list[tuple[Any, ...]]:
    """Build an embedded state that closes on an unescaped opening delimiter."""
    embedded = lexer()

    def body(_lexer: Any, match: Any, ctx: Any) -> Any:
        text = match.string
        start = match.start()
        search_from = start
        close = None
        while True:
            candidate = text.find(delimiter, search_from)
            if candidate < 0:
                break
            backslashes = 0
            cursor = candidate - 1
            while cursor >= start and text[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                close = candidate
                break
            search_from = candidate + len(delimiter)

        end = close if close is not None else len(text)
        source = text[start:end]
        token_stream = _dedented_tokens(embedded, source) if dedent else embedded.get_tokens_unprocessed(source)
        for offset, token, value in token_stream:
            yield start + offset, token, value
        if close is not None:
            yield close, String.Doc, delimiter
            ctx.pos = close + len(delimiter)
            if len(ctx.stack) > 1:
                ctx.stack.pop()
        else:
            ctx.pos = len(text)

    return [(r"[\s\S]", body)]


class CitryPythonLexer(ExtendedRegexLexer, PythonLexer):
    """Lexer for Citry component code: Python plus its embedded asset languages."""

    name = "Citry Python"
    aliases: ClassVar[list[str]] = ["citry"]

    tokens: ClassVar[dict[str, Any]] = {
        **PythonLexer.tokens,
        # The asset openers are prepended to Python's root so they win over its
        # own string handling. Each quote family gets its own closing state.
        "root": [
            (_CAPTURE.format(name="template", quote='"""'), _OPENER, "template_double_string"),
            (_CAPTURE.format(name="template", quote="'''"), _OPENER, "template_single_string"),
            (_CAPTURE.format(name="js", quote='"""'), _OPENER, "js_double_string"),
            (_CAPTURE.format(name="js", quote="'''"), _OPENER, "js_single_string"),
            (_CAPTURE.format(name="css", quote='"""'), _OPENER, "css_double_string"),
            (_CAPTURE.format(name="css", quote="'''"), _OPENER, "css_single_string"),
            (_CAPTURE.format(name="messages", quote='"""'), _OPENER, "messages_double_string"),
            (_CAPTURE.format(name="messages", quote="'''"), _OPENER, "messages_single_string"),
            *PythonLexer.tokens["root"],
        ],
        "template_double_string": _embedded_string_state(r'"""', CitryHtmlLexer),
        "template_single_string": _embedded_string_state(r"'''", CitryHtmlLexer),
        "js_double_string": _embedded_string_state(r'"""', JavascriptLexer),
        "js_single_string": _embedded_string_state(r"'''", JavascriptLexer),
        "css_double_string": _embedded_string_state(r'"""', CssLexer),
        "css_single_string": _embedded_string_state(r"'''", CssLexer),
        "messages_double_string": _embedded_string_state(r'"""', FluentLexer, dedent=True),
        "messages_single_string": _embedded_string_state(r"'''", FluentLexer, dedent=True),
    }
