"""Call-envelope builders and validators for citry-events/1."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .issues import (
    ProtocolValueError,
    ValidationIssue,
    copy_json,
    first_unknown,
    is_finite_json_number,
    pointer,
    validate_strict_json,
)

PROTOCOL = "citry-events/1"
CALLS_LIMIT = 16
ACTION_KINDS = ("render", "data", "state", "event", "redirect", "url")
SWAPS = ("morph", "replace", "inner", "append", "prepend", "remove", "none")
CAPABILITIES_BASELINE_V1: dict[str, tuple[str, ...]] = {
    "swaps": ("replace", "inner", "append", "prepend", "remove", "none"),
    "actions": ACTION_KINDS,
}

_ENVELOPE_FIELDS = ("protocol", "requestId", "capabilities", "calls")
_CALL_FIELDS = (
    "componentClassId",
    "handlerName",
    "callerRenderId",
    "args",
    "stateToken",
    "stateUpdates",
    "sendSequence",
)
_RENDER_ID_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_-")


def has_envelope_identity_fields(value: Mapping[str, Any]) -> bool:
    """Whether an object carries any required call-envelope member."""
    return any(field in value for field in ("protocol", "requestId", "calls"))


@dataclass(frozen=True, slots=True)
class ValidatedCallEnvelope:
    """The fields product code needs after complete validation."""

    request_id: str
    calls: list[Any]
    capabilities: dict[str, frozenset[str]]


@dataclass(frozen=True, slots=True)
class CallEnvelopeFailure:
    """A validation issue plus any schema-permitted correlation information."""

    issue: ValidationIssue
    request_id: str | None
    calls: list[Any] | None
    slots: int
    status: int = 400
    code: str = "protocol_mismatch"


def valid_render_id(value: Any) -> bool:
    """Whether a value has the protocol's case-safe render-ID shape."""
    return isinstance(value, str) and bool(value) and all(character in _RENDER_ID_CHARS for character in value)


def call_send_sequence(call: Any) -> int | None:
    """Read a valid send counter from an otherwise untrusted call."""
    if not isinstance(call, dict) and not isinstance(call, Mapping):
        return None
    value = call.get("sendSequence")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not is_finite_json_number(value)
        or (isinstance(value, float) and not value.is_integer())
        or value < 0
    ):
        return None
    return int(value)


def validate_call(call: Any, path: str = "") -> ValidationIssue | None:
    """Return the first structural issue in one fixed call record."""
    json_issue = validate_strict_json(call, path)
    if json_issue is not None:
        return _call_bag_message(json_issue, path)
    return _validate_call_shape(call, path)


def _call_bag_message(issue: ValidationIssue, path: str) -> ValidationIssue:
    """Keep the pointed application-bag message after an outer JSON walk."""
    for field in ("args", "stateUpdates"):
        prefix = pointer(path, field)
        if issue.path == prefix or issue.path.startswith(prefix + "/"):
            return ValidationIssue(
                issue.path,
                issue.category,
                f"The call's {field!r} must contain only strict JSON values under string keys.",
            )
    return issue


def _validate_call_shape(call: Any, path: str) -> ValidationIssue | None:
    """Validate one call after its containing value passed strict JSON."""
    if not isinstance(call, dict):
        return ValidationIssue(path, "type", "Each entry of 'calls' must be a call object.")

    for required in ("componentClassId", "handlerName", "args"):
        if required not in call:
            return ValidationIssue(
                pointer(path, required),
                "required",
                f"The call is missing required field {required!r}.",
            )
    found, unknown = first_unknown(call, set(_CALL_FIELDS))
    if found:
        name = repr(unknown)
        return ValidationIssue(pointer(path, unknown), "unknown_field", f"The call carries unknown field(s): {name}.")
    for name in ("componentClassId", "handlerName"):
        value = call[name]
        if not isinstance(value, str) or not value:
            return ValidationIssue(
                pointer(path, name),
                "type" if not isinstance(value, str) else "range",
                f"The call's {name!r} must be a non-empty string.",
            )
    if "callerRenderId" in call:
        value = call["callerRenderId"]
        if not isinstance(value, str) or not value:
            return ValidationIssue(
                pointer(path, "callerRenderId"),
                "type" if not isinstance(value, str) else "range",
                "The call's 'callerRenderId' must be a non-empty string.",
            )
        if not valid_render_id(value):
            return ValidationIssue(
                pointer(path, "callerRenderId"),
                "pattern",
                "The call's 'callerRenderId' must use only lowercase ASCII letters, digits, hyphens, and underscores.",
            )
    if not isinstance(call["args"], dict):
        return ValidationIssue(pointer(path, "args"), "type", "The call's 'args' must be an object.")
    if "stateToken" in call:
        value = call["stateToken"]
        if not isinstance(value, str) or not value:
            return ValidationIssue(
                pointer(path, "stateToken"),
                "type" if not isinstance(value, str) else "range",
                "The call's 'stateToken' must be a non-empty string.",
            )
    if "stateUpdates" in call and not isinstance(call["stateUpdates"], dict):
        return ValidationIssue(pointer(path, "stateUpdates"), "type", "The call's 'stateUpdates' must be an object.")
    if "sendSequence" in call:
        value = call["sendSequence"]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ValidationIssue(
                pointer(path, "sendSequence"),
                "type",
                "The call's 'sendSequence' must be an integer of at least 0.",
            )
        if not is_finite_json_number(value):
            return ValidationIssue(
                pointer(path, "sendSequence"),
                "strict_json",
                "The call's 'sendSequence' is outside the browser JSON range.",
            )
        if isinstance(value, float) and not value.is_integer():
            return ValidationIssue(
                pointer(path, "sendSequence"),
                "type",
                "The call's 'sendSequence' must be an integer of at least 0.",
            )
        if value < 0:
            return ValidationIssue(
                pointer(path, "sendSequence"),
                "range",
                "The call's 'sendSequence' must be an integer of at least 0.",
            )
    return None


