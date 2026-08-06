"""Result, error, and action helpers for citry-events/1."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .calls import ACTION_KINDS, CAPABILITIES_BASELINE_V1, PROTOCOL, SWAPS, call_send_sequence, valid_render_id
from .issues import (
    ProtocolValueError,
    ValidationIssue,
    _copy_json_unchecked,
    copy_json,
    first_unknown,
    is_finite_json_number,
    pointer,
    validate_strict_json,
)

ERROR_STATUS_BY_CODE: dict[str, int] = {
    "invalid_args": 422,
    "invalid_state": 403,
    "stale_state": 409,
    "unknown_event": 404,
    "unknown_component": 404,
    "forbidden": 403,
    "not_found": 404,
    "conflict": 409,
    "csrf_failed": 403,
    "payload_too_large": 413,
    "protocol_mismatch": 400,
    "handler_error": 500,
}
ERROR_CODES = (*ERROR_STATUS_BY_CODE, "error")

_RESULT_ENVELOPE_FIELDS = ("protocol", "requestId", "results")
_OK_RESULT_FIELDS = ("ok", "sendSequence", "actions")
_ERROR_RESULT_FIELDS = ("ok", "sendSequence", "error")
_ERROR_FIELDS = ("status", "code", "message", "fieldErrors")
_ACTION_FIELDS: dict[str, tuple[str, ...]] = {
    "render": ("action", "target", "swap", "html", "delay", "wait"),
    "data": ("action", "value", "delay"),
    "state": ("action", "targetRenderId", "stateToken", "delay", "wait"),
    "event": ("action", "eventName", "detail", "target", "delay", "wait"),
    "redirect": ("action", "url", "delay", "wait"),
    "url": ("action", "url", "mode", "delay", "wait"),
}
_ACTION_REQUIRED: dict[str, tuple[str, ...]] = {
    "render": ("action", "target", "swap", "html"),
    "data": ("action", "value"),
    "state": ("action", "targetRenderId", "stateToken"),
    "event": ("action", "eventName"),
    "redirect": ("action", "url"),
    "url": ("action", "url", "mode"),
}


def openapi_error_schema() -> dict[str, Any]:
    """Return the protocol-owned OpenAPI shape for one event error."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {"type": "integer"},
            "code": {"type": "string"},
            "message": {"type": "string"},
            "fieldErrors": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": "One message per failed field, keyed by the data-schema field path.",
            },
        },
        "required": ["status", "code", "message"],
    }


def openapi_error_envelope_schema(error_reference: str) -> dict[str, Any]:
    """Return the per-event route's failed result-envelope OpenAPI shape."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "protocol": {"const": PROTOCOL},
            "requestId": {"type": "string"},
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "ok": {"const": False},
                        "sendSequence": {"type": "integer", "minimum": 0},
                        "error": {"$ref": error_reference},
                    },
                    "required": ["ok", "error"],
                },
            },
        },
        "required": ["protocol", "requestId", "results"],
    }


def build_error(
    status: int,
    code: str,
    message: str,
    field_errors: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build one fresh error object."""
    error: dict[str, Any] = {"status": status, "code": code, "message": message}
    if field_errors:
        error["fieldErrors"] = copy_json(dict(field_errors))
    issue = _validate_error_shape(error, "")
    if issue is not None:
        raise ProtocolValueError(issue)
    return error


def build_error_result(error: Mapping[str, Any], send_sequence: int | None = None) -> dict[str, Any]:
    """Build one failure result and optionally echo its call counter."""
    result: dict[str, Any] = {"ok": False}
    if send_sequence is not None:
        result["sendSequence"] = send_sequence
    result["error"] = copy_json(dict(error))
    issue = _validate_result_shape(result, "")
    if issue is not None:
        raise ProtocolValueError(issue)
    return result


