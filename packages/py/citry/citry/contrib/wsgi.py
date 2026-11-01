"""
A generic WSGI sub-application serving a ``Citry`` instance's routes.

The WSGI twin of ``citry.contrib.asgi``, for Flask, Pyramid, Bottle, and
classic Django WSGI. Mount it at a prefix and record the prefix::

    from citry.contrib.wsgi import wsgi_app
    from werkzeug.middleware.dispatcher import DispatcherMiddleware

    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/citry": wsgi_app(citry_instance)})
    citry_instance.set_mounted_prefix("/citry")

Uses no third-party packages; only the WSGI protocol. WSGI is synchronous,
so route handlers must be plain functions; an ``async def`` handler is
rejected with an error pointing at the ASGI adapter.

Like every citry.contrib adapter, the app does one job in three steps:
translate the host's request into a framework-neutral ``RouteRequest``,
hand it to the matched citry route handler, and translate the returned
``RouteResponse`` back into the host's response shape (here: the
``start_response`` call plus a body iterable). Everything else in this
file is WSGI-protocol bookkeeping.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import parse_qs

from citry.util.routing import RouteHeaders, RouteRequest, RouteResponse, body_read_limit, match_route, sent_headers

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from citry.citry import Citry

    StartResponse = Callable[[str, list[tuple[str, str]]], Any]
    WSGIApp = Callable[[dict[str, Any], StartResponse], Iterable[bytes]]

__all__ = ["wsgi_app"]

_STATUS_LINES = {200: "200 OK", 404: "404 Not Found", 405: "405 Method Not Allowed"}


def _read_body(environ: dict[str, Any], limit: int | None) -> bytes:
    """
    Read the request body from ``wsgi.input``, at most ``limit`` bytes when a limit is set.

    ``Content-Length`` is the client's own claim, so with a limit it only
    caps how much is asked for: a larger claim still reads at most
    ``limit`` bytes. A body without a ``Content-Length`` (a chunked upload)
    is read only when the server says the stream ends with the body
    (``wsgi.input_terminated``); otherwise reading could wait forever.
    """
    # A request without a body may come without a stream at all.
    stream = environ.get("wsgi.input")
    if stream is None:
        return b""
    try:
        content_length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        content_length = 0
    if limit is None:
        return stream.read(content_length) if content_length > 0 else b""
    if content_length > 0:
        wanted = min(content_length, limit)
    elif environ.get("wsgi.input_terminated"):
        wanted = limit
    else:
        return b""
    # read(n) may return fewer bytes than asked for, so keep reading until
    # the stream ends or the limit is reached.
    chunks: list[bytes] = []
    received = 0
    while received < wanted:
        chunk = stream.read(wanted - received)
        if not chunk:
            break
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)


def _build_request(environ: dict[str, Any], method: str, body_limit: int | None) -> RouteRequest:
    """Read the WSGI environ into a framework-neutral request."""
    header_items: list[tuple[str, str]] = [
        (key[len("HTTP_") :].replace("_", "-"), value) for key, value in environ.items() if key.startswith("HTTP_")
    ]
    # Per the WSGI spec, these two ride outside the HTTP_* namespace.
    if environ.get("CONTENT_TYPE"):
        header_items.append(("Content-Type", environ["CONTENT_TYPE"]))
    if environ.get("CONTENT_LENGTH"):
        header_items.append(("Content-Length", environ["CONTENT_LENGTH"]))
    headers = RouteHeaders(header_items)

    body = _read_body(environ, body_limit)

    query = {
        key: tuple(values) for key, values in parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True).items()
    }
    return RouteRequest(
        method=method,
        path=environ.get("SCRIPT_NAME", "") + environ.get("PATH_INFO", ""),
        query=query,
        headers=headers,
        body=body,
        content_type=headers.get("content-type", ""),
        native=environ,
    )


def wsgi_app(citry_instance: Citry) -> WSGIApp:
    """
    Build the WSGI application serving ``citry_instance.urls``.

    The returned app routes each request to the matching citry handler.
    It builds a [`RouteRequest`][citry.RouteRequest] from the WSGI environ,
    calls the handler, and turns the returned
    [`RouteResponse`][citry.RouteResponse] into a WSGI response. Because
    WSGI is synchronous, a request that reaches an ``async def`` handler
    raises ``TypeError`` before the handler runs, and the message points to
    the ASGI adapter.
    """

    def app(environ: dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
        def respond(response: RouteResponse) -> Iterable[bytes]:
            """Translate a ``RouteResponse`` into the WSGI response shape."""
            status_line = _STATUS_LINES.get(response.status, f"{response.status} Response")
            start_response(status_line, [("Content-Type", response.content_type), *sent_headers(response)])
            return [response.body]

        # When mounted, the host moves the prefix into SCRIPT_NAME; PATH_INFO
        # is the remainder.
        path = environ.get("PATH_INFO", "").lstrip("/")
        matched = match_route(citry_instance.urls, path)
        if matched is None:
            return respond(RouteResponse(content="Not Found", status=404))
        method = environ.get("REQUEST_METHOD", "GET")
        if method not in matched.route.methods and method != "HEAD":
            return respond(RouteResponse(content="Method Not Allowed", status=405))

        handler = matched.route.handler
        assert handler is not None  # noqa: S101 - match_route only returns handler routes
        if inspect.iscoroutinefunction(handler):
            msg = (
                f"citry route {matched.route.name or matched.full_path!r} has an 'async def' handler, "
                "which the synchronous WSGI adapter cannot run. Serve citry through the ASGI adapter "
                "instead (citry.contrib.asgi.asgi_app, or citry.contrib.fastapi.mount), or make the "
                "handler a plain 'def'."
            )
            raise TypeError(msg)
        # The guard above rejected async handlers, so the call returns a
        # concrete RouteResponse.
        response = cast(
            "RouteResponse", handler(_build_request(environ, method, body_read_limit(matched.route)), **matched.params)
        )
        return respond(response)

    return app
