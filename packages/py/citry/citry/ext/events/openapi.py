"""
The OpenAPI command of the ``events`` extension (design
``docs/design/events.md`` section 9).

``citry ext run events openapi`` walks the engine's registered components
and emits an OpenAPI 3.1 document with one operation per (component, event
handler) pair, addressed over the per-event route
(``ext/events/e/{class_id}/{event}``). The request side comes from the
handler's ``data`` schema (a named ``components/schemas`` entry; query
parameters for GET handlers), the 422 response is the per-field error
envelope, and the 200 response is typed from the handler's return
annotation when that annotation is a JSON data value. Non-GET operations
also document the required ``X-Citry-Events`` header (the CSRF layer
rejects JSON calls without it). The document derives from the same handler
records that power dispatch, so it cannot drift from what the server
validates.

The output is deterministic: components, operations, and the named schemas
are sorted, so the emitted document is diffable and cache-friendly.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from dataclasses import MISSING, fields
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from inspect import getdoc
from pathlib import Path
from types import UnionType
from typing import TYPE_CHECKING, Any, NamedTuple, Union, cast, get_args, get_origin, get_type_hints
from uuid import UUID

from citry.command import CommandArg, style_success
from citry.ext.events.csrf import X_CITRY_EVENTS_HEADER
from citry.ext.events.dispatcher import PROTOCOL
from citry.ext.events.files import UploadedFile
from citry.ext.events.handlers import _is_schema_class
from citry.ext.events.routes import EVENT_PATH
from citry.ext.events.schemas import convert_schema_class
from citry.extension import ExtensionCommand

# Pydantic is optional here exactly as in the schema layer: a Pydantic-model
# schema delegates its JSON Schema to Pydantic; without Pydantic installed no
# such schema can exist.
try:
    import pydantic
except ImportError:  # pragma: no cover - exercised via the tests' None patch
    pydantic = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry.citry import Citry
    from citry.component import Component
    from citry.ext.events.extension import EventHandler, EventsExtension

__all__ = [
    "OpenApiCommand",
]

_REF_PREFIX = "#/components/schemas/"


################################################
# NAMED SCHEMAS
################################################


class _SchemaRegistry:
    """
    The named schemas of one document build (the ``components/schemas`` map).

    Schema classes register under their class name; a second, different
    class with the same name gets a numbered name, so one build never emits
    two meanings for one name. Registration order follows the sorted
    operation walk, so the numbering is deterministic.
    """

    def __init__(self) -> None:
        self._names_by_class: dict[type, str] = {}
        self._schemas: dict[str, dict[str, Any]] = {}

    def reserve(self, name: str, schema: dict[str, Any]) -> None:
        """Claim a fixed name (the error shapes) before any class can take it."""
        self._schemas[name] = schema

    def ref(self, cls: type) -> dict[str, Any]:
        """The ``$ref`` object pointing at ``cls``, registering it on first use."""
        return {"$ref": _REF_PREFIX + self.register(cls)}

    def register(self, cls: type) -> str:
        """The document name of ``cls``, building and storing its schema on first use."""
        if cls in self._names_by_class:
            return self._names_by_class[cls]
        name = self._claim(cls.__name__)
        self._names_by_class[cls] = name
        # The name is stored before the schema is built, so a schema whose
        # fields point back at it resolves to its own $ref instead of
        # recursing forever.
        self._schemas[name] = {}
        self._schemas[name] = self._build(cls)
        return name

    def schema_of(self, cls: type) -> dict[str, Any]:
        """The full named schema of ``cls`` (registering it on first use)."""
        return self._schemas[self.register(cls)]

    def as_sorted(self) -> dict[str, dict[str, Any]]:
        """The ``components/schemas`` map, sorted by name."""
        return {name: self._schemas[name] for name in sorted(self._schemas)}

    def _claim(self, base: str) -> str:
        """The first free name for ``base``: the bare name, else ``base_2``, ``base_3``, ..."""
        if base not in self._schemas:
            return base
        counter = 2
        while f"{base}_{counter}" in self._schemas:
            counter += 1
        return f"{base}_{counter}"

    def _build(self, cls: type) -> dict[str, Any]:
        """One class's JSON Schema: enums by value, Pydantic wholesale, else the field walk."""
        if issubclass(cls, Enum):
            return _enum_schema(cls)
        if _is_pydantic_model(cls):
            return self._pydantic_schema(cls)
        return _object_schema(cls, self)

    def _pydantic_schema(self, cls: type) -> dict[str, Any]:
        """
        Delegate a Pydantic model to Pydantic's own JSON Schema generator.

        Nested models arrive as ``$defs``; they are lifted into the document's
        ``components/schemas`` under the names Pydantic baked into the refs,
        so those names cannot be renamed away from a clash. A clash with a
        different schema is answered with a pointed error instead of a
        document that silently means two things by one name.
        """
        template = _REF_PREFIX + "{model}"
        if hasattr(cls, "model_json_schema"):
            schema = cls.model_json_schema(ref_template=template)
            nested = schema.pop("$defs", {})
        else:  # Pydantic v1 spells both the method and the nested-schema key differently.
            schema = cls.schema(ref_template=template)  # type: ignore[attr-defined]
            nested = schema.pop("definitions", {})
        for nested_name in sorted(nested):
            existing = self._schemas.get(nested_name)
            if existing is None:
                self._schemas[nested_name] = nested[nested_name]
            elif existing != nested[nested_name]:
                msg = (
                    f"Two different schemas want the name {nested_name!r} in components/schemas"
                    f" (a Pydantic nested model clashes with another schema class). Rename one of"
                    f" the classes so the document has one meaning per name."
                )
                raise ValueError(msg)
        return cast("dict[str, Any]", schema)


