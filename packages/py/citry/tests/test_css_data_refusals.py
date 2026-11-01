"""A `css_data()` value is checked token by token, so it cannot end its declaration or its `<style>` element."""

from __future__ import annotations

import random
import re
import string
from typing import TYPE_CHECKING

import pytest

from citry import Citry, Component
from citry.util.css import serialize_css_var_value, validate_css_var_value

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
    # stay in one declaration.
    assert serialize_css_var_value(not_a_url_token) == not_a_url_token
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
        # An escape is up to six hex digits and one trailing whitespace, or any one character.
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
            reader.take()


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
# strings spell `</style` by chance. A carriage return and a form feed are left
# out: the known differences below involve them.
_ALPHABET = [*"urlx7()[]{}\"'\\/*<!-; \n#@:,.\x00\ud800\x01\x7f\u00e9stye"]
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
    "</",
    "/*",
    '"a"',
    "'a'",
    "</style",
    "</STYLE",
]

# The shapes behind the known differences listed after the comparison: a hex
# escape that swallows the newline after it, and whitespace before the address
# in an unquoted url().
_STRICTER_SHAPES = re.compile(r"\\[0-9a-fA-F]{1,6}\n|url\([ \t\n]", re.IGNORECASE)


def _is_known_difference(value: str, expected: bool) -> bool:
    """Whether the scanner and reference differ on `value` only for a difference this file records."""
    # One direction is recorded: the reference accepts and the scanner refuses
    # (the scanner is stricter).
    return expected and _STRICTER_SHAPES.search(value) is not None


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
        if _implementation_accepts(value) != expected:
            # Only the differences recorded below may disagree; any other one fails.
            assert _is_known_difference(value, expected), repr(value)
            continue
        accepted += expected
        refused += not expected

    # The comparison only means something if both outcomes are well represented.
    assert accepted > 1_000
    assert refused > 1_000


# ---------------------------------------------------------------------------
# Where the scanner is stricter than the CSS Syntax text. Each value below is
# one that CSS Syntax accepts and the scanner refuses. That is safe, because a
# value the scanner refuses never reaches the page, but it is a difference. The
# first test checks that the reference reads each value the way CSS Syntax
# does, so a wrong reference fails loudly. The second is an expected failure
# that states what the scanner would have to do; when the scanner is changed
# to accept a value, that case turns into an error that says to delete it. The
# random comparison above waives these shapes (see `_is_known_difference`),
# because some seeds reach them.
# ---------------------------------------------------------------------------

_STRICTER_THAN_CSS_SYNTAX = [
    pytest.param('"\\7\n"', id="hex_escape_swallows_the_newline_after_it"),
    pytest.param('"\\\r\n"', id="carriage_return_and_newline_continue_a_string"),
    pytest.param("url( a)", id="whitespace_before_the_address_in_an_unquoted_url"),
]


@pytest.mark.parametrize("value", _STRICTER_THAN_CSS_SYNTAX)
def test_css_reference_reads_the_stricter_cases_as_css_syntax_does(value: str) -> None:
    assert _reference_accepts(value) is True


@pytest.mark.xfail(strict=True, reason="the scanner is stricter than CSS Syntax Level 3 on this value")
@pytest.mark.parametrize("value", _STRICTER_THAN_CSS_SYNTAX)
def test_css_scanner_accepts_what_css_syntax_accepts_on_known_differences(value: str) -> None:
    assert _implementation_accepts(value) is True


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
