"""Portable, conservative Python-to-JSON type descriptions for editor tools."""

from __future__ import annotations

import ast
import json
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from collections.abc import Mapping

JsonWireKind = Literal["unknown", "null", "boolean", "number", "string", "array", "object", "union"]


@dataclass(frozen=True, slots=True)
class JsonWireField:
    """One named property of a JSON object type."""

    name: str
    value: JsonWireType
    required: bool = True


@dataclass(frozen=True, slots=True)
class JsonWireType:
    """An editor-neutral JSON value type with conservative issue metadata."""

    kind: JsonWireKind
    items: tuple[JsonWireType, ...] = ()
    fields: tuple[JsonWireField, ...] = ()
    additional: JsonWireType | None = None
    literal: object | None = None
    unsupported: tuple[str, ...] = ()

    @property
    def javascript(self) -> str:
        """Render a JSDoc-compatible type without exposing Python spellings."""
        return self.render()

    def render(self, *, unknown: str = "unknown") -> str:
        """
        Render a JSDoc-compatible type, spelling each unproven part as `unknown`.

        A type checker must not report errors about a value Citry could not
        type, so the editor's projections pass `unknown="any"`.
        """
        if self.kind == "null":
            return "null"
        if self.kind in {"boolean", "number", "string"}:
            if self.literal is not None:
                return json.dumps(self.literal, ensure_ascii=False)
            return self.kind
        if self.kind == "array":
            item = merge_json_wire_types(self.items).render(unknown=unknown) if self.items else unknown
            return f"Array<{item}>"
        if self.kind == "object":
            members = [
                f"{_js_property(field.name)}{'?' if not field.required else ''}: {field.value.render(unknown=unknown)}"
                for field in self.fields
            ]
            if self.additional is not None:
                members.append(f"[key: string]: {self.additional.render(unknown=unknown)}")
            return "{" + ", ".join(members) + "}" if members else f"Record<string, {unknown}>"
        if self.kind == "union":
            rendered = tuple(dict.fromkeys(item.render(unknown=unknown) for item in self.items))
            return " | ".join(rendered) if rendered else unknown
        return unknown

    @property
    def display(self) -> str:
        """Use the same concise vocabulary in hovers and diagnostics."""
        return self.javascript


UNKNOWN_JSON_TYPE = JsonWireType("unknown")

# A JSON scalar an Enum member value may be, so `.value` can type as its literals.
_ENUM_VALUE_TYPES = (bool, int, float, str)

# How a class's instances behave once they reach a data method:
# "object" instances are read by attribute and rejected by the JSON wire;
# "named-tuple" instances are read by attribute and sent as arrays;
# "typed-dict" values are plain dicts, so they are sent as objects but have
# no attributes to read; "enum" members carry only `.value` and `.name`.
WireClassKind = Literal["object", "named-tuple", "typed-dict", "enum"]
_WIRE_CLASS_KINDS = frozenset({"object", "named-tuple", "typed-dict", "enum"})