class _FieldSpec(NamedTuple):
    """One schema field: its name, resolved annotation, and required-ness."""

    name: str
    annotation: Any
    required: bool


def _field_specs(schema_cls: type) -> tuple[_FieldSpec, ...]:
    """
    The wire fields of a non-Pydantic schema class.

    Follows the validator's own field rules (``schemas.py``): the class is
    run through the same dataclass conversion, ``field(init=False)`` fields
    cannot come from the wire so they are omitted, and a field is required
    exactly when it has neither a default nor a default factory.
    """
    converted = convert_schema_class(schema_cls)
    hints = get_type_hints(converted)
    return tuple(
        _FieldSpec(
            name=field.name,
            annotation=hints.get(field.name, Any),
            required=field.default is MISSING and field.default_factory is MISSING,
        )
        for field in fields(converted)
        if field.init
    )


def _object_schema(schema_cls: type, registry: _SchemaRegistry) -> dict[str, Any]:
    """An annotated class or dataclass as a JSON Schema object."""
    properties: dict[str, Any] = {}
    required: list[str] = []
    for spec in _field_specs(schema_cls):
        properties[spec.name] = _annotation_to_schema(spec.annotation, registry)
        if spec.required:
            required.append(spec.name)
    # additionalProperties: false is the validator's behavior: an undeclared
    # field is a per-field 422 error, never silently accepted.
    schema: dict[str, Any] = {"type": "object", "properties": properties, "additionalProperties": False}
    if required:
        schema["required"] = required
    return schema


def _enum_schema(enum_cls: type[Enum]) -> dict[str, Any]:
    """An Enum as a JSON Schema: its values, typed when they are all strings or all ints."""
    values = [member.value for member in enum_cls]
    schema: dict[str, Any] = {}
    if all(isinstance(value, str) for value in values):
        schema["type"] = "string"
    elif all(isinstance(value, int) and not isinstance(value, bool) for value in values):
        schema["type"] = "integer"
    schema["enum"] = values
    return schema


def _is_pydantic_model(cls: type) -> bool:
    """Whether ``cls`` is a Pydantic model (always ``False`` without Pydantic installed)."""
    return pydantic is not None and isinstance(cls, type) and issubclass(cls, pydantic.BaseModel)


################################################
# ANNOTATION CONVERSION
################################################


