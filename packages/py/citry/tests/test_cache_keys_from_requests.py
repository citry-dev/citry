"""Text a request chooses reaches the cache only in the shape Citry itself writes, so no backend can answer 500."""

from __future__ import annotations

import io
import json
import re
from typing import TYPE_CHECKING
from urllib.parse import unquote_to_bytes

import pytest
from flask import Flask

from citry import Citry, Component, InMemoryCache
from citry.contrib.flask import mount
from citry.contrib.wsgi import wsgi_app

if TYPE_CHECKING:
    from pathlib import Path


class StrictKeyCache(InMemoryCache):
    """A cache that refuses keys as Django's memcached backend does: too long, or with a space or control character."""

    def __init__(self) -> None:
        super().__init__()
        self.reads: list[str] = []

    def get(self, key: str) -> str | None:
        self.reads.append(key)
        if len(key) > 250 or any(ord(char) < 33 or ord(char) == 127 for char in key):
            raise ValueError(f"key refused: {key[:40]!r}")
        return super().get(key)


def _request(app: Citry, method: str, path: str, body: bytes = b"", headers: dict[str, str] | None = None) -> str:
    environ: dict[str, object] = {
        "REQUEST_METHOD": method,
        # `path` is what the browser sends. A WSGI server decodes its
        # percent escapes and hands the bytes on read as latin-1 (PEP 3333).
        "PATH_INFO": unquote_to_bytes(path).decode("latin-1"),
        "SCRIPT_NAME": "/citry",
        "SERVER_NAME": "testserver",
        "SERVER_PORT": "80",
        "HTTP_HOST": "testserver",
        "QUERY_STRING": "",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(body),
    }
    for name, value in (headers or {}).items():
        environ["CONTENT_TYPE" if name == "Content-Type" else "HTTP_" + name.upper().replace("-", "_")] = value
    statuses: list[str] = []
    b"".join(wsgi_app(app)(environ, lambda status, _headers: statuses.append(status)))
    return statuses[0]


def _app() -> tuple[Citry, StrictKeyCache, type[Component]]:
    cache = StrictKeyCache()
    app = Citry(secret="cache-key-shape-secret-0123456789abcdef", cache=cache)  # noqa: S106 - a test value
    app.set_mounted_prefix("/citry")

    class Stored(Component):
        citry = app
        template = """
            <div>s</div>
        """
        css = """
            div { color: var(--c); }
        """

        def css_data(self, kwargs, slots):
            return {"c": "red"}

        class State:
            count: int = 0
            _storage = "server"

        class Events:
            def bump(self, state):
                state.count += 1

    return app, cache, Stored


def _call(app: Citry, component: type[Component], token: str) -> tuple[str, str]:
    envelope = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "calls": [
            {
                "componentClassId": component.class_id,
                "handlerName": "bump",
                "callerRenderId": "x1",
                "args": {},
                "stateToken": token,
            }
        ],
    }
    status = _request(
        app,
        "POST",
        f"/ext/events/e/{component.class_id}/bump",
        json.dumps(envelope).encode(),
        {
            "Content-Type": "application/citry-events+json",
            "X-Citry-Events": "1",
            "Origin": "http://testserver",
            "Sec-Fetch-Site": "same-origin",
        },
    )
    return status, token


def test_a_minted_server_token_still_reaches_its_state() -> None:
    app, _cache, stored = _app()
    token = re.search(r"ces1\.[A-Za-z0-9_-]+", stored().render().serialize())
    assert token is not None
    status, _token = _call(app, stored, token.group())
    assert status.startswith("200")


@pytest.mark.parametrize(
    "key",
    [
        pytest.param("a" * 300, id="long"),
        pytest.param("a b", id="space"),
        pytest.param("a\nb", id="newline"),
        pytest.param("a" * 42, id="one_short"),
    ],
)
def test_a_server_token_key_of_another_shape_is_refused_before_the_cache(key: str) -> None:
    app, cache, stored = _app()
    cache.reads.clear()
    status, _token = _call(app, stored, f"ces1.{key}")
    assert status.startswith("403")
    assert not any(read.startswith("citry:state:") for read in cache.reads)


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/cache/{class_id}." + "a" * 300 + ".css", id="script_hash_long"),
        pytest.param("/cache/{class_id}.a b.css", id="script_hash_space"),
        pytest.param("/asset/" + "a" * 300 + ".css", id="asset_long"),
        pytest.param("/asset/a b.css", id="asset_space"),
    ],
)
def test_a_file_name_of_another_shape_is_a_miss_before_the_cache(path: str) -> None:
    app, cache, stored = _app()
    cache.reads.clear()
    assert _request(app, "GET", path.format(class_id=stored.class_id)).startswith("404")
    assert cache.reads == []


@pytest.mark.parametrize(
    "extension",
    [
        pytest.param("x" * 129, id="extension_over_128_bytes"),
        pytest.param("\U0001f600" * 33, id="non_ascii_extension_over_128_bytes"),
        pytest.param("c/ss", id="slash"),
        pytest.param("c\tss", id="tab"),
        pytest.param("caf%C3%A9", id="non_ascii_as_a_browser_sends_it"),
    ],
)
def test_an_asset_extension_a_page_never_links_is_a_miss_before_the_cache(extension: str) -> None:
    app, cache, _stored = _app()
    cache.reads.clear()
    assert _request(app, "GET", f"/asset/0123456789ab.{extension}").startswith("404")
    assert cache.reads == []


def _served_card(app: Citry, file_name: str) -> type[Component]:
    class Card(Component):
        citry = app
        template = """
            <p class="card">card</p>
        """

        class Dependencies:
            css = file_name
            local_files = "serve"

    return Card


@pytest.mark.parametrize(
    "extension",
    [
        pytest.param("css", id="css"),
        pytest.param("x" * 128, id="extension_of_128_characters"),
        pytest.param("a~b+c-d_e", id="punctuation_a_url_keeps"),
    ],
)
def test_a_served_file_whose_extension_reaches_the_server_unchanged_is_linked(tmp_path: Path, extension: str) -> None:
    (tmp_path / f"theme.{extension}").write_text(".theme { color: teal; }")
    cache = StrictKeyCache()
    app = Citry(dirs=[tmp_path], cache=cache)
    host = Flask(__name__)
    mount(host, app)
    html = _served_card(app, f"theme.{extension}")().render().serialize()
    found = re.search(r'href="/citry(/asset/[^"]+)"', html)
    assert found is not None
    # Through a WSGI server, and through Flask's own request handling.
    assert _request(app, "GET", found.group(1)).startswith("200")
    assert host.test_client().get("/citry" + found.group(1)).status_code == 200


@pytest.mark.parametrize(
    "extension",
    [
        pytest.param("c ss", id="space"),
        pytest.param("café", id="non_ascii"),
        pytest.param("c#ss", id="fragment_mark"),
        pytest.param("c?ss", id="query_mark"),
        pytest.param("c%2fss", id="percent_escape"),
        pytest.param("x" * 129, id="over_128_characters"),
    ],
)
def test_a_served_file_whose_extension_a_url_could_change_is_inlined(tmp_path: Path, extension: str) -> None:
    # A link to such a file would not reach the asset route unchanged from
    # every browser and server, so the page carries the file itself.
    (tmp_path / f"theme.{extension}").write_text(".theme { color: teal; }")
    app = Citry(dirs=[tmp_path], cache=StrictKeyCache())
    app.set_mounted_prefix("/citry")
    html = _served_card(app, f"theme.{extension}")().render().serialize()
    assert "/asset/" not in html
    assert ".theme { color: teal; }" in html