@dataclass(frozen=True, slots=True)
class WireClass:
    """
    The attribute annotations of one Python class that a data method reads through.

    A ``js_data()`` value such as ``kwargs.task.lane`` reads ``lane`` from the
    class of ``kwargs.task``. Each annotation is written the way Citry formats
    a schema field's type, so a class annotation is its import path and can
    itself be looked up in the same class table.

    Attributes:
        attributes: Each public attribute's annotation, or ``None`` when it
            could not be resolved to a type.
        kind: How the class's instances are read and sent; see ``WireClassKind``.
        required: The keys a TypedDict always has, else ``None``.
        enum_values: Every member's value when the class is an ``Enum`` whose
            values are all JSON scalars, else ``None``.
        enum_names: Every member's name when the class is an ``Enum``, else ``None``.

    """

    attributes: Mapping[str, str | None]
    kind: WireClassKind = "object"
    required: tuple[str, ...] | None = None
    enum_values: tuple[bool | int | float | str | None, ...] | None = None
    enum_names: tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready copy for the language server's worker payload."""
        return {
            "attributes": dict(self.attributes),
            "kind": self.kind,
            "required": None if self.required is None else list(self.required),
            "enum_values": None if self.enum_values is None else list(self.enum_values),
            "enum_names": None if self.enum_names is None else list(self.enum_names),
        }

    @classmethod
    def from_dict(cls, value: object) -> WireClass:
        """Validate and restore one copied class record."""
        if type(value) is not dict or set(value) != {"attributes", "kind", "required", "enum_values", "enum_names"}:
            msg = "wire class data must contain the exact supported fields"
            raise ValueError(msg)
        attributes = value["attributes"]
        if type(attributes) is not dict or any(
            type(name) is not str or (annotation is not None and type(annotation) is not str)
            for name, annotation in attributes.items()
        ):
            msg = "wire class attributes must map names to annotations"
            raise ValueError(msg)
        kind = value["kind"]
        if type(kind) is not str or kind not in _WIRE_CLASS_KINDS:
            msg = "wire class kind is not supported"
            raise ValueError(msg)
        required = value["required"]
        if required is not None and (type(required) is not list or any(type(item) is not str for item in required)):
            msg = "wire class required keys must be strings"
            raise ValueError(msg)
        enum_values = value["enum_values"]
        if enum_values is not None and (
            type(enum_values) is not list
            or any(item is not None and type(item) not in _ENUM_VALUE_TYPES for item in enum_values)
            or any(type(item) is float and not math.isfinite(item) for item in enum_values)
        ):
            msg = "wire class enum values must be JSON scalars"
            raise ValueError(msg)
        enum_names = value["enum_names"]
        if enum_names is not None and (
            type(enum_names) is not list or any(type(item) is not str for item in enum_names)
        ):
            msg = "wire class enum names must be strings"
            raise ValueError(msg)
        return cls(
            attributes=dict(attributes),
            kind=cast("WireClassKind", kind),
            required=None if required is None else tuple(required),
            enum_values=None if enum_values is None else tuple(enum_values),
            enum_names=None if enum_names is None else tuple(enum_names),
        )


def json_wire_type_from_annotation(source: str) -> JsonWireType:
    """Convert one Python annotation expression into a JSON wire type."""
    try:
        expression = ast.parse(source, mode="eval").body
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return _unsupported("the annotation cannot be analyzed as a strict JSON type")
    return _annotation_type(expression)


def json_wire_type_from_expression(
    source: str,
    *,
    member_types: Mapping[str, Mapping[str, JsonWireType]] | None = None,
    member_annotations: Mapping[str, Mapping[str, str | None]] | None = None,
    classes: Mapping[str, WireClass] | None = None,
) -> JsonWireType:
    """
    Infer JSON shape from a Python value expression and proven members.

    ``member_types`` types ``name.attr`` directly, such as ``kwargs.title``.
    ``member_annotations`` gives the same members' annotations, and
    ``classes`` describes the classes those annotations name, so a longer
    chain such as ``kwargs.task.lane`` follows each class's attribute
    annotations. A chain through a class the table does not describe, or
    through an optional value, stays unknown.
    """
    try:
        expression = ast.parse(source, mode="eval").body
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return UNKNOWN_JSON_TYPE
    context = _ExpressionContext(member_types or {}, member_annotations or {}, classes or {})
    return _expression_type(expression, context)


def merge_json_wire_types(values: tuple[JsonWireType, ...] | list[JsonWireType]) -> JsonWireType:
    """Join JSON types without claiming agreement that was not proven."""
    flattened: list[JsonWireType] = []
    issues: list[str] = []
    for value in values:
        issues.extend(value.unsupported)
        candidates = value.items if value.kind == "union" else (value,)
        for candidate in candidates:
            if candidate not in flattened:
                flattened.append(candidate)
    if not flattened:
        return UNKNOWN_JSON_TYPE
    if any(value.kind == "unknown" for value in flattened):
        return JsonWireType("unknown", unsupported=tuple(dict.fromkeys(issues)))
    if len(flattened) == 1:
        value = flattened[0]
        return JsonWireType(
            value.kind,
            value.items,
            value.fields,
            value.additional,
            value.literal,
            tuple(dict.fromkeys((*value.unsupported, *issues))),
        )
    return JsonWireType("union", tuple(flattened), unsupported=tuple(dict.fromkeys(issues)))


