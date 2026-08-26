import asyncio
from collections import deque

import pytest
from app.data import Project
from app.main import application


def asgi_lifespan() -> list[str]:
    received = deque(
        [
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ]
    )
    sent = []

    async def receive():
        return received.popleft()

    async def send(message):
        sent.append(message["type"])

    asyncio.run(application({"type": "lifespan"}, receive, send))
    return sent


def asgi_get(path: str) -> tuple[int, dict[bytes, bytes], bytes]:
    received = deque([{"type": "http.request", "body": b""}])
    sent = []

    async def receive():
        return received.popleft()

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 50000),
    }
    asyncio.run(application(scope, receive, send))
    start, body = sent
    return start["status"], dict(start["headers"]), body["body"]


def test_page_and_citry_runtime_are_served() -> None:
    assert asgi_lifespan() == ["lifespan.startup.complete", "lifespan.shutdown.complete"]

    status, headers, page = asgi_get("/")
    runtime_status, runtime_headers, _runtime = asgi_get("/citry/citry.js")
    events_status, events_headers, _events_runtime = asgi_get("/citry/ext/events/runtime.js")

    assert status == 200
    assert headers[b"content-type"].startswith(b"text/html")
    assert b"Project Explorer" in page
    assert b"Atlas" in page
    assert b"/citry/ext/events/runtime.js" in page
    assert runtime_status == 200
    assert runtime_headers[b"content-type"].startswith(b"text/javascript")
    assert events_status == 200
    assert events_headers[b"content-type"].startswith(b"text/javascript")


def test_page_escapes_project_data(monkeypatch: pytest.MonkeyPatch) -> None:
    def projects_with_markup() -> tuple[Project, ...]:
        return (Project("<script>alert(1)</script>", "Safe summary", "Active", "Python"),)

    monkeypatch.setattr("app.main.find_projects", projects_with_markup)
    _status, _headers, page = asgi_get("/")

    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert b"<script>alert(1)</script>" not in page


def test_unknown_page_returns_not_found() -> None:
    assert asgi_get("/missing")[0] == 404
