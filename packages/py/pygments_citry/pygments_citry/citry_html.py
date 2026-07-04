"""
The lexer for the HTML that lives inside a Citry component's ``template``.

Citry templates are HTML with a few additions: ``<c-*>`` component and
control-flow tags, ``c-*`` dynamic attributes whose values are Python
expressions, ``{{ python }}`` interpolation, ``{# comment #}``, and a verbatim
``<c-raw>`` element. This lexer extends Pygments' plain ``HtmlLexer`` with those,
so a Citry template highlights as HTML with the Citry bits called out, and the
Python inside ``{{ }}`` and ``c-*`` values is handed to the Python lexer.

It is registered as ``citry-html``, both on its own (for a fenced block that
shows only a template) and embedded by ``CitryPythonLexer`` to highlight the
``template`` string of a component.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from pygments.lexer import ExtendedRegexLexer, bygroups, using
from pygments.lexers.html import HtmlLexer
from pygments.lexers.python import PythonLexer
from pygments.token import Comment, Name, Operator, Punctuation, Text

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator

# The thirteen built-in <c-*> tags (control flow, slots, provide, assets, raw),
# highlighted distinctly from a user component such as <c-Card>. This list is
# the Python mirror of RESERVED_TAG_NAMES in
# crates/citry_template_parser/src/constants.rs; keep the two in step.
_BUILTIN_TAGS = (
    "c-if",
    "c-elif",
    "c-else",
    "c-for",
    "c-empty",
    "c-slot",
    "c-fill",
    "c-component",
    "c-element",
    "c-provide",
    "c-css",
    "c-js",
    "c-raw",
)
# The names without the leading "c-", for the tag-matching alternation.
_BUILTIN_TAG_NAMES = "|".join(tag[2:] for tag in _BUILTIN_TAGS)

# One Python lexer, reused for the bodies of {{ ... }} interpolations.
_PYTHON = PythonLexer()


def _interpolation(_lexer: Any, match: re.Match[str], ctx: Any) -> Iterator[tuple[int, Any, str]]:
    """
    Tokenise a ``{{ ... }}`` interpolation, handing the expression to Python.

    The closing ``}}`` is found by scanning for one at brace depth zero and
    skipping Python string literals along the way, so a ``}}`` inside a string
    (``{{ "}}" }}``) or a nested dict literal (``{{ {"a": {1: 2}} }}``) does not
    end the block early. This mirrors how the engine's grammar finds the
    boundary; a plain regex cannot, because it cannot count nesting.

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
        if char in "\"'":  # skip a Python string literal, honouring backslash escapes
            quote = char
            i += 1
            while i < length:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
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


# The value of a c-* (or built-in) attribute is a Python expression, quoted or bare.
_PY_ATTR_STATE = "python-attr"
# Attribute rules shared by ordinary and built-in tags: framework passthrough
# names plain HtmlLexer cannot tokenise (@click, [style], (click)), ordinary
# attributes (covers :class and v-model, which HtmlLexer handles), and the close.
_COMMON_ATTR_RULES = [
    (r"([@\[(][\w:@.()\[\]-]*)(\s*)(=)(\s*)", bygroups(Name.Attribute, Text, Operator, Text), "attr"),
    (r"[@\[(][\w:@.()\[\]-]*", Name.Attribute),
    (r"([\w:-]+)(\s*)(=)(\s*)", bygroups(Name.Attribute, Text, Operator, Text), "attr"),
    (r"[\w:-]+", Name.Attribute),
    (r"(/?)(\s*)(>)", bygroups(Punctuation, Text, Punctuation), "#pop"),
]
_WS_RULE = (r"\s+", Text)
# A c-* dynamic attribute: the value is a Python expression.
_C_ATTR_RULE = (r"(c-[\w:@.-]*)(\s*)(=)(\s*)", bygroups(Name.Attribute, Text, Operator, Text), _PY_ATTR_STATE)
# Built-in tags carry Python-valued attributes that are not c-*-prefixed:
# `cond` on c-if/c-elif, `each` on c-for, `is` on c-component/c-element. This
# rule is used only inside a built-in tag, so a plain HTML `is="..."` on an
# ordinary element still highlights as a string.
_BUILTIN_ATTR_RULE = (r"(cond|each|is)(\s*)(=)(\s*)", bygroups(Name.Attribute, Text, Operator, Text), _PY_ATTR_STATE)


class CitryHtmlLexer(ExtendedRegexLexer, HtmlLexer):
    """Highlights the HTML (plus Citry tags and interpolation) of a Citry template."""

    name = "Citry HTML"
    aliases: ClassVar[list[str]] = ["citry-html"]

    tokens: ClassVar[dict[str, Any]] = {
        **HtmlLexer.tokens,
        "root": [
            # {# template comment #}
            (r"\{#.*?#\}", Comment),
            # {{ python-expression }}: a callback scans to the balanced }}
            (r"\{\{", _interpolation),
            # a lone { that is not part of {{ or {#
            (r"\{", Text),
            # <c-raw> ... </c-raw>: the body is verbatim (not interpreted)
            (r"(<)(\s*)(c-raw)\b", bygroups(Punctuation, Text, Name.Builtin), ("raw-content", "tag")),
            # built-in <c-*> tags, distinct from user components (Name.Tag below)
            (
                r"(</?)(\s*)(c-(?:" + _BUILTIN_TAG_NAMES + r")\b)",
                bygroups(Punctuation, Text, Name.Builtin),
                "builtin-tag",
            ),
            # ordinary text, stopped at { so the interpolation/comment rules fire;
            # everything after this is HtmlLexer's own root (its [^<&]+ text rule,
            # which does not stop at {, is dropped by the [1:] slice)
            (r"[^<&{]+", Text),
            *HtmlLexer.tokens["root"][1:],
        ],
        # An ordinary element's attributes.
        "tag": [_WS_RULE, _C_ATTR_RULE, *_COMMON_ATTR_RULES],
        # A built-in <c-*> tag's attributes: adds its Python-valued cond/each/is.
        "builtin-tag": [_WS_RULE, _C_ATTR_RULE, _BUILTIN_ATTR_RULE, *_COMMON_ATTR_RULES],
        # The value of a c-* (or built-in) attribute: a Python expression.
        "python-attr": [
            (r'(")((?:[^"\\]|\\.)*)(")', bygroups(Punctuation, using(PythonLexer), Punctuation), "#pop"),
            (r"(')((?:[^'\\]|\\.)*)(')", bygroups(Punctuation, using(PythonLexer), Punctuation), "#pop"),
            (r"[^\s>]+", using(PythonLexer), "#pop"),
        ],
        # The verbatim body of <c-raw>...</c-raw>: plain text until the close tag.
        "raw-content": [
            (
                r"(<)(\s*)(/)(\s*)(c-raw)(\s*)(>)",
                bygroups(Punctuation, Text, Punctuation, Text, Name.Builtin, Text, Punctuation),
                "#pop",
            ),
            (r"[^<]+", Text),
            (r"<", Text),
        ],
    }
