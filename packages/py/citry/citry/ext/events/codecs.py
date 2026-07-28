"""
Payload codecs of the ``events`` extension: from a request body to the one
call-envelope shape.

Clients legitimately send event calls in different request shapes: the
runtime posts envelope JSON under the protocol's own media type, an API
client posts one flat JSON object of handler fields, a plain
``<form method="post">`` sends urlencoded fields, and a GET carries its
args in the query string. A codec translates one such shape into the call
envelope of design ``docs/design/events.md`` 4.2 before the dispatcher
ever sees it, so the dispatcher speaks exactly one language. The built-ins
are keyed by content type (the design 6.2 table):

- ``application/citry-events+json`` is the envelope itself
  (:class:`EnvelopeCodec`). The vendor media type is what marks a body as
  an envelope, so classification never depends on body shape (a user
  schema could legitimately declare a field named ``calls``).
- ``application/json`` is one flat JSON object of handler fields
  (:class:`FlatJsonCodec`) on the per-event route, where the URL names the
  handler. The batch route instead takes the envelope under this type too:
  a batch body has no flat reading, so ``decode_request`` routes it to
  :class:`EnvelopeCodec` there.
- ``application/x-www-form-urlencoded`` is a classic form post
  (:class:`FormCodec`), and a GET decodes from the query string
  (``decode_query_request``); both are per-event shapes.

User codecs ride ``CitrySettings.event_payload_codecs`` and are tried
before the built-ins; a codec is a small object with a ``content_type``
string and a ``decode(body, request)`` method returning the envelope
(raise ``EventError(status=400)`` for a malformed body).

The downlink needs no codec registry: the response is always envelope JSON
for runtime calls, or HTML / a 303 in the compatibility mode (design 6.2),
which the routes module owns.

Form posts and GET query strings carry every value as a string, so the
form and query codecs build their args payload as
:class:`~citry.ext.events.schemas.StringArgs`. That marking turns on the
source-aware binding rule of design 3.3 in the schema layer: on top of the
string parsing every payload gets (``str`` to ``UUID`` / ``datetime`` /
``date`` / ``time`` / ``Decimal`` / ``Enum``), strings from these codecs
additionally bind to declared ``int`` / ``float`` / ``bool`` fields. The
JSON codecs build plain dicts instead, so JSON payloads keep the strict
rules (a string where the schema declares ``int`` is a per-field error).
"""

from __future__ import annotations

import json
import math
from contextlib import suppress
from typing import TYPE_CHECKING, Any, NamedTuple, Protocol, runtime_checkable
from urllib.parse import parse_qs

from citry.ext.events.dispatcher import PROTOCOL
from citry.ext.events.errors import EventError
from citry.ext.events.schemas import StringArgs

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from citry.util.routing import RouteRequest

__all__ = [
    "CALLER_RENDER_ID_FIELD",
    "CAPABILITIES_FIELD",
    "PROTOCOL_FIELD",
    "REQUEST_ID_FIELD",
    "SEND_SEQUENCE_FIELD",
    "STATE_TOKEN_FIELD",
    "DecodedPayload",
    "EnvelopeCodec",
    "FlatJsonCodec",
    "FormCodec",
    "PayloadCodec",
    "decode_request",
]

# The reserved field names a form post, a flat JSON post, and a GET query
# string may carry besides the handler's own args (design 6.2).
STATE_TOKEN_FIELD = "_citry_state_token"  # noqa: S105 - reserved transport field name, not a credential
CALLER_RENDER_ID_FIELD = "_citry_caller_render_id"
# Browser-triggered GET calls carry the send epoch in the query string so
# their DOM actions retain the same stale-response protection as POST calls.
SEND_SEQUENCE_FIELD = "_citry_send_sequence"
# Browser-triggered GET calls flatten the envelope into the query. These
# fields preserve the envelope metadata that controls version rejection,
# response correlation, and action/swap capability negotiation. Hand-authored
# pasteable URLs omit them and retain the fixed query-envelope defaults.
PROTOCOL_FIELD = "_citry_protocol"
REQUEST_ID_FIELD = "_citry_request_id"
CAPABILITIES_FIELD = "_citry_capabilities"

# The synthesized correlation ids of the single-call envelopes built from a
# form post, a flat JSON post, and a GET query string. These callers cannot
# mint an id, and the result schema requires a non-empty one, so the ids are
# fixed (envelopes must be deterministic).
_FORM_ENVELOPE_ID = "form"
_FLAT_ENVELOPE_ID = "flat"
_QUERY_ENVELOPE_ID = "query"

# The envelope's identifying fields: every valid call envelope carries all
# three (spec section 3), so an object with none of them has no envelope
# reading at all.
_ENVELOPE_FIELDS = ("protocol", "requestId", "calls")


