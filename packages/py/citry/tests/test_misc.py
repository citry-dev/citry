"""Tests for citry.util.misc helpers."""

from citry.util.misc import format_url


def test_adds_query_and_fragment():
    assert format_url("https://example.com", query={"foo": "bar"}, fragment="baz") == "https://example.com?foo=bar#baz"


def test_true_is_a_flag_false_and_none_are_dropped():
    result = format_url(
        "https://example.com",
        query={"foo": "bar", "baz": None, "enabled": True, "debug": False},
    )
    assert result == "https://example.com?foo=bar&enabled"


def test_no_query_or_fragment_leaves_url_unchanged():
    assert format_url("https://example.com") == "https://example.com"


def test_merges_with_existing_query():
    assert format_url("https://example.com/p?a=1&b=2", query={"c": "3"}) == "https://example.com/p?a=1&b=2&c=3"


def test_supplied_query_overrides_existing_key():
    assert format_url("https://example.com/p?a=1", query={"a": "override"}) == "https://example.com/p?a=override"


def test_special_characters_are_percent_encoded():
    assert format_url("https://example.com", query={"q": "a b&c=d"}) == "https://example.com?q=a+b%26c%3Dd"


def test_existing_fragment_is_kept_when_fragment_is_none():
    assert format_url("https://example.com#old") == "https://example.com#old"


def test_fragment_overrides_and_is_encoded():
    assert format_url("https://example.com#old", fragment="new frag") == "https://example.com#new%20frag"


def test_relative_url():
    assert format_url("/relative/path", query={"x": "1"}, fragment="sec") == "/relative/path?x=1#sec"


def test_non_string_value_is_stringified():
    assert format_url("https://example.com", query={"n": 42, "ok": True}) == "https://example.com?n=42&ok"
