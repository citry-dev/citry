"""
The lexer for the HTML that lives inside a Citry component's ``template``.

Citry templates are HTML with a few additions: ``<c-*>`` component and
control-flow tags, server-side Python expressions, client directives,
``{{ python }}`` interpolation, ``{# comment #}``, and a verbatim ``<c-raw>``
element. This lexer extends Pygments' plain ``HtmlLexer`` with those languages
and channels called out.

It is registered as ``citry-html``, both on its own (for a fenced block that
shows only a template) and embedded by ``CitryPythonLexer`` to highlight the
``template`` string of a component.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygments.lexer import ExtendedRegexLexer, bygroups, using
from pygments.lexers.html import HtmlLexer
from pygments.lexers.javascript import JavascriptLexer
from pygments.lexers.python import PythonLexer
from pygments.token import Comment, Name, Operator, Punctuation, Text

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator

# An exact Citry tag name ends where the template grammar's tag name ends. The
# explicit lookahead stops a built-in prefix such as ``c-slot`` from stealing
# the start of a user component name such as ``c-slot-panel``.
_TAG_END = r"(?=\s|/?>|\{#)"

# One Python lexer, reused for the bodies of {{ ... }} interpolations.
_PYTHON = PythonLexer()
_JAVASCRIPT = JavascriptLexer()


def _interpolation(_lexer: Any, match: re.Match[str], ctx: Any) -> Iterator[tuple[int, Any, str]]:
    """
    Tokenise a ``{{ ... }}`` interpolation, handing the expression to Python.

    The closing ``}}`` is found by scanning for one at brace depth zero and
    skipping Python strings and line comments along the way. A ``}}`` inside a
    string (``{{ "}}" }}``) or a nested dict literal
    (``{{ {"a": {1: 2}} }}``) does not end the block early, while quotes and
    braces after ``#`` cannot hide the host delimiter. This mirrors how the
    engine's grammar finds the boundary; a plain regex cannot count nesting.

    Surrounding whitespace stays plain text and only the expression in the
    middle is highlighted, matching how the rest of the lexer treats a value.
    """
    text = match.string
    yield match.start(), Punctuation, "{{"
    start = match.end()
    length = len(text)
    i = start
    depth = 0
    close = None
    while i < length:
        char = text[i]
        if char == "#":
            i += 1
            while i < length and text[i] not in "\r\n":
                if depth == 0 and text.startswith("}}", i):
                    close = i
                    break
                i += 1
            if close is not None:
                break
            continue
        if char in "\"'":  # skip a Python string literal, honouring backslash escapes
            quote = char
            delimiter = quote * 3 if text.startswith(quote * 3, i) else quote
            i += len(delimiter)
            while i < length:
                if text[i] == "\\":
                    i += 2
                    continue
                if text.startswith(delimiter, i):
                    i += len(delimiter)
                    break
                i += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            if depth:
                depth -= 1
            elif i + 1 < length and text[i + 1] == "}":
                close = i
                break
        i += 1

    body = text[start : close if close is not None else length]
    lead = body[: len(body) - len(body.lstrip())]
    expr = body.strip()
    if lead:
        yield start, Text, lead
    for offset, token, value in _PYTHON.get_tokens_unprocessed(expr):
        yield start + len(lead) + offset, token, value
    trail = body[len(lead) + len(expr) :]
    if trail:
        yield start + len(lead) + len(expr), Text, trail

    if close is not None:
        yield close, Punctuation, "}}"
        ctx.pos = close + 2
    else:
        ctx.pos = length


def _handler_value(
    match: re.Match[str],
    ctx: Any,
    *,
    allow_args: bool,
) -> Iterator[tuple[int, Any, str]]:
    """Highlight a Citry handler reference and its optional Alpine arguments."""
    raw = match.group()
    quote = raw[0] if raw[0] in "\"'" else ""
    closed = bool(quote) and len(raw) > 1 and raw[-1] == quote
    body = raw[1:-1] if closed else raw[len(quote) :]
    body_start = match.start() + len(quote)

    if quote:
        yield match.start(), Punctuation, quote
    lead = body[: len(body) - len(body.lstrip())]
    content = body.strip()
    if lead:
        yield body_start, Text, lead

    content_start = body_start + len(lead)
    open_index = content.find("(") if allow_args else -1
    if open_index >= 0:
        handler = content[:open_index].rstrip()
        if handler:
            yield content_start, Name.Function, handler
        before_open = content[len(handler) : open_index]
        if before_open:
            yield content_start + len(handler), Text, before_open
        yield content_start + open_index, Punctuation, "("

        args_end = len(content) - 1 if content.endswith(")") else len(content)
        args = content[open_index + 1 : args_end]
        for offset, token, value in _JAVASCRIPT.get_tokens_unprocessed(args):
            yield content_start + open_index + 1 + offset, token, value
        if content.endswith(")"):
            yield content_start + len(content) - 1, Punctuation, ")"
    elif content:
        yield content_start, Name.Function, content

    trail = body[len(lead) + len(content) :]
    if trail:
        yield body_start + len(body) - len(trail), Text, trail
    if closed:
        yield match.end() - 1, Punctuation, quote
    ctx.pos = match.end()


def _event_handler(
    _lexer: Any,
    match: re.Match[str],
    ctx: Any,
) -> Iterator[tuple[int, Any, str]]:
    """Highlight an ``@c-*`` handler plus its optional Alpine argument object."""
    yield from _handler_value(match, ctx, allow_args=True)


def _state_handler(
    _lexer: Any,
    match: re.Match[str],
    ctx: Any,
) -> Iterator[tuple[int, Any, str]]:
    """Highlight a two-way ``:c-*`` flush handler reference."""
    yield from _handler_value(match, ctx, allow_args=False)


def _nested_template(
    lexer: Any,
    match: re.Match[str],
    ctx: Any,
) -> Iterator[tuple[int, Any, str]]:
    """Highlight one c-* nested template, including local fragment delimiters."""
    body = match.group()
    start = match.start()
    lead = body[: len(body) - len(body.lstrip())]
    content = body.strip()
    trail = body[len(lead) + len(content) :]

    if lead:
        yield start, Text, lead
    content_start = start + len(lead)
    if content.startswith("<>") and content.endswith("</>"):
        yield content_start, Punctuation, "<>"
        inner = content[2:-3]
        for offset, token, value in lexer.get_tokens_unprocessed(inner):
            yield content_start + 2 + offset, token, value
        yield content_start + len(content) - 3, Punctuation, "</>"
    else:
        for offset, token, value in lexer.get_tokens_unprocessed(content):
            yield content_start + offset, token, value
    if trail:
        yield start + len(body) - len(trail), Text, trail
    ctx.pos = match.end()


# A generic c-* value is either a Python expression or a nested Citry template.
_DYNAMIC_ATTR_STATE = "dynamic-attr"
# Some channels have one fixed value language.
_PY_ATTR_STATE = "python-attr"
_JS_ATTR_STATE = "javascript-attr"
_EVENT_HANDLER_STATE = "event-handler"
_STATE_HANDLER_STATE = "state-handler"
# Citry follows the parser grammar's permissive attribute-name boundary. The
# {# sequence starts a template comment rather than joining the attribute.
_ATTR_CHAR = r"(?:(?!\{#)[^\s=/><])"
_ATTR_NAME = rf"{_ATTR_CHAR}+"
_ATTR_TAIL = rf"{_ATTR_CHAR}*"
# Attribute rules shared by ordinary and built-in tags: template comments,
# ordinary attributes, boolean markers, and the tag close.
_COMMON_ATTR_RULES = [
    (r"\{#[\s\S]*?#\}", Comment),
    (rf"({_ATTR_NAME})(\s*)(=)(\s*)", bygroups(Name.Attribute, Text, Operator, Text), "attr"),
    (_ATTR_NAME, Name.Attribute),
    (r"(/?)(\s*)(>)", bygroups(Punctuation, Text, Punctuation), "#pop"),
]
_WS_RULE = (r"\s+", Text)
# `$c-props` is evaluated by the client runtime, so its value is JavaScript.
_CLIENT_PROPS_ATTR_RULE = (
    r"(\$c-props)(\s*)(=)(\s*)",
    bygroups(Name.Attribute, Text, Operator, Text),
    _JS_ATTR_STATE,
)
# `$c-tr` values are Alpine named-value expressions. Its c-prefixed form is
# still matched by `_C_ATTR_RULE` and therefore remains a Python expression.
_CLIENT_I18N_ATTR_RULE = (
    rf"(\$c-tr(?=[:.\[]){_ATTR_TAIL})(\s*)(=)(\s*)",
    bygroups(Name.Attribute, Text, Operator, Text),
    _JS_ATTR_STATE,
)
# #c-key is a server-side expression. #c-ignore is a bare marker and falls
# through to the common attribute-name rule.
_META_KEY_ATTR_RULE = (
    r"(#c-key)(\s*)(=)(\s*)",
    bygroups(Name.Attribute, Text, Operator, Text),
    _PY_ATTR_STATE,
)
# Citry Events values name a server handler. An @c-* handler may append one
# parenthesized Alpine expression, while a :c-* value is only a handler name.
_EVENT_ATTR_RULE = (
    rf"(@c-{_ATTR_TAIL})(\s*)(=)(\s*)",
    bygroups(Name.Attribute, Text, Operator, Text),
    _EVENT_HANDLER_STATE,
)
_STATE_BINDING_ATTR_RULE = (
    rf"(:c-{_ATTR_TAIL})(\s*)(=)(\s*)",
    bygroups(Name.Attribute, Text, Operator, Text),
    _STATE_HANDLER_STATE,
)
# Direct Alpine directives are evaluated in the browser. Their c-prefixed
# dynamic forms are matched by _C_ATTR_RULE first and stay Python.
_CLIENT_ATTR_RULE = (
    rf"((?:@|:|x-){_ATTR_TAIL})(\s*)(=)(\s*)",
    bygroups(Name.Attribute, Text, Operator, Text),
    _JS_ATTR_STATE,
)
# A c-* dynamic attribute may contain a Python expression or a nested template.
_C_ATTR_RULE = (
    rf"(c-{_ATTR_TAIL})(\s*)(=)(\s*)",
    bygroups(Name.Attribute, Text, Operator, Text),
    _DYNAMIC_ATTR_STATE,
)
# Structural control-flow tags carry Python-valued attributes that are not
# c-*-prefixed. These rules live in tag-specific states because the same names
# on other elements are ordinary static HTML attributes.
_COND_ATTR_RULE = (r"(cond)(\s*)(=)(\s*)", bygroups(Name.Attribute, Text, Operator, Text), _PY_ATTR_STATE)
_EACH_ATTR_RULE = (r"(each)(\s*)(=)(\s*)", bygroups(Name.Attribute, Text, Operator, Text), _PY_ATTR_STATE)


class CitryHtmlLexer(ExtendedRegexLexer, HtmlLexer):
    """Highlights the HTML (plus Citry tags and interpolation) of a Citry template."""

    name = "Citry HTML"
    aliases: ClassVar[list[str]] = ["citry-html"]

    tokens: ClassVar[dict[str, Any]] = {
        **HtmlLexer.tokens,
        "root": [
            # {# template comment #}
            (r"\{#[\s\S]*?#\}", Comment),
            # {{ python-expression }}: a callback scans to the balanced }}
            (r"\{\{", _interpolation),
            # a lone { that is not part of {{ or {#
            (r"\{", Text),
            # Outside a nested c-* value, <> is ordinary authored text.
            (r"<>", Text),
            # <c-raw> ... </c-raw>: the body is verbatim (not interpreted)
            (
                r"(<)(\s*)(c-raw)" + _TAG_END,
                bygroups(Punctuation, Text, Name.Tag),
                ("raw-content", "tag"),
            ),
            # Only the structural tags with unprefixed Python attributes need
            # special states. Every other c-* name falls through to HtmlLexer.
            (
                r"(</?)(\s*)(c-(?:if|elif))" + _TAG_END,
                bygroups(Punctuation, Text, Name.Tag),
                "condition-tag",
            ),
            (
                r"(</?)(\s*)(c-for)" + _TAG_END,
                bygroups(Punctuation, Text, Name.Tag),
                "for-tag",
            ),
            # ordinary text, stopped at { so the interpolation/comment rules fire;
            # everything after this is HtmlLexer's own root (its [^<&]+ text rule,
            # which does not stop at {, is dropped by the [1:] slice)
            (r"[^<&{]+", Text),
            *HtmlLexer.tokens["root"][1:],
        ],
        # An ordinary element's attributes.
        "tag": [
            _WS_RULE,
            _CLIENT_PROPS_ATTR_RULE,
            _CLIENT_I18N_ATTR_RULE,
            _META_KEY_ATTR_RULE,
            _C_ATTR_RULE,
            _EVENT_ATTR_RULE,
            _STATE_BINDING_ATTR_RULE,
            _CLIENT_ATTR_RULE,
            *_COMMON_ATTR_RULES,
        ],
        "condition-tag": [
            _WS_RULE,
            _CLIENT_PROPS_ATTR_RULE,
            _CLIENT_I18N_ATTR_RULE,
            _META_KEY_ATTR_RULE,
            _C_ATTR_RULE,
            _EVENT_ATTR_RULE,
            _STATE_BINDING_ATTR_RULE,
            _CLIENT_ATTR_RULE,
            _COND_ATTR_RULE,
            *_COMMON_ATTR_RULES,
        ],
        "for-tag": [
            _WS_RULE,
            _CLIENT_PROPS_ATTR_RULE,
            _CLIENT_I18N_ATTR_RULE,
            _META_KEY_ATTR_RULE,
            _C_ATTR_RULE,
            _EVENT_ATTR_RULE,
            _STATE_BINDING_ATTR_RULE,
            _CLIENT_ATTR_RULE,
            _EACH_ATTR_RULE,
            *_COMMON_ATTR_RULES,
        ],
        # A c-* value whose trimmed body begins with a tag or <> fragment is a
        # nested template. Other values are Python expressions.
        "dynamic-attr": [
            (
                r'(")(\s*<(?=>|[A-Za-z])(?:[^"\\]|\\.)*)(")',
                bygroups(Punctuation, _nested_template, Punctuation),
                "#pop",
            ),
            (
                r"(')(\s*<(?=>|[A-Za-z])(?:[^'\\]|\\.)*)(')",
                bygroups(Punctuation, _nested_template, Punctuation),
                "#pop",
            ),
            (r'(")((?:[^"\\]|\\.)*)(")', bygroups(Punctuation, using(PythonLexer), Punctuation), "#pop"),
            (r"(')((?:[^'\\]|\\.)*)(')", bygroups(Punctuation, using(PythonLexer), Punctuation), "#pop"),
            (r'(")([\s\S]*)$', bygroups(Punctuation, using(PythonLexer)), "#pop"),
            (r"(')([\s\S]*)$", bygroups(Punctuation, using(PythonLexer)), "#pop"),
            (r"[^\s>]+", using(PythonLexer), "#pop"),
        ],
        # The value of a fixed server-side attribute is a Python expression.
        "python-attr": [
            (r'(")((?:[^"\\]|\\.)*)(")', bygroups(Punctuation, using(PythonLexer), Punctuation), "#pop"),
            (r"(')((?:[^'\\]|\\.)*)(')", bygroups(Punctuation, using(PythonLexer), Punctuation), "#pop"),
            (r'(")([\s\S]*)$', bygroups(Punctuation, using(PythonLexer)), "#pop"),
            (r"(')([\s\S]*)$", bygroups(Punctuation, using(PythonLexer)), "#pop"),
            (r"[^\s>]+", using(PythonLexer), "#pop"),
        ],
        # The direct client props value is an Alpine/JavaScript expression.
        "javascript-attr": [
            (r'(")((?:[^"\\]|\\.)*)(")', bygroups(Punctuation, using(JavascriptLexer), Punctuation), "#pop"),
            (r"(')((?:[^'\\]|\\.)*)(')", bygroups(Punctuation, using(JavascriptLexer), Punctuation), "#pop"),
            (r'(")([\s\S]*)$', bygroups(Punctuation, using(JavascriptLexer)), "#pop"),
            (r"(')([\s\S]*)$", bygroups(Punctuation, using(JavascriptLexer)), "#pop"),
            (r"[^\s>]+", using(JavascriptLexer), "#pop"),
        ],
        # @c-* values use a handler reference followed by an optional
        # parenthesized Alpine expression. The lexer cannot know registry
        # aliases that themselves contain parentheses, so it treats the first
        # opening parenthesis as the author-facing call shell.
        "event-handler": [
            (r'"(?:[^"\\]|\\.)*"', _event_handler, "#pop"),
            (r"'(?:[^'\\]|\\.)*'", _event_handler, "#pop"),
            (r'"[\s\S]*$', _event_handler, "#pop"),
            (r"'[\s\S]*$", _event_handler, "#pop"),
            (r"[^\s>]+", _event_handler, "#pop"),
        ],
        # A valued :c-* binding names the handler that flushes the update.
        "state-handler": [
            (r'"(?:[^"\\]|\\.)*"', _state_handler, "#pop"),
            (r"'(?:[^'\\]|\\.)*'", _state_handler, "#pop"),
            (r'"[\s\S]*$', _state_handler, "#pop"),
            (r"'[\s\S]*$", _state_handler, "#pop"),
            (r"[^\s>]+", _state_handler, "#pop"),
        ],
        # The verbatim body of <c-raw>...</c-raw>: plain text until the close tag.
        "raw-content": [
            (
                r"(<)(\s*)(/)(\s*)(c-raw)(\s*)(>)",
                bygroups(Punctuation, Text, Punctuation, Text, Name.Tag, Text, Punctuation),
                "#pop",
            ),
            (r"[^<]+", Text),
            (r"<", Text),
        ],
    }
