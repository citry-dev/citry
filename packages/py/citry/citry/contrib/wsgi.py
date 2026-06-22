"""
A generic WSGI sub-application serving a ``Citry`` instance's routes.

The WSGI twin of ``citry.contrib.asgi``, for Flask, Pyramid, Bottle, and
classic Django WSGI. Mount it at a prefix and record the prefix::

    from citry.contrib.wsgi import wsgi_app
    from werkzeug.middleware.dispatcher import DispatcherMiddleware

    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/citry": wsgi_app(citry_instance)})
    citry_instance.set_mounted_prefix("/citry")

Uses no third-party packages; only the WSGI protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from citry.util.routing import match_route

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from citry.citry import Citry

    StartResponse = Callable[[str, list[tuple[str, str]]], Any]
    WSGIApp = Callable[[dict[str, Any], StartResponse], Iterable[bytes]]

_STATUS_LINES = {200: "200 OK", 404: "404 Not Found", 405: "405 Method Not Allowed"}


def wsgi_app(citry_instance: Citry) -> WSGIApp:
    """Build the WSGI application serving ``citry_instance.urls``."""

    def app(environ: dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
        def respond(status: int, content_type: str, body: bytes) -> Iterable[bytes]:
            status_line = _STATUS_LINES.get(status, f"{status} Response")
            start_response(status_line, [("Content-Type", content_type)])
            return [body]

        # When mounted, the host moves the prefix into SCRIPT_NAME; PATH_INFO
        # is the remainder.
        path = environ.get("PATH_INFO", "").lstrip("/")
        matched = match_route(citry_instance.urls, path)
        if matched is None:
            return respond(404, "text/plain", b"Not Found")
        method = environ.get("REQUEST_METHOD", "GET")
        if method not in matched.route.methods and method != "HEAD":
            return respond(405, "text/plain", b"Method Not Allowed")

        handler = matched.route.handler
        assert handler is not None  # noqa: S101 - match_route only returns handler routes
        response = handler(environ, **matched.params)
        return respond(response.status, response.content_type, response.body)

    return app
