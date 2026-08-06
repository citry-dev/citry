"""Tests for the deliberately small protocol conformance helpers."""

# ruff: noqa: S101

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from packages.protocol._tooling import (
    CASE_FORMAT,
    ConformanceCase,
    ContractToolError,
    ExpectedIssue,
    Operation,
    SchemaAuditError,
    apply_operations,
    audit_schema,
    inventory_schema,
    load_cases,
    write_cases,
)


def test_inventory_is_stable_and_escapes_schema_pointers() -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": {"text": {"type": "string", "minLength": 1}},
        "type": "object",
        "required": ["a/b~c"],
        "properties": {"a/b~c": {"$ref": "#/$defs/text"}},
        "additionalProperties": False,
    }

    inventory = inventory_schema("synthetic", schema)

    assert [entry.constraint_id for entry in inventory.constraints] == [
        "/$defs/text/minLength",
        "/$defs/text/type",
        "/additionalProperties",
        "/required/0",
        "/type",
    ]
    reference = next(entry for entry in inventory.keywords if entry.keyword == "$ref")
    assert reference.target_pointer == "/$defs/text"


def test_schema_audit_fails_on_unknown_keyword_and_bad_local_reference() -> None:
    with pytest.raises(SchemaAuditError, match="unknown runtime-relevant"):
        audit_schema({"type": "object", "dependentSchemas": {}})
    with pytest.raises(SchemaAuditError, match="unresolved local reference"):
        audit_schema({"$ref": "#/$defs/missing"})
    with pytest.raises(SchemaAuditError, match="only local JSON Pointer"):
        audit_schema({"$ref": "https://example.test/schema.json"})


def test_inventory_does_not_treat_if_or_not_children_as_rejection_constraints() -> None:
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string", "not": {"pattern": "^citry:"}}},
        "if": {"required": ["name"]},
        "then": {"required": ["enabled"]},
    }

    constraint_ids = {entry.constraint_id for entry in inventory_schema("routing", schema).constraints}

    assert "/properties/name/not" in constraint_ids
    assert "/properties/name/not/pattern" not in constraint_ids
    assert "/if/required/0" not in constraint_ids
    assert "/then/required/0" in constraint_ids


def test_apply_operations_copies_values_and_supports_escaped_paths() -> None:
    original = {"a/b~c": [1], "keep": True}
    added = {"nested": []}
    operations = (
        Operation("replace", "/a~1b~0c/0", 2),
        Operation("add", "/a~1b~0c/-", 3),
        Operation("remove", "/keep"),
        Operation("add", "/new", added),
    )

    mutated = apply_operations(original, operations)
    added["nested"].append("later")

    assert original == {"a/b~c": [1], "keep": True}
    assert mutated == {"a/b~c": [2, 3], "new": {"nested": []}}


def test_operations_reject_ambiguous_or_missing_targets() -> None:
    with pytest.raises(ContractToolError, match="must not have a value"):
        Operation("remove", "/x", 1)
    with pytest.raises(ContractToolError, match="invalid JSON Pointer escape"):
        Operation("remove", "/x~2")
    with pytest.raises(ContractToolError, match="does not exist"):
        apply_operations({}, (Operation("replace", "/x", 1),))
    with pytest.raises(ContractToolError, match="cannot be removed"):
        apply_operations({}, (Operation("remove", ""),))
    with pytest.raises(ContractToolError, match="invalid array index"):
        apply_operations([0, 1], (Operation("replace", "/\N{ARABIC-INDIC DIGIT ONE}", 2),))


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity", "1e999", "1" + "0" * 400])
def test_case_loader_rejects_non_finite_numbers(tmp_path: Path, constant: str) -> None:
    path = tmp_path / "cases.json"
    path.write_text(
        '{"format":"citry-protocol-conformance-cases/1","cases":['
        '{"id":"bad","schema":"value.schema.json","constraint":"/type",'
        '"seed":"valid.json","operations":[{"op":"replace","path":"","value":'
        f"{constant}"
        '}],"expected":{"path":"","category":"type"},"implementations":["python"]}]}',
        encoding="utf-8",
    )

    with pytest.raises(ContractToolError, match=r"strict JSON|finite JSON range"):
        load_cases(path)


def test_case_file_round_trips_and_is_strict(tmp_path: Path) -> None:
    case = ConformanceCase(
        case_id="missing-protocol",
        schema="events/call",
        constraint="/required/0",
        seed="happy_render.call.json",
        operations=(Operation("remove", "/protocol"),),
        expected=ExpectedIssue("/protocol", "required"),
        implementations=("python", "javascript"),
    )
    path = tmp_path / "cases.json"

    write_cases(path, (case,))

    assert load_cases(path) == (case,)
    assert json.loads(path.read_text(encoding="utf-8"))["format"] == CASE_FORMAT
    broken = case.to_dict()
    broken["surprise"] = True
    path.write_text(json.dumps({"format": CASE_FORMAT, "cases": [broken]}), encoding="utf-8")
    with pytest.raises(ContractToolError, match="extra fields"):
        load_cases(path)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 10**400])
def test_case_writer_rejects_values_its_readers_cannot_load(tmp_path: Path, value: object) -> None:
    case = ConformanceCase(
        case_id="bad-number",
        schema="value.schema.json",
        constraint="/type",
        seed="valid.json",
        operations=(Operation("replace", "", value),),
        expected=ExpectedIssue("", "type"),
        implementations=("python", "javascript"),
    )

    with pytest.raises(ContractToolError, match=r"strict JSON|finite JSON range"):
        write_cases(tmp_path / "cases.json", (case,))


def test_case_parser_rejects_duplicate_implementations() -> None:
    value = {
        "id": "duplicate",
        "schema": "events/call",
        "constraint": "/type",
        "seed": "happy_render.call.json",
        "operations": [{"op": "replace", "path": "", "value": []}],
        "expected": {"path": "", "category": "type"},
        "implementations": ["python", "python"],
    }

    with pytest.raises(ContractToolError, match="must be unique"):
        ConformanceCase.from_dict(value)
