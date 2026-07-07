"""
Framework-neutral URL routes.

Citry (and its extensions) serve a few things over HTTP: cached component
JS/CSS, the client-side dependency manager, and later whole components. Citry
itself cannot listen on a port, so it describes its endpoints as
:class:`URLRoute` objects, and a thin adapter per web framework
(``citry.contrib.asgi``, ``citry.contrib.wsgi``, ``citry.contrib.fastapi``,
...) mounts them into the host application. The combined route table is
``Citry.urls``.

A route's ``handler`` is a plain callable taking ``(request, **path_params)``
and returning a :class:`RouteResponse`. ``request`` is a :class:`RouteRequest`,
the same framework-neutral view of the HTTP request under every adapter, with
the untouched host object riding along as ``RouteRequest.native``. Under the
ASGI adapter a handler may also be ``async def`` (see :func:`call_maybe_sync`);
the WSGI and Django adapters run plain handlers only and reject async ones.

Adapted from django-components' ``URLRoute`` (which was already
framework-free), with two changes: ``methods`` is an explicit field (djc left
method checks to each view), and path parameters use ``{name}`` (matching any
characters except ``/`` and matched in route-definition order), so the
adapters can route without a host framework.

Design: docs/design/dependencies.md section 9.
"""

from __future__ import annotations

import asyncio
import inspect
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache, partial
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Iterator, Sequence


class RouteHeaders(Mapping[str, str]):
    """
    A read-only mapping of HTTP header names to values; lookups ignore case.

    Built from ``(name, value)`` pairs. Iteration yields the names lowercased,
    and a header sent multiple times has its values joined with ``", "`` (the
    HTTP rule for repeatable headers).

    Example:
        ```python
        headers = RouteHeaders([("Content-Type", "application/json")])
        headers["content-type"]  # "application/json"
        headers["CONTENT-TYPE"]  # "application/json"
        ```

    """

    __slots__ = ("_data",)

    def __init__(self, items: Iterable[tuple[str, str]] = ()) -> None:
        data: dict[str, str] = {}
        for name, value in items:
            key = name.lower()
            data[key] = f"{data[key]}, {value}" if key in data else value
        self._data = data

    def __getitem__(self, key: str) -> str:
        return self._data[key.lower()]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({list(self._data.items())!r})"


@dataclass(frozen=True, slots=True)
class RouteRequest:
    """
    A framework-neutral view of one HTTP request, passed to route handlers.

    Each web adapter (``citry.contrib.asgi``, ``citry.contrib.wsgi``, the
    Django patterns, ...) builds this from its host's request, so a handler
    reads the same fields no matter which framework serves it. Anything
    host-specific stays reachable through ``native``.

    Attributes:
        method: The HTTP method, uppercase (`"GET"`, `"POST"`, ...).
        path: The full URL path of the request, including the prefix the
            route table is mounted under (e.g. `"/citry/citry.js"`).
        query: The query-string parameters. Each key maps to all values it
            was sent with, in order, so repeated keys are preserved.
        headers: The HTTP request headers; lookups ignore case.
        body: The raw request body. Empty for bodyless methods such as GET.
        content_type: The `Content-Type` header value, or `""` when the
            request names none.
        native: The untouched host request object: the ASGI scope, the WSGI
            environ, or Django's `HttpRequest`.

    """

    method: str = "GET"
    path: str = ""
    query: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    headers: RouteHeaders = field(default_factory=RouteHeaders)
    body: bytes = b""
    content_type: str = ""
    native: Any = None


class URLRouteHandler(Protocol):
    """Framework-neutral "view" function for routes."""

    def __call__(
        self, request: RouteRequest, **kwargs: Any
    ) -> RouteResponse | Awaitable[RouteResponse]: ...  # pragma: no cover - protocol


@dataclass(frozen=True, slots=True)
class RouteResponse:
    """
    What a route handler returns; adapters translate it to the host's response type.

    Attributes:
        content: The response body, as text or raw bytes.
        content_type: The `Content-Type` header value to send.
        status: The HTTP status code.
        headers: Extra response headers, as `(name, value)` pairs; adapters
            send them in addition to `Content-Type`. A name may repeat (e.g.
            two `Set-Cookie` lines): the ASGI and WSGI adapters send every
            pair, while the Django adapter raises `ValueError` on a repeated
            name, because Django's response object holds one value per header
            name.

    """

    content: str | bytes = ""
    content_type: str = "text/plain"
    status: int = 200
    headers: tuple[tuple[str, str], ...] = ()

    @property
    def body(self) -> bytes:
        """The content as bytes (utf8-encoded when given as a string)."""
        return self.content.encode() if isinstance(self.content, str) else self.content


