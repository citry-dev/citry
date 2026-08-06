"""Logical relationship checks for a structurally valid client graph."""

from __future__ import annotations

from typing import Any

from .issues import ValidationIssue, pointer


def _cycle(nodes: dict[Any, Any]) -> bool:
    """Whether following one optional parent from each node reaches a cycle."""
    visiting: set[Any] = set()
    visited: set[Any] = set()
    for start in nodes:
        current = start
        path: list[Any] = []
        while current in nodes and current not in visited:
            if current in visiting:
                return True
            visiting.add(current)
            path.append(current)
            current = nodes[current]
        for item in path:
            visiting.discard(item)
            visited.add(item)
    return False


def _execution_cycle(edges: dict[str, list[str]]) -> bool:
    """Whether the parent-to-children component execution graph has a cycle."""
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[tuple[str, bool]] = [(node, False) for node in reversed(list(edges))]
    while stack:
        node, leaving = stack.pop()
        if leaving:
            visiting.discard(node)
            visited.add(node)
            continue
        if node in visiting:
            return True
        if node in visited:
            continue
        visiting.add(node)
        stack.append((node, True))
        for child in reversed(edges.get(node, [])):
            stack.append((child, False))
    return False


def _client_binding_key_issue(
    payload: dict[str, Any], binding_key: str, event: str | None, path: str
) -> ValidationIssue | None:
    """Check that a resolved component-tag key agrees with its payload."""
    payload_type = payload["type"]
    if payload_type == "props" and binding_key != "$c-props":
        return ValidationIssue(path, "semantic", "A props client binding must use the $c-props key.")
    if payload_type == "alpine-handler" and not (
        (binding_key.startswith("@") and not binding_key.startswith("@c-")) or binding_key.startswith("x-on:")
    ):
        return ValidationIssue(path, "semantic", "An Alpine-handler client binding has a non-Alpine key.")
    if payload_type == "citry-dom-event":
        if not binding_key.startswith("@c-") or binding_key[3:].split(".")[0] == "poll":
            return ValidationIssue(path, "semantic", "A Citry DOM-event client binding has a non-event key.")
        if event is not None and binding_key[3:].split(".")[0] != event:
            return ValidationIssue(path, "semantic", "A Citry DOM-event client binding disagrees with its key.")
    if payload_type == "citry-poll" and not binding_key.startswith("@c-poll."):
        return ValidationIssue(path, "semantic", "A Citry poll client binding must use an @c-poll key.")
    return None


