"""
The HTTP routes and URL builders of the ``events`` extension.

Four endpoints, mounted under the citry prefix (built-in extensions own
their paths directly; see ``ExtensionManager.urls``), fixed by design
``docs/design/events.md`` 3.8::

    POST      <prefix>/ext/events/call                  batch endpoint (envelope with calls[])
    GET       <prefix>/ext/events/runtime.js            standard events client runtime
    declared  <prefix>/ext/events/e/{class_id}/{event}  per-event handler methods

The route handlers are the HTTP transport of the dispatcher: they pick a
payload codec (``codecs.py``), build the transport context and the CSRF
check (``csrf.py``), dispatch, and translate the result envelope back into
HTTP. The batch endpoint always answers 200 with per-call statuses inside
the envelope; the per-event route mirrors its single call's status onto the
HTTP response so host middleware and access logs read correctly.

The per-event route also speaks the compatibility / no-JS mode (design
6.2): when a browser posts a plain form (no ``X-Citry-Events`` header) or
asks for ``text/html``, the response is not an envelope: a render action's
HTML is the body, a redirect becomes HTTP 303, a data action answers as
plain JSON, and errors carry their HTTP status as plain text.

This module also owns event URL building:
[`get_event_url`][citry.ext.events.routes.get_event_url] builds a handler's
URL anywhere, and [`Events.url`][citry.Events.url] calls it during a render.

The primary handlers are plain ``def``: the same route table must mount
under sync Django and WSGI (which reject ``async def`` route handlers at
startup), so the sync surface is the default under every adapter. The two
dispatch routes additionally carry an ``async def`` twin on
``URLRoute.handler_async``, which the ASGI adapter prefers: under ASGI a
call runs through ``EventsDispatcher.dispatch_async``, so ``async def``
event handlers are awaited natively on the event loop and plain handlers
are offloaded to a worker thread (design 6.2). Under the sync hosts the
sync dispatcher answers an ``async def`` event handler with the pointed
error naming ``EventsDispatcher.dispatch_async`` and the deployment fix.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import quote, urlsplit

from citry._owned_resource import PUBLIC_ASSET_CORS_HEADERS, _OwnedResource
from citry._protocol.events import (
    ProtocolValueError,
    add_route_identity,
    build_edge_error_envelope,
    build_rejected_call_envelope,
    validate_result_envelope,
)
from citry.ext.events.codecs import decode_request
from citry.ext.events.csrf import build_csrf_check
from citry.ext.events.dispatcher import EventRequest, EventsDispatcher, TransportContext
from citry.ext.events.errors import EventError, wire_error
from citry.ext.events.handlers import EVENT_ROUTE_METHODS
from citry.util.logger import logger
from citry.util.misc import format_url
from citry.util.routing import RouteResponse, URLRoute

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from urllib.parse import SplitResult

    from citry.citry import Citry
    from citry.component import Component
    from citry.ext.events.extension import EventHandler, EventsExtension
    from citry.util.routing import RouteRequest

__all__ = [
    "CALL_PATH",
    "DEFINITION_PATH",
    "EVENTS_RUNTIME_SRC",
    "EVENT_PATH",
    "EVENT_ROUTE_METHODS",
    "MAX_BODY_BYTES",
    "MAX_FORM_FIELDS",
    "RUNTIME_PATH",
    "STYLE_ASSET_PATH",
    "events_routes",
    "get_event_url",
]

# The route paths, fixed by design 3.8. RUNTIME_PATH matches what the
# serialize-time emission points the runtime script tag at
# (citry/ext/events/emission.py; the path is design-pinned on both sides).
CALL_PATH = "ext/events/call"
DEFINITION_PATH = "ext/events/definitions/{digest}.js"
STYLE_ASSET_PATH = "ext/events/assets/{digest}.css"
RUNTIME_PATH = "ext/events/runtime.js"
EVENT_PATH = "ext/events/e/{class_id}/{event}"
# EVENT_PATH admits EVENT_ROUTE_METHODS, the same fixed set a handler may
# declare with ``@event(methods=...)``; ``handlers.py`` explains why the set
# is fixed and defines it there so the decorator can check against it.

# The committed browser bundle built from packages/js/citry-client.
EVENTS_RUNTIME_SRC = Path(__file__).parents[2] / "_vue" / "runtime.js"

# The default cap on one request body (design 7.4 abuse limits). The host
# adapter stops reading one byte past it (one message past it under ASGI), and an oversized body answers
# payload_too_large without being parsed. Deployments size it per engine
# through ``extensions_defaults["events"]["_max_body_bytes"]`` (design 3.5).
# The protocol's calls-length cap is the dispatcher's; this one guards bytes.
MAX_BODY_BYTES = 1024 * 1024

# The default cap on the fields of one urlencoded form post, the same as
# Django's DATA_UPLOAD_MAX_NUMBER_FIELDS. A small body can still hold many
# short fields, each of which costs a dict entry and a validation step.
# Deployments size it through ``extensions_defaults["events"]["_max_form_fields"]``.
MAX_FORM_FIELDS = 1000

_JSON_CONTENT_TYPE = "application/json"
_NO_STORE = ("Cache-Control", "no-store")


################################################
# URL BUILDING
################################################


def get_event_url(
    comp_cls: type[Component],
    name: str,
    *,
    query: dict[str, Any] | None = None,
    fragment: str | None = None,
) -> str:
    """
    The URL one event handler is dispatchable at (the per-event route).

    Checks the event exists on the component, so a typo fails at build time
    instead of 404-ing at call time. Requires a mounted web integration
    (the URL must point somewhere); ``Citry.build_url`` raises the standard
    pointed error otherwise.

    Args:
        comp_cls: The component class declaring the handler.
        name: The handler's wire name.
        query: Optional query parameters to append.
        fragment: Optional ``#fragment`` to append.

    Returns:
        The absolute URL path, e.g. ``"/citry/ext/events/e/Doc_a1b2c3/save"``.

    Raises:
        ValueError: When the component declares no event of that name.
        RuntimeError: When no web integration is mounted.

    Example:
        ```python
        from citry.ext.events import get_event_url

        get_event_url(TodoList, "search", query={"q": "milk"})
        ```

    """
    extension = cast("EventsExtension", comp_cls.citry.extensions.get_extension("events"))
    info = extension.resolve(comp_cls)
    if name not in info.handlers:
        known = ", ".join(info.handlers) or "(none)"
        msg = f"Component {comp_cls.__name__} has no event {name!r}; declared events: {known}."
        raise ValueError(msg)
    url = comp_cls.citry.build_url(f"ext/events/e/{comp_cls.class_id}/{name}")
    return format_url(url, query=query, fragment=fragment)


################################################
# THE ROUTE TABLE
################################################


def events_routes(citry: Citry) -> list[URLRoute]:
    """The extension's route table, with handlers bound to one ``Citry`` instance."""
    from citry.ext.events.renderers import dispatcher_for  # noqa: PLC0415

    dispatcher = dispatcher_for(citry)

    def serve_runtime(_request: RouteRequest) -> RouteResponse:
        return _runtime_resource(citry).response()

    def serve_definition(_request: RouteRequest, *, digest: str) -> RouteResponse:
        from citry._vue.events import definition_bundle  # noqa: PLC0415

        if len(digest) != 64 or any(value not in "0123456789abcdef" for value in digest):
            return RouteResponse("", status=404, content_type="text/plain")
        content = definition_bundle(citry, digest)
        if content is None:
            return RouteResponse("", status=404, content_type="text/plain")
        return RouteResponse(
            content.decode(),
            content_type="text/javascript",
            # Content-addressed and public; the CORS header lets the browser
            # check the integrity the runtime puts on this request.
            headers=(*PUBLIC_ASSET_CORS_HEADERS, ("Cache-Control", "public, max-age=31536000, immutable")),
        )

    def serve_style_asset(_request: RouteRequest, *, digest: str) -> RouteResponse:
        from citry._vue.events import style_asset  # noqa: PLC0415

        if len(digest) != 64 or any(value not in "0123456789abcdef" for value in digest):
            return RouteResponse("", status=404, content_type="text/plain")
        content = style_asset(citry, digest)
        if content is None:
            return RouteResponse("", status=404, content_type="text/plain")
        return RouteResponse(
            content.decode(),
            content_type="text/css",
            # Content-addressed and public; the CORS header lets the browser
            # check the integrity the runtime puts on this request.
            headers=(*PUBLIC_ASSET_CORS_HEADERS, ("Cache-Control", "public, max-age=31536000, immutable")),
        )

    # The host adapters read at most one byte past the engine's body cap, so
    # an oversized body is never held in memory whole. The cap is looked up
    # per request, as _prepare_dispatch does.
    def body_cap() -> int:
        return _body_cap(citry)

    # Each dispatch route is a sync/async pair: the plain handler is what the
    # sync hosts (WSGI, sync Django) mount and run, and the async twin rides
    # URLRoute.handler_async so the ASGI adapter dispatches through
    # EventsDispatcher.dispatch_async (design 6.2).
    def serve_batch(request: RouteRequest) -> RouteResponse:
        return _serve_call(request, citry, dispatcher, url_component=None, url_event=None)

    async def serve_batch_async(request: RouteRequest) -> RouteResponse:
        return await _serve_call_async(request, citry, dispatcher, url_component=None, url_event=None)

    def serve_event(request: RouteRequest, *, class_id: str, event: str) -> RouteResponse:
        return _serve_call(request, citry, dispatcher, url_component=class_id, url_event=event)

    async def serve_event_async(request: RouteRequest, *, class_id: str, event: str) -> RouteResponse:
        return await _serve_call_async(request, citry, dispatcher, url_component=class_id, url_event=event)

    return [
        URLRoute(
            CALL_PATH,
            handler=serve_batch,
            handler_async=serve_batch_async,
            name="citry_events_call",
            methods=("POST",),
            max_body_bytes=body_cap,
        ),
        URLRoute(RUNTIME_PATH, handler=serve_runtime, name="citry_events_runtime", methods=("GET",)),
        URLRoute(
            DEFINITION_PATH,
            handler=serve_definition,
            name="citry_vue_definition",
            methods=("GET",),
        ),
        URLRoute(
            STYLE_ASSET_PATH,
            handler=serve_style_asset,
            name="citry_vue_style_asset",
            methods=("GET",),
        ),
        URLRoute(
            EVENT_PATH,
            handler=serve_event,
            handler_async=serve_event_async,
            name="citry_events_dispatch",
            methods=EVENT_ROUTE_METHODS,
            max_body_bytes=body_cap,
        ),
    ]


