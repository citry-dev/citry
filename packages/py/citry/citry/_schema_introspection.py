"""Shared runtime adapter for component schema declarations."""

from __future__ import annotations

import dataclasses
import json
import math
import sys
import types
import typing
from collections.abc import Callable as AbcCallable
from collections.abc import Mapping as AbcMapping
from collections.abc import Sequence as AbcSequence
from dataclasses import MISSING, Field, is_dataclass
from pathlib import Path
from typing import Any, ForwardRef, Literal, NamedTuple, TypeVar, cast, get_args, get_origin

from citry._class_introspection import _safe_class_import_path, _safe_class_text, _static_class_dict, _static_class_mro
from citry._nested_declarations import _get_nested_class_declarations
from citry.introspection import (
    ComponentSchemas,
    FieldInfo,
    SchemaInfo,
    _freeze_json_value,
    _is_utf8_string,
    _UnsupportedJsonValue,
)

_SCHEMA_ROLES = {
    "kwargs": "Kwargs",
    "slots": "Slots",
    "template_data": "TemplateData",
    "js_data": "JsData",
    "css_data": "CssData",
}
_UNAVAILABLE = object()
_TYPE_VAR_TYPE = type(TypeVar("_SchemaType"))
_SAFE_TYPING_FORM_TYPES = (
    types.GenericAlias,
    types.UnionType,
    type(typing.List[int]),  # noqa: UP006 - sample the runtime type of typing aliases
    type(typing.Union[int, str]),  # noqa: UP007 - sample the runtime type of typing unions
    type(typing.Callable[[int], str]),
    type(AbcCallable[[int], str]),
    type(typing.Literal[1]),
    type(typing.Annotated[int, "metadata"]),
)


class _RawField(NamedTuple):
    """One adapter-neutral field before safe type and value conversion."""

    name: str
    required: bool
    annotation: object
    default_kind: Literal["missing", "value", "factory"]
    default_value: object
    description: str | None
    declaring_class: type | None


def _inspect_component_schemas(
    component_class: type,
    *,
    include_default_values: bool = False,
) -> ComponentSchemas:
    """Build all five effective schema records for one component class."""
    schemas = {
        role: _inspect_schema_role(component_class, attribute, include_default_values=include_default_values)
        for role, attribute in _SCHEMA_ROLES.items()
    }
    return ComponentSchemas(
        kwargs=schemas["kwargs"],
        slots=schemas["slots"],
        template_data=schemas["template_data"],
        js_data=schemas["js_data"],
        css_data=schemas["css_data"],
    )


def _inspect_schema_role(
    component_class: type,
    attribute: str,
    *,
    include_default_values: bool = False,
) -> SchemaInfo:
    """Inspect one effective schema while retaining its authored C3 provenance."""
    owner: type | None
    schema: object
    declarations = _get_nested_class_declarations(component_class, attribute)
    if declarations:
        owner = declarations[0].declaring_class
        authored = declarations[0].value
        schema = (
            _static_class_dict(component_class).get(attribute, authored) if isinstance(authored, type) else authored
        )
    else:
        owner = None
        schema = None
        for candidate in _static_class_mro(component_class):
            namespace = _static_class_dict(candidate)
            if attribute in namespace:
                owner = candidate
                schema = namespace[attribute]
                break

    if owner is None:
        return SchemaInfo(kind="absent", declared_on=None, import_path=None, fields=())

    # Component's own None-valued role attributes are framework defaults, not
    # user declarations. A None on every other MRO class is an explicit shadow.
    framework_default = _static_class_dict(owner).get("_citry_component_root", False) is True and schema is None
    declared_on = None if framework_default else _safe_class_import_path(owner)
    if schema is None:
        if not framework_default and declared_on is None:
            msg = f"Could not determine a safe import path for the owner of the {attribute} schema binding."
            raise TypeError(msg)
        return SchemaInfo(kind="absent", declared_on=declared_on, import_path=None, fields=())
    if not isinstance(schema, type):
        component_name = (
            _safe_class_import_path(component_class) or _safe_class_text(component_class, "__name__") or "Component"
        )
        msg = f"{component_name}.{attribute} must be a class or None before it can be inspected."
        raise TypeError(msg)

    import_path = _safe_class_import_path(schema)
    if declared_on is None or import_path is None:
        msg = f"Could not determine safe import paths for the {attribute} schema binding."
        raise TypeError(msg)
    inspected_fields = _inspect_schema_class(schema, include_default_values=include_default_values)
    if inspected_fields is None:
        return SchemaInfo(kind="opaque", declared_on=declared_on, import_path=import_path, fields=())
    return SchemaInfo(kind="fields", declared_on=declared_on, import_path=import_path, fields=inspected_fields)


