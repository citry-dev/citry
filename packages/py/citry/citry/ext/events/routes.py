"""
The HTTP routes and URL builders of the ``events`` extension.

Three endpoints, mounted under the citry prefix (built-in extensions own
their paths directly; see ``ExtensionManager.urls``), fixed by design
``docs/design/events.md`` 3.8::

    POST      <prefix>/ext/events/call                  batch endpoint (envelope with calls[])
    GET       <prefix>/ext/events/runtime.js            the events client runtime
    GET|POST  <prefix>/ext/events/e/{class_id}/{event}  per-event dispatch

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
[`get_event_url`][citry.ext.events.routes.get_event_url] anywhere, and the
``component.events.url(...)`` method the extension attaches to the woven
config class (the component's ``Events`` class as the extension manager
rebuilt it on the config base).

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

import functools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

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
from citry.util.misc import format_url
from citry.util.routing import RouteResponse, URLRoute

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from citry.citry import Citry
    from citry.component import Component
    from citry.ext.events.config import Events
    from citry.ext.events.extension import EventHandler, EventsExtension
    from citry.util.routing import RouteRequest

__all__ = [
    "CALL_PATH",
    "EVENTS_RUNTIME_SRC",
    "EVENT_PATH",
    "MAX_ENVELOPE_BYTES",
    "RUNTIME_PATH",
    "events_config_url",
    "events_routes",
    "get_event_url",
]

# The route paths, fixed by design 3.8. RUNTIME_PATH matches what the
# serialize-time emission points the runtime script tag at
# (citry/ext/events/emission.py; the path is design-pinned on both sides).
CALL_PATH = "ext/events/call"
RUNTIME_PATH = "ext/events/runtime.js"
EVENT_PATH = "ext/events/e/{class_id}/{event}"

# The events client runtime file this route serves: the built bundle,
# generated from packages/js/citry-client/src/citry-events.ts (pnpm run
# build there regenerates it).
EVENTS_RUNTIME_SRC = Path(__file__).parent / "client" / "citry-events.js"

# The default transport-layer byte cap on one envelope (design 7.4 abuse
# limits; oversized bodies answer payload_too_large without being parsed).
# Deployments size it per engine through
# ``extensions_defaults["events"]["_max_envelope_bytes"]`` (design 3.5). The
# protocol's calls-length cap is the dispatcher's; this one guards bytes.
MAX_ENVELOPE_BYTES = 1024 * 1024

_JSON_CONTENT_TYPE = "application/json"
_NO_STORE = ("Cache-Control", "no-store")


@functools.cache
def _runtime_js() -> str:
    """The events client runtime source, read once per process."""
    return EVENTS_RUNTIME_SRC.read_text(encoding="utf-8")


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


def events_config_url(
    self: Events,
    name: str,
    *,
    query: dict[str, Any] | None = None,
    fragment: str | None = None,
) -> str:
    """
    Build the URL of one of this component's events (``component.events.url``).

    Available during render as ``self.events.url("submit")`` on the
    component (typically from ``template_data``, to feed a form's action
    URL). Same behavior as
    [`get_event_url`][citry.ext.events.routes.get_event_url], with the
    component class taken from the config instance.

    Args:
        self: The per-component Events config instance (``component.events``).
        name: The handler's wire name.
        query: Optional query parameters to append.
        fragment: Optional ``#fragment`` to append.

    Returns:
        The absolute URL path of the per-event route.

    """
    comp_cls = getattr(self, "component_class", None)
    if comp_cls is None:
        msg = (
            "Events.url() needs the component class, which only the per-component Events config"
            " carries; call it as component.events.url(...) (or use get_event_url(MyComponent, ...))."
        )
        raise RuntimeError(msg)
    return get_event_url(comp_cls, name, query=query, fragment=fragment)


################################################
# THE ROUTE TABLE
################################################


def events_routes(citry: Citry) -> list[URLRoute]:
    """The extension's route table, with handlers bound to one ``Citry`` instance."""
    dispatcher = EventsDispatcher()

    def serve_runtime(_request: RouteRequest) -> RouteResponse:
        return RouteResponse(
            content=_runtime_js(),
            content_type="text/javascript",
            headers=(_NO_STORE,),
        )

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
        ),
        URLRoute(RUNTIME_PATH, handler=serve_runtime, name="citry_events_runtime", methods=("GET",)),
        URLRoute(
            EVENT_PATH,
            handler=serve_event,
            handler_async=serve_event_async,
            name="citry_events_dispatch",
            methods=("GET", "POST"),
        ),
    ]


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

    cap = _envelope_cap(citry)
    if len(request.body) > cap:
        message = f"The request body is {len(request.body)} bytes; the cap is {cap}."
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
        response = _compat_response(outcome)
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


def _envelope_cap(citry: Citry) -> int:
    """
    The engine's envelope byte cap: the configured value, else the default.

    The cap guards the transport before any component resolves (a batch can
    span components), so it is engine-wide: the recognized
    ``extensions_defaults["events"]["_max_envelope_bytes"]`` setting, whose
    value the events extension validates at engine construction.
    """
    value = citry.settings.extensions_defaults.get("events", {}).get("_max_envelope_bytes")
    return MAX_ENVELOPE_BYTES if value is None else value


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


def _compat_response(envelope: Mapping[str, Any]) -> RouteResponse:
    """
    Translate the single call's result into a browser-native response.

    Errors carry their HTTP status as plain text; a redirect action becomes
    a 303 (the post/redirect/get answer for form posts); a render action's
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
        return RouteResponse(status=303, headers=(("Location", redirect["url"]),))
    render = next((action for action in actions if action.get("action") == "render"), None)
    if render is not None:
        return RouteResponse(content=render["html"], content_type="text/html")
    data = next((action for action in actions if action.get("action") == "data"), None)
    if data is not None:
        content = json.dumps(data["value"], separators=(",", ":"), allow_nan=False)
        return RouteResponse(content=content, content_type=_JSON_CONTENT_TYPE)
    return RouteResponse(status=204)


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
