"""
The dispatcher of the ``events`` extension: from a call envelope to a result
envelope.

When the browser runtime (or curl, or a plain form) sends an event call, some
server code has to work out which component and handler the call names, check
permissions, run the handler, and package the results for the client to
apply. That code is this module's :class:`EventsDispatcher`. There is exactly
one dispatcher; every transport (the HTTP routes today, WebSocket later)
decodes its request into the one call-envelope shape (design
``docs/design/events.md`` 4.2) and hands it to
:meth:`EventsDispatcher.dispatch`, which returns the matching result envelope
(design 4.3). Transports never look inside either envelope; they carry bytes.

The per-call pipeline, in the normative order (design 6.1's responsibilities
table): structural envelope validation -> component and event resolution (the
per-event URL is authoritative) -> the transport's CSRF check -> state-token
verification and two-way binding updates -> args validation -> the
``on_event`` emit hook (veto) -> the ``_context`` hook -> guards -> the
handler with by-name injection -> return coercion and wire encoding -> the
``on_event_result`` emit hook -> the state re-sign -> the send_sequence echo.
Uncaught exceptions become a generic 500 through ``on_event_error``;
exception text rides only in debug mode (the ``"citry"`` logger at DEBUG),
never a traceback.

Wire error messages here are contract: the protocol package's examples
(``packages/protocol/events/v1/tests/``) lock the exact text, and the
result schema pins each error code to its status. Structural rejections that
have no code of their own answer ``protocol_mismatch`` (400), the closed
code set's slot for "this is not a well-formed citry-events/1 exchange".
"""

from __future__ import annotations

import inspect
import json
import logging
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, TypedDict

from citry._input_types import _restore_json_tuples
from citry._page_nonce import page_nonce_from_headers
from citry._protocol.events import (
    ARGS_SOURCE_FORM,
    CAPABILITIES_BASELINE_V1,
    PROTOCOL,
    RENDERERS,
    CallEnvelopeFailure,
    ProtocolValueError,
    assemble_owned_ok_result,
    assemble_validated_ok_result,
    build_error,
    build_error_result,
    build_rejected_call_envelope,
    build_state_action,
    call_send_sequence,
    finalize_owned_result_envelope,
    inspect_call_envelope,
    validate_action,
    validate_result,
)
from citry.citry_element import CitryElement, RenderProvides, RenderTemplateGlobals
from citry.ext.events._pydantic_bounded import TOO_SLOW_MESSAGE, ValidationTooCostly, current_work, request_work

# The csrf_failed message is example-locked contract text; it lives next to
# the floor that raises it (csrf.py) and is shared here for the fallback path
# of a broken user policy.
from citry.ext.events.actions import Render, _download_content_disposition
from citry.ext.events.csrf import _MSG_CSRF_FAILED, csrf_field_names
from citry.ext.events.errors import EventError, limit_unexpected_fields, unlisted_fields_note, wire_error
from citry.ext.events.handlers import event_options
from citry.ext.events.results import (
    HTML_RENDER_ENCODER,
    RenderEncoder,
    RenderEncodingContext,
    coerce_result,
    encode_actions,
    extract_download_result,
    track_constructed_actions,
    warn_unreturned_actions,
)
from citry.ext.events.schemas import StringArgs, declared_field_names, validate_args
from citry.ext.events.state import (
    TOO_DEEP_TO_SIGN,
    check_changed_state,
    public_state_values,
    restore_state,
    state_model_kind,
    state_wire_values,
)
from citry.ext.events.tokens import (
    InvalidStateError,
    StaleStateError,
    StateUpdateError,
    apply_state_updates,
    commit_state_token,
    mint_state_token,
    oversized_state_decimals,
    prepare_state_token,
    state_bytes,
    state_growth_error,
    state_renewal_due,
    verify_state_token,
)
from citry.extension import _as_list_of_items
from citry.util.logger import logger
from citry.util.routing import RouteHeaders, RouteResponse, call_maybe_sync

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry.citry import Citry
    from citry.component import Component
    from citry.ext.events.extension import EventHandler, EventsInfo

__all__ = [
    "CAPABILITIES_BASELINE_V1",
    "PROTOCOL",
    "CallEvent",
    "EventRequest",
    "EventsDispatcher",
    "OnEventContext",
    "OnEventErrorContext",
    "OnEventResultContext",
    "RenderInputs",
    "TransportContext",
]

# Wire error messages locked by the protocol examples (exact text is
# contract; see the module docstring). The csrf_failed text is imported from
# ``csrf.py`` above.
_MSG_INVALID_STATE = "The state token failed verification (tampered or malformed)."
_MSG_STALE_STATE = "The state token is stale (expired or rotated out); reload the page to get a fresh one."
_MSG_HANDLER_ERROR = "The event handler raised an unexpected error."
_MSG_UNENCODABLE_RESULT = (
    "The handler returned a value strict JSON cannot encode (for example, a Decimal or a non-finite number such as "
    "inf or nan)."
)

# Sentinel: "the on_event hook did not answer the call" (None is a valid
# answer, meaning acknowledged with no actions).
_NOT_ANSWERED: Any = object()


# The action kinds a user sees applied (a state refresh is bookkeeping); used
# by the debug hint for a handler that mutated state but returned nothing
# visible (design 3.4).
_VISIBLE_KINDS = frozenset({"render", "data", "event", "redirect", "url"})

################################################
# THE SHAPES THE DISPATCHER RECEIVES AND INJECTS
################################################


@dataclass(frozen=True, slots=True)
class TransportContext:
    """
    What a transport tells the dispatcher about the request it decoded.

    One is built per request by the transport (the HTTP routes build it in
    ``citry.ext.events.routes``; a custom transport builds its own) and
    passed to [`EventsDispatcher.dispatch`][citry.ext.events.EventsDispatcher.dispatch].

    Experimental:
        Part of the experimental API for running event calls from server
        code. It stays usable, but it may change in a 1.x minor release
        without a deprecation period. The ``citry-events/1`` format it
        carries is frozen for all of 1.x.

    Attributes:
        transport: The transport's name, such as ``"http"``; handlers see it
            as ``event.transport``.
        citry: The engine the call dispatches against.
        host_request: The untouched host request object (Django's
            ``HttpRequest``, the ASGI scope, or a custom transport's own
            object); ``None`` when the transport has none.
        headers: A case-insensitive view of the request headers; empty when
            the transport carries none. When they hold `X-Citry-Page-Nonce`
            and the app sets no `_csp_nonce`, an HTML `Render` carries that
            nonce, so send the answer with `Cache-Control: no-store` and
            list `X-Citry-Page-Nonce` in its `Vary` header, as Citry's HTTP
            routes do.
        response_mode: ``"wire"`` for an ordinary result envelope, or
            ``"compat"`` when the HTTP transport will turn one call into a
            browser-native HTML, redirect, JSON, or empty response.

    """

    transport: str
    citry: Citry
    host_request: Any = None
    headers: Mapping[str, str] = field(default_factory=RouteHeaders)
    response_mode: Literal["wire", "compat"] = "wire"


@dataclass(frozen=True, slots=True)
class EventRequest:
    """
    The ``request`` value injected into event handlers.

    The framework-neutral request fields, always populated: the
    HTTP routes fill everything; other transports fill what they carry. The
    untouched host object stays reachable as ``native``, and
    ``event.transport`` says which transport built it.

    Attributes:
        method: The HTTP method, uppercase.
        path: The full URL path of the request.
        query: The query-string parameters; each key maps to every value it
            was sent with, in order.
        headers: The request headers; lookups ignore case.
        body: The raw request body.
        content_type: The ``Content-Type`` header value, or ``""``.
        form: The parsed form fields of a form post (urlencoded today),
            mapping field name to its string value (or list of values for a
            repeated field); empty for non-form requests.
        files: Uploaded files by field name when the selected payload codec or
            transport supplies them; otherwise empty.
        native: The untouched host request object.

    """

    method: str = "GET"
    path: str = ""
    query: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=RouteHeaders)
    body: bytes = b""
    content_type: str = ""
    form: Mapping[str, Any] = field(default_factory=dict)
    files: Mapping[str, Any] = field(default_factory=dict)
    native: Any = None


