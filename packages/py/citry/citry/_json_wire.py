"""Portable, conservative Python-to-JSON type descriptions for editor tools."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

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
        if self.kind == "null":
            return "null"
        if self.kind in {"boolean", "number", "string"}:
            if self.literal is not None:
                return json.dumps(self.literal, ensure_ascii=False)
            return self.kind
        if self.kind == "array":
            item = merge_json_wire_types(self.items).javascript if self.items else "unknown"
            return f"Array<{item}>"
        if self.kind == "object":
            members = [
                f"{_js_property(field.name)}{'?' if not field.required else ''}: {field.value.javascript}"
                for field in self.fields
            ]
            if self.additional is not None:
                members.append(f"[key: string]: {self.additional.javascript}")
            return "{" + ", ".join(members) + "}" if members else "Record<string, unknown>"
        if self.kind == "union":
            rendered = tuple(dict.fromkeys(item.javascript for item in self.items))
            return " | ".join(rendered) if rendered else "unknown"
        return "unknown"

    @property
    def display(self) -> str:
        """Use the same concise vocabulary in hovers and diagnostics."""
        return self.javascript


UNKNOWN_JSON_TYPE = JsonWireType("unknown")


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
) -> JsonWireType:
    """Infer JSON shape from a Python value expression and proven members."""
    try:
        expression = ast.parse(source, mode="eval").body
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return UNKNOWN_JSON_TYPE
    return _expression_type(expression, member_types or {})


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


def _expression_type(
    node: ast.expr,
    member_types: Mapping[str, Mapping[str, JsonWireType]],
) -> JsonWireType:
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return member_types.get(node.value.id, {}).get(node.attr, UNKNOWN_JSON_TYPE)
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
        item = merge_json_wire_types(tuple(_expression_type(element, member_types) for element in node.elts))
        return JsonWireType("array", (item,), unsupported=item.unsupported)
    if isinstance(node, ast.Set):
        return _unsupported("set literals are not JSON-serializable")
    if isinstance(node, ast.Dict):
        fields: list[JsonWireField] = []
        issues: list[str] = []
        for key, value_node in zip(node.keys, node.values, strict=True):
            if not isinstance(key, ast.Constant) or type(key.value) is not str:
                return _unsupported("JSON objects require string keys")
            value = _expression_type(value_node, member_types)
            issues.extend(value.unsupported)
            fields.append(JsonWireField(key.value, value))
        return JsonWireType("object", fields=tuple(fields), unsupported=tuple(dict.fromkeys(issues)))
    if isinstance(node, ast.Set | ast.SetComp):
        return _unsupported("sets are not JSON-serializable")
    if isinstance(node, ast.IfExp):
        return merge_json_wire_types(
            (_expression_type(node.body, member_types), _expression_type(node.orelse, member_types))
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return JsonWireType("boolean")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return (
            JsonWireType("number")
            if _expression_type(node.operand, member_types).kind == "number"
            else UNKNOWN_JSON_TYPE
        )
    if isinstance(node, ast.Compare):
        return JsonWireType("boolean")
    if isinstance(node, ast.BinOp):
        left = _expression_type(node.left, member_types)
        right = _expression_type(node.right, member_types)
        if isinstance(node.op, ast.Add) and left.kind == right.kind == "string":
            return JsonWireType("string")
        if left.kind == right.kind == "number":
            return JsonWireType("number")
    if isinstance(node, (ast.Lambda, ast.GeneratorExp)):
        return _unsupported("callables and generators are not JSON-serializable")
    return UNKNOWN_JSON_TYPE


def _literal_type(node: ast.expr) -> JsonWireType:
    value = _expression_type(node, {})
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
    "json_wire_type_from_annotation",
    "json_wire_type_from_expression",
    "merge_json_wire_types",
]
