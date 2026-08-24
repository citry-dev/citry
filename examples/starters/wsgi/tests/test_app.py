from io import BytesIO

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
    status, _headers, page = wsgi_get("/")
    runtime_status, runtime_headers, _runtime = wsgi_get("/citry/citry.js")

    assert status == "200 OK"
    assert b"Project Explorer" in page
    assert b"Atlas" in page
    assert runtime_status == "200 OK"
    assert runtime_headers["Content-Type"].startswith("text/javascript")


def test_unknown_page_returns_not_found() -> None:
    assert wsgi_get("/missing")[0] == "404 Not Found"
