"""
Small, fail-closed helpers for protocol conformance cases.

This is repository tooling, not a runtime JSON Schema implementation. It
inventories the vocabulary used by Citry's schemas and stores explicit
mutations that runtime packages can replay without depending on ``jsonschema``.
"""

from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

JsonValue = Any
CASE_FORMAT: Final = "citry-protocol-conformance-cases/1"
_MISSING: Final = object()

_ANNOTATION_KEYWORDS: Final = frozenset(
    {"$comment", "default", "deprecated", "description", "examples", "readOnly", "title", "writeOnly"}
)
_CONTROL_KEYWORDS: Final = frozenset({"$defs", "$id", "$schema"})
_APPLICATOR_KEYWORDS: Final = frozenset(
    {
        "$ref",
        "additionalProperties",
        "allOf",
        "else",
        "if",
        "items",
        "not",
        "oneOf",
        "properties",
        "propertyNames",
        "then",
    }
)
_ASSERTION_KEYWORDS: Final = frozenset(
    {
        "const",
        "enum",
        "maxItems",
        "maxLength",
        "maximum",
        "minItems",
        "minLength",
        "minimum",
        "pattern",
        "required",
        "type",
        "uniqueItems",
    }
)
_KNOWN_KEYWORDS: Final = _ANNOTATION_KEYWORDS | _CONTROL_KEYWORDS | _APPLICATOR_KEYWORDS | _ASSERTION_KEYWORDS
_SCHEMA_CHILDREN: Final = frozenset({"additionalProperties", "else", "if", "items", "not", "propertyNames", "then"})
_SCHEMA_LISTS: Final = frozenset({"allOf", "oneOf"})
_SCHEMA_MAPS: Final = frozenset({"$defs", "properties"})
_CONSTRAINT_KEYWORDS: Final = _ASSERTION_KEYWORDS | frozenset({"additionalProperties", "not", "oneOf"})


class ContractToolError(ValueError):
    """An input cannot safely be used to generate conformance data."""