@runtime_checkable
class PayloadCodec(Protocol):
    """
    What a payload codec looks like (design 6.2).

    Register instances on ``CitrySettings.event_payload_codecs``; they are
    tried before the built-ins, first match by content type wins.
    """

    content_type: str

    def decode(self, body: bytes, request: RouteRequest) -> dict[str, Any]:
        """Return the call envelope the body carries; raise ``EventError(status=400)`` when malformed."""
        ...  # pragma: no cover - protocol


class DecodedPayload(NamedTuple):
    """What decoding a request yields: the envelope, plus the raw form fields."""

    envelope: dict[str, Any]
    """The call envelope (design 4.2) the dispatcher runs."""
    form: Mapping[str, Any]
    """The parsed form fields of a form post (reserved fields included), for
    the handler's ``request.form``; empty for non-form requests."""
    needs_route_identity: bool = False
    """Whether a built-in flat/form/query codec synthesized the call and the
    per-event route must add ``componentClassId`` and ``handlerName``."""


class EnvelopeCodec:
    """
    The identity codec: the body already is the envelope. What the runtime sends.

    Claims the protocol's own media type, ``application/citry-events+json``.
    The vendor type is what marks a body as an envelope, so classification
    never depends on body shape. The batch route takes the envelope under
    plain ``application/json`` too (a batch body has no flat reading);
    [`decode_request`][citry.ext.events.codecs.decode_request] owns that
    routing.
    """

    content_type = "application/citry-events+json"

    def decode(self, body: bytes, request: RouteRequest) -> dict[str, Any]:  # noqa: ARG002 - codec protocol signature
        """Parse the JSON body; anything but a JSON object is malformed."""
        try:
            envelope = _parse_json(body)
        except ValueError as err:
            # ValueError covers malformed JSON, a non-UTF-8 body, and the
            # rejected non-standard literals alike.
            msg = "The request body is not valid JSON; the events endpoints take a citry-events/1 call envelope."
            raise EventError(msg, status=400) from err
        if not isinstance(envelope, dict):
            msg = "The request body must be a JSON object (the citry-events/1 call envelope)."
            raise EventError(msg, status=400)
        return envelope


class FlatJsonCodec:
    """
    Flat handler fields as one JSON object; the per-event route's plain JSON.

    What an external API client sends without knowing the protocol:
    ``POST {"email": "a@b.c"}`` straight to the handler's own URL. The
    object's fields become the args payload of one synthesized call, and
    the reserved ``_citry_state_token`` / ``_citry_caller_render_id`` keys
    map onto ``stateToken`` and ``callerRenderId`` exactly like the form
    codec's. The
    args stay a plain dict, so the fields bind per the strict JSON rules of
    design 3.3, never the string-transport binding.
    """

    content_type = "application/json"

    def decode(self, body: bytes, request: RouteRequest) -> dict[str, Any]:  # noqa: ARG002 - codec protocol signature
        """Build the single-call envelope a flat JSON post means."""
        try:
            payload = _parse_json(body)
        except ValueError as err:
            # ValueError covers malformed JSON, a non-UTF-8 body, and the
            # rejected non-standard literals alike.
            msg = "The request body is not valid JSON; the per-event route takes the handler's fields as one object."
            raise EventError(msg, status=400) from err
        if not isinstance(payload, dict):
            msg = "The request body must be a JSON object (the handler's fields, one key per field)."
            raise EventError(msg, status=400)
        call: dict[str, Any] = {}
        args = dict(payload)
        state = args.pop(STATE_TOKEN_FIELD, None)
        instance = args.pop(CALLER_RENDER_ID_FIELD, None)
        if isinstance(state, str) and state:
            call["stateToken"] = state
        if isinstance(instance, str) and instance:
            call["callerRenderId"] = instance
        call["args"] = args
        return {"protocol": PROTOCOL, "requestId": _FLAT_ENVELOPE_ID, "calls": [call]}


def _parse_json(body: bytes) -> Any:
    """
    Parse a JSON request body, admitting standard JSON only.

    Python's own parser also tolerates the non-standard literals
    ``Infinity`` / ``-Infinity`` / ``NaN``, and reads a number whose
    exponent overflows a float (``1e400``, valid JSON grammar) as infinity
    instead of failing. A conforming client cannot send the literals
    (``JSON.stringify`` has no spelling for the values), and the JSON
    result envelope could not carry any non-finite number back (spec
    section 2: all envelopes are JSON), so the JSON codecs reject both
    like any other malformed body: ``parse_constant`` fires exactly on
    those three literals, ``parse_float`` checks every parsed float, and
    raising in either surfaces as the ``ValueError`` the codecs already
    answer with a 400.
    """
    return json.loads(body, parse_constant=_reject_non_json_literal, parse_float=_parse_finite_float)