def _inspect_schema_class(
    schema_class: object,
    *,
    include_default_values: bool = False,
) -> tuple[FieldInfo, ...] | None:
    """Return rich fields for a recognized schema class, or None if opaque."""
    raw_fields = _read_schema_fields(schema_class)
    if raw_fields is None:
        return None
    return tuple(_field_info(field, include_default_values=include_default_values) for field in raw_fields)


def _read_schema_fields(schema_class: object) -> tuple[_RawField, ...] | None:
    """Read adapter-neutral facts using the same protocol precedence as runtime validation."""
    if not isinstance(schema_class, type):
        return None
    if is_dataclass(schema_class):
        classvar_marker = dataclasses._FIELD_CLASSVAR  # type: ignore[attr-defined]
        declared_fields = cast("dict[str, Field[Any]]", schema_class.__dataclass_fields__)
        return tuple(
            _dataclass_field(schema_class, field)
            for field in declared_fields.values()
            if field.init and field._field_type is not classvar_marker  # type: ignore[attr-defined]
        )

    # Pydantic v2 is checked first because v2 also exposes a deprecated v1 alias.
    model_fields = getattr(schema_class, "model_fields", None)
    if isinstance(model_fields, dict):
        return tuple(_pydantic_v2_field(schema_class, name, info) for name, info in model_fields.items())

    v1_fields = getattr(schema_class, "__fields__", None)
    if isinstance(v1_fields, dict):
        return tuple(_pydantic_v1_field(schema_class, name, info) for name, info in v1_fields.items())

    if issubclass(schema_class, tuple) and hasattr(schema_class, "_fields"):
        return _named_tuple_fields(schema_class)
    return None


def _dataclass_field(schema_class: type, field: Field[Any]) -> _RawField:
    if field.default is MISSING and field.default_factory is MISSING:
        default_kind: Literal["missing", "value", "factory"] = "missing"
        default_value = _UNAVAILABLE
    elif field.default_factory is not MISSING:
        default_kind = "factory"
        default_value = _UNAVAILABLE
    else:
        default_kind = "value"
        default_value = field.default
    description_value = field.metadata.get("description")
    description = description_value if type(description_value) is str and _is_utf8_string(description_value) else None
    return _RawField(
        name=field.name,
        required=default_kind == "missing",
        annotation=field.type,
        default_kind=default_kind,
        default_value=default_value,
        description=description,
        declaring_class=_field_declaring_class(schema_class, field.name),
    )


def _pydantic_v2_field(schema_class: type, name: str, info: object) -> _RawField:
    required = bool(cast("Any", info).is_required())
    default_factory = getattr(info, "default_factory", None)
    if required:
        default_kind: Literal["missing", "value", "factory"] = "missing"
        default_value = _UNAVAILABLE
    elif default_factory is not None:
        default_kind = "factory"
        default_value = _UNAVAILABLE
    else:
        default_kind = "value"
        default_value = getattr(info, "default", _UNAVAILABLE)
    description_value = getattr(info, "description", None)
    description = description_value if type(description_value) is str and _is_utf8_string(description_value) else None
    return _RawField(
        name=name,
        required=required,
        annotation=getattr(info, "annotation", _UNAVAILABLE),
        default_kind=default_kind,
        default_value=default_value,
        description=description,
        declaring_class=_field_declaring_class(schema_class, name),
    )


def _pydantic_v1_field(schema_class: type, name: str, info: object) -> _RawField:
    required = bool(getattr(info, "required", False))
    default_factory = getattr(info, "default_factory", None)
    if required:
        default_kind: Literal["missing", "value", "factory"] = "missing"
        default_value = _UNAVAILABLE
    elif default_factory is not None:
        default_kind = "factory"
        default_value = _UNAVAILABLE
    else:
        default_kind = "value"
        default_value = getattr(info, "default", _UNAVAILABLE)
    field_info = getattr(info, "field_info", None)
    description_value = getattr(field_info, "description", None)
    description = description_value if type(description_value) is str and _is_utf8_string(description_value) else None
    return _RawField(
        name=name,
        required=required,
        annotation=getattr(info, "annotation", _UNAVAILABLE),
        default_kind=default_kind,
        default_value=default_value,
        description=description,
        declaring_class=_field_declaring_class(schema_class, name),
    )