def _annotation_type(node: ast.expr) -> JsonWireType:
    if isinstance(node, ast.Constant):
        if node.value is None:
            return JsonWireType("null")
        if type(node.value) is str:
            try:
                nested = ast.parse(node.value, mode="eval").body
            except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
                return UNKNOWN_JSON_TYPE
            return _annotation_type(nested)
        rendered = ast.unparse(node)
        return _unsupported(f"{rendered} does not describe a supported strict JSON container")
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return merge_json_wire_types((_annotation_type(node.left), _annotation_type(node.right)))
    if isinstance(node, ast.Subscript):
        name = _qualified_name(node.value)
        arguments = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
        if name in {
            "Annotated",
            "typing.Annotated",
            "Required",
            "NotRequired",
            "typing.Required",
            "typing.NotRequired",
        }:
            return _annotation_type(arguments[0]) if arguments else UNKNOWN_JSON_TYPE
        if name in {"Optional", "typing.Optional"}:
            inner = _annotation_type(arguments[0]) if arguments else UNKNOWN_JSON_TYPE
            return merge_json_wire_types((inner, JsonWireType("null")))
        if name in {"Union", "typing.Union"}:
            return merge_json_wire_types(tuple(_annotation_type(argument) for argument in arguments))
        if name in {"Literal", "typing.Literal"}:
            return merge_json_wire_types(tuple(_literal_type(argument) for argument in arguments))
        if name in {
            "list",
            "List",
            "typing.List",
            "Sequence",
            "typing.Sequence",
            "collections.abc.Sequence",
        }:
            item = _annotation_type(arguments[0]) if arguments else UNKNOWN_JSON_TYPE
            return JsonWireType("array", (item,), unsupported=item.unsupported)
        if name in {"tuple", "Tuple", "typing.Tuple"}:
            retained = [
                argument
                for argument in arguments
                if not isinstance(argument, ast.Constant) or argument.value is not Ellipsis
            ]
            items = tuple(_annotation_type(argument) for argument in retained)
            item = merge_json_wire_types(items) if items else UNKNOWN_JSON_TYPE
            return JsonWireType("array", (item,), unsupported=item.unsupported)
        if name in {
            "dict",
            "Dict",
            "typing.Dict",
            "Mapping",
            "typing.Mapping",
            "collections.abc.Mapping",
        }:
            if len(arguments) != 2 or not _string_annotation(arguments[0]):
                return _unsupported("JSON objects require string keys")
            value = _annotation_type(arguments[1])
            return JsonWireType("object", additional=value, unsupported=value.unsupported)
        if name in {"set", "frozenset", "Set", "FrozenSet", "typing.Set", "typing.FrozenSet"}:
            return _unsupported("sets are not JSON-serializable")
        rendered = ast.unparse(node)
        return _unsupported(f"{rendered} does not describe a supported strict JSON container")
    name = _qualified_name(node)
    if name in {"None", "NoneType", "types.NoneType"}:
        return JsonWireType("null")
    if name == "bool":
        return JsonWireType("boolean")
    if name in {"int", "float"}:
        return JsonWireType("number")
    if name == "str":
        return JsonWireType("string")
    if name in {"Any", "typing.Any"}:
        return _unsupported("Any does not prove a strict JSON value")
    if name in {"bytes", "bytearray", "memoryview"}:
        return _unsupported(f"{name} values are not JSON-serializable")
    if name in {
        "date",
        "datetime.date",
        "datetime",
        "datetime.datetime",
        "time",
        "datetime.time",
        "timedelta",
        "datetime.timedelta",
        "Decimal",
        "decimal.Decimal",
        "UUID",
        "uuid.UUID",
        "Path",
        "pathlib.Path",
    }:
        return _unsupported(f"{name} values are not serialized by Citry's JSON wire format")
    if name in {"object", "Callable", "typing.Callable", "collections.abc.Callable"}:
        return _unsupported(f"{name} is not a JSON value type")
    if name is not None:
        return _unsupported(f"{name} cannot be proven to cross Citry's strict JSON wire")
    return _unsupported("the annotation does not describe a supported strict JSON value")