class RenderInputs(TypedDict, total=False):
    """
    The keyword arguments Citry passes to `render()` for each component a `Render` renders.

    A `_render_inputs` function returns this dict, from a component's
    `Events` class or from `extensions_defaults["events"]`. Citry then calls
    `.render(template_globals=..., provides=...)` with these values on each
    component a `Render` renders, exactly as you would when you render the
    component yourself. Both keys are optional, and each field has the type
    of the [`render()`][citry.CitryElement.render] parameter of the same
    name.

    Experimental:
        It may change in a 1.x minor release without a deprecation period.

    Attributes:
        template_globals: Template variables every template in the render
            can read.
        provides: Values the rendered components can read with `inject()`.

    Example:
        ```python
        from citry.ext.events import EventRequest, RenderInputs

        def render_inputs(request: EventRequest) -> RenderInputs:
            return {
                "template_globals": {"user": request.native.user},
                "provides": {"locale": "en-GB"},
            }
        ```

    """

    template_globals: RenderTemplateGlobals | None
    provides: RenderProvides | None


# The type of a `_render_inputs` function, on a component's `Events` class or
# in `extensions_defaults["events"]`.
RenderInputsFunction: TypeAlias = "Callable[[EventRequest], RenderInputs]"


@dataclass(frozen=True, slots=True)
class CallEvent:
    """
    The ``event`` value injected into event handlers: metadata about one call.

    Attributes:
        name: The handler's wire name the call addressed.
        instance_id: The calling instance's render id, or ``None`` for an
            instance-less call (an API client, a hand-written form).
        transport: The transport that carried the call (``"http"``, ...).
        args: The call's args before validation, with the host CSRF field
            names removed (the ``_csrf_field_names`` key of
            ``extensions_defaults["events"]``).
            Guards read this when they need payload values, because one guard
            covers handlers with different schemas.

    """

    name: str
    instance_id: str | None
    transport: str
    args: Mapping[str, Any]


################################################
# EMIT-HOOK CONTEXTS
################################################


@dataclass(frozen=True, slots=True)
class OnEventContext:
    """
    Context of the ``on_event`` emit hook, fired before every handler run.

    Fires after token verification and args validation, before ``_context``
    and guards (design 3.7), with ``result="first"``: an extension that
    returns a non-``None`` value answers the call in the handler's place
    (the value is coerced exactly like a handler return value), and raising
    [`EventError`][citry.ext.events.EventError] denies the call.
    This is where rate limiting plugs in.

    Attributes:
        citry: The engine the call dispatches against.
        component_class: The component class the call resolved to.
        handler: The resolved event handler record.
        events: The per-call events instance; its ambient attributes
            (``state``, ``request``, ``event``) are populated, ``context``
            is not yet (the ``_context`` hook runs after this emit).
        call: The raw wire call object.

    """

    citry: Citry
    component_class: type[Component]
    handler: EventHandler
    events: Any
    call: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class OnEventResultContext:
    """
    Context of the ``on_event_result`` emit hook, fired after the handler.

    Fires with ``result="map"`` over ``actions``: an extension that returns a
    list replaces the encoded wire actions the next extension (and finally
    the client) sees.

    Attributes:
        citry: The engine the call dispatched against.
        component_class: The component class the call resolved to.
        handler: The resolved event handler record.
        events: The per-call events instance the handler ran on.
        actions: The encoded wire actions, in return order.

    """

    citry: Citry
    component_class: type[Component]
    handler: EventHandler
    events: Any
    actions: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class OnEventErrorContext:
    """
    Context of the ``on_event_error`` emit hook, fired on an uncaught exception.

    Fires with ``result="first"``: an extension (a Sentry integration, say)
    can observe the exception, or return a result object (the
    ``{"ok": False, "error": {...}}`` shape) to replace the default 500
    answer.

    Attributes:
        citry: The engine the call dispatched against.
        component_class: The component class, or ``None`` when the error hit
            before resolution.
        handler: The resolved handler record, or ``None`` before resolution.
        events: The per-call events instance, or ``None`` before it existed.
        error: The uncaught exception.
        result: The default result object the call will answer with unless
            an extension returns a replacement.

    """

    citry: Citry
    component_class: type[Component] | None
    handler: EventHandler | None
    events: Any
    error: BaseException
    result: dict[str, Any]


################################################
# INTERNAL PER-CALL BOOKKEEPING
################################################


def _page_csp_nonce(ctx: TransportContext, plan: _CallPlan) -> str | None:
    """
    Return the CSP nonce of the page that sent the call.

    An HTML fragment from a Render starts on a nonce-protected page only when
    it carries that page's nonce. The app's ``_csp_nonce`` function answers
    when the app set one. Otherwise the ``X-Citry-Page-Nonce`` header that
    page code sends (from ``Citry.pageNonce()``) does, which works even with
    several tabs open. A made-up header only changes the answer to its own
    call. The HTTP routes mark every answer so that no cache passes it on;
    a custom transport must do the same (see ``TransportContext``).
    """
    nonce_for = ctx.citry.settings.extensions_defaults.get("events", {}).get("_csp_nonce")
    if nonce_for is None:
        return page_nonce_from_headers(ctx.headers)
    nonce = nonce_for(plan.events.request)
    # A wrong type would otherwise surface as a confusing error deep inside
    # serialize(); the call still answers handler_error either way.
    if nonce is not None and not isinstance(nonce, str):
        msg = f"The events '_csp_nonce' function must return a str or None; got {type(nonce).__name__}."
        raise TypeError(msg)
    return nonce


# The keys a ``_render_inputs`` function may return, matching the keyword
# arguments of ``CitryElement.render()`` they are passed to.
_RENDER_INPUT_KEYS = frozenset({"template_globals", "provides"})


def _call_render_inputs(plan: _CallPlan) -> tuple[RenderTemplateGlobals | None, RenderProvides | None]:
    """
    Return the template globals and provided values for this call's renders, from ``_render_inputs``.

    A page render gets request values (the user, the locale) from the app's
    own view, but a Render from a handler has no view around it, so the
    app's function supplies them for each call instead. The calling
    component's ``Events`` value was already resolved over the engine default
    when the class was defined.
    """
    inputs_for = plan.info.render_inputs
    if inputs_for is None:
        return None, None
    # Typed as Any: the function's annotation is a promise the app's code may
    # not keep, and the checks below are what Citry relies on.
    inputs: Any = inputs_for(plan.events.request)
    # A wrong shape is reported against the setting here, rather than as a
    # confusing error from inside the render; the call still answers
    # handler_error either way.
    if not isinstance(inputs, Mapping):
        msg = (
            "The events '_render_inputs' function must return a dict with the optional keys"
            f" 'template_globals' and 'provides'; got {type(inputs).__name__}."
        )
        raise TypeError(msg)
    unknown = sorted(str(key) for key in inputs if key not in _RENDER_INPUT_KEYS)
    if unknown:
        msg = (
            f"The events '_render_inputs' function returned unknown keys {unknown};"
            " the recognized keys are 'template_globals' and 'provides'."
        )
        raise TypeError(msg)
    template_globals = inputs.get("template_globals")
    provides = inputs.get("provides")
    for key, value in (("template_globals", template_globals), ("provides", provides)):
        if value is not None and not isinstance(value, Mapping):
            msg = (
                f"The events '_render_inputs' function must return a mapping or None for {key!r};"
                f" got {type(value).__name__}."
            )
            raise TypeError(msg)
    return template_globals, provides


@dataclass(slots=True)
class _CallPlan:
    """Everything the pipeline resolved for one call, ready for the handler to run."""

    comp_cls: type[Component]
    info: EventsInfo
    handler: EventHandler
    events: Any
    kwargs: dict[str, Any]
    state: Any
    state_fingerprint: str | None
    # The verified token is past half its lifetime, so the call sends a new
    # one even when State does not change (see `_resign_state`).
    renew_state: bool
    instance_id: str | None
    send_sequence: int | None
    # The on_event hook's answer, when an extension answered the call in the
    # handler's place; _NOT_ANSWERED means the handler runs.
    answered: Any


def _without_csrf_fields(args: dict[str, Any], data_schema: type | None, names: frozenset[str]) -> Any:
    """
    Return the call's args without the host CSRF fields that the data class does not declare.

    The result keeps the args' own class, so a form post's
    [`StringArgs`][citry.ext.events.schemas.StringArgs] still binds text to
    numbers and booleans. A data class that declares one of these names
    receives it like any other field.
    """
    present = names.intersection(args)
    if not present:
        return args
    if data_schema is not None:
        present -= declared_field_names(data_schema)
        if not present:
            return args
    return type(args)({key: value for key, value in args.items() if key not in present})


def _state_fingerprint(state: Any) -> str | None:
    """
    A comparable snapshot of a State instance's fields.

    Canonical JSON, so ``1`` and ``True`` (equal in Python, different on the
    wire) fingerprint differently. ``None`` means the fields cannot be
    serialized right now, which the caller treats as "changed" so the mint
    step gets to raise its own pointed error.
    """
    try:
        values = state_wire_values(state)
        return json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError):
        # A State nested past Python's recursion limit has no fingerprint, so
        # it counts as changed, and `check_changed_state` reports the depth.
        return None