def _named_tuple_fields(schema_class: type) -> tuple[_RawField, ...]:
    field_names = cast("tuple[str, ...]", cast("Any", schema_class)._fields)
    defaults = cast("dict[str, object]", getattr(schema_class, "_field_defaults", {}))
    annotations: dict[str, object] = {}
    for candidate in reversed(schema_class.__mro__):
        own_annotations = candidate.__dict__.get("__annotations__")
        if isinstance(own_annotations, dict):
            annotations.update(own_annotations)
    if any(name not in annotations for name in field_names):
        # Python 3.14 may defer a NamedTuple class's annotations behind an
        # annotation function. The generated __new__ retains raw ForwardRef
        # values across supported Python versions, so read its static metadata
        # instead of asking annotationlib to execute the annotation function.
        constructor_annotations: dict[str, object] = {}
        for candidate in reversed(schema_class.__mro__):
            if "_fields" not in candidate.__dict__:
                continue
            new_descriptor = candidate.__dict__.get("__new__")
            if type(new_descriptor) is staticmethod:
                new_annotations = new_descriptor.__func__.__annotations__
                if type(new_annotations) is dict:
                    constructor_annotations.update(new_annotations)
        annotations.update(
            (name, constructor_annotations[name])
            for name in field_names
            if name not in annotations and name in constructor_annotations
        )
    return tuple(
        _RawField(
            name=name,
            required=name not in defaults,
            annotation=annotations.get(name, _UNAVAILABLE),
            default_kind="missing" if name not in defaults else "value",
            default_value=defaults.get(name, _UNAVAILABLE),
            description=None,
            declaring_class=_field_declaring_class(schema_class, name),
        )
        for name in field_names
    )


def _field_info(field: _RawField, *, include_default_values: bool) -> FieldInfo:
    type_display = _format_annotation(field.annotation)
    if field.default_kind in {"missing", "factory"}:
        default_value_state: Literal["not-applicable", "omitted", "available", "unsupported"] = "not-applicable"
        default_value = None
    elif not include_default_values:
        default_value_state = "omitted"
        default_value = None
    else:
        try:
            default_value = _freeze_json_value(field.default_value)
        except _UnsupportedJsonValue:
            default_value_state = "unsupported"
            default_value = None
        else:
            default_value_state = "available"
    source_module, source_qualname, source_file = _field_source(field.declaring_class)
    return FieldInfo(
        name=field.name,
        required=field.required,
        type_display=type_display,
        type_fidelity="normalized" if type_display is not None else "unavailable",
        default_kind=field.default_kind,
        default_value_state=default_value_state,
        default_value=default_value,
        description=field.description,
        source_module=source_module,
        source_qualname=source_qualname,
        source_file=source_file,
    )


def _field_source(owner: type | None) -> tuple[str | None, str | None, Path | None]:
    """Return provenance atomically, or no provenance when identity is unsafe."""
    if owner is None:
        return None, None, None
    module = _safe_class_text(owner, "__module__")
    qualname = _safe_class_text(owner, "__qualname__")
    if module is None or qualname is None:
        return None, None, None
    return module, qualname, _loaded_python_file(owner)


def _field_declaring_class(schema_class: type, name: str) -> type | None:
    """Find the nearest authored class whose own declaration defines ``name``."""
    for candidate in _static_class_mro(schema_class):
        namespace = _static_class_dict(candidate)
        if namespace.get("_citry_synthesized_declaration", False) is True:
            continue
        annotations = namespace.get("__annotations__")
        if isinstance(annotations, dict) and name in annotations:
            return candidate
        own_fields = namespace.get("_fields")
        if type(own_fields) is tuple and name in own_fields:
            return candidate
    return None


