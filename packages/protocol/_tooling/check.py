"""Verify explicit conformance mutations and report schema coverage."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jsonschema import Draft202012Validator

from .contracts import (
    ConformanceCase,
    Constraint,
    ContractToolError,
    apply_operations,
    inventory_schema,
    load_cases,
    load_json_value,
)
from .ownership import OwnershipSummary, check_constraint_ownership

if TYPE_CHECKING:
    from jsonschema.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class Coverage:
    """Constraint totals for one schema."""

    schema: str
    total: int
    covered: int
    uncovered_by_keyword: tuple[tuple[str, int], ...]
    ownership: OwnershipSummary | None = None

    def to_dict(self) -> dict[str, Any]:
        report = {
            "schema": self.schema,
            "total": self.total,
            "covered": self.covered,
            "uncovered": self.total - self.covered,
            "uncoveredByKeyword": dict(self.uncovered_by_keyword),
        }
        if self.ownership is not None:
            report["ownership"] = self.ownership.to_dict()
        return report


def check_package(package_root: Path) -> tuple[tuple[Coverage, ...], tuple[str, ...]]:
    """Check one protocol package's case file and return coverage plus problems."""
    tests_dir = package_root / "tests"
    cases = load_cases(tests_dir / "conformance-cases.json")
    problems: list[str] = []
    inventories: dict[str, dict[str, Constraint]] = {}
    covered: dict[str, set[str]] = {}

    for case in cases:
        if "python" not in case.implementations:
            problems.append(f"{case.case_id}: Python is missing from implementations")
        schema_path = package_root / case.schema
        if case.schema not in inventories:
            try:
                schema = load_json_value(schema_path)
                inventory = inventory_schema(case.schema, schema)
            except (OSError, json.JSONDecodeError, ContractToolError) as error:
                problems.append(f"{case.case_id}: cannot inventory {case.schema}: {error}")
                continue
            inventories[case.schema] = {entry.constraint_id: entry for entry in inventory.constraints}
            covered[case.schema] = set()
        constraints = inventories[case.schema]
        constraint = constraints.get(case.constraint)
        if constraint is None:
            problems.append(f"{case.case_id}: unknown constraint {case.constraint!r} in {case.schema}")
            continue
        covered[case.schema].add(case.constraint)
        _check_case(case, constraint, constraints, tests_dir, schema_path, problems)

    for schema_path in sorted(package_root.glob("*.schema.json")):
        schema_name = schema_path.name
        if schema_name not in inventories:
            schema = load_json_value(schema_path)
            inventory = inventory_schema(schema_name, schema)
            inventories[schema_name] = {entry.constraint_id: entry for entry in inventory.constraints}
            covered[schema_name] = set()

    ownership, ownership_problems = check_constraint_ownership(package_root, inventories)
    problems.extend(ownership_problems)
    ownership_by_schema = {entry.schema: entry for entry in ownership}
    coverage: list[Coverage] = []
    for schema_name in sorted(inventories):
        constraints = inventories[schema_name]
        uncovered = [entry for key, entry in constraints.items() if key not in covered[schema_name]]
        counts = Counter(entry.keyword for entry in uncovered)
        coverage.append(
            Coverage(
                schema=schema_name,
                total=len(constraints),
                covered=len(covered[schema_name]),
                uncovered_by_keyword=tuple(sorted(counts.items())),
                ownership=ownership_by_schema.get(schema_name),
            )
        )
    return tuple(coverage), tuple(problems)


def _check_case(
    case: ConformanceCase,
    constraint: Constraint,
    constraints: dict[str, Constraint],
    tests_dir: Path,
    schema_path: Path,
    problems: list[str],
) -> None:
    try:
        schema = load_json_value(schema_path)
        seed = load_json_value(tests_dir / case.seed)
    except ContractToolError as error:
        problems.append(f"{case.case_id}: cannot load seed or schema: {error}")
        return
    validator = Draft202012Validator(schema)
    seed_errors = list(validator.iter_errors(seed))
    if seed_errors:
        problems.append(f"{case.case_id}: seed {case.seed} is invalid: {seed_errors[0].message}")
        return
    try:
        mutated = apply_operations(seed, case.operations)
    except ContractToolError as error:
        problems.append(f"{case.case_id}: cannot apply operations: {error}")
        return
    errors = list(validator.iter_errors(mutated))
    if not errors:
        problems.append(f"{case.case_id}: mutation remains valid")
        return
    occurrences = _constraint_occurrences(schema, constraints)
    intended = [
        error for error in _flatten_errors(errors) if _error_matches_constraint(error, constraint, occurrences)
    ]
    if not intended:
        validators = sorted({str(error.validator) for error in _flatten_errors(errors)})
        problems.append(
            f"{case.case_id}: mutation did not reach {constraint.keyword!r}; observed validators {validators!r}"
        )
        return
    if case.rule not in {None, "discriminator"}:
        problems.append(f"{case.case_id}: unknown handwritten rule {case.rule!r}")
        return
    expected_category = "enum" if case.rule == "discriminator" else _category_for_keyword(constraint.keyword)
    if case.expected.category != expected_category:
        problems.append(
            f"{case.case_id}: category {case.expected.category!r} does not match "
            f"{constraint.keyword!r} category {expected_category!r}"
        )
    if case.rule == "discriminator":
        path_matches = any(_matches_discriminator_path(case, error) for error in intended)
    else:
        path_matches = any(_matches_expected_path(case, constraint, error) for error in intended)
    if not path_matches:
        paths = sorted({_error_pointer(error) for error in intended})
        problems.append(
            f"{case.case_id}: expected issue path {case.expected.path!r}; observed schema error paths {paths!r}"
        )


