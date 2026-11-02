"""A `css_data()` value is checked token by token, so it cannot end its declaration or its `<style>` element."""

from __future__ import annotations

import io
import random
import string
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component
from citry.contrib.wsgi import wsgi_app
from citry.util.css import _escape_beyond_printable_ascii, serialize_css_var_value, validate_css_var_value

if TYPE_CHECKING:
    from collections.abc import Callable


def _render_with_css_value(value: str) -> str:
    """Render a component whose `css_data()` returns `value`, to prove the check also runs when a page renders."""
    app = Citry()

    class Widget(Component):
        citry = app
        template = """
            <span class="w">w</span>
        """
        css = """
            .w { color: var(--x); }
        """

        def css_data(self, kwargs, slots):
            return {"x": value}

    return str(Widget())


def _implementation_accepts(value: str) -> bool:
    try:
        validate_css_var_value(value)
    except ValueError:
        return False
    return True


# Each case is (value, a short stable fragment of the refusal message).
# Values the check must refuse; `b{c:d}` stands in for a second rule.
_REFUSED_VALUES = {
    # Characters not allowed in an unquoted url().
    "double_quote_in_url": ('url(a"x)y;b{c:d}z")', r"url\(\)"),
    "single_quote_in_url": ("url(a'x)y;b{c:d}z')", r"url\(\)"),
    "comment_in_url": ("url(a/*x)y;b{c:d}z*/)", "top-level ';'"),
    "semicolon_then_rule": ("red;b{c:d}", "top-level ';'"),
    "style_end_tag": ("</style>b{c:d}", "</style"),
    "style_end_tag_upper": ("</STYLE>b{c:d}", "</style"),
    "style_end_tag_mixed_case": ("</StYlE>b{c:d}", "</style"),
    "colon_semicolon_rule": ("x:1;b{c:d}", "top-level ';'"),
    # The style element's end tag and comment start are refused in every token,
    # in any letter case.
    "style_end_tag_in_string": ('"</style>"', "</style"),
    "style_end_tag_in_string_upper": ('"</STYLE>"', "</style"),
    "style_end_tag_in_quoted_url": ('url("</style>")', "</style"),
    "style_end_tag_in_quoted_url_mixed_case": ('url("</StYlE>")', "</style"),
    "style_end_tag_in_unquoted_url": ("url(</style>)", "</style"),
    "style_end_tag_in_unquoted_url_upper": ("url(</STYLE>)", "</style"),
    "comment_start_marker": ("<!--", "<!--"),
    "comment_start_marker_in_string": ('"<!--"', "<!--"),
    "comment_start_marker_in_url": ("url(<!--)", "<!--"),
    # A backslash outside a string is refused, so every name in a value reads as written.
    "backslash_between_names": ("a\\b", "backslash"),
    "backslash_spelling_url": ("\\75rl(a;b)", "backslash"),
    "backslash_at_the_end": ("red\\", "backslash"),
    "backslash_after_url_name": ("url\\(a)", "backslash"),
    # A null or surrogate character is refused wherever it sits.
    "null_character": ("a\x00b", "null character"),
    "lone_surrogate": ("a\ud800b", "surrogate"),
    # Other single-token refusals.
    "plain_comment": ("a/**/b", "comment"),
    "unclosed_comment": ("red/*", "comment"),
    "open_brace": ("a{b", r"'\{'"),
    "closing_brace": ("red}", r"'\}'"),
    "important_flag": ("red!important", "top-level '!'"),
    "top_level_semicolon": ("a;b", "top-level ';'"),
    "bare_less_than": ("a<b", "'<'"),
    "unclosed_paren": ("calc(1", "unclosed"),
    "unmatched_close": ("1)", "unmatched"),
    "crossed_brackets": ("([)]", "closes the block"),
    "unclosed_string": ('"abc', "unclosed"),
    "newline_in_string": ('f("a\nb")', "newline"),
    "unclosed_url": ("url(a;b", "unclosed"),
    # An unquoted url() token is read up to its own closing parenthesis.
    "paren_in_unquoted_url": ("url(a(b)", r"url\(\)"),
    "space_in_unquoted_url": ("url(a b)", r"url\(\)"),
    "quote_in_unquoted_url": ("url(a'b)", r"url\(\)"),
    # The control characters an unquoted url() refuses, at both ends of each range.
    "backspace_in_unquoted_url": ("url(a\x08b)", r"url\(\)"),
    "vertical_tab_in_unquoted_url": ("url(a\x0bb)", r"url\(\)"),
    "shift_out_in_unquoted_url": ("url(a\x0eb)", r"url\(\)"),
    "unit_separator_in_unquoted_url": ("url(a\x1fb)", r"url\(\)"),
    "unquoted_url_in_upper_case": ("URL(a b)", r"url\(\)"),
    "unquoted_url_after_delimiter": ("f(x,url(a b))", r"url\(\)"),
    # A control character or DEL makes a bad url. A null is also refused by
    # the null rule, which `serialize_css_var_value` applies first.
    "null_in_unquoted_url": ("url(a\x00b)", r"url\(\)|null character"),
    "control_character_in_unquoted_url": ("url(a\x01b)", r"url\(\)"),
    "delete_character_in_unquoted_url": ("url(a\x7fb)", r"url\(\)"),
}