def _loaded_python_file(cls: type) -> Path | None:
    """Return an already-loaded authoring module path without importing it."""
    module_name = _safe_class_text(cls, "__module__")
    if module_name is None:
        return None
    module = sys.modules.get(module_name)
    # Read the concrete module namespace so a module-level ``__getattr__``
    # cannot execute user code during introspection.
    module_file = module.__dict__.get("__file__") if type(module) is types.ModuleType else None
    if (
        type(module_file) is not str
        or not module_file
        or not _is_utf8_string(module_file)
        or (module_file.startswith("<") and module_file.endswith(">"))
    ):
        return None
    path = Path(module_file)
    return path if path.is_absolute() else path.absolute()


def _format_annotation(annotation: object) -> str | None:
    """Format one annotation through Citry's deliberately small safe vocabulary."""
    try:
        return _format_annotation_inner(annotation, set())
    except RecursionError:
        return None


def _format_annotation_inner(annotation: object, active: set[int]) -> str | None:
    annotation_type = type(annotation)
    if annotation_type is str:
        string_annotation = cast("str", annotation)
        return string_annotation if string_annotation and _is_utf8_string(string_annotation) else None
    if annotation is None or annotation is type(None):
        return "None"
    if annotation is Any:
        return "Any"
    if annotation is Ellipsis:
        return "..."
    if annotation_type is ForwardRef:
        name = cast("ForwardRef", annotation).__forward_arg__
        return name if type(name) is str and name and _is_utf8_string(name) else None
    if annotation_type is _TYPE_VAR_TYPE:
        name = cast("Any", annotation).__name__
        return name if type(name) is str and name and _is_utf8_string(name) else None

    is_typing_form = any(annotation_type is safe_type for safe_type in _SAFE_TYPING_FORM_TYPES)
    if not is_typing_form:
        if issubclass(annotation_type, type):
            return _safe_class_import_path(cast("type", annotation))
        return None

    identity = id(annotation)
    if identity in active:
        return None
    active.add(identity)
    try:
        try:
            origin = get_origin(annotation)
            arguments = get_args(annotation)
        except Exception:  # noqa: BLE001 - unsafe typing protocols are unavailable
            return None
        if type(arguments) is not tuple:
            return None
        if origin is typing.Annotated:
            return _format_annotation_inner(arguments[0], active) if arguments else None
        if origin is typing.Literal:
            if not arguments:
                return None
            values = [_format_literal(value) for value in arguments]
            if any(value is None for value in values):
                return None
            return f"Literal[{', '.join(cast('list[str]', values))}]"
        if origin is typing.Union or origin is types.UnionType:
            if not arguments:
                return None
            values = [_format_annotation_inner(value, active) for value in arguments]
            if any(value is None for value in values):
                return None
            return " | ".join(cast("list[str]", values))
        if origin is AbcCallable:
            return _format_callable(arguments, active)

        labels = (
            (list, "list"),
            (tuple, "tuple"),
            (dict, "dict"),
            (set, "set"),
            (frozenset, "frozenset"),
            (type, "type"),
            (AbcSequence, "Sequence"),
            (AbcMapping, "Mapping"),
        )
        label = next((value for expected_origin, value in labels if origin is expected_origin), None)
        if label is None or not arguments:
            return None
        values = [_format_annotation_inner(value, active) for value in arguments]
        if any(value is None for value in values):
            return None
        return f"{label}[{', '.join(cast('list[str]', values))}]"
    finally:
        active.remove(identity)


def _format_callable(arguments: tuple[object, ...], active: set[int]) -> str | None:
    if len(arguments) != 2:
        return None
    parameters, returns = arguments
    return_value = _format_annotation_inner(returns, active)
    if return_value is None:
        return None
    if parameters is Ellipsis:
        return f"Callable[..., {return_value}]"
    if type(parameters) is not list:
        return None
    parameter_values = [_format_annotation_inner(parameter, active) for parameter in parameters]
    if any(value is None for value in parameter_values):
        return None
    return f"Callable[[{', '.join(cast('list[str]', parameter_values))}], {return_value}]"


def _format_literal(value: object) -> str | None:
    if value is None:
        return "None"
    if type(value) is bool:
        return "True" if value else "False"
    if type(value) is int:
        return str(value)
    if type(value) is float:
        return repr(value) if math.isfinite(value) else None
    if type(value) is str:
        return json.dumps(value, ensure_ascii=False) if _is_utf8_string(value) else None
    return None


__all__: list[str] = []
