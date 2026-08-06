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
from dataclasses import dataclass, field, fields, replace
from typing import TYPE_CHECKING, Any, Literal

from citry._protocol.events import (
    CAPABILITIES_BASELINE_V1,
    PROTOCOL,
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

# The csrf_failed message is example-locked contract text; it lives next to
# the floor that raises it (csrf.py) and is shared here for the fallback path
# of a broken user policy.
from citry.ext.events.actions import Render, _download_content_disposition
from citry.ext.events.csrf import _MSG_CSRF_FAILED
from citry.ext.events.errors import EventError, wire_error
from citry.ext.events.handlers import event_options
from citry.ext.events.results import (
    coerce_result,
    encode_actions,
    extract_download_result,
    track_constructed_actions,
    warn_unreturned_actions,
)
from citry.ext.events.schemas import validate_args
from citry.ext.events.tokens import (
    InvalidStateError,
    StaleStateError,
    StateUpdateError,
    apply_state_updates,
    mint_state_token,
    verify_state_token,
)
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

# Compatibility/no-JS responses consume render HTML as the whole response
# before it reaches a client. Giving an otherwise targetless render this
# schema-valid internal target keeps on_event_result hooks on the wire shape;
# the target itself is never sent in compatibility mode.
_COMPAT_RENDER_TARGET = ":root"


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

    Attributes:
        transport: The transport's name (``"http"``, later ``"ws"``); handlers
            see it as ``event.transport``.
        citry: The engine the call dispatches against.
        host_request: The untouched host request object (Django's
            ``HttpRequest``, the ASGI scope, a WS connection); ``None`` when
            the transport has none.
        headers: A case-insensitive view of the request headers; empty when
            the transport carries none.
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

    The framework-neutral request fields (design 3.3), always populated: the
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


@dataclass(frozen=True, slots=True)
class CallEvent:
    """
    The ``event`` value injected into event handlers: metadata about one call.

    Attributes:
        name: The handler's wire name the call addressed.
        instance_id: The calling instance's render id, or ``None`` for an
            instance-less call (an API client, a hand-written form).
        transport: The transport that carried the call (``"http"``, ...).
        args: The raw, unvalidated wire args payload. Guards read this when
            they need payload values, because one guard covers handlers with
            different schemas (design 3.5).

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
    instance_id: str | None
    send_sequence: int | None
    # The on_event hook's answer, when an extension answered the call in the
    # handler's place; _NOT_ANSWERED means the handler runs.
    answered: Any


def _state_fingerprint(state: Any) -> str | None:
    """
    A comparable snapshot of a State instance's fields.

    Canonical JSON, so ``1`` and ``True`` (equal in Python, different on the
    wire) fingerprint differently. ``None`` means the fields cannot be
    serialized right now, which the caller treats as "changed" so the mint
    step gets to raise its own pointed error.
    """
    try:
        values = {state_field.name: getattr(state, state_field.name) for state_field in fields(state)}
        return json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError):
        return None


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
    resolver, say) decodes its request into the call envelope of design 4.2
    and calls [`dispatch`][citry.ext.events.EventsDispatcher.dispatch]
    (or its async twin) directly.
    """

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
            envelope: The decoded call envelope (design 4.2).
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
            The result envelope (design 4.3), or the handler's
            ``RouteResponse`` when the per-event escape hatch was used.

        """
        checked = self._check_envelope(envelope)
        if isinstance(checked, dict):
            return checked
        envelope_id, calls, capabilities = checked
        results: list[dict[str, Any]] = []
        for call in calls:
            outcome = self._run_call_sync(
                call,
                ctx,
                capabilities=capabilities,
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
        sync handlers are offloaded to a worker thread
        (``citry.util.routing.call_maybe_sync``) so they cannot block it.

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
        for call in calls:
            outcome = await self._run_call_async(
                call,
                ctx,
                capabilities=capabilities,
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
        request: EventRequest | None,
        url_component: str | None,
        url_event: str | None,
        csrf_check: Callable[[EventHandler], None] | None,
    ) -> dict[str, Any] | RouteResponse:
        """One call through the sync pipeline; see ``dispatch`` for the split."""
        plan = self._prepare_call(
            call,
            ctx,
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
            return self._complete_call(plan, ctx, actions, capabilities)
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
        request: EventRequest | None,
        url_component: str | None,
        url_event: str | None,
        csrf_check: Callable[[EventHandler], None] | None,
    ) -> dict[str, Any] | RouteResponse:
        """The async twin of ``_run_call_sync``; only the handler invocation differs."""
        plan = self._prepare_call(
            call,
            ctx,
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
            return self._complete_call(plan, ctx, actions, capabilities)
        except EventError as err:
            return build_error_result(wire_error(err), plan.send_sequence)
        except Exception as err:  # noqa: BLE001 - the dispatcher answers 500, never crashes the host
            return self._unexpected_error(ctx, err, plan=plan)

    def _prepare_call(
        self,
        call: Any,
        ctx: TransportContext,
        *,
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
        token = call.get("stateToken")
        updates = call.get("stateUpdates")
        needs_state = "state" in handler.params
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
            try:
                # A call that needs state but carries no token verifies the
                # empty string, which maps to the malformed 403 like any
                # other unreadable token.
                verified = verify_state_token(token or "", cls=comp_cls, secrets=secrets, cache=ctx.citry.cache)
            except InvalidStateError as err:
                logger.debug(err.message)
                return build_error_result(build_error(403, "invalid_state", _MSG_INVALID_STATE), send_sequence)
            except StaleStateError as err:
                logger.debug(err.message)
                return build_error_result(build_error(409, "stale_state", _MSG_STALE_STATE), send_sequence)
            try:
                state = info.state_cls(**verified.state_kwargs)
            except TypeError:
                # The token verified but its fields no longer match the State
                # class: the version-skew case (the class changed across a
                # deploy), which is the stale-token story (design 4.5).
                return build_error_result(build_error(409, "stale_state", _MSG_STALE_STATE), send_sequence)
            state_fingerprint = _state_fingerprint(state)
            if updates and info.state_meta is not None:
                try:
                    apply_state_updates(state, updates, model_fields=info.state_meta.model)
                except StateUpdateError as err:
                    return build_error_result(build_error(422, "invalid_args", err.message, err.fields), send_sequence)

        # Args validation against the handler's data schema (design 3.3, WP9).
        args = call.get("args") or {}
        data_value: Any = None
        if handler.data_schema is not None:
            validation = validate_args(handler.data_schema, args)
            if not validation.ok:
                message = f"The args for event {event_name!r} on component {comp_cls.__name__!r} did not validate."
                return build_error_result(build_error(422, "invalid_args", message, validation.fields), send_sequence)
            data_value = validation.value
        elif args:
            # A handler that declares no data takes no input; extra keys are
            # a 422 here exactly as they are on a schema (design 3.3).
            message = f"The args for event {event_name!r} on component {comp_cls.__name__!r} did not validate."
            extra = dict.fromkeys(sorted(str(key) for key in args), "Unexpected field: not declared on the schema.")
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
        route. State cannot change because this response bypasses the normal
        state-token refresh.
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
    ) -> dict[str, Any]:
        """Encode, apply capabilities, emit ``on_event_result``, re-sign state, echo send_sequence."""
        if ctx.response_mode == "compat" and plan.instance_id is None:
            actions = [
                replace(action, target=_COMPAT_RENDER_TARGET)
                if isinstance(action, Render) and action.target is None
                else action
                for action in actions
            ]
        try:
            encoded = encode_actions(actions, instance_id=plan.instance_id, handler=plan.handler.name)
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
            final_actions = ctx.citry.extensions.emit("on_event_result", result_ctx, result="map", field="actions")
            if not isinstance(final_actions, list):
                final_actions = list(final_actions)
            try:
                final_actions = self._validate_hook_actions(final_actions, handler=plan.handler.name)
            except ProtocolValueError:
                return build_error_result(
                    build_error(500, "handler_error", _MSG_UNENCODABLE_RESULT), plan.send_sequence
                )
        else:
            final_actions = encoded
        final_actions = self._resign_state(plan, ctx, final_actions, capabilities)
        final_actions = self._apply_capabilities(final_actions, capabilities, handler=plan.handler.name)

        if _debug_enabled() and plan.state is not None and self._state_changed(plan):
            kinds = {action.get("action") for action in final_actions}
            if not (kinds & _VISIBLE_KINDS):
                logger.debug(
                    f"Event handler {plan.handler.name!r} on component {plan.comp_cls.__name__} mutated"
                    f" state but returned nothing visible (no render, data, dispatch, redirect, or URL"
                    f" action). If the page should update, return a rendering, e.g. 'return state.render()'."
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
    ) -> list[dict[str, Any]]:
        """
        Changed State means a fresh token in the response (design 4.3).

        A render that re-renders the calling instance needs no companion (the
        fresh fragment's manifest carries the new token); otherwise a
        ``state`` action is placed before the handler's own actions. The
        placement breaks no ordering promise: the action is server-added, and
        the client applies a result's token refresh before the actions array
        either way.
        """
        if plan.state is None or not self._state_changed(plan):
            return wire_actions
        if plan.instance_id is not None:
            self_target = f"render:{plan.instance_id}"
            if any(
                action.get("action") == "render" and action.get("target") == self_target for action in wire_actions
            ):
                return wire_actions
        meta = plan.info.state_meta
        if meta is None:  # pragma: no cover - a state instance implies its meta
            return wire_actions
        token = mint_state_token(
            plan.state,
            class_id=plan.comp_cls.class_id,
            secret=ctx.citry.settings.secret,
            max_age=meta.max_age,
            max_bytes=meta.max_bytes,
            storage=meta.storage,
            cache=ctx.citry.cache,
        )
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
                f" capabilities exclude the 'state' action; the token refresh is dropped."
            )
            return wire_actions
        state_action = build_state_action(plan.instance_id, token)
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

        The one defined downgrade is ``morph`` to ``replace`` (protocol spec
        section 5); anything else outside the set is an encode-time error,
        because dropping or reordering actions is never allowed.
        """
        swaps = capabilities["swaps"]
        kinds = capabilities["actions"]
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
                swap = action.get("swap")
                if swap not in swaps:
                    if swap == "morph" and "replace" in swaps:
                        action = {**action, "swap": "replace"}  # noqa: PLW2901 - the downgraded copy is the point
                    else:
                        msg = (
                            f"Event handler {handler!r} produced a render with swap {swap!r}, which"
                            f" the client's advertised capabilities do not include (only 'morph'"
                            f" downgrades, to 'replace')."
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
    ) -> dict[str, Any]:
        """
        An uncaught exception: log it, fire ``on_event_error``, answer a 500.

        The wire message is the generic contract text; the exception text
        rides only in debug mode, and a traceback never rides at all
        (design 3.7).
        """
        if plan is not None:
            comp_cls = plan.comp_cls
            handler = plan.handler
            events = plan.events
            send_sequence = plan.send_sequence
        handler_label = handler.name if handler is not None else "<unresolved>"
        comp_label = comp_cls.__name__ if comp_cls is not None else "<unresolved>"
        logger.exception(f"Uncaught exception from event handler {handler_label!r} on component {comp_label}.")
        if _debug_enabled():
            message = f"The event handler raised an unexpected error: {type(err).__name__}: {err}"
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
