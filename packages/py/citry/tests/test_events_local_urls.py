r"""
Tests for ``is_local_url`` and ``local_url_or``, the redirect URL checks in ``citry.ext.events``.

Each case says whether the check accepts the URL and whether Django's
``url_has_allowed_host_and_scheme`` gives the same answer. Where the two
differ on purpose, the case says why. The browser-reading cases (``\`` read
as ``/``, extra slashes before a host) were checked in Chromium, Firefox and
WebKit with ``new URL()`` and real 303 navigations when this module was
written.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry.ext.events import actions, is_local_url, local_url_or

HOSTS = frozenset({"shop.example", "shop.example:8000", "[::1]:8000"})

# (url, expected, django_agrees). django_agrees is False only where this
# check is deliberately stricter or reads the URL as a browser does.
CASES: list[tuple[str, bool, bool]] = [
    # Relative URLs stay on the page's site.
    ("/", True, True),
    ("/orders/7", True, True),
    ("/orders/7?page=2#top", True, True),
    ("?page=2", True, True),
    ("#top", True, True),
    ("next", True, True),
    ("orders/7", True, True),
    ("/path/to/a:b", True, True),
    ("/@other.example", True, True),
    ("a/b@other.example", True, True),
    ("/%2F%2Fother.example", True, True),
    ("/ /other.example", True, True),
    # Leading and trailing whitespace is removed before the check.
    ("  /orders/7  ", True, True),
    ("  //other.example", False, True),
    ("\u3000//other.example", False, True),
    ("\u3000/orders", False, False),  # Django strips U+3000; a browser keeps it
    ("/orders\u00a0", False, False),
    ("//shop.example\u00a0\u3000", False, False),  # Chromium reads another host
    # Two slashes, or any mix of "/" and "\", name a host.
    ("//other.example", False, True),
    ("//other.example/path", False, True),
    ("/\\other.example", False, True),
    ("\\/other.example", False, True),
    ("\\\\other.example", False, True),
    ("\\\\\\other.example", False, True),
    ("//shop.example/orders", True, True),
    ("\\\\shop.example/orders", True, True),
    # The browser skips any number of slashes before the host.
    ("///other.example", False, True),
    ("////other.example", False, True),
    ("///shop.example", False, True),
    ("/\\/other.example", False, True),
    ("https:///other.example", False, True),
    ("https:////other.example", False, True),
    ("https:\\\\\\other.example", False, True),
    # Absolute URLs must name an allowed host.
    ("https://shop.example", True, True),
    ("https://shop.example/orders/7", True, True),
    ("http://shop.example/orders/7", True, True),
    ("https://shop.example?x=1", True, True),
    ("https://shop.example#x", True, True),
    ("https://SHOP.Example/orders", True, False),  # Django compares case exactly
    ("HTTPS://shop.example/", True, True),
    ("https://shop.example:8000/", True, True),
    ("https://[::1]:8000/", True, True),
    ("https://other.example", False, True),
    ("https://shop.example.other.example/", False, True),
    ("https://shop.example:9000/", False, True),
    ("https://shop.example:/", False, True),
    ("https://shop.example./", False, True),
    ("https://shop%2Eexample/", False, True),
    ("https:\\\\other.example", False, True),
    ("https:/\\other.example", False, True),
    ("https://shop.example\\other.example", True, False),  # "\" ends the host
    # A scheme without "//" after it can name a host in a browser.
    ("https:next", False, True),
    ("https:/orders/7", False, True),
    ("https:other.example", False, True),
    ("http:other.example", False, True),
    # A user name or password hides the real host.
    ("https://user@other.example", False, True),
    ("https://shop.example@other.example", False, True),
    ("https://user:pw@shop.example/", False, True),
    ("//shop.example@other.example", False, True),
    ("https://shop.example\\@other.example", False, True),
    ("https://other.example\\@shop.example", False, True),
    # Any scheme other than http and https.
    ("javascript:alert(1)", False, True),
    ("JavaScript:alert(1)", False, True),
    ("  javascript:alert(1)", False, True),
    ("data:text/html,<script>alert(1)</script>", False, True),
    ("vbscript:msgbox(1)", False, True),
    ("ftp://shop.example/", False, True),
    ("mailto:someone@shop.example", False, True),
    ("blob:https://shop.example/1", False, True),
    # Control characters: refused anywhere, since Redirect refuses them too.
    ("\x00//other.example", False, True),
    ("\x08//other.example", False, True),
    ("\x1f//other.example", False, True),
    ("\x7f//other.example", False, True),
    ("/\t/other.example", False, True),
    ("/\n/other.example", False, True),
    ("/\r/other.example", False, True),
    ("java\tscript:alert(1)", False, True),
    ("/orders/\t7", False, False),  # Django drops the tab and accepts
    ("/orders/7\n", False, False),  # Django strips the newline and accepts
    ("/a\x85b", False, False),  # a C1 control; Django accepts
    ("?\x9f", False, False),
    # Invisible characters at the start.
    ("\u200b//other.example", False, True),
    ("\u0085//other.example", False, True),
    ("\u200e/orders", False, True),
    # Internationalized names compare as written.
    ("https://xn--bcher-kva.example/", False, True),
    ("https://b\u00fccher.example/", True, True),
    ("https://B\u00dcCHER.example/", False, True),
    # Malformed hosts are refused, never raised on.
    ("http://[::1", False, True),
    ("http://]::1[/", False, True),
    ("https://", False, True),
    ("https://?x", False, True),
    ("https://#x", False, True),
    ("//", False, False),  # Django reads a path; a browser fails on the empty host
]

HOSTS_WITH_IDN = HOSTS | {"b\u00fccher.example"}


@pytest.mark.parametrize(("url", "expected", "django_agrees"), CASES)
def test_is_local_url_cases(url: str, expected: bool, django_agrees: bool) -> None:
    assert is_local_url(url, allowed_hosts=HOSTS_WITH_IDN) is expected


@pytest.mark.parametrize(("url", "expected", "django_agrees"), CASES)
def test_cases_match_django(url: str, expected: bool, django_agrees: bool) -> None:
    """Every case marked as agreeing gets the same answer from Django; the others differ."""
    django_http = pytest.importorskip("django.utils.http")
    django_says = django_http.url_has_allowed_host_and_scheme(url, allowed_hosts=HOSTS_WITH_IDN)
    assert (django_says == expected) is django_agrees


@pytest.mark.parametrize(
    "url",
    ["/orders/7", "?page=2", "https://shop.example/x", "//shop.example/x"],
)
def test_require_https_keeps_relative_and_https(url: str) -> None:
    assert is_local_url(url, allowed_hosts=HOSTS, require_https=False)
    expected = not url.startswith("//")
    assert is_local_url(url, allowed_hosts=HOSTS, require_https=True) is expected


def test_require_https_refuses_http() -> None:
    assert not is_local_url("http://shop.example/", allowed_hosts=HOSTS, require_https=True)
    assert not is_local_url("//shop.example/", allowed_hosts=HOSTS, require_https=True)


def test_no_allowed_hosts_accepts_only_relative_urls() -> None:
    assert is_local_url("/orders/7")
    assert is_local_url("?page=2")
    assert not is_local_url("https://shop.example/")
    assert not is_local_url("//shop.example/")


def test_allowed_hosts_single_string_is_one_host() -> None:
    assert is_local_url("https://shop.example/", allowed_hosts="shop.example")
    # Iterating the string would allow the one-letter host "s".
    assert not is_local_url("https://s/", allowed_hosts="shop.example")


def test_allowed_hosts_are_case_insensitive_for_ascii() -> None:
    assert is_local_url("https://shop.example/", allowed_hosts={"SHOP.Example"})


def test_allowed_hosts_generator_is_read_once() -> None:
    hosts = (host for host in ["shop.example"])
    # The fallback check and the url check both need the hosts.
    assert local_url_or("https://shop.example/x", "https://shop.example/", allowed_hosts=hosts) == (
        "https://shop.example/x"
    )


@pytest.mark.parametrize("url", [None, "", "   ", "\t", "\u3000"])
def test_empty_urls_are_refused(url: str | None) -> None:
    assert is_local_url(url) is False
    assert local_url_or(url, "/home") == "/home"


@pytest.mark.parametrize("url", [b"/orders", 7, ["/orders"]])
def test_non_string_url_raises_type_error(url: Any) -> None:
    with pytest.raises(TypeError, match="must be a string or None"):
        is_local_url(url)
    with pytest.raises(TypeError, match="must be a string or None"):
        local_url_or(url)


def test_non_string_allowed_host_raises_type_error() -> None:
    with pytest.raises(TypeError, match="allowed_hosts"):
        is_local_url("/x", allowed_hosts=[b"shop.example"])  # type: ignore[list-item]


def test_local_url_or_returns_url_unchanged() -> None:
    assert local_url_or("  /orders/7 ") == "  /orders/7 "
    assert local_url_or("https://SHOP.example/x", allowed_hosts=HOSTS) == "https://SHOP.example/x"


def test_local_url_or_returns_fallback() -> None:
    assert local_url_or("//other.example") == "/"
    assert local_url_or("//other.example", "/account/") == "/account/"
    assert local_url_or("javascript:alert(1)", "https://shop.example/", allowed_hosts=HOSTS) == (
        "https://shop.example/"
    )


@pytest.mark.parametrize("fallback", ["//other.example", "https://other.example/", "javascript:x", "", None])
def test_local_url_or_refuses_bad_fallback(fallback: str | None) -> None:
    # Raised even when the url itself passes, so the first test finds it.
    with pytest.raises(ValueError, match="fallback"):
        local_url_or("/orders/7", fallback)  # type: ignore[arg-type]


def test_local_url_or_fallback_follows_require_https() -> None:
    with pytest.raises(ValueError, match="fallback"):
        local_url_or("/x", "http://shop.example/", allowed_hosts=HOSTS, require_https=True)


@pytest.mark.parametrize(("url", "expected", "django_agrees"), CASES)
def test_accepted_urls_build_a_redirect(url: str, expected: bool, django_agrees: bool) -> None:
    """Redirect never raises on a URL the check accepts."""
    target = local_url_or(url, allowed_hosts=HOSTS_WITH_IDN)
    assert actions.Redirect(target).url == (url if expected else "/")
