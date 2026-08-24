import asyncio
from collections import deque

from app.main import application


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
    status, _headers, page = asgi_get("/")
    runtime_status, runtime_headers, _runtime = asgi_get("/citry/citry.js")

    assert status == 200
    assert b"Project Explorer" in page
    assert b"Atlas" in page
    assert runtime_status == 200
    assert runtime_headers[b"content-type"].startswith(b"text/javascript")


def test_unknown_page_returns_not_found() -> None:
    assert asgi_get("/missing")[0] == 404
