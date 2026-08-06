"""Check which runtime validators own each schema constraint."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

from .contracts import Constraint, ContractToolError, load_json_value

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

OWNERSHIP_FORMAT: Final = "citry-protocol-constraint-ownership/1"
_FAMILY_FIELDS: Final = {
    "id",
    "schema",
    "exactSchemaPointers",
    "schemaPointerPrefixes",
    "pythonValidators",
    "javascriptValidators",
    "tests",
    "constraintCount",
    "constraintSha256",
}


@dataclass(frozen=True, slots=True)
class OwnershipSummary:
    """How many constraints one schema assigns to named validator families."""

    schema: str
    total: int
    assigned: int
    families: int

    def to_dict(self) -> dict[str, int | str]:
        """Return the stable command-line report shape."""
        return {
            "schema": self.schema,
            "total": self.total,
            "assigned": self.assigned,
            "families": self.families,
        }


@dataclass(frozen=True, slots=True)
class OwnershipFamily:
    """One schema area and the runtime validators and tests responsible for it."""

    family_id: str
    schema: str
    exact_schema_pointers: tuple[str, ...]
    schema_pointer_prefixes: tuple[str, ...]
    python_validators: tuple[str, ...]
    javascript_validators: tuple[str, ...]
    tests: tuple[str, ...]
    constraint_count: int
    constraint_sha256: str

    def matches(self, constraint: Constraint) -> bool:
        """Return whether this family selects one concrete constraint."""
        pointer = constraint.schema_pointer
        if pointer in self.exact_schema_pointers:
            return True
        return any(pointer == prefix or pointer.startswith(f"{prefix}/") for prefix in self.schema_pointer_prefixes)


def constraint_fingerprint(constraints: Sequence[Constraint]) -> str:
    """Hash constraint identities and values using stable JSON bytes."""
    payload = [constraint.to_dict() for constraint in sorted(constraints, key=lambda entry: entry.constraint_id)]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def check_constraint_ownership(
    package_root: Path,
    inventories: Mapping[str, Mapping[str, Constraint]],
) -> tuple[tuple[OwnershipSummary, ...], tuple[str, ...]]:
    """Require every inventoried constraint to have one fail-closed owner."""
    registry_path = package_root / "tests" / "constraint-ownership.json"
    try:
        families = _load_families(registry_path)
    except ContractToolError as error:
        return (), (str(error),)

    problems: list[str] = []
    known_schemas = set(inventories)
    family_ids: set[str] = set()
    by_schema: dict[str, list[OwnershipFamily]] = {schema: [] for schema in known_schemas}
    for family in families:
        if family.family_id in family_ids:
            problems.append(f"duplicate ownership family id {family.family_id!r}")
        family_ids.add(family.family_id)
        if family.schema not in known_schemas:
            problems.append(f"{family.family_id}: unknown schema {family.schema!r}")
            continue
        by_schema[family.schema].append(family)
        _check_references(package_root, family, problems)

    summaries: list[OwnershipSummary] = []
    for schema in sorted(inventories):
        constraints = inventories[schema]
        schema_families = by_schema[schema]
        matched_by_family: dict[str, list[Constraint]] = {family.family_id: [] for family in schema_families}
        assigned = 0
        for constraint in constraints.values():
            matching = [family for family in schema_families if family.matches(constraint)]
            if not matching:
                problems.append(f"{schema}: unassigned constraint {constraint.constraint_id!r}")
                continue
            if len(matching) > 1:
                owners = sorted(family.family_id for family in matching)
                problems.append(f"{schema}: constraint {constraint.constraint_id!r} has multiple owners {owners!r}")
                continue
            assigned += 1
            matched_by_family[matching[0].family_id].append(constraint)

        for family in schema_families:
            matched = matched_by_family[family.family_id]
            observed_count = len(matched)
            observed_sha256 = constraint_fingerprint(matched)
            if observed_count != family.constraint_count or observed_sha256 != family.constraint_sha256:
                problems.append(
                    f"{family.family_id}: constraint inventory changed; "
                    f"observed count {observed_count} and sha256 {observed_sha256}"
                )

        summaries.append(
            OwnershipSummary(
                schema=schema,
                total=len(constraints),
                assigned=assigned,
                families=len(schema_families),
            )
        )
    return tuple(summaries), tuple(problems)


def _load_families(path: Path) -> tuple[OwnershipFamily, ...]:
    payload = load_json_value(path)
    if not isinstance(payload, dict) or set(payload) != {"format", "families"}:
        raise ContractToolError(f"{path}: ownership registry must contain only 'format' and 'families'")
    if payload["format"] != OWNERSHIP_FORMAT:
        raise ContractToolError(f"{path}: unsupported ownership format {payload['format']!r}")
    raw_families = payload["families"]
    if not isinstance(raw_families, list) or not raw_families:
        raise ContractToolError(f"{path}: ownership families must be a non-empty array")
    return tuple(_parse_family(value, path) for value in raw_families)


def _parse_family(value: Any, path: Path) -> OwnershipFamily:
    if not isinstance(value, dict) or set(value) != _FAMILY_FIELDS:
        raise ContractToolError(f"{path}: each ownership family must have the exact v1 fields")
    family_id = _non_empty_string(value["id"], "ownership family id", path)
    exact = _pointer_list(value["exactSchemaPointers"], "exactSchemaPointers", path)
    prefixes = _pointer_list(value["schemaPointerPrefixes"], "schemaPointerPrefixes", path)
    if not exact and not prefixes:
        raise ContractToolError(f"{path}: ownership family {family_id!r} has no selectors")
    if "" in prefixes:
        raise ContractToolError(f"{path}: ownership family {family_id!r} may not use a root subtree selector")
    count = value["constraintCount"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ContractToolError(f"{path}: ownership family {family_id!r} constraintCount must be positive")
    digest = _non_empty_string(value["constraintSha256"], "constraintSha256", path)
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ContractToolError(f"{path}: ownership family {family_id!r} has an invalid constraintSha256")
    return OwnershipFamily(
        family_id=family_id,
        schema=_non_empty_string(value["schema"], "schema", path),
        exact_schema_pointers=exact,
        schema_pointer_prefixes=prefixes,
        python_validators=_string_list(value["pythonValidators"], "pythonValidators", path),
        javascript_validators=_string_list(value["javascriptValidators"], "javascriptValidators", path),
        tests=_string_list(value["tests"], "tests", path),
        constraint_count=count,
        constraint_sha256=digest,
    )


def _pointer_list(value: Any, name: str, path: Path) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ContractToolError(f"{path}: {name} must be an array")
    if any(not isinstance(item, str) for item in value):
        raise ContractToolError(f"{path}: {name} entries must be strings")
    values = tuple(value)
    if len(set(values)) != len(values):
        raise ContractToolError(f"{path}: {name} entries must be unique")
    for pointer in values:
        if pointer and not pointer.startswith("/"):
            raise ContractToolError(f"{path}: {name} entries must be JSON Pointers")
    return values


def _string_list(value: Any, name: str, path: Path, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ContractToolError(f"{path}: {name} must be {'an' if allow_empty else 'a non-empty'} array")
    values = tuple(_non_empty_string(item, name, path) for item in value)
    if len(set(values)) != len(values):
        raise ContractToolError(f"{path}: {name} entries must be unique")
    return values


def _non_empty_string(value: Any, name: str, path: Path) -> str:
    if not isinstance(value, str) or not value:
        raise ContractToolError(f"{path}: {name} must be a non-empty string")
    return value


def _check_references(package_root: Path, family: OwnershipFamily, problems: list[str]) -> None:
    for language, references in (
        ("Python", family.python_validators),
        ("JavaScript", family.javascript_validators),
    ):
        for reference in references:
            relative_path, separator, symbol = reference.rpartition(":")
            if not separator or not relative_path or not symbol:
                problems.append(f"{family.family_id}: invalid {language} validator reference {reference!r}")
                continue
            source_path = package_root / relative_path
            if not source_path.is_file():
                problems.append(f"{family.family_id}: missing {language} validator file {relative_path!r}")
                continue
            if language == "Python":
                try:
                    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
                except (OSError, SyntaxError) as error:
                    problems.append(f"{family.family_id}: cannot parse {relative_path!r}: {error}")
                    continue
                names = {node.name for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))}
                found = symbol in names
            else:
                source = source_path.read_text(encoding="utf-8")
                found = re.search(rf"\b(?:const|function|class)\s+{re.escape(symbol)}\b", source) is not None
            if not found:
                problems.append(f"{family.family_id}: missing {language} validator symbol {reference!r}")

    for test in family.tests:
        if not (package_root / test).is_file():
            problems.append(f"{family.family_id}: missing supporting test file {test!r}")