def _flatten_errors(errors: list[ValidationError]) -> list[ValidationError]:
    flattened: list[ValidationError] = []
    pending = list(errors)
    while pending:
        error = pending.pop()
        flattened.append(error)
        pending.extend(error.context)
    return flattened


def _error_matches_constraint(
    error: ValidationError,
    constraint: Constraint,
    occurrences: dict[str, set[str]],
) -> bool:
    if error.validator != constraint.keyword:
        return False
    if constraint.constraint_id not in occurrences.get(_schema_error_pointer(error), set()):
        return False
    if constraint.keyword == "required":
        return isinstance(error.validator_value, list) and constraint.value in error.validator_value
    return error.validator_value == constraint.value


def _constraint_occurrences(
    schema: Any,
    constraints: dict[str, Constraint],
) -> dict[str, set[str]]:
    """Map validator schema paths back to canonical constraint IDs."""
    by_node: dict[str, list[Constraint]] = {}
    for constraint in constraints.values():
        by_node.setdefault(constraint.schema_pointer, []).append(constraint)
    occurrences: dict[str, set[str]] = {}
    active_refs: set[tuple[str, str]] = set()

    def walk(node: Any, occurrence_pointer: str, canonical_pointer: str) -> None:
        if isinstance(node, bool) or not isinstance(node, dict):
            return
        for constraint in by_node.get(canonical_pointer, []):
            keyword_pointer = _join_pointer(occurrence_pointer, constraint.keyword)
            occurrences.setdefault(keyword_pointer, set()).add(constraint.constraint_id)

        reference = node.get("$ref")
        if isinstance(reference, str) and reference.startswith("#"):
            target_pointer = reference[1:]
            ref_key = (occurrence_pointer, target_pointer)
            if ref_key not in active_refs:
                active_refs.add(ref_key)
                walk(_resolve_schema_pointer(schema, target_pointer), occurrence_pointer, target_pointer)
                active_refs.remove(ref_key)

        for keyword in ("additionalProperties", "else", "if", "items", "not", "propertyNames", "then"):
            child = node.get(keyword)
            if isinstance(child, (dict, bool)):
                walk(
                    child,
                    _join_pointer(occurrence_pointer, keyword),
                    _join_pointer(canonical_pointer, keyword),
                )
        for keyword in ("allOf", "oneOf"):
            children = node.get(keyword)
            if isinstance(children, list):
                for index, child in enumerate(children):
                    walk(
                        child,
                        _join_pointer(_join_pointer(occurrence_pointer, keyword), index),
                        _join_pointer(_join_pointer(canonical_pointer, keyword), index),
                    )
        properties = node.get("properties")
        if isinstance(properties, dict):
            for name, child in properties.items():
                walk(
                    child,
                    _join_pointer(_join_pointer(occurrence_pointer, "properties"), name),
                    _join_pointer(_join_pointer(canonical_pointer, "properties"), name),
                )

    walk(schema, "", "")
    return occurrences


def _resolve_schema_pointer(schema: Any, pointer: str) -> Any:
    current = schema
    if pointer == "":
        return current
    for raw in pointer.removeprefix("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def _schema_error_pointer(error: ValidationError) -> str:
    pointer = ""
    for part in error.absolute_schema_path:
        pointer = _join_pointer(pointer, part)
    return pointer


def _matches_expected_path(case: ConformanceCase, constraint: Constraint, error: ValidationError) -> bool:
    pointer = _error_pointer(error)
    if constraint.keyword == "required":
        pointer = _join_pointer(pointer, constraint.value)
        removed = {operation.path for operation in case.operations if operation.op == "remove"}
        return pointer == case.expected.path and case.expected.path in removed
    elif constraint.keyword == "additionalProperties":
        if not isinstance(error.instance, dict) or not isinstance(error.schema, dict):
            return False
        declared = error.schema.get("properties", {})
        if not isinstance(declared, dict):
            return False
        unknown = sorted(set(error.instance) - set(declared), key=_utf16_sort_key)
        expected = _join_pointer(pointer, unknown[0]) if unknown else None
        return expected == case.expected.path
    return pointer == case.expected.path


def _matches_discriminator_path(case: ConformanceCase, error: ValidationError) -> bool:
    changed = {operation.path for operation in case.operations if operation.op in {"add", "replace"}}
    return case.expected.path in changed and _error_pointer(error) == _parent_pointer(case.expected.path)


def _category_for_keyword(keyword: str) -> str:
    if keyword == "required":
        return "required"
    if keyword == "additionalProperties":
        return "unknown_field"
    if keyword == "type":
        return "type"
    if keyword in {"const", "enum"}:
        return "enum"
    if keyword == "pattern":
        return "pattern"
    if keyword in {"maximum", "maxItems", "maxLength", "minimum", "minItems", "minLength"}:
        return "range"
    return "semantic"


def _error_pointer(error: ValidationError) -> str:
    pointer = ""
    for part in error.absolute_path:
        pointer = _join_pointer(pointer, part)
    return pointer


def _join_pointer(pointer: str, value: object) -> str:
    token = str(value).replace("~", "~0").replace("/", "~1")
    return f"{pointer}/{token}"


def _parent_pointer(pointer: str) -> str:
    return pointer.rpartition("/")[0]


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be", errors="surrogatepass")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packages", nargs="+", type=Path)
    args = parser.parse_args(argv)
    failed = False
    for package in args.packages:
        coverage, problems = check_package(package)
        report = {
            "package": package.as_posix(),
            "coverage": [entry.to_dict() for entry in coverage],
            "problems": list(problems),
        }
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
        failed = failed or bool(problems)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