def _reject_non_json_literal(literal: str) -> Any:
    # json.loads calls parse_constant only for Infinity / -Infinity / NaN.
    msg = f"non-standard JSON literal {literal}"
    raise ValueError(msg)


def _parse_finite_float(raw: str) -> float:
    # json.loads calls parse_float with the raw number text. RFC 8259 leaves
    # out-of-range numbers implementation-defined, and Python overflows them
    # to inf; no JSON encoder could carry that value back.
    value = float(raw)
    if not math.isfinite(value):
        msg = f"JSON number out of range for a float: {raw}"
        raise ValueError(msg)
    return value


class FormCodec:
    """
    Classic form posts: fields become the args payload of one synthesized call.

    The reserved ``_citry_state_token`` / ``_citry_caller_render_id`` fields
    map onto the call's ``stateToken`` and ``callerRenderId``; every other
    field is an arg. A field
    sent once arrives as its string value; a repeated field arrives as the
    list of its values. The args are built as
    [`StringArgs`][citry.ext.events.schemas.StringArgs], so validation binds
    the strings to declared ``int`` / ``float`` / ``bool`` fields (the
    source-aware rule of design 3.3).
    """

    content_type = "application/x-www-form-urlencoded"

    def decode(self, body: bytes, request: RouteRequest) -> dict[str, Any]:  # noqa: ARG002 - codec protocol signature
        """Build the single-call envelope a form post means."""
        fields = parse_form_fields(body)
        call: dict[str, Any] = {}
        args = StringArgs(fields)
        state = args.pop(STATE_TOKEN_FIELD, None)
        instance = args.pop(CALLER_RENDER_ID_FIELD, None)
        if isinstance(state, str) and state:
            call["stateToken"] = state
        if isinstance(instance, str) and instance:
            call["callerRenderId"] = instance
        call["args"] = args
        return {"protocol": PROTOCOL, "requestId": _FORM_ENVELOPE_ID, "calls": [call]}


def parse_form_fields(body: bytes) -> dict[str, Any]:
    """
    The urlencoded fields of a form post, single values unwrapped.

    Raises:
        EventError: With status 400 when the body is not decodable text.

    """
    try:
        parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    except UnicodeDecodeError as err:
        msg = "The form body is not valid UTF-8."
        raise EventError(msg, status=400) from err
    return {key: values[0] if len(values) == 1 else values for key, values in parsed.items()}


def decode_query_request(request: RouteRequest, *, state_declared: bool) -> dict[str, Any]:
    """
    The GET codec: args ride as query parameters (design 6.2).

    The state token rides the ``_citry_state_token`` parameter only when the
    handler declares ``state`` in its signature; a read-only GET URL stays
    pasteable and token-free, and a stray token parameter on a stateless
    handler is simply not part of the call. ``_citry_caller_render_id`` maps
    onto the call's ``callerRenderId`` either way. Browser sends also carry
    their integer out-of-order guard as ``_citry_send_sequence``. Browser
    calls preserve the flattened envelope's protocol, request ID, and JSON capabilities
    under the other reserved ``_citry_*`` fields. The args are built as
    [`StringArgs`][citry.ext.events.schemas.StringArgs], so validation binds
    the strings to declared ``int`` / ``float`` / ``bool`` fields (the
    source-aware rule of design 3.3).

    Args:
        request: The GET request whose query string carries the call.
        state_declared: Whether the resolved handler declares ``state``.

    Returns:
        The single-call envelope the query string means.

    """
    args: dict[str, Any] = StringArgs(
        {key: values[0] if len(values) == 1 else list(values) for key, values in request.query.items()}
    )
    call: dict[str, Any] = {}
    state = args.pop(STATE_TOKEN_FIELD, None)
    instance = args.pop(CALLER_RENDER_ID_FIELD, None)
    send_sequence = args.pop(SEND_SEQUENCE_FIELD, None)
    protocol = args.pop(PROTOCOL_FIELD, PROTOCOL)
    request_id = args.pop(REQUEST_ID_FIELD, _QUERY_ENVELOPE_ID)
    capabilities = args.pop(CAPABILITIES_FIELD, None)
    if state_declared and isinstance(state, str) and state:
        call["stateToken"] = state
    if isinstance(instance, str) and instance:
        call["callerRenderId"] = instance
    if isinstance(send_sequence, str) and send_sequence:
        try:
            call["sendSequence"] = int(send_sequence)
        except ValueError:
            # Preserve an invalid authored value so the dispatcher returns
            # its ordinary protocol error rather than silently dropping it.
            call["sendSequence"] = send_sequence
    elif send_sequence is not None:
        call["sendSequence"] = send_sequence
    call["args"] = args
    envelope: dict[str, Any] = {"protocol": protocol, "requestId": request_id, "calls": [call]}
    if capabilities is not None:
        if isinstance(capabilities, str):
            with suppress(json.JSONDecodeError):
                capabilities = json.loads(capabilities)
                # An invalid value stays a string so the dispatcher's
                # ordinary envelope validation returns protocol_mismatch.
        envelope["capabilities"] = capabilities
    return envelope


