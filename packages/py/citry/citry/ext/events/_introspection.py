"""Safe copied metadata for the Events component-introspection entry."""

from __future__ import annotations

import inspect
import typing
from dataclasses import MISSING, Field, is_dataclass
from dataclasses import fields as dataclass_fields
from typing import TYPE_CHECKING, Literal, cast, get_origin

from citry._class_introspection import _safe_class_import_path, _static_class_dict, _static_class_mro
from citry._schema_introspection import _format_annotation, _inspect_schema_class
from citry.ext.events.handlers import _get_annotations_as_text
from citry.introspection import FieldInfo, _is_utf8_string

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry.ext.events.extension import EventHandler, EventsInfo


def capture_handler_introspection(
    func: Callable[..., object],
) -> tuple[str | None, Literal["normalized", "unavailable"], str | None]:
    """Copy a handler's advisory return type and cleaned documentation."""
    annotations = _read_function_annotations(func)
    return_type_display = _format_annotation(annotations["return"]) if "return" in annotations else None
    return_type_fidelity: Literal["normalized", "unavailable"] = (
        "normalized" if return_type_display is not None else "unavailable"
    )

    raw_description = func.__doc__
    if type(raw_description) is str:
        cleaned_description = inspect.cleandoc(raw_description)
        description = cleaned_description if cleaned_description and _is_utf8_string(cleaned_description) else None
    else:
        description = None
    return return_type_display, return_type_fidelity, description


def _read_function_annotations(func: Callable[..., object]) -> dict[str, object]:
    """Read copied annotation text without resolving names on supported Python versions."""
    try:
        return cast("dict[str, object]", _get_annotations_as_text(func))
    except Exception:  # noqa: BLE001 - advisory metadata must not break class creation
        return {}


def inspect_events(info: EventsInfo) -> dict[str, object] | None:
    """Build the version 1 Events entry from class-creation metadata."""
    if info.events_cls is None:
        return None
    return {
        "handlers": [_inspect_handler(info.handlers[name]) for name in sorted(info.handlers)],
    }


def _inspect_handler(handler: EventHandler) -> dict[str, object]:
    """Build one allowlisted handler object in the version 1 wire shape."""
    return {
        "name": handler.name,
        "methods": list(handler.methods),
        "request_schema": _inspect_request_schema(handler.data_schema),
        "return_type_display": handler.return_type_display,
        "return_type_fidelity": handler.return_type_fidelity,
        "description": handler.description,
        "debounce": handler.debounce,
        "throttle": handler.throttle,
    }


def _inspect_request_schema(schema_class: type | None) -> dict[str, object] | None:
    """Describe one request schema without converting it or executing defaults."""
    if schema_class is None:
        return None
    import_path = _safe_class_import_path(schema_class)
    inspected_fields = _inspect_schema_class(schema_class)
    if inspected_fields is not None and is_dataclass(schema_class):
        wire_names = {field.name for field in dataclass_fields(schema_class) if field.init}
        inspected_fields = tuple(field for field in inspected_fields if field.name in wire_names)
    if inspected_fields is None:
        inspected_fields = _inspect_plain_annotated_class(schema_class)
    if inspected_fields is None:
        return {
            "kind": "opaque",
            "import_path": import_path,
            "fields": [],
        }
    return {
        "kind": "fields",
        "import_path": import_path,
        "fields": [_inspect_field(field) for field in inspected_fields],
    }


def _inspect_field(field: FieldInfo) -> dict[str, object]:
    """Copy the allowlisted portion of a shared schema field record."""
    return {
        "name": field.name,
        "required": field.required,
        "type_display": field.type_display,
        "type_fidelity": field.type_fidelity,
        "description": field.description,
    }


def _inspect_plain_annotated_class(schema_class: type) -> tuple[FieldInfo, ...] | None:
    """Read the fields that Events' dataclass conversion would create."""
    annotations: dict[str, object] = {}
    saw_annotation = False
    for candidate in reversed(_static_class_mro(schema_class)):
        raw_annotations = _get_annotations_as_text(candidate)
        if not raw_annotations:
            continue
        saw_annotation = True
        for name, annotation in cast("dict[object, object]", raw_annotations).items():
            if type(name) is not str:
                continue
            if _is_classvar_annotation(annotation):
                # A subclass can remove an inherited input by redeclaring it
                # as a class variable, matching dataclass field discovery.
                annotations.pop(name, None)
            else:
                annotations[name] = annotation
    if not annotations:
        return () if saw_annotation else None

    result: list[FieldInfo] = []
    for name, annotation in annotations.items():
        default = _plain_field_default(schema_class, name)
        if type(default) is Field and not default.init:
            continue
        default_kind, required = _classify_default(default)
        description = _field_description(default) if type(default) is Field else None
        type_display = _format_annotation(annotation)
        result.append(
            FieldInfo(
                name=name,
                required=required,
                type_display=type_display,
                type_fidelity="normalized" if type_display is not None else "unavailable",
                default_kind=default_kind,
                default_value_state="not-applicable" if default_kind in {"missing", "factory"} else "omitted",
                default_value=None,
                description=description,
            )
        )
    return tuple(result)


def _is_classvar_annotation(annotation: object) -> bool:
    """Recognize ordinary and deferred ClassVar spellings without resolving them."""
    if annotation is typing.ClassVar or get_origin(annotation) is typing.ClassVar:
        return True
    if type(annotation) is not str:
        return False
    compact = cast("str", annotation).replace(" ", "")
    return compact in {"ClassVar", "typing.ClassVar"} or compact.startswith(("ClassVar[", "typing.ClassVar["))


def _plain_field_default(schema_class: type, name: str) -> object:
    """Read the nearest static class value for one merged annotation."""
    for candidate in _static_class_mro(schema_class):
        namespace = _static_class_dict(candidate)
        if name in namespace:
            return namespace[name]
    return MISSING


def _classify_default(default: object) -> tuple[Literal["missing", "value", "factory"], bool]:
    """Match dataclasses' default rules without calling a factory."""
    if default is MISSING:
        return "missing", True
    if type(default) is not Field:
        return "value", False
    field = cast("Field[object]", default)
    if field.default_factory is not MISSING:
        return "factory", False
    if field.default is not MISSING:
        return "value", False
    return "missing", True


def _field_description(field: Field[object]) -> str | None:
    """Copy a valid description from a plain class's dataclass field marker."""
    value = field.metadata.get("description")
    return value if type(value) is str and _is_utf8_string(value) else None


__all__: list[str] = []
