"""
The ``citry`` lexer: Python, with the embedded ``template``/``js``/``css`` highlighted.

``CitryPythonLexer`` behaves like Pygments' ``PythonLexer`` but recognises the
three multiline string attributes a Citry component uses and hands each body to
the right language:

- ``template = \"\"\"...\"\"\"`` to the Citry HTML lexer (``<c-*>`` tags, ``{{ }}``, ...),
- ``js = \"\"\"...\"\"\"`` to the JavaScript lexer,
- ``css = \"\"\"...\"\"\"`` to the CSS lexer.

The detection is deliberately simple, matching the upstream ``pygments-djc``: it
fires on any ``template``/``js``/``css`` triple-quoted assignment, even one not
on a component class. That is fine for documentation, where these names almost
always mean a component.
"""

from __future__ import annotations

from typing import Any, ClassVar

from pygments.lexer import ExtendedRegexLexer, bygroups
from pygments.lexers.css import CssLexer
from pygments.lexers.javascript import JavascriptLexer
from pygments.lexers.python import PythonLexer
from pygments.token import Name, Operator, Punctuation, String, Text

from pygments_citry.citry_html import CitryHtmlLexer

# Matches one exact quote family for `template = """` or the typed form.
# The nine capture groups are highlighted individually by the bygroups action below.
_CAPTURE = r"({name})(\s*)(?:(:)(\s*)([^\s=]+))?(\s*)(=)(\s*)({quote})"

# Highlights the nine groups of _CAPTURE. Reused for all three openers, which
# differ only in the attribute name and the state they push.
_OPENER = bygroups(
    Name.Variable,  # the attribute name (template / js / css)
    Text,
    Punctuation,  # the ':' of an optional type annotation
    Text,
    Name.Class,  # the annotation type, if present
    Text,
    Operator,  # the '='
    Text,
    String.Doc,  # the opening triple quote
)


def _embedded_string_state(delimiter: str, lexer: type[Any]) -> list[tuple[Any, ...]]:
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
        for offset, token, value in embedded.get_tokens_unprocessed(text[start:end]):
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
    """Lexer for Citry component code: Python plus the embedded template/js/css."""

    name = "Citry Python"
    aliases: ClassVar[list[str]] = ["citry"]

    tokens: ClassVar[dict[str, Any]] = {
        **PythonLexer.tokens,
        # The three openers are prepended to Python's root so they win over its
        # own string handling. Each quote family gets its own closing state.
        "root": [
            (_CAPTURE.format(name="template", quote='"""'), _OPENER, "template_double_string"),
            (_CAPTURE.format(name="template", quote="'''"), _OPENER, "template_single_string"),
            (_CAPTURE.format(name="js", quote='"""'), _OPENER, "js_double_string"),
            (_CAPTURE.format(name="js", quote="'''"), _OPENER, "js_single_string"),
            (_CAPTURE.format(name="css", quote='"""'), _OPENER, "css_double_string"),
            (_CAPTURE.format(name="css", quote="'''"), _OPENER, "css_single_string"),
            *PythonLexer.tokens["root"],
        ],
        "template_double_string": _embedded_string_state(r'"""', CitryHtmlLexer),
        "template_single_string": _embedded_string_state(r"'''", CitryHtmlLexer),
        "js_double_string": _embedded_string_state(r'"""', JavascriptLexer),
        "js_single_string": _embedded_string_state(r"'''", JavascriptLexer),
        "css_double_string": _embedded_string_state(r'"""', CssLexer),
        "css_single_string": _embedded_string_state(r"'''", CssLexer),
    }