def _runtime_resource(citry: Citry) -> _OwnedResource:
    """Serve the same committed Vue runtime used by document serialization."""
    return _OwnedResource(
        url=citry.build_url(RUNTIME_PATH),
        content=EVENTS_RUNTIME_SRC.read_text(encoding="utf8"),
        content_type="text/javascript",
        headers=(("Cache-Control", "no-store"),),
    )


@dataclass(frozen=True, slots=True)
class _PreparedDispatch:
    """One decoded events request, ready for the dispatcher: what the route computes before the sync/async split."""

    envelope: Mapping[str, Any]
    request: EventRequest
    ctx: TransportContext
    csrf_check: Callable[[EventHandler], None]
    batch: bool
    compat: bool


def _serve_call(
    request: RouteRequest,
    citry: Citry,
    dispatcher: EventsDispatcher,
    *,
    url_component: str | None,
    url_event: str | None,
) -> RouteResponse:
    """One events HTTP request through the sync dispatcher: decode, dispatch, translate back to HTTP."""
    prepared = _prepare_dispatch(request, citry, url_component=url_component, url_event=url_event)
    if isinstance(prepared, RouteResponse):
        return prepared
    outcome = dispatcher.dispatch(
        prepared.envelope,
        prepared.ctx,
        request=prepared.request,
        url_component=url_component,
        url_event=url_event,
        csrf_check=prepared.csrf_check,
    )
    return _respond(request, outcome, batch=prepared.batch, compat=prepared.compat)


