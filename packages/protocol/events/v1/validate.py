"""
Self-check for the citry-events/1 protocol package.

Checks the request/response exchanges, component-class descriptors, and full
browser manifests in ``tests/`` against their schemas and semantic rules. It
also checks that every declared dynamic field resolves. Run it directly:

    .venv/bin/python packages/protocol/events/v1/validate.py

The script prefers the ``jsonschema`` package when it is importable and
otherwise falls back to a built-in structural checker that implements exactly
the keywords these schemas use. The same checks run in CI:
``packages/py/citry/tests/test_events_protocol_package.py`` loads this file by
path and drives the check functions through pytest. The direct run stays
dependency-free so binding authors in other languages can check the package
without pytest.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    jsonschema = None

ROOT = Path(__file__).resolve().parent
TESTS_DIR = ROOT / "tests"
DESCRIPTORS_DIR = TESTS_DIR / "descriptors"
MANIFESTS_DIR = TESTS_DIR / "manifests"

# Envelope-level rejections are answered before per-call processing, so their
# exchange calls are deliberately non-conforming uplink (tests/README.md,
# "Deliberately non-conforming calls").
ENVELOPE_REJECTION_CODES = {"protocol_mismatch", "payload_too_large"}
BASELINE_SWAPS = {"replace", "inner", "append", "prepend", "remove", "none"}
BASELINE_ACTIONS = {"render", "data", "state", "event", "redirect", "url"}

# Matches one path segment of the dynamic-field grammar: `.key` or `[n]`.
_SEGMENT_RE = re.compile(r"\.([A-Za-z0-9_]+)|\[([0-9]+)\]")


def _json_equal(left: Any, right: Any) -> bool:
    """Equality that keeps JSON types apart (in Python, True == 1; in JSON they differ)."""
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    return bool(left == right)


def _has_type(value: Any, expected: str | list[str]) -> bool:
    if isinstance(expected, list):
        return any(_has_type(value, item) for item in expected)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any]:
    node: Any = root
    for part in ref.removeprefix("#/").split("/"):
        node = node[part]
    return node  # type: ignore[no-any-return]


def _json_value_errors(value: Any, path: str = "$", ancestors: set[int] | None = None) -> list[str]:
    """Reject values that cannot exist in the protocol's strict JSON data model."""
    if value is None or isinstance(value, (str, bool, int)):
        return []
    if isinstance(value, float):
        return [] if math.isfinite(value) else [f"{path}: non-finite number is not strict JSON"]
    if not isinstance(value, (dict, list)):
        return [f"{path}: {type(value).__name__} is not a JSON value"]
    seen = ancestors or set()
    identity = id(value)
    if identity in seen:
        return [f"{path}: cyclic value is not strict JSON"]
    seen.add(identity)
    problems: list[str] = []
    if isinstance(value, list):
        for index, item in enumerate(value):
            problems += _json_value_errors(item, f"{path}[{index}]", seen)
    else:
        for key, item in value.items():
            if not isinstance(key, str):
                problems.append(f"{path}: object key {key!r} is not a string")
                continue
            problems += _json_value_errors(item, f"{path}.{key}", seen)
    seen.remove(identity)
    return problems