def decode_request(
    request: RouteRequest,
    user_codecs: Sequence[Any] = (),
    *,
    state_declared: bool = False,
    batch: bool = False,
) -> DecodedPayload:
    """
    Decode one HTTP request into the call envelope, picking the codec.

    GET requests always decode through the query codec. Bodied requests
    match their content type (parameters like ``charset`` ignored) against
    the user codecs first (``CitrySettings.event_payload_codecs``, in
    order), then the built-ins; the first match wins. The built-in set is
    per-route (design 6.2): the per-event route takes the envelope
    (``application/citry-events+json``), flat JSON handler fields
    (``application/json``), and form posts; the batch route takes only the
    envelope, under either the vendor type or plain ``application/json``
    (a batch body has no flat reading).

    Args:
        request: The incoming request.
        user_codecs: The engine's registered payload codecs.
        state_declared: Whether the resolved handler declares ``state``
            (the GET codec's token rule); irrelevant for bodied requests.
        batch: Whether the request hit the batch route (envelope-only) or
            the per-event route (all shapes).

    Returns:
        The decoded envelope plus the form fields (for ``request.form``).

    Raises:
        EventError: From the codec for a malformed body, or with status 400
            when no codec claims the content type.

    """
    if request.method == "GET":
        return DecodedPayload(
            envelope=decode_query_request(request, state_declared=state_declared),
            form={},
            needs_route_identity=True,
        )

    base_type = request.content_type.split(";")[0].strip().lower()
    for codec in user_codecs:
        if getattr(codec, "content_type", None) == base_type:
            return DecodedPayload(
                envelope=codec.decode(request.body, request),
                form={},
                needs_route_identity=not batch,
            )
    if base_type == EnvelopeCodec.content_type:
        return DecodedPayload(envelope=EnvelopeCodec().decode(request.body, request), form={})
    if batch:
        if base_type == FlatJsonCodec.content_type:
            envelope = EnvelopeCodec().decode(request.body, request)
            _check_batch_envelope_shape(envelope)
            return DecodedPayload(envelope=envelope, form={})
        msg = (
            f"No payload codec claims the content type {request.content_type or '(none)'!r} on the"
            f" batch endpoint. It takes the citry-events/1 call envelope as"
            f" application/citry-events+json (or application/json), or a codec registered on"
            f" CitrySettings.event_payload_codecs."
        )
        raise EventError(msg, status=400)
    if base_type == FlatJsonCodec.content_type:
        return DecodedPayload(
            envelope=FlatJsonCodec().decode(request.body, request),
            form={},
            needs_route_identity=True,
        )
    if base_type == FormCodec.content_type:
        return DecodedPayload(
            envelope=FormCodec().decode(request.body, request),
            form=parse_form_fields(request.body),
            needs_route_identity=True,
        )
    msg = (
        f"No payload codec claims the content type {request.content_type or '(none)'!r}. The"
        f" per-event route takes the citry-events/1 call envelope"
        f" (application/citry-events+json), the handler's fields as one JSON object"
        f" (application/json), urlencoded form posts, or a codec registered on"
        f" CitrySettings.event_payload_codecs."
    )
    raise EventError(msg, status=400)


def _check_batch_envelope_shape(envelope: dict[str, Any]) -> None:
    """
    Point a flat-shaped JSON object on the batch route at the right shape.

    This chooses between two error messages only, never between behaviors:
    an object carrying none of the envelope's identifying fields is invalid
    either way (the dispatcher would reject it as an envelope too), so the
    pointed message costs nothing, and a valid envelope always carries the
    fields, so classification still never depends on body shape.
    """
    if any(field in envelope for field in _ENVELOPE_FIELDS):
        return
    msg = (
        "The batch endpoint takes the citry-events/1 call envelope (an object with 'protocol',"
        " 'requestId', and 'calls'), not flat handler fields. To post one handler's fields as a plain"
        " JSON object, use that event's own per-event route (ext/events/e/{class_id}/{event})."
    )
    raise EventError(msg, status=400)
