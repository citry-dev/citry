"""Tests for conformance-case proof and coverage reporting."""

# ruff: noqa: S101

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from packages.protocol._tooling import (
    OWNERSHIP_FORMAT,
    ConformanceCase,
    ExpectedIssue,
    Operation,
    constraint_fingerprint,
    inventory_schema,
    write_cases,
)
from packages.protocol._tooling.check import check_package


def _write_ownership_registry(package: Path, schema: dict[str, object]) -> None:
    """Give a synthetic schema one complete validator-family assignment."""
    constraints = inventory_schema("value.schema.json", schema).constraints
    pointers = sorted({constraint.schema_pointer for constraint in constraints})
    (package / "validator.py").write_text("def validate(value):\n    return value\n", encoding="utf-8")
    (package / "validator.ts").write_text("const validate = (value: unknown) => value;\n", encoding="utf-8")
    registry = {
        "format": OWNERSHIP_FORMAT,
        "families": [
            {
                "id": "synthetic-value",
                "schema": "value.schema.json",
                "exactSchemaPointers": pointers,
                "schemaPointerPrefixes": [],
                "pythonValidators": ["validator.py:validate"],
                "javascriptValidators": ["validator.ts:validate"],
                "tests": ["tests/valid.json"],
                "constraintCount": len(constraints),
                "constraintSha256": constraint_fingerprint(constraints),
            }
        ],
    }
    (package / "tests" / "constraint-ownership.json").write_text(json.dumps(registry), encoding="utf-8")


def test_package_check_proves_intended_constraint_and_reports_gaps(tmp_path: Path) -> None:
    package = tmp_path / "protocol"
    tests = package / "tests"
    tests.mkdir(parents=True)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["name"],
        "properties": {"name": {"type": "string", "minLength": 1}},
    }
    (package / "value.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    _write_ownership_registry(package, schema)
    (tests / "valid.json").write_text(json.dumps({"name": "ok"}), encoding="utf-8")
    write_cases(
        tests / "conformance-cases.json",
        (
            ConformanceCase(
                case_id="missing-name",
                schema="value.schema.json",
                constraint="/required/0",
                seed="valid.json",
                operations=(Operation("remove", "/name"),),
                expected=ExpectedIssue("/name", "required"),
                implementations=("python", "javascript"),
            ),
        ),
    )

    coverage, problems = check_package(package)

    assert problems == ()
    assert coverage[0].total == 5
    assert coverage[0].covered == 1
    assert dict(coverage[0].uncovered_by_keyword) == {
        "additionalProperties": 1,
        "minLength": 1,
        "type": 2,
    }


def test_package_check_rejects_wrong_expected_category(tmp_path: Path) -> None:
    package = tmp_path / "protocol"
    tests = package / "tests"
    tests.mkdir(parents=True)
    schema = {"type": "string", "minLength": 1}
    (package / "value.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    _write_ownership_registry(package, schema)
    (tests / "valid.json").write_text(json.dumps("ok"), encoding="utf-8")
    write_cases(
        tests / "conformance-cases.json",
        (
            ConformanceCase(
                case_id="empty",
                schema="value.schema.json",
                constraint="/minLength",
                seed="valid.json",
                operations=(Operation("replace", "", ""),),
                expected=ExpectedIssue("", "pattern"),
                implementations=("python",),
            ),
        ),
    )

    _coverage, problems = check_package(package)

    assert problems == ("empty: category 'pattern' does not match 'minLength' category 'range'",)


def test_package_check_does_not_accept_a_different_constraint_with_the_same_keyword(tmp_path: Path) -> None:
    package = tmp_path / "protocol"
    tests = package / "tests"
    tests.mkdir(parents=True)
    schema = {
        "type": "object",
        "required": ["name", "age"],
        "properties": {"name": {"type": "string"}, "age": {"type": "string"}},
    }
    (package / "value.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    _write_ownership_registry(package, schema)
    (tests / "valid.json").write_text(json.dumps({"name": "Ada", "age": "30"}), encoding="utf-8")
    write_cases(
        tests / "conformance-cases.json",
        (
            ConformanceCase(
                case_id="wrong-string-field",
                schema="value.schema.json",
                constraint="/properties/name/type",
                seed="valid.json",
                operations=(Operation("replace", "/age", 30),),
                expected=ExpectedIssue("/age", "type"),
                implementations=("python",),
            ),
        ),
    )

    _coverage, problems = check_package(package)

    assert problems == ("wrong-string-field: mutation did not reach 'type'; observed validators ['type']",)


def test_package_check_ties_required_constraint_to_the_removed_member(tmp_path: Path) -> None:
    package = tmp_path / "protocol"
    tests = package / "tests"
    tests.mkdir(parents=True)
    schema = {"type": "object", "required": ["name", "age"]}
    (package / "value.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    _write_ownership_registry(package, schema)
    (tests / "valid.json").write_text(json.dumps({"name": "Ada", "age": 30}), encoding="utf-8")
    write_cases(
        tests / "conformance-cases.json",
        (
            ConformanceCase(
                case_id="wrong-required-member",
                schema="value.schema.json",
                constraint="/required/0",
                seed="valid.json",
                operations=(Operation("remove", "/age"),),
                expected=ExpectedIssue("/name", "required"),
                implementations=("python",),
            ),
        ),
    )

    _coverage, problems = check_package(package)

    assert problems == ("wrong-required-member: expected issue path '/name'; observed schema error paths ['']",)


def test_package_check_selects_first_actual_unknown_member(tmp_path: Path) -> None:
    package = tmp_path / "protocol"
    tests = package / "tests"
    tests.mkdir(parents=True)
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "additionalProperties": False,
    }
    (package / "value.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    _write_ownership_registry(package, schema)
    (tests / "valid.json").write_text(json.dumps({"name": "Ada"}), encoding="utf-8")
    write_cases(
        tests / "conformance-cases.json",
        (
            ConformanceCase(
                case_id="wrong-unknown-member",
                schema="value.schema.json",
                constraint="/additionalProperties",
                seed="valid.json",
                operations=(Operation("add", "/bad", value=True), Operation("replace", "/name", "Grace")),
                expected=ExpectedIssue("/name", "unknown_field"),
                implementations=("python",),
            ),
        ),
    )

    _coverage, problems = check_package(package)

    assert problems == ("wrong-unknown-member: expected issue path '/name'; observed schema error paths ['']",)


def test_package_check_rejects_non_finite_seed_json(tmp_path: Path) -> None:
    package = tmp_path / "protocol"
    tests = package / "tests"
    tests.mkdir(parents=True)
    schema = {"type": "number"}
    (package / "value.schema.json").write_text(json.dumps(schema), encoding="utf-8")
    _write_ownership_registry(package, schema)
    (tests / "valid.json").write_text("Infinity", encoding="utf-8")
    write_cases(
        tests / "conformance-cases.json",
        (
            ConformanceCase(
                case_id="non-finite-seed",
                schema="value.schema.json",
                constraint="/type",
                seed="valid.json",
                operations=(Operation("replace", "", "not-a-number"),),
                expected=ExpectedIssue("", "type"),
                implementations=("python",),
            ),
        ),
    )

    _coverage, problems = check_package(package)

    assert len(problems) == 1
    assert "non-finite number 'Infinity' is not strict JSON" in problems[0]