async def _serve_call_async(
    request: RouteRequest,
    citry: Citry,
    dispatcher: EventsDispatcher,
    *,
    url_component: str | None,
    url_event: str | None,
) -> RouteResponse:
    """
    The async twin of ``_serve_call``, dispatched under ASGI.

    Only the dispatcher entry point differs: ``dispatch_async`` awaits
    ``async def`` event handlers natively on the event loop and offloads
    plain ones to a worker thread (design 6.2).
    """
    prepared = _prepare_dispatch(request, citry, url_component=url_component, url_event=url_event)
    if isinstance(prepared, RouteResponse):
        return prepared
    outcome = await dispatcher.dispatch_async(
        prepared.envelope,
        prepared.ctx,
        request=prepared.request,
        url_component=url_component,
        url_event=url_event,
        csrf_check=prepared.csrf_check,
    )
    return _respond(request, outcome, batch=prepared.batch, compat=prepared.compat)


def _prepare_dispatch(
    request: RouteRequest,
    citry: Citry,
    *,
    url_component: str | None,
    url_event: str | None,
) -> _PreparedDispatch | RouteResponse:
    """
    Everything before the dispatcher runs: caps, codecs, the transport context.

    A returned ``RouteResponse`` is an early rejection to send as-is.
    """
    batch = url_event is None
    compat = not batch and _wants_compat(request)

    cap = _body_cap(citry)
    if len(request.body) > cap:
        # The adapter stopped reading one byte past the cap, so the real size
        # is unknown, only that it is over the cap.
        message = (
            f"The request body is larger than {cap} bytes, the most this endpoint accepts."
            ' Raise extensions_defaults["events"]["_max_body_bytes"] to accept larger requests.'
        )
        return _edge_response(413, "payload_too_large", message, batch=batch, compat=compat)
    field_cap = _form_field_cap(citry)
    if _is_form_post(request) and _form_field_count(request.body) > field_cap:
        message = (
            f"The form post has more than {field_cap} fields, the most this endpoint accepts."
            ' Raise extensions_defaults["events"]["_max_form_fields"] to accept more.'
        )
        return _edge_response(413, "payload_too_large", message, batch=batch, compat=compat)

    # Best-effort handler resolution, for the pieces that need it before
    # dispatch: the per-event method allowlist and the GET codec's token
    # rule. Resolution failures stay None here; the dispatcher answers them
    # with the proper wire errors.
    handler = _resolve_handler(citry, url_component, url_event) if not batch else None
    if handler is not None and request.method not in handler.methods:
        # Method configs govern the per-event route only (design 3.8); the
        # allowlist violation is plain HTTP, not a wire error.
        return RouteResponse(
            content=f"Method not allowed; {url_event!r} accepts: {', '.join(handler.methods)}.",
            status=405,
            headers=(("Allow", ", ".join(handler.methods)),),
        )

    try:
        decoded = decode_request(
            request,
            citry.settings.event_payload_codecs,
            state_declared=handler is not None and "state" in handler.params,
            batch=batch,
        )
    except EventError as err:
        return _edge_response(err.status, _edge_code(err), err.message, batch=batch, compat=compat)

    if decoded.needs_route_identity:
        # Flat JSON, form, and query requests name their target in the URL,
        # not in their external payload. Convert them into the same complete,
        # strict call object the dispatcher accepts from every transport.
        if url_component is None or url_event is None:  # pragma: no cover - these codecs are per-event only
            message = "A synthesized event payload requires the per-event route's component and handler."
            return _parsed_edge_response(decoded.envelope, 400, "protocol_mismatch", message, compat=compat)
        decoded = decoded._replace(envelope=add_route_identity(decoded.envelope, url_component, url_event))

    calls = decoded.envelope.get("calls")
    if not batch and isinstance(calls, list) and len(calls) != 1:
        message = (
            f"The per-event route takes a single call; this envelope carries {len(calls)}."
            f" Use {CALL_PATH} for batches."
        )
        return _parsed_edge_response(decoded.envelope, 400, "protocol_mismatch", message, compat=compat)

    event_request = EventRequest(
        method=request.method,
        path=request.path,
        query=request.query,
        headers=request.headers,
        body=request.body,
        content_type=request.content_type,
        form=decoded.form,
        files={},
        native=request.native,
    )
    ctx = TransportContext(
        transport="http",
        citry=citry,
        host_request=request.native,
        headers=request.headers,
        response_mode="compat" if compat else "wire",
    )
    return _PreparedDispatch(
        envelope=decoded.envelope,
        request=event_request,
        ctx=ctx,
        csrf_check=build_csrf_check(request),
        batch=batch,
        compat=compat,
    )


