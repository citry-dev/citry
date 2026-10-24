"""
Numeric character references longer than Python converts to an ``int``.

Python refuses to convert a string of more than 4,300 decimal digits to an
``int``, and ``html.unescape`` converts every decimal reference that way.
A browser reads such a reference without that limit: leading zeros do not
count, and a value past U+10FFFF reads as U+FFFD. Each decoder these tests
cover must read such a reference without raising, as the browser does.

The file also checks that a numeric reference in text keeps the control
characters and noncharacters a browser keeps.
"""

from __future__ import annotations

import html
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any, cast

import pytest

from citry import Citry, Component, Markup
from citry.__main__ import main
from citry._page_ids import _IdScanner
from citry._vue.serialization import _HostValidator, _PreloadHeadLocator
from citry.serialize import _PreparedMarkupTracker
from citry.util.html import (
    LongReferenceSafeParser,
    bound_long_decimal_references,
    decode_attribute_entities,
    decode_character_references,
)

from ._render_paths import render_both

if TYPE_CHECKING:
    from pathlib import Path

# Far more zeros than Python converts; the browser reads the value 106, "j".
ZEROS = "0" * 5000
LONG_J = f"&#{ZEROS}106;"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (LONG_J, "j"),
        (f"&#{ZEROS}106", "j"),
        (f"&#x{ZEROS}6a;", "j"),
        (f"&#{ZEROS};", "\ufffd"),
        # More than seven significant digits is past U+10FFFF.
        ("&#" + "9" * 5000 + ";", "\ufffd"),
        ("&#11141120;", "\ufffd"),
        ("&#x1100000;", "\ufffd"),
        (f"a {LONG_J} b {LONG_J}", "a j b j"),
    ],
)
def test_long_numeric_references_decode_as_the_browser_reads_them(source: str, expected: str) -> None:
    assert decode_character_references(source) == expected
    assert decode_attribute_entities(source) == expected


@pytest.mark.parametrize(
    "source",
    ["&#106;", "&#x6A", "&#1114112;", "&#9999999;", "&#128;", "&#0;", "&#55296;", "&amp; &copy &bogus;"],
)
def test_short_references_decode_as_html_unescape_does(source: str) -> None:
    assert decode_character_references(source) == html.unescape(source)


def test_citry_check_reads_a_long_reference_in_an_attribute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "card.py").write_text(
        "from citry import Citry, Component\n"
        "\n"
        "app = Citry(autodiscover=False)\n"
        "\n"
        "\n"
        "class Card(Component):\n"
        "    citry = app\n"
        '    template = """\n'
        f'        <img role="{LONG_J}" alt="x">\n'
        '    """\n',
        encoding="utf-8",
    )
    try:
        code = main(["check", "--static"])
    except SystemExit as exc:
        code = exc.code
    assert code == 0, capsys.readouterr().err


def _render_markup_text() -> str:
    app = Citry(autodiscover=False)

    class Live(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"text": Markup(LONG_J)}  # noqa: S704 - a fixed test reference

        template = """
            <main><p>{{ text }}</p></main>
        """
        js = """
            $component({});
        """

    return Live().render().serialize()


def test_an_interactive_component_prints_a_long_reference_in_markup(monkeypatch: pytest.MonkeyPatch) -> None:
    rust, _python = render_both(_render_markup_text, monkeypatch)
    page = str(rust.result)
    assert '"hydrate":true' in page, page[:300]
    assert "<p>j</p>" in page


def test_an_authored_attribute_with_a_long_reference_reaches_the_csp_check() -> None:
    app = Citry(autodiscover=False)

    class Card(Component):
        citry = app
        template = f"""
            <a href="{LONG_J}avascript:alert(1)">x</a>
        """

    # The browser reads the URL as `javascript:alert(1)`, which the check refuses.
    with pytest.raises(ValueError, match="a javascript: URL in 'href'"):
        Card().render().serialize(security_csp="strict")


def test_a_markup_attribute_value_with_a_long_reference_reaches_the_csp_check() -> None:
    app = Citry(autodiscover=False)

    class Card(Component):
        citry = app

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"href": Markup(f"{LONG_J}avascript:alert(1)")}  # noqa: S704 - a fixed test reference

        template = """
            <a c-href="href">x</a>
        """

    # The browser reads the URL as `javascript:alert(1)`, which the check refuses.
    with pytest.raises(ValueError, match="a javascript: URL in 'href'"):
        Card().render().serialize(security_csp="strict")