class SchemaAuditError(ContractToolError):
    """A schema is invalid or uses vocabulary the tooling does not know."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(self.problems))


@dataclass(frozen=True, slots=True)
class KeywordUse:
    """One recognized schema keyword at a stable RFC 6901 pointer."""

    pointer: str
    keyword: str
    role: str
    target_pointer: str | None = None

    def to_dict(self) -> dict[str, str]:
        record = {"pointer": self.pointer, "keyword": self.keyword, "role": self.role}
        if self.target_pointer is not None:
            record["targetPointer"] = self.target_pointer
        return record


@dataclass(frozen=True, slots=True)
class Constraint:
    """One runtime-relevant schema constraint."""

    constraint_id: str
    schema_pointer: str
    keyword: str
    value: JsonValue

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "id": self.constraint_id,
            "schemaPointer": self.schema_pointer,
            "keyword": self.keyword,
            "value": copy.deepcopy(self.value),
        }


@dataclass(frozen=True, slots=True)
class SchemaInventory:
    """Stable keyword and constraint inventory for one schema."""

    schema: str
    keywords: tuple[KeywordUse, ...]
    constraints: tuple[Constraint, ...]

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "keywords": [entry.to_dict() for entry in self.keywords],
            "constraints": [entry.to_dict() for entry in self.constraints],
        }


@dataclass(frozen=True, slots=True)
class ExpectedIssue:
    """The stable portion of the issue a mutation must produce."""

    path: str
    category: str

    @classmethod
    def from_dict(cls, value: JsonValue) -> ExpectedIssue:
        record = _strict_record(value, {"path", "category"}, "expected issue")
        return cls(
            path=_pointer(record["path"], "expected issue path"),
            category=_string(record["category"], "issue category"),
        )

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "category": self.category}


@dataclass(frozen=True, slots=True)
class Operation:
    """One explicit add, remove, or replace operation."""

    op: str
    path: str
    value: JsonValue = field(default=_MISSING, repr=False)

    def __post_init__(self) -> None:
        if self.op not in {"add", "remove", "replace"}:
            raise ContractToolError(f"unsupported operation {self.op!r}")
        _pointer_tokens(self.path)
        if self.op == "remove" and self.value is not _MISSING:
            raise ContractToolError("remove operations must not have a value")
        if self.op != "remove" and self.value is _MISSING:
            raise ContractToolError(f"{self.op} operations require a value")

    @classmethod
    def from_dict(cls, value: JsonValue) -> Operation:
        if not isinstance(value, dict):
            raise ContractToolError("operation must be an object")
        op = _string(value.get("op"), "operation op")
        expected = {"op", "path"} if op == "remove" else {"op", "path", "value"}
        record = _strict_record(value, expected, "operation")
        return cls(op=op, path=_pointer(record["path"], "operation path"), value=record.get("value", _MISSING))

    def to_dict(self) -> dict[str, JsonValue]:
        record: dict[str, JsonValue] = {"op": self.op, "path": self.path}
        if self.value is not _MISSING:
            record["value"] = copy.deepcopy(self.value)
        return record


@dataclass(frozen=True, slots=True)
class ConformanceCase:
    """A valid seed file plus one explicit mutation and its expected issue."""

    case_id: str
    schema: str
    constraint: str
    seed: str
    operations: tuple[Operation, ...]
    expected: ExpectedIssue
    implementations: tuple[str, ...]
    rule: str | None = None

    @classmethod
    def from_dict(cls, value: JsonValue) -> ConformanceCase:
        fields = {"id", "schema", "constraint", "seed", "operations", "expected", "implementations"}
        if isinstance(value, dict) and "rule" in value:
            fields.add("rule")
        record = _strict_record(value, fields, "conformance case")
        raw_operations = record["operations"]
        raw_implementations = record["implementations"]
        if not isinstance(raw_operations, list) or not raw_operations:
            raise ContractToolError("conformance case operations must be a non-empty array")
        if not isinstance(raw_implementations, list) or not raw_implementations:
            raise ContractToolError("conformance case implementations must be a non-empty array")
        implementations = tuple(_string(item, "implementation") for item in raw_implementations)
        if len(set(implementations)) != len(implementations):
            raise ContractToolError("conformance case implementations must be unique")
        return cls(
            case_id=_string(record["id"], "case id"),
            schema=_string(record["schema"], "schema id"),
            constraint=_string(record["constraint"], "constraint id"),
            seed=_string(record["seed"], "seed path"),
            operations=tuple(Operation.from_dict(item) for item in raw_operations),
            expected=ExpectedIssue.from_dict(record["expected"]),
            implementations=implementations,
            rule=_string(record["rule"], "handwritten rule") if "rule" in record else None,
        )

    def to_dict(self) -> dict[str, JsonValue]:
        record: dict[str, JsonValue] = {
            "id": self.case_id,
            "schema": self.schema,
            "constraint": self.constraint,
            "seed": self.seed,
            "operations": [operation.to_dict() for operation in self.operations],
            "expected": self.expected.to_dict(),
            "implementations": list(self.implementations),
        }
        if self.rule is not None:
            record["rule"] = self.rule
        return record


def audit_schema(schema: JsonValue) -> tuple[KeywordUse, ...]:
    """Check Draft 2020-12 shape and reject unknown schema vocabulary."""
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise SchemaAuditError((f"invalid Draft 2020-12 schema: {error.message}",)) from error

    uses: list[KeywordUse] = []
    problems: list[str] = []

    def walk(node: JsonValue, pointer: str) -> None:
        if isinstance(node, bool):
            return
        if not isinstance(node, dict):
            problems.append(f"{pointer or '/'}: schema node must be an object or boolean")
            return
        for keyword, value in node.items():
            keyword_pointer = _join_pointer(pointer, keyword)
            if keyword not in _KNOWN_KEYWORDS:
                problems.append(f"{keyword_pointer}: unknown runtime-relevant schema keyword {keyword!r}")
                continue
            target = None
            if keyword == "$ref":
                if not isinstance(value, str) or not value.startswith("#"):
                    problems.append(f"{keyword_pointer}: only local JSON Pointer references are supported")
                else:
                    target = value[1:]
                    try:
                        resolved = _resolve_pointer(schema, target)
                    except (KeyError, IndexError, TypeError, ValueError):
                        problems.append(f"{keyword_pointer}: unresolved local reference {value!r}")
                    else:
                        if not isinstance(resolved, (dict, bool)):
                            problems.append(f"{keyword_pointer}: reference target is not a schema")
            uses.append(KeywordUse(keyword_pointer, keyword, _keyword_role(keyword), target))

        for keyword in _SCHEMA_CHILDREN:
            child = node.get(keyword, _MISSING)
            if child is not _MISSING and isinstance(child, (dict, bool)):
                walk(child, _join_pointer(pointer, keyword))
        for keyword in _SCHEMA_LISTS:
            children = node.get(keyword)
            if isinstance(children, list):
                for index, child in enumerate(children):
                    walk(child, _join_pointer(_join_pointer(pointer, keyword), index))
        for keyword in _SCHEMA_MAPS:
            children = node.get(keyword)
            if isinstance(children, dict):
                for name, child in children.items():
                    walk(child, _join_pointer(_join_pointer(pointer, keyword), name))

    walk(schema, "")
    if problems:
        raise SchemaAuditError(tuple(problems))
    return tuple(sorted(uses, key=lambda entry: entry.pointer))


def inventory_schema(schema_id: str, schema: JsonValue) -> SchemaInventory:
    """Return a stable inventory of known keywords and concrete constraints."""
    keywords = audit_schema(schema)
    constraints: list[Constraint] = []

    def walk(node: JsonValue, pointer: str, *, rejection_context: bool) -> None:
        if isinstance(node, bool) or not isinstance(node, dict):
            return
        if rejection_context:
            for keyword in _CONSTRAINT_KEYWORDS:
                if keyword not in node:
                    continue
                value = node[keyword]
                keyword_pointer = _join_pointer(pointer, keyword)
                if keyword == "required":
                    for index, member in enumerate(value):
                        constraints.append(
                            Constraint(
                                constraint_id=_join_pointer(keyword_pointer, index),
                                schema_pointer=pointer,
                                keyword=keyword,
                                value=copy.deepcopy(member),
                            )
                        )
                elif (keyword == "additionalProperties" and value is not False) or (
                    keyword == "uniqueItems" and value is not True
                ):
                    continue
                else:
                    constraints.append(
                        Constraint(
                            constraint_id=keyword_pointer,
                            schema_pointer=pointer,
                            keyword=keyword,
                            value=copy.deepcopy(value),
                        )
                    )

        for keyword in _SCHEMA_CHILDREN:
            child = node.get(keyword, _MISSING)
            if child is _MISSING or not isinstance(child, (dict, bool)):
                continue
            # `if` only chooses a branch, and `not` reverses its child. Their
            # inner assertions cannot be covered by a rejection mutation of
            # their own. The wrapper/selected branch remains inventory-worthy.
            child_rejects = rejection_context and keyword not in {"if", "not"}
            walk(child, _join_pointer(pointer, keyword), rejection_context=child_rejects)
        for keyword in _SCHEMA_LISTS:
            children = node.get(keyword)
            if isinstance(children, list):
                for index, child in enumerate(children):
                    walk(
                        child,
                        _join_pointer(_join_pointer(pointer, keyword), index),
                        rejection_context=rejection_context,
                    )
        for keyword in _SCHEMA_MAPS:
            children = node.get(keyword)
            if isinstance(children, dict):
                for name, child in children.items():
                    walk(
                        child,
                        _join_pointer(_join_pointer(pointer, keyword), name),
                        rejection_context=rejection_context,
                    )

    walk(schema, "", rejection_context=True)
    return SchemaInventory(schema_id, keywords, tuple(sorted(constraints, key=lambda entry: entry.constraint_id)))


def apply_operations(document: JsonValue, operations: Sequence[Operation]) -> JsonValue:
    """Apply explicit mutation operations to a detached copy of a JSON value."""
    result = copy.deepcopy(document)
    for operation in operations:
        tokens = _pointer_tokens(operation.path)
        if not tokens:
            if operation.op == "remove":
                raise ContractToolError("the document root cannot be removed")
            result = copy.deepcopy(operation.value)
            continue
        parent = result
        for token in tokens[:-1]:
            parent = _member(parent, token)
        path_segment = tokens[-1]
        if isinstance(parent, list):
            if operation.op == "add":
                index = len(parent) if path_segment == "-" else _array_index(path_segment, len(parent), allow_end=True)
                parent.insert(index, copy.deepcopy(operation.value))
            else:
                index = _array_index(path_segment, len(parent))
                if operation.op == "remove":
                    parent.pop(index)
                else:
                    parent[index] = copy.deepcopy(operation.value)
        elif isinstance(parent, dict):
            if operation.op != "add" and path_segment not in parent:
                raise ContractToolError(f"operation path does not exist: {operation.path!r}")
            if operation.op == "remove":
                del parent[path_segment]
            else:
                parent[path_segment] = copy.deepcopy(operation.value)
        else:
            raise ContractToolError(f"operation parent is not a container: {operation.path!r}")
    return result


def load_cases(path: Path) -> tuple[ConformanceCase, ...]:
    """Load and strictly check one conformance-case file."""
    payload = load_json_value(path)
    record = _strict_record(payload, {"format", "cases"}, "conformance case file")
    if record["format"] != CASE_FORMAT:
        raise ContractToolError(f"unsupported conformance case format {record['format']!r}")
    if not isinstance(record["cases"], list):
        raise ContractToolError("conformance case file cases must be an array")
    cases = tuple(ConformanceCase.from_dict(item) for item in record["cases"])
    case_ids = [case.case_id for case in cases]
    if len(set(case_ids)) != len(case_ids):
        raise ContractToolError("conformance case ids must be unique")
    return cases


def load_json_value(path: Path) -> JsonValue:
    """Load strict JSON, rejecting JavaScript-incompatible non-finite numbers."""
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_json_constant,
            parse_float=_finite_json_float,
            parse_int=_finite_json_int,
        )
    except (OSError, ValueError) as error:
        raise ContractToolError(f"cannot load {path}: {error}") from error


def write_cases(path: Path, cases: Sequence[ConformanceCase]) -> None:
    """Write cases in their caller-defined order using stable formatting."""
    case_ids = [case.case_id for case in cases]
    if len(set(case_ids)) != len(case_ids):
        raise ContractToolError("conformance case ids must be unique")
    payload = {"format": CASE_FORMAT, "cases": [case.to_dict() for case in cases]}
    _validate_json_value(payload)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _strict_record(value: JsonValue, fields: set[str], description: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, dict):
        raise ContractToolError(f"{description} must be an object")
    actual = set(value)
    if actual != fields:
        missing = sorted(fields - actual)
        extra = sorted(actual - fields)
        raise ContractToolError(f"{description} has missing fields {missing!r} and extra fields {extra!r}")
    return value


def _string(value: JsonValue, description: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractToolError(f"{description} must be a non-empty string")
    return value


def _pointer(value: JsonValue, description: str) -> str:
    if not isinstance(value, str):
        raise ContractToolError(f"{description} must be a string")
    _pointer_tokens(value)
    return value


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite number {value!r} is not strict JSON")


def _finite_json_float(value: str) -> float:
    decoded = float(value)
    if not math.isfinite(decoded):
        raise ValueError(f"number {value!r} is outside the finite JSON range")
    return decoded


def _finite_json_int(value: str) -> int:
    decoded = int(value)
    try:
        js_number = float(decoded)
    except OverflowError as error:
        raise ValueError("integer is outside the finite JSON range") from error
    if not math.isfinite(js_number):
        raise ValueError("integer is outside the finite JSON range")
    return decoded


def _validate_json_value(value: JsonValue, ancestors: set[int] | None = None) -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        try:
            _finite_json_int(str(value))
        except ValueError as error:
            raise ContractToolError(str(error)) from error
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractToolError("non-finite number is not strict JSON")
        return
    if not isinstance(value, (dict, list)):
        raise ContractToolError(f"{type(value).__name__} is not strict JSON")
    active = ancestors if ancestors is not None else set()
    identity = id(value)
    if identity in active:
        raise ContractToolError("cyclic value is not strict JSON")
    active.add(identity)
    if isinstance(value, list):
        for item in value:
            _validate_json_value(item, active)
    else:
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractToolError("object keys must be strings in strict JSON")
            _validate_json_value(item, active)
    active.remove(identity)


def _keyword_role(keyword: str) -> str:
    if keyword in _ANNOTATION_KEYWORDS:
        return "annotation"
    if keyword in _CONTROL_KEYWORDS:
        return "control"
    if keyword in _APPLICATOR_KEYWORDS:
        return "applicator"
    return "assertion"


def _escape_pointer_token(token: object) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


def _join_pointer(pointer: str, token: object) -> str:
    return f"{pointer}/{_escape_pointer_token(token)}"


def _pointer_tokens(pointer: str) -> tuple[str, ...]:
    if pointer == "":
        return ()
    if not pointer.startswith("/"):
        raise ContractToolError(f"not an RFC 6901 JSON Pointer: {pointer!r}")
    tokens: list[str] = []
    for raw in pointer[1:].split("/"):
        index = 0
        while index < len(raw):
            if raw[index] == "~" and (index + 1 == len(raw) or raw[index + 1] not in "01"):
                raise ContractToolError(f"invalid JSON Pointer escape in {pointer!r}")
            index += 2 if raw[index] == "~" else 1
        tokens.append(raw.replace("~1", "/").replace("~0", "~"))
    return tuple(tokens)


def _resolve_pointer(document: JsonValue, pointer: str) -> JsonValue:
    current = document
    for token in _pointer_tokens(pointer):
        current = _member(current, token)
    return current


def _member(container: JsonValue, token: str) -> JsonValue:
    if isinstance(container, list):
        return container[_array_index(token, len(container))]
    if isinstance(container, dict):
        return container[token]
    raise TypeError("JSON Pointer traversed a scalar")


def _array_index(token: str, length: int, *, allow_end: bool = False) -> int:
    if not token.isascii() or not token.isdigit() or (len(token) > 1 and token.startswith("0")):
        raise ContractToolError(f"invalid array index {token!r}")
    index = int(token)
    upper = length if allow_end else length - 1
    if index > upper:
        raise ContractToolError(f"array index {index} is out of range")
    return index
