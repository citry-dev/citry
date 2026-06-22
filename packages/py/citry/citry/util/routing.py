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
and returning a :class:`RouteResponse`; ``request`` is whatever the adapter
passes (citry's own handlers never read it), so handlers stay host-neutral.

Adapted from django-components' ``URLRoute`` (which was already
framework-free), with two changes: ``methods`` is an explicit field (djc left
method checks to each view), and path parameters use ``{name}`` (matching any
characters except ``/`` and matched in route-definition order), so the
adapters can route without a host framework.

Design: docs/design/dependencies.md section 9.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cache
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence


class URLRouteHandler(Protocol):
    """Framework-neutral "view" function for routes."""

    def __call__(self, request: Any, **kwargs: Any) -> RouteResponse: ...  # pragma: no cover - protocol


@dataclass(frozen=True, slots=True)
class RouteResponse:
    """What a route handler returns; adapters translate it to the host's response type."""

    content: str | bytes = ""
    content_type: str = "text/plain"
    status: int = 200

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
    handler: Callable[..., RouteResponse] | None = None
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