@pytest.mark.parametrize(("value", "reason"), list(_REFUSED_VALUES.values()), ids=list(_REFUSED_VALUES))
def test_css_data_refuses_declaration_breaks(value: str, reason: str) -> None:
    # Serializing, validating directly, and rendering a component all run the
    # same check, so a value cannot get past it on one path.
    with pytest.raises(ValueError, match=reason):
        validate_css_var_value(value)
    with pytest.raises(ValueError, match=reason):
        serialize_css_var_value(value)
    with pytest.raises(ValueError, match=reason):
        _render_with_css_value(value)


@pytest.mark.parametrize(
    ("value", "kind", "offset"),
    [
        pytest.param("ab\x00", "null character", 2, id="null"),
        pytest.param('"a\ud800"', "surrogate", 2, id="surrogate_in_a_string"),
        pytest.param('"\\\x00"', "null character", 2, id="null_after_a_backslash"),
    ],
)
def test_css_data_names_the_offset_of_a_null_or_surrogate(value: str, kind: str, offset: int) -> None:
    # The error points at the character, so the author can find it in a long value.
    with pytest.raises(ValueError, match=rf"{kind} at offset {offset}\."):
        validate_css_var_value(value)


# `url(` starts a url token only where a token starts. After a name character,
# or a `#` or `@` that begins a name, it is a plain function or a group of
# brackets, and its `;` sits inside a bracket where a declaration may hold it.
# Each pair shows the reading: the same text is refused as an unquoted url()
# at a token start and accepted after the name character.
_URL_READINGS = {
    "name_character_before": ("xurl(a;b)", "url(a b)"),
    "hash_before": ("#url(a;b)", "url(a b)"),
    "at_sign_before": ("@url(a;b)", "url(a b)"),
    "digit_before": ("1url(a;b)", "url(a b)"),
    "hyphen_before": ("-url(a;b)", "url(a b)"),
    "non_ascii_letter_before": ("\u00e9url(a;b)", "url(a b)"),
}


