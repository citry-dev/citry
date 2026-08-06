"""Tests for Citry's public trusted-HTML marker."""

from markupsafe import Markup as MarkupSafeMarkup

from citry import Markup


def test_markup_is_the_exact_markupsafe_class() -> None:
    assert Markup is MarkupSafeMarkup


def test_markup_constructor_trusts_the_complete_value() -> None:
    value = '<img src=x onerror="alert(1)">'

    assert Markup(value) == value  # noqa: S704 - this test locks the unsafe constructor contract


def test_markup_format_escapes_dynamic_values() -> None:
    value = '<img src=x onerror="alert(1)">'
    expected = "<strong>&lt;img src=x onerror=&#34;alert(1)&#34;&gt;</strong>"

    assert Markup("<strong>{}</strong>").format(value) == expected