def _respond(
    request: RouteRequest,
    outcome: dict[str, Any] | RouteResponse,
    *,
    batch: bool,
    compat: bool,
) -> RouteResponse:
    """Translate the dispatcher's outcome (a result envelope or the escape hatch) into the HTTP response."""
    if isinstance(outcome, RouteResponse):
        # The RouteResponse escape hatch (per-event route only).
        return _with_no_store(outcome) if request.method == "GET" else outcome

    if compat:
        response = _compat_response(outcome, request)
    else:
        content, sent = _encode_envelope(outcome)
        status = 200 if batch else _mirror_status(sent)
        response = RouteResponse(
            content=content,
            content_type=_JSON_CONTENT_TYPE,
            status=status,
        )
    # GET handlers are cacheable in principle but served no-store until GET
    # caching lands (design 3.5 and section 16).
    return _with_no_store(response) if request.method == "GET" else response


def _encode_envelope(envelope: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]]:
    """
    Encode a result envelope as strict JSON: the body text, plus the envelope it carries.

    The protocol package checks the final wire value before serialization.
    ``allow_nan=False`` keeps this HTTP encoder aligned with that boundary.
    """
    issue = validate_result_envelope(envelope)
    if issue is not None:
        raise ProtocolValueError(issue)
    return json.dumps(envelope, separators=(",", ":"), allow_nan=False), envelope