@pytest.mark.parametrize(
    ("not_a_url_token", "a_url_token"),
    list(_URL_READINGS.values()),
    ids=list(_URL_READINGS),
)
def test_css_data_url_token_starts_only_at_the_start_of_a_token(not_a_url_token: str, a_url_token: str) -> None:
    # A `;` inside the brackets is nested, so these values are accepted and
    # stay in one declaration. Only a non-ASCII character is rewritten, as a
    # hex escape.
    written = "".join(char if char.isascii() else f"\\{ord(char):x} " for char in not_a_url_token)
    assert serialize_css_var_value(not_a_url_token) == written
    # Whitespace or a bracket inside the parentheses is what an unquoted url()
    # refuses; a plain function accepts both.
    prefix = not_a_url_token.split("url(")[0]
    assert _implementation_accepts(f"{prefix}url(a b)")
    assert _implementation_accepts(f"{prefix}url(a(b))")
    assert _implementation_accepts(f"{prefix}url(a'b')")
    # Without the name character the same text is a url token and is refused.
    with pytest.raises(ValueError, match=r"url\(\)"):
        validate_css_var_value(a_url_token)
    with pytest.raises(ValueError, match=r"url\(\)"):
        validate_css_var_value("url(a(b))")
    # The brackets still have to balance in the plain-function reading.
    with pytest.raises(ValueError, match="unclosed"):
        validate_css_var_value(f"{prefix}url(a(b)")


def test_css_data_url_token_start_follows_a_url_token_that_just_ended() -> None:
    # `)` ends the first url token, so the second `url(` starts a new token.
    assert _implementation_accepts("url(a)url(b)")
    with pytest.raises(ValueError, match=r"url\(\)"):
        validate_css_var_value("url(a)url(b c)")


@pytest.mark.parametrize(
    "value",
    [
        "rgb(1, 2, 3)",
        "calc((100% - 20px) / 2)",
        "url(/a.png)",
        'url("data:image/svg+xml;utf8,<svg></svg>")',
        "url(data:image/svg+xml;utf8,<svg></svg>)",
        "var(--x, 1)",
        "var(--fallback, rgb(1, 2, 3))",
        '"Roboto"',
        "'Roboto'",
        '"a;b{c:d}"',
        '"a/*b*/c"',
        # A value with spaces that does not start with a function is quoted
        # before the check runs, so these two rows go through the quoting
        # path, not the raw scanner.
        "1px solid red",
        "[a b] 1fr",
    ],
    ids=lambda value: repr(value),
)
def test_css_data_still_accepts_ordinary_values(value: str) -> None:
    # The control group: values the check must keep passing, on every path.
    serialized = serialize_css_var_value(value)
    validate_css_var_value(serialized)
    assert f"  --x: {serialized};" in _render_with_css_value(value)


# ---------------------------------------------------------------------------
# A second reading of the value rules, used to check the real scanner.
#
# It follows the token rules of CSS Syntax Level 3 (section 4, "Tokenization")
# as a small reader with one method per token kind, and keeps the bracket and
# declaration checks in a separate pass over the token list. The scanner under
# test does both in a single loop, so the two are built differently.
#
# What the rules refuse, beyond what the CSS tokenizer calls a parse error:
# a comment, a brace, a `<` or a backslash outside a string and url(), a
# top-level `;` or `!`, an unbalanced bracket, a string or url() that is
# malformed or left unclosed, a null or surrogate character, and `</style`
# or `<!--` anywhere. Neither side checks that a value suits a property (the
# function is "not a full property validator"), so both accept `1 2 3`.
# ---------------------------------------------------------------------------

_WHITESPACE = "\n\t "
_QUOTES = "\"'"
_HEX_DIGITS = string.hexdigits
_NAME_START = string.ascii_letters + "_"
_NAME_CHARS = _NAME_START + string.digits + "-"


class _Refused(Exception):
    """Raised by the reference reader when the text breaks a rule."""


def _is_name_start(char: str) -> bool:
    return char != "" and (char in _NAME_START or ord(char) >= 0x80)


def _is_name_char(char: str) -> bool:
    return char != "" and (char in _NAME_CHARS or ord(char) >= 0x80)


def _is_digit(char: str) -> bool:
    return char != "" and char in string.digits


def _is_non_printable(char: str) -> bool:
    code = ord(char)
    return code <= 0x08 or code == 0x0B or 0x0E <= code <= 0x1F or code == 0x7F


