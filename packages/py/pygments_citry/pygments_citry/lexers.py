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

from pygments.lexer import bygroups, using
from pygments.lexers.css import CssLexer
from pygments.lexers.javascript import JavascriptLexer
from pygments.lexers.python import PythonLexer
from pygments.token import Name, Operator, Punctuation, String, Text

from pygments_citry.citry_html import CitryHtmlLexer

# Matches `template = """` or the typed `template: some.Type = """` (and the ''' form).
# The nine capture groups are highlighted individually by the bygroups action below.
_CAPTURE = r'({name})(\s*)(?:(:)(\s*)([^\s=]+))?(\s*)(=)(\s*)((?:"""|\'\'\'))'

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


class CitryPythonLexer(PythonLexer):
    """Lexer for Citry component code: Python plus the embedded template/js/css."""

    name = "Citry Python"
    aliases: ClassVar[list[str]] = ["citry"]

    tokens: ClassVar[dict[str, Any]] = {
        **PythonLexer.tokens,
        # The three openers are prepended to Python's root so they win over its
        # own string handling; each pushes a state that re-lexes the body.
        "root": [
            (_CAPTURE.format(name="template"), _OPENER, "template_string"),
            (_CAPTURE.format(name="js"), _OPENER, "js_string"),
            (_CAPTURE.format(name="css"), _OPENER, "css_string"),
            *PythonLexer.tokens["root"],
        ],
        # Inside a body: the closing triple quote pops (first, so it wins);
        # otherwise the run up to the close is handed to the embedded lexer.
        "template_string": [
            (r'(?:"""|\'\'\')', String.Doc, "#pop"),
            (r'((?!"""|\'\'\')(?:.|\n))+', using(CitryHtmlLexer)),
        ],
        "js_string": [
            (r'(?:"""|\'\'\')', String.Doc, "#pop"),
            (r'((?!"""|\'\'\')(?:.|\n))+', using(JavascriptLexer)),
        ],
        "css_string": [
            (r'(?:"""|\'\'\')', String.Doc, "#pop"),
            (r'((?!"""|\'\'\')(?:.|\n))+', using(CssLexer)),
        ],
    }