def _body_cap(citry: Citry) -> int:
    """
    The engine's request body cap in bytes: the configured value, else the default.

    The cap guards the transport before any component resolves (a batch can
    span components), so it is engine-wide: the recognized
    ``extensions_defaults["events"]["_max_body_bytes"]`` setting, whose
    value the events extension validates at engine construction.
    """
    value = citry.settings.extensions_defaults.get("events", {}).get("_max_body_bytes")
    return MAX_BODY_BYTES if value is None else value


def _form_field_cap(citry: Citry) -> int:
    """The engine's cap on the fields of one form post: the configured value, else the default."""
    value = citry.settings.extensions_defaults.get("events", {}).get("_max_form_fields")
    return MAX_FORM_FIELDS if value is None else value


def _is_form_post(request: RouteRequest) -> bool:
    """Whether the request carries a urlencoded form body, the one body Citry splits into fields."""
    return request.content_type.split(";")[0].strip().lower() == "application/x-www-form-urlencoded"


def _form_field_count(body: bytes) -> int:
    """
    Count the fields of a urlencoded body without parsing it.

    This is the count ``parse_qs`` checks against ``max_num_fields``: one
    more than the number of ``&`` separators. Empty pieces count too, so it
    can be higher than the number of fields parsing returns, never lower.
    """
    return body.count(b"&") + 1 if body else 0


def _resolve_handler(citry: Citry, class_id: str | None, event: str | None) -> EventHandler | None:
    """The per-event route's handler record, or ``None`` when it does not resolve."""
    if class_id is None or event is None:
        return None
    try:
        comp_cls = citry.get_component_by_class_id(class_id)
    except KeyError:
        return None
    extension = cast("EventsExtension", citry.extensions.get_extension("events"))
    return extension.resolve(comp_cls).handlers.get(event)


def _edge_code(err: EventError) -> str:
    """
    The wire code of a transport-edge rejection.

    The result schema's code set is closed; a 400 at the edge (a body no
    codec reads, an unclaimed content type) answers ``protocol_mismatch``,
    and other statuses keep the error's own mapping.
    """
    return "protocol_mismatch" if err.status == 400 else wire_error(err)["code"]