class _Reader:
    """A cursor over the text with the look-ahead the CSS tokenizer needs."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    def peek(self, ahead: int = 0) -> str:
        """The character `ahead` places past the cursor, or an empty string past the end."""
        at = self.pos + ahead
        return self.text[at] if at < len(self.text) else ""

    def take(self) -> str:
        char = self.peek()
        self.pos += 1
        return char

    def take_while(self, test: Callable[[str], bool]) -> None:
        while self.peek() != "" and test(self.peek()):
            self.pos += 1

    def at_whitespace(self, ahead: int = 0) -> bool:
        return self.peek(ahead) != "" and self.peek(ahead) in _WHITESPACE

    def at_quote(self, ahead: int = 0) -> bool:
        return self.peek(ahead) != "" and self.peek(ahead) in _QUOTES

    def at_ident_start(self, ahead: int = 0) -> bool:
        first, second = self.peek(ahead), self.peek(ahead + 1)
        if first == "-":
            return _is_name_start(second) or second == "-"
        return _is_name_start(first)

    def at_number_start(self) -> bool:
        first, second, third = self.peek(), self.peek(1), self.peek(2)
        if first in {"+", "-"}:
            return _is_digit(second) or (second == "." and _is_digit(third))
        if first == ".":
            return _is_digit(second)
        return _is_digit(first)


def _read_string(reader: _Reader, ending: str) -> None:
    """Read a string token after its opening quote; refuse one that is unclosed or broken by a newline."""
    while True:
        char = reader.take()
        if char == ending:
            return
        if char == "":
            raise _Refused("unclosed string")
        if char == "\n":
            raise _Refused("newline in a string")
        if char != "\\":
            continue
        after = reader.peek()
        if after == "":
            raise _Refused("backslash at the end")
        if after == "\n":
            # A backslash and a newline continue the string on the next line.
            reader.take()
            continue
        _read_escape(reader)


def _read_escape(reader: _Reader) -> None:
    """Read what follows a backslash: up to six hex digits and one whitespace that ends them, or any one character."""
    digits = 0
    while digits < 6 and reader.peek() != "" and reader.peek() in _HEX_DIGITS:
        reader.take()
        digits += 1
    if digits == 0 or reader.at_whitespace():
        reader.take()


def _read_url(reader: _Reader) -> None:
    """Read an unquoted url token after `url(`; refuse the cases where a browser makes a bad url."""
    # The CSS tokenizer skips whitespace before the address begins.
    reader.take_while(lambda c: c in _WHITESPACE)
    while True:
        char = reader.take()
        if char == ")":
            return
        if char == "":
            raise _Refused("unclosed url")
        if char in _WHITESPACE:
            # Whitespace is allowed only just before the closing parenthesis.
            reader.take_while(lambda c: c in _WHITESPACE)
            if reader.peek() != ")":
                raise _Refused("whitespace inside a url")
        elif char in "\"'(" or _is_non_printable(char):
            raise _Refused("bad url")
        elif char == "\\":
            if reader.peek() in {"", "\n"}:
                raise _Refused("backslash that starts no escape")
            _read_escape(reader)


def _read_name(reader: _Reader) -> str:
    start = reader.pos
    while _is_name_char(reader.peek()):
        reader.take()
    if reader.peek() == "\\":
        raise _Refused("backslash")
    return reader.text[start : reader.pos].lower()


def _read_number(reader: _Reader) -> None:
    if reader.peek() in {"+", "-"}:
        reader.take()
    reader.take_while(_is_digit)
    if reader.peek() == "." and _is_digit(reader.peek(1)):
        reader.take()
        reader.take_while(_is_digit)
    if reader.peek() in {"e", "E"}:
        sign = 1 if reader.peek(1) in {"+", "-"} else 0
        if _is_digit(reader.peek(1 + sign)):
            reader.pos += 1 + sign
            reader.take_while(_is_digit)


def _read_ident_like(reader: _Reader) -> str:
    """Read a name; return `(` when it opens a group (a function call or a quoted url), else `ident` or `url`."""
    name = _read_name(reader)
    if reader.peek() != "(":
        return "ident"
    reader.take()
    if name != "url":
        return "("
    while reader.at_whitespace() and reader.at_whitespace(1):
        reader.take()
    if reader.at_quote() or (reader.at_whitespace() and reader.at_quote(1)):
        return "("
    _read_url(reader)
    return "url"


def _tokenize(text: str) -> list[str]:
    """Split `text` into token kinds; brackets, `;` and `!` keep their own character as the kind."""
    reader = _Reader(text)
    tokens: list[str] = []
    while reader.peek() != "":
        char = reader.peek()
        if char in _WHITESPACE:
            reader.take_while(lambda c: c in _WHITESPACE)
            tokens.append("space")
        elif char in _QUOTES:
            reader.take()
            _read_string(reader, char)
            tokens.append("string")
        elif char == "#":
            reader.take()
            if _is_name_char(reader.peek()):
                _read_name(reader)
            tokens.append("hash")
        elif char == "@":
            reader.take()
            if reader.at_ident_start():
                _read_name(reader)
            tokens.append("at-keyword")
        elif char in "()[];!":
            reader.take()
            tokens.append(char)
        elif char in "{}":
            raise _Refused("brace")
        elif char == "<":
            raise _Refused("less-than sign")
        elif char == "\\":
            raise _Refused("backslash")
        elif char == "/":
            reader.take()
            if reader.peek() == "*":
                raise _Refused("comment")
            tokens.append("delim")
        elif reader.at_number_start():
            _read_number(reader)
            if reader.at_ident_start():
                # A unit; a `(` after it is a separate group, not a function call.
                _read_name(reader)
            elif reader.peek() == "%":
                reader.take()
            tokens.append("number")
        elif reader.text.startswith("-->", reader.pos):
            reader.pos += 3
            tokens.append("cdc")
        elif reader.at_ident_start():
            tokens.append(_read_ident_like(reader))
        else:
            reader.take()
            tokens.append("delim")
    return tokens


def _reference_accepts(text: str) -> bool:
    """A second reading of the rules `validate_css_var_value` documents; True when the value passes."""
    folded = text.lower()
    if "</style" in folded or "<!--" in folded:
        return False
    if any(char == "\0" or 0xD800 <= ord(char) <= 0xDFFF for char in text):
        return False
    # The CSS input stage turns every kind of line break into one newline.
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    try:
        tokens = _tokenize(text)
    except _Refused:
        return False

    closers = {"(": ")", "[": "]"}
    waiting_for: list[str] = []
    for token in tokens:
        if token in closers:
            waiting_for.append(closers[token])
        elif token in {")", "]"}:
            if not waiting_for or waiting_for.pop() != token:
                return False
        elif token in {";", "!"} and not waiting_for:
            return False
    return not waiting_for


# The characters that change how a value is read. A digit is included for
# numbers and units, and `x` for names that run into `url(`. A null, a lone
# surrogate, a control character, DEL and a non-ASCII letter cover the
# characters each rule treats on its own, and `s`, `t`, `y`, `e` let short
# strings spell `</style` by chance. A tab, a carriage return and a form feed
# are the other whitespace characters; `a` and `4` spell a hex escape.
_ALPHABET = [*"urlx7()[]{}\"'\\/*<!-; \n\t\r\f\x0b#@:,.\x00\ud800\x01\x7f\u00e9styea4"]
# Whole pieces drawn alongside single characters, so that short strings
# often contain a `url(` token or a string that closes.
_PIECES = [
    *_ALPHABET,
    "url(",
    "url(",
    "URL(",
    "xurl(",
    "#url(",
    "@url(",
    "\\\n",
    "\\\r\n",
    "\\41 ",
    "\\41\r\n",
    "</",
    "/*",
    '"a"',
    "'a'",
    "</style",
    "</STYLE",
]


def _random_value(rng: random.Random) -> str:
    return "".join(rng.choice(_PIECES) for _ in range(rng.randrange(15)))


def test_css_data_tokenizer_matches_reference() -> None:
    # A fixed seed keeps the generated strings the same on every run.
    rng = random.Random(7_302)  # noqa: S311 - test data, not secrets
    accepted = 0
    refused = 0
    for _ in range(20_000):
        value = _random_value(rng)
        expected = _reference_accepts(value)
        assert _implementation_accepts(value) == expected, repr(value)
        accepted += expected
        refused += not expected

    # The comparison only means something if both outcomes are well represented.
    assert accepted > 1_000
    assert refused > 1_000


# ---------------------------------------------------------------------------
# Escapes and whitespace, where a scanner that differs from the browser by one
# character would see a quote or `)` that the browser does not. Each
# value has the outcome CSS Syntax gives it. The first test checks that the
# reference reads each value that way, so a wrong reference fails loudly; the
# second checks the scanner against the same outcome.
# ---------------------------------------------------------------------------

_ESCAPES_AND_WHITESPACE = [
    # A hex escape takes the one whitespace after it, so a newline there does
    # not end the string.
    pytest.param('"\\7\n"', True, id="hex_escape_swallows_the_newline_after_it"),
    pytest.param('"\\\r\n"', True, id="carriage_return_and_newline_continue_a_string"),
    pytest.param('"\\41\r\n"', True, id="hex_escape_swallows_carriage_return_and_newline"),
    pytest.param('"\\41\f"', True, id="hex_escape_swallows_a_form_feed"),
    # A non-hex escape takes one character only, so a newline after it ends the string.
    pytest.param('"\\g\n"', False, id="non_hex_escape_leaves_the_newline_after_it"),
    pytest.param('"\\41  \n"', False, id="hex_escape_swallows_one_whitespace_only"),
    # Whitespace before the address is skipped, and whitespace after it is allowed.
    pytest.param("url( a)", True, id="whitespace_before_the_address_in_an_unquoted_url"),
    pytest.param("url(\t\n/a.png \n)", True, id="whitespace_on_both_sides_of_an_unquoted_url"),
    pytest.param("url( )", True, id="only_whitespace_in_an_unquoted_url"),
    pytest.param("url( a b)", False, id="whitespace_in_the_middle_of_an_unquoted_url"),
    # In an unquoted url(), a hex escape takes the one whitespace after it.
    pytest.param("url(a\\41 b)", True, id="hex_escape_swallows_a_space_in_an_unquoted_url"),
    pytest.param("url(a\\41\r\nb)", True, id="hex_escape_swallows_carriage_return_and_newline_in_a_url"),
    pytest.param("url(a\\000041 b)", True, id="six_digit_hex_escape_in_an_unquoted_url"),
    pytest.param("url(a\\0000411 b)", False, id="seventh_digit_is_not_part_of_the_escape"),
    pytest.param("url(a\\41  b)", False, id="hex_escape_swallows_one_space_only_in_an_unquoted_url"),
    pytest.param("url(a\\g b)", False, id="non_hex_escape_leaves_the_space_in_an_unquoted_url"),
    # Only CSS whitespace ends an escape: a vertical tab or unit separator after
    # the digits stays in the URL, where it is not allowed.
    pytest.param("url(a\\41\x0bb)", False, id="hex_escape_does_not_swallow_a_vertical_tab"),
    pytest.param("url(a\\41\x1fb)", False, id="hex_escape_does_not_swallow_a_unit_separator"),
    pytest.param("url(a\\\nb)", False, id="backslash_and_newline_in_an_unquoted_url"),
    pytest.param("url(a\\\r\nb)", False, id="backslash_and_carriage_return_newline_in_an_unquoted_url"),
]


@pytest.mark.parametrize(("value", "accepted"), _ESCAPES_AND_WHITESPACE)
def test_css_reference_reads_escapes_and_whitespace_as_css_syntax_does(value: str, accepted: bool) -> None:
    assert _reference_accepts(value) is accepted


@pytest.mark.parametrize(("value", "accepted"), _ESCAPES_AND_WHITESPACE)
def test_css_data_reads_escapes_and_whitespace_as_css_syntax_does(value: str, accepted: bool) -> None:
    assert _implementation_accepts(value) is accepted


# A null character or lone surrogate is refused in every token, including the
# character after a backslash, which the string and url() scanners step over.
_UNREADABLE_CHARACTERS = [
    pytest.param('"a\ud800b"', id="surrogate_in_a_string"),
    pytest.param("url(a\ud800b)", id="surrogate_in_an_unquoted_url"),
    pytest.param('url("a\ud800b")', id="surrogate_in_a_quoted_url"),
    pytest.param('"a\x00b"', id="null_in_a_string"),
    pytest.param('"\\\ud800"', id="surrogate_after_a_backslash_in_a_string"),
    pytest.param('"\\\x00"', id="null_after_a_backslash_in_a_string"),
    pytest.param("url(a\\\ud800)", id="surrogate_after_a_backslash_in_an_unquoted_url"),
    pytest.param("url(a\\\x00)", id="null_after_a_backslash_in_an_unquoted_url"),
]


@pytest.mark.parametrize("value", _UNREADABLE_CHARACTERS)
def test_css_data_refuses_a_null_or_surrogate_in_every_token(value: str) -> None:
    assert _reference_accepts(value) is False
    assert _implementation_accepts(value) is False
    with pytest.raises(ValueError, match=r"null character|surrogate"):
        serialize_css_var_value(value)


# ---------------------------------------------------------------------------
# A stylesheet of printable ASCII and CSS whitespace reads the same in each
# encoding that keeps ASCII bytes as they are. So the serializer writes every
# other character as a hex escape, which the browser reads as that character.
# Without the escape, on a page in GBK or Big5 the last byte of a non-ASCII
# character is read together with the next ASCII byte, which can hide the
# backslash of an escaped quote.
# ---------------------------------------------------------------------------
_ESCAPED_OUTPUT = [
    pytest.param('"\u8868"', '"\\8868 "', id="a_string"),
    pytest.param('"\u8868\\";}.evil{--evil:1}"', '"\\8868 \\";}.evil{--evil:1}"', id="the_breakout_on_a_gbk_page"),
    pytest.param("url(\u8868.png)", "url(\\8868 .png)", id="an_unquoted_url"),
    pytest.param('"\\\u8868"', '"\\8868 "', id="a_backslash_before_the_character_is_one_escape"),
    pytest.param('"a\\\\\u8868"', '"a\\\\\\8868 "', id="an_escaped_backslash_then_the_character"),
    pytest.param('"\\41\u8868"', '"\\41\\8868 "', id="a_hex_escape_then_the_character"),
    pytest.param('url("\\41 \u8868")', 'url("\\41 \\8868 ")', id="a_hex_escape_ended_by_a_space_then_the_character"),
    pytest.param('"\U0001f600"', '"\\1f600 "', id="a_character_outside_the_basic_plane"),
    pytest.param('"\u00e9"', '"\\e9 "', id="a_latin_letter"),
    pytest.param('"\x1b$B"', '"\\1b $B"', id="the_escape_character_that_switches_a_japanese_encoding"),
    pytest.param('"\x7f"', '"\\7f "', id="delete"),
    pytest.param("\u8868 x", '"\\8868  x"', id="text_with_a_space_is_quoted_then_escaped"),
    pytest.param("calc(1px + 2px)", "calc(1px + 2px)", id="ascii_is_unchanged"),
    pytest.param('"a\\"b"', '"a\\"b"', id="an_escaped_quote_is_unchanged"),
    pytest.param('url("a\\\nb")', 'url("a\\\nb")', id="a_line_continuation_is_unchanged"),
]


@pytest.mark.parametrize(("value", "expected"), _ESCAPED_OUTPUT)
def test_css_data_writes_characters_beyond_printable_ascii_as_hex_escapes(value: str, expected: str) -> None:
    assert serialize_css_var_value(value) == expected


def _decode_css_escapes(text: str) -> str:
    """Read `text` the way CSS Syntax reads escapes: up to 6 hex digits and one whitespace, or any one character."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    decoded: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        index += 1
        if char != "\\" or index >= len(text):
            decoded.append(char)
            continue
        if text[index] == "\n":
            index += 1
            continue
        digits = ""
        while index < len(text) and len(digits) < 6 and text[index] in _HEX_DIGITS:
            digits += text[index]
            index += 1
        if not digits:
            decoded.append(text[index])
            index += 1
            continue
        if index < len(text) and text[index] in _WHITESPACE:
            index += 1
        codepoint = int(digits, 16)
        decoded.append(
            "\ufffd" if codepoint == 0 or codepoint > 0x10FFFF or 0xD800 <= codepoint < 0xE000 else chr(codepoint)
        )
    return "".join(decoded)


