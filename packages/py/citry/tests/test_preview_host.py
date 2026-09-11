"""Command-owned preview hosting preserves the ordinary application's route table."""

import asyncio
import errno
import socket
import threading
from urllib.request import ProxyHandler, build_opener

import pytest

from citry import Citry
from citry.contrib.asgi import asgi_app
from citry.ext.preview.host import PreviewServer, preview_app
from citry.util.routing import RouteResponse, URLRoute, flatten_routes


def _request(app, path, *, method="GET", query=b"", root_path=""):
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    asyncio.run(
        app(
            {
                "type": "http",
                "path": path,
                "root_path": root_path,
                "method": method,
                "query_string": query,
                "headers": [(b"X-Test", b"yes")],
            },
            receive,
            send,
        )
    )
    return messages[0]["status"], dict(messages[0]["headers"]), messages[1]["body"]


def test_routes_are_private_and_delegate_assets():
    engine = Citry()
    before = [path for path, _route in flatten_routes(engine.urls)]
    routes = (URLRoute("render/{component_id}", handler=lambda _request, component_id: RouteResponse(component_id)),)
    host = preview_app(engine, routes)
    ordinary = asgi_app(engine)
    path = "/citry/ext/preview/render/Widget"
    assert _request(ordinary, path, root_path="/citry")[0] == 404
    assert _request(host, path)[2] == b"Widget"
    assert _request(ordinary, path, root_path="/citry")[0] == 404
    assert [path for path, _route in flatten_routes(engine.urls)] == before
    assert _request(host, "/citry/citry.js")[0] == 200
    assert _request(host, "/citryx/citry.js")[0] == 404


def test_request_translation_head_methods_and_unknown_paths():
    def handler(request):
        assert request.query == {"variant": ("one", ""), "x": ("a b",)}
        assert request.headers["x-test"] == "yes"
        assert request.path == "/citry/ext/preview/catalog"
        assert request.native["path"] == request.path
        return RouteResponse("catalog", content_type="application/json")

    app = preview_app(Citry(), (URLRoute("catalog", handler=handler),))
    status, headers, body = _request(app, "/citry/ext/preview/catalog", query=b"variant=one&variant=&x=a+b")
    assert (status, body) == (200, b"catalog")
    assert headers[b"cache-control"] == b"no-store"
    assert _request(app, "/citry/ext/preview/catalog", method="HEAD", query=b"variant=one&variant=&x=a+b")[2] == b""
    assert _request(app, "/citry/ext/preview/catalog", method="POST")[0] == 405
    assert _request(app, "/citry/ext/preview/missing", method="HEAD")[::2] == (404, b"")


def test_async_twin_is_preferred():
    def sync_handler(request):
        pytest.fail("sync twin called")

    async def async_handler(request):
        return RouteResponse("async")

    app = preview_app(Citry(), (URLRoute("catalog", handler=sync_handler, handler_async=async_handler),))
    assert _request(app, "/citry/ext/preview/catalog")[2] == b"async"


def test_live_server_shutdown_and_engine_overlap():
    pytest.importorskip("uvicorn")
    engine = Citry()
    engine.set_mounted_prefix("/application")
    routes = (URLRoute("catalog", handler=lambda _request: RouteResponse("catalog")),)
    ordinary = asgi_app(engine)
    opener = build_opener(ProxyHandler({}))
    with PreviewServer(engine, routes) as server:
        port = server.port
        assert engine.mounted_prefix == "/citry"
        with opener.open(server.base_url + "/ext/preview/catalog", timeout=2) as response:
            assert response.read() == b"catalog"
        assert _request(ordinary, "/citry/ext/preview/catalog", root_path="/citry")[0] == 404
        with pytest.raises(RuntimeError, match="already running"), PreviewServer(engine, routes):
            pass
        assert engine.mounted_prefix == "/citry"
    assert engine.mounted_prefix == "/application"
    with socket.socket() as probe:
        assert probe.connect_ex(("127.0.0.1", port)) != 0
    with PreviewServer(engine, routes):
        pass


def test_port_conflict_preserves_mount_and_releases_claim():
    pytest.importorskip("uvicorn")
    engine = Citry()
    engine.set_mounted_prefix("/application")
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        with (
            pytest.raises(OSError) as caught,  # noqa: PT011 - assert portable socket codes below.
            PreviewServer(engine, (), port=occupied.getsockname()[1]),
        ):
            pass
        assert caught.value.errno == errno.EADDRINUSE or getattr(caught.value, "winerror", None) == 10048
    assert engine.mounted_prefix == "/application"
    with PreviewServer(engine, ()):
        pass


def test_initialization_failure_releases_engine_claim(monkeypatch):
    pytest.importorskip("uvicorn")
    engine = Citry()
    original = engine.initialize

    def fail():
        raise RuntimeError("initialization failed")

    monkeypatch.setattr(engine, "initialize", fail)
    with pytest.raises(RuntimeError, match="initialization failed"), PreviewServer(engine, ()):
        pass
    assert engine.mounted_prefix is None
    monkeypatch.setattr(engine, "initialize", original)
    with PreviewServer(engine, ()):
        pass


@pytest.mark.parametrize("port", [-1, 65536, True, 1.5])
def test_invalid_ports(port):
    with pytest.raises(ValueError, match="port"):
        PreviewServer(Citry(), (), port=port)


def test_startup_timeout_stops_thread_and_listener(monkeypatch):
    pytest.importorskip("uvicorn")

    # Suppress startup reporting while keeping a real owned listener to exercise cleanup.
    def never_starts(server):
        while not server._server.should_exit:
            threading.Event().wait(0.01)

    monkeypatch.setattr(PreviewServer, "_run", never_starts)
    engine = Citry()
    engine.set_mounted_prefix("/old")
    server = PreviewServer(engine, (), startup_timeout=0.05)
    with pytest.raises(RuntimeError, match="did not become ready"), server:
        pass
    assert not server._thread.is_alive()
    assert engine.mounted_prefix == "/old"
    with socket.socket() as probe:
        assert probe.connect_ex(("127.0.0.1", server.port)) != 0


def test_missing_server_dependency_is_actionable(monkeypatch):
    def missing(name):
        raise ImportError(name)

    monkeypatch.setattr("citry.ext.preview.host.importlib.import_module", missing)
    engine = Citry()
    with pytest.raises(RuntimeError, match=r"citry\[ext-preview\]"), PreviewServer(engine, ()):
        pass
    assert engine.mounted_prefix is None
