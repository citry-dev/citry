"""Every adapter sends a text response built from a string as UTF-8, and its Content-Type says so."""

from __future__ import annotations

import io
from typing import Any

import pytest

from citry import Citry
from citry.contrib.wsgi import wsgi_app
from citry.util.routing import RouteResponse, URLRoute, sent_content_type


@pytest.mark.parametrize(
    ("content", "content_type", "expected"),
    [
        pytest.param("é", "text/plain", "text/plain; charset=utf-8", id="plain_text"),
        pytest.param("é", "text/html", "text/html; charset=utf-8", id="html"),
        pytest.param("é", "TEXT/CSS", "TEXT/CSS; charset=utf-8", id="capitals"),
        pytest.param("é", "text/csv; charset=utf-8", "text/csv; charset=utf-8", id="charset_already_named"),
        pytest.param("é", "text/plain;Charset=Latin-1", "text/plain;Charset=Latin-1", id="another_charset_is_left_alone"),
        pytest.param("{}", "application/json", "application/json", id="json_has_no_charset_parameter"),
        pytest.param(b"\xff", "text/plain", "text/plain", id="bytes_are_sent_as_given"),
        pytest.param("", "text/plain", "text/plain; charset=utf-8", id="empty_text"),
    ],
)
def test_a_text_type_with_a_string_body_names_utf8(content: str | bytes, content_type: str, expected: str) -> None:
    assert sent_content_type(RouteResponse(content=content, content_type=content_type)) == expected


def _get(app: Citry, path: str) -> dict[str, str]:
    captured: dict[str, Any] = {}

    def start_response(_status: str, headers: list[tuple[str, str]]) -> None:
        captured["headers"] = {name.lower(): value for name, value in headers}

    environ = {"REQUEST_METHOD": "GET", "PATH_INFO": path, "SCRIPT_NAME": "", "QUERY_STRING": "", "wsgi.input": io.BytesIO()}
    b"".join(wsgi_app(app)(environ, start_response))
    return captured["headers"]


def test_the_wsgi_adapter_sends_the_charset_for_a_route_that_names_none() -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")
    app.urls.append(URLRoute("ext/hello", handler=lambda _request: RouteResponse(content="é", content_type="text/html")))
    assert _get(app, "/ext/hello")["content-type"] == "text/html; charset=utf-8"
