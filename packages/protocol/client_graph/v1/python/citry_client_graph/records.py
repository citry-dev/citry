"""Closed-record builders and validators for the client ownership graph."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from .canonical import MAX_SAFE_INTEGER
from .issues import (
    ProtocolValueError,
    ValidationIssue,
    copy_json,
    first_unknown,
    is_finite_json_number,
    pointer,
    validate_strict_json,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

_RENDER_ID = re.compile(r"^[a-z0-9_-]+$")
_LOCATION_KINDS = (
    "component-call",
    "component-tag-client-binding",
    "implicit-fill",
    "named-fill",
    "fallback-fill",
    "slot-outlet",
)
_BINDING_SOURCES = ("direct", "server-dynamic", "spread")
_FILL_KINDS = ("implicit", "named", "fallback", "python", "typed-default")
_SOURCE_POLICIES = ("template", "python-detached", "typed-default-detached")
_MORPH_MODES = ("ignore",)

_COMPONENT_CLASS_FIELDS = ("classId", "className")
_COMPONENT_INSTANCE_FIELDS = (
    "instanceId",
    "renderId",
    "classId",
    "invocationId",
    "parentRenderId",
    "transparent",
)
_SOURCE_LOCATION_FIELDS = (
    "locationId",
    "kind",
    "ownerRenderId",
    "ownerClassId",
    "carrierInstanceId",
    "origin",
    "sourceOffset",
    "sourcePos",
    "mappingKey",
    "mappingIndex",
)
_EXPRESSION_PAYLOAD_FIELDS = ("type", "expression")
_DOM_PAYLOAD_FIELDS = (
    "type",
    "classId",
    "event",
    "handler",
    "args",
    "prevent",
    "stop",
    "self",
    "once",
    "key",
    "debounce",
    "throttle",
)
_POLL_PAYLOAD_FIELDS = ("type", "classId", "handler", "args", "interval")
_CLIENT_BINDING_FIELDS = ("key", "source", "locationId", "payload")
_NESTED_COMPONENT_FIELDS = (
    "invocationId",
    "sourceRenderId",
    "sourceClassId",
    "locationId",
    "tagName",
    "targetClassId",
    "morphKey",
    "morphMode",
    "targetRenderId",
    "parentRegionId",
    "clientBindings",
)
_EXECUTION_CONSTRAINT_FIELDS = ("invocationId", "parentRenderId", "childRenderId")
_FILL_FIELDS = (
    "fillId",
    "kind",
    "slotName",
    "policy",
    "ownerRenderId",
    "ownerClassId",
    "locationId",
    "sourceInvocationId",
    "receiverRenderId",
    "receiverClassId",
    "fallbackLocationId",
)
_SLOT_REGION_FIELDS = (
    "regionId",
    "fillId",
    "receiverRenderId",
    "slotLocationId",
    "ownerRenderId",
    "sourceLocationId",
    "parentRegionId",
    "transitionFromRenderId",
    "resultOwnerRenderId",
)
GRAPH_FIELDS = (
    "graphId",
    "componentClasses",
    "componentInstances",
    "sourceLocations",
    "nestedComponents",
    "componentExecutionOrderConstraints",
    "fills",
    "slotRegions",
)


def _record_issue(
    value: Any,
    path: str,
    fields: tuple[str, ...],
    label: str,
    *,
    strict: bool = True,
) -> ValidationIssue | None:
    if strict:
        issue = validate_strict_json(value, path)
        if issue is not None:
            return issue
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", f"{label} must be an object.")
    for required in fields:
        if required not in value:
            return ValidationIssue(pointer(path, required), "required", f"{label} requires {required!r}.")
    found, unknown = first_unknown(value, set(fields))
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", f"{label} has an unknown field.")
    return None


def _string_issue(value: Any, path: str, label: str) -> ValidationIssue | None:
    if not isinstance(value, str):
        return ValidationIssue(path, "type", f"{label} must be a string.")
    return None


def _nullable_string_issue(value: Any, path: str, label: str) -> ValidationIssue | None:
    if value is not None and not isinstance(value, str):
        return ValidationIssue(path, "type", f"{label} must be a string or null.")
    return None


def _integer_issue(
    value: Any,
    path: str,
    label: str,
    *,
    minimum: int,
) -> ValidationIssue | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ValidationIssue(path, "type", f"{label} must be an integer.")
    if not is_finite_json_number(value):
        return ValidationIssue(path, "strict_json", f"{label} is outside the browser JSON range.")
    if isinstance(value, float) and not value.is_integer():
        return ValidationIssue(path, "type", f"{label} must be an integer.")
    if not minimum <= value <= MAX_SAFE_INTEGER:
        return ValidationIssue(
            path,
            "range",
            f"{label} must be from {minimum} to {MAX_SAFE_INTEGER}.",
        )
    return None


def _nullable_integer_issue(
    value: Any,
    path: str,
    label: str,
    *,
    minimum: int,
) -> ValidationIssue | None:
    return None if value is None else _integer_issue(value, path, label, minimum=minimum)


def _enum_issue(value: Any, path: str, choices: tuple[str, ...], label: str) -> ValidationIssue | None:
    if not isinstance(value, str):
        return ValidationIssue(path, "type", f"{label} must be a string.")
    if value not in choices:
        return ValidationIssue(path, "enum", f"{label} is not a client-graph v1 value.")
    return None


def _nullable_enum_issue(
    value: Any,
    path: str,
    choices: tuple[str, ...],
    label: str,
) -> ValidationIssue | None:
    return None if value is None else _enum_issue(value, path, choices, label)


def _built(
    record: dict[str, Any],
    validator: Callable[[Any, str], ValidationIssue | None],
    *,
    audit: bool = True,
) -> dict[str, Any]:
    if not audit:
        return record
    issue = validator(record, "")
    if issue is not None:
        raise ProtocolValueError(issue)
    return record


def validate_component_class(value: Any, path: str = "", *, strict: bool = True) -> ValidationIssue | None:
    """Return the first issue in one component-class record."""
    issue = _record_issue(value, path, _COMPONENT_CLASS_FIELDS, "A component-class record", strict=strict)
    if issue is not None:
        return issue
    for field in _COMPONENT_CLASS_FIELDS:
        issue = _string_issue(value[field], pointer(path, field), f"The component {field}")
        if issue is not None:
            return issue
    return None


def build_component_class(class_id: str, class_name: str, *, audit: bool = True) -> dict[str, Any]:
    """Build one component-class record."""
    return _built({"classId": class_id, "className": class_name}, validate_component_class, audit=audit)


def validate_component_instance(value: Any, path: str = "", *, strict: bool = True) -> ValidationIssue | None:
    """Return the first issue in one component-instance record."""
    issue = _record_issue(value, path, _COMPONENT_INSTANCE_FIELDS, "A component-instance record", strict=strict)
    if issue is not None:
        return issue
    checks = (
        _integer_issue(value["instanceId"], pointer(path, "instanceId"), "The instance ID", minimum=1),
        _string_issue(value["renderId"], pointer(path, "renderId"), "The render ID"),
        _string_issue(value["classId"], pointer(path, "classId"), "The class ID"),
        _nullable_integer_issue(value["invocationId"], pointer(path, "invocationId"), "The invocation ID", minimum=1),
        _nullable_string_issue(value["parentRenderId"], pointer(path, "parentRenderId"), "The parent render ID"),
    )
    for check in checks:
        if check is not None:
            return check
    if _RENDER_ID.fullmatch(value["renderId"]) is None:
        return ValidationIssue(
            pointer(path, "renderId"),
            "pattern",
            "The component renderId is not safe for an HTML attribute name.",
        )
    if not isinstance(value["transparent"], bool):
        return ValidationIssue(pointer(path, "transparent"), "type", "The transparent flag must be a boolean.")
    return None


def build_component_instance(
    *,
    instance_id: int,
    render_id: str,
    class_id: str,
    invocation_id: int | None,
    parent_render_id: str | None,
    transparent: bool,
    audit: bool = True,
) -> dict[str, Any]:
    """Build one component-instance record."""
    return _built(
        {
            "instanceId": instance_id,
            "renderId": render_id,
            "classId": class_id,
            "invocationId": invocation_id,
            "parentRenderId": parent_render_id,
            "transparent": transparent,
        },
        validate_component_instance,
        audit=audit,
    )


def validate_source_location(value: Any, path: str = "", *, strict: bool = True) -> ValidationIssue | None:
    """Return the first issue in one development source-location record."""
    issue = _record_issue(value, path, _SOURCE_LOCATION_FIELDS, "A source-location record", strict=strict)
    if issue is not None:
        return issue
    scalar_checks = (
        _integer_issue(value["locationId"], pointer(path, "locationId"), "The location ID", minimum=1),
        _enum_issue(value["kind"], pointer(path, "kind"), _LOCATION_KINDS, "The location kind"),
        _string_issue(value["ownerRenderId"], pointer(path, "ownerRenderId"), "The location owner render ID"),
        _string_issue(value["ownerClassId"], pointer(path, "ownerClassId"), "The location owner class ID"),
        _integer_issue(
            value["carrierInstanceId"], pointer(path, "carrierInstanceId"), "The carrier instance ID", minimum=1
        ),
        _nullable_string_issue(value["origin"], pointer(path, "origin"), "The source origin"),
    )
    for check in scalar_checks:
        if check is not None:
            return check
    offset_path = pointer(path, "sourceOffset")
    issue = _record_issue(
        value["sourceOffset"], offset_path, ("start", "end"), "A source-offset record", strict=strict
    )
    if issue is not None:
        return issue
    for field in ("start", "end"):
        issue = _integer_issue(
            value["sourceOffset"][field], pointer(offset_path, field), f"The source-offset {field}", minimum=0
        )
        if issue is not None:
            return issue
    position_path = pointer(path, "sourcePos")
    issue = _record_issue(
        value["sourcePos"], position_path, ("line", "column"), "A source-position record", strict=strict
    )
    if issue is not None:
        return issue
    for field in ("line", "column"):
        issue = _integer_issue(
            value["sourcePos"][field], pointer(position_path, field), f"The source-position {field}", minimum=1
        )
        if issue is not None:
            return issue
    issue = _nullable_string_issue(value["mappingKey"], pointer(path, "mappingKey"), "The mapping key")
    if issue is not None:
        return issue
    return _nullable_integer_issue(
        value["mappingIndex"], pointer(path, "mappingIndex"), "The mapping index", minimum=0
    )


def build_source_location(
    *,
    location_id: int,
    kind: str,
    owner_render_id: str,
    owner_class_id: str,
    carrier_instance_id: int,
    origin: str | None,
    source_start: int,
    source_end: int,
    source_line: int,
    source_column: int,
    mapping_key: str | None,
    mapping_index: int | None,
    audit: bool = True,
) -> dict[str, Any]:
    """Build one development source-location record."""
    return _built(
        {
            "locationId": location_id,
            "kind": kind,
            "ownerRenderId": owner_render_id,
            "ownerClassId": owner_class_id,
            "carrierInstanceId": carrier_instance_id,
            "origin": origin,
            "sourceOffset": {"start": source_start, "end": source_end},
            "sourcePos": {"line": source_line, "column": source_column},
            "mappingKey": mapping_key,
            "mappingIndex": mapping_index,
        },
        validate_source_location,
        audit=audit,
    )


def validate_client_binding_payload(value: Any, path: str = "", *, strict: bool = True) -> ValidationIssue | None:
    """Return the first issue in one component-tag client-binding payload."""
    if strict:
        issue = validate_strict_json(value, path)
        if issue is not None:
            return issue
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", "A client-binding payload must be an object.")
    if "type" not in value:
        return ValidationIssue(pointer(path, "type"), "required", "A client-binding payload requires 'type'.")
    payload_type = value["type"]
    if not isinstance(payload_type, str):
        return ValidationIssue(pointer(path, "type"), "type", "The client-binding payload type must be a string.")
    fields: tuple[str, ...]
    if payload_type in {"props", "alpine-handler"}:
        fields = _EXPRESSION_PAYLOAD_FIELDS
    elif payload_type == "citry-dom-event":
        fields = _DOM_PAYLOAD_FIELDS
    elif payload_type == "citry-poll":
        fields = _POLL_PAYLOAD_FIELDS
    else:
        return ValidationIssue(pointer(path, "type"), "enum", "The client-binding payload type is not a v1 value.")
    issue = _record_issue(value, path, fields, "A client-binding payload", strict=False)
    if issue is not None:
        return issue
    if payload_type in {"props", "alpine-handler"}:
        return _string_issue(value["expression"], pointer(path, "expression"), "The Alpine expression")
    if payload_type == "citry-poll":
        for field in ("classId", "handler"):
            issue = _string_issue(value[field], pointer(path, field), f"The poll {field}")
            if issue is not None:
                return issue
        issue = _nullable_string_issue(value["args"], pointer(path, "args"), "The poll arguments")
        if issue is not None:
            return issue
        return _integer_issue(value["interval"], pointer(path, "interval"), "The poll interval", minimum=1)
    for field in ("classId", "event", "handler"):
        issue = _string_issue(value[field], pointer(path, field), f"The DOM-event {field}")
        if issue is not None:
            return issue
    issue = _nullable_string_issue(value["args"], pointer(path, "args"), "The DOM-event args")
    if issue is not None:
        return issue
    for field in ("prevent", "stop", "self", "once"):
        if not isinstance(value[field], bool):
            return ValidationIssue(pointer(path, field), "type", f"The DOM-event {field} flag must be a boolean.")
    issue = _nullable_string_issue(value["key"], pointer(path, "key"), "The DOM-event key")
    if issue is not None:
        return issue
    for field in ("debounce", "throttle"):
        issue = _nullable_integer_issue(value[field], pointer(path, field), f"The DOM-event {field} delay", minimum=0)
        if issue is not None:
            return issue
    return None


def build_expression_payload(payload_type: str, expression: str, *, audit: bool = True) -> dict[str, Any]:
    """Build one props or Alpine-handler expression payload."""
    return _built(
        {"type": payload_type, "expression": expression},
        validate_client_binding_payload,
        audit=audit,
    )


def build_dom_event_payload(
    *,
    class_id: str,
    event: str,
    handler: str,
    args: str | None,
    prevent: bool,
    stop: bool,
    self_: bool,
    once: bool,
    key: str | None,
    debounce: int | None,
    throttle: int | None,
    audit: bool = True,
) -> dict[str, Any]:
    """Build one compiled Citry DOM-event payload."""
    return _built(
        {
            "type": "citry-dom-event",
            "classId": class_id,
            "event": event,
            "handler": handler,
            "args": args,
            "prevent": prevent,
            "stop": stop,
            "self": self_,
            "once": once,
            "key": key,
            "debounce": debounce,
            "throttle": throttle,
        },
        validate_client_binding_payload,
        audit=audit,
    )


def build_poll_payload(
    *,
    class_id: str,
    handler: str,
    args: str | None,
    interval: int,
    audit: bool = True,
) -> dict[str, Any]:
    """Build one compiled Citry polling payload."""
    return _built(
        {"type": "citry-poll", "classId": class_id, "handler": handler, "args": args, "interval": interval},
        validate_client_binding_payload,
        audit=audit,
    )


def validate_client_binding(value: Any, path: str = "", *, strict: bool = True) -> ValidationIssue | None:
    """Return the first issue in one component-tag client-binding record."""
    issue = _record_issue(
        value,
        path,
        _CLIENT_BINDING_FIELDS,
        "A component-tag client-binding record",
        strict=strict,
    )
    if issue is not None:
        return issue
    checks = (
        _string_issue(value["key"], pointer(path, "key"), "The client-binding key"),
        _enum_issue(value["source"], pointer(path, "source"), _BINDING_SOURCES, "The client-binding source"),
        _nullable_integer_issue(
            value["locationId"], pointer(path, "locationId"), "The client-binding location ID", minimum=1
        ),
    )
    for check in checks:
        if check is not None:
            return check
    return validate_client_binding_payload(value["payload"], pointer(path, "payload"), strict=False)


def build_client_binding(
    *,
    key: str,
    source: str,
    location_id: int | None,
    payload: dict[str, Any],
    audit: bool = True,
) -> dict[str, Any]:
    """Build one component-tag client-binding record."""
    record = _built(
        {
            "key": key,
            "source": source,
            "locationId": location_id,
            "payload": payload,
        },
        validate_client_binding,
        audit=audit,
    )
    return copy_json(record) if audit else record


def validate_nested_component(value: Any, path: str = "", *, strict: bool = True) -> ValidationIssue | None:
    """Return the first issue in one nested-component record."""
    issue = _record_issue(value, path, _NESTED_COMPONENT_FIELDS, "A nested-component record", strict=strict)
    if issue is not None:
        return issue
    checks = (
        _integer_issue(value["invocationId"], pointer(path, "invocationId"), "The invocation ID", minimum=1),
        _string_issue(value["sourceRenderId"], pointer(path, "sourceRenderId"), "The source render ID"),
        _string_issue(value["sourceClassId"], pointer(path, "sourceClassId"), "The source class ID"),
        _nullable_integer_issue(value["locationId"], pointer(path, "locationId"), "The location ID", minimum=1),
        _string_issue(value["tagName"], pointer(path, "tagName"), "The nested-component tag name"),
        _string_issue(value["targetClassId"], pointer(path, "targetClassId"), "The target class ID"),
        _nullable_string_issue(value["morphKey"], pointer(path, "morphKey"), "The component morph key"),
        _nullable_enum_issue(value["morphMode"], pointer(path, "morphMode"), _MORPH_MODES, "The component morph mode"),
        _string_issue(value["targetRenderId"], pointer(path, "targetRenderId"), "The target render ID"),
        _nullable_integer_issue(
            value["parentRegionId"], pointer(path, "parentRegionId"), "The parent slot-region ID", minimum=1
        ),
    )
    for check in checks:
        if check is not None:
            return check
    bindings = value["clientBindings"]
    if not isinstance(bindings, list):
        return ValidationIssue(pointer(path, "clientBindings"), "type", "Client bindings must be an array.")
    for index, binding in enumerate(bindings):
        issue = validate_client_binding(binding, pointer(pointer(path, "clientBindings"), index), strict=False)
        if issue is not None:
            return issue
    return None


def build_nested_component(
    *,
    invocation_id: int,
    source_render_id: str,
    source_class_id: str,
    location_id: int | None,
    tag_name: str,
    target_class_id: str,
    morph_key: str | None,
    morph_mode: str | None,
    target_render_id: str,
    parent_region_id: int | None,
    client_bindings: Sequence[dict[str, Any]],
    audit: bool = True,
) -> dict[str, Any]:
    """Build one nested-component record."""
    record = _built(
        {
            "invocationId": invocation_id,
            "sourceRenderId": source_render_id,
            "sourceClassId": source_class_id,
            "locationId": location_id,
            "tagName": tag_name,
            "targetClassId": target_class_id,
            "morphKey": morph_key,
            "morphMode": morph_mode,
            "targetRenderId": target_render_id,
            "parentRegionId": parent_region_id,
            "clientBindings": list(client_bindings),
        },
        validate_nested_component,
        audit=audit,
    )
    return copy_json(record) if audit else record


def validate_execution_constraint(value: Any, path: str = "", *, strict: bool = True) -> ValidationIssue | None:
    """Return the first issue in one component execution-order record."""
    issue = _record_issue(value, path, _EXECUTION_CONSTRAINT_FIELDS, "An execution-order constraint", strict=strict)
    if issue is not None:
        return issue
    checks = (
        _integer_issue(value["invocationId"], pointer(path, "invocationId"), "The invocation ID", minimum=1),
        _string_issue(value["parentRenderId"], pointer(path, "parentRenderId"), "The parent render ID"),
        _string_issue(value["childRenderId"], pointer(path, "childRenderId"), "The child render ID"),
    )
    return next((check for check in checks if check is not None), None)


def build_execution_constraint(
    *,
    invocation_id: int,
    parent_render_id: str,
    child_render_id: str,
    audit: bool = True,
) -> dict[str, Any]:
    """Build one component execution-order constraint."""
    return _built(
        {"invocationId": invocation_id, "parentRenderId": parent_render_id, "childRenderId": child_render_id},
        validate_execution_constraint,
        audit=audit,
    )


def validate_fill(value: Any, path: str = "", *, strict: bool = True) -> ValidationIssue | None:
    """Return the first issue in one logical fill record."""
    issue = _record_issue(value, path, _FILL_FIELDS, "A fill record", strict=strict)
    if issue is not None:
        return issue
    checks = (
        _integer_issue(value["fillId"], pointer(path, "fillId"), "The fill ID", minimum=1),
        _enum_issue(value["kind"], pointer(path, "kind"), _FILL_KINDS, "The fill kind"),
        _string_issue(value["slotName"], pointer(path, "slotName"), "The fill slot name"),
        _enum_issue(value["policy"], pointer(path, "policy"), _SOURCE_POLICIES, "The fill source policy"),
        _nullable_string_issue(value["ownerRenderId"], pointer(path, "ownerRenderId"), "The fill owner render ID"),
        _nullable_string_issue(value["ownerClassId"], pointer(path, "ownerClassId"), "The fill owner class ID"),
        _nullable_integer_issue(value["locationId"], pointer(path, "locationId"), "The fill location ID", minimum=1),
        _nullable_integer_issue(
            value["sourceInvocationId"], pointer(path, "sourceInvocationId"), "The source invocation ID", minimum=1
        ),
        _nullable_string_issue(value["receiverRenderId"], pointer(path, "receiverRenderId"), "The receiver render ID"),
        _nullable_string_issue(value["receiverClassId"], pointer(path, "receiverClassId"), "The receiver class ID"),
        _nullable_integer_issue(
            value["fallbackLocationId"], pointer(path, "fallbackLocationId"), "The fallback location ID", minimum=1
        ),
    )
    return next((check for check in checks if check is not None), None)


def build_fill(
    *,
    fill_id: int,
    kind: str,
    slot_name: str,
    policy: str,
    owner_render_id: str | None,
    owner_class_id: str | None,
    location_id: int | None,
    source_invocation_id: int | None,
    receiver_render_id: str | None,
    receiver_class_id: str | None,
    fallback_location_id: int | None,
    audit: bool = True,
) -> dict[str, Any]:
    """Build one logical fill record."""
    return _built(
        {
            "fillId": fill_id,
            "kind": kind,
            "slotName": slot_name,
            "policy": policy,
            "ownerRenderId": owner_render_id,
            "ownerClassId": owner_class_id,
            "locationId": location_id,
            "sourceInvocationId": source_invocation_id,
            "receiverRenderId": receiver_render_id,
            "receiverClassId": receiver_class_id,
            "fallbackLocationId": fallback_location_id,
        },
        validate_fill,
        audit=audit,
    )


def validate_slot_region(value: Any, path: str = "", *, strict: bool = True) -> ValidationIssue | None:
    """Return the first issue in one physical slot-region record."""
    issue = _record_issue(value, path, _SLOT_REGION_FIELDS, "A slot-region record", strict=strict)
    if issue is not None:
        return issue
    checks = (
        _integer_issue(value["regionId"], pointer(path, "regionId"), "The slot-region ID", minimum=1),
        _integer_issue(value["fillId"], pointer(path, "fillId"), "The fill ID", minimum=1),
        _nullable_string_issue(value["receiverRenderId"], pointer(path, "receiverRenderId"), "The receiver render ID"),
        _nullable_integer_issue(
            value["slotLocationId"], pointer(path, "slotLocationId"), "The slot location ID", minimum=1
        ),
        _nullable_string_issue(value["ownerRenderId"], pointer(path, "ownerRenderId"), "The owner render ID"),
        _nullable_integer_issue(
            value["sourceLocationId"], pointer(path, "sourceLocationId"), "The source location ID", minimum=1
        ),
        _nullable_integer_issue(
            value["parentRegionId"], pointer(path, "parentRegionId"), "The parent slot-region ID", minimum=1
        ),
        _nullable_string_issue(
            value["transitionFromRenderId"],
            pointer(path, "transitionFromRenderId"),
            "The transition source render ID",
        ),
        _nullable_string_issue(
            value["resultOwnerRenderId"], pointer(path, "resultOwnerRenderId"), "The result owner render ID"
        ),
    )
    return next((check for check in checks if check is not None), None)


def build_slot_region(
    *,
    region_id: int,
    fill_id: int,
    receiver_render_id: str | None,
    slot_location_id: int | None,
    owner_render_id: str | None,
    source_location_id: int | None,
    parent_region_id: int | None,
    transition_from_render_id: str | None,
    result_owner_render_id: str | None,
    audit: bool = True,
) -> dict[str, Any]:
    """Build one physical slot-region record."""
    return _built(
        {
            "regionId": region_id,
            "fillId": fill_id,
            "receiverRenderId": receiver_render_id,
            "slotLocationId": slot_location_id,
            "ownerRenderId": owner_render_id,
            "sourceLocationId": source_location_id,
            "parentRegionId": parent_region_id,
            "transitionFromRenderId": transition_from_render_id,
            "resultOwnerRenderId": result_owner_render_id,
        },
        validate_slot_region,
        audit=audit,
    )


def validate_graph(value: Any, path: str = "", *, strict: bool = True) -> ValidationIssue | None:
    """Return the first structural issue in one graph record."""
    issue = _record_issue(value, path, GRAPH_FIELDS, "A graph record", strict=strict)
    if issue is not None:
        return issue
    issue = _integer_issue(value["graphId"], pointer(path, "graphId"), "The graph ID", minimum=0)
    if issue is not None:
        return issue
    collections: tuple[tuple[str, Callable[..., ValidationIssue | None]], ...] = (
        ("componentClasses", validate_component_class),
        ("componentInstances", validate_component_instance),
        ("sourceLocations", validate_source_location),
        ("nestedComponents", validate_nested_component),
        ("componentExecutionOrderConstraints", validate_execution_constraint),
        ("fills", validate_fill),
        ("slotRegions", validate_slot_region),
    )
    for field, validator in collections:
        records = value[field]
        field_path = pointer(path, field)
        if not isinstance(records, list):
            return ValidationIssue(field_path, "type", f"The graph's {field} must be an array.")
        for index, record in enumerate(records):
            issue = validator(record, pointer(field_path, index), strict=False)
            if issue is not None:
                return issue
    return None


def build_graph(
    *,
    graph_id: int,
    component_classes: Sequence[dict[str, Any]],
    component_instances: Sequence[dict[str, Any]],
    source_locations: Sequence[dict[str, Any]],
    nested_components: Sequence[dict[str, Any]],
    component_execution_order_constraints: Sequence[dict[str, Any]],
    fills: Sequence[dict[str, Any]],
    slot_regions: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Build one graph from already selected protocol records."""
    graph = assemble_graph(
        graph_id=graph_id,
        component_classes=component_classes,
        component_instances=component_instances,
        source_locations=source_locations,
        nested_components=nested_components,
        component_execution_order_constraints=component_execution_order_constraints,
        fills=fills,
        slot_regions=slot_regions,
    )
    issue = validate_graph(graph)
    if issue is not None:
        raise ProtocolValueError(issue)
    return copy_json(graph)


