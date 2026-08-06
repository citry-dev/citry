"""Reserved transport-carrier names and pure field conversion."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .calls import PROTOCOL
from .issues import loads_strict_json

if TYPE_CHECKING:
    from collections.abc import Mapping

STATE_TOKEN_FIELD = "_citry_state_token"  # noqa: S105 - reserved field name, not a credential
CALLER_RENDER_ID_FIELD = "_citry_caller_render_id"
SEND_SEQUENCE_FIELD = "_citry_send_sequence"
PROTOCOL_FIELD = "_citry_protocol"
REQUEST_ID_FIELD = "_citry_request_id"
CAPABILITIES_FIELD = "_citry_capabilities"

FORM_REQUEST_ID = "form"
FLAT_REQUEST_ID = "flat"
QUERY_REQUEST_ID = "query"
_ABSENT = object()


@dataclass(frozen=True, slots=True)
class CarrierFields:
    """Protocol fields recovered from an already-decoded query multimap."""

    protocol: Any
    request_id: Any
    capabilities: Any
    call: dict[str, Any]


def build_partial_call_envelope(
    request_id: Any,
    call: Mapping[str, Any],
    *,
    protocol: Any = PROTOCOL,
    capabilities: Any = _ABSENT,
) -> dict[str, Any]:
    """Build the partial envelope completed by a per-event route's URL identity."""
    envelope: dict[str, Any] = {"protocol": protocol, "requestId": request_id, "calls": [dict(call)]}
    if capabilities is not _ABSENT:
        envelope["capabilities"] = capabilities
    return envelope


def build_query_envelope(fields: CarrierFields) -> dict[str, Any]:
    """Build the partial envelope represented by converted query fields."""
    return build_partial_call_envelope(
        fields.request_id,
        fields.call,
        protocol=fields.protocol,
        capabilities=fields.capabilities if fields.capabilities is not None else _ABSENT,
    )


def add_route_identity(envelope: Mapping[str, Any], component_class_id: str, handler_name: str) -> dict[str, Any]:
    """Complete synthesized calls with the target named by their per-event URL."""
    calls = envelope.get("calls")
    completed = (
        [
            {"componentClassId": component_class_id, "handlerName": handler_name, **call}
            if isinstance(call, dict)
            else call
            for call in calls
        ]
        if isinstance(calls, list)
        else calls
    )
    return {**envelope, "calls": completed}


def split_flat_fields(fields: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split flat JSON or form fields into open args and optional call metadata."""
    args = dict(fields)
    call: dict[str, Any] = {}
    state = args.pop(STATE_TOKEN_FIELD, None)
    caller = args.pop(CALLER_RENDER_ID_FIELD, None)
    if isinstance(state, str) and state:
        call["stateToken"] = state
    if isinstance(caller, str) and caller:
        call["callerRenderId"] = caller
    return args, call


def split_query_fields(fields: Mapping[str, Any], *, state_declared: bool) -> CarrierFields:
    """Convert decoded query values into envelope metadata and call fields."""
    args = dict(fields)
    call: dict[str, Any] = {}
    state = args.pop(STATE_TOKEN_FIELD, None)
    caller = args.pop(CALLER_RENDER_ID_FIELD, None)
    send_sequence = args.pop(SEND_SEQUENCE_FIELD, None)
    protocol = args.pop(PROTOCOL_FIELD, PROTOCOL)
    request_id = args.pop(REQUEST_ID_FIELD, QUERY_REQUEST_ID)
    capabilities = args.pop(CAPABILITIES_FIELD, None)

    if state_declared and isinstance(state, str) and state:
        call["stateToken"] = state
    if isinstance(caller, str) and caller:
        call["callerRenderId"] = caller
    if isinstance(send_sequence, str) and send_sequence:
        try:
            call["sendSequence"] = int(send_sequence)
        except ValueError:
            call["sendSequence"] = send_sequence
    elif send_sequence is not None:
        call["sendSequence"] = send_sequence
    if isinstance(capabilities, str):
        with suppress(ValueError):
            capabilities = loads_strict_json(capabilities)
    call["args"] = args
    return CarrierFields(protocol, request_id, capabilities, call)
