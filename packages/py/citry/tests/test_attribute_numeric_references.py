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

import html
from typing import Any

import pytest

from citry import Citry, Component, Markup
from citry._page_ids import _IdScanner
from citry.attrs import normalize_class, normalize_style
from citry.util.html import LongReferenceSafeParser, decode_attribute_entities, escape_attribute_value

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
    """Return the attributes each start tag in ``source`` gives a subclass of the Citry parser."""
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


@pytest.mark.parametrize(("code_point", "browser", "unescaped"), BROWSER_READS[:12])
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