def _annotation_to_schema(annotation: Any, registry: _SchemaRegistry) -> dict[str, Any]:
    """
    One field annotation as a JSON Schema.

    Mirrors the validator's coercion table (``schemas.py``): the string-fed
    types (UUID, datetime, date, time, Decimal, Enum) document as strings
    with formats, containers recurse, unions become ``anyOf``, and a nested
    schema class becomes a named ``$ref``. Anything the table does not know
    documents as the empty schema (anything goes) rather than guessing.
    """
    if annotation is Any or annotation is object:
        return {}

    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        return {"anyOf": [_annotation_to_schema(member, registry) for member in get_args(annotation)]}
    if origin in (list, set, tuple, dict, Mapping):
        return _container_schema(annotation, origin, registry)
    if origin is not None:
        return {}

    if annotation is type(None):
        return {"type": "null"}
    if not isinstance(annotation, type):
        return {}

    # The four JSON primitives, by identity, so an Enum or user subclass
    # documents by its own rule below (mirroring the validator).
    if annotation is bool:
        return {"type": "boolean"}
    if annotation is int:
        return {"type": "integer"}
    if annotation is float:
        return {"type": "number"}
    if annotation is str:
        return {"type": "string"}
    if annotation is list or annotation is tuple:
        return {"type": "array"}
    if annotation is set:
        return {"type": "array", "uniqueItems": True}
    if annotation is dict or annotation is Mapping:
        return {"type": "object"}

    if issubclass(annotation, Enum):
        return registry.ref(annotation)
    if issubclass(annotation, UUID):
        return {"type": "string", "format": "uuid"}
    # datetime before date: datetime subclasses date.
    if issubclass(annotation, datetime):
        return {"type": "string", "format": "date-time"}
    if issubclass(annotation, date):
        return {"type": "string", "format": "date"}
    if issubclass(annotation, time):
        return {"type": "string", "format": "time"}
    if issubclass(annotation, Decimal):
        # The validator takes Decimals from strings only, never JSON floats.
        return {"type": "string", "format": "decimal"}
    if issubclass(annotation, UploadedFile):
        return {"type": "string", "format": "binary"}
    if _is_pydantic_model(annotation) or _is_schema_class(annotation):
        return registry.ref(annotation)
    return {}


def _container_schema(annotation: Any, origin: type, registry: _SchemaRegistry) -> dict[str, Any]:
    """A parametrized list / set / tuple / dict annotation as a JSON Schema."""
    args = get_args(annotation)
    if origin is dict or origin is Mapping:
        # JSON object keys are strings; only the value type documents.
        return {"type": "object", "additionalProperties": _annotation_to_schema(args[1], registry)}
    if origin is set:
        return {"type": "array", "items": _annotation_to_schema(args[0], registry), "uniqueItems": True}
    if origin is tuple and not (len(args) == 2 and args[1] is Ellipsis):
        # A fixed-shape tuple documents per position, like the validator coerces it.
        return {
            "type": "array",
            "prefixItems": [_annotation_to_schema(member, registry) for member in args],
            "minItems": len(args),
            "maxItems": len(args),
        }
    return {"type": "array", "items": _annotation_to_schema(args[0], registry)}


################################################
# RETURN ANNOTATIONS (THE DATA RESPONSES)
################################################


def _return_annotation(comp_cls: type, func: Callable[..., Any]) -> Any:
    """
    Resolve a handler's return annotation, or ``None`` when it has none.

    Resolution uses the same rescue namespace as the ``data`` annotation
    (the component's nested classes and MRO names), but never raises: return
    annotations are advisory (dispatch never needs them), so one that does
    not resolve simply leaves the operation without a typed response.
    """
    annotations = getattr(func, "__annotations__", {})
    if "return" not in annotations:
        return None

    localns: dict[str, Any] = {}
    for klass in reversed(comp_cls.__mro__):
        localns[klass.__name__] = klass
        localns.update({name: nested for name, nested in vars(klass).items() if isinstance(nested, type)})

    def probe() -> None: ...

    probe.__annotations__ = {"return": annotations["return"]}
    try:
        return get_type_hints(probe, globalns=getattr(func, "__globals__", None), localns=localns).get("return")
    except (NameError, TypeError):
        return None


def _is_data_annotation(annotation: Any) -> bool:
    """
    Whether a return annotation is a JSON data value (design 9's "JSON-able").

    Dict shapes are the return channel's built-in data coercion; schema-shaped
    classes (annotated classes, dataclasses, Pydantic models) are the shapes
    result resolvers answer with. Actions, elements, strings, and bare
    scalars are not data. ``None`` union members are dropped: returning
    ``None`` acknowledges the call instead of answering data.
    """
    if annotation is None or annotation is type(None):
        return False
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        members = [member for member in get_args(annotation) if member is not type(None)]
        return bool(members) and all(_is_data_annotation(member) for member in members)
    if origin in (dict, Mapping) or annotation is dict or annotation is Mapping:
        return True
    if not isinstance(annotation, type) or issubclass(annotation, Enum):
        return False
    return _is_pydantic_model(annotation) or _is_schema_class(annotation)