def validate_capabilities(value: Any, path: str = "/capabilities") -> ValidationIssue | None:
    """Return the first issue in the closed capability record."""
    json_issue = validate_strict_json(value, path)
    if json_issue is not None:
        return json_issue
    return _validate_capabilities_shape(value, path)


def _validate_capabilities_shape(value: Any, path: str) -> ValidationIssue | None:
    """Validate capabilities after their containing value passed strict JSON."""
    message = (
        "The envelope's 'capabilities' must contain only 'swaps' and 'actions';"
        " each value must be a duplicate-free array of known v1 names."
    )
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", message)
    found, unknown = first_unknown(value, {"swaps", "actions"})
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", message)
    for name, known in (("swaps", SWAPS), ("actions", ACTION_KINDS)):
        if name not in value:
            continue
        items = value[name]
        item_path = pointer(path, name)
        if not isinstance(items, list):
            return ValidationIssue(item_path, "type", message)
        seen: set[str] = set()
        for index, item in enumerate(items):
            if not isinstance(item, str):
                return ValidationIssue(pointer(item_path, index), "type", message)
            if item not in known:
                return ValidationIssue(pointer(item_path, index), "enum", message)
            if item in seen:
                return ValidationIssue(item_path, "semantic", message)
            seen.add(item)
    return None


def resolve_capabilities(value: Mapping[str, Any] | None = None) -> dict[str, frozenset[str]]:
    """Resolve omitted capability members to the v1 baseline."""
    raw = {} if value is None else value
    issue = validate_capabilities(raw)
    if issue is not None:
        raise ProtocolValueError(issue)
    return {
        name: frozenset(raw[name] if name in raw else CAPABILITIES_BASELINE_V1[name]) for name in ("swaps", "actions")
    }


