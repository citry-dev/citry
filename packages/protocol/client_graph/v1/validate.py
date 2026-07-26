"""
Check that this package's example manifests still behave the way the spec says.

The files in ``fixtures/`` are worked examples of the JSON the server sends the
browser: some are correct manifests a reader should accept, some are
deliberately broken ones a reader should reject. ``fixtures/index.json`` lists
them and says which is which. This script reads that list and confirms each
example behaves as listed: every ``"expect": "valid"`` file passes the JSON
Schema and every rule below, every ``"expect": "invalid"`` file is rejected
with a message that contains the substring its index entry names, and the list
matches the files on disk. Run it directly:

    .venv/bin/python packages/protocol/client_graph/v1/validate.py

It checks the JSON shape with the ``jsonschema`` package when that package is
installed, and otherwise falls back to a small built-in checker that covers
exactly the schema keywords this package uses, so the direct run needs nothing
beyond the standard library. That lets someone writing a Citry binding in
another language check the package without installing anything. The same checks
also run in CI, through
``packages/py/citry/tests/test_client_graph_protocol_package.py``.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    jsonschema = None

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
MAX_MANIFEST_BYTES = 1_000_000
RENDER_ID_RE = re.compile(r"^[a-z0-9_-]+$")

# An index entry may carry only these keys. `manifest` and `expect` are
# required; the rest describe an invalid fixture for the tests that replay it
# (see fixtures/README.md).
_INDEX_REQUIRED = {"manifest", "expect"}
_INDEX_OPTIONAL = {"locks", "defect", "problem", "browserProblem", "harness", "preserveRevision"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf8"))


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any]:
    node: Any = root
    for part in ref.removeprefix("#/").split("/"):
        node = node[part]
    return node  # type: ignore[no-any-return]


def _json_equal(left: Any, right: Any) -> bool:
    """Equality that keeps JSON types apart (in Python, True == 1; in JSON they differ)."""
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
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _structural_errors(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str) -> list[str]:
    """
    Validate `value` against `schema`, returning problem strings (empty when valid).

    Implements the subset of JSON Schema 2020-12 the manifest schema uses; an
    unknown keyword is deliberately ignored, like the real thing.
    """
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
        if matches != 1:
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
        for i, item in enumerate(value):
            problems += _structural_errors(item, schema["items"], root, f"{path}[{i}]")

    if isinstance(value, str) and "pattern" in schema and re.search(schema["pattern"], value) is None:
        problems.append(f"{path}: does not match pattern {schema['pattern']!r}")

    if _has_type(value, "integer") and "minimum" in schema and value < schema["minimum"]:
        problems.append(f"{path}: below minimum {schema['minimum']}")

    return problems


def schema_errors(value: Any, schema: dict[str, Any]) -> list[str]:
    """Validate with the jsonschema package when available, else the built-in checker."""
    if jsonschema is not None:
        validator = jsonschema.Draft202012Validator(schema)
        return [error.message for error in validator.iter_errors(value)]
    return _structural_errors(value, schema, schema, "$")


def component_execution_order_cycle_errors(edges: dict[str, list[str]], graph_index: int) -> list[str]:
    problems: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(render: str) -> None:
        if render in visiting:
            problems.append(f"graphs[{graph_index}] component execution order contains a cycle")
            return
        if render in visited:
            return
        visiting.add(render)
        for child in edges.get(render, []):
            visit(child)
        visiting.remove(render)
        visited.add(render)

    for render in edges:
        visit(render)
    return problems


def instance_cycle_errors(parents: dict[str, str | None], graph_index: int) -> list[str]:
    problems: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(render: str) -> None:
        if render in visiting:
            problems.append(f"graphs[{graph_index}] logical instance ancestry contains a cycle")
            return
        if render in visited:
            return
        visiting.add(render)
        parent = parents.get(render)
        if parent is not None and parent in parents:
            visit(parent)
        visiting.remove(render)
        visited.add(render)

    for render in parents:
        visit(render)
    return problems


def slot_region_cycle_errors(parents: dict[int, int | None], graph_index: int) -> list[str]:
    problems: list[str] = []
    visiting: set[int] = set()
    visited: set[int] = set()

    def visit(slot_region_id: int) -> None:
        if slot_region_id in visiting:
            problems.append(f"graphs[{graph_index}] slot region ancestry contains a cycle")
            return
        if slot_region_id in visited:
            return
        visiting.add(slot_region_id)
        parent = parents.get(slot_region_id)
        if parent is not None and parent in parents:
            visit(parent)
        visiting.remove(slot_region_id)
        visited.add(slot_region_id)

    for slot_region_id in parents:
        visit(slot_region_id)
    return problems


def _relay_key_errors(payload: Any, relay_key: str | None, event: str | None, graph_index: int) -> list[str]:
    """
    The relay key and its payload must agree, the same way the browser checks
    them: the key is the template attribute the relay was authored on, so a
    payload of one kind under another kind's key is a producer bug.
    """
    if relay_key is None or not isinstance(payload, dict):
        return []
    payload_type = payload.get("type")
    problems: list[str] = []
    if payload_type == "props" and relay_key != "$c-props":
        problems.append(f"graphs[{graph_index}] props relay payload must use the $c-props relay key")
    if payload_type == "alpine-handler" and not (
        (relay_key.startswith("@") and not relay_key.startswith("@c-")) or relay_key.startswith("x-on:")
    ):
        problems.append(f"graphs[{graph_index}] Alpine-handler relay payload has a non-Alpine relay key")
    if payload_type == "citry-dom-event":
        # The event segment decides poll-vs-DOM-event, matching the server's
        # classifier: "@c-poll.5s" is a poll, "@c-pollchange" is a DOM event.
        if not relay_key.startswith("@c-") or relay_key[3:].split(".")[0] == "poll":
            problems.append(f"graphs[{graph_index}] Citry DOM-event relay payload has a non-event relay key")
        elif event is not None and relay_key[3:].split(".")[0] != event:
            problems.append(f"graphs[{graph_index}] Citry DOM-event relay payload disagrees with its relay key")
    if payload_type == "citry-poll" and not relay_key.startswith("@c-poll."):
        problems.append(f"graphs[{graph_index}] Citry poll relay payload must use an @c-poll relay key")
    return problems


def semantic_errors(manifest: Any) -> list[str]:
    problems: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest is not an object"]
    encoded_size = len(json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode("utf8"))
    if encoded_size > MAX_MANIFEST_BYTES:
        problems.append(f"manifest is {encoded_size} bytes; the limit is {MAX_MANIFEST_BYTES}")
    unsigned = {key: value for key, value in manifest.items() if key != "revision"}
    canonical = json.dumps(unsigned, separators=(",", ":"), sort_keys=True).encode("utf8")
    expected = hashlib.sha256(canonical).hexdigest()
    if manifest.get("revision") != expected:
        problems.append("revision does not match the canonical unsigned manifest")

    # Development ships source provenance (the source locations and every
    # reference to them); production keeps that collection empty and nulls the
    # references (dev_prod_mode.md). Source-location checks run only in
    # development, where there are records to check against.
    dev = manifest.get("mode") == "development"

    graphs = manifest.get("graphs", [])
    if not isinstance(graphs, list):
        return [*problems, "graphs is not an array"]

    id_field = {
        "componentInstances": "instanceId",
        "sourceLocations": "locationId",
        "nestedComponents": "invocationId",
        "fills": "fillId",
        "slotRegions": "regionId",
    }
    # Render ids are unique across the whole manifest, not just within one
    # graph: they become physical `data-cid` markers in one shared document.
    all_renders: set[str] = set()

    for graph_index, graph in enumerate(graphs):
        if not isinstance(graph, dict):
            problems.append(f"graphs[{graph_index}] is not an object")
            continue
        if graph.get("graphId") != graph_index:
            problems.append(f"graphs[{graph_index}].graphId is not dense and ordered")

        ids: dict[str, set[int]] = {}
        for collection, id_key in id_field.items():
            records = graph.get(collection, [])
            values = [
                value
                for record in records
                if isinstance(record, dict)
                and isinstance((value := record.get(id_key)), int)
                and not isinstance(value, bool)
            ]
            ids[collection] = set(values)
            if len(values) != len(ids[collection]):
                problems.append(f"graphs[{graph_index}].{collection} has duplicate ids")

        if not dev:
            # Production must carry no provenance records or references.
            if graph.get("sourceLocations"):
                problems.append(f"graphs[{graph_index}] production manifest has sourceLocations")
            for invocation in graph.get("nestedComponents", []):
                if invocation.get("locationId") is not None:
                    problems.append(f"graphs[{graph_index}] production invocation has a location reference")
                if any(relay.get("locationId") is not None for relay in invocation.get("relays", [])):
                    problems.append(f"graphs[{graph_index}] production relay has a location reference")
            for fill in graph.get("fills", []):
                if fill.get("locationId") is not None or fill.get("fallbackLocationId") is not None:
                    problems.append(f"graphs[{graph_index}] production fill has a location reference")
            for region in graph.get("slotRegions", []):
                if region.get("slotLocationId") is not None or region.get("sourceLocationId") is not None:
                    problems.append(f"graphs[{graph_index}] production slot region has a location reference")

        class_ids: set[str] = set()
        for record in graph.get("componentClasses", []):
            class_id = record.get("classId")
            if class_id in class_ids:
                problems.append(f"graphs[{graph_index}] has duplicate class ids")
            elif class_id is not None:
                class_ids.add(class_id)

        renders: set[str] = set()
        classes_by_render: dict[str, str] = {}
        instances_by_id: dict[int, str] = {}
        instance_records: list[tuple[str | None, str | None, Any]] = []
        instance_parents: dict[str, str | None] = {}
        for index, record in enumerate(graph.get("componentInstances", [])):
            where = f"graphs[{graph_index}].componentInstances[{index}]"
            render = record.get("renderId")
            class_id = record.get("classId")
            if isinstance(render, str) and RENDER_ID_RE.fullmatch(render) is None:
                problems.append(f"{where}.renderId is not safe for an HTML attribute name")
            if class_id is not None and class_id not in class_ids:
                problems.append(f"{where}.classId is unknown")
            if render in renders:
                problems.append(f"graphs[{graph_index}] has duplicate render ids")
            elif render is not None:
                if render in all_renders:
                    problems.append(f"render id '{render}' appears in more than one graph")
                renders.add(render)
                all_renders.add(render)
                if class_id is not None:
                    classes_by_render[render] = class_id
                if isinstance(record.get("instanceId"), int):
                    instances_by_id[record["instanceId"]] = render
            parent = record.get("parentRenderId")
            if render is not None:
                instance_parents[render] = parent
            instance_records.append((render, parent, record.get("invocationId")))
        for index, record in enumerate(graph.get("componentInstances", [])):
            parent = record.get("parentRenderId")
            if parent is not None and parent not in renders:
                problems.append(f"graphs[{graph_index}].componentInstances[{index}].parentRenderId is unknown")

        problems.extend(instance_cycle_errors(instance_parents, graph_index))

        location_owners: dict[int, tuple[str | None, str | None]] = {}
        location_kinds: dict[int, str | None] = {}
        if dev:
            for location in graph.get("sourceLocations", []):
                if location.get("carrierInstanceId") not in ids["componentInstances"]:
                    problems.append(f"graphs[{graph_index}] location has an unknown carrier")
                offset = location.get("sourceOffset", {})
                if offset.get("start", 0) > offset.get("end", 0):
                    problems.append(f"graphs[{graph_index}] location has a reversed byte range")
                owner = location.get("ownerRenderId")
                class_id = location.get("ownerClassId")
                if owner not in renders or (owner is not None and classes_by_render.get(owner) != class_id):
                    problems.append(f"graphs[{graph_index}] location owner is unknown or mismatched")
                if instances_by_id.get(location.get("carrierInstanceId")) != owner:
                    problems.append(f"graphs[{graph_index}] location carrier is mismatched")
                if isinstance(location.get("locationId"), int):
                    location_owners[location["locationId"]] = (owner, class_id)
                    location_kinds[location["locationId"]] = location.get("kind")

        invocation_edges: dict[int, tuple[str | None, str | None]] = {}
        for invocation in graph.get("nestedComponents", []):
            source = invocation.get("sourceRenderId")
            source_class = invocation.get("sourceClassId")
            target = invocation.get("targetRenderId")
            target_class = invocation.get("targetClassId")
            if source not in renders or classes_by_render.get(source) != source_class:
                problems.append(f"graphs[{graph_index}] invocation source is unknown or mismatched")
            if target not in renders or classes_by_render.get(target) != target_class:
                problems.append(f"graphs[{graph_index}] invocation target is unknown or mismatched")
            if dev:
                if invocation.get("locationId") not in ids["sourceLocations"]:
                    problems.append(f"graphs[{graph_index}] invocation has an unknown location")
                if location_owners.get(invocation.get("locationId")) != (source, source_class):
                    problems.append(f"graphs[{graph_index}] invocation location owner is mismatched")
                if location_kinds.get(invocation.get("locationId")) != "component-call":
                    problems.append(f"graphs[{graph_index}] invocation location kind is mismatched")
            parent_region = invocation.get("parentRegionId")
            if parent_region is not None and parent_region not in ids["slotRegions"]:
                problems.append(
                    f"graphs[{graph_index}] nested component parentRegionId references an unknown slot region"
                )
            if isinstance(invocation.get("invocationId"), int):
                invocation_edges[invocation["invocationId"]] = (source, target)
            for relay in invocation.get("relays", []):
                relay_key = relay.get("key")
                if dev:
                    if relay.get("locationId") not in ids["sourceLocations"]:
                        problems.append(f"graphs[{graph_index}] relay has an unknown location")
                    if location_owners.get(relay.get("locationId")) != (source, source_class):
                        problems.append(f"graphs[{graph_index}] relay location owner is mismatched")
                payload = relay.get("payload", {})
                if payload.get("type") in {"citry-dom-event", "citry-poll"} and payload.get("classId") != source_class:
                    problems.append(f"graphs[{graph_index}] Citry relay class is not its source parent")
                problems.extend(_relay_key_errors(payload, relay_key, payload.get("event"), graph_index))

        for record in graph.get("componentInstances", []):
            invocation_id = record.get("invocationId")
            if invocation_id is not None and invocation_id not in ids["nestedComponents"]:
                problems.append(f"graphs[{graph_index}] instance has an unknown invocation")

        for render, parent, invocation_id in instance_records:
            if invocation_id is None:
                if parent is not None:
                    problems.append(f"graphs[{graph_index}] uninvoked instance has a parent")
                continue
            if invocation_edges.get(invocation_id) != (parent, render):
                problems.append(f"graphs[{graph_index}] instance endpoints do not match their invocation")
        for invocation_id in ids["nestedComponents"]:
            targets = [record for record in instance_records if record[2] == invocation_id]
            if len(targets) != 1:
                problems.append(f"graphs[{graph_index}] invocation does not bind exactly one target instance")

        fill_records: dict[int, tuple[str | None, str | None, Any]] = {}
        for fill in graph.get("fills", []):
            owner = fill.get("ownerRenderId")
            owner_class = fill.get("ownerClassId")
            receiver = fill.get("receiverRenderId")
            receiver_class = fill.get("receiverClassId")
            kind = fill.get("kind")
            source_invocation = fill.get("sourceInvocationId")
            if (owner is None) != (owner_class is None) or (
                owner is not None and classes_by_render.get(owner) != owner_class
            ):
                problems.append(f"graphs[{graph_index}] fill owner and class are mismatched")
            if (receiver is None) != (receiver_class is None) or (
                receiver is not None and classes_by_render.get(receiver) != receiver_class
            ):
                problems.append(f"graphs[{graph_index}] fill receiver and class are mismatched")
            if source_invocation is not None and source_invocation not in ids["nestedComponents"]:
                problems.append(f"graphs[{graph_index}] fill has an unknown sourceInvocation")
            source_kind = location_kinds.get(fill.get("locationId"))
            fallback_kind = location_kinds.get(fill.get("fallbackLocationId"))
            if dev:
                for key in ("locationId", "fallbackLocationId"):
                    if fill.get(key) is not None and fill.get(key) not in ids["sourceLocations"]:
                        problems.append(f"graphs[{graph_index}] fill has an unknown {key}")
                source_owner = location_owners.get(fill.get("locationId"))
                fallback_owner = location_owners.get(fill.get("fallbackLocationId"))
                if (owner is None) != (source_owner is None):
                    problems.append(f"graphs[{graph_index}] fill owner and source location are inconsistent")
                if source_owner is not None and source_owner != (owner, owner_class):
                    problems.append(f"graphs[{graph_index}] fill source location owner is mismatched")
                if fallback_owner is not None and fallback_owner != (receiver, receiver_class):
                    problems.append(f"graphs[{graph_index}] fill fallback location receiver is mismatched")
            if fill.get("policy") == "template":
                if owner is None or receiver is None or kind not in {"implicit", "named", "fallback"}:
                    problems.append(f"graphs[{graph_index}] template fill ownership is inconsistent")
                if dev:
                    expected_kind = {
                        "implicit": "implicit-fill",
                        "named": "named-fill",
                        "fallback": "fallback-fill",
                    }.get(kind)
                    if source_kind != expected_kind:
                        problems.append(f"graphs[{graph_index}] template fill source location kind is mismatched")
                    if kind == "fallback" and (
                        fill.get("fallbackLocationId") is None or fallback_kind != "slot-outlet"
                    ):
                        problems.append(f"graphs[{graph_index}] fallback location kind is mismatched")
                    if kind != "fallback" and fill.get("fallbackLocationId") is not None:
                        problems.append(f"graphs[{graph_index}] supplied fill carrier is inconsistent")
                if kind == "fallback":
                    if source_invocation is not None:
                        problems.append(f"graphs[{graph_index}] fallback fill carrier is inconsistent")
                elif source_invocation is None:
                    problems.append(f"graphs[{graph_index}] supplied fill carrier is inconsistent")
                elif invocation_edges.get(source_invocation, (None, None))[0] != owner:
                    problems.append(f"graphs[{graph_index}] supplied fill source invocation owner is mismatched")
            elif fill.get("policy") == "python-detached":
                if (
                    kind != "python"
                    or owner is not None
                    or receiver is None
                    or source_invocation is not None
                    or fill.get("fallbackLocationId") is not None
                ):
                    problems.append(f"graphs[{graph_index}] detached Python fill ownership is inconsistent")
            elif (
                kind != "typed-default"
                or owner is not None
                or receiver is None
                or source_invocation is not None
                or fill.get("fallbackLocationId") is not None
            ):
                problems.append(f"graphs[{graph_index}] detached typed-default fill ownership is inconsistent")
            if isinstance(fill.get("fillId"), int):
                fill_records[fill["fillId"]] = (owner, receiver, fill.get("locationId"))

        slot_region_records: dict[int, tuple[str | None, str | None, Any, str | None]] = {}
        for slot_region in graph.get("slotRegions", []):
            if slot_region.get("fillId") not in ids["fills"]:
                problems.append(f"graphs[{graph_index}] slot region has an unknown fill")
            if (
                slot_region.get("parentRegionId") is not None
                and slot_region.get("parentRegionId") not in ids["slotRegions"]
            ):
                problems.append(f"graphs[{graph_index}] slot region has an unknown parent")
            resolved_slot_region = {
                "receiver": slot_region.get("receiverRenderId"),
                "owner": slot_region.get("ownerRenderId"),
                "transitionFrom": slot_region.get("transitionFromRenderId"),
                "resultOwner": slot_region.get("resultOwnerRenderId"),
            }
            for key, render in resolved_slot_region.items():
                if render is not None and render not in renders:
                    problems.append(f"graphs[{graph_index}] slot region.{key} is unknown")
            if dev:
                for key in ("slotLocationId", "sourceLocationId"):
                    if slot_region.get(key) is not None and slot_region.get(key) not in ids["sourceLocations"]:
                        problems.append(f"graphs[{graph_index}] slot region has an unknown {key}")
                slot_owner = location_owners.get(slot_region.get("slotLocationId"))
                if slot_owner is not None and slot_owner[0] != resolved_slot_region["receiver"]:
                    problems.append(f"graphs[{graph_index}] slot region slot location receiver is mismatched")
                if (
                    slot_region.get("slotLocationId") is not None
                    and location_kinds.get(slot_region.get("slotLocationId")) != "slot-outlet"
                ):
                    problems.append(f"graphs[{graph_index}] slot region slot location kind is mismatched")
            fill_record = fill_records.get(slot_region.get("fillId"))
            actual = (
                resolved_slot_region["owner"],
                resolved_slot_region["receiver"],
                slot_region.get("sourceLocationId"),
            )
            if fill_record != actual:
                problems.append(f"graphs[{graph_index}] slot region ownership does not match its fill")
            if isinstance(slot_region.get("regionId"), int):
                slot_region_records[slot_region["regionId"]] = (
                    resolved_slot_region["owner"],
                    resolved_slot_region["receiver"],
                    slot_region.get("parentRegionId"),
                    resolved_slot_region["transitionFrom"],
                )

        slot_region_parents = {
            slot_region_id: parent if isinstance(parent, int) else None
            for slot_region_id, (_, _, parent, _) in slot_region_records.items()
        }
        problems.extend(slot_region_cycle_errors(slot_region_parents, graph_index))
        for _owner, receiver, parent, transition_from in slot_region_records.values():
            expected_transition = (
                receiver if parent is None else slot_region_records.get(parent, (None, None, None, None))[0]
            )
            if transition_from != expected_transition:
                problems.append(f"graphs[{graph_index}] slot region scope transition does not match its ancestry")

        execution_constraints_by_parent: dict[str, list[str]] = {}
        for record in graph.get("componentExecutionOrderConstraints", []):
            parent = record.get("parentRenderId")
            child = record.get("childRenderId")
            edge = invocation_edges.get(record.get("invocationId"))
            if edge != (parent, child):
                problems.append(
                    f"graphs[{graph_index}] component execution order constraint does not match its invocation"
                )
            if isinstance(parent, str) and isinstance(child, str):
                execution_constraints_by_parent.setdefault(parent, []).append(child)

        problems.extend(component_execution_order_cycle_errors(execution_constraints_by_parent, graph_index))
    return problems


def check_manifest(manifest: Any, schema: dict[str, Any]) -> list[str]:
    return [*schema_errors(manifest, schema), *semantic_errors(manifest)]


def check_index_entries(index: Any, problems: list[str]) -> list[dict[str, Any]]:
    """Shape-check index.json and return its usable entries."""
    if not isinstance(index, list):
        problems.append("index.json: expected a top-level array")
        return []
    entries: list[dict[str, Any]] = []
    for i, entry in enumerate(index):
        if not isinstance(entry, dict) or not set(entry) >= _INDEX_REQUIRED:
            problems.append(f"index.json[{i}]: entry must have at least the keys manifest and expect")
            continue
        unknown = set(entry) - _INDEX_REQUIRED - _INDEX_OPTIONAL
        if unknown:
            problems.append(f"index.json[{i}]: unknown keys {sorted(unknown)}")
            continue
        if not isinstance(entry["manifest"], str) or entry["expect"] not in {"valid", "invalid"}:
            problems.append(f"index.json[{i}]: manifest must be a string and expect 'valid' or 'invalid'")
            continue
        if entry["expect"] == "invalid" and not isinstance(entry.get("problem"), str):
            problems.append(f"index.json[{i}]: an invalid fixture must declare its expected problem substring")
            continue
        if entry["expect"] == "invalid" and not entry["manifest"].startswith("error_"):
            problems.append(f"index.json[{i}]: invalid fixtures use the error_ name prefix: {entry['manifest']}")
            continue
        if entry["expect"] == "valid" and entry["manifest"].startswith("error_"):
            problems.append(f"index.json[{i}]: valid fixtures must not use the error_ name prefix")
            continue
        entries.append(entry)
    return entries


def check_index_matches_disk(
    entries: list[dict[str, Any]],
    problems: list[str],
    fixtures_dir: Path = FIXTURES,
) -> None:
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


def check_fixture(entry: dict[str, Any], schema: dict[str, Any], fixtures_dir: Path = FIXTURES) -> list[str]:
    """Check one index entry's fixture against its declared expectation."""
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
    schema = load_json(ROOT / "manifest.schema.json")
    problems: list[str] = []
    try:
        index = load_json(FIXTURES / "index.json")
    except (OSError, json.JSONDecodeError) as error:
        print(f"FAIL index.json: cannot load: {error}", file=sys.stderr)  # noqa: T201 - standalone validator CLI
        return 1
    entries = check_index_entries(index, problems)
    check_index_matches_disk(entries, problems)
    for entry in entries:
        problems.extend(check_fixture(entry, schema))
    backend = "jsonschema" if jsonschema is not None else "built-in checker"
    if problems:
        print("\n".join(problems), file=sys.stderr)  # noqa: T201 - standalone validator CLI
        return 1
    print(f"citry-client-graph/1 fixtures: ok ({len(entries)} fixtures, {backend})")  # noqa: T201 - standalone validator CLI
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
