"""
The Events CSRF name settings and the page nonce that a request sends.

``_csrf_cookie`` and ``_csrf_header`` reach the browser runtime through each
app's configuration block, so a host whose CSRF names differ from Django's
defaults needs no script of its own. ``page_nonce_from_headers()`` reads the
``X-Citry-Page-Nonce`` header that page code fills from ``Citry.pageNonce()``,
and an Events ``Render`` uses it when the app sets no ``_csp_nonce``.
"""

from __future__ import annotations

import json
import re

import pytest

from citry import PAGE_NONCE_HEADER, Citry, Component, page_nonce_from_headers
from citry.ext.events.renderers import dispatcher_for
from citry.util.routing import RouteHeaders

SECRET = "csrf-names-test-secret"  # noqa: S105


def _citry(**kwargs):
    c = Citry(secret=SECRET, autodiscover=False, **kwargs)
    c.set_mounted_prefix("/citry")
    return c


def _page_configuration(c: Citry) -> dict[str, object]:
    """The configuration block of a mounted page with one Events component."""

    class App(Component):
        citry = c
        template = '<button @c-click="save">Save</button>'

        class Events:
            def save(self):
                return None

    dispatcher_for(c)
    html = App().render().serialize()
    match = re.search(
        r'<script type="application/json" data-citry-vue-document="[^"]*"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    return json.loads(match.group(1))


class TestCsrfNameSettings:
    @pytest.mark.parametrize(
        ("events", "expected"),
        [
            ({"_csrf_cookie": "__Host-csrftoken"}, {"cookie": "__Host-csrftoken"}),
            ({"_csrf_header": "X-CSRF-Token"}, {"header": "X-CSRF-Token"}),
            # Django's CSRF_USE_SESSIONS or CSRF_COOKIE_HTTPONLY: no cookie to read.
            ({"_csrf_cookie": None}, {"cookie": None}),
            (
                {"_csrf_cookie": "site_csrf", "_csrf_header": "X-Site-CSRF"},
                {"cookie": "site_csrf", "header": "X-Site-CSRF"},
            ),
        ],
    )
    def test_the_block_carries_the_names_the_app_set(self, events, expected):
        assert _page_configuration(_citry(extensions_defaults={"events": events}))["csrfNames"] == expected

    def test_a_page_on_the_defaults_has_no_csrf_names(self):
        assert "csrfNames" not in _page_configuration(_citry())

    @pytest.mark.parametrize(
        ("name", "value", "message"),
        [
            ("_csrf_cookie", "", "must be a cookie name"),
            ("_csrf_cookie", "a b", "must be a cookie name"),
            ("_csrf_cookie", "x;y", "must be a cookie name"),
            ("_csrf_cookie", 1, "must be a cookie name"),
            ("_csrf_header", None, "must be a header name"),
            ("_csrf_header", "X CSRF", "must be a header name"),
            ("_csrf_header", "X-Token\r\nSet-Cookie: a=b", "must be a header name"),
            ("_csrf_header", "X-Citry-Token", "sets itself"),
            ("_csrf_header", "Cookie", "sets itself"),
            ("_csrf_header", "sec-csrf", "sets itself"),
        ],
    )
    def test_a_name_the_browser_could_not_use_is_refused_at_startup(self, name, value, message):
        with pytest.raises(ValueError, match=re.escape(message)):
            _citry(extensions_defaults={"events": {name: value}})

    @pytest.mark.parametrize("name", ["_csrf_cookie", "_csrf_header"])
    def test_a_component_cannot_set_them(self, name):
        c = _citry()
        with pytest.raises(ValueError, match="is engine-wide configuration"):

            class Page(Component):
                citry = c

                Events = type("Events", (), {name: "csrftoken", "go": lambda _self: None})


class TestPageNonceFromHeaders:
    def test_the_header_name(self):
        assert PAGE_NONCE_HEADER == "X-Citry-Page-Nonce"

    @pytest.mark.parametrize(
        "headers",
        [
            RouteHeaders([("X-Citry-Page-Nonce", "cGFnZS1ub25jZQ==")]),
            {"X-Citry-Page-Nonce": "cGFnZS1ub25jZQ=="},
            # A plain dict that keeps another letter case.
            {"x-citry-page-nonce": "cGFnZS1ub25jZQ=="},
        ],
    )
    def test_reads_a_nonce_of_the_right_shape(self, headers):
        assert page_nonce_from_headers(headers) == "cGFnZS1ub25jZQ=="

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "a b",
            '"><script>',
            # A header sent twice is joined with a comma.
            "one, two",
            "a===",
            "x" * 257,
        ],
    )
    def test_ignores_a_value_of_another_shape(self, value):
        assert page_nonce_from_headers({"X-Citry-Page-Nonce": value}) is None

    def test_a_missing_header_gives_none(self):
        assert page_nonce_from_headers(RouteHeaders()) is None
        assert page_nonce_from_headers({}) is None

    def test_a_nonce_at_the_length_cap_is_read(self):
        assert page_nonce_from_headers({"X-Citry-Page-Nonce": "x" * 256}) == "x" * 256
