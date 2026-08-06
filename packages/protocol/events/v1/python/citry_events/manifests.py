"""Descriptor and browser-manifest helpers for citry-events/1."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from .calls import PROTOCOL, valid_render_id
from .issues import (
    ProtocolValueError,
    ValidationIssue,
    copy_json,
    first_unknown,
    is_finite_json_number,
    pointer,
    utf16_key,
    validate_strict_json,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_HTTP_METHOD = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Z-]+$")
_REVISION = re.compile(r"^[0-9a-f]{64}$")
_DESCRIPTOR_FIELDS = ("componentClassId", "eventHandlers", "writableStateFields")
_HANDLER_FIELDS = (
    "httpMethod",
    "usesState",
    "debounceMilliseconds",
    "throttleMilliseconds",
    "latestCallWins",
    "allowBatching",
)
_INSTANCE_FIELDS = ("renderId", "componentClassId", "stateToken", "publicState")
_MANIFEST_FIELDS = ("protocol", "clientGraphRevision", "componentClasses", "componentInstances")


def validate_handler_descriptor(value: Any, path: str = "") -> ValidationIssue | None:
    """Return the first issue in one handler-hints record."""
    json_issue = validate_strict_json(value, path)
    if json_issue is not None:
        return json_issue
    return _validate_handler_descriptor_shape(value, path)


def _validate_handler_descriptor_shape(value: Any, path: str) -> ValidationIssue | None:
    """Validate handler hints after their containing value passed strict JSON."""
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", "Event-handler hints must be an object.")
    if "httpMethod" not in value:
        return ValidationIssue(pointer(path, "httpMethod"), "required", "Handler hints require 'httpMethod'.")
    found, unknown = first_unknown(value, set(_HANDLER_FIELDS))
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", "Handler hints have an unknown field.")
    method = value["httpMethod"]
    if not isinstance(method, str):
        return ValidationIssue(pointer(path, "httpMethod"), "type", "The HTTP method must be a string.")
    if _HTTP_METHOD.fullmatch(method) is None:
        return ValidationIssue(pointer(path, "httpMethod"), "pattern", "The HTTP method must be an uppercase token.")
    if "usesState" in value and value["usesState"] is not True:
        return ValidationIssue(
            pointer(path, "usesState"), "enum", "The usesState hint has its non-default literal value."
        )
    for name in ("debounceMilliseconds", "throttleMilliseconds"):
        if name not in value:
            continue
        duration = value[name]
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            return ValidationIssue(pointer(path, name), "type", f"The {name} hint must be an integer.")
        if not is_finite_json_number(duration):
            return ValidationIssue(
                pointer(path, name), "strict_json", f"The {name} hint is outside the browser JSON range."
            )
        if isinstance(duration, float) and not duration.is_integer():
            return ValidationIssue(pointer(path, name), "type", f"The {name} hint must be an integer.")
        if duration < 0:
            return ValidationIssue(pointer(path, name), "range", f"The {name} hint must be at least 0.")
    if "latestCallWins" in value and value["latestCallWins"] is not True:
        return ValidationIssue(
            pointer(path, "latestCallWins"), "enum", "The latestCallWins hint has its non-default literal value."
        )
    if "allowBatching" in value and value["allowBatching"] is not False:
        return ValidationIssue(
            pointer(path, "allowBatching"), "enum", "The allowBatching hint has its non-default literal value."
        )
    return None


def validate_descriptor(value: Any, path: str = "") -> ValidationIssue | None:
    """Return the first issue in one component-class descriptor."""
    json_issue = validate_strict_json(value, path)
    if json_issue is not None:
        return json_issue
    return _validate_descriptor_shape(value, path)


def _validate_descriptor_shape(value: Any, path: str) -> ValidationIssue | None:
    """Validate one descriptor after its containing value passed strict JSON."""
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", "A component descriptor must be an object.")
    for required in ("componentClassId", "eventHandlers"):
        if required not in value:
            return ValidationIssue(pointer(path, required), "required", f"The descriptor requires {required!r}.")
    found, unknown = first_unknown(value, set(_DESCRIPTOR_FIELDS))
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", "The descriptor has an unknown field.")
    class_id = value["componentClassId"]
    if not isinstance(class_id, str):
        return ValidationIssue(pointer(path, "componentClassId"), "type", "The component class ID must be a string.")
    if not class_id:
        return ValidationIssue(pointer(path, "componentClassId"), "range", "The component class ID must not be empty.")
    handlers = value["eventHandlers"]
    if not isinstance(handlers, dict):
        return ValidationIssue(pointer(path, "eventHandlers"), "type", "Event handlers must be an object.")
    if any(not isinstance(name, str) for name in handlers):
        return ValidationIssue(pointer(path, "eventHandlers"), "strict_json", "A handler name must be a string.")
    for name in sorted(handlers, key=utf16_key):
        if not name:
            return ValidationIssue(pointer(path, "eventHandlers"), "range", "A handler name must not be empty.")
        issue = _validate_handler_descriptor_shape(handlers[name], pointer(pointer(path, "eventHandlers"), name))
        if issue is not None:
            return issue
    if "writableStateFields" in value:
        fields = value["writableStateFields"]
        field_path = pointer(path, "writableStateFields")
        if not isinstance(fields, list):
            return ValidationIssue(field_path, "type", "Writable State fields must be an array.")
        seen: set[str] = set()
        for index, field in enumerate(fields):
            if not isinstance(field, str):
                return ValidationIssue(pointer(field_path, index), "type", "A writable State field must be a string.")
            if not field:
                return ValidationIssue(
                    pointer(field_path, index), "range", "A writable State field must not be empty."
                )
            if field in seen:
                return ValidationIssue(field_path, "semantic", "Writable State fields must be unique.")
            seen.add(field)
    return None


def build_handler_descriptor(
    http_method: str,
    *,
    uses_state: bool = False,
    debounce_milliseconds: int | None = None,
    throttle_milliseconds: int | None = None,
    latest_call_wins: bool = False,
    allow_batching: bool = True,
) -> dict[str, Any]:
    """Build one handler's compact browser hints."""
    hints: dict[str, Any] = {"httpMethod": http_method}
    if uses_state:
        hints["usesState"] = True
    if debounce_milliseconds is not None:
        hints["debounceMilliseconds"] = debounce_milliseconds
    if throttle_milliseconds is not None:
        hints["throttleMilliseconds"] = throttle_milliseconds
    if latest_call_wins:
        hints["latestCallWins"] = True
    if not allow_batching:
        hints["allowBatching"] = False
    issue = validate_handler_descriptor(hints)
    if issue is not None:
        raise ProtocolValueError(issue)
    return hints