def _edge_response(status: int, code: str, message: str, *, batch: bool, compat: bool) -> RouteResponse:
    """
    A rejection raised before dispatch could run (size cap, codec failure).

    Envelope consumers still get a result envelope. There is no parsed
    ``calls`` array or request ID at this boundary, so the result is the one
    uncorrelated transport-edge error permitted with a null ``requestId``.
    The compatibility mode gets the plain-text status it gets for any error.
    """
    if compat:
        return RouteResponse(content=message, content_type="text/plain", status=status)
    envelope = build_edge_error_envelope(status, code, message)
    return RouteResponse(
        # allow_nan=False for uniformity with the other envelope encoders;
        # this envelope is built from strings and ints, so it cannot trip.
        content=json.dumps(envelope, separators=(",", ":"), allow_nan=False),
        content_type=_JSON_CONTENT_TYPE,
        status=200 if batch else status,
    )


def _parsed_edge_response(
    envelope: Mapping[str, Any],
    status: int,
    code: str,
    message: str,
    *,
    compat: bool,
) -> RouteResponse:
    """Reject a decoded envelope, correlating slots only when its request ID permits it."""
    if compat:
        return RouteResponse(content=message, content_type="text/plain", status=status)

    rejected = build_rejected_call_envelope(envelope, status=status, code=code, message=message)
    return RouteResponse(
        content=json.dumps(rejected, separators=(",", ":"), allow_nan=False),
        content_type=_JSON_CONTENT_TYPE,
        status=status,
    )


def _mirror_status(envelope: Mapping[str, Any]) -> int:
    """The per-event route's HTTP status: the single call's status (200 when ok)."""
    results = envelope.get("results") or []
    first = results[0] if results else {}
    if first.get("ok"):
        return 200
    error = first.get("error") or {}
    status = error.get("status")
    return status if isinstance(status, int) else 200


def _wants_compat(request: RouteRequest) -> bool:
    """
    Whether the per-event response should be HTML-shaped instead of an envelope.

    The compatibility / no-JS mode (design 6.2): a request that asks for
    ``text/html``, or a classic form post without the ``X-Citry-Events``
    header, is not the runtime and cannot apply an envelope.
    """
    accept = request.headers.get("accept") or ""
    if "text/html" in accept.lower():
        return True
    base_type = request.content_type.split(";")[0].strip().lower()
    return base_type == "application/x-www-form-urlencoded" and "x-citry-events" not in request.headers


def _compat_response(envelope: Mapping[str, Any], request: RouteRequest) -> RouteResponse:
    """
    Translate the single call's result into a browser-native response.

    Errors carry their HTTP status as plain text; a redirect action becomes
    a 303 (the post/redirect/get answer for form posts) whose relative URL
    is first resolved against the posting page; a render action's
    HTML is the body; a data action answers as plain JSON (a pasted GET URL
    shows the value); an acknowledged call with nothing to apply is a 204,
    which leaves a form-posting browser on its page. Browser event and URL
    actions also fall through to 204 because a plain form response has no
    client runtime to apply them.
    """
    results = envelope.get("results") or [{}]
    first = results[0]
    if not first.get("ok"):
        error = first.get("error") or {}
        message = error.get("message", "The call failed.")
        fields = error.get("fieldErrors") or {}
        lines = [message, *(f"{name}: {text}" for name, text in fields.items())]
        status = error.get("status")
        return RouteResponse(
            content="\n".join(lines),
            content_type="text/plain",
            status=status if isinstance(status, int) else 500,
        )
    actions = first.get("actions") or []
    redirect = next((action for action in actions if action.get("action") == "redirect"), None)
    if redirect is not None:
        # Resolve first, then encode: the resolver works on the URL as the
        # handler wrote it, and the header must carry only ASCII.
        location = _encode_location(_resolve_redirect_url(redirect["url"], request))
        return RouteResponse(status=303, headers=(("Location", location),))
    render = next((action for action in actions if action.get("action") == "render"), None)
    if render is not None:
        return RouteResponse(content=render["html"], content_type="text/html")
    data = next((action for action in actions if action.get("action") == "data"), None)
    if data is not None:
        content = json.dumps(data["value"], separators=(",", ":"), allow_nan=False)
        return RouteResponse(content=content, content_type=_JSON_CONTENT_TYPE)
    return RouteResponse(status=204)


