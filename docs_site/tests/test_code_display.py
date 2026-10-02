"""The docs site shows code with each run of blank lines shortened to one."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from lxml import html as lxml_html
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from docs_site._internal.code_display import display_code, highlight_for_display, language_collapses
from docs_site._internal.components.landing import _tour_code
from docs_site._internal.config import DocsConfig
from docs_site._internal.pipeline import render_page

if TYPE_CHECKING:
    from pathlib import Path

    from pygments.lexer import Lexer

# Two top-level definitions the way ruff formats them, with a whitespace-only
# line in the middle of the second run to prove it also counts as blank.
_FORMATTED = "import os\n\n\nclass First:\n    pass\n\n  \n\ndef second():\n    return os\n"
_SHOWN = "import os\n\nclass First:\n    pass\n\ndef second():\n    return os\n"
_PYTHON = get_lexer_by_name("python")


def _code_blocks(html: str) -> list[str]:
    """Return the visible text of every rendered code block."""
    document = lxml_html.fragment_fromstring(html, create_parent="div")
    return [code.text_content() for code in document.xpath(".//pre/code")]


def test_display_code_keeps_one_blank_line_from_each_run() -> None:
    shown = display_code(_FORMATTED, _PYTHON)

    assert shown.text == _SHOWN
    # Source line 4 (`class First:`, after the first run) is displayed as line 3.
    assert shown.display_line(4) == 3
    assert shown.display_line(9) == 6
    # Dropped blank lines point at the blank line kept from their run.
    assert shown.display_line(3) == shown.display_line(2) == 2
    assert shown.display_lines([6, 7, 8]) == [5]


@pytest.mark.parametrize("lexer", [None, get_lexer_by_name("text")])
def test_display_code_without_collapsing_maps_every_line_to_itself(lexer: Lexer | None) -> None:
    shown = display_code(_FORMATTED, lexer)

    assert shown.text == _FORMATTED
    assert shown.display_lines(range(1, 10)) == list(range(1, 10))


def test_line_numbers_outside_the_source() -> None:
    shown = display_code("a\n\n\nb", _PYTHON)

    # display_line clamps a number outside the block so a bad range still
    # lands somewhere visible.
    assert shown.display_line(0) == 1
    assert shown.display_line(99) == 3
    # hl_lines past the end are dropped, as Pygments drops them.
    assert shown.display_lines([4, 5, 99]) == [3]


@pytest.mark.parametrize(
    ("language", "source"),
    [
        ("python", 'TEXT = """\nfirst\n\n\nsecond\n"""\n'),
        ("citry", 'class C:\n    template = """\n      <p></p>\n\n\n      <p></p>\n    """\n'),
        ("javascript", "const text = `first\n\n\nsecond`;\n"),
    ],
)
def test_blank_lines_inside_strings_are_kept(language: str, source: str) -> None:
    # A blank line inside a string is part of its value, so copying or running
    # the displayed code must give the same string.
    assert display_code(source, get_lexer_by_name(language)).text == source


@pytest.mark.parametrize("language", ["python", "py", "citry", "citry-html", "html", "js", "css", "json"])
def test_code_languages_collapse(language: str) -> None:
    assert language_collapses(language)


@pytest.mark.parametrize("language", ["text", "console", "diff", "markdown", "yaml", "fluent", "", "no-such-lexer"])
def test_languages_with_meaningful_blank_lines_do_not_collapse(language: str) -> None:
    assert not language_collapses(language)


def test_markdown_fence_displays_single_blank_lines() -> None:
    result = render_page(f"```python\n{_FORMATTED}```\n", wrap_in_layout=False)

    assert _code_blocks(result.html) == [_SHOWN]
    # The Markdown companion keeps the source's blank lines as written.
    assert "import os\n\n\nclass First:" in result.markdown_body


@pytest.mark.parametrize("language", ["text", "console", "diff", "markdown"])
def test_excluded_fence_keeps_its_blank_lines(language: str) -> None:
    body = "first\n\n\nsecond\n"
    result = render_page(f"```{language}\n{body}```\n", wrap_in_layout=False)

    assert _code_blocks(result.html) == [body]


def test_hl_lines_still_mark_the_source_lines_they_name() -> None:
    # hl_lines are written against the source: line 4 is `class First:` and
    # line 9 is `def second():`, both below a run of blank lines.
    result = render_page(f'```python hl_lines="4 9"\n{_FORMATTED}```\n', wrap_in_layout=False)

    document = lxml_html.fragment_fromstring(result.html, create_parent="div")
    marked = [span.text_content().strip() for span in document.xpath('.//span[@class="hll"]')]
    assert marked == ["class First:", "def second():"]


def test_hl_lines_past_the_end_mark_nothing() -> None:
    result = render_page('```python hl_lines="7-9"\na\n\n\nb\n```\n', wrap_in_layout=False)

    assert 'class="hll"' not in result.html


def test_fence_with_line_numbers_keeps_source_numbering() -> None:
    # Shown numbers must match the file, so the blank lines stay.
    body = "import os\n\n\nclass First:\n    pass\n"
    result = render_page(f'```python linenums="1"\n{body}```\n', wrap_in_layout=False)

    assert _code_blocks(result.html) == [body]


def test_snippet_include_collapses_without_touching_the_file(tmp_path: Path) -> None:
    (tmp_path / "snippet.py").write_text(_FORMATTED, encoding="utf-8")
    cfg = DocsConfig(repo_root=tmp_path, content_dir=tmp_path, site_dir=tmp_path / "site")

    included = render_page('```python\n--8<-- "snippet.py"\n```\n', config=cfg, wrap_in_layout=False)
    tagged = render_page('<c-include-file path="snippet.py" />\n', config=cfg, wrap_in_layout=False)

    assert _code_blocks(included.html) == [_SHOWN]
    assert _code_blocks(tagged.html) == [_SHOWN]
    assert (tmp_path / "snippet.py").read_text(encoding="utf-8") == _FORMATTED


def test_highlight_for_display_follows_the_lexer_language() -> None:
    formatter = HtmlFormatter(nowrap=True)

    collapsed = highlight_for_display("a\n\n\nb\n", get_lexer_by_name("citry"), formatter)
    kept = highlight_for_display("a\n\n\nb\n", get_lexer_by_name("text"), formatter)

    assert re.sub(r"<[^>]+>", "", collapsed) == "a\n\nb\n"
    assert re.sub(r"<[^>]+>", "", kept) == "a\n\n\nb\n"


def test_walkthrough_ranges_follow_their_lines_past_removed_blanks() -> None:
    stops = (
        {"id": "first", "lines": (4, 5)},
        {"id": "second", "lines": (9, 10)},
    )

    html = _tour_code(_FORMATTED, stops)

    document = lxml_html.fragment_fromstring(html, create_parent="div")
    for stop_id, expected in (("first", ["class First:", "pass"]), ("second", ["def second():", "return os"])):
        lines = document.xpath(f'.//span[@data-tour="{stop_id}"]')
        assert [line.text_content().strip() for line in lines] == expected
        # The marker dot sits on the first line of the range.
        assert lines[0].get("data-tour-start") is not None
    rendered = [line.text_content() for line in document.xpath('.//span[contains(@class, "landing-tour__line")]')]
    assert rendered == _SHOWN.splitlines()
