"""
Shape source code for display on the docs site.

Python formatters such as ruff put two blank lines between top-level
definitions. That is the right layout for a source file, but in a narrow docs
column the second blank line only pushes the example further down the page.
Every code block the site renders therefore passes its source through
``display_code`` first, which shortens each run of two or more blank lines to a
single blank line. The source files on disk stay formatted as they are, and
executed examples run from those files, so this changes only what a reader
sees (and what the copy button copies, since it copies the displayed text).

Some languages give blank lines meaning, so the rule applies only to the
languages in ``COLLAPSED_LANGUAGES``. Diffs (blank context lines), console and
plain-text output, Markdown, YAML and Fluent (blank lines inside block values),
and anything unrecognised keep their blank lines exactly.

Line numbers written against the source file (a Markdown fence's ``hl_lines``,
the landing walkthrough's line ranges) are translated with
``DisplayCode.display_line`` so they still point at the same code after the
blank lines are removed. A block that shows line numbers keeps every blank line,
because its numbers must match the file a reader may open beside it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from pymdownx.highlight import Highlight, HighlightExtension

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pygments.formatter import Formatter
    from pygments.lexer import Lexer

# Pygments' primary alias for each language whose blank lines carry no meaning
# outside string literals. A language joins this set only after checking that
# collapsing cannot change what a reader would copy and run in a way that
# matters; the module docstring lists the languages left out and why.
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
        """Return the displayed line for a 1-based source line number."""
        # A number past the end (an off-by-one in an author's range, or a
        # trailing newline counted as a line) still has to land somewhere
        # visible, so it clamps to the last displayed line.
        if not self.line_map:
            return source_line
        index = min(max(source_line, 1), len(self.line_map)) - 1
        return self.line_map[index]

    def display_lines(self, source_lines: Iterable[int]) -> list[int]:
        """Translate source line numbers, dropping duplicates but keeping their order."""
        # Two removed blank lines map to the same kept line; listing it twice
        # would be harmless to Pygments but noisy for any other consumer.
        seen: dict[int, None] = {}
        for line in source_lines:
            seen.setdefault(self.display_line(line), None)
        return list(seen)


def language_collapses(language: str) -> bool:
    """Return whether a code block in ``language`` should lose its extra blank lines."""
    # Resolve the name through Pygments so every alias a page may use (py,
    # python3, js) reaches the same decision as the lexer that colours it.
    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        return False
    return lexer_collapses(lexer)


def lexer_collapses(lexer: Lexer) -> bool:
    """Return whether code coloured by ``lexer`` should lose its extra blank lines."""
    return bool(COLLAPSED_LANGUAGES.intersection(lexer.aliases))


def display_code(source: str, *, collapse: bool = True) -> DisplayCode:
    """
    Shorten every run of two or more blank lines in ``source`` to one.

    A line holding only spaces or tabs counts as blank, because it looks blank
    on the page. The first line of each run is the one kept. With
    ``collapse=False`` the text is returned unchanged with an identity line map,
    so callers can treat every block the same way.
    """
    # A trailing newline ends the last line rather than starting an empty one;
    # set it aside so it is neither counted as a line nor merged into a run.
    body, ending = (source[:-1], "\n") if source.endswith("\n") else (source, "")
    lines = body.split("\n")
    if not collapse:
        return DisplayCode(text=source, line_map=tuple(range(1, len(lines) + 1)))

    kept: list[str] = []
    line_map: list[int] = []
    previous_blank = False
    for line in lines:
        blank = not line.strip()
        if blank and previous_blank:
            # The extra blank line is dropped and points at the one already kept.
            line_map.append(len(kept))
            continue
        kept.append(line)
        line_map.append(len(kept))
        previous_blank = blank
    return DisplayCode(text="\n".join(kept) + ending, line_map=tuple(line_map))


def highlight_for_display(source: str, lexer: Lexer, formatter: Formatter[Any]) -> str:
    """
    Colour ``source`` with Pygments after shaping it for display.

    Components that render a code block themselves (live examples, example
    cards, component previews, the landing page) call this instead of
    ``pygments.highlight`` so they follow the same blank-line rule as Markdown
    fences.
    """
    shown = display_code(source, collapse=lexer_collapses(lexer)).text
    return highlight(shown, lexer, formatter)


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
        """Collapse blank lines in a block and move its ``hl_lines`` with them."""
        if not inline and not self._shows_line_numbers(linestart) and self._collapses(src, language):
            shown = display_code(src)
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

    def _collapses(self, src: str, language: str) -> bool:
        # Ask for the lexer pymdownx itself will use, so a fence without a
        # language, an extended alias, or default_lang reaches the same answer.
        if not self.use_pygments:
            return language_collapses(language or self.default_lang)
        lexer, _name = self.get_lexer(src, language or self.default_lang, False, self.stripnl)  # noqa: FBT003
        return lexer_collapses(lexer)


class DisplayHighlightExtension(HighlightExtension):
    """
    ``pymdownx.highlight`` that hands fenced code to ``DisplayHighlight``.

    superfences asks the registered highlight extension for its highlighter
    class, so swapping this extension in reaches every fenced block, including
    blocks expanded from ``--8<--`` snippet includes and ``<c-include-file>``.
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
    "highlight_for_display",
    "language_collapses",
    "lexer_collapses",
]
