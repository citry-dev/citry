"""
Shape source code for display on the docs site.

Python formatters such as ruff put two blank lines between top-level
definitions. That is the right layout for a source file, but in a narrow docs
column the second blank line only pushes the example further down the page.
Code blocks in pages (fences, ``--8<--`` includes, ``<c-include-file>``), live
examples, Citry UI previews, example cards, diagnostic catalog examples, and
the landing page therefore pass their source through ``display_code`` first,
which shortens each run of two or more blank lines to a single blank line. The
source files on disk stay formatted as they are, and executed examples run from
those files, so this changes only what a reader sees. The copy button copies
the displayed text, and a live example's editor starts from it.

Two kinds of text keep every blank line:

- Languages where a blank line can carry meaning. The rule applies only to the
  languages in ``COLLAPSED_LANGUAGES``. Diffs (blank context lines), console and
  plain-text output, Markdown, YAML and Fluent (blank lines inside block
  values), shell scripts (heredocs), and anything unrecognised are left alone.
- String literals. A blank line inside a Python or JavaScript string is part of
  the value, so removing it would change the code a reader copies or runs. For
  a Citry component that includes the ``template``, ``js``, ``css`` and
  ``messages`` strings. HTML has no strings, so a run inside ``<pre>`` or
  ``<textarea>`` in an HTML block is still shortened.

Line numbers written against the source file (a Markdown fence's ``hl_lines``,
the landing walkthrough's line ranges) are translated with
``DisplayCode.display_line`` so they still point at the same code after the
blank lines are removed. A block that shows line numbers keeps every blank line,
because its numbers must match the file a reader may open beside it. The
playground editor is a workspace rather than a code block, so its starter code
is shown exactly as written.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pygments import highlight
from pygments.lexers import PythonLexer, get_lexer_by_name
from pygments.token import String
from pygments.util import ClassNotFound
from pymdownx.highlight import Highlight, HighlightExtension

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pygments.formatter import Formatter
    from pygments.lexer import Lexer

# Pygments' primary alias for each language whose blank lines matter only
# inside string literals, which display_code leaves untouched. The module
# docstring lists the languages left out and why.
COLLAPSED_LANGUAGES = frozenset(
    {
        "citry",
        "citry-html",
        "css",
        "html",
        "javascript",
        "json",
        "python",
        "typescript",
    },
)


@dataclass(frozen=True)
class DisplayCode:
    """
    The text a code block shows, and where each source line ended up.

    Attributes:
        text: The source with each run of blank lines shortened to one.
        line_map: For source line ``n`` (1-based), ``line_map[n - 1]`` is the
            displayed line that shows it. A removed blank line maps to the blank
            line kept from its run, so a range that touches it stays contiguous.

    """

    text: str
    line_map: tuple[int, ...]

    def display_line(self, source_line: int) -> int:
        """Return the displayed line for a 1-based source line, clamped to the block."""
        # A walkthrough range is checked against the source by its own test, so
        # clamping here only keeps a bad number from raising mid-render.
        index = min(max(source_line, 1), len(self.line_map)) - 1
        return self.line_map[index]

    def display_lines(self, source_lines: Iterable[int]) -> list[int]:
        """
        Translate source line numbers, keeping their order and dropping the rest.

        A number outside the source is dropped rather than clamped, matching
        Pygments, which ignores an ``hl_lines`` entry past the end of a block.
        Two removed blank lines map to the same kept line, so duplicates are
        dropped too.
        """
        seen: dict[int, None] = {}
        for line in source_lines:
            if 1 <= line <= len(self.line_map):
                seen.setdefault(self.line_map[line - 1], None)
        return list(seen)


def language_collapses(language: str) -> bool:
    """Return whether a code block in ``language`` should lose its extra blank lines."""
    lexer = _lexer_for(language)
    return lexer is not None and lexer_collapses(lexer)


def lexer_collapses(lexer: Lexer) -> bool:
    """Return whether code coloured by ``lexer`` should lose its extra blank lines."""
    return bool(COLLAPSED_LANGUAGES.intersection(lexer.aliases))


def display_code(source: str, lexer: Lexer | None) -> DisplayCode:
    """
    Shorten every run of two or more blank lines in ``source`` to one.

    ``lexer`` is the lexer that colours the block. When it is ``None`` or not in
    ``COLLAPSED_LANGUAGES``, the text comes back unchanged with each line mapped
    to itself, so callers can treat every block the same way. A line holding
    only spaces or tabs counts as blank, because it looks blank on the page. The
    first line of each run is the one kept.
    """
    # A trailing newline ends the last line rather than starting an empty one;
    # set it aside so it is neither counted as a line nor merged into a run.
    body, ending = (source[:-1], "\n") if source.endswith("\n") else (source, "")
    lines = body.split("\n")
    if lexer is None or not lexer_collapses(lexer):
        return DisplayCode(text=source, line_map=tuple(range(1, len(lines) + 1)))

    string_newlines = _string_newline_offsets(body, lexer)
    kept: list[str] = []
    line_map: list[int] = []
    previous_blank = False
    offset = 0
    for line in lines:
        blank = not line.strip()
        # The newline just before this line decides whether it sits inside a
        # string literal; a blank line there is part of the string's value.
        inside_string = offset - 1 in string_newlines
        offset += len(line) + 1
        if blank and previous_blank and not inside_string:
            # The extra blank line is dropped and points at the one already kept.
            line_map.append(len(kept))
            continue
        kept.append(line)
        line_map.append(len(kept))
        previous_blank = blank
    return DisplayCode(text="\n".join(kept) + ending, line_map=tuple(line_map))


def display_code_for_language(source: str, language: str) -> DisplayCode:
    """Shape ``source`` for a block that names its language rather than a lexer."""
    return display_code(source, _lexer_for(language))


def highlight_for_display(source: str, lexer: Lexer, formatter: Formatter[Any]) -> str:
    """
    Colour ``source`` with Pygments after shaping it for display.

    Components that render a code block themselves (live examples, example
    cards, component previews, the landing page) call this instead of
    ``pygments.highlight`` so they follow the same blank-line rule as Markdown
    fences.
    """
    return highlight(display_code(source, lexer).text, lexer, formatter)


def _lexer_for(language: str) -> Lexer | None:
    # Resolve the name through Pygments so every alias a page may use (py,
    # python3, js) reaches the same decision as the lexer that colours it.
    try:
        return get_lexer_by_name(language)
    except ClassNotFound:
        return None


def _string_newline_offsets(text: str, lexer: Lexer) -> set[int]:
    """Return the offsets of newlines that sit inside a string literal."""
    # The Citry lexer colours a component's template, js and css strings in
    # their own languages, so its tokens no longer say where those strings
    # are. The plain Python lexer still sees them as Python strings.
    reader = PythonLexer() if "citry" in lexer.aliases else lexer
    offsets: set[int] = set()
    # get_tokens_unprocessed keeps offsets into the raw text, unlike
    # get_tokens, which may strip or rewrite leading and trailing newlines.
    for start, token_type, value in reader.get_tokens_unprocessed(text):
        if token_type in String:
            offsets.update(start + index for index, char in enumerate(value) if char == "\n")
    return offsets


class DisplayHighlight(Highlight):
    """The pymdownx highlighter, with the docs blank-line rule applied to fenced code."""

    def highlight(
        self,
        src: str,
        language: str,
        css_class: str = "highlight",
        hl_lines: list[int] | None = None,
        linestart: int = -1,
        linestep: int = -1,
        linespecial: int = -1,
        inline: bool = False,
        classes: list[str] | None = None,
        id_value: str = "",
        attrs: dict[str, str] | None = None,
        title: str | None = None,
        code_block_count: int = 0,
    ) -> Any:
        """Shorten each run of blank lines in a fenced block and move its ``hl_lines`` to match."""
        if not inline and not self._shows_line_numbers(linestart):
            shown = display_code(src, self._block_lexer(src, language))
            src = shown.text
            # superfences hands over hl_lines already parsed into source line
            # numbers; translate them so the same code stays highlighted.
            if hl_lines:
                hl_lines = shown.display_lines(hl_lines)
        return super().highlight(
            src,
            language,
            css_class,
            hl_lines=hl_lines,
            linestart=linestart,
            linestep=linestep,
            linespecial=linespecial,
            inline=inline,
            classes=classes,
            id_value=id_value,
            attrs=attrs,
            title=title,
            code_block_count=code_block_count,
        )

    def _shows_line_numbers(self, linestart: int) -> bool:
        # The same test pymdownx applies before drawing line numbers: a global
        # linenums setting, or a per-fence linenums="N".
        return bool((self.linenums and linestart != 0) or (self.linenums is not False and linestart > 0))

    def _block_lexer(self, src: str, language: str) -> Lexer | None:
        # Ask for the lexer pymdownx itself will use, so a fence without a
        # language, a name mapped through extend_pygments_lang, or default_lang
        # reaches the same answer as the colouring.
        if not self.use_pygments:
            return _lexer_for(language or self.default_lang)
        lexer, _name = self.get_lexer(src, language or self.default_lang, False, self.stripnl)  # noqa: FBT003
        return lexer


class DisplayHighlightExtension(HighlightExtension):
    """
    ``pymdownx.highlight`` that hands fenced code to ``DisplayHighlight``.

    superfences asks the registered highlight extension for its highlighter
    class, so swapping this extension in reaches every fenced block, including
    blocks expanded from ``--8<--`` snippet includes and ``<c-include-file>``.
    An indented code block has no language, so it is shown as plain text and
    keeps its blank lines either way.
    """

    def get_pymdownx_highlighter(self) -> type[Highlight]:
        """Return the highlighter class superfences instantiates for each block."""
        return DisplayHighlight


__all__ = [
    "COLLAPSED_LANGUAGES",
    "DisplayCode",
    "DisplayHighlight",
    "DisplayHighlightExtension",
    "display_code",
    "display_code_for_language",
    "highlight_for_display",
    "language_collapses",
    "lexer_collapses",
]