def _data_response_schema(annotation: Any, registry: _SchemaRegistry) -> dict[str, Any]:
    """The 200 schema of a data-typed return annotation (checked by ``_is_data_annotation``)."""
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        members = [member for member in get_args(annotation) if member is not type(None)]
        if len(members) == 1:
            return _data_response_schema(members[0], registry)
        return {"anyOf": [_data_response_schema(member, registry) for member in members]}
    if origin in (dict, Mapping) or annotation is dict or annotation is Mapping:
        return _annotation_to_schema(annotation, registry)
    return registry.ref(annotation)


################################################
# THE DOCUMENT
################################################


def _event_error_schema() -> dict[str, Any]:
    """The error object of a failed call: status, code, message, and the per-field map."""
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


def _event_error_envelope_schema() -> dict[str, Any]:
    """The result envelope of a failed call, as the per-event route answers it."""
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
                        "error": {"$ref": _REF_PREFIX + "EventError"},
                    },
                    "required": ["ok", "error"],
                },
            },
        },
        "required": ["protocol", "requestId", "results"],
    }


def _claim_operation_id(used: set[str], base: str) -> str:
    """A unique operationId: the bare ``Component_event``, numbered on a clash."""
    operation_id = base
    counter = 2
    while operation_id in used:
        operation_id = f"{base}_{counter}"
        counter += 1
    used.add(operation_id)
    return operation_id


def _query_parameters(schema_cls: type, registry: _SchemaRegistry) -> list[dict[str, Any]]:
    """One query parameter per data-schema field (GET carries its args in the query string)."""
    schema = registry.schema_of(schema_cls)
    required = set(schema.get("required", ()))
    return [
        {"name": name, "in": "query", "required": name in required, "schema": property_schema}
        for name, property_schema in schema.get("properties", {}).items()
    ]


def _build_operation(
    comp_cls: type[Component],
    handler: EventHandler,
    registry: _SchemaRegistry,
    used_operation_ids: set[str],
    *,
    annotation: Any,
    data_typed: bool,
) -> dict[str, Any]:
    """One (component, event) pair as an OpenAPI operation object."""
    operation: dict[str, Any] = {
        "operationId": _claim_operation_id(used_operation_ids, f"{comp_cls.__name__}_{handler.name}")
    }
    description = getdoc(handler.func)
    if description:
        operation["description"] = description

    if handler.methods[0] == "GET":
        if handler.data_schema is not None:
            parameters = _query_parameters(handler.data_schema, registry)
            if parameters:
                operation["parameters"] = parameters
    else:
        # The CSRF layer rejects any JSON-bodied call that does not send the
        # X-Citry-Events header (design 7.4), so document the header as
        # required: a client generated from this document then sends it and
        # its first call passes the check. GET handlers are exempt.
        operation["parameters"] = [
            {
                "name": X_CITRY_EVENTS_HEADER,
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": (
                    "CSRF protection of the events endpoints: JSON requests without this header"
                    ' are rejected with 403. Any value passes; the citry runtime sends "1".'
                ),
            }
        ]
        if handler.data_schema is not None:
            # A JSON body on the per-event route is the flat data schema (the
            # call envelope rides its own application/citry-events+json vendor
            # type, so the two shapes never collide); the form content type is
            # the no-JS path carrying the same fields.
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {"schema": registry.ref(handler.data_schema)},
                    "application/x-www-form-urlencoded": {"schema": registry.ref(handler.data_schema)},
                },
            }

    responses: dict[str, Any] = {}
    if data_typed:
        responses["200"] = {
            "description": (
                "The handler's data value (citry-events/1 envelope callers receive it as the result's data action)."
            ),
            "content": {"application/json": {"schema": _data_response_schema(annotation, registry)}},
        }
    else:
        responses["200"] = {"description": "The citry-events/1 result envelope."}
    responses["422"] = {
        "description": "The args did not validate; per-field messages ride in results[0].error.fieldErrors.",
        "content": {"application/json": {"schema": {"$ref": _REF_PREFIX + "EventErrorEnvelope"}}},
    }
    operation["responses"] = responses
    return operation