@dataclass(frozen=True, slots=True)
class _ExpressionContext:
    """The member and class facts one expression is typed against."""

    member_types: Mapping[str, Mapping[str, JsonWireType]]
    member_annotations: Mapping[str, Mapping[str, str | None]]
    classes: Mapping[str, WireClass]


def _attribute_chain(node: ast.Attribute) -> tuple[str, ...] | None:
    """Return ``("kwargs", "task", "lane")`` for ``kwargs.task.lane``, or ``None`` for any other base."""
    names: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        names.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    names.append(current.id)
    return tuple(reversed(names))


def _attribute_chain_type(chain: tuple[str, ...], context: _ExpressionContext) -> JsonWireType:
    """Follow ``root.member.attr...`` through the class table to the last attribute's type."""
    root, member, *attributes = chain
    annotation = context.member_annotations.get(root, {}).get(member)
    if not attributes:
        # A NamedTuple or TypedDict member is sent as an array or object.
        owner = context.classes.get(annotation) if annotation is not None else None
        if annotation is not None and owner is not None and owner.kind in {"named-tuple", "typed-dict"}:
            return _class_value_type(annotation, context)
        return context.member_types.get(root, {}).get(member, UNKNOWN_JSON_TYPE)
    for attribute in attributes[:-1]:
        # Only a plain class annotation is followed; `Owner | None` could be
        # None at run time, so reading through it proves nothing.
        owner = _readable_class(annotation, context)
        annotation = owner.attributes.get(attribute) if owner is not None else None
    last = attributes[-1]
    owner = context.classes.get(annotation) if annotation is not None else None
    if owner is not None and owner.kind == "enum":
        # An Enum member's `.value` and `.name` are the only JSON values it carries.
        if last == "value" and owner.enum_values is not None:
            return merge_json_wire_types(tuple(_literal_value_type(value) for value in owner.enum_values))
        if last == "name" and owner.enum_names is not None:
            return merge_json_wire_types(tuple(JsonWireType("string", literal=name) for name in owner.enum_names))
        return UNKNOWN_JSON_TYPE
    owner = _readable_class(annotation, context)
    field_annotation = owner.attributes.get(last) if owner is not None else None
    if field_annotation is None:
        return UNKNOWN_JSON_TYPE
    return _class_value_type(field_annotation, context)


def _readable_class(annotation: str | None, context: _ExpressionContext) -> WireClass | None:
    """Return the class whose attributes a value of this annotation has, or ``None``."""
    owner = context.classes.get(annotation) if annotation is not None else None
    # A TypedDict value is a plain dict, and an Enum member has no fields.
    return owner if owner is not None and owner.kind in {"object", "named-tuple"} else None


def _class_value_type(annotation: str, context: _ExpressionContext) -> JsonWireType:
    """Type a whole value of ``annotation``, as the JSON wire sends it."""
    owner = context.classes.get(annotation)
    if owner is not None and owner.kind in {"named-tuple", "typed-dict"}:
        # Each field is typed from its own annotation; an unresolved one stays unknown.
        values = {
            name: (json_wire_type_from_annotation(field) if field is not None else UNKNOWN_JSON_TYPE)
            for name, field in owner.attributes.items()
        }
        if owner.kind == "named-tuple":
            # The wire sends a NamedTuple as an array of its fields.
            item = merge_json_wire_types(tuple(values.values())) if values else UNKNOWN_JSON_TYPE
            return JsonWireType("array", (item,), unsupported=item.unsupported)
        required = set(owner.required or ())
        fields = tuple(JsonWireField(name, value, name in required) for name, value in values.items())
        issues = tuple(dict.fromkeys(issue for value in values.values() for issue in value.unsupported))
        return JsonWireType("object", fields=fields, unsupported=issues)
    return json_wire_type_from_annotation(annotation)