# Characters browsers strip from both ends of a URL before they parse it (C0
# controls and space), so " //host" means the same as "//host" to them.
_URL_LEADING_STRIP = "".join(chr(code) for code in range(0x21))


# A URL scheme as browsers read it: a letter, then letters, digits, "+",
# "-", or ".", then ":". A regex rather than urlsplit, which raises on
# some non-ASCII hosts and would turn the redirect into a 500.
_URL_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")


# The (handler path, URL) pairs already warned about, for the life of the
# process. The cap keeps a client that varies the path from growing it
# without limit; once it is full, a pair not yet recorded warns on every
# request, which costs log volume and nothing else.
_WARNED_REDIRECTS: set[tuple[str, str]] = set()
_MAX_WARNED_REDIRECTS = 1024


def _resolve_redirect_url(url: str, request: RouteRequest) -> str:
    r"""
    Resolve a redirect's URL the way the JavaScript runtime would.

    The runtime calls ``location.assign(url)``, so the browser resolves a
    relative URL such as ``"?page=2"`` or ``"next"`` against the page the
    visitor is on. A 303 ``Location`` is resolved against the URL that was
    requested instead, which here is the handler's own URL, so the server
    resolves the URL against the posting page first. The page comes from
    the ``Referer`` header, the only place a plain form post names it.

    A URL that does not depend on the page (it has a scheme, or starts with
    ``/`` or ``\``, which browsers read like ``/``) passes through as is.
    When the request has no Referer, or one from another host, the URL also
    passes through unchanged and the browser resolves it against the handler
    URL. That is right when someone opens a ``GET`` handler URL directly, so
    only other methods log a warning that names the fix. Two cases resolve
    differently from ``location.assign()`` and cannot be detected here, so
    the docs ask those pages to use a path that starts with ``/``:

    - a ``Referrer-Policy`` that sends only the origin gives a Referer of
      ``https://host/``, which looks like a page at the site root;
    - a ``<base href>`` changes what the browser resolves against, but the
      Referer still names the page's own URL.
    """
    stripped = url.lstrip(_URL_LEADING_STRIP).translate({9: None, 10: None, 13: None})
    if _URL_SCHEME.match(stripped) or stripped.startswith(("/", "\\")):
        return url

    referer = request.headers.get("referer") or ""
    try:
        base = urlsplit(referer)
    except ValueError:
        # urlsplit rejects some hosts, such as "[::1" or ones with full-width
        # delimiters; the client sent it, so treat it as no Referer.
        base = urlsplit("")
    host = (request.headers.get("host") or "").lower()
    # Compare the Referer's host with the request's own Host, as the always-on
    # CSRF check (enforce_floor) does for Origin: a page from another site is
    # not the page this redirect is relative to.
    if base.scheme in ("http", "https") and base.netloc and base.netloc.lower() == host:
        # Answer with the absolute URL: the base is the visitor's own page on
        # this host, and an absolute Location keeps a page path such as
        # "//other/x" from turning the result into a link to another host.
        return _join_like_a_browser(base, stripped)

    # A GET handler URL opened directly is the page itself, so resolving
    # against it is correct. One warning per handler and URL is enough to
    # find the problem without a line for every visitor.
    warning_key = (request.path, url)
    if request.method != "GET" and warning_key not in _WARNED_REDIRECTS:
        if len(_WARNED_REDIRECTS) < _MAX_WARNED_REDIRECTS:
            _WARNED_REDIRECTS.add(warning_key)
        logger.warning(
            f"actions.Redirect({url!r}) is a relative URL, but the request to {request.path!r} has no"
            " Referer header naming a page on this site, so the browser will resolve it against the"
            " handler URL and likely show a 404. Redirect to a path that starts with '/', or check"
            " the page's Referrer-Policy."
        )
    return url


# Path segments the URL standard reads as "this folder" and "the folder above",
# including their percent-encoded spellings.
_SINGLE_DOT_SEGMENTS = frozenset({".", "%2e"})
_DOUBLE_DOT_SEGMENTS = frozenset({"..", ".%2e", "%2e.", "%2e%2e"})