def build_ok_result(actions: Sequence[Mapping[str, Any]], send_sequence: int | None = None) -> dict[str, Any]:
    """Build one successful result from already normalized wire actions."""
    result: dict[str, Any] = {"ok": True}
    if send_sequence is not None:
        result["sendSequence"] = send_sequence
    result["actions"] = copy_json([dict(action) for action in actions])
    issue = _validate_result_shape(result, "")
    if issue is not None:
        raise ProtocolValueError(issue)
    return result


def assemble_validated_ok_result(
    actions: Sequence[Mapping[str, Any]], send_sequence: int | None = None
) -> dict[str, Any]:
    """Assemble a result after each action has passed protocol validation."""
    if send_sequence is not None:
        issue = _send_sequence_issue(send_sequence, "/sendSequence")
        if issue is not None:
            raise ProtocolValueError(issue)
    result: dict[str, Any] = {"ok": True}
    if send_sequence is not None:
        result["sendSequence"] = send_sequence
    result["actions"] = list(actions)
    return _copy_json_unchecked(result)


def assemble_owned_ok_result(actions: list[dict[str, Any]], send_sequence: int | None = None) -> dict[str, Any]:
    """Wrap action records already freshly owned by the protocol layer."""
    if send_sequence is not None:
        issue = _send_sequence_issue(send_sequence, "/sendSequence")
        if issue is not None:
            raise ProtocolValueError(issue)
    result: dict[str, Any] = {"ok": True}
    if send_sequence is not None:
        result["sendSequence"] = send_sequence
    result["actions"] = actions
    return result


