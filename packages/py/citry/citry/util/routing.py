"""
Framework-neutral URL routes.

Citry (and its extensions) serve a few things over HTTP: cached component
JS/CSS, Citry's browser runtime, event calls, and component previews. Citry
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
A route that must serve the sync hosts and still run natively on an event
loop carries both: the plain ``handler`` every adapter mounts, plus an
``async def`` twin on ``handler_async`` that the ASGI adapter prefers.

Adapted from django-components' ``URLRoute`` (which was already
framework-free), with two changes: ``methods`` is an explicit field (djc left
method checks to each view), and path parameters use ``{name}`` (one or more
characters except ``/``), matched by Citry's own matcher in route-definition
order, so the adapters can route without a host framework.

Design: docs/design/dependencies.md section 9.
"""

from __future__ import annotations

import asyncio
import inspect
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache
from itertools import pairwise
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
        content_type: The `Content-Type` header value to send. A `text/*`
            type with a ``str`` body and no ``charset`` is sent with
            `; charset=utf-8`, because the adapters encode the string as UTF-8.
        status: The HTTP status code.
        headers: Extra response headers, as `(name, value)` pairs; adapters
            send them in addition to `Content-Type`. Adapters also send
            `X-Content-Type-Options: nosniff` unless this sets that header,
            so the browser uses `content_type` as given; set it to the
            body's real type. A name may repeat (e.g.
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

    A child's full path is the parent's path followed by the child's, joined
    as plain text, so end a parent path with ``/`` when the child starts a
    new segment. A ``{name}`` parameter
    in the path becomes a keyword argument of the handler.

    ``handler_async`` optionally carries an ``async def`` twin of ``handler``
    (same signature and behavior). Adapters that run an event loop (ASGI)
    serve the route through the twin, awaiting it natively, while the plain
    ``handler`` stays what the sync hosts (WSGI, sync Django) mount and run.
    Only routes that need both worlds carry it; a route table meant solely
    for ASGI can simply pass an ``async def`` function as ``handler``.

    Example::

        URLRoute(
            "files/{folder}/{name}.{ext}",
            handler=serve_file,
            name="my_ext_file",
            dotless_params=frozenset({"name"}),
        )
        URLRoute(
            "ext/",
            children=[URLRoute("my_ext/status", handler=status)],
        )

    The request path must match the full path exactly. A parameter takes
    one or more characters and never a ``/``, so a parameter ends at the
    next ``/`` or at the fixed text that follows it. When that fixed text
    could also fall inside the value, as with ``{name}.{ext}`` and the path
    ``files/docs/report.v2.txt``, each parameter takes as much as it can,
    the earlier one first: without ``dotless_params``, the route would give
    ``name="report.v2"`` and ``ext="txt"``.

    A parameter listed in ``dotless_params`` never holds a ``.`` and ends
    at the first one, which gives ``name="report"`` and ``ext="v2.txt"``
    in the route above. Only the ``dotless_params`` of the route that has
    the handler applies, not a parent's, even for parameters in the
    parent's path.

    Two parameters with nothing between them, such as ``{year}{month}``,
    have no single correct split, so the web framework integrations raise
    ``ValueError`` for such a route when they mount the routes. That
    includes a parent path that ends in a parameter joined to a child path
    that starts with one. A path that uses one parameter name twice raises
    ``ValueError`` the same way.

    ``methods`` is always a non-empty tuple of uppercase HTTP method names
    (``("GET",)``, ``("POST", "PUT")``), so an adapter can iterate it to
    register or check the route. Any other value raises ``TypeError`` (not a
    tuple of strings) or ``ValueError`` (empty, or a name that is not an
    uppercase HTTP method token such as ``"get"``) when the route is built.
    Adapters answer any other method with 405. A route that lists ``GET``
    also accepts ``HEAD`` (see :func:`route_allows_method`). When a route
    admits more methods than its handler serves, the handler answers 405
    for the rest.

    ``max_body_bytes`` is an optional function that returns the largest
    request body the route accepts. Citry calls it for each request, so the
    limit can follow a setting. The ASGI, WSGI, and Django integrations then
    read at most one byte more than the limit (under ASGI, at most one more
    message), whatever ``Content-Length`` says, so a client cannot make the
    server hold a large body in memory. ``request.body`` then holds at most
    the limit plus one byte, and the handler must reject a body longer than
    the limit, because that body was cut short. ``None`` (the default) reads
    the whole body. No adapter reads the body of a GET, HEAD or OPTIONS
    request, whatever the limit. The limit applies to this route only, not to its
    ``children``. A function that returns something other than an ``int``
    of 0 or more makes each request fail with an error, which the web
    framework answers with status 500.
    """

    path: str
    # Typed with an ellipsis signature: a concrete handler names its path
    # parameters as keyword arguments (see URLRouteHandler for the calling
    # convention), which a (request, **kwargs) callable type cannot express.
    # The Awaitable side of the union admits `async def` handlers, which the
    # ASGI adapter awaits (the sync adapters reject them).
    handler: Callable[..., RouteResponse | Awaitable[RouteResponse]] | None = None
    handler_async: Callable[..., Awaitable[RouteResponse]] | None = None
    children: tuple[URLRoute, ...] = ()
    name: str | None = None
    methods: tuple[str, ...] = ("GET",)
    extra: dict[str, Any] = field(default_factory=dict)
    max_body_bytes: Callable[[], int] | None = None
    # Path parameters whose values never hold a `.`; each ends at the first
    # `.`. Citry's own cache routes use this so a class id followed by
    # `.js` or `.<hash>.css` splits at the first dot.
    dotless_params: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if self.handler is not None and self.children:
            msg = "URLRoute cannot have both a handler and children"
            raise ValueError(msg)
        if self.handler_async is not None and self.handler is None:
            msg = (
                "URLRoute got handler_async without a handler. The async twin rides alongside a plain"
                " 'def' handler (what the sync adapters mount and run); pass handler as well. For a"
                " route served only under ASGI, pass the async function as handler instead."
            )
            raise ValueError(msg)
        _validate_route_methods(self.methods)
        if self.max_body_bytes is not None and not callable(self.max_body_bytes):
            msg = (
                "URLRoute(max_body_bytes=...) must be a function that returns the limit in bytes,"
                f" such as lambda: 64_000; got {self.max_body_bytes!r}."
            )
            raise TypeError(msg)


# An HTTP method is an RFC 9110 token. Adapters compare the request's method
# with these names exactly, so a lowercase name would never match and the
# route would answer 405 to every request; only uppercase tokens are accepted.
_ROUTE_METHOD_RE = re.compile(r"[!#$%&'*+.^_`|~0-9A-Z-]+")


# The standard header that tells the browser to use the declared
# Content-Type and never guess another one from the body.
_NOSNIFF_HEADER = ("X-Content-Type-Options", "nosniff")


def sent_headers(response: RouteResponse) -> tuple[tuple[str, str], ...]:
    """
    Return the headers an adapter sends besides `Content-Type`.

    Every adapter calls this, so each Citry response carries the same
    standard headers: the response's own, plus
    `X-Content-Type-Options: nosniff` unless the response sets it itself.
    """
    if any(name.lower() == "x-content-type-options" for name, _ in response.headers):
        return response.headers
    return (*response.headers, _NOSNIFF_HEADER)


def sent_content_type(response: RouteResponse) -> str:
    """
    Return the `Content-Type` an adapter sends for ``response``.

    Every adapter sends a ``str`` body as UTF-8 bytes. A `text/*` type that
    names no charset would leave the browser to decode those bytes with a guess
    or with the encoding of the page that links the file, so such a type gets
    `; charset=utf-8`. A ``bytes`` body, a type that names a charset, and a
    type that is not `text/*` (such as `application/json`) are sent as given.
    """
    lowered = response.content_type.lower()
    if not isinstance(response.content, str) or not lowered.startswith("text/") or "charset=" in lowered:
        return response.content_type
    return f"{response.content_type}; charset=utf-8"


# Methods whose requests carry no body a route can use. Every adapter skips
# reading the body for them, so Citry reads none of a large body sent with a
# GET, whatever limit the route sets.
BODYLESS_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def body_read_limit(route: URLRoute) -> int | None:
    """
    Return how many body bytes an adapter reads for ``route``, or ``None`` to read the whole body.

    One byte past the route's limit is enough for the handler to see that
    the body is too long, so the adapter never reads more than that.
    """
    if route.max_body_bytes is None:
        return None
    limit = route.max_body_bytes()
    if isinstance(limit, bool) or not isinstance(limit, int):
        msg = f"URLRoute(max_body_bytes=...) must return an int byte count; got {limit!r}."
        raise TypeError(msg)
    if limit < 0:
        msg = f"URLRoute(max_body_bytes=...) must return a byte count of 0 or more; got {limit!r}."
        raise ValueError(msg)
    return limit + 1


def _validate_route_methods(methods: object) -> None:
    """Reject a ``URLRoute.methods`` value the adapters could not register."""
    # A bare string is iterable, so ("GET") silently becoming "G", "E", "T" is caught here first.
    if not isinstance(methods, tuple) or not all(isinstance(method, str) for method in methods):
        msg = f'URLRoute(methods=...) must be a tuple of HTTP method names, e.g. ("POST",); got {methods!r}.'
        raise TypeError(msg)
    # A route that admits no method could never be reached.
    if not methods:
        msg = "URLRoute(methods=...) must name at least one HTTP method; got an empty tuple."
        raise ValueError(msg)
    invalid = next((method for method in methods if _ROUTE_METHOD_RE.fullmatch(method) is None), None)
    if invalid is not None:
        msg = (
            f"URLRoute(methods=...) contains {invalid!r}, which is not an uppercase HTTP method name."
            ' Write method names in uppercase, e.g. ("GET", "POST").'
        )
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


def normalize_mount_prefix(prefix: str) -> str:
    """
    Check a mount prefix and return it without a trailing ``/``.

    Every host adapter calls this before it changes the host app or the Citry
    instance, so a bad prefix fails with the same ``ValueError`` everywhere and
    leaves nothing half-mounted. ``"/citry/"`` and ``"/citry"`` mount at the
    same place, and ``"/"`` becomes ``""`` (the host's root).

    Raises:
        ValueError: If ``prefix`` does not start with ``/``.

    """
    if not prefix.startswith("/"):
        msg = f"Mount prefix must start with '/', got {prefix!r}"
        raise ValueError(msg)
    return prefix.rstrip("/")


# A path parameter: `{name}` where name is a Python identifier. Any other
# text, including a `{` that does not start a parameter, is fixed text.
_PARAM_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


@cache
def compile_route_pattern(path: str, dotless_params: frozenset[str] = frozenset()) -> re.Pattern[str]:
    """
    Build a regex that describes a route path, for Django's ``reverse()`` and URL checks.

    Each ``{name}`` becomes a named group of one or more characters other
    than ``/`` (and other than ``.`` for a parameter in ``dotless_params``),
    and the text around the parameters must appear as written. The Django
    integration registers this regex so that ``reverse()`` and Django's URL
    checks know the route's parameters. No adapter matches a request path
    against it: with several parameters in one path segment, Python's regex
    engine can take time that grows much faster than the path's length, so
    every adapter matches requests with :func:`match_route_pattern`.
    """
    pattern = ""
    last_end = 0
    for match in _PARAM_RE.finditer(path):
        pattern += re.escape(path[last_end : match.start()])
        characters = "[^/.]" if match.group(1) in dotless_params else "[^/]"
        pattern += f"(?P<{match.group(1)}>{characters}+)"
        last_end = match.end()
    pattern += re.escape(path[last_end:])
    return re.compile(f"^{pattern}$")


def check_route_table(routes: Iterable[URLRoute]) -> None:
    """
    Check the full path of every handler route in a route tree.

    A route's full path is its parents' paths followed by its own, joined
    as plain text, so a problem can come from the join itself. The web
    framework integrations call this when they mount the routes, so a bad
    route fails when the app starts rather than on a request.

    Raises:
        ValueError: If a full path uses one parameter name twice, or puts two
            parameters next to each other with nothing between them (such as
            ``{a}{b}``). The message names the route, and both the parent and
            the child route when joining their paths made the problem.

    """

    def walk(chain: tuple[URLRoute, ...], items: Iterable[URLRoute]) -> None:
        for route in items:
            here = (*chain, route)
            if route.handler is not None:
                _check_full_path(tuple((item.path, item.name) for item in here))
            walk(here, route.children)

    walk((), routes)


def _route_label(path: str, name: str | None) -> str:
    """Describe one route for an error message: its own path, and its name when it has one."""
    return f"{path!r} (name {name!r})" if name else repr(path)


def _check_full_path(chain: tuple[tuple[str, str | None], ...]) -> None:
    """
    Raise ``ValueError`` when a route's full path repeats a parameter or puts two side by side.

    ``chain`` holds the ``(path, name)`` of each route from the outermost
    parent down to the route itself; their paths joined make the full path.
    """
    full_path = "".join(path for path, _name in chain)
    # Where each route's own path starts in the full path, so a parameter
    # can be traced back to the route that wrote it.
    starts: list[int] = []
    offset = 0
    for path, _name in chain:
        starts.append(offset)
        offset += len(path)

    def owner(position: int) -> int:
        # The last route starting at or before the position wrote it; a
        # route with an empty path starts where the next one does, so it is
        # skipped.
        return max(index for index, start in enumerate(starts) if start <= position)

    own_path, own_name = chain[-1]
    # The route's own path is what its author wrote; the full path shows
    # what the parents added in front of it.
    details = [f"name {own_name!r}"] if own_name else []
    if len(chain) > 1:
        details.append(f"full path {full_path!r}")
    where = repr(own_path) + (f" ({', '.join(details)})" if details else "")

    def written_by(index: int) -> str:
        # Name the route whose own path holds the problem, which can be a
        # parent of the route that has the handler.
        if index == len(chain) - 1:
            return where
        return (
            f"{_route_label(*chain[index])}, a parent of {_route_label(own_path, own_name)} (full path {full_path!r}),"
        )

    params = list(_PARAM_RE.finditer(full_path))

    # The handler receives each parameter as a keyword argument, so two with
    # one name could not both reach it.
    first_seen: dict[str, int] = {}
    for match in params:
        name = match.group(1)
        if name in first_seen:
            earlier, later = owner(first_seen[name]), owner(match.start())
            who = written_by(earlier) if earlier == later else where
            msg = (
                f"The URLRoute path {who} uses the parameter {{{name}}} twice. The handler receives each"
                " parameter as a keyword argument, so give each one its own name."
            )
            if earlier != later:
                msg += (
                    f" One comes from the earlier path {_route_label(*chain[earlier])} and one from"
                    f" {_route_label(*chain[later])}."
                )
            raise ValueError(msg)
        first_seen[name] = match.start()

    # Two parameters with nothing between them have no single place where
    # one ends and the next begins, so the route has no one right split.
    for current, following in pairwise(params):
        if current.end() != following.start():
            continue
        names = f"{{{current.group(1)}}} and {{{following.group(1)}}}"
        parent, child = owner(current.start()), owner(following.start())
        if parent == child:
            msg = (
                f"The URLRoute path {written_by(parent)} puts the parameters {names} next to each other with nothing"
                " between them, so Citry cannot tell where one ends and the next begins. Put fixed text"
                " between them, such as '/' or '.'."
            )
        else:
            msg = (
                f"The URLRoute path {_route_label(*chain[child])} is joined to the path before it,"
                f" {_route_label(*chain[parent])}, as plain text, which makes {full_path!r} and puts the"
                f" parameters {names} next to each other with nothing between them. Citry cannot tell"
                " where one ends and the next begins. End the parent path with '/', or start the child"
                " path with fixed text."
            )
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class _RouteSegment:
    """
    The part of a route path between two ``/``, split at its parameters.

    ``literals`` holds the fixed text around the parameters, one more entry
    than ``params``: the text before the first parameter, the text between
    each pair, and the text after the last. Each entry of ``params`` is the
    parameter's name and whether it is dotless (excludes ``.``).
    """

    literals: tuple[str, ...]
    params: tuple[tuple[str, bool], ...]


@cache
def _parse_route_path(path: str, dotless_params: frozenset[str]) -> tuple[_RouteSegment, ...]:
    """
    Split a full route path into its segments, after checking it.

    Raises the same ``ValueError`` as :func:`check_route_table`, so a route
    that skipped that check (one built after the routes were mounted, or
    matched with :func:`match_route` directly) is refused on every request
    path rather than matched by an arbitrary split.
    """
    _check_full_path(((path, None),))
    segments: list[_RouteSegment] = []
    literals = [""]
    params: list[tuple[str, bool]] = []

    def add_text(text: str) -> None:
        # A `/` in the fixed text ends the current segment; parameters never
        # hold a `/`, so the request path's segments line up with these.
        pieces = text.split("/")
        literals[-1] += pieces[0]
        for piece in pieces[1:]:
            segments.append(_RouteSegment(tuple(literals), tuple(params)))
            literals[:] = [piece]
            params.clear()

    last_end = 0
    for match in _PARAM_RE.finditer(path):
        add_text(path[last_end : match.start()])
        params.append((match.group(1), match.group(1) in dotless_params))
        literals.append("")
        last_end = match.end()
    add_text(path[last_end:])
    segments.append(_RouteSegment(tuple(literals), tuple(params)))
    return tuple(segments)


def _match_segments(segments: tuple[_RouteSegment, ...], pieces: list[str]) -> dict[str, str] | None:
    """Match a request path, already split at each ``/``, against a route split by :func:`_parse_route_path`."""
    # Parameters never hold a `/`, so the path must have exactly as many
    # segments as the route.
    if len(pieces) != len(segments):
        return None
    params: dict[str, str] = {}
    for segment, text in zip(segments, pieces, strict=True):
        if not _match_segment(segment, text, params):
            return None
    return params


def _match_segment(segment: _RouteSegment, text: str, params: dict[str, str]) -> bool:
    """
    Match one path segment and add its parameters to ``params``.

    Each parameter takes as many characters as it can while the rest of the
    segment still matches, the earlier parameter first. So this first works
    out, from the end of the segment backwards, where the rest can start,
    and then lets each parameter in turn take the longest run that leaves a
    match for the rest. Each step looks at each character of the segment
    once per parameter, so the time grows in step with the segment's length.
    Segments with one parameter, with no dotless parameter before the last,
    or shaped like Citry's cache routes take a quicker path first.
    """
    literals, names = segment.literals, segment.params
    if not names:
        return text == literals[0]
    head, tail = literals[0], literals[-1]
    # Each parameter takes at least one character.
    if len(text) < len(head) + len(tail) + len(names) or not text.startswith(head) or not text.endswith(tail):
        return False
    # The text before the first parameter and after the last is fixed, so
    # only the middle is split between the parameters.
    middle = text[len(head) : len(text) - len(tail)]
    size = len(middle)

    # Most segments hold one parameter, which takes the whole middle.
    if len(names) == 1:
        name, dotless = names[0]
        if dotless and "." in middle:
            return False
        params[name] = middle
        return True
    # Without a dotless parameter before the last, each split can be found
    # with a search from the right, which is much quicker than the general
    # walk below.
    if not any(dotless for _name, dotless in names[:-1]):
        return _split_from_the_right(literals, names, middle, params)
    # Citry's own cache routes: each parameter before the last is dotless
    # and followed by text that starts with `.`, so it ends at the next `.`.
    if all(dotless and literals[index + 1].startswith(".") for index, (_name, dotless) in enumerate(names[:-1])):
        return _split_at_dots(literals, names, middle, params)

    # next_dot[j] is the first `.` at or after j (or the end): where a
    # dotless parameter starting at j has to stop.
    next_dot = [size] * (size + 1)
    for index in range(size - 1, -1, -1):
        next_dot[index] = index if middle[index] == "." else next_dot[index + 1]

    def run_end(start: int, dotless: bool) -> int:
        return next_dot[start] if dotless else size

    # can_start[j]: the parameters from the current one on can match middle[j:].
    # The last parameter runs to the end of the middle.
    last_dotless = names[-1][1]
    can_start = [start < size and run_end(start, last_dotless) == size for start in range(size + 1)]
    # latest_ends[i][x]: the furthest place at or before x where parameter i
    # can end, so that the text after it and the later parameters match; -1
    # when there is none.
    latest_ends: list[list[int]] = [[] for _ in names[:-1]]
    for index in range(len(names) - 2, -1, -1):
        between = literals[index + 1]
        latest = [-1] * (size + 1)
        for end in range(1, size + 1):
            resume = end + len(between)
            fits = resume <= size and can_start[resume] and middle.startswith(between, end)
            latest[end] = end if fits else latest[end - 1]
        latest_ends[index] = latest
        dotless = names[index][1]
        can_start = [start < size and latest[run_end(start, dotless)] > start for start in range(size + 1)]
    if not can_start[0]:
        return False

    # Each parameter takes its longest run that leaves a match for the rest.
    start = 0
    for index, (name, dotless) in enumerate(names[:-1]):
        end = latest_ends[index][run_end(start, dotless)]
        params[name] = middle[start:end]
        start = end + len(literals[index + 1])
    params[names[-1][0]] = middle[start:]
    return True


def _split_from_the_right(
    literals: tuple[str, ...], names: tuple[tuple[str, bool], ...], middle: str, params: dict[str, str]
) -> bool:
    """
    Split the middle of a segment where no parameter before the last is dotless.

    Such a parameter accepts any run of one or more characters, so it can
    end wherever the fixed text after it fits. Putting each fixed text as
    far right as it can go, starting with the last, gives the split where
    each parameter takes as much as it can. Each search runs once over
    part of the middle.
    """
    size = len(middle)
    last_dotless = names[-1][1]
    # A dotless last parameter must start after the last `.`.
    last_floor = middle.rfind(".") + 1 if last_dotless else 0
    # The next parameter must start before `limit`, so it keeps at least one character.
    limit = size
    ends = [0] * (len(names) - 1)
    for index in range(len(names) - 2, -1, -1):
        between = literals[index + 1]
        # The fixed text must end at or before limit - 1. A negative bound
        # would count from the end, so rule it out first.
        if limit - 1 < len(between):
            return False
        end = middle.rfind(between, 0, limit - 1)
        if end < 0:
            return False
        if index == len(names) - 2 and end + len(between) < last_floor:
            return False
        ends[index] = end
        limit = end
    # The first parameter needs at least one character too.
    if ends[0] < 1:
        return False
    start = 0
    for index, (name, _dotless) in enumerate(names[:-1]):
        params[name] = middle[start : ends[index]]
        start = ends[index] + len(literals[index + 1])
    params[names[-1][0]] = middle[start:]
    return True


def _split_at_dots(
    literals: tuple[str, ...], names: tuple[tuple[str, bool], ...], middle: str, params: dict[str, str]
) -> bool:
    """
    Split the middle of a segment where each parameter but the last is dotless and followed by a ``.``.

    Such a parameter cannot hold a ``.`` and must be followed by one, so it
    ends exactly at the next ``.``; there is only one possible split.
    """
    start = 0
    for index, (name, _dotless) in enumerate(names[:-1]):
        end = middle.find(".", start)
        between = literals[index + 1]
        # The parameter needs at least one character, and the fixed text
        # after it must follow in full.
        if end <= start or not middle.startswith(between, end):
            return False
        params[name] = middle[start:end]
        start = end + len(between)
    rest = middle[start:]
    last_name, last_dotless = names[-1]
    if not rest or (last_dotless and "." in rest):
        return False
    params[last_name] = rest
    return True


def match_route_pattern(route_path: str, dotless_params: frozenset[str], request_path: str) -> dict[str, str] | None:
    """
    Match a request path against one full route path and return its parameters, or ``None``.

    The whole request path must match. Each ``{name}`` takes one or more
    characters other than ``/`` (and other than ``.`` when it is in
    ``dotless_params``), and the fixed text must appear as written. Where a
    segment could split between its parameters in more than one way, each
    parameter takes as much as it can, the earlier one first. The time
    grows in step with the request path's length.

    Raises:
        ValueError: If the route path uses one parameter name twice or puts
            two parameters next to each other (see :func:`check_route_table`).

    """
    return _match_segments(_parse_route_path(route_path, dotless_params), request_path.split("/"))


def match_path_below_mount(routes: Sequence[URLRoute], path: str) -> MatchedRoute | None:
    """
    Resolve the part of a request path below the mount prefix against a route tree.

    The host adapters call this with what follows the prefix: empty, or a
    path that starts with ``/`` (``/ext/events/call``), as the WSGI and
    ASGI specs describe. Only that one ``/`` is removed before
    :func:`match_route` runs, so ``/citry//ext/events/call`` matches no
    route. A remainder that does not start with ``/`` matches nothing
    either: a server passes the request line ``POST ext/events/call``
    through unchanged, and an ASGI server with a ``root_path`` of
    ``/citry`` can hand over ``/citryext/events/call``. In each case a
    host rule that checks the path, such as
    ``path.startswith("/citry/ext/events")``, sees a different path from
    the one Citry would route, so Citry answers 404.
    """
    if path and not path.startswith("/"):
        return None
    return match_route(routes, path.removeprefix("/"))


def route_allows_method(route: URLRoute, method: str) -> bool:
    """
    Return whether ``route`` accepts a request with ``method``.

    A method the route lists is accepted. ``HEAD`` is also accepted when the
    route lists ``GET``, since HEAD asks for the same response without its
    body (RFC 9110 section 9.3.2). So a POST-only route answers 405 to HEAD:
    a host rule that checks only POST requests, and Django's CSRF check,
    which skips HEAD, both see every request that reaches a POST handler.
    """
    return method in route.methods or (method == "HEAD" and "GET" in route.methods)


def match_route(routes: Sequence[URLRoute], path: str) -> MatchedRoute | None:
    """
    Resolve a request path (no leading slash) against a route tree.

    Routes are tried in definition order; the first match wins, so define
    more specific patterns first (e.g. the three-parameter
    ``cache/{class_id}.{vars_hash}.{script_type}`` before the two-parameter
    ``cache/{class_id}.{script_type}``). The whole path must match, as
    :func:`match_route_pattern` describes. The ASGI and WSGI adapters call
    :func:`match_path_below_mount`, which prepares the request path first.
    """
    # Split once and reuse the pieces for every route.
    pieces = path.split("/")
    for full_path, route in flatten_routes(routes):
        params = _match_segments(_parse_route_path(full_path, route.dotless_params), pieces)
        if params is not None:
            return MatchedRoute(route=route, full_path=full_path, params=params)
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
    # asyncio.to_thread preserves the caller's ContextVars in the worker. The
    # events dispatcher relies on that for per-call construction tracking,
    # and extension or request context should behave the same way.
    result = await asyncio.to_thread(fn, *args, **kwargs)
    # This branch only runs plain callables, so the result is already the final
    # value; the cast spells out what the union-typed signature cannot.
    return cast("_R", result)
