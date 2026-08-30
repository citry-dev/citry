from collections.abc import Iterable
from typing import Any

from app.citry_app import citry_app
from app.components.project_page import ProjectPage
from app.data import find_projects
from citry.contrib.wsgi import wsgi_app

PREFIX = "/citry"
citry_routes = wsgi_app(citry_app)
citry_app.set_mounted_prefix(PREFIX)
citry_app.initialize()


def application(environ: dict[str, Any], start_response) -> Iterable[bytes]:
    path = environ.get("PATH_INFO", "")
    if path == PREFIX or path.startswith(PREFIX + "/"):
        mounted_environ = dict(environ)
        mounted_environ["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + PREFIX
        mounted_environ["PATH_INFO"] = path[len(PREFIX) :]
        return citry_routes(mounted_environ, start_response)

    if path == "/" and environ.get("REQUEST_METHOD", "GET") in {"GET", "HEAD"}:
        html = str(ProjectPage(projects=find_projects()))
        body = html.encode()
        if environ.get("REQUEST_METHOD") == "HEAD":
            body = b""
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"Not Found"]