def _join_like_a_browser(base: SplitResult, reference: str) -> str:
    """
    Resolve a relative ``reference`` against ``base`` as the URL standard does.

    ``urllib.parse.urljoin`` follows RFC 3986 and drops empty path segments,
    so it turns a page at ``//a/b`` into ``/a/b``; a browser keeps them. This
    follows the WHATWG URL rules for ``http`` and ``https`` instead, so the
    303 lands where ``location.assign()`` would. It keeps the characters as
    written; ``_encode_location`` percent-encodes the result afterwards.
    """
    # Browsers drop tabs and newlines anywhere in a URL before parsing it.
    reference = reference.translate({9: None, 10: None, 13: None}).rstrip(_URL_LEADING_STRIP)
    reference, hash_mark, fragment = reference.partition("#")
    path, question_mark, query = reference.partition("?")
    origin = f"{base.scheme}://{base.netloc}"
    tail = f"{hash_mark}{fragment}"
    if not path:
        # "?q" replaces only the query; "#f" keeps the page's query too.
        if question_mark:
            return f"{origin}{base.path}?{query}{tail}"
        page_query = f"?{base.query}" if base.query else ""
        return f"{origin}{base.path}{page_query}{tail}"

    # For http and https a backslash is a path separator, and the reference
    # replaces the last segment of the page's path.
    segments = base.path.split("/")[1:-1] if base.path else []
    reference_segments = path.replace("\\", "/").split("/")
    for index, segment in enumerate(reference_segments):
        is_last = index == len(reference_segments) - 1
        lowered = segment.lower()
        if lowered in _DOUBLE_DOT_SEGMENTS:
            if segments:
                segments.pop()
            if is_last:
                segments.append("")
        elif lowered in _SINGLE_DOT_SEGMENTS:
            if is_last:
                segments.append("")
        else:
            segments.append(segment)
    resolved_query = f"{question_mark}{query}"
    return f"{origin}/{'/'.join(segments)}{resolved_query}{tail}"


# Every printable ASCII character except space. These pass into the header
# as written: a browser reads reserved characters and "%XX" escapes in a
# Location exactly as it reads them in location.assign().
_LOCATION_SAFE = "".join(chr(code) for code in range(0x21, 0x7F))

# A lone surrogate cannot be encoded as UTF-8. Browsers turn one into U+FFFD
# when a string becomes a URL, so the server does the same.
_LONE_SURROGATE = re.compile("[\ud800-\udfff]")


def _encode_location(url: str) -> str:
    """
    Turn a redirect URL into the ASCII form a ``Location`` header needs.

    HTTP headers carry bytes, and Citry's ASGI and WSGI adapters send
    header text as Latin-1, so a URL such as ``"/caf\u00e9"`` must go out
    as ``"/caf%C3%A9"``, the form a browser gives it when
    ``location.assign()`` navigates to it. Every character outside
    printable ASCII becomes UTF-8 ``%XX`` escapes, the host included;
    printable ASCII, including reserved characters and existing escapes,
    stays as is.

    The host stays percent-encoded rather than converted to its ASCII
    ``xn--`` form (IDNA). A browser decodes the escapes in an ``http`` or
    ``https`` host and converts it with its own rules, so it lands where
    ``location.assign()`` would. Python's ``idna`` codec follows older
    rules that send some hosts elsewhere.
    """
    # Most URLs are already printable ASCII, and browsers read those as written.
    if all("!" <= char <= "~" for char in url):
        return url
    # Do what browsers do before they parse: drop control characters and
    # spaces at both ends, tabs and newlines anywhere, and replace lone surrogates.
    url = url.strip(_URL_LEADING_STRIP).translate({9: None, 10: None, 13: None})
    url = _LONE_SURROGATE.sub("\ufffd", url)
    return quote(url, safe=_LOCATION_SAFE)


def _with_no_store(response: RouteResponse) -> RouteResponse:
    """Add ``Cache-Control: no-store`` unless the handler already set a cache policy."""
    if any(name.lower() == "cache-control" for name, _ in response.headers):
        return response
    return RouteResponse(
        content=response.content,
        content_type=response.content_type,
        status=response.status,
        headers=(*response.headers, _NO_STORE),
    )
