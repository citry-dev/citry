"""Tests for fail-closed schema-constraint ownership."""

# ruff: noqa: S101

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from packages.protocol._tooling import (
    OWNERSHIP_FORMAT,
    Constraint,
    check_constraint_ownership,
    constraint_fingerprint,
    inventory_schema,
)


def _family(constraints: tuple[Constraint, ...]) -> dict[str, object]:
    return {
        "id": "value",
        "schema": "value.schema.json",
        "exactSchemaPointers": [""],
        "schemaPointerPrefixes": [],
        "pythonValidators": ["validator.py:validate"],
        "javascriptValidators": ["validator.ts:validate"],
        "tests": ["tests/value.json"],
        "constraintCount": len(constraints),
        "constraintSha256": constraint_fingerprint(constraints),
    }


def _package(tmp_path: Path) -> tuple[Path, tuple[Constraint, ...]]:
    package = tmp_path / "protocol"
    tests = package / "tests"
    tests.mkdir(parents=True)
    (tests / "value.json").write_text("{}", encoding="utf-8")
    (package / "validator.py").write_text("def validate(value):\n    return value\n", encoding="utf-8")
    (package / "validator.ts").write_text("const validate = (value: unknown) => value;\n", encoding="utf-8")
    constraints = inventory_schema("value.schema.json", {"type": "object"}).constraints
    return package, constraints


def test_ownership_assigns_every_constraint_and_detects_inventory_change(tmp_path: Path) -> None:
    package, constraints = _package(tmp_path)
    registry = {"format": OWNERSHIP_FORMAT, "families": [_family(constraints)]}
    (package / "tests" / "constraint-ownership.json").write_text(json.dumps(registry), encoding="utf-8")
    inventories = {"value.schema.json": {entry.constraint_id: entry for entry in constraints}}

    summaries, problems = check_constraint_ownership(package, inventories)

    assert problems == ()
    assert summaries[0].to_dict() == {
        "schema": "value.schema.json",
        "total": 1,
        "assigned": 1,
        "families": 1,
    }

    changed = inventory_schema("value.schema.json", {"type": "array"}).constraints
    _summaries, changed_problems = check_constraint_ownership(
        package,
        {"value.schema.json": {entry.constraint_id: entry for entry in changed}},
    )

    assert len(changed_problems) == 1
    assert "constraint inventory changed" in changed_problems[0]


def test_ownership_rejects_multiple_owners_and_missing_references(tmp_path: Path) -> None:
    package, constraints = _package(tmp_path)
    first = _family(constraints)
    second = {**first, "id": "duplicate", "pythonValidators": ["validator.py:missing"]}
    registry = {"format": OWNERSHIP_FORMAT, "families": [first, second]}
    (package / "tests" / "constraint-ownership.json").write_text(json.dumps(registry), encoding="utf-8")
    inventories = {"value.schema.json": {entry.constraint_id: entry for entry in constraints}}

    summaries, problems = check_constraint_ownership(package, inventories)

    assert summaries[0].assigned == 0
    assert any("multiple owners" in problem for problem in problems)
    assert any("missing Python validator symbol" in problem for problem in problems)