class _Recorder(LongReferenceSafeParser):
    """Record what the parser reports, with the position of each start tag."""

    def __init__(self, *, convert_charrefs: bool) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.events: list[tuple[object, ...]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.events.append(("start", tag, tuple(attrs), self.getpos()))

    def handle_data(self, data: str) -> None:
        self.events.append(("data", data))


class _PlainRecorder(HTMLParser):
    """The same recorder on Python's own parser, for input it can read."""

    def __init__(self, *, convert_charrefs: bool) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.events: list[tuple[object, ...]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.events.append(("start", tag, tuple(attrs), self.getpos()))

    def handle_data(self, data: str) -> None:
        self.events.append(("data", data))


def _parse(parser: LongReferenceSafeParser | HTMLParser, *chunks: str) -> list[tuple[object, ...]]:
    for chunk in chunks:
        parser.feed(chunk)
    parser.close()
    return cast("Any", parser).events


@pytest.mark.parametrize("convert_charrefs", [True, False])
def test_the_parser_reads_a_long_reference_in_an_attribute_and_in_text(convert_charrefs: bool) -> None:
    source = f'<b title="{LONG_J}">a{LONG_J}b</b><i>x</i>'
    events = _parse(_Recorder(convert_charrefs=convert_charrefs), source)
    # The same input with the short reference: equal events, and the <i>
    # starts at the same column, because the rewrite keeps the length.
    short = _parse(_PlainRecorder(convert_charrefs=convert_charrefs), source.replace(LONG_J, "&#106;"))
    assert [event[:3] for event in events] == [event[:3] for event in short]
    assert events[0][2] == (("title", "j"),)
    assert events[-2][3] == (1, len(source) - len("<i>x</i>"))


@pytest.mark.parametrize(
    ("chunks", "title", "text"),
    [
        ((f'<b title="&#{ZEROS[:100]}', f'{ZEROS}106;">x</b>'), "j", "x"),
        # Text that ends in the reference, in one chunk or split around it.
        ((f"<b>x</b>a&#{ZEROS}106",), None, "xaj"),
        ((f"<b>x</b>a&#{ZEROS}106", "<i>y</i>"), None, "xajy"),
        ((f"<b>x</b>a&#{ZEROS}", "106", "<i>y</i>"), None, "xajy"),
    ],
    ids=["attribute-split", "text-at-end", "split-after", "split-inside"],
)
def test_the_parser_reads_a_long_reference_split_across_chunks(
    chunks: tuple[str, ...], title: str | None, text: str
) -> None:
    events = _parse(_Recorder(convert_charrefs=True), *chunks)
    assert "".join(str(event[1]) for event in events if event[0] == "data") == text
    if title is not None:
        assert events[0][2] == (("title", title),)


def test_the_rewrite_keeps_every_position_and_leaves_short_references_alone() -> None:
    source = f"a {LONG_J} &#065; b"
    rewritten = bound_long_decimal_references(source)
    assert len(rewritten) == len(source)
    assert html.unescape(rewritten) == "a j A b"
    assert bound_long_decimal_references("a &#065; b") == "a &#065; b"


@pytest.mark.parametrize("parser", [_IdScanner, _HostValidator, _PreloadHeadLocator, _PreparedMarkupTracker])
def test_every_citry_output_parser_uses_the_long_reference_parser(parser: type) -> None:
    assert issubclass(parser, LongReferenceSafeParser)


def test_a_static_textarea_with_a_long_reference_in_an_attribute_renders() -> None:
    app = Citry(autodiscover=False)

    class Note(Component):
        citry = app
        template = f"""
            <textarea title="{LONG_J}">x</textarea>
        """

    assert "<textarea" in Note().render().serialize()


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        # Control characters and noncharacters stay, as the browser keeps them.
        ("&#127;", "\x7f"),
        ("&#1;&#x8;&#xb;&#x1f;", "\x01\x08\x0b\x1f"),
        ("&#xfdd0;&#xfffe;&#x1ffff;&#1114111;", "\ufdd0\ufffe\U0001ffff\U0010ffff"),
        # 0x80 to 0x9F read as Windows-1252, except the five codes it leaves
        # undefined, which stay.
        ("&#x80;&#x9f;", "\u20ac\u0178"),
        ("&#x81;&#x8d;&#x8f;&#x90;&#x9d;", "\x81\x8d\x8f\x90\x9d"),
        # NUL, a surrogate, and a value past U+10FFFF read as U+FFFD.
        ("&#0;&#xd800;&#x110000;", "\ufffd" * 3),
        ("&#13;", "\r"),
    ],
)
def test_numeric_references_in_text_decode_as_the_browser_reads_them(source: str, expected: str) -> None:
    assert decode_character_references(source) == expected


def test_an_interactive_component_keeps_a_control_character_from_markup(monkeypatch: pytest.MonkeyPatch) -> None:
    # A Markup value without tags becomes text. A static page writes it as is and
    # the browser keeps U+007F and U+FDD0, so the interactive page must too.
    def render_page() -> str:
        app = Citry(autodiscover=False)

        class Live(Component):
            citry = app

            def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
                return {"text": Markup("a&#127;b&#xfdd0;c")}

            template = """
                <main><p>{{ text }}</p></main>
            """
            js = """
                $component({});
            """

        return Live().render().serialize()

    rust, python = render_both(render_page, monkeypatch)
    for result in (rust.result, python.result):
        page = str(result)
        assert '"hydrate":true' in page, page[:300]
        assert "<p>a\x7fb\ufdd0c</p>" in page
