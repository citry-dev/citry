"""Versioned, immutable client ownership graph serialization."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from citry._protocol.client_graph import (
    COMMENT_PREFIX,
    PROTOCOL,
    assemble_graph,
    assemble_manifest,
    build_client_binding,
    build_component_class,
    build_component_instance,
    build_dom_event_payload,
    build_execution_constraint,
    build_expression_payload,
    build_fill,
    build_nested_component,
    build_poll_payload,
    build_slot_region,
    build_source_location,
    format_ownership_comment,
    serialize_manifest,
)
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
    from citry.ownership import (
        ComponentInvocationRecord,
        ComponentTagClientBindingRecord,
        OwnershipGraph,
        PhysicalRegionId,
    )


EXTRA_KEY = "citry:ownership-manifest"
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
    audit_manifest: bool = True

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
        return format_ownership_comment(self.revision, graph_index, kind, record_id, side)

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
        return serialize_manifest(self.manifest, audit=self.audit_manifest)


def has_range_directive(invocation: ComponentInvocationRecord) -> bool:
    """Whether an invocation needs browser-visible ComponentRange metadata."""
    return invocation.morph_key is not None or invocation.morph_mode is not None


def _client_binding_payload(
    client_binding: ComponentTagClientBindingRecord,
    *,
    include_location: bool,
) -> dict[str, Any]:
    payload = client_binding.payload
    if isinstance(payload, (PropsClientBindingPayload, AlpineHandlerClientBindingPayload)):
        wire = build_expression_payload(payload.type, payload.expression, audit=False)
    elif isinstance(payload, CitryDomEventClientBindingPayload):
        wire = build_dom_event_payload(
            class_id=payload.class_id,
            event=payload.event,
            handler=payload.handler,
            args=payload.args,
            prevent=payload.prevent,
            stop=payload.stop,
            self_=payload.self_,
            once=payload.once,
            key=payload.key,
            debounce=payload.debounce,
            throttle=payload.throttle,
            audit=False,
        )
    elif isinstance(payload, CitryPollClientBindingPayload):
        wire = build_poll_payload(
            class_id=payload.class_id,
            handler=payload.handler,
            args=payload.args,
            interval=payload.interval,
            audit=False,
        )
    else:  # pragma: no cover - closed internal union
        msg = f"Unsupported component-tag client binding payload {type(payload).__name__}."
        raise TypeError(msg)
    return build_client_binding(
        key=client_binding.key,
        source=client_binding.source.value,
        # The location is developer-only provenance; production omits it (Option
        # B in the client_graph package review, and dev_prod_mode.md).
        location_id=int(client_binding.source_location_id) if include_location else None,
        payload=wire,
        audit=False,
    )


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
        reached_render_ids = reachable | physical_transparent_ids
        logical_by_render = {
            record.render_id: record
            for record in snapshot.logical_instances
            if record.state == OwnershipState.ACTIVE and record.render_id in reached_render_ids
        }
        # A range-directed transparent/rootless component is itself the virtual
        # node whose caps carry policy. Include it and every reached transparent
        # logical ancestor needed to encode the invocation path to it.
        directed_path: list[str] = []
        for invocation in snapshot.component_invocations:
            if (
                invocation.state == OwnershipState.ACTIVE
                and has_range_directive(invocation)
                and invocation.source_render_id in reached_render_ids
                and invocation.target_render_id in reached_render_ids
            ):
                directed_path.extend((invocation.source_render_id, invocation.target_render_id))
        while directed_path:
            render_id = directed_path.pop()
            if render_id not in physical_transparent_ids or render_id in required_transparent_ids:
                continue
            required_transparent_ids.add(render_id)
            instance = logical_by_render.get(render_id)
            if instance is not None and instance.logical_parent_render_id is not None:
                directed_path.append(instance.logical_parent_render_id)
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
            for fill_render_id in (fill.lexical_owner_render_id, fill.receiver_render_id):
                if fill_render_id is not None:
                    client_active_instances.add((graph_id, fill_render_id))
        for region in active_regions:
            if region.logical_fill_id not in template_fill_ids:
                continue
            for region_render_id in (
                region.lexical_owner_render_id,
                region.receiver_render_id,
                region.transition_from_render_id,
                region.result_owner_render_id,
            ):
                if region_render_id is not None:
                    client_active_instances.add((graph_id, region_render_id))

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
            for location_record in locations:
                carrier_instance_id = instance_ids.get((graph_id, location_record.owner_render_id))
                if carrier_instance_id is None:
                    msg = "Every serialized source location must identify a component instance included in the graph."
                    raise RuntimeError(msg)
                location_wire.append(
                    build_source_location(
                        location_id=int(location_record.id),
                        kind=location_record.kind.value,
                        owner_render_id=location_record.owner_render_id,
                        owner_class_id=location_record.owner_class_id,
                        carrier_instance_id=carrier_instance_id,
                        origin=location_record.origin,
                        source_start=location_record.byte_span[0],
                        source_end=location_record.byte_span[1],
                        source_line=location_record.line,
                        source_column=location_record.column,
                        mapping_key=location_record.mapping_key,
                        mapping_index=location_record.mapping_index,
                        audit=False,
                    )
                )

        component_class_wire = [
            build_component_class(class_id, class_name, audit=False) for class_id, class_name in classes.items()
        ]
        component_instance_wire = [
            build_component_instance(
                instance_id=instance_ids[(graph_id, record.render_id)],
                render_id=record.render_id,
                class_id=record.class_id,
                invocation_id=None if record.invocation_id not in invocation_ids else int(record.invocation_id),
                parent_render_id=(
                    record.logical_parent_render_id if record.logical_parent_render_id in serialized_renders else None
                ),
                transparent=record.transparent,
                audit=False,
            )
            for record in active_instances
        ]
        nested_component_wire = [
            build_nested_component(
                invocation_id=int(record.id),
                source_render_id=record.source_render_id,
                source_class_id=record.source_class_id,
                location_id=_location_ref(record.source_location_id),
                tag_name=record.authored_tag,
                target_class_id=record.target_class_id,
                morph_key=record.morph_key,
                morph_mode=record.morph_mode,
                target_render_id=record.target_render_id or "",
                parent_region_id=(
                    None if record.physical_parent_region_id is None else int(record.physical_parent_region_id)
                ),
                client_bindings=[
                    _client_binding_payload(client_binding, include_location=include_provenance)
                    for client_binding in record.client_bindings
                ],
                audit=False,
            )
            for record in active_invocations
        ]
        execution_constraint_wire = [
            build_execution_constraint(
                invocation_id=int(record.invocation_id),
                parent_render_id=record.parent_render_id,
                child_render_id=record.child_render_id,
                audit=False,
            )
            for record in active_execution_constraints
        ]
        fill_wire = [
            build_fill(
                fill_id=int(record.id),
                kind=record.kind.value,
                slot_name=record.slot_name,
                policy=record.source_policy.value,
                owner_render_id=record.lexical_owner_render_id,
                owner_class_id=record.lexical_owner_class_id,
                location_id=_location_ref(record.source_location_id),
                source_invocation_id=(
                    None if record.source_invocation_id is None else int(record.source_invocation_id)
                ),
                receiver_render_id=record.receiver_render_id,
                receiver_class_id=record.receiver_class_id,
                fallback_location_id=_location_ref(record.fallback_slot_site_location_id),
                audit=False,
            )
            for record in active_fills
        ]
        slot_region_wire = [
            build_slot_region(
                region_id=int(record.id),
                fill_id=int(record.logical_fill_id),
                receiver_render_id=record.receiver_render_id,
                slot_location_id=_location_ref(record.slot_site_location_id),
                owner_render_id=record.lexical_owner_render_id,
                source_location_id=_location_ref(record.source_location_id),
                parent_region_id=(None if record.containing_region_id is None else int(record.containing_region_id)),
                transition_from_render_id=record.transition_from_render_id,
                result_owner_render_id=record.result_owner_render_id,
                audit=False,
            )
            for record in active_regions
        ]
        graph_wires.append(
            assemble_graph(
                graph_id=graph_index,
                component_classes=component_class_wire,
                component_instances=component_instance_wire,
                source_locations=location_wire,
                nested_components=nested_component_wire,
                component_execution_order_constraints=execution_constraint_wire,
                fills=fill_wire,
                slot_regions=slot_region_wire,
            )
        )
        region_ids.update((graph_id, int(record.id)) for record in active_regions)

    manifest = assemble_manifest(mode, graph_wires, audit=include_provenance)
    revision = manifest["revision"]
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
        audit_manifest=include_provenance,
    )
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
    reached_render_ids_by_graph: dict[int, tuple[OwnershipGraph, set[str]]] = {}
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
        graph = current.context.ownership
        render_id = current.frame.render_id
        if graph is not None and render_id is not None and component_class is not None:
            reached_renders = reached_render_ids_by_graph.get(id(graph))
            if reached_renders is None:
                reached_renders = (graph, set())
                reached_render_ids_by_graph[id(graph)] = reached_renders
            reached_renders[1].add(render_id)
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

    for graph, render_ids in reached_render_ids_by_graph.values():
        if any(
            invocation.state == OwnershipState.ACTIVE
            and has_range_directive(invocation)
            and invocation.source_render_id in render_ids
            and invocation.target_render_id in render_ids
            for invocation in graph.snapshot().component_invocations
        ):
            return True

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
    "has_range_directive",
    "ownership_manifest_required",
    "prepare_ownership_manifest",
]
