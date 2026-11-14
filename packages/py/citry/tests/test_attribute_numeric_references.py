"""
Numeric character references in a ``Markup`` attribute value.

When an app passes a ``Markup`` value to an attribute, Citry decodes its HTML
to the text a browser reads and writes that text, escaped. A browser decodes
a numeric reference by the HTML standard's rule, which keeps code points that
Python's ``html.unescape`` drops, such as U+0001 and U+FDD0. These tests check
that Citry writes the value the browser reads from the ``Markup`` itself, and
that Citry's own HTML parsers read attribute values the same way.
"""

from __future__ import annotations

import functools
import html
import re
import sys
from typing import Any

import pytest

import citry.util.html as html_util
from citry import Citry, Component, Markup
from citry._page_ids import _IdScanner
from citry._vue.serialization import _HostValidator, _PreloadHeadLocator
from citry.attrs import normalize_class, normalize_style
from citry.serialize import _PreparedMarkupTracker
from citry.util.html import (
    LongReferenceSafeParser,
    bound_long_decimal_references,
    decode_attribute_entities,
    escape_attribute_value,
)

from ._render_paths import render_both

# The value Chromium 156 and Firefox 157 read from title="a&#xN;b", one row
# per code point, next to what html.unescape reads. Both browsers read every
# row the same way: each browser loaded a page with these titles, and the
# values are the ones it returned.
BROWSER_READS = [
    # (code point, the browser's value, html.unescape's value)
    (0x01, "a\x01b", "ab"),
    (0x08, "a\x08b", "ab"),
    (0x0B, "a\x0bb", "ab"),
    (0x0E, "a\x0eb", "ab"),
    (0x1F, "a\x1fb", "ab"),
    (0x7F, "a\x7fb", "ab"),
    (0xFDD0, "a\ufdd0b", "ab"),
    (0xFDEF, "a\ufdefb", "ab"),
    (0xFFFE, "a\ufffeb", "ab"),
    (0xFFFF, "a\uffffb", "ab"),
    (0x1FFFE, "a\U0001fffeb", "ab"),
    (0x10FFFF, "a\U0010ffffb", "ab"),
    # Rows where the two already agree, kept so the table shows the whole rule.
    (0x09, "a\tb", "a\tb"),
    (0x80, "a\u20acb", "a\u20acb"),
    (0x81, "a\x81b", "a\x81b"),
    (0x9F, "a\u0178b", "a\u0178b"),
    (0xA0, "a\xa0b", "a\xa0b"),
    (0x00, "a\ufffdb", "a\ufffdb"),
    (0xD800, "a\ufffdb", "a\ufffdb"),
    (0x110000, "a\ufffdb", "a\ufffdb"),
]

# The rows where ``html.unescape`` reads something other than the browser,
# which is where the parser would give a wrong value without this change.
DROPPED_BY_UNESCAPE = [row for row in BROWSER_READS if row[1] != row[2]]


@pytest.mark.parametrize(
    ("code_point", "browser", "unescaped"), BROWSER_READS, ids=lambda v: f"{v:#x}" if isinstance(v, int) else ""
)
def test_a_markup_attribute_value_decodes_as_the_browser_reads_it(
    code_point: int, browser: str, unescaped: str
) -> None:
    source = f"a&#x{code_point:x};b"
    # The table records the difference this decoder exists to avoid.
    assert html.unescape(source) == unescaped
    assert decode_attribute_entities(source) == browser
    # The decimal form reads the same.
    assert decode_attribute_entities(f"a&#{code_point};b") == browser
    # The written value holds the character itself, which the browser reads
    # back unchanged (a raw U+0000 would read as U+FFFD, so NUL is never
    # written: its reference already decodes to U+FFFD).
    assert escape_attribute_value(Markup(source)) == browser  # noqa: S704 - a fixed test reference


def test_a_class_or_style_markup_piece_keeps_the_code_point() -> None:
    assert normalize_class([Markup("a&#1;b"), "c"]) == "a\x01b c"
    assert normalize_style({"content": Markup("'a&#xfdd0;b'")}) == "content: 'a\ufdd0b';"
    assert normalize_style([Markup("content: 'a&#1;b'")]) == "content: 'a\x01b';"


