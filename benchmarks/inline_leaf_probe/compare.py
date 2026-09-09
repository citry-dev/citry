"""Compare the retained graph and HTML after the declared icon identity removal."""

from __future__ import annotations

import dataclasses
import json
import re
from collections import Counter
from typing import Any

from benchmarks.render_structure_probe.census import canonical

from citry._protocol.client_graph import validate_manifest


def render_names(snapshots: list[Any], selected_class_id: str) -> tuple[dict[str, str], set[str]]:
    """Assign stable comparison names to distinct instances in creation order."""
    counts: Counter[str] = Counter()
    names = {}
    selected = set()
    for snapshot in snapshots:
        for row in snapshot.logical_instances:
            if row.render_id in names:
                continue
            counts[row.class_id] += 1
            names[row.render_id] = f"render_{row.class_id}_{counts[row.class_id]}"
            if row.class_id == selected_class_id:
                selected.add(row.render_id)
    return names, selected


def html(output: str, names: dict[str, str], selected: set[str]) -> str:
    """Project explicit icon identities out of HTML and its browser ownership data."""
    revisions = set()

    def manifest(match: re.Match[str]) -> str:
        nonlocal output
        wire = json.loads(match[1])
        if validate_manifest(wire) is not None:
            raise AssertionError("Invalid raw browser manifest")
        if wire["mode"] != "production" or any(part["sourceLocations"] for part in wire["graphs"]):
            raise AssertionError("This comparison requires production manifests without source provenance")
        revision = wire["revision"]
        revisions.add(revision)
        for part in wire["graphs"]:
            graph_id = part["graphId"]
            removed_instances = {
                row["instanceId"] for row in part["componentInstances"] if row["renderId"] in selected
            }
            removed_classes = {row["classId"] for row in part["componentInstances"] if row["renderId"] in selected}
            part["componentInstances"] = [row for row in part["componentInstances"] if row["renderId"] not in selected]
            part["nestedComponents"] = [
                row for row in part["nestedComponents"] if row["targetRenderId"] not in selected
            ]
            part["componentExecutionOrderConstraints"] = [
                row for row in part["componentExecutionOrderConstraints"] if row["childRenderId"] not in selected
            ]
            remaining_classes = {row["classId"] for row in part["componentInstances"]}
            part["componentClasses"] = [
                row
                for row in part["componentClasses"]
                if row["classId"] not in removed_classes or row["classId"] in remaining_classes
            ]
            mappings = {}
            for table, key in (
                ("componentInstances", "instanceId"),
                ("nestedComponents", "invocationId"),
                ("fills", "fillId"),
                ("slotRegions", "regionId"),
                ("sourceLocations", "locationId"),
            ):
                mappings[key] = {row[key]: index + 1 for index, row in enumerate(part[table])}
            # Record namespaces are independent; a region numbered 1 is not instance 1.
            field_kinds = {
                "instanceId": "instanceId",
                "invocationId": "invocationId",
                "sourceInvocationId": "invocationId",
                "fillId": "fillId",
                "regionId": "regionId",
                "parentRegionId": "regionId",
                "locationId": "locationId",
                "fallbackLocationId": "locationId",
                "slotLocationId": "locationId",
                "sourceLocationId": "locationId",
            }
            for rows in part.values():
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    for field, kind in field_kinds.items():
                        if field in row and row[field] is not None:
                            row[field] = mappings[kind][row[field]]
            cap_pattern = re.compile(
                r"<!--citry:g1:" + re.escape(revision[:8]) + ":" + str(graph_id) + r":([ir]):(\d+):([se])-->"
            )

            def cap(
                cap_match: re.Match[str],
                removed_instances: Any = removed_instances,
                mappings: Any = mappings,
                graph_id: Any = graph_id,
            ) -> str:
                kind, number, side = cap_match.groups()
                old_id = int(number)
                if kind == "i" and old_id in removed_instances:
                    return ""
                mapped = mappings["instanceId" if kind == "i" else "regionId"][old_id]
                return f"<!--citry:g1:normalized:{graph_id}:{kind}:{mapped}:{side}-->"

            output = cap_pattern.sub(cap, output)
        wire["revision"] = "normalized"
        return (
            '<script type="application/json" data-citry-graph>'
            + json.dumps(wire, sort_keys=True, separators=(",", ":"))
            + "</script>"
        )

    pattern = re.compile(r'<script type="application/json" data-citry-graph>(.*?)</script>', re.DOTALL)
    # Calculate replacements first because manifest comparison also rewrites range comments.
    replacements = [(match[0], manifest(match)) for match in list(pattern.finditer(output))]
    for before, after in replacements:
        output = output.replace(before, after)
    for revision in revisions:
        output = output.replace('"graph": "' + revision + '"', '"graph": "normalized"')
    for render_id in selected:
        output = output.replace(f' data-cid-{render_id}=""', "")
        output = output.replace(f' data-citry-root="" data-cid="{render_id}"', "")
        if render_id in output:
            raise AssertionError("Selected icon ID has a use beyond its declared removable identity")
    if not names:
        return output
    pattern = re.compile("|".join(re.escape(name) for name in sorted(names, key=len, reverse=True)))
    return pattern.sub(lambda match: names[match[0]], output)