def assemble_graph(
    *,
    graph_id: int,
    component_classes: Sequence[dict[str, Any]],
    component_instances: Sequence[dict[str, Any]],
    source_locations: Sequence[dict[str, Any]],
    nested_components: Sequence[dict[str, Any]],
    component_execution_order_constraints: Sequence[dict[str, Any]],
    fills: Sequence[dict[str, Any]],
    slot_regions: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble package-built records without copying or checking them again."""
    return {
        "graphId": graph_id,
        "componentClasses": list(component_classes),
        "componentInstances": list(component_instances),
        "sourceLocations": list(source_locations),
        "nestedComponents": list(nested_components),
        "componentExecutionOrderConstraints": list(component_execution_order_constraints),
        "fills": list(fills),
        "slotRegions": list(slot_regions),
    }


__all__ = [
    "GRAPH_FIELDS",
    "assemble_graph",
    "build_client_binding",
    "build_component_class",
    "build_component_instance",
    "build_dom_event_payload",
    "build_execution_constraint",
    "build_expression_payload",
    "build_fill",
    "build_graph",
    "build_nested_component",
    "build_poll_payload",
    "build_slot_region",
    "build_source_location",
    "validate_client_binding",
    "validate_client_binding_payload",
    "validate_component_class",
    "validate_component_instance",
    "validate_execution_constraint",
    "validate_fill",
    "validate_graph",
    "validate_nested_component",
    "validate_slot_region",
    "validate_source_location",
]