def build_descriptor(
    component_class_id: str,
    event_handlers: Mapping[str, Mapping[str, Any]],
    *,
    writable_state_fields: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build one fresh component-class descriptor."""
    descriptor: dict[str, Any] = {
        "componentClassId": component_class_id,
        "eventHandlers": {name: copy_json(dict(hints)) for name, hints in event_handlers.items()},
    }
    if writable_state_fields is not None:
        descriptor["writableStateFields"] = list(writable_state_fields)
    issue = validate_descriptor(descriptor)
    if issue is not None:
        raise ProtocolValueError(issue)
    return descriptor


def validate_component_instance(value: Any, path: str = "") -> ValidationIssue | None:
    """Return the first issue in one rendered component-instance record."""
    json_issue = validate_strict_json(value, path)
    if json_issue is not None:
        return json_issue
    return _validate_component_instance_shape(value, path)


def _validate_component_instance_shape(value: Any, path: str) -> ValidationIssue | None:
    """Validate one instance after its containing value passed strict JSON."""
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", "A component instance must be an object.")
    for required in _INSTANCE_FIELDS:
        if required not in value:
            return ValidationIssue(pointer(path, required), "required", f"The instance requires {required!r}.")
    found, unknown = first_unknown(value, set(_INSTANCE_FIELDS))
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", "The component instance has an unknown field.")
    render_id = value["renderId"]
    if not isinstance(render_id, str):
        return ValidationIssue(pointer(path, "renderId"), "type", "The render ID must be a string.")
    if not valid_render_id(render_id):
        return ValidationIssue(pointer(path, "renderId"), "pattern", "The render ID has invalid characters.")
    class_id = value["componentClassId"]
    if not isinstance(class_id, str):
        return ValidationIssue(pointer(path, "componentClassId"), "type", "The component class ID must be a string.")
    if not class_id:
        return ValidationIssue(pointer(path, "componentClassId"), "range", "The component class ID must not be empty.")
    token = value["stateToken"]
    if token is not None and not isinstance(token, str):
        return ValidationIssue(pointer(path, "stateToken"), "type", "The state token must be a string or null.")
    if token == "":
        return ValidationIssue(pointer(path, "stateToken"), "range", "The state token must not be empty.")
    public_state = value["publicState"]
    if not isinstance(public_state, dict):
        return ValidationIssue(pointer(path, "publicState"), "type", "Public State must be an object.")
    return None


def build_component_instance(
    render_id: str,
    component_class_id: str,
    state_token: str | None,
    public_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one fresh component-instance record."""
    instance = {
        "renderId": render_id,
        "componentClassId": component_class_id,
        "stateToken": state_token,
        "publicState": copy_json(dict(public_state)),
    }
    issue = validate_component_instance(instance)
    if issue is not None:
        raise ProtocolValueError(issue)
    return instance


def validate_manifest(value: Any, path: str = "") -> ValidationIssue | None:
    """Return the first structural or relationship issue in a browser manifest."""
    json_issue = validate_strict_json(value, path)
    if json_issue is not None:
        return json_issue
    return _validate_manifest_shape(value, path)


def _validate_manifest_shape(value: Any, path: str) -> ValidationIssue | None:
    """Validate one manifest after the complete value passed strict JSON."""
    if not isinstance(value, dict):
        return ValidationIssue(path, "type", "The Events manifest must be an object.")
    for required in _MANIFEST_FIELDS:
        if required not in value:
            return ValidationIssue(pointer(path, required), "required", f"The manifest requires {required!r}.")
    found, unknown = first_unknown(value, set(_MANIFEST_FIELDS))
    if found:
        return ValidationIssue(pointer(path, unknown), "unknown_field", "The manifest has an unknown field.")
    if value["protocol"] != PROTOCOL:
        category = "type" if not isinstance(value["protocol"], str) else "enum"
        return ValidationIssue(pointer(path, "protocol"), category, "The manifest protocol must be citry-events/1.")
    revision = value["clientGraphRevision"]
    if revision is not None and not isinstance(revision, str):
        return ValidationIssue(
            pointer(path, "clientGraphRevision"), "type", "The graph revision must be a string or null."
        )
    if isinstance(revision, str) and _REVISION.fullmatch(revision) is None:
        return ValidationIssue(
            pointer(path, "clientGraphRevision"), "pattern", "The graph revision must be lowercase SHA-256."
        )
    classes = value["componentClasses"]
    if not isinstance(classes, list):
        return ValidationIssue(pointer(path, "componentClasses"), "type", "Component classes must be an array.")

    for index, descriptor in enumerate(classes):
        item_path = pointer(pointer(path, "componentClasses"), index)
        issue = _validate_descriptor_shape(descriptor, item_path)
        if issue is not None:
            return issue

    instances = value["componentInstances"]
    if not isinstance(instances, list):
        return ValidationIssue(pointer(path, "componentInstances"), "type", "Component instances must be an array.")
    for index, instance in enumerate(instances):
        item_path = pointer(pointer(path, "componentInstances"), index)
        issue = _validate_component_instance_shape(instance, item_path)
        if issue is not None:
            return issue

    class_ids: set[str] = set()
    for index, descriptor in enumerate(classes):
        item_path = pointer(pointer(path, "componentClasses"), index)
        class_id = descriptor["componentClassId"]
        if class_id in class_ids:
            return ValidationIssue(item_path, "semantic", f"Duplicate component class ID {class_id!r}.")
        class_ids.add(class_id)
    render_ids: set[str] = set()
    for index, instance in enumerate(instances):
        item_path = pointer(pointer(path, "componentInstances"), index)
        render_id = instance["renderId"]
        if render_id in render_ids:
            return ValidationIssue(item_path, "semantic", f"Duplicate render ID {render_id!r}.")
        render_ids.add(render_id)
    for index, instance in enumerate(instances):
        item_path = pointer(pointer(path, "componentInstances"), index)
        if instance["componentClassId"] not in class_ids:
            return ValidationIssue(
                pointer(item_path, "componentClassId"),
                "semantic",
                "The instance refers to an unknown component class.",
            )
    for index, instance in enumerate(instances):
        item_path = pointer(pointer(path, "componentInstances"), index)
        if instance["stateToken"] is None and instance["publicState"]:
            return ValidationIssue(
                pointer(item_path, "publicState"), "semantic", "A stateless instance must have empty public State."
            )
    return None


def build_manifest(
    client_graph_revision: str | None,
    component_classes: Sequence[Mapping[str, Any]],
    component_instances: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a fresh, fully validated Events browser manifest."""
    manifest = {
        "protocol": PROTOCOL,
        "clientGraphRevision": client_graph_revision,
        "componentClasses": [copy_json(dict(item)) for item in component_classes],
        "componentInstances": [copy_json(dict(item)) for item in component_instances],
    }
    issue = validate_manifest(manifest)
    if issue is not None:
        raise ProtocolValueError(issue)
    return manifest