def graph(snapshot: Any, names: dict[str, str], selected_class_id: str) -> dict[str, Any]:
    """Keep remaining fields and event order while renaming graph-local references."""
    if any(row.client_bindings for row in snapshot.component_invocations):
        raise AssertionError("This graph comparison excludes component-tag client bindings")
    invocations = {row.id for row in snapshot.component_invocations if row.target_class_id == selected_class_id}
    sources = {row.source_location_id for row in snapshot.component_invocations if row.id in invocations}
    instances = {row.render_id for row in snapshot.logical_instances if row.class_id == selected_class_id}
    tables = {field.name: list(getattr(snapshot, field.name)) for field in dataclasses.fields(snapshot)}
    tables["source_locations"] = [row for row in tables["source_locations"] if row.id not in sources]
    tables["component_invocations"] = [row for row in tables["component_invocations"] if row.id not in invocations]
    tables["logical_instances"] = [row for row in tables["logical_instances"] if row.render_id not in instances]
    tables["init_ancestry"] = [row for row in tables["init_ancestry"] if row.child_render_id not in instances]
    tables["render_queue"] = [row for row in tables["render_queue"] if row.invocation_id not in invocations]
    local_names = {}
    orders = set()
    for table, rows in tables.items():
        for index, row in enumerate(rows):
            if hasattr(row, "id"):
                local_names[(table, row.id)] = f"{table}_{index}"
            for key in row._fields:
                value = getattr(row, key)
                if key.endswith("order") and value is not None:
                    orders.add(value)
    ranked_orders = {value: index for index, value in enumerate(sorted(orders))}
    result = {}
    for table, rows in tables.items():
        converted = []
        for row in rows:
            fields = {}
            for key in row._fields:
                value = getattr(row, key)
                if value is None:
                    fields[key] = None
                elif key.endswith("order"):
                    fields[key] = ranked_orders[value]
                elif key.endswith("render_ids"):
                    fields[key] = [names[item] for item in value]
                elif key.endswith("render_id"):
                    if value in instances:
                        raise AssertionError("Retained graph still references a removed icon")
                    fields[key] = names[value]
                elif key == "id":
                    fields[key] = local_names[(table, value)]
                elif key.endswith("_id") and not key.endswith("class_id"):
                    if "invocation" in key:
                        target = "component_invocations"
                    elif "location" in key:
                        target = "source_locations"
                    elif "region" in key:
                        target = "physical_regions"
                    elif "fill" in key:
                        target = "logical_fills"
                    else:
                        raise AssertionError(f"Unknown graph reference field: {key}")
                    fields[key] = local_names[(target, value)]
                else:
                    fields[key] = canonical(value)
            converted.append(fields)
        result[table] = converted
    return result