def validate_relationships(manifest: dict[str, Any], path: str = "") -> ValidationIssue | None:
    """Return the first cross-record problem in a structurally valid manifest."""
    development = manifest["mode"] == "development"
    all_render_ids: set[str] = set()

    for graph_index, graph in enumerate(manifest["graphs"]):
        graph_path = pointer(pointer(path, "graphs"), graph_index)
        if graph["graphId"] != graph_index:
            return ValidationIssue(
                pointer(graph_path, "graphId"),
                "semantic",
                f"graphs[{graph_index}].graphId is not dense and ordered.",
            )

        id_fields = {
            "componentInstances": "instanceId",
            "sourceLocations": "locationId",
            "nestedComponents": "invocationId",
            "fills": "fillId",
            "slotRegions": "regionId",
        }
        ids: dict[str, set[int]] = {}
        for collection, id_field in id_fields.items():
            values = [int(record[id_field]) for record in graph[collection]]
            ids[collection] = set(values)
            if len(values) != len(ids[collection]):
                return ValidationIssue(
                    pointer(graph_path, collection),
                    "semantic",
                    f"graphs[{graph_index}].{collection} has duplicate ids.",
                )

        if not development:
            if graph["sourceLocations"]:
                return ValidationIssue(
                    pointer(graph_path, "sourceLocations"),
                    "semantic",
                    f"graphs[{graph_index}] production manifest has sourceLocations.",
                )
            for invocation_index, invocation in enumerate(graph["nestedComponents"]):
                invocation_path = pointer(pointer(graph_path, "nestedComponents"), invocation_index)
                if invocation["locationId"] is not None:
                    return ValidationIssue(
                        pointer(invocation_path, "locationId"),
                        "semantic",
                        f"graphs[{graph_index}] production invocation has a location reference.",
                    )
                for binding_index, binding in enumerate(invocation["clientBindings"]):
                    if binding["locationId"] is not None:
                        binding_path = pointer(pointer(invocation_path, "clientBindings"), binding_index)
                        return ValidationIssue(
                            pointer(binding_path, "locationId"),
                            "semantic",
                            f"graphs[{graph_index}] production client binding has a location reference.",
                        )
            for fill_index, fill in enumerate(graph["fills"]):
                for field in ("locationId", "fallbackLocationId"):
                    if fill[field] is not None:
                        fill_path = pointer(pointer(graph_path, "fills"), fill_index)
                        return ValidationIssue(
                            pointer(fill_path, field),
                            "semantic",
                            f"graphs[{graph_index}] production fill has a location reference.",
                        )
            for region_index, region in enumerate(graph["slotRegions"]):
                for field in ("slotLocationId", "sourceLocationId"):
                    if region[field] is not None:
                        region_path = pointer(pointer(graph_path, "slotRegions"), region_index)
                        return ValidationIssue(
                            pointer(region_path, field),
                            "semantic",
                            f"graphs[{graph_index}] production slot region has a location reference.",
                        )

        class_ids: set[str] = set()
        for class_index, component_class in enumerate(graph["componentClasses"]):
            class_id = component_class["classId"]
            if class_id in class_ids:
                class_path = pointer(pointer(graph_path, "componentClasses"), class_index)
                return ValidationIssue(
                    pointer(class_path, "classId"),
                    "semantic",
                    f"graphs[{graph_index}] has duplicate class ids.",
                )
            class_ids.add(class_id)

        render_ids: set[str] = set()
        classes_by_render: dict[str, str] = {}
        instances_by_id: dict[int, str] = {}
        instances_by_invocation: dict[int, list[tuple[str, str | None, int | None]]] = {}
        instance_records: list[tuple[str, str | None, int | None]] = []
        instance_parents: dict[str, str | None] = {}
        for instance_index, instance in enumerate(graph["componentInstances"]):
            instance_path = pointer(pointer(graph_path, "componentInstances"), instance_index)
            render_id = instance["renderId"]
            class_id = instance["classId"]
            if class_id not in class_ids:
                return ValidationIssue(
                    pointer(instance_path, "classId"),
                    "semantic",
                    f"graphs[{graph_index}] component instance classId is unknown.",
                )
            if render_id in render_ids:
                return ValidationIssue(
                    pointer(instance_path, "renderId"),
                    "semantic",
                    f"graphs[{graph_index}] has duplicate render ids.",
                )
            if render_id in all_render_ids:
                return ValidationIssue(
                    pointer(instance_path, "renderId"),
                    "semantic",
                    f"render id {render_id!r} appears in more than one graph.",
                )
            render_ids.add(render_id)
            all_render_ids.add(render_id)
            classes_by_render[render_id] = class_id
            instances_by_id[int(instance["instanceId"])] = render_id
            parent = instance["parentRenderId"]
            invocation_id = None if instance["invocationId"] is None else int(instance["invocationId"])
            instance_parents[render_id] = parent
            record = (render_id, parent, invocation_id)
            instance_records.append(record)
            if invocation_id is not None:
                instances_by_invocation.setdefault(invocation_id, []).append(record)
        for instance_index, instance in enumerate(graph["componentInstances"]):
            parent = instance["parentRenderId"]
            if parent is not None and parent not in render_ids:
                instance_path = pointer(pointer(graph_path, "componentInstances"), instance_index)
                return ValidationIssue(
                    pointer(instance_path, "parentRenderId"),
                    "semantic",
                    f"graphs[{graph_index}] component instance parentRenderId is unknown.",
                )
        location_owners: dict[int, tuple[str, str]] = {}
        location_kinds: dict[int, str] = {}
        if development:
            for location_index, location in enumerate(graph["sourceLocations"]):
                location_path = pointer(pointer(graph_path, "sourceLocations"), location_index)
                carrier_id = int(location["carrierInstanceId"])
                if carrier_id not in ids["componentInstances"]:
                    return ValidationIssue(
                        pointer(location_path, "carrierInstanceId"),
                        "semantic",
                        f"graphs[{graph_index}] location has an unknown carrier.",
                    )
                if location["sourceOffset"]["start"] > location["sourceOffset"]["end"]:
                    return ValidationIssue(
                        pointer(location_path, "sourceOffset"),
                        "semantic",
                        f"graphs[{graph_index}] location has a reversed byte range.",
                    )
                owner = location["ownerRenderId"]
                class_id = location["ownerClassId"]
                if owner not in render_ids or classes_by_render.get(owner) != class_id:
                    return ValidationIssue(
                        pointer(location_path, "ownerRenderId"),
                        "semantic",
                        f"graphs[{graph_index}] location owner is unknown or mismatched.",
                    )
                if instances_by_id.get(carrier_id) != owner:
                    return ValidationIssue(
                        pointer(location_path, "carrierInstanceId"),
                        "semantic",
                        f"graphs[{graph_index}] location carrier is mismatched.",
                    )
                location_id = int(location["locationId"])
                location_owners[location_id] = (owner, class_id)
                location_kinds[location_id] = location["kind"]

        invocation_edges: dict[int, tuple[str, str]] = {}
        for invocation_index, invocation in enumerate(graph["nestedComponents"]):
            invocation_path = pointer(pointer(graph_path, "nestedComponents"), invocation_index)
            source = invocation["sourceRenderId"]
            source_class = invocation["sourceClassId"]
            target = invocation["targetRenderId"]
            target_class = invocation["targetClassId"]
            if source not in render_ids or classes_by_render.get(source) != source_class:
                return ValidationIssue(
                    pointer(invocation_path, "sourceRenderId"),
                    "semantic",
                    f"graphs[{graph_index}] invocation source is unknown or mismatched.",
                )
            if target not in render_ids or classes_by_render.get(target) != target_class:
                return ValidationIssue(
                    pointer(invocation_path, "targetRenderId"),
                    "semantic",
                    f"graphs[{graph_index}] invocation target is unknown or mismatched.",
                )
            invocation_location_id = None if invocation["locationId"] is None else int(invocation["locationId"])
            if development:
                if invocation_location_id not in ids["sourceLocations"]:
                    return ValidationIssue(
                        pointer(invocation_path, "locationId"),
                        "semantic",
                        f"graphs[{graph_index}] invocation has an unknown location.",
                    )
                if location_owners.get(invocation_location_id) != (source, source_class):
                    return ValidationIssue(
                        pointer(invocation_path, "locationId"),
                        "semantic",
                        f"graphs[{graph_index}] invocation location owner is mismatched.",
                    )
                if location_kinds.get(invocation_location_id) != "component-call":
                    return ValidationIssue(
                        pointer(invocation_path, "locationId"),
                        "semantic",
                        f"graphs[{graph_index}] invocation location kind is mismatched.",
                    )
            parent_region_id = None if invocation["parentRegionId"] is None else int(invocation["parentRegionId"])
            if parent_region_id is not None and parent_region_id not in ids["slotRegions"]:
                return ValidationIssue(
                    pointer(invocation_path, "parentRegionId"),
                    "semantic",
                    f"graphs[{graph_index}] nested component parentRegionId references an unknown slot region.",
                )
            invocation_id = int(invocation["invocationId"])
            invocation_edges[invocation_id] = (source, target)
            for binding_index, binding in enumerate(invocation["clientBindings"]):
                binding_path = pointer(pointer(invocation_path, "clientBindings"), binding_index)
                binding_location = None if binding["locationId"] is None else int(binding["locationId"])
                if development:
                    if binding_location not in ids["sourceLocations"]:
                        return ValidationIssue(
                            pointer(binding_path, "locationId"),
                            "semantic",
                            f"graphs[{graph_index}] client binding has an unknown location.",
                        )
                    if location_owners.get(binding_location) != (source, source_class):
                        return ValidationIssue(
                            pointer(binding_path, "locationId"),
                            "semantic",
                            f"graphs[{graph_index}] client-binding location owner is mismatched.",
                        )
                    if location_kinds.get(binding_location) != "component-tag-client-binding":
                        return ValidationIssue(
                            pointer(binding_path, "locationId"),
                            "semantic",
                            f"graphs[{graph_index}] client-binding location kind is mismatched.",
                        )
                payload = binding["payload"]
                if payload["type"] in {"citry-dom-event", "citry-poll"} and payload["classId"] != source_class:
                    return ValidationIssue(
                        pointer(pointer(binding_path, "payload"), "classId"),
                        "semantic",
                        f"graphs[{graph_index}] Citry client-binding class is not its source parent.",
                    )
                issue = _client_binding_key_issue(
                    payload,
                    binding["key"],
                    payload.get("event"),
                    pointer(binding_path, "key"),
                )
                if issue is not None:
                    return issue

        for instance_index, instance in enumerate(graph["componentInstances"]):
            invocation_id = None if instance["invocationId"] is None else int(instance["invocationId"])
            if invocation_id is not None and invocation_id not in ids["nestedComponents"]:
                instance_path = pointer(pointer(graph_path, "componentInstances"), instance_index)
                return ValidationIssue(
                    pointer(instance_path, "invocationId"),
                    "semantic",
                    f"graphs[{graph_index}] instance has an unknown invocation.",
                )
        for instance_index, (render, parent, invocation_id) in enumerate(instance_records):
            instance_path = pointer(pointer(graph_path, "componentInstances"), instance_index)
            if invocation_id is None:
                if parent is not None:
                    return ValidationIssue(
                        pointer(instance_path, "parentRenderId"),
                        "semantic",
                        f"graphs[{graph_index}] uninvoked instance has a parent.",
                    )
                continue
            if invocation_edges.get(invocation_id) != (parent, render):
                return ValidationIssue(
                    pointer(instance_path, "invocationId"),
                    "semantic",
                    f"graphs[{graph_index}] instance endpoints do not match their invocation.",
                )
        for invocation_index, invocation in enumerate(graph["nestedComponents"]):
            invocation_id = int(invocation["invocationId"])
            if len(instances_by_invocation.get(invocation_id, [])) != 1:
                invocation_path = pointer(pointer(graph_path, "nestedComponents"), invocation_index)
                return ValidationIssue(
                    pointer(invocation_path, "invocationId"),
                    "semantic",
                    f"graphs[{graph_index}] invocation does not bind exactly one target instance.",
                )

        fill_records: dict[int, tuple[str | None, str | None, int | None]] = {}
        for fill_index, fill in enumerate(graph["fills"]):
            fill_path = pointer(pointer(graph_path, "fills"), fill_index)
            owner = fill["ownerRenderId"]
            owner_class = fill["ownerClassId"]
            receiver = fill["receiverRenderId"]
            receiver_class = fill["receiverClassId"]
            kind = fill["kind"]
            source_invocation = None if fill["sourceInvocationId"] is None else int(fill["sourceInvocationId"])
            if (owner is None) != (owner_class is None) or (
                owner is not None and classes_by_render.get(owner) != owner_class
            ):
                return ValidationIssue(
                    pointer(fill_path, "ownerRenderId"),
                    "semantic",
                    f"graphs[{graph_index}] fill owner and class are mismatched.",
                )
            if (receiver is None) != (receiver_class is None) or (
                receiver is not None and classes_by_render.get(receiver) != receiver_class
            ):
                return ValidationIssue(
                    pointer(fill_path, "receiverRenderId"),
                    "semantic",
                    f"graphs[{graph_index}] fill receiver and class are mismatched.",
                )
            if source_invocation is not None and source_invocation not in ids["nestedComponents"]:
                return ValidationIssue(
                    pointer(fill_path, "sourceInvocationId"),
                    "semantic",
                    f"graphs[{graph_index}] fill has an unknown sourceInvocation.",
                )
            fill_location_id = None if fill["locationId"] is None else int(fill["locationId"])
            fallback_id = None if fill["fallbackLocationId"] is None else int(fill["fallbackLocationId"])
            source_kind = None if fill_location_id is None else location_kinds.get(fill_location_id)
            fallback_kind = None if fallback_id is None else location_kinds.get(fallback_id)
            policy = fill["policy"]
            if policy == "template":
                if owner is None or receiver is None or kind not in {"implicit", "named", "fallback"}:
                    return ValidationIssue(
                        pointer(fill_path, "policy"),
                        "semantic",
                        f"graphs[{graph_index}] template fill ownership is inconsistent.",
                    )
            elif policy == "python-detached":
                if (
                    kind != "python"
                    or owner is not None
                    or receiver is None
                    or source_invocation is not None
                    or fallback_id is not None
                ):
                    return ValidationIssue(
                        pointer(fill_path, "policy"),
                        "semantic",
                        f"graphs[{graph_index}] detached Python fill ownership is inconsistent.",
                    )
            elif (
                kind != "typed-default"
                or owner is not None
                or receiver is None
                or source_invocation is not None
                or fallback_id is not None
            ):
                return ValidationIssue(
                    pointer(fill_path, "policy"),
                    "semantic",
                    f"graphs[{graph_index}] detached typed-default fill ownership is inconsistent.",
                )
            if development:
                for field, location in (("locationId", fill_location_id), ("fallbackLocationId", fallback_id)):
                    if location is not None and location not in ids["sourceLocations"]:
                        return ValidationIssue(
                            pointer(fill_path, field),
                            "semantic",
                            f"graphs[{graph_index}] fill has an unknown {field}.",
                        )
                source_owner = None if fill_location_id is None else location_owners.get(fill_location_id)
                fallback_owner = None if fallback_id is None else location_owners.get(fallback_id)
                if (owner is None) != (source_owner is None):
                    return ValidationIssue(
                        pointer(fill_path, "locationId"),
                        "semantic",
                        f"graphs[{graph_index}] fill owner and source location are inconsistent.",
                    )
                if source_owner is not None and source_owner != (owner, owner_class):
                    return ValidationIssue(
                        pointer(fill_path, "locationId"),
                        "semantic",
                        f"graphs[{graph_index}] fill source location owner is mismatched.",
                    )
                if fallback_owner is not None and fallback_owner != (receiver, receiver_class):
                    return ValidationIssue(
                        pointer(fill_path, "fallbackLocationId"),
                        "semantic",
                        f"graphs[{graph_index}] fill fallback location receiver is mismatched.",
                    )
            if policy == "template":
                if development:
                    expected_kind = {
                        "implicit": "implicit-fill",
                        "named": "named-fill",
                        "fallback": "fallback-fill",
                    }[kind]
                    if source_kind != expected_kind:
                        return ValidationIssue(
                            pointer(fill_path, "locationId"),
                            "semantic",
                            f"graphs[{graph_index}] template fill source location kind is mismatched.",
                        )
                    if kind == "fallback" and (fallback_id is None or fallback_kind != "slot-outlet"):
                        return ValidationIssue(
                            pointer(fill_path, "fallbackLocationId"),
                            "semantic",
                            f"graphs[{graph_index}] fallback location kind is mismatched.",
                        )
                    if kind != "fallback" and fallback_id is not None:
                        return ValidationIssue(
                            pointer(fill_path, "fallbackLocationId"),
                            "semantic",
                            f"graphs[{graph_index}] supplied fill carrier is inconsistent.",
                        )
                if kind == "fallback":
                    if source_invocation is not None:
                        return ValidationIssue(
                            pointer(fill_path, "sourceInvocationId"),
                            "semantic",
                            f"graphs[{graph_index}] fallback fill carrier is inconsistent.",
                        )
                elif source_invocation is None:
                    return ValidationIssue(
                        pointer(fill_path, "sourceInvocationId"),
                        "semantic",
                        f"graphs[{graph_index}] supplied fill carrier is inconsistent.",
                    )
                elif invocation_edges.get(source_invocation, (None, None))[0] != owner:
                    return ValidationIssue(
                        pointer(fill_path, "sourceInvocationId"),
                        "semantic",
                        f"graphs[{graph_index}] supplied fill source invocation owner is mismatched.",
                    )
            fill_records[int(fill["fillId"])] = (owner, receiver, fill_location_id)

        slot_region_records: dict[int, tuple[str | None, str | None, int | None, str | None]] = {}
        for region_index, region in enumerate(graph["slotRegions"]):
            region_path = pointer(pointer(graph_path, "slotRegions"), region_index)
            fill_id = int(region["fillId"])
            if fill_id not in ids["fills"]:
                return ValidationIssue(
                    pointer(region_path, "fillId"),
                    "semantic",
                    f"graphs[{graph_index}] slot region has an unknown fill.",
                )
            parent_id = None if region["parentRegionId"] is None else int(region["parentRegionId"])
            if parent_id is not None and parent_id not in ids["slotRegions"]:
                return ValidationIssue(
                    pointer(region_path, "parentRegionId"),
                    "semantic",
                    f"graphs[{graph_index}] slot region has an unknown parent.",
                )
            renders = {
                "receiverRenderId": region["receiverRenderId"],
                "ownerRenderId": region["ownerRenderId"],
                "transitionFromRenderId": region["transitionFromRenderId"],
                "resultOwnerRenderId": region["resultOwnerRenderId"],
            }
            for field, render_id in renders.items():
                if render_id is not None and render_id not in render_ids:
                    return ValidationIssue(
                        pointer(region_path, field),
                        "semantic",
                        f"graphs[{graph_index}] slot region.{field} is unknown.",
                    )
            slot_location = None if region["slotLocationId"] is None else int(region["slotLocationId"])
            region_source_location = None if region["sourceLocationId"] is None else int(region["sourceLocationId"])
            if development:
                for field, candidate_location_id in (
                    ("slotLocationId", slot_location),
                    ("sourceLocationId", region_source_location),
                ):
                    if candidate_location_id is not None and candidate_location_id not in ids["sourceLocations"]:
                        return ValidationIssue(
                            pointer(region_path, field),
                            "semantic",
                            f"graphs[{graph_index}] slot region has an unknown {field}.",
                        )
                slot_owner = None if slot_location is None else location_owners.get(slot_location)
                if slot_owner is not None and slot_owner[0] != renders["receiverRenderId"]:
                    return ValidationIssue(
                        pointer(region_path, "slotLocationId"),
                        "semantic",
                        f"graphs[{graph_index}] slot region slot location receiver is mismatched.",
                    )
                if slot_location is not None and location_kinds.get(slot_location) != "slot-outlet":
                    return ValidationIssue(
                        pointer(region_path, "slotLocationId"),
                        "semantic",
                        f"graphs[{graph_index}] slot region slot location kind is mismatched.",
                    )
            actual = (renders["ownerRenderId"], renders["receiverRenderId"], region_source_location)
            if fill_records.get(fill_id) != actual:
                return ValidationIssue(
                    pointer(region_path, "fillId"),
                    "semantic",
                    f"graphs[{graph_index}] slot region ownership does not match its fill.",
                )
            slot_region_records[int(region["regionId"])] = (
                renders["ownerRenderId"],
                renders["receiverRenderId"],
                parent_id,
                renders["transitionFromRenderId"],
            )

        if _cycle({region_id: record[2] for region_id, record in slot_region_records.items()}):
            return ValidationIssue(
                pointer(graph_path, "slotRegions"),
                "semantic",
                f"graphs[{graph_index}] slot region ancestry contains a cycle.",
            )
        for region_index, region in enumerate(graph["slotRegions"]):
            parent_id = None if region["parentRegionId"] is None else int(region["parentRegionId"])
            expected_transition = (
                region["receiverRenderId"] if parent_id is None else slot_region_records[parent_id][0]
            )
            if region["transitionFromRenderId"] != expected_transition:
                region_path = pointer(pointer(graph_path, "slotRegions"), region_index)
                return ValidationIssue(
                    pointer(region_path, "transitionFromRenderId"),
                    "semantic",
                    f"graphs[{graph_index}] slot region scope transition does not match its ancestry.",
                )

        execution_edges: dict[str, list[str]] = {}
        for constraint_index, constraint in enumerate(graph["componentExecutionOrderConstraints"]):
            constraint_path = pointer(pointer(graph_path, "componentExecutionOrderConstraints"), constraint_index)
            invocation_id = int(constraint["invocationId"])
            edge = invocation_edges.get(invocation_id)
            expected = (constraint["parentRenderId"], constraint["childRenderId"])
            if edge != expected:
                return ValidationIssue(
                    pointer(constraint_path, "invocationId"),
                    "semantic",
                    f"graphs[{graph_index}] component execution order constraint does not match its invocation.",
                )
            execution_edges.setdefault(constraint["parentRenderId"], []).append(constraint["childRenderId"])
        if _execution_cycle(execution_edges):
            return ValidationIssue(
                pointer(graph_path, "componentExecutionOrderConstraints"),
                "semantic",
                f"graphs[{graph_index}] component execution order contains a cycle.",
            )
        if _cycle(instance_parents):
            return ValidationIssue(
                pointer(graph_path, "componentInstances"),
                "semantic",
                f"graphs[{graph_index}] logical instance ancestry contains a cycle.",
            )
    return None


__all__ = ["validate_relationships"]
