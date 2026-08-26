from io import BytesIO

import pytest
from app.data import Project
from app.main import application


def wsgi_get(path: str) -> tuple[str, dict[str, str], bytes]:
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": "GET",
        "SCRIPT_NAME": "",
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "SERVER_NAME": "testserver",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http",
        "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(),
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }
    body = b"".join(application(environ, start_response))
    return captured["status"], captured["headers"], body


def test_page_and_citry_runtime_are_served() -> None:
    status, headers, page = wsgi_get("/")
    runtime_status, runtime_headers, _runtime = wsgi_get("/citry/citry.js")
    events_status, events_headers, _events_runtime = wsgi_get("/citry/ext/events/runtime.js")

    assert status == "200 OK"
    assert headers["Content-Type"].startswith("text/html")
    assert b"Project Explorer" in page
    assert b"Atlas" in page
    assert b"/citry/ext/events/runtime.js" in page
    assert runtime_status == "200 OK"
    assert runtime_headers["Content-Type"].startswith("text/javascript")
    assert events_status == "200 OK"
    assert events_headers["Content-Type"].startswith("text/javascript")


def test_page_escapes_project_data(monkeypatch: pytest.MonkeyPatch) -> None:
    def projects_with_markup() -> tuple[Project, ...]:
        return (Project("<script>alert(1)</script>", "Safe summary", "Active", "Python"),)

    monkeypatch.setattr("app.main.find_projects", projects_with_markup)
    _status, _headers, page = wsgi_get("/")

    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert b"<script>alert(1)</script>" not in page


def test_unknown_page_returns_not_found() -> None:
    assert wsgi_get("/missing")[0] == "404 Not Found"