def _literal_value_type(value: str | float | None) -> JsonWireType:
    if value is None:
        return JsonWireType("null")
    if type(value) is bool:
        return JsonWireType("boolean", literal=value)
    if type(value) is str:
        return JsonWireType("string", literal=value)
    return JsonWireType("number", literal=value)


def _expression_type(
    node: ast.expr,
    context: _ExpressionContext,
) -> JsonWireType:
    if isinstance(node, ast.Attribute):
        chain = _attribute_chain(node)
        return _attribute_chain_type(chain, context) if chain is not None else UNKNOWN_JSON_TYPE
    if isinstance(node, ast.Constant):
        if node.value is None:
            return JsonWireType("null")
        if type(node.value) is bool:
            return JsonWireType("boolean", literal=node.value)
        if type(node.value) in {int, float}:
            return JsonWireType("number", literal=node.value)
        if type(node.value) is str:
            return JsonWireType("string", literal=node.value)
        if type(node.value) in {bytes, complex}:
            return _unsupported(f"{type(node.value).__name__} literals are not JSON-serializable")
        return UNKNOWN_JSON_TYPE
    if isinstance(node, ast.JoinedStr):
        return JsonWireType("string")
    if isinstance(node, ast.List | ast.Tuple):
        item = merge_json_wire_types(tuple(_expression_type(element, context) for element in node.elts))
        return JsonWireType("array", (item,), unsupported=item.unsupported)
    if isinstance(node, ast.Set):
        return _unsupported("set literals are not JSON-serializable")
    if isinstance(node, ast.Dict):
        fields: list[JsonWireField] = []
        issues: list[str] = []
        for key, value_node in zip(node.keys, node.values, strict=True):
            if not isinstance(key, ast.Constant) or type(key.value) is not str:
                return _unsupported("JSON objects require string keys")
            value = _expression_type(value_node, context)
            issues.extend(value.unsupported)
            fields.append(JsonWireField(key.value, value))
        return JsonWireType("object", fields=tuple(fields), unsupported=tuple(dict.fromkeys(issues)))
    if isinstance(node, ast.Set | ast.SetComp):
        return _unsupported("sets are not JSON-serializable")
    if isinstance(node, ast.IfExp):
        return merge_json_wire_types((_expression_type(node.body, context), _expression_type(node.orelse, context)))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return JsonWireType("boolean")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return (
            JsonWireType("number") if _expression_type(node.operand, context).kind == "number" else UNKNOWN_JSON_TYPE
        )
    if isinstance(node, ast.Compare):
        return JsonWireType("boolean")
    if isinstance(node, ast.BinOp):
        left = _expression_type(node.left, context)
        right = _expression_type(node.right, context)
        if isinstance(node.op, ast.Add) and left.kind == right.kind == "string":
            return JsonWireType("string")
        if left.kind == right.kind == "number":
            return JsonWireType("number")
    if isinstance(node, (ast.Lambda, ast.GeneratorExp)):
        return _unsupported("callables and generators are not JSON-serializable")
    return UNKNOWN_JSON_TYPE


def _literal_type(node: ast.expr) -> JsonWireType:
    value = _expression_type(node, _ExpressionContext({}, {}, {}))
    return value if value.kind != "unknown" else _unsupported("Literal contains a non-JSON value")


def _unsupported(reason: str) -> JsonWireType:
    return JsonWireType("unknown", unsupported=(reason,))


def _qualified_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent else None
    return None


def _string_annotation(node: ast.expr) -> bool:
    return _qualified_name(node) in {"str", "builtins.str"}


def _js_property(name: str) -> str:
    return name if name.isidentifier() else json.dumps(name, ensure_ascii=False)


__all__ = [
    "UNKNOWN_JSON_TYPE",
    "JsonWireField",
    "JsonWireKind",
    "JsonWireType",
    "WireClass",
    "WireClassKind",
    "json_wire_type_from_annotation",
    "json_wire_type_from_expression",
    "merge_json_wire_types",
]
