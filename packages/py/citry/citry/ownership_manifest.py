"""Versioned, immutable client ownership graph serialization."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from citry.citry_render import CitryRender, PhysicalRegionPart, PhysicalRegionRender
from citry.ownership import (
    AlpineHandlerClientBindingPayload,
    CitryDomEventClientBindingPayload,
    CitryPollClientBindingPayload,
    OwnershipSnapshot,
    OwnershipState,
    PropsClientBindingPayload,
    QueueState,
    RegionState,
    SourcePolicy,
)

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.component import Component
    from citry.ext.events.extension import EventsExtension
    from citry.ownership import ComponentTagClientBindingRecord, OwnershipGraph, PhysicalRegionId


PROTOCOL = "citry-client-graph/1"
EXTRA_KEY = "citry:ownership-manifest"
COMMENT_PREFIX = "citry:g1"
_ALPINE_ATTRIBUTE_RE = re.compile(
    r"(?:^|[\s<])(?:x-[^\s=/>]+|@[^\s=/>]+|:[^\s=/>]+)(?=\s|=|/?>)",
    re.IGNORECASE,
)
_AMBIENT_CONTEXT_MAGIC_RE = re.compile(
    r"(?:^|[\s<])(?:x-[^\s=/>]+|@[^\s=/>]+|:[^\s=/>]+)\s*=\s*"
    r"""(?P<quote>["'])(?:(?!(?P=quote)).)*"""
    r"\$(?:provide|inject|unprovide)\b",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class GraphCapture:
    """One graph reached from the settled render tree and its serialized snapshot."""

    graph: OwnershipGraph
    snapshot: OwnershipSnapshot


@dataclass(frozen=True, slots=True)
class OwnershipManifestArtifact:
    """A validated wire manifest plus physical-cap lookup tables."""

    revision: str
    manifest: dict[str, Any]
    captures: tuple[GraphCapture, ...]
    graph_indexes: dict[int, int]
    instance_ids: dict[tuple[int, str], int]
    transparent_instance_ids: frozenset[tuple[int, str]]
    region_ids: frozenset[tuple[int, int]]
    client_active_instances: frozenset[tuple[int, str]]

    def assert_unchanged(self) -> None:
        """Fail closed if delayed work mutated a graph after serialization."""
        for capture in self.captures:
            if capture.graph.snapshot() != capture.snapshot:
                msg = "The client ownership graph changed after its manifest was prepared."
                raise RuntimeError(msg)

    def cap(self, graph: OwnershipGraph, kind: str, record_id: int, side: str) -> str:
        """Return one restricted-ASCII physical range comment."""
        graph_index = self.graph_indexes.get(id(graph))
        if graph_index is None:
            msg = "A physical ownership cap refers to a graph absent from the manifest."
            raise RuntimeError(msg)
        return f"<!--{COMMENT_PREFIX}:{self.revision}:{graph_index}:{kind}:{record_id}:{side}-->"

    def instance_cap(self, graph: OwnershipGraph, render_id: str, side: str) -> str:
        key = (id(graph), render_id)
        instance_id = self.instance_ids.get(key)
        if instance_id is None:
            msg = f"No component instance included in the graph has render id {render_id!r}."
            raise RuntimeError(msg)
        return self.cap(graph, "i", instance_id, side)

    def is_transparent_instance(self, graph: OwnershipGraph, render_id: str) -> bool:
        """Whether an instance included in the graph uses caps without an element root."""
        return (id(graph), render_id) in self.transparent_instance_ids

    def region_cap(self, graph: OwnershipGraph, region_id: PhysicalRegionId, side: str) -> str:
        key = (id(graph), int(region_id))
        if key not in self.region_ids:
            msg = f"No slot region included in the graph has id {int(region_id)}."
            raise RuntimeError(msg)
        return self.cap(graph, "r", int(region_id), side)

    def has_region(self, graph: OwnershipGraph, region_id: PhysicalRegionId) -> bool:
        """Whether one server-side slot wrapper participates in this revision."""
        return (id(graph), int(region_id)) in self.region_ids

    def is_client_active(self, graph: OwnershipGraph, render_id: str) -> bool:
        """Whether an instance needs Citry's client lifecycle and Alpine boundary."""
        return (id(graph), render_id) in self.client_active_instances

    def json(self) -> str:
        """Return deterministic compact JSON suitable for an inert script tag."""
        self.assert_unchanged()
        return json.dumps(self.manifest, separators=(",", ":"), sort_keys=True)


def _client_binding_payload(
    client_binding: ComponentTagClientBindingRecord,
    *,
    include_location: bool,
) -> dict[str, Any]:
    payload = client_binding.payload
    wire: dict[str, Any]
    if isinstance(payload, (PropsClientBindingPayload, AlpineHandlerClientBindingPayload)):
        wire = {"type": payload.type, "expression": payload.expression}
    elif isinstance(payload, CitryDomEventClientBindingPayload):
        wire = {
            "type": payload.type,
            "classId": payload.class_id,
            "event": payload.event,
            "handler": payload.handler,
            "args": payload.args,
            "prevent": payload.prevent,
            "stop": payload.stop,
            "self": payload.self_,
            "once": payload.once,
            "key": payload.key,
            "debounce": payload.debounce,
            "throttle": payload.throttle,
        }
    elif isinstance(payload, CitryPollClientBindingPayload):
        wire = {
            "type": payload.type,
            "classId": payload.class_id,
            "handler": payload.handler,
            "args": payload.args,
            "interval": payload.interval,
        }
    else:  # pragma: no cover - closed internal union
        msg = f"Unsupported component-tag client binding payload {type(payload).__name__}."
        raise TypeError(msg)
    return {
        "key": client_binding.key,
        "source": client_binding.source.value,
        # The location is developer-only provenance; production omits it (Option
        # B in the client_graph package review, and dev_prod_mode.md).
        "locationId": int(client_binding.source_location_id) if include_location else None,
        "payload": wire,
    }


def _require_local_render(serialized_renders: set[str], render_id: str | None, relation: str) -> None:
    if render_id is not None and render_id not in serialized_renders:
        msg = (
            f"The {relation} included in the graph refers to render {render_id!r} outside its graph's "
            "physical instance set; v1 cannot encode that cross-graph relation."
        )
        raise RuntimeError(msg)


def prepare_ownership_manifest(root: CitryRender) -> OwnershipManifestArtifact:
    """Validate the settled render tree and build its deterministic v1 manifest."""
    root_component = root.context.component
    root_citry = root_component.citry if root_component is not None else None
    graph_order: list[OwnershipGraph] = []
    graph_seen: set[int] = set()
    reachable_render_ids: dict[int, set[str]] = {}
    transparent_frame_ids: dict[int, set[str]] = {}
    reached_region_ids: dict[int, set[int]] = {}
    reached_region_parts: dict[int, dict[int, object]] = {}
    component_occurrences: set[str] = set()
    wrapper_occurrences: set[int] = set()
    client_active_seeds: set[tuple[int, str]] = set()

    # Imported lazily so ownership serialization keeps its existing import
    # boundary with the dependency extension.
    from citry.ext.dependencies.scripts import uses_component  # noqa: PLC0415

    pending: list[object] = [root]
    while pending:
        current = pending.pop()
        if isinstance(current, (PhysicalRegionPart, PhysicalRegionRender)):
            object_id = id(current)
            if object_id in wrapper_occurrences:
                msg = "The same physical slot occurrence was inserted more than once; render a fresh occurrence."
                raise RuntimeError(msg)
            wrapper_occurrences.add(object_id)
            graph_id = id(current.graph)
            if graph_id not in graph_seen:
                graph_seen.add(graph_id)
                graph_order.append(current.graph)
            reached_region_ids.setdefault(graph_id, set()).add(int(current.region_id))
            reached_region_parts.setdefault(graph_id, {})[int(current.region_id)] = current.part
            pending.append(current.part)
            continue
        if not isinstance(current, CitryRender):
            continue
        component = current.context.component
        frame = current.frame
        component_class = _resolve_frame_class(current, root_citry)
        if component_class is not None:
            if root_citry is not None and component_class.citry is not root_citry:
                msg = "A serialized render tree cannot mix components owned by different Citry instances."
                raise RuntimeError(msg)
            if frame.is_component_root and frame.render_id is not None:
                if frame.render_id in component_occurrences:
                    msg = (
                        "The same rendered component occurrence was inserted more than once; "
                        "render a fresh component occurrence for each physical position."
                    )
                    raise RuntimeError(msg)
                component_occurrences.add(frame.render_id)
        graph = current.context.ownership
        if graph is not None:
            graph_id = id(graph)
            if graph_id not in graph_seen:
                graph_seen.add(graph_id)
                graph_order.append(graph)
            if component_class is not None and frame.is_component_root and frame.render_id is not None:
                reachable_render_ids.setdefault(graph_id, set()).add(frame.render_id)
                events = cast("EventsExtension", component_class.citry.extensions.get_extension("events"))
                info = events.resolve(component_class)
                if (
                    (component is not None and component._component_tag_client_bindings)
                    or uses_component(component_class)
                    or info.events_cls is not None
                    or info.state_cls is not None
                    or _render_part_uses_ambient_context(current, owner_render_id=frame.render_id)
                ):
                    client_active_seeds.add((graph_id, frame.render_id))
            elif component_class is not None and frame.render_id is not None and component_class.transparent:
                transparent_frame_ids.setdefault(graph_id, set()).add(frame.render_id)
        pending.extend(reversed(current.parts))

    captures = tuple(GraphCapture(graph=graph, snapshot=graph.snapshot()) for graph in graph_order)
    # The build environment decides whether source provenance reaches the wire
    # (dev_prod_mode.md). Production leaves sourceLocations empty and nulls
    # every reference to them; development ships the records.
    mode = root_citry.mode if root_citry is not None else "production"
    include_provenance = mode == "development"

    def _location_ref(location_id: int | None) -> int | None:
        """A location reference: the id in development, null in production."""
        return int(location_id) if include_provenance and location_id is not None else None

    graph_wires: list[dict[str, Any]] = []
    graph_indexes = {id(graph): index for index, graph in enumerate(graph_order)}
    instance_ids: dict[tuple[int, str], int] = {}
    region_ids: set[tuple[int, int]] = set()
    client_active_instances: set[tuple[int, str]] = set(client_active_seeds)

    for graph_index, capture in enumerate(captures):
        snapshot = capture.snapshot
        graph_id = id(capture.graph)
        reachable = reachable_render_ids.get(graph_id, set())
        reached_region_numbers = reached_region_ids.get(graph_id, set())
        active_regions = [
            record
            for record in snapshot.physical_regions
            if record.state == RegionState.CAPTURED and int(record.id) in reached_region_numbers
        ]
        if {int(record.id) for record in active_regions} != reached_region_numbers:
            msg = "A physical region cap refers to a failed, retired, or unknown ownership region."
            raise RuntimeError(msg)
        physical_transparent_ids = transparent_frame_ids.get(graph_id, set())
        required_transparent_ids = {
            render_id
            for region in active_regions
            for render_id in (
                region.receiver_render_id,
                region.lexical_owner_render_id,
                region.transition_from_render_id,
                region.result_owner_render_id,
            )
            if render_id in physical_transparent_ids
        }
        active_instances = [
            record
            for record in snapshot.logical_instances
            if record.state == OwnershipState.ACTIVE
            and (
                (record.render_id in reachable and not record.transparent)
                or (record.render_id in required_transparent_ids and record.transparent)
            )
        ]
        for instance_id, record in enumerate(active_instances, start=1):
            instance_ids[(graph_id, record.render_id)] = instance_id
        serialized_renders = {record.render_id for record in active_instances}

        active_invocations = [
            record
            for record in snapshot.component_invocations
            if record.state == OwnershipState.ACTIVE
            and record.source_render_id in serialized_renders
            and record.target_render_id in serialized_renders
        ]
        invocation_ids = {record.id for record in active_invocations}
        for invocation in active_invocations:
            if invocation.client_bindings:
                client_active_instances.add((graph_id, invocation.source_render_id))
                if invocation.target_render_id is not None:
                    client_active_instances.add((graph_id, invocation.target_render_id))

        # An active boundary cuts Alpine inheritance at every nested
        # component boundary below it. Descendants with no callback still
        # need isolation, while unrelated graph branches remain marker-free.
        children_by_parent: dict[str, list[str]] = {}
        for instance in active_instances:
            if instance.logical_parent_render_id is not None:
                children_by_parent.setdefault(instance.logical_parent_render_id, []).append(instance.render_id)
        pending_active = [
            render_id for candidate_graph_id, render_id in client_active_instances if candidate_graph_id == graph_id
        ]
        while pending_active:
            parent_render_id = pending_active.pop()
            for child_render_id in children_by_parent.get(parent_render_id, []):
                key = (graph_id, child_render_id)
                if key in client_active_instances:
                    continue
                client_active_instances.add(key)
                pending_active.append(child_render_id)
        dangling = [
            record
            for record in snapshot.render_queue
            if record.invocation_id in invocation_ids and record.state in (QueueState.ENQUEUED, QueueState.RENDERED)
        ]
        if dangling:
            msg = "Cannot serialize a client ownership graph while component render-queue work is unsettled."
            raise RuntimeError(msg)

        direct_alpine_region_ids = {
            int(record.id)
            for record in active_regions
            if _render_part_uses_alpine(
                reached_region_parts[graph_id][int(record.id)],
                owner_render_id=record.lexical_owner_render_id,
            )
        }

        # ``str(result)`` inside a render hook serializes a same-graph subtree
        # before its enclosing render is flattened. The subtree is a valid
        # standalone fragment, but an inert outer slot wrapper can still name
        # the omitted caller. Drop only that non-projecting boundary wrapper;
        # a wrapper with its own Alpine expression still fails closed because
        # v1 cannot qualify its absent lexical source. Foreign graph fragments
        # remain strict as well.
        root_graph = root.context.ownership
        if capture.graph is root_graph:
            selected_region_ids = {record.id for record in active_regions}
            fill_source_invocations = {record.id: record.source_invocation_id for record in snapshot.logical_fills}

            active_regions = [
                record
                for record in active_regions
                if (
                    all(
                        render_id is None or render_id in serialized_renders
                        for render_id in (
                            record.receiver_render_id,
                            record.lexical_owner_render_id,
                            record.transition_from_render_id,
                            record.result_owner_render_id,
                        )
                    )
                    and (record.containing_region_id is None or record.containing_region_id in selected_region_ids)
                    and (
                        fill_source_invocations[record.logical_fill_id] is None
                        or fill_source_invocations[record.logical_fill_id] in invocation_ids
                    )
                )
                or int(record.id) in direct_alpine_region_ids
            ]
        active_region_ids = {record.id for record in active_regions}
        for invocation in active_invocations:
            if (
                invocation.physical_parent_region_id is not None
                and invocation.physical_parent_region_id not in active_region_ids
            ):
                msg = "A nested component included in the graph refers to a slot region outside that graph."
                raise RuntimeError(msg)
        active_fill_ids = {record.logical_fill_id for record in active_regions}
        active_fills = [
            record
            for record in snapshot.logical_fills
            if record.state == OwnershipState.ACTIVE and record.id in active_fill_ids
        ]

        # A template-authored fill is client-active even when neither endpoint
        # declares Component.js or Events. Alpine expressions in supplied
        # content belong to the caller and fallback expressions belong to the
        # receiver, so both endpoint lifecycles must exist before the browser
        # can project the recorded transition. Detached Python and typed
        # defaults deliberately do not gain an invented client source here.
        alpine_fill_ids = {
            record.logical_fill_id for record in active_regions if int(record.id) in direct_alpine_region_ids
        }
        template_fill_ids = {
            record.id
            for record in active_fills
            if record.source_policy == SourcePolicy.TEMPLATE and record.id in alpine_fill_ids
        }
        for fill in active_fills:
            if fill.id not in template_fill_ids:
                continue
            for render_id in (fill.lexical_owner_render_id, fill.receiver_render_id):
                if render_id is not None:
                    client_active_instances.add((graph_id, render_id))
        for region in active_regions:
            if region.logical_fill_id not in template_fill_ids:
                continue
            for render_id in (
                region.lexical_owner_render_id,
                region.receiver_render_id,
                region.transition_from_render_id,
                region.result_owner_render_id,
            ):
                if render_id is not None:
                    client_active_instances.add((graph_id, render_id))

        # Template fill endpoints can add new active roots after the ordinary
        # callback/Event seed pass above. Apply the same isolation cascade to
        # their descendants so a nested component never inherits caller fill
        # data through physical DOM ancestry.
        pending_active = [
            render_id for candidate_graph_id, render_id in client_active_instances if candidate_graph_id == graph_id
        ]
        while pending_active:
            parent_render_id = pending_active.pop()
            for child_render_id in children_by_parent.get(parent_render_id, []):
                key = (graph_id, child_render_id)
                if key in client_active_instances:
                    continue
                client_active_instances.add(key)
                pending_active.append(child_render_id)
        active_execution_constraints = [
            record
            for record in snapshot.init_ancestry
            if record.state == OwnershipState.ACTIVE
            and record.invocation_id in invocation_ids
            and record.parent_render_id in reachable
            and record.child_render_id in reachable
        ]

        for instance in active_instances:
            if capture.graph is not root_graph or instance.logical_parent_render_id in serialized_renders:
                _require_local_render(serialized_renders, instance.logical_parent_render_id, "instance parent")
        for invocation in active_invocations:
            _require_local_render(serialized_renders, invocation.source_render_id, "invocation source")
            _require_local_render(serialized_renders, invocation.target_render_id, "invocation target")
        for fill in active_fills:
            _require_local_render(serialized_renders, fill.lexical_owner_render_id, "fill owner")
            _require_local_render(serialized_renders, fill.receiver_render_id, "fill receiver")
            if fill.source_invocation_id is not None and fill.source_invocation_id not in invocation_ids:
                msg = "A template fill included in the graph refers to a nested component outside that graph."
                raise RuntimeError(msg)
        for region in active_regions:
            _require_local_render(serialized_renders, region.receiver_render_id, "region receiver")
            _require_local_render(serialized_renders, region.lexical_owner_render_id, "region owner")
            _require_local_render(serialized_renders, region.transition_from_render_id, "region transition")
            _require_local_render(serialized_renders, region.result_owner_render_id, "region result owner")
        for constraint in active_execution_constraints:
            _require_local_render(
                serialized_renders,
                constraint.parent_render_id,
                "component execution-order parent",
            )
            _require_local_render(
                serialized_renders,
                constraint.child_render_id,
                "component execution-order child",
            )

        referenced_locations = {record.source_location_id for record in active_invocations}
        referenced_locations.update(
            client_binding.source_location_id
            for record in active_invocations
            for client_binding in record.client_bindings
        )
        for fill in active_fills:
            if fill.source_location_id is not None:
                referenced_locations.add(fill.source_location_id)
            if fill.fallback_slot_site_location_id is not None:
                referenced_locations.add(fill.fallback_slot_site_location_id)
        for region in active_regions:
            if region.slot_site_location_id is not None:
                referenced_locations.add(region.slot_site_location_id)
            if region.source_location_id is not None:
                referenced_locations.add(region.source_location_id)
        locations = [record for record in snapshot.source_locations if record.id in referenced_locations]
        if {record.id for record in locations} != referenced_locations:
            msg = "The graph being serialized contains a dangling source-location reference."
            raise RuntimeError(msg)

        classes: dict[str, str] = {}
        for record in active_instances:
            classes.setdefault(record.class_id, record.class_name)

        location_wire: list[dict[str, Any]] = []
        if include_provenance:
            location_wire = [
                {
                    "locationId": int(record.id),
                    "kind": record.kind.value,
                    "ownerRenderId": record.owner_render_id,
                    "ownerClassId": record.owner_class_id,
                    "carrierInstanceId": instance_ids.get((graph_id, record.owner_render_id)),
                    "origin": record.origin,
                    "sourceOffset": {"start": record.byte_span[0], "end": record.byte_span[1]},
                    "sourcePos": {"line": record.line, "column": record.column},
                    "mappingKey": record.mapping_key,
                    "mappingIndex": record.mapping_index,
                }
                for record in locations
            ]
            if any(record["carrierInstanceId"] is None for record in location_wire):
                msg = "Every serialized source location must identify a component instance included in the graph."
                raise RuntimeError(msg)

        graph_wires.append(
            {
                "graphId": graph_index,
                "componentClasses": [{"classId": class_id, "className": name} for class_id, name in classes.items()],
                "componentInstances": [
                    {
                        "instanceId": instance_ids[(graph_id, record.render_id)],
                        "renderId": record.render_id,
                        "classId": record.class_id,
                        "invocationId": (
                            None if record.invocation_id not in invocation_ids else int(record.invocation_id)
                        ),
                        "parentRenderId": (
                            record.logical_parent_render_id
                            if record.logical_parent_render_id in serialized_renders
                            else None
                        ),
                        "transparent": record.transparent,
                    }
                    for record in active_instances
                ],
                "sourceLocations": location_wire,
                "nestedComponents": [
                    {
                        "invocationId": int(record.id),
                        "sourceRenderId": record.source_render_id,
                        "sourceClassId": record.source_class_id,
                        "locationId": _location_ref(record.source_location_id),
                        "tagName": record.authored_tag,
                        "targetClassId": record.target_class_id,
                        "targetRenderId": record.target_render_id or "",
                        "parentRegionId": (
                            None if record.physical_parent_region_id is None else int(record.physical_parent_region_id)
                        ),
                        "clientBindings": [
                            _client_binding_payload(client_binding, include_location=include_provenance)
                            for client_binding in record.client_bindings
                        ],
                    }
                    for record in active_invocations
                ],
                "componentExecutionOrderConstraints": [
                    {
                        "invocationId": int(record.invocation_id),
                        "parentRenderId": record.parent_render_id,
                        "childRenderId": record.child_render_id,
                    }
                    for record in active_execution_constraints
                ],
                "fills": [
                    {
                        "fillId": int(record.id),
                        "kind": record.kind.value,
                        "slotName": record.slot_name,
                        "policy": record.source_policy.value,
                        "ownerRenderId": record.lexical_owner_render_id,
                        "ownerClassId": record.lexical_owner_class_id,
                        "locationId": _location_ref(record.source_location_id),
                        "sourceInvocationId": (
                            None if record.source_invocation_id is None else int(record.source_invocation_id)
                        ),
                        "receiverRenderId": record.receiver_render_id,
                        "receiverClassId": record.receiver_class_id,
                        "fallbackLocationId": _location_ref(record.fallback_slot_site_location_id),
                    }
                    for record in active_fills
                ],
                "slotRegions": [
                    {
                        "regionId": int(record.id),
                        "fillId": int(record.logical_fill_id),
                        "receiverRenderId": record.receiver_render_id,
                        "slotLocationId": _location_ref(record.slot_site_location_id),
                        "ownerRenderId": record.lexical_owner_render_id,
                        "sourceLocationId": _location_ref(record.source_location_id),
                        "parentRegionId": (
                            None if record.containing_region_id is None else int(record.containing_region_id)
                        ),
                        "transitionFromRenderId": record.transition_from_render_id,
                        "resultOwnerRenderId": record.result_owner_render_id,
                    }
                    for record in active_regions
                ],
            }
        )
        region_ids.update((graph_id, int(record.id)) for record in active_regions)

    unsigned = {
        "protocol": PROTOCOL,
        "mode": mode,
        "graphs": graph_wires,
        "delimiters": {"format": COMMENT_PREFIX},
    }
    canonical = json.dumps(unsigned, separators=(",", ":"), sort_keys=True).encode("utf8")
    revision = hashlib.sha256(canonical).hexdigest()
    manifest = {**unsigned, "revision": revision}
    artifact = OwnershipManifestArtifact(
        revision=revision,
        manifest=manifest,
        captures=captures,
        graph_indexes=graph_indexes,
        instance_ids=instance_ids,
        transparent_instance_ids=frozenset(
            (id(capture.graph), record.render_id)
            for capture in captures
            for record in capture.snapshot.logical_instances
            if record.transparent and (id(capture.graph), record.render_id) in instance_ids
        ),
        region_ids=frozenset(region_ids),
        client_active_instances=frozenset(client_active_instances),
    )
    artifact.json()
    return artifact


def _render_part_uses_alpine(part: object, *, owner_render_id: str | None = None) -> bool:
    """Whether settled region output directly contains an Alpine attribute."""
    pending = [part]
    while pending:
        current = pending.pop()
        if isinstance(current, str):
            if _ALPINE_ATTRIBUTE_RE.search(current):
                return True
            continue
        if isinstance(current, (PhysicalRegionPart, PhysicalRegionRender)):
            pending.append(current.part)
        elif isinstance(current, CitryRender):
            render_id = current.frame.render_id
            if (
                owner_render_id is not None
                and current.is_component_root
                and render_id is not None
                and render_id != owner_render_id
            ):
                continue
            pending.extend(current.parts)
    return False


def _render_part_uses_ambient_context(part: object, *, owner_render_id: str | None = None) -> bool:
    """Whether one component's settled HTML references a client context magic."""
    pending = [part]
    while pending:
        current = pending.pop()
        if isinstance(current, str):
            if _AMBIENT_CONTEXT_MAGIC_RE.search(current):
                return True
            continue
        if isinstance(current, (PhysicalRegionPart, PhysicalRegionRender)):
            pending.append(current.part)
        elif isinstance(current, CitryRender):
            render_id = current.frame.render_id
            if (
                owner_render_id is not None
                and current.is_component_root
                and render_id is not None
                and render_id != owner_render_id
            ):
                continue
            pending.extend(current.parts)
    return False


def ownership_manifest_required(root: CitryRender) -> bool:
    """Whether this settled tree has any client-active ownership behavior."""
    from citry.ext.dependencies.scripts import uses_component  # noqa: PLC0415

    root_component = root.context.component
    root_citry = root_component.citry if root_component is not None else None
    pending: list[object] = [root]
    seen: set[int] = set()
    reached_regions_by_graph: dict[int, tuple[OwnershipGraph, set[int]]] = {}
    reached_region_parts: dict[int, dict[int, object]] = {}
    while pending:
        current = pending.pop()
        if isinstance(current, (PhysicalRegionPart, PhysicalRegionRender)):
            graph_id = id(current.graph)
            reached = reached_regions_by_graph.get(graph_id)
            if reached is None:
                reached = (current.graph, set())
                reached_regions_by_graph[graph_id] = reached
            reached[1].add(int(current.region_id))
            reached_region_parts.setdefault(graph_id, {})[int(current.region_id)] = current.part
            pending.append(current.part)
            continue
        if not isinstance(current, CitryRender):
            continue
        object_id = id(current)
        if object_id in seen:
            continue
        seen.add(object_id)
        component = current.context.component
        component_class = _resolve_frame_class(current, root_citry)
        if component_class is not None:
            if (
                (component is not None and component._component_tag_client_bindings)
                or uses_component(component_class)
                or _render_part_uses_ambient_context(current, owner_render_id=current.frame.render_id)
            ):
                return True
            events = cast("EventsExtension", component_class.citry.extensions.get_extension("events"))
            info = events.resolve(component_class)
            if info.events_cls is not None or info.state_cls is not None:
                return True
        pending.extend(current.parts)

    for graph, region_ids in reached_regions_by_graph.values():
        snapshot = graph.snapshot()
        regions = [
            region
            for region in snapshot.physical_regions
            if region.state == RegionState.CAPTURED and int(region.id) in region_ids
        ]
        fill_ids = {region.logical_fill_id for region in regions}
        alpine_fill_ids = {
            region.logical_fill_id
            for region in regions
            if _render_part_uses_alpine(
                reached_region_parts[id(graph)][int(region.id)],
                owner_render_id=region.lexical_owner_render_id,
            )
        }
        if any(
            fill.state == OwnershipState.ACTIVE
            and fill.id in fill_ids
            and fill.id in alpine_fill_ids
            and fill.source_policy == SourcePolicy.TEMPLATE
            for fill in snapshot.logical_fills
        ):
            return True
    return False


def _resolve_frame_class(root: CitryRender, citry: Citry | None) -> type[Component] | None:
    """Resolve identity-only frame metadata without requiring a live component."""
    component = root.context.component
    if component is not None:
        return type(component)
    class_id = root.frame.class_id
    if class_id is None or citry is None:
        return None
    try:
        return citry.get_component_by_class_id(class_id)
    except KeyError as err:
        msg = f"Rendered frame refers to unregistered component class_id {class_id!r}."
        raise RuntimeError(msg) from err


__all__ = [
    "COMMENT_PREFIX",
    "EXTRA_KEY",
    "PROTOCOL",
    "OwnershipManifestArtifact",
    "ownership_manifest_required",
    "prepare_ownership_manifest",
]
