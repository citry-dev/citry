"""The citry-ui parsers of rendered output read the HTML as the browser does."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import citry.util.html as html_util
from citry.util.html import LongReferenceSafeParser
from citry_ui.components._markup_tree import MarkupTreeParser
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
def test_output_parsers_follow_the_elements_a_browser_keeps_open(parser: type) -> None:
    # The shared base reads SVG and MathML content and end tags as a browser does.
    assert issubclass(parser, MarkupTreeParser)


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


# Each fill puts an element inside the checked region of the page in
# Chromium, Firefox and WebKit, where the check must refuse it. Python's
# HTMLParser alone reads the first group as text and closes the region early
# on the second.
HIDDEN_CONTENT = {
    "svg-style": "<svg><style><g tabindex=0></g></style></svg>",
    "svg-style-breakout": "<svg><style><span tabindex=0>x</span></style></svg>",
    "math-style": "<math><style><b tabindex=0>x</b></style></math>",
    "svg-script": "<svg><script><a href='#' tabindex=0>x</a></script></svg>",
    "html-cdata": "<span><![CDATA[ x><b tabindex=0>y</b>]]></span>",
    "void-end-tag": "<span><link></link></span><b tabindex=0>x</b>",
    "img-end-tag": "<span></img></span><b tabindex=0>x</b>",
    "self-closing-span": "<span><span/></span></span><b tabindex=0>x</b>",
    "form-end-tag": "<form><span></form></span><b tabindex=0>x</b>",
    # With scripting on, the browser reads ``</span>`` here as text.
    "noscript": "<noscript></span></noscript><b>x</b>",
}

# Fills the browser reads as text or shapes only, which the checks must keep
# accepting: a styled SVG icon, and ``<style>`` where SVG holds HTML.
HARMLESS_CONTENT = {
    "svg-icon": "<svg viewBox='0 0 1 1'><style>.a{fill:red}</style><path d='M0 0'/></svg>",
    "foreign-object-style": "<svg><foreignObject><style><b tabindex=0></b></style></foreignObject></svg>",
    "math-text-style": "<math><mi><style><b tabindex=0></b></style></mi></math>",
}

REGION_CHECKS = {
    "image": (_CImageVisualParser, '<span data-citry-ui-part="placeholder">{}</span>'),
    "command-palette": (
        _VisualParser,
        "<div data-citry-command-palette-host><dialog data-citry-command-palette-root>"
        "<span data-citry-command-palette-visual>{}</span></dialog></div>",
    ),
    "listbox": (
        _ListboxOutputParser,
        '<div data-citry-ui-part="listbox-root"><div data-citry-ui-part="listbox">'
        '<div data-citry-ui-part="listbox-option"><span data-citry-ui-part="listbox-option-start"'
        " data-cui-listbox-slot-region>{}</span></div></div></div>",
    ),
}


@pytest.mark.parametrize("fill", list(HIDDEN_CONTENT.values()), ids=list(HIDDEN_CONTENT))
@pytest.mark.parametrize(("make_parser", "template"), list(REGION_CHECKS.values()), ids=list(REGION_CHECKS))
def test_region_checks_refuse_focusable_content_the_browser_puts_in_the_region(
    make_parser: Callable[[], LongReferenceSafeParser], template: str, fill: str
) -> None:
    assert _verdict(make_parser(), template.format(fill))


@pytest.mark.parametrize("fill", list(HARMLESS_CONTENT.values()), ids=list(HARMLESS_CONTENT))
@pytest.mark.parametrize(("make_parser", "template"), list(REGION_CHECKS.values()), ids=list(REGION_CHECKS))
def test_region_checks_accept_content_the_browser_reads_as_text(
    make_parser: Callable[[], LongReferenceSafeParser], template: str, fill: str
) -> None:
    assert not _verdict(make_parser(), template.format(fill))


def test_a_check_keeps_the_region_open_past_an_end_tag_a_table_cell_hides() -> None:
    # A browser ignores ``</span>`` inside the cell, so the button stays in the fill.
    html = '<span data-citry-ui-part="placeholder"><table><tr><td></span><button>x</button></td></tr></table></span>'
    assert _verdict(_CImageVisualParser(), html)


@pytest.mark.parametrize(
    "fill",
    ["<svg><style><dialog open></dialog></style></svg>", "<div><![CDATA[ x><div popover>y</div>]]></div>"],
    ids=["svg-style", "html-cdata"],
)
def test_the_disclosure_content_check_sees_elements_inside_svg_style_and_cdata(fill: str) -> None:
    assert _verdict(_ContentOutputParser(actions=False), fill)


def test_the_disclosure_title_check_sees_elements_after_html_cdata() -> None:
    assert _verdict(_TitleOutputParser(), "Title<![CDATA[ x><b tabindex=0>y</b>]]>") == ("<b> cannot use 'tabindex'")


def _direct_items(*items: str) -> object:
    """Feed each item's HTML as a declared CAccordion item and return the parser's verdict."""
    parser = _DirectItemParser()
    for index, item in enumerate(items):
        parser.enter_item(f"r{index}")
        parser.feed_text(item)
        parser.exit_item(f"r{index}")
    parser.flush()
    parser.close()
    return parser.invalid


def test_direct_item_check_counts_the_roots_a_browser_builds() -> None:
    assert not _direct_items("<div>a</div>", "<div>b</div>")
    # Inside SVG ``<style>``, ``</div>`` closes the SVG and the item's root,
    # and the ``<div>`` after it is a second root.
    assert _direct_items("<div><svg><style></div><div></style></svg></div>")
    # ``</form>`` closes only the form, so the item's root stays open and
    # the next item would sit inside it.
    assert _direct_items("<div><form><div></form></div>", "<div>b</div>")
    # ``</link>`` closes nothing in a browser.
    assert not _direct_items("<div><link></link>a</div>")
    # An end tag that closes nothing inside the item could close an element
    # around the collection.
    assert _direct_items("<div>a</div></section>")


def test_direct_menu_check_counts_the_roots_a_browser_builds() -> None:
    def invalid(html: str) -> object:
        parser = _DirectMenuParser({"r0": "div"})
        parser.enter("r0")
        parser.feed_text(html)
        parser.exit("r0")
        parser.flush()
        parser.close()
        return parser.invalid

    assert not invalid("<div><img></img>a</div>")
    assert invalid("<div><svg><style></div><div></style></svg></div>")


def test_direct_menu_check_sees_a_nested_button_or_link_close_the_root() -> None:
    def invalid(tag: str, html: str) -> object:
        parser = _DirectMenuParser({"r0": tag})
        parser.enter("r0")
        parser.feed_text(html)
        parser.exit("r0")
        parser.flush()
        parser.close()
        return parser.invalid

    assert not invalid("button", "<button><span>x</span></button>")
    # A browser closes the open button before a new one, and the open link
    # before a new link, so each fill builds two roots.
    assert invalid("button", "<button>x<button>y</button></button>")
    assert invalid("a", "<a href='#'>x<a href='#'>y</a></a>")