def _validate(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str) -> list[str]:
    """
    Validate `value` against `schema`, returning problem strings (empty when valid).

    Implements the subset of JSON Schema 2020-12 these four schemas use; an
    unknown keyword is deliberately ignored, like the real thing.
    """
    problems: list[str] = []

    # 2020-12: $ref applies in conjunction with its sibling keywords.
    if "$ref" in schema:
        problems += _validate(value, _resolve_ref(schema["$ref"], root), root, path)

    if "type" in schema and not _has_type(value, schema["type"]):
        problems.append(f"{path}: expected type {schema['type']}")
        return problems

    if "const" in schema and not _json_equal(value, schema["const"]):
        problems.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and not any(_json_equal(value, option) for option in schema["enum"]):
        problems.append(f"{path}: {value!r} not in enum {schema['enum']!r}")
    if "not" in schema and not _validate(value, schema["not"], root, path):
        problems.append(f"{path}: matches a schema it must not match")

    if "oneOf" in schema:
        matches = sum(1 for branch in schema["oneOf"] if not _validate(value, branch, root, path))
        if matches != 1:
            problems.append(f"{path}: {matches} oneOf branches matched, expected exactly 1")

    for branch in schema.get("allOf", []):
        problems += _validate(value, branch, root, path)

    if "if" in schema:
        branch = schema.get("then") if not _validate(value, schema["if"], root, path) else schema.get("else")
        if isinstance(branch, dict):
            problems += _validate(value, branch, root, path)

    if isinstance(value, dict):
        if isinstance(schema.get("propertyNames"), dict):
            for key in value:
                problems += _validate(key, schema["propertyNames"], root, f"{path}.<key>")
        for key in schema.get("required", []):
            if key not in value:
                problems.append(f"{path}: missing required member {key!r}")
        declared = schema.get("properties", {})
        for key, sub_schema in declared.items():
            if key in value:
                problems += _validate(value[key], sub_schema, root, f"{path}.{key}")
        extra_schema = schema.get("additionalProperties")
        if extra_schema is False:
            for key in value:
                if key not in declared:
                    problems.append(f"{path}: unknown member {key!r}")
        elif isinstance(extra_schema, dict):
            for key, member in value.items():
                if key not in declared:
                    problems += _validate(member, extra_schema, root, f"{path}.{key}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            problems.append(f"{path}: {len(value)} items, minimum is {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            problems.append(f"{path}: {len(value)} items, maximum is {schema['maxItems']}")
        if "items" in schema:
            for i, item in enumerate(value):
                problems += _validate(item, schema["items"], root, f"{path}[{i}]")
        if schema.get("uniqueItems") is True:
            for i, item in enumerate(value):
                if any(_json_equal(item, previous) for previous in value[:i]):
                    problems.append(f"{path}[{i}]: duplicate item is forbidden by uniqueItems")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            problems.append(f"{path}: shorter than minLength {schema['minLength']}")
        # JSON Schema patterns are unanchored: a match anywhere satisfies them.
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            problems.append(f"{path}: does not match pattern {schema['pattern']!r}")

    if _has_type(value, "number") and "minimum" in schema and value < schema["minimum"]:
        problems.append(f"{path}: below minimum {schema['minimum']}")
    if _has_type(value, "number") and "maximum" in schema and value > schema["maximum"]:
        problems.append(f"{path}: above maximum {schema['maximum']}")

    return problems


def schema_errors(value: Any, schema: dict[str, Any]) -> list[str]:
    """Validate with the jsonschema package when available, else the built-in checker."""
    json_problems = _json_value_errors(value)
    if json_problems:
        return json_problems
    if jsonschema is not None:
        validator = jsonschema.Draft202012Validator(schema)
        return [f"$.{'.'.join(str(p) for p in error.path)}: {error.message}" for error in validator.iter_errors(value)]
    return _validate(value, schema, schema, "$")


def load_json(path: Path, problems: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"{path.name}: cannot load: {exc}")
        return None


def _resolve_dynamic_field(doc: Any, path: str) -> bool:
    """Walk a dynamic-field path (grammar in tests/README.md); True when it resolves."""
    text = "." + path
    pos = 0
    node = doc
    while pos < len(text):
        segment = _SEGMENT_RE.match(text, pos)
        if segment is None:
            return False
        pos = segment.end()
        key, index = segment.group(1), segment.group(2)
        if key is not None:
            if not isinstance(node, dict) or key not in node:
                return False
            node = node[key]
        else:
            position = int(index)
            if not isinstance(node, list) or position >= len(node):
                return False
            node = node[position]
    return True


def _is_envelope_rejection(result_env: Any) -> bool:
    """True when every result item is an error carrying an envelope-rejection code."""
    results = result_env.get("results") if isinstance(result_env, dict) else None
    if not isinstance(results, list) or not results:
        return False
    return all(
        isinstance(item, dict)
        and item.get("ok") is False
        and isinstance(item.get("error"), dict)
        and item["error"].get("code") in ENVELOPE_REJECTION_CODES
        for item in results
    )


def _rejection_input_errors(call: Any, result: Any, call_schema: dict[str, Any]) -> list[str]:
    """Validate every part of a deliberately rejected input except its one locked fault."""
    if not isinstance(call, dict) or not isinstance(result, dict):
        return ["rejection input must be an object"]
    results = result.get("results")
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        return ["rejection result must contain at least one result object"]
    error = results[0].get("error")
    code = error.get("code") if isinstance(error, dict) else None
    corrected = dict(call)
    if code == "protocol_mismatch":
        if call.get("protocol") == "citry-events/1":
            return ["protocol_mismatch input does not carry an unknown protocol"]
        corrected["protocol"] = "citry-events/1"
    elif code == "payload_too_large":
        calls = call.get("calls")
        if not isinstance(calls, list) or len(calls) <= 16:
            return ["payload_too_large input does not exceed the 16-call cap"]
        corrected["calls"] = calls[:16]
    else:
        return [f"unsupported envelope-rejection example code {code!r}"]
    return schema_errors(corrected, call_schema)


def check_index_entries(index: Any, problems: list[str]) -> list[dict[str, Any]]:
    """Shape-check index.json and return its usable entries."""
    if not isinstance(index, list):
        problems.append("index.json: expected a top-level array")
        return []
    entries: list[dict[str, Any]] = []
    for i, entry in enumerate(index):
        if not isinstance(entry, dict) or set(entry) != {"call", "result", "dynamic_fields"}:
            problems.append(f"index.json[{i}]: entry must have exactly the keys call, result, dynamic_fields")
            continue
        # Wrong value types would crash the checks below; report them as FAIL lines instead.
        if (
            not isinstance(entry["call"], str)
            or not isinstance(entry["result"], str)
            or not isinstance(entry["dynamic_fields"], list)
            or not all(isinstance(path, str) for path in entry["dynamic_fields"])
        ):
            problems.append(f"index.json[{i}]: call and result must be strings and dynamic_fields a list of strings")
            continue
        stem = entry["call"].removesuffix(".call.json")
        if entry["call"] != f"{stem}.call.json" or entry["result"] != f"{stem}.result.json":
            problems.append(f"index.json[{i}]: call/result names do not share a stem: {entry['call']}")
            continue
        entries.append(entry)
    return entries


def check_index_matches_disk(
    entries: list[dict[str, Any]],
    problems: list[str],
    tests_dir: Path = TESTS_DIR,
) -> None:
    listed = [name for entry in entries for name in (entry["call"], entry["result"])]
    for name in listed:
        if not (tests_dir / name).is_file():
            problems.append(f"index.json lists {name}, which does not exist")
    seen: set[str] = set()
    for name in listed:
        if name in seen:
            problems.append(f"index.json lists {name} more than once")
        seen.add(name)
    on_disk = {path.name for path in tests_dir.glob("*.call.json")}
    on_disk |= {path.name for path in tests_dir.glob("*.result.json")}
    for name in sorted(on_disk - seen):
        problems.append(f"{name} exists on disk but is not listed in index.json")


def check_exchange(
    entry: dict[str, Any],
    call_schema: dict[str, Any],
    result_schema: dict[str, Any],
    problems: list[str],
    tests_dir: Path = TESTS_DIR,
) -> None:
    call_name, result_name = entry["call"], entry["result"]
    call = load_json(tests_dir / call_name, problems)
    result = load_json(tests_dir / result_name, problems)
    if call is None or result is None:
        return

    for problem in schema_errors(result, result_schema):
        problems.append(f"{result_name}: {problem}")

    if _is_envelope_rejection(result):
        call_problems = _rejection_input_errors(call, result, call_schema)
    else:
        call_problems = schema_errors(call, call_schema)
    problems += [f"{call_name}: {problem}" for problem in call_problems]

    calls = call.get("calls")
    results = result.get("results")
    if isinstance(calls, list) and isinstance(results, list) and len(calls) != len(results):
        problems.append(f"{result_name}: {len(results)} results answer {len(calls)} calls")
    if call.get("requestId") != result.get("requestId"):
        problems.append(
            f"{result_name}: requestId {result.get('requestId')!r} does not echo the call's {call.get('requestId')!r}"
        )

    if isinstance(calls, list) and isinstance(results, list):
        for i, (call_item, result_item) in enumerate(zip(calls, results, strict=False)):
            if not isinstance(call_item, dict) or not isinstance(result_item, dict):
                continue
            sent = call_item.get("sendSequence")
            answered = result_item.get("sendSequence")
            if sent != answered and (sent is not None or answered is not None):
                problems.append(f"{result_name}: results[{i}].sendSequence {answered!r} does not echo {sent!r}")
            actions = result_item.get("actions")
            if isinstance(actions, list):
                data_count = sum(isinstance(action, dict) and action.get("action") == "data" for action in actions)
                if data_count > 1:
                    problems.append(
                        f"{result_name}: results[{i}] carries {data_count} data actions; at most one is valid"
                    )

    problems += [f"{result_name}: {problem}" for problem in capability_errors(call, result)]

    if _is_envelope_rejection(result) and isinstance(results, list):
        first_error = results[0].get("error") if isinstance(results[0], dict) else None
        if any(not isinstance(item, dict) or item.get("error") != first_error for item in results[1:]):
            problems.append(f"{result_name}: envelope rejection results must carry identical errors")

    docs = {"call": call, "result": result}
    for dynamic in entry["dynamic_fields"]:
        prefix, _, rest = str(dynamic).partition(".")
        if prefix not in docs or not rest:
            problems.append(f"{call_name}: dynamic field {dynamic!r} must start with 'call.' or 'result.'")
        elif not _resolve_dynamic_field(docs[prefix], rest):
            problems.append(f"{call_name}: dynamic field {dynamic!r} does not resolve")


def capability_errors(call: Any, result: Any) -> list[str]:
    """Report result actions or render swaps outside the caller's advertised set."""
    if not isinstance(call, dict) or not isinstance(result, dict):
        return []
    advertised = call.get("capabilities")
    capabilities = advertised if isinstance(advertised, dict) else {}
    raw_actions = capabilities.get("actions", BASELINE_ACTIONS)
    raw_swaps = capabilities.get("swaps", BASELINE_SWAPS)
    allowed_actions = set(raw_actions) if isinstance(raw_actions, list | set) else set()
    allowed_swaps = set(raw_swaps) if isinstance(raw_swaps, list | set) else set()

    problems: list[str] = []
    results = result.get("results")
    if not isinstance(results, list):
        return problems
    for result_index, item in enumerate(results):
        actions = item.get("actions") if isinstance(item, dict) else None
        if not isinstance(actions, list):
            continue
        for action_index, action in enumerate(actions):
            if not isinstance(action, dict):
                continue
            kind = action.get("action")
            if kind not in allowed_actions:
                problems.append(f"results[{result_index}].actions[{action_index}] uses unadvertised action {kind!r}")
            if kind == "render" and action.get("swap") not in allowed_swaps:
                problems.append(
                    f"results[{result_index}].actions[{action_index}] uses unadvertised swap {action.get('swap')!r}"
                )
    return problems


def check_vocabulary_consistency(call_schema: dict[str, Any], result_schema: dict[str, Any]) -> list[str]:
    """The swap and action-kind vocabularies are declared in both schemas; they must agree."""
    problems: list[str] = []
    call_swaps = call_schema["$defs"]["swap"]["enum"]
    result_swaps = result_schema["$defs"]["swap"]["enum"]
    if call_swaps != result_swaps:
        problems.append(f"swap vocabulary differs between schemas: {call_swaps} vs {result_swaps}")
    call_kinds = set(call_schema["$defs"]["actionKind"]["enum"])
    result_kinds = {
        definition["properties"]["action"]["const"]
        for definition in result_schema["$defs"].values()
        if isinstance(definition, dict) and "properties" in definition and "action" in definition["properties"]
    }
    if call_kinds != result_kinds:
        problems.append(f"action-kind vocabulary differs: {sorted(call_kinds)} vs {sorted(result_kinds)}")
    return problems


def manifest_semantic_errors(manifest: Any) -> list[str]:
    """Check relationships JSON Schema cannot express clearly."""
    if not isinstance(manifest, dict):
        return []
    classes = manifest.get("componentClasses")
    instances = manifest.get("componentInstances")
    if not isinstance(classes, list) or not isinstance(instances, list):
        return []

    problems: list[str] = []
    class_ids: set[str] = set()
    for i, item in enumerate(classes):
        if not isinstance(item, dict) or not isinstance(item.get("componentClassId"), str):
            continue
        class_id = item["componentClassId"]
        if class_id in class_ids:
            problems.append(f"$.componentClasses[{i}]: duplicate componentClassId {class_id!r}")
        class_ids.add(class_id)

    render_ids: set[str] = set()
    for i, item in enumerate(instances):
        if not isinstance(item, dict):
            continue
        render_id = item.get("renderId")
        class_id = item.get("componentClassId")
        if isinstance(render_id, str):
            if render_id in render_ids:
                problems.append(f"$.componentInstances[{i}]: duplicate renderId {render_id!r}")
            render_ids.add(render_id)
        if isinstance(class_id, str) and class_id not in class_ids:
            problems.append(f"$.componentInstances[{i}]: componentClassId {class_id!r} has no componentClasses record")
        if item.get("stateToken") is None and item.get("publicState") not in ({}, None):
            problems.append(f"$.componentInstances[{i}]: a stateless instance must carry an empty publicState object")
    return problems


def check_corpus(
    *,
    label: str,
    directory: Path,
    schema: dict[str, Any],
    problems: list[str],
    semantic_check: Any | None = None,
) -> int:
    """Validate a positive/negative JSON corpus listed by its own index.json."""
    index = load_json(directory / "index.json", problems)
    if not isinstance(index, list):
        problems.append(f"{label}/index.json: expected a top-level array")
        return 0
    listed: set[str] = set()
    for i, entry in enumerate(index):
        if not isinstance(entry, dict) or set(entry) != {"file", "valid"}:
            problems.append(f"{label}/index.json[{i}]: expected exactly file and valid")
            continue
        name, expected_valid = entry["file"], entry["valid"]
        if not isinstance(name, str) or not isinstance(expected_valid, bool):
            problems.append(f"{label}/index.json[{i}]: file must be text and valid a boolean")
            continue
        if name in listed:
            problems.append(f"{label}/index.json lists {name} more than once")
        listed.add(name)
        doc = load_json(directory / name, problems)
        if doc is None:
            continue
        errors = schema_errors(doc, schema)
        if semantic_check is not None:
            errors += semantic_check(doc)
        actual_valid = not errors
        if actual_valid != expected_valid:
            expectation = "valid" if expected_valid else "invalid"
            detail = "; ".join(errors[:3]) if errors else "no validation problem was found"
            problems.append(f"{label}/{name}: expected {expectation}; {detail}")

    on_disk = {path.name for path in directory.glob("*.valid.json")}
    on_disk |= {path.name for path in directory.glob("*.invalid.json")}
    for name in sorted(on_disk - listed):
        problems.append(f"{label}/{name} exists on disk but is not listed in index.json")
    for name in sorted(listed - on_disk):
        problems.append(f"{label}/index.json lists {name}, which does not exist")
    return len(index)


def main() -> int:
    problems: list[str] = []

    call_schema = load_json(ROOT / "call.schema.json", problems)
    result_schema = load_json(ROOT / "result.schema.json", problems)
    descriptor_schema = load_json(ROOT / "descriptor.schema.json", problems)
    manifest_schema = load_json(ROOT / "manifest.schema.json", problems)
    index = load_json(TESTS_DIR / "index.json", problems)
    if problems:
        for problem in problems:
            sys.stderr.write(f"FAIL {problem}\n")
        return 1

    problems += check_vocabulary_consistency(call_schema, result_schema)

    entries = check_index_entries(index, problems)
    check_index_matches_disk(entries, problems)
    for entry in entries:
        check_exchange(entry, call_schema, result_schema, problems)
    descriptor_count = check_corpus(
        label="descriptors",
        directory=DESCRIPTORS_DIR,
        schema=descriptor_schema,
        problems=problems,
    )
    manifest_count = check_corpus(
        label="manifests",
        directory=MANIFESTS_DIR,
        schema=manifest_schema,
        problems=problems,
        semantic_check=manifest_semantic_errors,
    )

    backend = "jsonschema" if jsonschema is not None else "built-in checker"
    if problems:
        for problem in problems:
            sys.stderr.write(f"FAIL {problem}\n")
        sys.stderr.write(
            f"\n{len(problems)} problem(s) across {len(entries)} exchanges, "
            f"{descriptor_count} descriptors, and {manifest_count} manifests ({backend}).\n"
        )
        return 1
    sys.stdout.write(
        f"OK: {len(entries)} exchanges, {descriptor_count} descriptors, and "
        f"{manifest_count} manifests validate ({backend}).\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