def build_result_envelope(request_id: str, results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build a normal result envelope at the final serialization boundary."""
    envelope = {
        "protocol": PROTOCOL,
        "requestId": request_id,
        "results": copy_json([dict(result) for result in results]),
    }
    issue = _validate_result_envelope_shape(envelope, "")
    if issue is not None:
        raise ProtocolValueError(issue)
    return envelope


def finalize_owned_result_envelope(request_id: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate and wrap result records already freshly owned by the protocol layer."""
    envelope = {"protocol": PROTOCOL, "requestId": request_id, "results": results}
    issue = _validate_result_envelope_shape(envelope, "")
    if issue is not None:
        raise ProtocolValueError(issue)
    return envelope


def build_edge_error_envelope(status: int, code: str, message: str) -> dict[str, Any]:
    """Build the single transport-edge error that has no request ID."""
    envelope = {
        "protocol": PROTOCOL,
        "requestId": None,
        "results": [build_error_result(build_error(status, code, message))],
    }
    issue = validate_result_envelope(envelope)
    if issue is not None:
        raise ProtocolValueError(issue)
    return envelope


def build_rejected_call_envelope(
    raw_envelope: Any,
    *,
    status: int,
    code: str,
    message: str,
) -> dict[str, Any]:
    """Build a rejection, correlating call slots only when a request ID permits it."""
    request_id: str | None = None
    calls: list[Any] | None = None
    if isinstance(raw_envelope, Mapping):
        raw_id = raw_envelope.get("requestId")
        if isinstance(raw_id, str) and raw_id:
            request_id = raw_id
        if request_id is None:
            return build_edge_error_envelope(status, code, message)
        raw_calls = raw_envelope.get("calls")
        if isinstance(raw_calls, list) and raw_calls:
            calls = raw_calls
    slot_calls = calls if calls is not None else [None]
    error = build_error(status, code, message)
    results = [build_error_result(error, call_send_sequence(call)) for call in slot_calls]
    return {"protocol": PROTOCOL, "requestId": request_id, "results": results}


def _validate_timing(action: Mapping[str, Any], path: str) -> ValidationIssue | None:
    if "delay" in action:
        delay = action["delay"]
        if isinstance(delay, bool) or not isinstance(delay, (int, float)):
            return ValidationIssue(pointer(path, "delay"), "type", "The action delay must be a finite number.")
        if not is_finite_json_number(delay):
            return ValidationIssue(pointer(path, "delay"), "strict_json", "The action delay must be finite.")
        if delay < 0:
            return ValidationIssue(pointer(path, "delay"), "range", "The action delay must be at least 0.")
    if "wait" in action and action["wait"] is not False:
        return ValidationIssue(pointer(path, "wait"), "enum", "The action wait flag, when present, must be false.")
    return None


def _validate_target(value: Any, path: str) -> ValidationIssue | None:
    if not isinstance(value, str):
        return ValidationIssue(path, "type", "An action target must be a non-empty string.")
    if not value:
        return ValidationIssue(path, "range", "An action target must be a non-empty string.")
    if value.startswith("render:") and not valid_render_id(value[7:]):
        return ValidationIssue(path, "pattern", "A render target must contain a valid render ID.")
    return None


def validate_action(value: Any, path: str = "") -> ValidationIssue | None:
    """Return the first issue in one discriminated action record."""
    json_issue = validate_strict_json(value, path)
    if json_issue is not None:
        return json_issue
    return _validate_action_shape(value, path)


def _validate_action_shape(value: Any, path: str) -> ValidationIssue | None:
    """Validate one action after its containing value passed strict JSON."""
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", "An action must be an object.")
    if "action" not in value:
        return ValidationIssue(pointer(path, "action"), "required", "The action kind is required.")
    kind = value["action"]
    if not isinstance(kind, str):
        return ValidationIssue(pointer(path, "action"), "type", "The action kind must be a string.")
    if kind not in ACTION_KINDS:
        return ValidationIssue(pointer(path, "action"), "enum", f"Unknown action kind {kind!r}.")
    for required in _ACTION_REQUIRED[kind]:
        if required not in value:
            return ValidationIssue(pointer(path, required), "required", f"The {kind} action requires {required!r}.")
    found, unknown = first_unknown(value, set(_ACTION_FIELDS[kind]))
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", f"The {kind} action has an unknown field.")
    if kind == "render":
        issue = _validate_target(value["target"], pointer(path, "target"))
        if issue is not None:
            return issue
        if value["swap"] not in SWAPS:
            category = "type" if not isinstance(value["swap"], str) else "enum"
            return ValidationIssue(pointer(path, "swap"), category, "The render swap is not a v1 swap.")
        if not isinstance(value["html"], str):
            return ValidationIssue(pointer(path, "html"), "type", "The render HTML must be a string.")
    elif kind == "data":
        pass
    elif kind == "state":
        render_id = value["targetRenderId"]
        if not isinstance(render_id, str):
            return ValidationIssue(pointer(path, "targetRenderId"), "type", "The state target must be a render ID.")
        if not valid_render_id(render_id):
            return ValidationIssue(
                pointer(path, "targetRenderId"), "pattern", "The state target must be a valid render ID."
            )
        token = value["stateToken"]
        if not isinstance(token, str):
            return ValidationIssue(pointer(path, "stateToken"), "type", "The state token must be a string.")
        if not token:
            return ValidationIssue(pointer(path, "stateToken"), "range", "The state token must not be empty.")
    elif kind == "event":
        name = value["eventName"]
        if not isinstance(name, str):
            return ValidationIssue(pointer(path, "eventName"), "type", "The event name must be a string.")
        if not name:
            return ValidationIssue(pointer(path, "eventName"), "range", "The event name must not be empty.")
        if name.startswith("citry:"):
            return ValidationIssue(pointer(path, "eventName"), "pattern", "The event name is reserved.")
        if "target" in value:
            issue = _validate_target(value["target"], pointer(path, "target"))
            if issue is not None:
                return issue
    elif kind == "redirect":
        url = value["url"]
        if not isinstance(url, str):
            return ValidationIssue(pointer(path, "url"), "type", "The redirect URL must be a string.")
        if not url:
            return ValidationIssue(pointer(path, "url"), "range", "The redirect URL must not be empty.")
    else:
        url = value["url"]
        if not isinstance(url, str):
            return ValidationIssue(pointer(path, "url"), "type", "The URL action URL must be a string.")
        if not url:
            return ValidationIssue(pointer(path, "url"), "range", "The URL action URL must not be empty.")
        mode = value["mode"]
        if mode not in ("push", "replace"):
            category = "type" if not isinstance(mode, str) else "enum"
            return ValidationIssue(pointer(path, "mode"), category, "The URL action mode must be push or replace.")
    return _validate_timing(value, path)


def _with_timing(record: dict[str, Any], delay: float, wait: bool, *, allow_wait: bool = True) -> dict[str, Any]:
    if delay:
        record["delay"] = delay
    if allow_wait and not wait:
        record["wait"] = False
    issue = _validate_action_shape(record, "")
    if issue is not None:
        raise ProtocolValueError(issue)
    return record


def build_render_action(target: str, swap: str, html: str, *, delay: float = 0, wait: bool = True) -> dict[str, Any]:
    return _with_timing({"action": "render", "target": target, "swap": swap, "html": html}, delay, wait)


def build_data_action(value: Any, *, delay: float = 0) -> dict[str, Any]:
    return _with_timing({"action": "data", "value": copy_json(value)}, delay, wait=True, allow_wait=False)


def build_state_action(
    target_render_id: str, state_token: str, *, delay: float = 0, wait: bool = True
) -> dict[str, Any]:
    return _with_timing(
        {"action": "state", "targetRenderId": target_render_id, "stateToken": state_token}, delay, wait
    )


def build_event_action(
    event_name: str,
    *,
    detail: Any = None,
    include_detail: bool = False,
    target: str | None = None,
    delay: float = 0,
    wait: bool = True,
) -> dict[str, Any]:
    record: dict[str, Any] = {"action": "event", "eventName": event_name}
    if include_detail:
        record["detail"] = copy_json(detail)
    if target is not None:
        record["target"] = target
    return _with_timing(record, delay, wait)


def build_redirect_action(url: str, *, delay: float = 0, wait: bool = True) -> dict[str, Any]:
    return _with_timing({"action": "redirect", "url": url}, delay, wait)


def build_url_action(url: str, mode: str, *, delay: float = 0, wait: bool = True) -> dict[str, Any]:
    return _with_timing({"action": "url", "url": url, "mode": mode}, delay, wait)


def validate_error(value: Any, path: str = "") -> ValidationIssue | None:
    """Return the first issue in one error record."""
    json_issue = validate_strict_json(value, path)
    if json_issue is not None:
        return json_issue
    return _validate_error_shape(value, path)


def _validate_error_shape(value: Any, path: str) -> ValidationIssue | None:
    """Validate one error after its containing value passed strict JSON."""
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", "The result error must be an object.")
    for required in ("status", "code", "message"):
        if required not in value:
            return ValidationIssue(pointer(path, required), "required", f"The error requires {required!r}.")
    found, unknown = first_unknown(value, set(_ERROR_FIELDS))
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", "The error has an unknown field.")
    status = value["status"]
    if isinstance(status, bool) or not isinstance(status, (int, float)):
        return ValidationIssue(pointer(path, "status"), "type", "The error status must be an integer.")
    if isinstance(status, float) and not status.is_integer():
        return ValidationIssue(pointer(path, "status"), "type", "The error status must be an integer.")
    if not 400 <= status <= 599:
        return ValidationIssue(pointer(path, "status"), "range", "The error status must be from 400 to 599.")
    code = value["code"]
    if not isinstance(code, str):
        return ValidationIssue(pointer(path, "code"), "type", "The error code must be a string.")
    if code not in ERROR_CODES:
        return ValidationIssue(pointer(path, "code"), "enum", "The error code is not a v1 code.")
    message = value["message"]
    if not isinstance(message, str):
        return ValidationIssue(pointer(path, "message"), "type", "The error message must be a string.")
    if not message:
        return ValidationIssue(pointer(path, "message"), "range", "The error message must not be empty.")
    if "fieldErrors" in value:
        fields = value["fieldErrors"]
        if not isinstance(fields, dict):
            return ValidationIssue(pointer(path, "fieldErrors"), "type", "Field errors must be an object.")
        if any(not isinstance(name, str) for name in fields):
            return ValidationIssue(pointer(path, "fieldErrors"), "strict_json", "Field error names must be strings.")
        for name in sorted(fields):
            if not isinstance(fields[name], str):
                return ValidationIssue(
                    pointer(pointer(path, "fieldErrors"), name), "type", "Field errors map strings."
                )
    expected_status = ERROR_STATUS_BY_CODE.get(code)
    if expected_status is not None and status != expected_status:
        return ValidationIssue(pointer(path, "status"), "semantic", "The error status does not match its code.")
    return None


def _send_sequence_issue(value: Any, path: str) -> ValidationIssue | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ValidationIssue(path, "type", "The send sequence must be an integer.")
    if not is_finite_json_number(value):
        return ValidationIssue(path, "strict_json", "The send sequence is outside the browser JSON range.")
    if isinstance(value, float) and not value.is_integer():
        return ValidationIssue(path, "type", "The send sequence must be an integer.")
    if value < 0:
        return ValidationIssue(path, "range", "The send sequence must be at least 0.")
    return None


def validate_result(value: Any, path: str = "") -> ValidationIssue | None:
    """Return the first issue in one success or error result."""
    json_issue = validate_strict_json(value, path)
    if json_issue is not None:
        return json_issue
    return _validate_result_shape(value, path)


def _validate_result_shape(value: Any, path: str) -> ValidationIssue | None:
    """Validate one result after its containing value passed strict JSON."""
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", "A result must be an object.")
    if "ok" not in value:
        return ValidationIssue(pointer(path, "ok"), "required", "The result requires 'ok'.")
    ok = value["ok"]
    if not isinstance(ok, bool):
        return ValidationIssue(pointer(path, "ok"), "type", "The result's 'ok' field must be a boolean.")
    allowed = _OK_RESULT_FIELDS if ok else _ERROR_RESULT_FIELDS
    required = ("ok", "actions") if ok else ("ok", "error")
    for field in required:
        if field not in value:
            return ValidationIssue(pointer(path, field), "required", f"The result requires {field!r}.")
    found, unknown = first_unknown(value, set(allowed))
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", "The result has an unknown field.")
    if "sendSequence" in value:
        issue = _send_sequence_issue(value["sendSequence"], pointer(path, "sendSequence"))
        if issue is not None:
            return issue
    if not ok:
        return _validate_error_shape(value["error"], pointer(path, "error"))
    actions = value["actions"]
    if not isinstance(actions, list):
        return ValidationIssue(pointer(path, "actions"), "type", "The result actions must be an array.")
    for index, action in enumerate(actions):
        issue = _validate_action_shape(action, "")
        if issue is not None:
            return ValidationIssue(
                pointer(pointer(path, "actions"), index) + issue.path,
                issue.category,
                issue.message,
            )
    if sum(action["action"] == "data" for action in actions) > 1:
        return ValidationIssue(pointer(path, "actions"), "semantic", "Each result may carry at most one data action.")
    return None


def validate_result_envelope(value: Any, path: str = "") -> ValidationIssue | None:
    """Return the first structural issue in one complete result envelope."""
    json_issue = validate_strict_json(value, path)
    if json_issue is not None:
        return json_issue
    return _validate_result_envelope_shape(value, path)


def _validate_result_envelope_shape(value: Any, path: str) -> ValidationIssue | None:
    """Validate one envelope after the complete value passed strict JSON."""
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", "The result envelope must be an object.")
    for required in ("protocol", "requestId", "results"):
        if required not in value:
            return ValidationIssue(pointer(path, required), "required", f"The result envelope requires {required!r}.")
    found, unknown = first_unknown(value, set(_RESULT_ENVELOPE_FIELDS))
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", "The result envelope has an unknown field.")
    if value["protocol"] != PROTOCOL:
        category = "type" if not isinstance(value["protocol"], str) else "enum"
        return ValidationIssue(pointer(path, "protocol"), category, "The result protocol must be citry-events/1.")
    request_id = value["requestId"]
    if request_id is not None and not isinstance(request_id, str):
        return ValidationIssue(pointer(path, "requestId"), "type", "The result request ID must be a string or null.")
    if request_id == "":
        return ValidationIssue(pointer(path, "requestId"), "range", "The result request ID must not be empty.")
    results = value["results"]
    if not isinstance(results, list):
        return ValidationIssue(pointer(path, "results"), "type", "The results must be an array.")
    if not results:
        return ValidationIssue(pointer(path, "results"), "range", "The results array must not be empty.")
    for index, result in enumerate(results):
        issue = _validate_result_shape(result, "")
        if issue is not None:
            return ValidationIssue(
                pointer(pointer(path, "results"), index) + issue.path,
                issue.category,
                issue.message,
            )
    if request_id is None:
        if len(results) != 1:
            return ValidationIssue(pointer(path, "results"), "correlation", "An edge error has exactly one result.")
        result = results[0]
        if result.get("ok") is not False or "sendSequence" in result:
            return ValidationIssue(
                pointer(path, "results"), "correlation", "A null request ID is only for an edge error."
            )
        error = result.get("error", {})
        if error.get("code") not in ("protocol_mismatch", "payload_too_large"):
            return ValidationIssue(
                pointer(path, "results"), "correlation", "A null request ID is only for an edge error."
            )
        if "fieldErrors" in error:
            return ValidationIssue(pointer(path, "results"), "correlation", "An edge error has no field errors.")
    return None


def validate_exchange(call_envelope: Mapping[str, Any], result_envelope: Any) -> ValidationIssue | None:
    """Validate result correlation and advertised capabilities for one exchange."""
    issue = validate_result_envelope(result_envelope)
    if issue is not None:
        return issue
    if result_envelope["requestId"] != call_envelope.get("requestId"):
        return ValidationIssue("/requestId", "correlation", "The result request ID does not match the call.")
    calls = call_envelope.get("calls")
    results = result_envelope["results"]
    if not isinstance(calls, list) or len(calls) != len(results):
        return ValidationIssue("/results", "correlation", "The result count does not match the call count.")
    raw_capabilities = call_envelope.get("capabilities", {})
    allowed = {
        name: set(raw_capabilities.get(name, CAPABILITIES_BASELINE_V1[name]))
        if isinstance(raw_capabilities, dict)
        else set()
        for name in ("swaps", "actions")
    }
    for index, (call, result) in enumerate(zip(calls, results, strict=True)):
        expected_sequence = call_send_sequence(call)
        actual_sequence = result.get("sendSequence")
        if expected_sequence != actual_sequence or (("sendSequence" in result) != (expected_sequence is not None)):
            return ValidationIssue(
                f"/results/{index}/sendSequence", "correlation", "The result does not echo the call's send sequence."
            )
        if result.get("ok") is not True:
            continue
        for action_index, action in enumerate(result["actions"]):
            if action["action"] not in allowed["actions"]:
                return ValidationIssue(
                    f"/results/{index}/actions/{action_index}/action",
                    "capability",
                    "The result uses an action the caller did not advertise.",
                )
            if action["action"] == "render" and action["swap"] not in allowed["swaps"]:
                return ValidationIssue(
                    f"/results/{index}/actions/{action_index}/swap",
                    "capability",
                    "The result uses a swap the caller did not advertise.",
                )
    return None