def _attributes(source: str, *chunks: str) -> list[list[tuple[str, str | None]]]:
    """
    Feed ``source``, then each of ``chunks``, to a ``LongReferenceSafeParser`` subclass.

    Returns the attributes it receives for each start tag.
    """
    seen: list[list[tuple[str, str | None]]] = []

    class Recorder(LongReferenceSafeParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            seen.append(attrs)

        def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            # The start tag handler is wrapped too, and must pass on the
            # values it is given here rather than decode them again.
            self.handle_starttag(tag, [*attrs, ("seen-by", "startend")])

    parser = Recorder()
    for chunk in (source, *chunks):
        parser.feed(chunk)
    parser.close()
    return seen


@pytest.mark.parametrize(("code_point", "browser", "unescaped"), DROPPED_BY_UNESCAPE)
def test_the_citry_parser_reads_attribute_values_as_the_browser_does(
    code_point: int, browser: str, unescaped: str
) -> None:
    del unescaped
    reference = f"a&#x{code_point:x};b"
    assert _attributes(f"<p title=\"{reference}\" data-x='{reference}' id={reference}>") == [
        [("title", browser), ("data-x", browser), ("id", browser)]
    ]
    assert _attributes(f'<br title="{reference}"/>') == [[("title", browser), ("seen-by", "startend")]]


def test_the_citry_parser_reads_named_and_long_references_and_split_chunks() -> None:
    long_j = "&#" + "0" * 5000 + "106;"
    assert _attributes(f'<p title="{long_j}&#1;" hidden>') == [[("title", "j\x01"), ("hidden", None)]]
    # A legacy name without ";" stays as typed before "=", as in the browser.
    assert _attributes('<a href="?a=1&copy=2&amp;b">') == [[("href", "?a=1&copy=2&b")]]
    # The tag arrives in pieces, and after a long reference earlier in the input.
    assert _attributes(f'<b>{long_j}</b><p title="a&#', '1;b">') == [[], [("title", "a\x01b")]]


@pytest.mark.parametrize(
    "chunks",
    [
        # Some feeds parse nothing, and recent Python releases then buffer
        # them inside ``HTMLParser``.
        ("<p", " ", 'id="&#1;"', "><p", " id", "=", '"&#2;">'),
        tuple('<p id="&#1;"><p id="&#2;">'),
    ],
    ids=["small-pieces", "one-character-each"],
)
def test_each_tag_gets_its_own_values_however_the_input_is_split(chunks: tuple[str, ...]) -> None:
    assert _attributes(*chunks) == [[("id", "\x01")], [("id", "\x02")]]


def test_a_subclass_of_a_subclass_and_a_handler_called_by_hand_keep_their_values() -> None:
    seen: list[tuple[str, list[tuple[str, str | None]]]] = []

    class Base(LongReferenceSafeParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            seen.append((tag, attrs))

    class Child(Base):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            # A changed list passed to the parent must reach it unchanged.
            super().handle_starttag(tag, [(name, f"<{value}>") for name, value in attrs])

        def handle_data(self, data: str) -> None:
            # A call made outside a start tag gets exactly what it passes.
            self.handle_starttag("span", [("title", data)])

    parser = Child()
    parser.feed('<p title="&#1;">x')
    parser.close()
    assert seen == [("p", [("title", "<\x01>")]), ("span", [("title", "<x>")])]


def test_feeding_after_close_keeps_the_original_text_aligned() -> None:
    seen: list[list[tuple[str, str | None]]] = []

    class Recorder(LongReferenceSafeParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            seen.append(attrs)

    parser = Recorder()
    parser.feed('<p title="&#1;">')
    parser.close()
    parser.feed('<i title="&#x7f;">')
    parser.close()
    assert seen == [[("title", "\x01")], [("title", "\x7f")]]


def test_a_long_reference_in_an_attribute_name_keeps_the_browser_values() -> None:
    # A reference too long for ``html.unescape`` is spelled differently in the
    # text ``HTMLParser`` reads, so the name differs from the original. The
    # values must still be the ones a browser reads, and not fall back to
    # ``HTMLParser``'s, which would read ``a&#1;b`` as ``ab``.
    long_name = "&#" + "0" * 5000 + "1;"
    [attrs] = _attributes(f'<p {long_name}="x" title="a&#1;b">')
    assert attrs == [(bound_long_decimal_references(long_name), "x"), ("title", "a\x01b")]


@pytest.mark.parametrize(
    ("written", "read"),
    [("n{i}&#1;", "n{i}\x01"), ("n{i}", "n{i}")],
    ids=["with-a-reference", "without-one"],
)
def test_input_fed_in_many_chunks_reads_the_same_and_keeps_little_text(written: str, read: str) -> None:
    # Tags each almost as long as a chunk, so about three in four straddle a
    # chunk boundary.
    size = 4096
    source = "".join(f'<p id="{written.format(i=i)}" class="{"x" * 3000}">' for i in range(200))
    seen: list[list[tuple[str, str | None]]] = []

    class Recorder(LongReferenceSafeParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            seen.append(attrs)

    parser = Recorder()
    kept = 0
    for start in range(0, len(source), size):
        parser.feed(source[start : start + size])
        kept = max(kept, sum(len(chunk) for chunk in parser._source))
    parser.close()
    assert [dict(attrs)["id"] for attrs in seen] == [read.format(i=i) for i in range(200)]
    # Text before the tag being read is dropped, so the parser holds about
    # two chunks and not the whole input.
    assert kept < 3 * size


def test_a_parser_that_never_reads_values_keeps_no_text() -> None:
    for parser in (_PreparedMarkupTracker(), _PreloadHeadLocator()):
        for _ in range(20):
            parser.feed('<p id="x">text</p>')
        assert not parser._keeps_source
        assert len(parser._source) == 0


@pytest.mark.parametrize(
    ("written", "hosts"),
    [("app&#1;", 0), ("a&#x70;p", 1), ("app", 1)],
    ids=["kept-code-point", "reference-to-a-letter", "plain"],
)
def test_the_vue_host_check_matches_the_id_the_browser_reads(written: str, hosts: int) -> None:
    validator = _HostValidator("app")
    validator.feed(f'<div id="{written}"></div>')
    validator.close()
    assert validator.count == hosts


def test_a_tag_that_cannot_be_lined_up_gets_the_values_htmlparser_gives(monkeypatch: pytest.MonkeyPatch) -> None:
    source = '<p title="a&#1;b">'
    # A pattern that reads other names than ``HTMLParser`` does, as a later
    # Python's might: pairing the browser's values with those names would be
    # wrong, so the handler keeps what ``HTMLParser`` gives.
    monkeypatch.setattr(html_util, "_ATTRIBUTE", re.compile(r"\s*([a-z])()()"))
    assert _attributes(source) == [[("title", "ab")]]
    # The same when ``HTMLParser`` no longer has the patterns at all.
    monkeypatch.setattr(html_util, "_ATTRIBUTE", None)
    assert _attributes(source) == [[("title", "ab")]]


@pytest.mark.skipif(not hasattr(sys, "set_int_max_str_digits"), reason="this Python has no digit limit to change")
def test_a_tag_split_across_two_digit_limits_gets_the_values_htmlparser_gives() -> None:
    # The first feed rewrites the long reference under a limit of 4,300
    # digits, and the end of the tag arrives under no limit, so the original
    # text no longer rewrites to the text ``HTMLParser`` read.
    long_reference = "&#" + "0" * 4400 + "106;"
    seen: list[list[tuple[str, str | None]]] = []

    class Recorder(LongReferenceSafeParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            seen.append(attrs)

    saved = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(4300)
        parser = Recorder()
        parser.feed(f'<p title="a&#1;b" data-x="{long_reference}"')
        sys.set_int_max_str_digits(0)
        parser.feed(' id="q&#2;">')
        parser.close()
    finally:
        sys.set_int_max_str_digits(saved)
    assert seen == [[("title", "ab"), ("data-x", "j"), ("id", "q")]]


def test_a_handler_reached_through_super_from_a_parser_that_opts_out_gets_the_browser_values() -> None:
    seen: list[list[tuple[str, str | None]]] = []

    class Base(LongReferenceSafeParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            seen.append(attrs)

    class Child(Base):
        _reads_attribute_values = False

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            super().handle_starttag(tag, attrs)

    parser = Child()
    parser.feed('<p title="a&#1;b">')
    parser.close()
    # The child never reads the values, but the parent it calls does, so the
    # parser keeps the original text for it.
    assert seen == [[("title", "a\x01b")]]


def test_a_handler_that_copies_the_marker_of_a_wrapped_one_still_gets_the_browser_values() -> None:
    seen: list[list[tuple[str, str | None]]] = []

    class Base(LongReferenceSafeParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            seen.append(attrs)

    class Child(LongReferenceSafeParser):
        # ``functools.wraps`` copies the attributes of the function it wraps,
        # including the mark that says the browser's values are already wrapped in.
        @functools.wraps(Base.handle_starttag)
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            seen.append(attrs)

    parser = Child()
    parser.feed('<p title="a&#1;b">')
    parser.close()
    assert seen == [[("title", "a\x01b")]]


def test_the_id_check_tells_apart_ids_that_differ_by_a_kept_code_point() -> None:
    scanner = _IdScanner()
    scanner.feed('<p id="a&#1;b"></p><p id="ab"></p><p id="a&#xfdd0;b"></p>')
    scanner.close()
    assert scanner.ids == ["a\x01b", "ab", "a\ufdd0b"]


def _link_page(*, interactive: bool) -> str:
    """Render a link whose title is a ``Markup`` value, on a static or an interactive page."""
    app = Citry(autodiscover=False)

    class StaticLink(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"u": Markup("a&#1;b&#xfdd0;c")}

        template = """
            <main><a c-title="u">x</a></main>
        """

    class LiveLink(StaticLink):
        js = """
            $component({});
        """

    link = LiveLink if interactive else StaticLink
    return str(link().render().serialize())


def test_a_static_and_an_interactive_page_write_the_same_value(monkeypatch: pytest.MonkeyPatch) -> None:
    assert 'title="a\x01b\ufdd0c"' in _link_page(interactive=False)
    rust, python = render_both(lambda: _link_page(interactive=True), monkeypatch, leaves=(1, ()))
    for result in (rust.result, python.result):
        page = str(result)
        assert '"hydrate":true' in page, page[:300]
        assert 'title="a\x01b\ufdd0c"' in page


def test_a_subclass_of_a_parser_that_opts_out_still_gets_the_browser_values() -> None:
    seen: list[list[tuple[str, str | None]]] = []

    class Skips(LongReferenceSafeParser):
        _reads_attribute_values = False

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            seen.append(attrs)

    class Reads(Skips):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            seen.append(attrs)

    for parser in (Skips(), Reads()):
        parser.feed('<p title="a&#1;b">')
        parser.close()
    assert seen == [[("title", "ab")], [("title", "a\x01b")]]
