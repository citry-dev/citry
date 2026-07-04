"""
pygments-citry: a Pygments lexer for Citry components.

Importing this package registers the ``citry`` lexer with Pygments, so
``get_lexer_by_name("citry")`` resolves even in an environment where the plugin
entry point was not picked up (for example an editable checkout whose plugin
metadata is not written). For an installed package, the ``pygments.lexers``
entry point in ``pyproject.toml`` is the primary registration and needs no
import.
"""

from __future__ import annotations

from pygments.lexers import LEXERS

from pygments_citry.citry_html import CitryHtmlLexer
from pygments_citry.lexers import CitryPythonLexer

__all__ = ["CitryHtmlLexer", "CitryPythonLexer"]

# Register in Pygments' builtin lexer table. get_lexer_by_name scans this table
# before the entry-point plugins, so an explicit `import pygments_citry` becomes
# a deterministic loader. Each tuple is (module, name, aliases, filenames,
# mimetypes); _load_lexers imports the module and finds the class via __all__.
#
# `citry` is the full component lexer (Python + embedded template/js/css);
# `citry-html` is the template lexer alone, for a fence that shows only a
# template (`<c-*>` tags, `{{ }}`, `{# #}`) with no surrounding Python.
LEXERS["CitryPythonLexer"] = (
    "pygments_citry",
    "Citry Python",
    ("citry",),
    (),
    (),
)
LEXERS["CitryHtmlLexer"] = (
    "pygments_citry",
    "Citry HTML",
    ("citry-html",),
    (),
    (),
)