def _too_deep_to_write(state: Any) -> bool:
    """Whether Pydantic stops writing ``state`` out as JSON because it nests too deeply."""
    try:
        state_wire_values(state)
    except ValueError as error:
        # `state_wire_values` marks that stop with this cause (see its docstring).
        cause = error.__cause__
        return isinstance(cause, ValidationTooCostly) and cause.reason == "depth"
    except Exception:  # noqa: BLE001 - other failures are reported where the State is signed
        return False
    return False


# The component class ids and error kinds whose failed State token renewal was
# already logged, so each warns once rather than on every call for up to half
# a token lifetime, while a different kind of failure still warns. Later
# repeats log at debug level.
_RENEWAL_FAILURES_LOGGED: set[tuple[str, str]] = set()


def _log_failed_renewal(comp_cls: type[Component], err: Exception) -> None:
    """Log why a State token could not be renewed: a warning once per component class and error kind, then debug."""
    message = (
        f"Component {comp_cls.__name__}: the State token is past half its lifetime, but a new one could not be"
        f" made, so the page keeps its current token until it expires: {type(err).__name__}: {err}"
    )
    seen = (comp_cls.class_id, type(err).__name__)
    if seen in _RENEWAL_FAILURES_LOGGED:
        logger.debug(message)
        return
    _RENEWAL_FAILURES_LOGGED.add(seen)
    # A value that cannot be signed or a cache that is down is expected and
    # explained by the message. Anything else may be a bug in Citry, which
    # would otherwise show only as pages expiring, so it keeps its traceback.
    logger.warning(message, exc_info=not isinstance(err, (ValueError, OSError)))


def _instances_given_a_token(wire_actions: list[dict[str, Any]]) -> set[str]:
    """The render ids that these result actions give a new State token."""
    ids: set[str] = set()
    for action in wire_actions:
        if action.get("action") == "state":
            ids.add(action["targetRenderId"])
        elif action.get("action") == "render":
            # A render of a component carries that component's new token in
            # the content it sends; a `mark:` region inside one carries none.
            target = action.get("target")
            if isinstance(target, str) and target.startswith("render:"):
                ids.add(target.removeprefix("render:"))
    return ids


def _is_detached(handler: EventHandler) -> bool:
    """Whether the handler was declared ``@event(detached=True)``."""
    options = event_options(handler.func)
    return options is not None and options.detached


def _detached_render_message(plan: _CallPlan) -> str:
    """The error for a detached handler whose result holds a render."""
    return (
        f"Event handler {plan.handler.name!r} on component {plan.comp_cls.__name__} is declared with"
        f" @event(detached=True) but returned actions.Render (or a component). A detached handler may"
        f" return data, dispatch an event, redirect, update the URL, or return a Download; remove"
        f" detached=True to render."
    )


def _debug_enabled() -> bool:
    """Debug mode is the ``"citry"`` logger at DEBUG; the engine has no separate flag."""
    return logger.isEnabledFor(logging.DEBUG)


################################################
# THE DISPATCHER
################################################


