"""Check every worked client-graph manifest against its executable contract."""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
TESTS = ROOT / "tests"
sys.path.insert(0, str(ROOT / "python"))

from citry_client_graph import (  # noqa: E402
    canonical_json,  # noqa: F401 - compatibility export
    validate_manifest,
    validate_revision,
)

try:
    import jsonschema
except ImportError:
    jsonschema = None

_INDEX_REQUIRED = {"manifest", "expect"}
_INDEX_OPTIONAL = {"locks", "defect", "problem", "harness", "preserveRevision"}


def load_json(path: Path) -> Any:
    """Load one UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf8"))


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any]:
    node: Any = root
    for part in ref.removeprefix("#/").split("/"):
        node = node[part]
    return node  # type: ignore[no-any-return]


def _json_equal(left: Any, right: Any) -> bool:
    """Compare JSON scalars without Python's ``True == 1`` equivalence."""
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    return bool(left == right)


def _has_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        return isinstance(value, float) and math.isfinite(value) and value.is_integer()
    if expected == "null":
        return value is None
    return False


def _structural_errors(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str) -> list[str]:
    """Check the JSON Schema keyword subset used by this protocol."""
    problems: list[str] = []

    # 2020-12: $ref applies in conjunction with its sibling keywords.
    if "$ref" in schema:
        problems += _structural_errors(value, _resolve_ref(schema["$ref"], root), root, path)

    if "type" in schema and not _has_type(value, schema["type"]):
        problems.append(f"{path}: expected type {schema['type']}")
        return problems

    if "const" in schema and not _json_equal(value, schema["const"]):
        problems.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and not any(_json_equal(value, option) for option in schema["enum"]):
        problems.append(f"{path}: {value!r} not in enum {schema['enum']!r}")

    if "oneOf" in schema:
        matches = sum(1 for branch in schema["oneOf"] if not _structural_errors(value, branch, root, path))
        if matches == 0:
            problems.append(f"{path}: is not valid under any of the given schemas")
        elif matches > 1:
            problems.append(f"{path}: {matches} oneOf branches matched, expected exactly 1")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                problems.append(f"{path}: missing required member {key!r}")
        declared = schema.get("properties", {})
        for key, sub_schema in declared.items():
            if key in value:
                problems += _structural_errors(value[key], sub_schema, root, f"{path}.{key}")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in declared:
                    problems.append(f"{path}: unknown member {key!r}")
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            problems += _structural_errors(item, schema["items"], root, f"{path}[{index}]")
    if isinstance(value, str) and "pattern" in schema and re.search(schema["pattern"], value) is None:
        problems.append(f"{path}: does not match pattern {schema['pattern']!r}")

    if _has_type(value, "integer") and "minimum" in schema and value < schema["minimum"]:
        problems.append(f"{path}: below minimum {schema['minimum']}")

    if _has_type(value, "integer") and "maximum" in schema and value > schema["maximum"]:
        problems.append(f"{path}: above maximum {schema['maximum']}")
    return problems


def schema_errors(value: Any, schema: dict[str, Any]) -> list[str]:
    """Validate with jsonschema when available, or the standard-library reader."""
    if jsonschema is not None:
        validator = jsonschema.Draft202012Validator(schema)
        return [error.message for error in validator.iter_errors(value)]
    return _structural_errors(value, schema, schema, "$")


def check_manifest(manifest: Any, schema: dict[str, Any]) -> list[str]:
    """Return schema problems plus the executable package's first issue."""
    problems = schema_errors(manifest, schema)
    revision_issue = validate_revision(manifest)
    if revision_issue is not None:
        problems.append(f"{revision_issue.path}: {revision_issue.message}")
    issue = validate_manifest(manifest)
    if issue is not None and issue != revision_issue:
        problems.append(f"{issue.path or '/'}: {issue.message}")
    return problems


def check_index_entries(index: Any, problems: list[str]) -> list[dict[str, Any]]:
    """Shape-check index.json and return its usable entries."""
    if not isinstance(index, list):
        problems.append("index.json: expected a top-level array")
        return []
    entries: list[dict[str, Any]] = []
    for index_position, entry in enumerate(index):
        if not isinstance(entry, dict) or not set(entry) >= _INDEX_REQUIRED:
            problems.append(f"index.json[{index_position}]: entry must have at least the keys manifest and expect")
            continue
        unknown = set(entry) - _INDEX_REQUIRED - _INDEX_OPTIONAL
        if unknown:
            problems.append(f"index.json[{index_position}]: unknown keys {sorted(unknown)}")
            continue
        if not isinstance(entry["manifest"], str) or entry["expect"] not in {"valid", "invalid"}:
            problems.append(f"index.json[{index_position}]: manifest must be a string and expect 'valid' or 'invalid'")
            continue
        if entry["expect"] == "invalid" and not isinstance(entry.get("problem"), str):
            problems.append(f"index.json[{index_position}]: an invalid fixture must declare its expected problem")
            continue
        if entry["expect"] == "invalid" and not entry["manifest"].startswith("error_"):
            problems.append(
                f"index.json[{index_position}]: invalid fixtures use the error_ prefix: {entry['manifest']}"
            )
            continue
        if entry["expect"] == "valid" and entry["manifest"].startswith("error_"):
            problems.append(f"index.json[{index_position}]: valid fixtures must not use the error_ prefix")
            continue
        entries.append(entry)
    return entries


def check_index_matches_disk(
    entries: list[dict[str, Any]],
    problems: list[str],
    fixtures_dir: Path = TESTS,
) -> None:
    """Require the fixture index and manifest files to name the same set."""
    listed = [entry["manifest"] for entry in entries]
    for name in listed:
        if not (fixtures_dir / name).is_file():
            problems.append(f"index.json lists {name}, which does not exist")
    seen: set[str] = set()
    for name in listed:
        if name in seen:
            problems.append(f"index.json lists {name} more than once")
        seen.add(name)
    on_disk = {path.name for path in fixtures_dir.glob("*.manifest.json")}
    for name in sorted(on_disk - seen):
        problems.append(f"{name} exists on disk but is not listed in index.json")


def check_fixture(entry: dict[str, Any], schema: dict[str, Any], fixtures_dir: Path = TESTS) -> list[str]:
    """Check one fixture against its declared valid or invalid result."""
    name = entry["manifest"]
    try:
        manifest = load_json(fixtures_dir / name)
    except (OSError, json.JSONDecodeError) as error:
        return [f"{name}: cannot load: {error}"]
    found = check_manifest(manifest, schema)
    if entry["expect"] == "valid":
        return [f"{name}: {problem}" for problem in found]
    if not found:
        return [f"{name}: expected an invalid manifest, but every check passed"]
    needle = entry["problem"]
    if not any(needle in problem for problem in found):
        return [f"{name}: no problem contains {needle!r}; found: {found}"]
    return []


def main() -> int:
    """Run the standalone fixture checker."""
    schema = load_json(ROOT / "manifest.schema.json")
    problems: list[str] = []
    try:
        index = load_json(TESTS / "index.json")
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL index.json: cannot load: {error}", file=sys.stderr)  # noqa: T201 - validator CLI
        return 1
    entries = check_index_entries(index, problems)
    check_index_matches_disk(entries, problems)
    for entry in entries:
        problems.extend(check_fixture(entry, schema))
    backend = "jsonschema" if jsonschema is not None else "built-in checker"
    if problems:
        print("\n".join(problems), file=sys.stderr)  # noqa: T201 - validator CLI
        return 1
    print(f"citry-client-graph/1 fixtures: ok ({len(entries)} fixtures, {backend})")  # noqa: T201 - validator CLI
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