def inspect_call_envelope(value: Any) -> ValidatedCallEnvelope | CallEnvelopeFailure:
    """Validate a complete call envelope and retain rejection correlation data."""
    json_issue = validate_strict_json(value)
    if json_issue is not None:
        raw_calls = value.get("calls") if isinstance(value, dict) else None
        calls = raw_calls if isinstance(raw_calls, list) and raw_calls else None
        if calls is not None:
            for index in range(len(calls)):
                json_issue = _call_bag_message(json_issue, f"/calls/{index}")
        raw_id = value.get("requestId") if isinstance(value, dict) else None
        request_id = raw_id if isinstance(raw_id, str) and raw_id else None
        return CallEnvelopeFailure(
            json_issue,
            request_id,
            calls,
            len(calls) if calls is not None else 1,
        )
    if not isinstance(value, dict):
        return CallEnvelopeFailure(
            ValidationIssue("", "type", "The request body is not a call envelope object."),
            None,
            None,
            1,
        )

    raw_calls = value.get("calls")
    calls = raw_calls if isinstance(raw_calls, list) and raw_calls else None
    slots = len(calls) if calls is not None else 1
    raw_id = value.get("requestId")
    request_id = raw_id if isinstance(raw_id, str) and raw_id else None

    if "protocol" not in value:
        message = f"The envelope names no protocol; this server speaks {PROTOCOL!r}."
        return CallEnvelopeFailure(ValidationIssue("/protocol", "required", message), request_id, calls, slots)
    if "requestId" not in value:
        message = "The envelope carries no 'requestId' string."
        return CallEnvelopeFailure(ValidationIssue("/requestId", "required", message), None, calls, slots)
    if "calls" not in value:
        message = "The envelope carries no calls; 'calls' must be an array of 1 to 16 call objects."
        return CallEnvelopeFailure(ValidationIssue("/calls", "required", message), request_id, None, 1)
    found, unknown = first_unknown(value, set(_ENVELOPE_FIELDS))
    if found:
        message = f"The envelope carries unknown field(s): {unknown!r}."
        return CallEnvelopeFailure(
            ValidationIssue(pointer("", unknown), "unknown_field", message), request_id, calls, slots
        )
    protocol = value["protocol"]
    if protocol != PROTOCOL:
        if isinstance(protocol, str):
            message = f"Unknown protocol {protocol!r}; this server speaks {PROTOCOL!r}."
            category = "enum"
        else:
            message = f"The envelope names no protocol; this server speaks {PROTOCOL!r}."
            category = "type"
        return CallEnvelopeFailure(ValidationIssue("/protocol", category, message), request_id, calls, slots)
    if not isinstance(raw_id, str) or not raw_id:
        message = "The envelope carries no 'requestId' string."
        category = "type" if not isinstance(raw_id, str) else "range"
        return CallEnvelopeFailure(ValidationIssue("/requestId", category, message), None, calls, slots)
    if "capabilities" in value:
        issue = _validate_capabilities_shape(value["capabilities"], "/capabilities")
        if issue is not None:
            return CallEnvelopeFailure(issue, request_id, calls, slots)
        raw_capabilities = value["capabilities"]
        capabilities = {
            name: frozenset(raw_capabilities[name] if name in raw_capabilities else CAPABILITIES_BASELINE_V1[name])
            for name in ("swaps", "actions")
        }
    else:
        capabilities = {name: frozenset(values) for name, values in CAPABILITIES_BASELINE_V1.items()}

    if not isinstance(raw_calls, list):
        message = "The envelope carries no calls; 'calls' must be an array of 1 to 16 call objects."
        return CallEnvelopeFailure(ValidationIssue("/calls", "type", message), request_id, None, 1)
    if not raw_calls:
        message = "The envelope carries no calls; 'calls' must be an array of 1 to 16 call objects."
        return CallEnvelopeFailure(ValidationIssue("/calls", "range", message), request_id, None, 1)
    if len(raw_calls) > CALLS_LIMIT:
        message = f"The envelope carries {len(raw_calls)} calls; the cap is {CALLS_LIMIT}."
        return CallEnvelopeFailure(
            ValidationIssue("/calls", "range", message),
            request_id,
            raw_calls,
            len(raw_calls),
            status=413,
            code="payload_too_large",
        )

    for index, call in enumerate(raw_calls):
        issue = _validate_call_shape(call, f"/calls/{index}")
        if issue is not None:
            return CallEnvelopeFailure(issue, request_id, raw_calls, len(raw_calls))
    return ValidatedCallEnvelope(raw_id, raw_calls, capabilities)


def validate_call_envelope(value: Any) -> ValidationIssue | None:
    """Return the first issue in a complete call envelope."""
    inspected = inspect_call_envelope(value)
    return inspected.issue if isinstance(inspected, CallEnvelopeFailure) else None


def build_call(
    component_class_id: str,
    handler_name: str,
    args: Mapping[str, Any],
    *,
    caller_render_id: str | None = None,
    state_token: str | None = None,
    state_updates: Mapping[str, Any] | None = None,
    send_sequence: int | None = None,
) -> dict[str, Any]:
    """Build one fresh, validated call record."""
    call: dict[str, Any] = {
        "componentClassId": component_class_id,
        "handlerName": handler_name,
        "args": copy_json(dict(args)),
    }
    if caller_render_id is not None:
        call["callerRenderId"] = caller_render_id
    if state_token is not None:
        call["stateToken"] = state_token
    if state_updates is not None:
        call["stateUpdates"] = copy_json(dict(state_updates))
    if send_sequence is not None:
        call["sendSequence"] = send_sequence
    issue = validate_call(call)
    if issue is not None:
        raise ProtocolValueError(issue)
    return call


def build_call_envelope(
    request_id: str,
    calls: list[Mapping[str, Any]],
    *,
    capabilities: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one fresh, validated call envelope."""
    envelope: dict[str, Any] = {
        "protocol": PROTOCOL,
        "requestId": request_id,
        "calls": [copy_json(dict(call)) for call in calls],
    }
    if capabilities is not None:
        envelope["capabilities"] = copy_json(dict(capabilities))
    issue = validate_call_envelope(envelope)
    if issue is not None:
        raise ProtocolValueError(issue)
    return envelope
