"""
HTTP-method admission on the Events routes, under the dependency-free adapters.

Every route in ``Citry.urls`` declares its methods as a tuple, so a custom
framework adapter can iterate the table to register or check each route. The
per-event route declares every standard method a handler may use; the
resolved handler then answers a method it did not declare with its own 405
and ``Allow`` list. The Django and FastAPI hosts run the same PUT/DELETE
contract in ``test_events_host_parity.py``; this module covers the raw ASGI
and WSGI apps.
"""

from __future__ import annotations

import asyncio
import io
import json
from typing import Any

import pytest

from citry import Citry, Component
from citry.contrib.asgi import asgi_app
from citry.contrib.wsgi import wsgi_app
from citry.ext.events import event
from citry.ext.events.routes import EVENT_PATH, EVENT_ROUTE_METHODS
from citry.util.routing import flatten_routes

SIGNING_KEY = "route-methods-secret"


class _TextIn:
    text: str


def _replace_component(engine: Citry) -> type[Component]:
    """A component whose one handler accepts PUT and DELETE only."""
    calls: list[str] = []

    class Replacer(Component):
        citry = engine

        class Events:
            @event(methods=("PUT", "DELETE"))
            def replace(self, data: _TextIn) -> dict[str, str]:
                calls.append(data.text)
                return {"replaced": data.text}

        template = """
            <p>replacer</p>
        """

    Replacer.calls = calls  # type: ignore[attr-defined]
    return Replacer


def _wsgi(engine: Citry, method: str, path: str, body: bytes, headers: dict[str, str]) -> tuple[int, dict[str, str]]:
    captured: dict[str, Any] = {}

    def start_response(status: str, response_headers: list[tuple[str, str]]) -> None:
        captured["status"] = int(status.split(" ", 1)[0])
        captured["headers"] = {name.lower(): value for name, value in response_headers}

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_TYPE": "application/json",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        **{"HTTP_" + name.upper().replace("-", "_"): value for name, value in headers.items()},
    }
    b"".join(wsgi_app(engine)(environ, start_response))
    return captured["status"], captured["headers"]


def _asgi(engine: Citry, method: str, path: str, body: bytes, headers: dict[str, str]) -> tuple[int, dict[str, str]]:
    messages: list[dict[str, Any]] = []
    sent = False

    async def receive() -> dict[str, Any]:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "root_path": "",
        "query_string": b"",
        "headers": [
            (b"content-type", b"application/json"),
            *((name.lower().encode(), value.encode()) for name, value in headers.items()),
        ],
    }
    asyncio.run(asgi_app(engine)(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    response_headers = {name.decode("latin-1").lower(): value.decode("latin-1") for name, value in start["headers"]}
    return start["status"], response_headers


def test_every_route_declares_a_method_tuple() -> None:
    engine = Citry()
    flat = flatten_routes(engine.urls)

    # The events extension is on by default, so its per-event route is part
    # of the table this check walks.
    assert any(path.endswith(EVENT_PATH) for path, _route in flat)
    for path, route in flat:
        assert isinstance(route.methods, tuple), path
        assert route.methods, path
        assert all(isinstance(method, str) and method == method.upper() for method in route.methods), path


def test_per_event_route_declares_the_standard_methods() -> None:
    engine = Citry()
    event_route = next(route for path, route in flatten_routes(engine.urls) if path.endswith(EVENT_PATH))
    assert event_route.methods == EVENT_ROUTE_METHODS
    assert set(EVENT_ROUTE_METHODS) >= {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"}


@pytest.mark.parametrize("call", [_wsgi, _asgi], ids=["wsgi", "asgi"])
def test_per_event_put_and_delete_reach_the_handler(call: Any) -> None:
    engine = Citry(secret=SIGNING_KEY)
    component = _replace_component(engine)
    path = f"/ext/events/e/{component.class_id}/replace"
    runtime = {"X-Citry-Events": "1"}

    # Without the runtime header an unsafe method fails the CSRF check.
    status, _headers = call(engine, "PUT", path, json.dumps({"text": "blocked"}).encode(), {})
    assert status == 403

    put_status, _headers = call(engine, "PUT", path, json.dumps({"text": "put"}).encode(), runtime)
    delete_status, _headers = call(engine, "DELETE", path, json.dumps({"text": "delete"}).encode(), runtime)
    assert (put_status, delete_status) == (200, 200)

    # PATCH passes the route's tuple but not the handler's own list, so the
    # handler's 405 names what it accepts.
    patch_status, patch_headers = call(engine, "PATCH", path, json.dumps({"text": "patch"}).encode(), runtime)
    assert (patch_status, patch_headers.get("allow")) == (405, "PUT, DELETE")

    # A method outside the route's tuple stops at the adapter.
    other_status, _headers = call(engine, "PROPFIND", path, b"{}", runtime)
    assert other_status == 405

    assert component.calls == ["put", "delete"]  # type: ignore[attr-defined]


def test_event_decorator_rejects_a_method_the_route_does_not_accept() -> None:
    # The route answers PURGE with the adapter's 405, so a handler declaring
    # it could never be called; the error appears while the class is defined.
    with pytest.raises(ValueError, match="per-event route does not accept") as err:

        class Cache(Component):
            class Events:
                @event(methods=("POST", "purge"))
                def flush(self) -> None:
                    return None

    message = str(err.value)
    assert "'PURGE'" in message
    assert "Cache.Events.flush" in message
    assert "GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS" in message


@pytest.mark.parametrize("method", EVENT_ROUTE_METHODS)
def test_event_decorator_accepts_every_route_method(method: str) -> None:
    @event(methods=(method.lower(),))
    def handler() -> None:
        return None

    assert handler._citry_event_options.methods == (method,)  # type: ignore[attr-defined]


def test_component_methods_default_rejects_a_method_the_route_does_not_accept() -> None:
    engine = Citry(autodiscover=False)
    with pytest.raises(ValueError, match=r"Events\._methods declares HTTP method 'PROPFIND'"):

        class Folder(Component):
            citry = engine

            class Events:
                _methods = ("PROPFIND",)

                def list_files(self) -> None:
                    return None

            template = """
                <p>folder</p>
            """


def test_engine_methods_default_rejects_a_method_the_route_does_not_accept() -> None:
    engine = Citry(autodiscover=False, extensions_defaults={"events": {"_methods": ("LINK",)}})
    with pytest.raises(ValueError, match="'LINK', which the per-event route does not accept"):

        class Share(Component):
            citry = engine

            class Events:
                def share(self) -> None:
                    return None

            template = """
                <p>share</p>
            """