_PIECES_BEYOND_PRINTABLE_ASCII = [
    "\u8868",
    "\u00e9",
    "\U0001f600",
    "\u00a0",
    "\u2028",
    "\x85",
    "\x1b",
    "\x7f",
    "\\\u8868",
    "\\\x1b",
    "\\\u00e9\\41",
]


def _random_value_with_other_characters(rng: random.Random) -> str:
    pieces = [*_PIECES, *_PIECES_BEYOND_PRINTABLE_ASCII]
    return "".join(rng.choice(pieces) for _ in range(rng.randrange(15)))


def test_css_data_escape_keeps_every_character_and_leaves_only_printable_ascii_and_css_whitespace() -> None:
    rng = random.Random(4_417)  # noqa: S311 - test data, not secrets
    changed = 0
    for _ in range(40_000):
        value = _random_value_with_other_characters(rng)
        if not _implementation_accepts(value):
            continue
        escaped = _escape_beyond_printable_ascii(value)
        # Only printable ASCII and CSS whitespace remain.
        assert all(char in "\n\r\t\f" or " " <= char <= "~" for char in escaped), repr(value)
        # The browser reads the same characters before and after.
        assert _decode_css_escapes(escaped) == _decode_css_escapes(value), repr(value)
        # Escaping twice changes nothing more.
        assert _escape_beyond_printable_ascii(escaped) == escaped, repr(value)
        changed += escaped != value

    # The comparison means something only if many values hold such a character.
    assert changed > 1_000


def test_css_data_renders_the_same_ascii_text_inline_and_in_the_linked_stylesheet() -> None:
    app = Citry()
    app.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = app
        template = """
            <span class="w">w</span>
        """
        css = """
            .w { color: var(--x); }
        """

        def css_data(self, kwargs, slots):
            return {"x": '"\u8868\\";}.evil{--evil:1}"', "y": "1"}

    inline = Widget().render().serialize(deps_strategy="document")
    assert '--x: "\\8868 \\";}.evil{--evil:1}";' in inline
    assert "\u8868" not in inline

    # The stylesheet the page links is the same ASCII text, served through the real route.
    rendered = Widget().render()
    rendered.serialize(deps_strategy="fragment")
    record = next(item for item in rendered.context.extra["dependencies"] if item.class_id == Widget.class_id)
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": f"/cache/{Widget.class_id}.{record.css_vars_hash}.css",
        "SCRIPT_NAME": "",
        "QUERY_STRING": "",
        "wsgi.input": io.BytesIO(b""),
    }
    body = b"".join(wsgi_app(app)(environ, lambda _status, _headers: None))
    assert body.isascii()
    assert b'--x: "\\8868 \\";}.evil{--evil:1}";' in body
