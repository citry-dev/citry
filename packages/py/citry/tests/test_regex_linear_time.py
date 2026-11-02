"""
Five regexes that read input finish in one pass over long input.

They read a route's HTTP methods, an event handler's ``methods`` option,
the time in an Events modifier such as ``.debounce.300ms``, whether an
expression a v-for error message suggests is a plain dotted name, and the
scheme of a ``Redirect`` URL. The app's code or the template author
supplies the first four; a ``Redirect`` URL can hold text the app took
from a request. No two parts of a pattern can claim the same character,
so a long value that almost matches fails after one scan. These tests
keep it that way: a change that lets a pattern try many ways to split its
input fails its test, or makes the test hang when the pattern becomes
exponential.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from citry._vue_loop_errors import _PLAIN_PATH
from citry.ext.events.bindings import _TIME_RE
from citry.ext.events.handlers import _HTTP_METHOD_RE
from citry.ext.events.routes import _URL_SCHEME
from citry.util.routing import _ROUTE_METHOD_RE

if TYPE_CHECKING:
    import re

# Long enough that a quadratic match takes seconds (about 2 s for the time
# pattern rewritten as `[0-9]*[0-9]*s`, 1 to 20 s for the others), short
# enough that a one-pass match takes about a millisecond.
_LENGTH = 50_000
# Generous, so a slow CI machine never fails a linear pattern.
_BOUND_SECONDS = 0.5


@pytest.mark.parametrize(
    ("pattern", "text"),
    [
        # Each input repeats text the pattern accepts, then ends with a
        # character it does not, so the match must scan everything before
        # failing.
        (_ROUTE_METHOD_RE, "A" * _LENGTH + "a"),
        (_HTTP_METHOD_RE, "A" * _LENGTH + " "),
        (_TIME_RE, "1" * _LENGTH + "x"),
        # Many short names, and one long name: a rewrite can backtrack
        # across the dots or inside a single name.
        (_PLAIN_PATH, "a." * _LENGTH + "!"),
        (_PLAIN_PATH, "a" * _LENGTH + "!"),
        (_URL_SCHEME, "a" * _LENGTH + "!"),
    ],
    ids=["route-method", "http-method", "time", "loop-path-dots", "loop-path-name", "redirect-scheme"],
)
def test_validation_patterns_reject_long_input_quickly(pattern: re.Pattern[str], text: str) -> None:
    start = time.perf_counter()
    matched = pattern.fullmatch(text)
    elapsed = time.perf_counter() - start
    # The input must be one the pattern refuses, or the timing proves nothing.
    assert matched is None
    assert elapsed < _BOUND_SECONDS
