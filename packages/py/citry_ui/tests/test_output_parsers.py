"""The citry-ui parsers of rendered output read the HTML as the browser does."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import citry.util.html as html_util
from citry.util.html import LongReferenceSafeParser
from citry_ui.components.caccordion.caccordion import _DirectItemParser
from citry_ui.components.ccommand_palette.ccommand_palette import _VisualParser
from citry_ui.components.cdisclosure.cdisclosure import _ContentOutputParser, _TitleOutputParser
from citry_ui.components.cimage.cimage import _CImageVisualParser
from citry_ui.components.clistbox.clistbox import _ListboxOutputParser
from citry_ui.components.cmenu.cmenu import _DirectMenuParser
from citry_ui.components.ctree.ctree import _TreeOutputParser

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.parametrize(
    "parser",
    [
        _DirectItemParser,
        _VisualParser,
        _ContentOutputParser,
        _TitleOutputParser,
        _CImageVisualParser,
        _ListboxOutputParser,
        _DirectMenuParser,
        _TreeOutputParser,
    ],
)
def test_output_parsers_use_the_long_reference_parser(parser: type) -> None:
    # Python's HTMLParser raises ValueError for a decimal reference with more
    # than 4,300 digits; this base class reads it as the browser does.
    assert issubclass(parser, LongReferenceSafeParser)


@pytest.mark.parametrize("parser", [_DirectMenuParser, _DirectItemParser])
def test_parsers_that_never_read_attribute_values_skip_decoding_them(parser: type[LongReferenceSafeParser]) -> None:
    assert not parser._keeps_source


@pytest.mark.parametrize("extra", ["", " &#" + "0" * 5000 + "1;=x"], ids=["plain", "long-reference-in-a-name"])
def test_the_content_parser_reads_a_popover_value_as_the_browser_does(extra: str) -> None:
    def problem(popover: str) -> str | None:
        parser = _ContentOutputParser(actions=False)
        parser.feed(f'<div popover="{popover}" data-citry-ui-part="hover-card"{extra}>')
        parser.close()
        return parser.problem

    assert problem("manual") is None
    # A browser reads man&#1;ual as "man", U+0001, "ual", which is not "manual".
    assert problem("man&#1;ual") == "raw or unrecognized native popovers are not accepted"


def _verdict(parser: LongReferenceSafeParser, html: str) -> object:
    """Feed ``html`` to ``parser`` and return what it decided: its problem, or whether it found the HTML invalid."""
    parser.feed(html)
    parser.close()
    return getattr(parser, "problem", None) or getattr(parser, "invalid", None)


# Each case repeats one attribute: the first value is one the check refuses
# and the second one it accepts. A browser keeps the first value, so the
# check must refuse the tag, and must accept it with the values swapped.
REPEATED_ATTRIBUTE_CASES = {
    "disclosure-popover": (
        lambda: _ContentOutputParser(actions=False),
        '<div popover="{}" popover="{}" data-citry-ui-part="hover-card">',
        ("auto", "manual"),
    ),
    "disclosure-title-alt": (_TitleOutputParser, '<img alt="{}" alt="{}">x', ("Logo", "")),
    "image-contenteditable": (
        _CImageVisualParser,
        '<div data-citry-ui-part="placeholder"><span contenteditable="{}" contenteditable="{}">',
        ("", "false"),
    ),
    "listbox-tabindex": (
        _ListboxOutputParser,
        '<div data-cui-listbox-slot-region><span tabindex="{}" tabindex="{}">',
        ("0", "-1"),
    ),
    "tree-part": (
        _TreeOutputParser,
        '<ul data-citry-ui-part="tree"><li data-citry-ui-part="{}" data-citry-ui-part="{}">',
        ("row", "item"),
    ),
    "command-palette-alt": (
        _VisualParser,
        '<div data-citry-command-palette-visual><img alt="{}" alt="{}">',
        ("Logo", ""),
    ),
}


@pytest.mark.parametrize(
    ("make_parser", "template", "values"),
    list(REPEATED_ATTRIBUTE_CASES.values()),
    ids=list(REPEATED_ATTRIBUTE_CASES),
)
@pytest.mark.parametrize("core_keeps_first", [True, False], ids=["current-citry", "older-citry"])
def test_output_parsers_read_a_repeated_attribute_as_its_first_value(
    make_parser: Callable[[], LongReferenceSafeParser],
    template: str,
    values: tuple[str, str],
    core_keeps_first: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not core_keeps_first:
        # Citry UI also runs on Citry releases whose parser hands over every
        # occurrence, so its checks must keep the first value themselves.
        monkeypatch.setattr(html_util, "_first_attribute_occurrences", lambda attrs: attrs)
    refused, accepted = values
    assert _verdict(make_parser(), template.format(refused, accepted))
    assert not _verdict(make_parser(), template.format(accepted, refused))


@pytest.mark.parametrize(
    ("make_parser", "html"),
    [
        (_TitleOutputParser, "<x\x1b>"),
        (lambda: _ContentOutputParser(actions=False), "<x-\x1b>"),
        (_ListboxOutputParser, "<p\x1b>"),
        (_ListboxOutputParser, '<div data-cui-listbox-slot-region><p\x1b role="option">'),
        (_TreeOutputParser, '<ul data-citry-ui-part="tree"><p\x1b>'),
    ],
    ids=["title-element", "custom-element", "listbox-structure", "listbox-option", "tree"],
)
def test_output_parser_messages_show_control_characters_in_tag_names_as_escapes(
    make_parser: Callable[[], LongReferenceSafeParser], html: str
) -> None:
    # Written as it is, ESC in the message would reach the developer's terminal.
    problem = _verdict(make_parser(), html)
    assert isinstance(problem, str)
    assert "\\x1b" in problem
    assert "\x1b" not in problem