class EventsDispatcher:
    """
    Runs call envelopes through the events pipeline and answers result envelopes.

    Stateless: everything a dispatch needs rides in the envelope and the
    [`TransportContext`][citry.ext.events.TransportContext], so
    one instance (or a fresh one per call) serves every transport. The HTTP
    routes own the built-in usage; a custom transport (a GraphQL mutation
    resolver, say) decodes its request into the same JSON call that Citry's
    browser code sends (the ``citry-events/1`` call envelope)
    and calls [`dispatch`][citry.ext.events.EventsDispatcher.dispatch]
    (or its async twin) directly.

    ``EventsDispatcher()`` with no arguments answers a render only as
    ``html-fragment/1``. Citry's own browser code asks for
    ``vue-prepared/1`` renders, so a handler that returns a render fails
    when such a page calls through this dispatcher. A transport that
    serves Citry's own pages forwards calls to Citry's HTTP routes.

    Experimental:
        Part of the experimental API for running event calls from server
        code. It stays usable, but it may change in a 1.x minor release
        without a deprecation period. The ``citry-events/1`` format it
        reads and writes is frozen for all of 1.x.
    """

    def __init__(
        self,
        *,
        render_encoders: tuple[RenderEncoder, ...] = (HTML_RENDER_ENCODER,),
        preferred_renderer: str = "html-fragment/1",
    ) -> None:
        registry: dict[str, RenderEncoder] = {}
        for encoder in render_encoders:
            if encoder.renderer not in RENDERERS:
                raise ValueError(f"Unknown render encoder renderer {encoder.renderer!r}.")
            if encoder.renderer in registry:
                raise ValueError(f"A render encoder is already registered for {encoder.renderer!r}.")
            registry[encoder.renderer] = encoder
        if preferred_renderer not in registry:
            raise ValueError(f"The preferred renderer {preferred_renderer!r} has no registered encoder.")
        self._render_encoders = registry
        self._preferred_renderer = preferred_renderer

    def dispatch(
        self,
        envelope: Mapping[str, Any],
        ctx: TransportContext,
        *,
        request: EventRequest | None = None,
        url_component: str | None = None,
        url_event: str | None = None,
        csrf_check: Callable[[EventHandler], None] | None = None,
    ) -> dict[str, Any] | RouteResponse:
        """
        Dispatch a call envelope synchronously and return the result envelope.

        This is the plain-``def`` pipeline WSGI and sync Django hosts run.
        An ``async def`` event handler is answered with the 500 error naming
        the fix (dispatch through
        [`dispatch_async`][citry.ext.events.EventsDispatcher.dispatch_async],
        which an async transport calls); it is never silently run on a
        private event loop.

        Args:
            envelope: The decoded ``citry-events/1`` call envelope.
            ctx: What the transport knows about the request.
            request: The neutral request injected into handlers as
                ``request``; ``None`` builds an empty one carrying
                ``ctx.host_request`` as ``native``.
            url_component: The class id the per-event URL names; when given,
                the URL is authoritative and a differing body field is
                rejected. ``None`` on the batch endpoint.
            url_event: The event wire name the per-event URL names. A raw
                response additionally requires HTTP and
                ``@event(bundle=False)``.
            csrf_check: The transport's per-call CSRF check, called with the
                resolved handler; raise to reject the call as
                ``csrf_failed``. ``None`` skips the check (a transport with
                its own protection, or a direct caller).

        Returns:
            The ``citry-events/1`` result envelope, or the handler's
            ``RouteResponse`` when the per-event escape hatch was used.

        """
        checked = self._check_envelope(envelope)
        if isinstance(checked, dict):
            return checked
        envelope_id, calls, capabilities = checked
        results: list[dict[str, Any]] = []
        # The caller instances that an earlier call in this request already
        # sent a token, so a later call does not renew from older State.
        token_sent_to: set[str] = set()
        # The calls of one request share one work budget for data that can be
        # checked more than once.
        with request_work():
            for call in calls:
                outcome = self._run_call_sync(
                    call,
                    ctx,
                    capabilities=capabilities,
                    token_sent_to=token_sent_to,
                    request=request,
                    url_component=url_component,
                    url_event=url_event,
                    csrf_check=csrf_check,
                )
                if isinstance(outcome, RouteResponse):
                    return outcome
                results.append(outcome)
        return finalize_owned_result_envelope(envelope_id, results)

    async def dispatch_async(
        self,
        envelope: Mapping[str, Any],
        ctx: TransportContext,
        *,
        request: EventRequest | None = None,
        url_component: str | None = None,
        url_event: str | None = None,
        csrf_check: Callable[[EventHandler], None] | None = None,
    ) -> dict[str, Any] | RouteResponse:
        """
        Dispatch a call envelope from async code.

        The one behavioral difference from
        [`dispatch`][citry.ext.events.EventsDispatcher.dispatch]:
        ``async def`` event handlers are awaited on the running loop, and
        sync handlers run in a worker thread so they cannot block it.

        Args:
            envelope: The decoded call envelope.
            ctx: What the transport knows about the request.
            request: The neutral request injected into handlers, or ``None``
                to build one from ``ctx.host_request``.
            url_component: The class id named by a per-event URL, or ``None``
                for a batch or custom transport.
            url_event: The event name named by a per-event URL. A raw response
                additionally requires HTTP and ``@event(bundle=False)``.
            csrf_check: A callable that raises to reject a resolved handler,
                or ``None`` when the transport provides its own protection.

        Returns:
            The result envelope, or the handler's ``RouteResponse`` when the
            per-event response escape was used.

        """
        checked = self._check_envelope(envelope)
        if isinstance(checked, dict):
            return checked
        envelope_id, calls, capabilities = checked
        results: list[dict[str, Any]] = []
        # The caller instances that an earlier call in this request already
        # sent a token, so a later call does not renew from older State.
        token_sent_to: set[str] = set()
        # The calls of one request share one work budget for data that can be
        # checked more than once.
        with request_work():
            for call in calls:
                outcome = await self._run_call_async(
                    call,
                    ctx,
                    capabilities=capabilities,
                    token_sent_to=token_sent_to,
                    request=request,
                    url_component=url_component,
                    url_event=url_event,
                    csrf_check=csrf_check,
                )
                if isinstance(outcome, RouteResponse):
                    return outcome
                results.append(outcome)
        return finalize_owned_result_envelope(envelope_id, results)

    # ----- Envelope-level validation -----

    def _check_envelope(
        self, envelope: Mapping[str, Any]
    ) -> dict[str, Any] | tuple[str, list[Any], dict[str, frozenset[str]]]:
        """
        Structurally validate the envelope; reject it as a whole on failure.

        The embedded protocol package owns the fixed records and returns the
        parsed pieces on success. With a usable request ID, a rejection mirrors
        the error into every call slot. Without one, it returns the single
        uncorrelated transport-edge error permitted by the result schema.
        """
        checked = inspect_call_envelope(envelope)
        if isinstance(checked, CallEnvelopeFailure):
            return build_rejected_call_envelope(
                envelope,
                status=checked.status,
                code=checked.code,
                message=checked.issue.message,
            )
        return checked.request_id, checked.calls, checked.capabilities

    # ----- The per-call pipeline -----

    def _run_call_sync(
        self,
        call: Any,
        ctx: TransportContext,
        *,
        capabilities: dict[str, frozenset[str]],
        token_sent_to: set[str],
        request: EventRequest | None,
        url_component: str | None,
        url_event: str | None,
        csrf_check: Callable[[EventHandler], None] | None,
    ) -> dict[str, Any] | RouteResponse:
        """One call through the sync pipeline; see ``dispatch`` for the split."""
        plan = self._prepare_call(
            call,
            ctx,
            capabilities=capabilities,
            request=request,
            url_component=url_component,
            url_event=url_event,
            csrf_check=csrf_check,
        )
        if isinstance(plan, dict):
            return plan
        try:
            with track_constructed_actions(plan.events):
                if plan.answered is not _NOT_ANSWERED:
                    value = plan.answered
                else:
                    if inspect.iscoroutinefunction(plan.handler.func):
                        msg = (
                            f"Event handler {plan.handler.name!r} on component"
                            f" {plan.comp_cls.__name__} is 'async def', but the call arrived"
                            f" through a synchronous host (WSGI or sync Django). Deploy under"
                            f" ASGI (an async transport dispatches through dispatch_async),"
                            f" or make the handler a plain 'def'."
                        )
                        raise RuntimeError(msg)
                    value = plan.handler.func(plan.events, **plan.kwargs)
                response = self._extract_response_result(
                    plan,
                    value,
                    ctx=ctx,
                    per_event=url_component is not None and url_event is not None,
                )
                if response is not None:
                    return response
                actions = coerce_result(
                    value,
                    resolvers=ctx.citry.settings.event_result_resolvers,
                    events=plan.events,
                    handler=plan.handler.name,
                )
                warn_unreturned_actions(plan.events, actions, plan.handler.name)
            return self._complete_call(plan, ctx, actions, capabilities, token_sent_to)
        except EventError as err:
            return build_error_result(wire_error(err), plan.send_sequence)
        except Exception as err:  # noqa: BLE001 - the dispatcher answers 500, never crashes the host
            return self._unexpected_error(ctx, err, plan=plan)

    async def _run_call_async(
        self,
        call: Any,
        ctx: TransportContext,
        *,
        capabilities: dict[str, frozenset[str]],
        token_sent_to: set[str],
        request: EventRequest | None,
        url_component: str | None,
        url_event: str | None,
        csrf_check: Callable[[EventHandler], None] | None,
    ) -> dict[str, Any] | RouteResponse:
        """The async twin of ``_run_call_sync``; only the handler invocation differs."""
        plan = self._prepare_call(
            call,
            ctx,
            capabilities=capabilities,
            request=request,
            url_component=url_component,
            url_event=url_event,
            csrf_check=csrf_check,
        )
        if isinstance(plan, dict):
            return plan
        try:
            with track_constructed_actions(plan.events):
                if plan.answered is not _NOT_ANSWERED:
                    value = plan.answered
                else:
                    # Async handlers are awaited on the running loop; sync
                    # ones run in a worker thread so they cannot block it.
                    value = await call_maybe_sync(plan.handler.func, plan.events, **plan.kwargs)
                response = self._extract_response_result(
                    plan,
                    value,
                    ctx=ctx,
                    per_event=url_component is not None and url_event is not None,
                )
                if response is not None:
                    return response
                actions = coerce_result(
                    value,
                    resolvers=ctx.citry.settings.event_result_resolvers,
                    events=plan.events,
                    handler=plan.handler.name,
                )
                warn_unreturned_actions(plan.events, actions, plan.handler.name)
            return self._complete_call(plan, ctx, actions, capabilities, token_sent_to)
        except EventError as err:
            return build_error_result(wire_error(err), plan.send_sequence)
        except Exception as err:  # noqa: BLE001 - the dispatcher answers 500, never crashes the host
            return self._unexpected_error(ctx, err, plan=plan)

    def _prepare_call(
        self,
        call: Any,
        ctx: TransportContext,
        *,
        capabilities: dict[str, frozenset[str]],
        request: EventRequest | None,
        url_component: str | None,
        url_event: str | None,
        csrf_check: Callable[[EventHandler], None] | None,
    ) -> _CallPlan | dict[str, Any]:
        """
        Everything before the handler runs: validate, resolve, verify, inject.

        Returns the ready plan, or the finished (usually failed) result item
        when the call ends before the handler.
        """
        if not isinstance(call, Mapping):
            error = build_error(400, "protocol_mismatch", "Each entry of 'calls' must be a call object.")
            return build_error_result(error, None)

        # The complete envelope was validated before the dispatcher entered
        # its call loop, so no handler can run before a malformed later call
        # is rejected. Read the already-proved correlation counter here.
        send_sequence = call_send_sequence(call)

        # Component and event resolution. The per-event URL is authoritative:
        # body fields must match it when present (design 3.8).
        mismatch = self._url_body_mismatch(call, url_component=url_component, url_event=url_event)
        if mismatch is not None:
            return build_error_result(mismatch, send_sequence)
        class_id = url_component if url_component is not None else call.get("componentClassId")
        event_name = url_event if url_event is not None else call.get("handlerName")
        if class_id is None:
            error = build_error(
                400,
                "protocol_mismatch",
                "The call names no component; the batch endpoint requires each call to carry its target's class id.",
            )
            return build_error_result(error, send_sequence)
        if event_name is None:
            error = build_error(
                400,
                "protocol_mismatch",
                "The call names no event; the batch endpoint requires each call to carry the handler's wire name.",
            )
            return build_error_result(error, send_sequence)
        try:
            comp_cls = ctx.citry.get_component_by_class_id(class_id)
        except KeyError:
            error = build_error(404, "unknown_component", f"No component with class id {class_id!r} is registered.")
            return build_error_result(error, send_sequence)
        extension = ctx.citry.extensions.get_extension("events")
        info: EventsInfo = extension.resolve(comp_cls)  # type: ignore[attr-defined]
        handler = info.handlers.get(event_name)
        if handler is None:
            error = build_error(404, "unknown_event", f"Component {comp_cls.__name__!r} has no event {event_name!r}.")
            return build_error_result(error, send_sequence)

        # The transport's CSRF check (HTTP attaches the floor and the
        # per-handler policy; design 7.4). Any rejection answers csrf_failed.
        if csrf_check is not None:
            try:
                csrf_check(handler)
            except EventError as err:
                return build_error_result(build_error(403, "csrf_failed", err.message, err.fields), send_sequence)
            except Exception:  # noqa: BLE001 - a broken user policy still answers the fixed wire error
                logger.exception(f"The CSRF policy for event {event_name!r} on {comp_cls.__name__} raised.")
                return build_error_result(build_error(403, "csrf_failed", _MSG_CSRF_FAILED), send_sequence)

        # Token verification and two-way binding updates (design 6.1, WP8).
        state = None
        state_fingerprint: str | None = None
        renew_state = False
        token = call.get("stateToken")
        updates = call.get("stateUpdates")
        needs_state = "state" in handler.params
        if updates is not None and _is_detached(handler):
            # A detached handler never returns a new State token, so browser
            # State changes applied here would be lost after the call. Even
            # an empty object is refused, matching the browser's own check.
            error = build_error(
                422,
                "invalid_args",
                f"The call carries state updates, but event {event_name!r} on component"
                f" {comp_cls.__name__!r} is declared with @event(detached=True), so it cannot change State."
                f" Send the State updates with a call to a handler that is not detached.",
            )
            return build_error_result(error, send_sequence)
        if info.state_cls is None:
            # A stray token on a stateless component is ignored (there is
            # nothing to rebuild), but updates have no writable target.
            if updates:
                error = build_error(
                    422,
                    "invalid_args",
                    f"The call carries state updates, but component {comp_cls.__name__!r} declares no State class.",
                )
                return build_error_result(error, send_sequence)
        elif token is not None or needs_state or updates:
            secrets = list(ctx.citry.settings.secret or [])
            # The State class and its meta are resolved together, so the meta
            # is always here; an empty storage would refuse every token.
            storage = info.state_meta.storage if info.state_meta is not None else ""
            try:
                # A call that needs state but carries no token verifies the
                # empty string, which maps to the malformed 403 like any
                # other unreadable token.
                verified = verify_state_token(
                    token or "",
                    cls=comp_cls,
                    storage=storage,
                    secrets=secrets,
                    cache=ctx.citry.cache,
                )
            except InvalidStateError as err:
                logger.debug(err.message)
                return build_error_result(build_error(403, "invalid_state", _MSG_INVALID_STATE), send_sequence)
            except StaleStateError as err:
                logger.debug(err.message)
                return build_error_result(build_error(409, "stale_state", _MSG_STALE_STATE), send_sequence)
            budget = current_work()
            if state_model_kind(info.state_cls) == "v1" and budget is not None and budget.out_of_time():
                # A Pydantic v1 restore counts toward the request's CPU limit
                # but cannot be stopped partway outside a check (see
                # `_parse_v1`), so once earlier work used the time up, this
                # call is refused before it starts another one.
                error = build_error(
                    422,
                    "invalid_args",
                    f"The State of component {comp_cls.__name__!r} could not be checked in time.",
                    {"_state": TOO_SLOW_MESSAGE},
                )
                return build_error_result(error, send_sequence)
            try:
                state = restore_state(info.state_cls, verified.state_kwargs)
            except Exception as err:  # noqa: BLE001 - a validator's own bug must not escape the dispatcher
                if not isinstance(err, (TypeError, ValueError)):
                    # Not a value that no longer fits: a State validator
                    # failed, which is the author's bug and answers 500.
                    return self._unexpected_error(
                        ctx, err, comp_cls=comp_cls, handler=handler, send_sequence=send_sequence
                    )
                # A model State validates its values here, and a
                # ValidationError means the same as a dataclass's TypeError.
                # The page only learns that it is out of date, so the server log says why.
                logger.warning(
                    f"Component {comp_cls.__name__}: a verified State token no longer fits the State class, so the"
                    f" call answers stale_state: {type(err).__name__}."
                )
                # The token verified but its fields no longer match the State
                # class: the version-skew case (the class changed across a
                # deploy), which is the stale-token story (design 4.5).
                return build_error_result(build_error(409, "stale_state", _MSG_STALE_STATE), send_sequence)
            # JSON has no tuple, so a tuple field comes back from the token as
            # a list. Restore it before the fingerprint, so the handler and any
            # component it renders from this State see the declared type.
            _restore_json_tuples(state, info.state_cls)
            # A token signed by an earlier release, or State the app filled
            # itself, may hold a Decimal far too large to write out.
            # Refusing the call here, before the handler, keeps the value off
            # the page and stops the server from signing such a token again
            # with a new expiry.
            oversized = oversized_state_decimals(state, info.state_cls)
            if oversized is not None:
                # The field names are the author's own, so the log can name
                # them and point the author at a value their code put there.
                logger.warning(
                    f"Component {comp_cls.__name__}: a verified State token holds a Decimal outside the range"
                    f" Citry accepts from a request in {sorted(oversized)}, so the call answers invalid_args."
                )
                error = build_error(
                    422,
                    "invalid_args",
                    f"The State of component {comp_cls.__name__!r} holds a number that is too large"
                    " or has too many decimal places.",
                    oversized,
                )
                return build_error_result(error, send_sequence)
            state_fingerprint = _state_fingerprint(state)
            renew_state = state_renewal_due(verified)
            if state_fingerprint is None and _too_deep_to_write(state):
                # Pydantic's limit on writing nested values depends on the
                # platform, so a token signed by a server with a higher limit
                # can hold a State this server cannot write out again. It is
                # stale here, as a State too deep to restore is, and the call
                # ends before the handler runs.
                logger.warning(
                    f"Component {comp_cls.__name__}: a verified State token holds a State nested too deeply for"
                    " Pydantic to write as JSON on this server, so the call answers stale_state."
                )
                return build_error_result(build_error(409, "stale_state", _MSG_STALE_STATE), send_sequence)
            if updates and info.state_meta is not None:
                meta = info.state_meta
                # A browser write must not make State larger than the cap:
                # signed storage could not sign it after the handler ran, and
                # server storage keeps every changed State in the cache. The
                # check runs here, before the handler, so a refused call has
                # no side effects.
                capped = meta.max_bytes is not None
                if meta.storage != "server":
                    # Signed State is signed again only for a caller instance
                    # that accepts the `state` action (see `_resign_state`).
                    # A call that makes no token, such as an API call, keeps
                    # working with a State it never sends back.
                    accepted = (
                        CAPABILITIES_BASELINE_V1["actions"]
                        if ctx.response_mode == "compat"
                        else capabilities["actions"]
                    )
                    capped = capped and call.get("callerRenderId") is not None and "state" in accepted
                # Server storage may hold a State the server itself made
                # larger than the cap, which the browser may still change
                # as long as it does not grow it. A signed State over the cap
                # cannot be signed at all, so it has no size to compare with.
                compares = capped and meta.storage == "server"
                size_before = state_bytes(state, comp_cls.class_id) if compares else None
                try:
                    apply_state_updates(state, updates, model_fields=meta.model)
                except StateUpdateError as err:
                    return build_error_result(build_error(422, "invalid_args", err.message, err.fields), send_sequence)
                # A browser update for a tuple field also arrives as a list.
                _restore_json_tuples(state, info.state_cls)
                if capped:
                    too_large = state_growth_error(
                        before=size_before,
                        after=state_bytes(state, comp_cls.class_id),
                        max_bytes=meta.max_bytes,
                        component_name=comp_cls.__name__,
                    )
                    if too_large is not None:
                        return build_error_result(build_error(422, "invalid_args", too_large), send_sequence)

        # Args validation against the handler's data schema (design 3.3, WP9).
        args = call.get("args") or {}
        # The browser marks args it collected from a form: their values are
        # the form's text, so they bind to numbers and booleans exactly as a
        # no-JS form post does. Without the mark, JSON values stay strict.
        if call.get("argsSource") == ARGS_SOURCE_FORM:
            args = StringArgs(args)
        # A form may hold the host's CSRF hidden field, which the browser and
        # a no-JS post both send as one more field; drop it first so the call
        # is not rejected for a field the data class never asked for. The
        # drop keeps the args' class, so the form conversion above survives.
        validation = None
        try:
            args = _without_csrf_fields(args, handler.data_schema, csrf_field_names(ctx.citry))
            if handler.data_schema is not None:
                validation = validate_args(handler.data_schema, args)
        except EventError as err:
            return build_error_result(wire_error(err), send_sequence)
        except Exception as err:  # noqa: BLE001 - a crash while checking args answers this call only
            # The data class's own code (a `__post_init__`, a validator, a
            # class Citry cannot read) may raise anything. Without this, the
            # exception would leave the dispatcher and end the whole
            # request, losing the results of the calls that already ran.
            return self._unexpected_error(
                ctx, err, comp_cls=comp_cls, handler=handler, send_sequence=send_sequence, checking_args=True
            )
        data_value: Any = None
        if validation is not None:
            if not validation.ok:
                message = f"The args for event {event_name!r} on component {comp_cls.__name__!r} did not validate."
                # Validation listed only the first undeclared keys and the
                # first item errors of each list or dict; the message
                # counts the rest.
                message += unlisted_fields_note(validation.unlisted_fields)
                return build_error_result(build_error(422, "invalid_args", message, validation.fields), send_sequence)
            data_value = validation.value
        elif args:
            # A handler that declares no data takes no input; extra keys are
            # a 422 here exactly as they are on a schema (design 3.3).
            message = f"The args for event {event_name!r} on component {comp_cls.__name__!r} did not validate."
            extra = dict.fromkeys(sorted(str(key) for key in args), "Unexpected field: not declared on the schema.")
            # Every key here is undeclared, so the request decides how many
            # there are: list the first few and count the rest.
            extra, unlisted = limit_unexpected_fields(extra, extra.keys())
            message += unlisted_fields_note(unlisted)
            return build_error_result(build_error(422, "invalid_args", message, extra), send_sequence)

        # The per-call events instance: the woven config class (the
        # component's Events class as the extension manager rebuilt it on the
        # config base), with the ambient attributes populated (design 3.3
        # "Ambient access").
        instance_id = call.get("callerRenderId")
        events_cls = getattr(comp_cls, "Events")  # noqa: B009 - the woven config class, always present
        events = events_cls(None)
        event_request = request if request is not None else EventRequest(headers=ctx.headers, native=ctx.host_request)
        call_event = CallEvent(name=event_name, instance_id=instance_id, transport=ctx.transport, args=args)
        events.state = state
        events.context = None
        events.request = event_request
        events.event = call_event

        answered: Any = _NOT_ANSWERED
        try:
            # on_event: veto or answer (design 3.7); fires before _context
            # and guards.
            hook_ctx = OnEventContext(
                citry=ctx.citry, component_class=comp_cls, handler=handler, events=events, call=call
            )
            veto = ctx.citry.extensions.emit("on_event", hook_ctx, result="first")
            if veto is not None:
                answered = veto
            else:
                # _context builds the per-call context injectable; guards read
                # it, so it runs first (design 3.6).
                if info.context is not None:
                    events.context = info.context(events)
                if handler.guard is not None:
                    handler.guard(events)
        except EventError as err:
            return build_error_result(wire_error(err), send_sequence)
        except Exception as err:  # noqa: BLE001 - a crash before the handler still answers 500
            return self._unexpected_error(
                ctx, err, comp_cls=comp_cls, handler=handler, events=events, send_sequence=send_sequence
            )

        injectables: dict[str, Any] = {
            "data": data_value,
            "state": state,
            "context": events.context,
            "request": event_request,
            "event": call_event,
        }
        kwargs = {name: injectables[name] for name in handler.params}
        return _CallPlan(
            comp_cls=comp_cls,
            info=info,
            handler=handler,
            events=events,
            kwargs=kwargs,
            state=state,
            state_fingerprint=state_fingerprint,
            renew_state=renew_state,
            instance_id=instance_id,
            send_sequence=send_sequence,
            answered=answered,
        )

    @staticmethod
    def _url_body_mismatch(
        call: Mapping[str, Any], *, url_component: str | None, url_event: str | None
    ) -> dict[str, Any] | None:
        """On the per-event route, a body naming a different target is rejected."""
        body_component = call.get("componentClassId")
        if url_component is not None and body_component is not None and body_component != url_component:
            return build_error(
                400,
                "protocol_mismatch",
                f"The call names component {body_component!r}, but the URL addresses {url_component!r};"
                f" the URL is authoritative on the per-event route.",
            )
        body_event = call.get("handlerName")
        if url_event is not None and body_event is not None and body_event != url_event:
            return build_error(
                400,
                "protocol_mismatch",
                f"The call names event {body_event!r}, but the URL addresses {url_event!r};"
                f" the URL is authoritative on the per-event route.",
            )
        return None

    def _extract_response_result(
        self,
        plan: _CallPlan,
        value: Any,
        *,
        ctx: TransportContext,
        per_event: bool,
    ) -> RouteResponse | None:
        """Extract and validate a raw response result before action coercion."""
        if isinstance(value, RouteResponse):
            warn_unreturned_actions(plan.events, [], plan.handler.name)
            return self._escape_route_response(
                plan,
                value,
                ctx=ctx,
                per_event=per_event,
                result_name="a RouteResponse",
            )
        download = extract_download_result(value, handler=plan.handler.name)
        if download is None:
            return None
        warn_unreturned_actions(plan.events, [download], plan.handler.name)
        response = RouteResponse(
            content=download.content,
            content_type=download.content_type,
            headers=(
                ("Content-Disposition", _download_content_disposition(download.filename)),
                ("Cache-Control", "no-store"),
            ),
        )
        return self._escape_route_response(
            plan,
            response,
            ctx=ctx,
            per_event=per_event,
            result_name="actions.Download",
        )

    def _escape_route_response(
        self,
        plan: _CallPlan,
        value: RouteResponse,
        *,
        ctx: TransportContext,
        per_event: bool,
        result_name: str,
    ) -> RouteResponse:
        """
        The ``RouteResponse`` escape hatch: per-event HTTP route only.

        The handler opts out of bundling and must run through its own HTTP
        route. State cannot change because this response has no result
        envelope, so no ``state`` action can carry the new State token and
        public State values to the browser.
        """
        if ctx.transport != "http" or not per_event:
            msg = (
                f"Event handler {plan.handler.name!r} on component {plan.comp_cls.__name__} returned"
                f" {result_name}, which bypasses the result envelope and is only available on the"
                f" per-event HTTP route (the e/{{class_id}}/{{event}} URL). Batch calls and non-HTTP"
                f" transports must return actions. Mark response handlers with @event(bundle=False)"
                f" and call their per-event URL."
            )
            raise ValueError(msg)
        options = event_options(plan.handler.func)
        if options is None or options.bundle:
            msg = (
                f"Event handler {plan.handler.name!r} on component {plan.comp_cls.__name__} returned"
                f" {result_name} but is eligible for bundled requests. Mark it with"
                " @event(bundle=False) so the client always sends it through its per-event HTTP route."
            )
            raise ValueError(msg)
        if self._state_changed(plan):
            msg = (
                f"Event handler {plan.handler.name!r} on component {plan.comp_cls.__name__} mutated"
                f" State while returning {result_name}. Raw responses bypass the state-token"
                " refresh, so response handlers must leave State unchanged."
            )
            raise ValueError(msg)
        return value

    def _complete_call(
        self,
        plan: _CallPlan,
        ctx: TransportContext,
        actions: list[Any],
        capabilities: dict[str, frozenset[str]],
        token_sent_to: set[str],
    ) -> dict[str, Any]:
        """Encode, apply capabilities, emit ``on_event_result``, re-sign state, echo send_sequence."""
        if ctx.response_mode == "compat":
            capabilities = {name: frozenset(values) for name, values in CAPABILITIES_BASELINE_V1.items()}
        # Checked before encoding too, so a render the handler may not return
        # is never built, which could already write server-stored State.
        if _is_detached(plan.handler) and any(isinstance(action, Render) for action in actions):
            raise ValueError(_detached_render_message(plan))
        # A model State is validated once before anything signs or stores it,
        # so a wrong value fails this call (500) instead of the next one (409).
        # An unchanged State was validated when it was restored.
        if plan.state is not None and self._state_changed(plan):
            problem = check_changed_state(plan.state)
            if problem is not None:
                field, detail = problem
                where = f" field {field!r}" if field is not None else ""
                if detail == TOO_DEEP_TO_SIGN:
                    advice = " Keep State nested fewer levels deep."
                elif "does not read back" in detail:
                    advice = " Remove the field's serializer, or use a type whose JSON reads back as the same value."
                else:
                    advice = " Assign a value of the field's declared type."
                msg = (
                    f"Event handler {plan.handler.name!r} on component {plan.comp_cls.__name__} left State{where}"
                    f" with a value Citry cannot sign: {detail}.{advice}"
                )
                raise ValueError(msg)
        try:
            advertised_renderers = capabilities["renderers"]
            if ctx.response_mode == "compat":
                renderer = HTML_RENDER_ENCODER.renderer
            elif self._preferred_renderer in advertised_renderers:
                renderer = self._preferred_renderer
            else:
                renderer = next(
                    (name for name in self._render_encoders if name in advertised_renderers),
                    self._preferred_renderer,
                )
            if any(isinstance(action, Render) for action in actions) and renderer not in advertised_renderers:
                raise ValueError(
                    f"Event handler {plan.handler.name!r} produced a render, but no configured renderer"
                    " was advertised by the client."
                )
            # Asked only when Citry itself renders a component for this call: a
            # render the handler built already carries its own inputs, and a call
            # without a render needs none. The function runs after the handler,
            # so after the CSRF and State token checks too, and after the renderer
            # check above, so a call that fails anyway never asks.
            if any(isinstance(action, Render) and isinstance(action.element, CitryElement) for action in actions):
                render_globals, render_provides = _call_render_inputs(plan)
            else:
                render_globals, render_provides = None, None
            encoder = self._render_encoders[renderer]
            encoded = encode_actions(
                actions,
                instance_id=plan.instance_id,
                handler=plan.handler.name,
                render_encoder=encoder,
                render_context=RenderEncodingContext(
                    citry=ctx.citry,
                    caller_render_id=plan.instance_id,
                    handler=plan.handler,
                    transport=ctx.transport,
                    renderer=renderer,
                    headers=dict(ctx.headers),
                    response_mode=ctx.response_mode,
                    # Asked only when the answer is HTML with a Render in it, so a nonce
                    # function that cannot answer for some request never fails a call
                    # that needs no nonce.
                    csp_nonce=_page_csp_nonce(ctx, plan)
                    if renderer == HTML_RENDER_ENCODER.renderer and any(isinstance(a, Render) for a in actions)
                    else None,
                    template_globals=render_globals,
                    provides=render_provides,
                ),
            )
        except ProtocolValueError:
            return build_error_result(build_error(500, "handler_error", _MSG_UNENCODABLE_RESULT), plan.send_sequence)
        encoded = self._apply_capabilities(encoded, capabilities, handler=plan.handler.name)

        has_result_hooks = bool(ctx.citry.extensions._extensions_with_hook("on_event_result"))
        if has_result_hooks:
            result_ctx = OnEventResultContext(
                citry=ctx.citry,
                component_class=plan.comp_cls,
                handler=plan.handler,
                events=plan.events,
                actions=encoded,
            )
            # Each extension's return is checked before the next one runs, so
            # a value that is not a list of actions is reported against the
            # extension that returned it. A tuple or other iterable becomes a
            # list here.
            final_actions = ctx.citry.extensions._thread_checked(
                "on_event_result",
                result_ctx,
                field="actions",
                normalize=_as_list_of_items,
                target=f"event handler {plan.handler.name!r} of {plan.comp_cls.__name__}",
                hint="which is not a list. Return the new actions as a list, or None to keep them.",
            )
            try:
                final_actions = self._validate_hook_actions(final_actions, handler=plan.handler.name)
            except ProtocolValueError:
                return build_error_result(
                    build_error(500, "handler_error", _MSG_UNENCODABLE_RESULT), plan.send_sequence
                )
        else:
            final_actions = encoded
        # Checked after the hooks, so an extension cannot add what the
        # handler itself may not return.
        self._check_detached_result(plan, final_actions)
        try:
            final_actions = self._resign_state(plan, ctx, final_actions, capabilities, token_sent_to)
        except ProtocolValueError:
            # A public State value the browser cannot read (such as an integer wider
            # than a browser number) is a result encoding failure, not a handler bug.
            return build_error_result(build_error(500, "handler_error", _MSG_UNENCODABLE_RESULT), plan.send_sequence)
        final_actions = self._apply_capabilities(final_actions, capabilities, handler=plan.handler.name)
        token_sent_to.update(_instances_given_a_token(final_actions))

        if _debug_enabled() and plan.state is not None and self._state_changed(plan):
            kinds = {action.get("action") for action in final_actions}
            if not (kinds & _VISIBLE_KINDS):
                # Only a `state` action that reached the response updates `$state`.
                refreshed = (
                    " The browser receives the new public State for `$state` and State bindings,"
                    " but server-rendered content stays as it was."
                    if "state" in kinds
                    else ""
                )
                logger.debug(
                    f"Event handler {plan.handler.name!r} on component {plan.comp_cls.__name__} mutated"
                    f" state but returned nothing visible (no render, data, dispatch, redirect, or URL"
                    f" action).{refreshed} If the page should change, return a rendering,"
                    f" e.g. 'return state.render()'."
                )

        try:
            result = (
                assemble_validated_ok_result(final_actions, plan.send_sequence)
                if has_result_hooks
                else assemble_owned_ok_result(final_actions, plan.send_sequence)
            )
        except ProtocolValueError:
            return build_error_result(build_error(500, "handler_error", _MSG_UNENCODABLE_RESULT), plan.send_sequence)
        return result

    @staticmethod
    def _validate_hook_actions(actions: list[Any], *, handler: str) -> list[dict[str, Any]]:
        """Require ``on_event_result`` replacements to have valid v1 action structure."""
        validated: list[dict[str, Any]] = []
        data_count = 0
        for index, action in enumerate(actions):
            if not isinstance(action, Mapping):
                msg = (
                    f"The on_event_result hook for event handler {handler!r} returned item {index}"
                    " as something other than a wire action object."
                )
                raise ValueError(msg)  # noqa: TRY004 - one failure type for malformed hook results
            encoded = dict(action)
            issue = validate_action(encoded)
            if issue is not None:
                if issue.category == "strict_json":
                    raise ProtocolValueError(issue)
                msg = (
                    f"The on_event_result hook for event handler {handler!r} returned item {index}"
                    f" with an invalid wire action: {issue.message}"
                )
                raise ValueError(msg)
            if encoded["action"] == "data":
                data_count += 1
            validated.append(encoded)

        if data_count > 1:
            msg = (
                f"The on_event_result hook for event handler {handler!r} returned {data_count} data actions;"
                " each result may carry at most one."
            )
            raise ValueError(msg)
        return validated

    def _check_detached_result(self, plan: _CallPlan, wire_actions: list[dict[str, Any]]) -> None:
        """
        Fail the call when a detached handler renders or changes State.

        The browser may send a detached call while the app's queued calls are
        still in flight. A render would be built on a page that a queued call
        may already have replaced, and a new State token could overwrite the
        token a queued call returned, or be overwritten by it.
        """
        if not _is_detached(plan.handler):
            return
        kinds = {action.get("action") for action in wire_actions}
        label = f"Event handler {plan.handler.name!r} on component {plan.comp_cls.__name__}"
        # The handler's own renders were refused before encoding, and handler
        # code cannot build a state action, so an on_event_result extension
        # added whatever is found here.
        for kind in ("render", "state"):
            if kind in kinds:
                msg = (
                    f"{label} is declared with @event(detached=True), but its result holds a {kind!r}"
                    f" action, which an on_event_result extension added. Change that extension to leave"
                    f" a detached handler's result without a {kind!r} action."
                )
                raise ValueError(msg)
        if self._state_changed(plan):
            msg = (
                f"Event handler {plan.handler.name!r} on component {plan.comp_cls.__name__} is declared with"
                f" @event(detached=True) but changed State. A detached handler may read State but not change"
                f" it; remove detached=True to change State."
            )
            raise ValueError(msg)

    def _state_changed(self, plan: _CallPlan) -> bool:
        """Whether the call's State differs from what the verified token carried."""
        if plan.state is None:
            return False
        return _state_fingerprint(plan.state) != plan.state_fingerprint

    def _resign_state(
        self,
        plan: _CallPlan,
        ctx: TransportContext,
        wire_actions: list[dict[str, Any]],
        capabilities: dict[str, frozenset[str]],
        token_sent_to: set[str],
    ) -> list[dict[str, Any]]:
        """
        Changed State means a fresh token and fresh public values in the response (design 4.3).

        A render that re-renders the calling instance needs no companion (the
        fresh fragment's manifest carries the new token and values); otherwise
        a ``state`` action is placed before the handler's own actions. The
        placement breaks no ordering promise: the action is server-added, and
        the client applies a result's State refresh before the actions array
        either way.

        A token past half its lifetime gets the same ``state`` action with
        unchanged State, so a component that keeps getting calls never
        reaches the expiry (design 7.1). ``_renewal_wanted`` and ``_renew_state`` skip it
        wherever it could do harm or nobody would store it.
        """
        if plan.state is None:
            return wire_actions
        if not self._state_changed(plan):
            if not self._renewal_wanted(plan, token_sent_to):
                return wire_actions
            return self._renew_state(plan, ctx, wire_actions, capabilities)
        if plan.instance_id is not None:
            self_target = f"render:{plan.instance_id}"
            if any(
                action.get("action") == "render" and action.get("target") == self_target for action in wire_actions
            ):
                return wire_actions
        meta = plan.info.state_meta
        if meta is None:  # pragma: no cover - a state instance implies its meta
            return wire_actions
        # Both checks below come before the token is made: for server storage,
        # making one writes a cache entry, and an entry no client receives is
        # never read, so it would only fill the cache.
        if plan.instance_id is None:
            # No instance, no client registry entry to refresh; the caller is
            # an API client or a plain form (design 4.2).
            logger.debug(
                f"Event handler {plan.handler.name!r} mutated state, but the call carries no"
                f" instance to address the token refresh to; the response omits it."
            )
            return wire_actions
        if "state" not in capabilities["actions"]:
            # The client explicitly advertised a set without the state kind;
            # emitting one anyway would violate the capability contract.
            logger.warning(
                f"Event handler {plan.handler.name!r} mutated state, but the client's advertised"
                f" capabilities exclude the 'state' action; the State refresh is dropped."
            )
            return wire_actions
        token = mint_state_token(
            plan.state,
            class_id=plan.comp_cls.class_id,
            secret=ctx.citry.settings.secret,
            max_age=meta.max_age,
            max_bytes=meta.max_bytes,
            storage=meta.storage,
            cache=ctx.citry.cache,
            component_name=plan.comp_cls.__name__,
        )
        # The browser shows public State through `$state` and State bindings, and
        # nothing else will refresh them: the caller is not rendered again here.
        state_action = build_state_action(plan.instance_id, token, public_state_values(plan.state, meta))
        return [state_action, *wire_actions]

    @staticmethod
    def _renewal_wanted(plan: _CallPlan, token_sent_to: set[str]) -> bool:
        """Whether a call whose State did not change should still send a new token."""
        if not plan.renew_state or plan.instance_id is None:
            # A young token needs nothing, and a call without a caller
            # instance (an API client or a plain form) has nowhere to store one.
            return False
        if _is_detached(plan.handler):
            # The browser may send a detached call while queued calls are in
            # flight, so its token could replace the newer one a queued call
            # returns. A later call that is not detached renews instead.
            return False
        # An earlier call in this request may already have sent this caller a
        # token, possibly for State it changed. Renewing from this call's
        # older State would undo that change in the browser.
        return plan.instance_id not in token_sent_to

    def _renew_state(
        self,
        plan: _CallPlan,
        ctx: TransportContext,
        wire_actions: list[dict[str, Any]],
        capabilities: dict[str, frozenset[str]],
    ) -> list[dict[str, Any]]:
        """Send unchanged State with a new token, or return the result as it is when a new token cannot help."""
        meta = plan.info.state_meta
        if meta is None or plan.instance_id is None:  # pragma: no cover - checked by the caller
            return wire_actions
        self_target = f"render:{plan.instance_id}"
        if any(action.get("action") == "render" and action.get("target") == self_target for action in wire_actions):
            # A render of the caller already carries a token with a full lifetime.
            return wire_actions
        if "state" not in capabilities["actions"] or ctx.response_mode == "compat":
            # The client cannot store a token from a `state` action: it said
            # so in its capabilities, or it is a form posted without
            # JavaScript, whose answer drops the action. Its current token
            # keeps working until it expires.
            return wire_actions
        try:
            prepared = prepare_state_token(
                plan.state,
                class_id=plan.comp_cls.class_id,
                secret=ctx.citry.settings.secret,
                max_age=meta.max_age,
                max_bytes=meta.max_bytes,
                storage=meta.storage,
                component_name=plan.comp_cls.__name__,
            )
            state_action = build_state_action(plan.instance_id, prepared.token, public_state_values(plan.state, meta))
            # Written last, so a token dropped by the checks above leaves no
            # server-storage entry behind.
            commit_state_token(prepared, ctx.citry.cache)
        except Exception as err:  # noqa: BLE001 - a renewal is optional and must not fail the call
            # The handler did not change State, so the call itself succeeded.
            # A State that cannot be signed again (one over a `_max_bytes`
            # lowered since the token was made, a public value the browser
            # cannot read, or a cache that refuses the write) keeps its
            # current token until it expires rather than failing the call.
            _log_failed_renewal(plan.comp_cls, err)
            return wire_actions
        return [state_action, *wire_actions]

    @staticmethod
    def _apply_capabilities(
        wire_actions: list[dict[str, Any]],
        capabilities: dict[str, frozenset[str]],
        *,
        handler: str,
    ) -> list[dict[str, Any]]:
        """
        Never emit an action kind or swap outside the client's advertised set.

        The only allowed downgrade turns an HTML-fragment render's ``morph``
        into ``replace`` (protocol spec "Capabilities"); anything else outside
        the set is an encode-time error, because dropping or reordering actions
        is never allowed.
        """
        swaps = capabilities["swaps"]
        kinds = capabilities["actions"]
        renderers = capabilities["renderers"]
        applied: list[dict[str, Any]] = []
        for action in wire_actions:
            kind = action.get("action")
            if kind not in kinds:
                msg = (
                    f"Event handler {handler!r} produced a {kind!r} action, but the client's"
                    f" advertised capabilities do not include it; the server never emits an action"
                    f" kind outside the advertised set."
                )
                raise ValueError(msg)
            if kind == "render":
                renderer = action.get("renderer", "html-fragment/1")
                if renderer not in renderers:
                    raise ValueError(
                        f"Event handler {handler!r} produced a render with renderer {renderer!r}, which"
                        " the client did not advertise."
                    )
                swap = action.get("swap")
                if swap not in swaps:
                    # Prepared Vue content can only morph, so only an HTML
                    # fragment has a replace to fall back to.
                    if swap == "morph" and "replace" in swaps and renderer == "html-fragment/1":
                        action = {**action, "swap": "replace"}  # noqa: PLW2901 - the downgraded copy is the point
                    else:
                        msg = (
                            f"Event handler {handler!r} produced a render with swap {swap!r}, which"
                            f" the client's advertised capabilities do not include (only an HTML"
                            f" fragment's 'morph' downgrades, to 'replace')."
                        )
                        raise ValueError(msg)
            applied.append(action)
        return applied

    def _unexpected_error(
        self,
        ctx: TransportContext,
        err: BaseException,
        *,
        plan: _CallPlan | None = None,
        comp_cls: type[Component] | None = None,
        handler: EventHandler | None = None,
        events: Any = None,
        send_sequence: int | None = None,
        checking_args: bool = False,
    ) -> dict[str, Any]:
        """
        An uncaught exception: log it, fire ``on_event_error``, answer a 500.

        The wire message is the generic contract text; the exception text
        rides only in debug mode, and a traceback never rides at all
        (design 3.7). ``checking_args`` says the exception came from checking
        the call's data, so the handler never ran, and the log and the
        debug text say so.
        """
        if plan is not None:
            comp_cls = plan.comp_cls
            handler = plan.handler
            events = plan.events
            send_sequence = plan.send_sequence
        handler_label = handler.name if handler is not None else "<unresolved>"
        comp_label = comp_cls.__name__ if comp_cls is not None else "<unresolved>"
        source = "checking the data for" if checking_args else "from"
        logger.exception(f"Uncaught exception {source} event handler {handler_label!r} on component {comp_label}.")
        if _debug_enabled():
            raised = "Checking the event's data raised" if checking_args else "The event handler raised"
            message = f"{raised} an unexpected error: {type(err).__name__}: {err}"
        else:
            message = _MSG_HANDLER_ERROR
        result = build_error_result(build_error(500, "handler_error", message), send_sequence)
        error_ctx = OnEventErrorContext(
            citry=ctx.citry,
            component_class=comp_cls,
            handler=handler,
            events=events,
            error=err,
            # Observers replace by returning a result. A private copy keeps
            # the fallback pristine if one mutates its context and then
            # returns None or raises.
            result=deepcopy(result),
        )
        try:
            replaced = ctx.citry.extensions.emit("on_event_error", error_ctx, result="first")
        except Exception:  # noqa: BLE001 - an observer must not turn a handled failure into a host exception
            logger.exception(
                f"The on_event_error hook for event handler {handler_label!r} on component {comp_label} raised;"
                " the original generic handler_error response is retained."
            )
            return result
        if replaced is None:
            return result
        normalized = self._normalize_error_hook_result(replaced, send_sequence=send_sequence)
        if normalized is None:
            logger.error(
                f"The on_event_error hook for event handler {handler_label!r} on component {comp_label}"
                " returned a malformed error result; the original generic handler_error response is retained."
            )
            return result
        return normalized

    @staticmethod
    def _normalize_error_hook_result(replaced: Any, *, send_sequence: int | None) -> dict[str, Any] | None:
        """Validate an error-hook replacement and restore the answered call's exact send_sequence."""
        if not isinstance(replaced, Mapping) or replaced.get("ok") is not False:
            return None
        candidate = dict(replaced)
        if send_sequence is None:
            candidate.pop("sendSequence", None)
        else:
            candidate["sendSequence"] = send_sequence
        if validate_result(candidate) is not None:
            return None
        return build_error_result(candidate["error"], send_sequence)