def build_openapi_document(citry: Citry, *, only_data: bool = False) -> dict[str, Any]:
    """
    Build the OpenAPI 3.1 document of the engine's event handlers.

    Walks the registered components that declare event handlers and emits
    one operation per (component, event) pair over the per-event route, with
    ``operationId`` ``<ComponentName>_<event>``. The request side comes from
    the handler's ``data`` schema (a named ``components/schemas`` entry, or
    query parameters for a GET handler), non-GET operations document the
    required ``X-Citry-Events`` header (the CSRF layer rejects JSON calls
    without it), every operation carries the 422 per-field error response,
    and handlers whose return annotation is a JSON data value get a typed
    200. Handler docstrings become the operation
    descriptions. Paths are relative to the prefix the citry routes are
    mounted under. Components, operations, and schemas are sorted, so the
    document is deterministic.

    Args:
        citry: The engine whose registered components are walked.
        only_data: Keep only the handlers with a JSON-typed return (the
            data API surface); everything else is dropped from the document.

    Returns:
        The OpenAPI document, as a JSON-ready dict.

    Example:
        ```python
        import json
        from citry.ext.events.openapi import build_openapi_document

        document = build_openapi_document(citry)
        print(json.dumps(document, indent=2))
        ```

    """
    extension = cast("EventsExtension", citry.extensions.get_extension("events"))

    declaring: list[type[Component]] = []
    seen: set[type[Component]] = set()
    for comp_cls in citry.components.values():
        # The registry maps names to classes and one class may hold several
        # names; the document describes classes, so each appears once.
        if comp_cls in seen:
            continue
        seen.add(comp_cls)
        if extension.resolve(comp_cls).handlers:
            declaring.append(comp_cls)
    declaring.sort(key=lambda cls: (cls.__name__, cls.class_id))

    registry = _SchemaRegistry()
    registry.reserve("EventError", _event_error_schema())
    registry.reserve("EventErrorEnvelope", _event_error_envelope_schema())

    paths: dict[str, dict[str, Any]] = {}
    used_operation_ids: set[str] = set()
    for comp_cls in declaring:
        info = extension.resolve(comp_cls)
        for event_name in sorted(info.handlers):
            handler = info.handlers[event_name]
            annotation = _return_annotation(comp_cls, handler.func)
            data_typed = _is_data_annotation(annotation)
            if only_data and not data_typed:
                continue
            operation = _build_operation(
                comp_cls,
                handler,
                registry,
                used_operation_ids,
                annotation=annotation,
                data_typed=data_typed,
            )
            path = "/" + EVENT_PATH.format(class_id=comp_cls.class_id, event=event_name)
            # One operation per pair, under the handler's primary method.
            paths.setdefault(path, {})[handler.methods[0].lower()] = operation

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Citry events",
            "version": PROTOCOL,
            "description": (
                "One operation per component event handler, dispatched over the per-event route."
                ' Paths are relative to the prefix the citry routes are mounted under (for example "/citry").'
            ),
        },
        "paths": paths,
        # The error shapes only mean something next to operations; an app
        # with no event handlers gets a clean empty document.
        "components": {"schemas": registry.as_sorted() if paths else {}},
    }


################################################
# THE COMMAND
################################################


class OpenApiCommand(ExtensionCommand):
    """
    The ``citry ext run events openapi`` command.

    Emits an OpenAPI 3.1 document for the engine the CLI runs against, to
    stdout or to ``--out <file>``.
    ``--only-data`` keeps only the handlers with a JSON-typed return (the
    data API surface).
    """

    name = "openapi"
    help = "Emit the OpenAPI 3.1 document of the registered event handlers."
    arguments = (
        CommandArg(
            name_or_flags=["--out"],
            help="Write the document to this file instead of stdout.",
        ),
        CommandArg(
            name_or_flags=["--only-data"],
            action="store_true",
            help="Only the handlers whose return annotation is a JSON data value (the data API surface).",
        ),
    )

    def handle(self, **kwargs: Any) -> None:
        """Build the document for the bound engine and write it to ``--out`` or stdout."""
        if self.citry is None:
            message = (
                "The openapi command needs an engine; run it through the citry CLI (citry ext run events openapi)."
            )
            print(message, file=sys.stderr)  # noqa: T201 - CLI commands talk through stdout/stderr
            # Exit 1 like the sibling commands' failure paths, so a scripted
            # run does not read "nothing was written" as success.
            raise SystemExit(1)
        document = build_openapi_document(self.citry, only_data=bool(kwargs.get("only_data")))
        text = json.dumps(document, indent=2)
        out = kwargs.get("out")
        if out:
            Path(out).write_text(text + "\n", encoding="utf-8")
            print(style_success(f"Wrote the OpenAPI document to {out}."))  # noqa: T201 - CLI output
        else:
            print(text)  # noqa: T201 - the document itself, to stdout
