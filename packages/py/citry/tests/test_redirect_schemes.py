"""`actions.Redirect` accepts only http(s) and relative URLs."""

from __future__ import annotations

import random
import string

import pytest

from citry.ext.events import actions
from citry.ext.events.actions import redirect_url_scheme


@pytest.mark.parametrize(
    "url",
    [
        "javascript:void 0",
        "JAVASCRIPT:void 0",
        "java\tscript:void 0",
        "java\nscript:void 0",
        " javascript:void 0",
        "\x01javascript:void 0",
        "data:text/plain,x",
        "vbscript:x",
    ],
)
def test_redirect_refuses_non_http_schemes(url: str) -> None:
    with pytest.raises(ValueError, match="scheme|control character"):
        actions.Redirect(url)


@pytest.mark.parametrize(
    "url",
    ["/orders/7", "orders/7", "?page=2", "#top", "//example.com/x", "https://example.com/", "HTTP://example.com/"],
)
def test_redirect_accepts_http_and_relative_urls(url: str) -> None:
    assert actions.Redirect(url).url == url


def _reference_scheme(url: str) -> str | None:
    """A second, plainly written reading of the URL parser's first steps."""
    text = url.strip("".join(chr(code) for code in range(0x21)))
    text = "".join(char for char in text if char not in "\t\n\r")
    if ":" not in text:
        return None
    scheme = text.split(":", 1)[0]
    letters = string.ascii_letters
    if not scheme or scheme[0] not in letters:
        return None
    if any(char not in letters + string.digits + "+-." for char in scheme):
        return None
    return scheme.lower()


_URL_CHARS = [*"abcjsvJS:/.+-0", "\t", "\n", "\r", " ", "\x00", "\x1f", "?", "#"]


def test_redirect_scheme_reading_matches_the_reference() -> None:
    # A fixed seed keeps the generated strings the same on every run.
    rng = random.Random(469)  # noqa: S311 - test data, not secrets
    for _ in range(20_000):
        url = "".join(rng.choice(_URL_CHARS) for _ in range(rng.randrange(17)))
        assert redirect_url_scheme(url) == _reference_scheme(url), repr(url)