@dataclass(frozen=True, slots=True)
class URLRoute:
    """
    One framework-neutral route: either a ``handler`` or nested ``children``.

    A child's full path is the parent's path followed by the child's (plain
    concatenation; end a parent path with ``/``). ``{name}`` segments in the
    path become keyword arguments of the handler.

    Example::

        URLRoute("cache/{class_id}.{script_type}", handler=serve_script, name="citry_cached_script")
        URLRoute("ext/", children=[URLRoute("my_ext/status", handler=status)])
    """

    path: str
    # Typed with an ellipsis signature: a concrete handler names its path
    # parameters as keyword arguments (see URLRouteHandler for the calling
    # convention), which a (request, **kwargs) callable type cannot express.
    # The Awaitable side of the union admits `async def` handlers, which the
    # ASGI adapter awaits (the sync adapters reject them).
    handler: Callable[..., RouteResponse | Awaitable[RouteResponse]] | None = None
    children: tuple[URLRoute, ...] = ()
    name: str | None = None
    methods: tuple[str, ...] = ("GET",)
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.handler is not None and self.children:
            msg = "URLRoute cannot have both a handler and children"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class MatchedRoute:
    """One resolved request: the route, its full path pattern, and the extracted path parameters."""

    route: URLRoute
    full_path: str
    params: dict[str, str]


def flatten_routes(routes: Iterable[URLRoute]) -> list[tuple[str, URLRoute]]:
    """All handler routes in a route tree, as ``(full_path, route)``, in definition order."""
    flat: list[tuple[str, URLRoute]] = []

    def walk(prefix: str, items: Iterable[URLRoute]) -> None:
        for route in items:
            full_path = prefix + route.path
            if route.handler is not None:
                flat.append((full_path, route))
            walk(full_path, route.children)

    walk("", routes)
    return flat


# A path parameter: `{name}` where name is a Python identifier.
_PARAM_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


@cache
def compile_route_pattern(path: str) -> re.Pattern[str]:
    """Compile a route path into a regex: ``{name}`` matches any characters except ``/``."""
    pattern = ""
    last_end = 0
    for match in _PARAM_RE.finditer(path):
        pattern += re.escape(path[last_end : match.start()])
        pattern += f"(?P<{match.group(1)}>[^/]+)"
        last_end = match.end()
    pattern += re.escape(path[last_end:])
    return re.compile(f"^{pattern}$")


def match_route(routes: Sequence[URLRoute], path: str) -> MatchedRoute | None:
    """
    Resolve a request path (no leading slash) against a route tree.

    Routes are tried in definition order; the first match wins, so define
    more specific patterns first (e.g. the two-parameter
    ``cache/{class_id}.{vars_hash}.{script_type}`` before the one-parameter
    ``cache/{class_id}.{script_type}``).
    """
    for full_path, route in flatten_routes(routes):
        match = compile_route_pattern(full_path).match(path)
        if match is not None:
            return MatchedRoute(route=route, full_path=full_path, params=match.groupdict())
    return None


_R = TypeVar("_R")


async def call_maybe_sync(fn: Callable[..., _R | Awaitable[_R]], /, *args: Any, **kwargs: Any) -> _R:
    """
    Call ``fn`` from async code without caring whether it is async itself.

    An ``async def`` function is awaited on the running event loop. A plain
    function runs in the loop's default worker-thread pool, so a slow or
    blocking callable does not stall the loop (and everything else it is
    serving). The ASGI adapter calls every route handler through this.

    Args:
        fn: The function to call (positional-only, so it cannot clash with a
            keyword argument meant for ``fn`` itself).
        *args: Positional arguments passed through to ``fn``.
        **kwargs: Keyword arguments passed through to ``fn``.

    Returns:
        ``fn``'s result, awaited when ``fn`` is async.

    """
    if inspect.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)
    loop = asyncio.get_running_loop()
    # partial() binds the arguments because run_in_executor accepts none itself.
    result = await loop.run_in_executor(None, partial(fn, *args, **kwargs))
    # This branch only runs plain callables, so the result is already the final
    # value; the cast spells out what the union-typed signature cannot.
    return cast("_R", result)
