"""Selected component-subtree export and detached replay planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from citry.citry_context import CitryContext
from citry.citry_render import (
    CitryRender,
    DeferredComponent,
    PhysicalRegionPart,
    PhysicalRegionRender,
    Placeholder,
    RenderFrame,
)
from citry.client_directives import ComponentTagClientBindingSource, validate_client_props_target
from citry.extension import OnRenderCacheExportContext, RenderCacheInstance, StagedRenderCacheContribution
from citry.ownership import (
    AlpineHandlerClientBindingPayload,
    CitryDomEventClientBindingPayload,
    CitryPollClientBindingPayload,
    ComponentInvocationId,
    ComponentInvocationRecord,
    ComponentTagClientBindingPayload,
    ComponentTagClientBindingRecord,
    InitAncestryRecord,
    LogicalFillId,
    LogicalFillKind,
    LogicalFillRecord,
    LogicalInstanceRecord,
    MorphMode,
    OwnershipSnapshot,
    OwnershipState,
    PhysicalRegionId,
    PhysicalRegionRequestRecord,
    PropsClientBindingPayload,
    QueueState,
    RegionState,
    RenderQueueRecord,
    SourceLocationId,
    SourceLocationKind,
    SourceLocationRecord,
    SourcePolicy,
)
from citry.util.id import gen_render_id, validate_render_id

from .artifact import (
    ArtifactFrame,
    ArtifactFramePart,
    ArtifactPart,
    ArtifactPlaceholderPart,
    ArtifactRegionPart,
    ArtifactTextPart,
    CachedRenderArtifact,
    FrozenJsonObject,
    _freeze_object,
    _thaw_json,
)
from .errors import CacheArtifactError

if TYPE_CHECKING:
    from citry.component import Component
    from citry.ownership import OwnershipGraph


_WriterPath = tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _LiveFrame:
    render: CitryRender
    parts: tuple[ArtifactPart, ...]


@dataclass(frozen=True, slots=True)
class _ArtifactInstance:
    class_id: str
    class_name: str
    parent: _ArtifactRenderRef | None
    transparent: bool


@dataclass(frozen=True, slots=True)
class _ArtifactRenderRef:
    instance: int | None = None
    anchor: str | None = None
    slot: _WriterPath | None = None


@dataclass(frozen=True, slots=True)
class _ExportedOwnership:
    payload: FrozenJsonObject
    instances: tuple[RenderCacheInstance, ...]
    local_by_id: dict[str, int]


def _export_component_artifact(render: CitryRender) -> CachedRenderArtifact:
    """Detach one settled component subtree from all live render objects."""
    return _export_boundary_artifact(render, component_root=True)


def _export_fragment_artifact(render: CitryRender) -> CachedRenderArtifact:
    """Detach one settled transparent fragment subtree from live render objects."""
    return _export_boundary_artifact(render, component_root=False)


def _export_boundary_artifact(render: CitryRender, *, component_root: bool) -> CachedRenderArtifact:
    """Detach one settled subtree rooted at a live component boundary."""
    boundary_id = render.frame.render_id
    if render.frame.is_component_root is not component_root or boundary_id is None:
        kind = "component" if component_root else "fragment"
        raise CacheArtifactError(f"A {kind} cache artifact has an invalid root render boundary.")
    graph = render.context.ownership
    if graph is None:
        raise CacheArtifactError("A component cache artifact requires an ownership graph.")

    live_frames, region_local_by_id = _collect_live_frames(render, graph)
    snapshot = graph.snapshot()
    selected_ids = _select_render_instances(
        live_frames,
        snapshot,
        boundary_id=boundary_id,
        selected_region_ids=set(region_local_by_id),
    )
    active_instances = {
        record.render_id: record for record in snapshot.logical_instances if record.state == OwnershipState.ACTIVE
    }
    if boundary_id not in active_instances:
        raise CacheArtifactError("The cache boundary is not an active ownership instance.")
    missing = selected_ids - set(active_instances)
    if missing:
        raise CacheArtifactError(f"The selected render tree contains inactive instance {sorted(missing)[0]!r}.")

    exported_ownership = _export_ownership(
        render,
        snapshot,
        selected_ids=selected_ids,
        region_local_by_id=region_local_by_id,
    )

    artifact_frames = tuple(_detach_frame(live_frame, exported_ownership.local_by_id) for live_frame in live_frames)
    boundary = render.context.component
    if boundary is None:
        raise CacheArtifactError("A render-cache artifact requires a live boundary component.")
    if type(boundary).transparent is component_root:
        kind = "component" if component_root else "fragment"
        raise CacheArtifactError(f"A {kind} cache artifact has an invalid boundary transparency.")
    extensions = boundary.citry.extensions._export_render_cache(
        OnRenderCacheExportContext(
            citry=boundary.citry,
            root_context=render.context,
            instances=exported_ownership.instances,
            selected_render_ids=frozenset(exported_ownership.local_by_id),
        )
    )
    return CachedRenderArtifact(
        root_frame=0,
        frames=artifact_frames,
        ownership=exported_ownership.payload,
        extensions=extensions,
    )


def _select_render_instances(
    live_frames: tuple[_LiveFrame, ...],
    snapshot: OwnershipSnapshot,
    *,
    boundary_id: str,
    selected_region_ids: set[int],
) -> set[str]:
    """Select component identities represented by the physical subtree."""
    frame_candidates = {
        frame.render.frame.render_id for frame in live_frames if frame.render.frame.render_id is not None
    }
    selected = {
        frame.render.frame.render_id
        for frame in live_frames
        if frame.render.frame.is_component_root and frame.render.frame.render_id is not None
    }
    selected.add(boundary_id)

    # Transparent component outputs have identity-bearing frames but no
    # component-root frame. Follow active invocations into candidates that
    # were physically reached from the selected subtree or one of its Slot
    # regions. The fixed point handles chains of transparent components.
    active_invocations = [record for record in snapshot.component_invocations if record.state == OwnershipState.ACTIVE]
    changed = True
    while changed:
        changed = False
        for invocation in active_invocations:
            target = invocation.target_render_id
            if target is None or target in selected or target not in frame_candidates:
                continue
            parent_region = invocation.physical_parent_region_id
            if invocation.source_render_id in selected or (
                parent_region is not None and int(parent_region) in selected_region_ids
            ):
                selected.add(target)
                changed = True
    return selected


def _collect_live_frames(
    root: CitryRender,
    graph: OwnershipGraph,
) -> tuple[tuple[_LiveFrame, ...], dict[int, int]]:
    """Encode every physical render occurrence while rejecting cycles and reuse."""
    frames: list[_LiveFrame | None] = []
    active: set[int] = set()
    component_roots: set[str] = set()
    wrapper_objects: set[int] = set()
    region_local_by_id: dict[int, int] = {}

    def add_frame(render: CitryRender, path: str) -> int:
        object_id = id(render)
        if object_id in active:
            raise CacheArtifactError(f"Render object cycle encountered at {path}.")
        render_id = render.frame.render_id
        if render.frame.is_component_root and render_id is not None:
            if render_id in component_roots:
                raise CacheArtifactError(f"Component render {render_id!r} occurs more than once in the subtree.")
            component_roots.add(render_id)
        if render.context.ownership is not None and render.context.ownership is not graph:
            raise CacheArtifactError("A cached subtree cannot mix ownership graphs in artifact format v1.")

        frame_index = len(frames)
        frames.append(None)
        active.add(object_id)
        try:
            parts = tuple(
                add_part(part, f"{path}.parts[{part_index}]") for part_index, part in enumerate(render.parts)
            )
        finally:
            active.remove(object_id)
        frames[frame_index] = _LiveFrame(render=render, parts=parts)
        return frame_index

    def add_part(part: object, path: str) -> ArtifactPart:
        if isinstance(part, str):
            return ArtifactTextPart(str(part))
        if isinstance(part, (PhysicalRegionPart, PhysicalRegionRender)):
            wrapper_id = id(part)
            if wrapper_id in wrapper_objects:
                raise CacheArtifactError(f"Physical region wrapper occurs more than once at {path}.")
            wrapper_objects.add(wrapper_id)
            if part.graph is not graph:
                raise CacheArtifactError("A cached subtree cannot contain a physical region from another graph.")
            region_id = int(part.region_id)
            if region_id in region_local_by_id:
                raise CacheArtifactError(f"Physical region {region_id} occurs more than once in the subtree.")
            local_region = len(region_local_by_id)
            region_local_by_id[region_id] = local_region
            return ArtifactRegionPart(local_region, add_part(part.part, f"{path}.part"))
        if isinstance(part, CitryRender):
            return ArtifactFramePart(add_frame(part, path))
        if isinstance(part, Placeholder):
            return ArtifactPlaceholderPart(part.key)
        if isinstance(part, DeferredComponent):
            raise CacheArtifactError("Cannot export an unsettled DeferredComponent into a cache artifact.")
        raise CacheArtifactError(f"Unsupported settled render part {type(part).__name__} at {path}.")

    add_frame(root, "render")
    return tuple(cast("_LiveFrame", frame) for frame in frames), region_local_by_id


def _export_ownership(
    render: CitryRender,
    snapshot: OwnershipSnapshot,
    *,
    selected_ids: set[str],
    region_local_by_id: dict[int, int],
) -> _ExportedOwnership:
    """Detach the selected active ownership closure into local references."""
    boundary = render.context.component
    if boundary is None:
        raise CacheArtifactError("A component artifact boundary requires its current live component.")
    boundary_id = boundary.id
    active_instances = {
        record.render_id: record for record in snapshot.logical_instances if record.state == OwnershipState.ACTIVE
    }
    active_fills = {record.id: record for record in snapshot.logical_fills if record.state == OwnershipState.ACTIVE}
    source_by_id = {record.id: record for record in snapshot.source_locations}
    invocation_by_id = {record.id: record for record in snapshot.component_invocations}

    fill_anchor_by_id: dict[LogicalFillId, _WriterPath] = {}
    fill_anchor_by_path: dict[_WriterPath, LogicalFillRecord] = {}
    writer_paths_by_id: dict[str, list[_WriterPath]] = {}
    graph = render.context.ownership
    if graph is None:  # guarded by the caller
        raise CacheArtifactError("A component artifact boundary requires an ownership graph.")

    # A cached Slot body may itself contain a literal <c-slot>. Follow the
    # current component-parent chain so those transitive fills and lexical
    # writers remain symbolic anchors rather than being mistaken for local
    # cached instances. A one-part path is the boundary's direct supplied Slot;
    # each later part names a supplied Slot on the preceding lexical writer.
    live_ancestors: dict[str, Component] = {}
    ancestor_depth: dict[str, int] = {}
    current: Component | None = boundary
    depth = 0
    while current is not None:
        live_ancestors[current.id] = current
        ancestor_depth[current.id] = depth
        current = current.parent
        depth += 1
    pending_receivers: list[tuple[Component, _WriterPath]] = [(boundary, ())]
    visited_receiver_paths: set[tuple[str, _WriterPath]] = set()
    while pending_receivers:
        receiver, prefix = pending_receivers.pop()
        receiver_key = (receiver.id, prefix)
        if receiver_key in visited_receiver_paths:
            continue
        visited_receiver_paths.add(receiver_key)
        for slot_name in receiver.raw_slots:
            current_fill_id = graph.supplied_fill_id(receiver, slot_name)
            if current_fill_id is None:
                continue
            writer_path = (*prefix, slot_name)
            fill = active_fills.get(current_fill_id)
            if fill is None:
                continue
            fill_anchor_by_id[current_fill_id] = writer_path
            fill_anchor_by_path[writer_path] = fill
            writer_id = fill.lexical_owner_render_id
            if writer_id is None:
                continue
            writer_paths_by_id.setdefault(writer_id, []).append(writer_path)
            writer = live_ancestors.get(writer_id)
            if writer is not None and ancestor_depth[writer.id] > ancestor_depth[receiver.id]:
                pending_receivers.append((writer, writer_path))

    selected_closure = set(selected_ids)
    selected_closure.add(boundary_id)
    pending = list(selected_closure)
    while pending:
        render_id = pending.pop()
        record = active_instances.get(render_id)
        if record is None:
            raise CacheArtifactError(f"Selected ownership instance {render_id!r} is not active.")
        # The cache boundary keeps the current call's already-bound parent.
        # Its original outer parent is not part of the reusable subtree.
        if render_id == boundary_id:
            continue
        parent_id = record.logical_parent_render_id
        if parent_id is None or parent_id == boundary_id or parent_id in writer_paths_by_id:
            continue
        if parent_id not in active_instances:
            raise CacheArtifactError(
                f"Selected descendant {render_id!r} refers to unavailable logical parent {parent_id!r}."
            )
        if parent_id not in selected_closure:
            selected_closure.add(parent_id)
            pending.append(parent_id)

    ordered_ids = [boundary_id]
    ordered_ids.extend(
        record.render_id
        for record in snapshot.logical_instances
        if record.state == OwnershipState.ACTIVE
        and record.render_id in selected_closure
        and record.render_id != boundary_id
    )
    local_by_id = {render_id: index for index, render_id in enumerate(ordered_ids)}

    def render_ref(
        render_id: str | None,
        *,
        allow_none: bool = True,
        writer_path: _WriterPath | None = None,
    ) -> object:
        if render_id is None:
            if allow_none:
                return None
            raise CacheArtifactError("A required ownership render reference is absent.")
        local = local_by_id.get(render_id)
        if local is not None:
            return local
        writer_paths = writer_paths_by_id.get(render_id, [])
        if writer_path is not None:
            if writer_path not in writer_paths:
                raise CacheArtifactError(
                    f"Ownership relation does not belong to supplied Slot path {writer_path!r}'s writer."
                )
            return {"anchor": "writer", "slot": _writer_path_to_wire(writer_path)}
        if len(writer_paths) == 1:
            return {"anchor": "writer", "slot": _writer_path_to_wire(writer_paths[0])}
        if writer_paths:
            raise CacheArtifactError(f"Ownership relation to render {render_id!r} is ambiguous across supplied Slots.")
        raise CacheArtifactError(f"Ownership relation refers to render {render_id!r} outside the cached subtree.")

    active_regions = {
        record.id: record
        for record in snapshot.physical_regions
        if record.state == RegionState.CAPTURED and int(record.id) in region_local_by_id
    }
    if {int(record_id) for record_id in active_regions} != set(region_local_by_id):
        raise CacheArtifactError("A selected physical wrapper refers to an inactive ownership region.")

    selected_fill_ids = {
        region.logical_fill_id for region in active_regions.values() if region.logical_fill_id not in fill_anchor_by_id
    }
    selected_fills = [
        record
        for record in snapshot.logical_fills
        if record.state == OwnershipState.ACTIVE and record.id in selected_fill_ids
    ]
    fill_local_by_id = {record.id: index for index, record in enumerate(selected_fills)}

    selected_invocations = [
        record
        for record in snapshot.component_invocations
        if record.state == OwnershipState.ACTIVE
        and record.target_render_id != boundary_id
        and (
            record.target_render_id in selected_closure
            or any(render_id in selected_closure for render_id in record.selector_render_ids)
        )
    ]
    invocation_local_by_id = {record.id: index for index, record in enumerate(selected_invocations)}

    selected_location_ids: set[SourceLocationId] = set()
    for invocation in selected_invocations:
        selected_location_ids.add(invocation.source_location_id)
        selected_location_ids.update(
            client_binding.source_location_id for client_binding in invocation.client_bindings
        )
    for fill in selected_fills:
        for location_id in (
            fill.source_location_id,
            fill.fallback_slot_site_location_id,
        ):
            if location_id is not None:
                selected_location_ids.add(location_id)
    for region in active_regions.values():
        for location_id in (region.slot_site_location_id, region.source_location_id):
            if location_id is not None:
                selected_location_ids.add(location_id)
    selected_locations = [record for record in snapshot.source_locations if record.id in selected_location_ids]
    location_local_by_id = {record.id: index for index, record in enumerate(selected_locations)}
    if set(location_local_by_id) != selected_location_ids:
        raise CacheArtifactError("A selected ownership relation refers to a missing source location.")

    writer_path_by_location: dict[SourceLocationId, _WriterPath] = {}
    for location in selected_locations:
        writer_paths = writer_paths_by_id.get(location.owner_render_id, [])
        if not writer_paths:
            continue
        candidates: list[_WriterPath] = []
        for writer_path in writer_paths:
            fill = fill_anchor_by_path[writer_path]
            if fill.source_location_id is None:
                continue
            fill_location = source_by_id.get(fill.source_location_id)
            if fill_location is None:
                raise CacheArtifactError(f"Supplied Slot {slot_name!r} has no source-location record.")
            if (
                location.source == fill_location.source
                and location.origin == fill_location.origin
                and fill_location.span[0] <= location.span[0] <= location.span[1] <= fill_location.span[1]
            ):
                candidates.append(writer_path)
        if len(candidates) != 1:
            raise CacheArtifactError(
                f"Source location {int(location.id)} cannot be assigned to exactly one supplied Slot writer."
            )
        writer_path_by_location[location.id] = candidates[0]

    def writer_occurrence(location: SourceLocationRecord, writer_path: _WriterPath) -> int | None:
        fill = fill_anchor_by_path[writer_path]
        if fill.source_location_id is None:
            raise CacheArtifactError(f"Supplied Slot {slot_name!r} has no source location.")
        fill_location = source_by_id[fill.source_location_id]
        if location.id == fill_location.id:
            return None
        snippet = location.snippet
        if not snippet:
            raise CacheArtifactError("An external writer source location cannot have an empty span.")
        starts: list[int] = []
        cursor = fill_location.span[0]
        while True:
            found = fill_location.source.find(snippet, cursor, fill_location.span[1])
            if found < 0:
                break
            starts.append(found)
            cursor = found + 1
        try:
            return starts.index(location.span[0])
        except ValueError as err:
            raise CacheArtifactError(
                f"Source location {int(location.id)} is not an exact occurrence inside its supplied Slot."
            ) from err

    def relation_writer_path(location_id: SourceLocationId | None) -> _WriterPath | None:
        return None if location_id is None else writer_path_by_location.get(location_id)

    boundary_invocation = next(
        (
            record
            for record in snapshot.component_invocations
            if record.id == active_instances[boundary_id].invocation_id
        ),
        None,
    )
    boundary_parent_region = None if boundary_invocation is None else boundary_invocation.physical_parent_region_id

    def invocation_ref(invocation_id: ComponentInvocationId | None) -> object:
        if invocation_id is None:
            return None
        local = invocation_local_by_id.get(invocation_id)
        if local is not None:
            return local
        if boundary_invocation is not None and invocation_id == boundary_invocation.id:
            return {"anchor": "invocation"}
        raise CacheArtifactError(
            f"Ownership relation refers to invocation {int(invocation_id)} outside the cached subtree."
        )

    def fill_ref(fill_id: LogicalFillId) -> object:
        local = fill_local_by_id.get(fill_id)
        if local is not None:
            return local
        writer_path = fill_anchor_by_id.get(fill_id)
        if writer_path is not None:
            return {"anchor": "fill", "slot": _writer_path_to_wire(writer_path)}
        raise CacheArtifactError(f"Ownership region refers to fill {int(fill_id)} outside the cached subtree.")

    def region_ref(region_id: PhysicalRegionId | None) -> object:
        if region_id is None:
            return None
        local = region_local_by_id.get(int(region_id))
        if local is not None:
            return local
        if boundary_parent_region is not None and region_id == boundary_parent_region:
            return {"anchor": "containing-region"}
        raise CacheArtifactError(
            f"Ownership relation refers to physical region {int(region_id)} outside the cached subtree."
        )

    selected_init = [
        record
        for record in snapshot.init_ancestry
        if record.state == OwnershipState.ACTIVE and record.invocation_id in invocation_local_by_id
    ]
    selected_queue = [record for record in snapshot.render_queue if record.invocation_id in invocation_local_by_id]
    if any(record.state != QueueState.SETTLED for record in selected_queue):
        raise CacheArtifactError("A cached ownership subtree contains unsettled render-queue work.")

    order_values: set[int] = set()
    for records in (
        selected_locations,
        selected_invocations,
        [active_instances[render_id] for render_id in ordered_ids],
        selected_init,
        selected_fills,
        list(active_regions.values()),
    ):
        order_values.update(record.order for record in records)
    for queue in selected_queue:
        order_values.add(queue.enqueued_order)
        if queue.rendered_order is not None:
            order_values.add(queue.rendered_order)
        if queue.settled_order is not None:
            order_values.add(queue.settled_order)
    order_rank = {value: index + 1 for index, value in enumerate(sorted(order_values))}

    instance_values = []
    for render_id in ordered_ids:
        record = active_instances[render_id]
        instance_invocation = None if record.invocation_id is None else invocation_by_id.get(record.invocation_id)
        parent = (
            None
            if render_id == boundary_id
            else render_ref(
                record.logical_parent_render_id,
                allow_none=False,
                writer_path=(
                    None
                    if instance_invocation is None
                    else relation_writer_path(instance_invocation.source_location_id)
                ),
            )
        )
        instance_values.append(
            {
                "class_id": record.class_id,
                "class_name": record.class_name,
                "invocation": None if render_id == boundary_id else invocation_ref(record.invocation_id),
                "order": order_rank[record.order],
                "parent": parent,
                "transparent": record.transparent,
            }
        )

    payload = _freeze_object(
        {
            "fills": [
                {
                    "fallback_location": (
                        None
                        if record.fallback_slot_site_location_id is None
                        else location_local_by_id[record.fallback_slot_site_location_id]
                    ),
                    "id": fill_local_by_id[record.id],
                    "kind": record.kind.value,
                    "lexical_class": record.lexical_owner_class_id,
                    "lexical_owner": render_ref(
                        record.lexical_owner_render_id,
                        writer_path=relation_writer_path(record.source_location_id),
                    ),
                    "order": order_rank[record.order],
                    "receiver": render_ref(record.receiver_render_id),
                    "receiver_class": record.receiver_class_id,
                    "slot": record.slot_name,
                    "source_invocation": invocation_ref(record.source_invocation_id),
                    "source_location": (
                        None if record.source_location_id is None else location_local_by_id[record.source_location_id]
                    ),
                    "source_policy": record.source_policy.value,
                }
                for record in selected_fills
            ],
            "init": [
                {
                    "child": render_ref(
                        record.child_render_id,
                        allow_none=False,
                        writer_path=relation_writer_path(invocation_by_id[record.invocation_id].source_location_id),
                    ),
                    "invocation": invocation_local_by_id[record.invocation_id],
                    "order": order_rank[record.order],
                    "parent": render_ref(
                        record.parent_render_id,
                        allow_none=False,
                        writer_path=relation_writer_path(invocation_by_id[record.invocation_id].source_location_id),
                    ),
                }
                for record in selected_init
            ],
            "instances": instance_values,
            "invocations": [
                {
                    "authored_tag": record.authored_tag,
                    "id": invocation_local_by_id[record.id],
                    "location": location_local_by_id[record.source_location_id],
                    "morph_key": record.morph_key,
                    "morph_mode": record.morph_mode,
                    "order": order_rank[record.order],
                    "parent_region": region_ref(record.physical_parent_region_id),
                    "client_bindings": [
                        _client_binding_to_wire(client_binding, location_local_by_id)
                        for client_binding in record.client_bindings
                    ],
                    "selectors": [
                        render_ref(
                            value,
                            allow_none=False,
                            writer_path=relation_writer_path(record.source_location_id),
                        )
                        for value in record.selector_render_ids
                    ],
                    "source": render_ref(
                        record.source_render_id,
                        allow_none=False,
                        writer_path=relation_writer_path(record.source_location_id),
                    ),
                    "source_class": record.source_class_id,
                    "target": render_ref(record.target_render_id),
                    "target_class": record.target_class_id,
                }
                for record in selected_invocations
            ],
            "locations": [
                {
                    "byte_span": list(record.byte_span),
                    "column": record.column,
                    "id": location_local_by_id[record.id],
                    "kind": record.kind.value,
                    "line": record.line,
                    "mapping_index": record.mapping_index,
                    "mapping_key": record.mapping_key,
                    "order": order_rank[record.order],
                    "origin": record.origin,
                    "owner": render_ref(
                        record.owner_render_id,
                        allow_none=False,
                        writer_path=writer_path_by_location.get(record.id),
                    ),
                    "owner_class": record.owner_class_id,
                    "source": record.source,
                    "span": list(record.span),
                    "writer_occurrence": (
                        None
                        if record.id not in writer_path_by_location
                        else writer_occurrence(record, writer_path_by_location[record.id])
                    ),
                    "writer_slot": (
                        None
                        if record.id not in writer_path_by_location
                        else _writer_path_to_wire(writer_path_by_location[record.id])
                    ),
                }
                for record in selected_locations
            ],
            "queue": [
                {
                    "enqueued": order_rank[record.enqueued_order],
                    "invocation": invocation_local_by_id[record.invocation_id],
                    "rendered": (None if record.rendered_order is None else order_rank[record.rendered_order]),
                    "settled": (None if record.settled_order is None else order_rank[record.settled_order]),
                    "state": record.state.value,
                    "target": render_ref(record.target_render_id),
                }
                for record in selected_queue
            ],
            "regions": [
                {
                    "containing": region_ref(record.containing_region_id),
                    "fill": fill_ref(record.logical_fill_id),
                    "id": region_local_by_id[int(record.id)],
                    "lexical_owner": render_ref(
                        record.lexical_owner_render_id,
                        writer_path=relation_writer_path(record.source_location_id),
                    ),
                    "order": order_rank[record.order],
                    "receiver": render_ref(record.receiver_render_id),
                    "result_owner": render_ref(
                        record.result_owner_render_id,
                        writer_path=relation_writer_path(record.source_location_id),
                    ),
                    "slot_location": (
                        None
                        if record.slot_site_location_id is None
                        else location_local_by_id[record.slot_site_location_id]
                    ),
                    "source_location": (
                        None if record.source_location_id is None else location_local_by_id[record.source_location_id]
                    ),
                    "transition_from": render_ref(record.transition_from_render_id),
                }
                for record in sorted(active_regions.values(), key=lambda item: region_local_by_id[int(item.id)])
            ],
        },
        "artifact.ownership",
    )
    return _ExportedOwnership(
        payload=payload,
        instances=tuple(
            RenderCacheInstance(
                index=index,
                render_id=render_id,
                class_id=active_instances[render_id].class_id,
            )
            for index, render_id in enumerate(ordered_ids)
        ),
        local_by_id=local_by_id,
    )


def _client_binding_to_wire(
    client_binding: ComponentTagClientBindingRecord,
    location_local_by_id: dict[SourceLocationId, int],
) -> dict[str, object]:
    payload = client_binding.payload
    if isinstance(payload, (PropsClientBindingPayload, AlpineHandlerClientBindingPayload)):
        payload_wire: dict[str, object] = {
            "expression": payload.expression,
            "type": payload.type,
        }
    elif isinstance(payload, CitryDomEventClientBindingPayload):
        payload_wire = {
            "args": payload.args,
            "class_id": payload.class_id,
            "debounce": payload.debounce,
            "event": payload.event,
            "handler": payload.handler,
            "key": payload.key,
            "once": payload.once,
            "prevent": payload.prevent,
            "self": payload.self_,
            "stop": payload.stop,
            "throttle": payload.throttle,
            "type": payload.type,
        }
    elif isinstance(payload, CitryPollClientBindingPayload):
        payload_wire = {
            "args": payload.args,
            "class_id": payload.class_id,
            "handler": payload.handler,
            "interval": payload.interval,
            "type": payload.type,
        }
    else:  # pragma: no cover - closed internal union
        raise CacheArtifactError(f"Unsupported component-tag client binding payload {type(payload).__name__}.")
    return {
        "key": client_binding.key,
        "location": location_local_by_id[client_binding.source_location_id],
        "payload": payload_wire,
        "source": client_binding.source.value,
    }


def _detach_frame(
    live: _LiveFrame,
    local_by_id: dict[str, int],
) -> ArtifactFrame:
    frame = live.render.frame
    render_id = frame.render_id
    instance = local_by_id.get(render_id) if render_id is not None else None
    class_id = frame.class_id if instance is not None else None
    class_name = frame.class_name if instance is not None else None
    markers = _detached_markers((*frame.root_markers, *live.render.context._get_root_markers()))
    return ArtifactFrame(
        instance=instance,
        class_id=class_id,
        class_name=class_name,
        is_component_root=frame.is_component_root,
        root_markers=markers,
        parts=live.parts,
    )


def _detached_markers(markers: tuple[str, ...]) -> tuple[str, ...]:
    """Strip render-ID markers before detached storage."""
    detached: list[str] = []
    for marker in markers:
        if marker.startswith('data-cid="'):
            continue
        if marker not in detached:
            detached.append(marker)
    return tuple(detached)


def _replay_component_artifact(
    artifact: CachedRenderArtifact,
    *,
    boundary: Component,
    context: CitryContext,
    revision: int | None = None,
) -> CitryRender:
    """Validate, stage, and atomically attach one component artifact."""
    return _replay_boundary_artifact(
        artifact,
        boundary=boundary,
        context=context,
        revision=revision,
        component_root=True,
    )


def _replay_fragment_artifact(
    artifact: CachedRenderArtifact,
    *,
    boundary: Component,
    context: CitryContext,
    revision: int | None = None,
) -> CitryRender:
    """Validate, stage, and attach one transparent fragment artifact."""
    return _replay_boundary_artifact(
        artifact,
        boundary=boundary,
        context=context,
        revision=revision,
        component_root=False,
    )


def _replay_boundary_artifact(
    artifact: CachedRenderArtifact,
    *,
    boundary: Component,
    context: CitryContext,
    revision: int | None,
    component_root: bool,
) -> CitryRender:
    """Validate, stage, and atomically attach one boundary artifact."""
    graph = context.ownership
    if graph is None or boundary._ownership_graph is not graph:
        raise CacheArtifactError("The current cache boundary has no matching ownership graph.")
    if context.component is not boundary:
        raise CacheArtifactError("The replay context does not belong to the current cache boundary.")
    instances = _decode_instances(artifact.ownership)
    if not instances:
        raise CacheArtifactError("Artifact ownership has no cache-boundary instance.")
    boundary_class = type(boundary)
    root_instance = instances[0]
    if root_instance.class_id != boundary_class.class_id:
        raise CacheArtifactError("Artifact boundary class does not match the current component class.")
    if boundary_class.transparent is component_root:
        kind = "component" if component_root else "fragment"
        raise CacheArtifactError(f"The current {kind} cache boundary has invalid transparency.")

    for index, instance in enumerate(instances):
        try:
            component_class = boundary.citry.get_component_by_class_id(instance.class_id)
        except KeyError as err:
            raise CacheArtifactError(
                f"Artifact instance {index} refers to a class_id with no registered component."
            ) from err
        if component_class.__name__ != instance.class_name:
            raise CacheArtifactError(f"Artifact instance {index} class name does not match the registered component.")
    _validate_instance_frames(artifact, instances, boundary_component_root=component_root)

    id_by_instance = [boundary.id]
    occupied = {record.render_id for record in graph.snapshot().logical_instances}
    for _instance in instances[1:]:
        render_id = _mint_render_id(boundary.citry)
        if render_id in occupied:
            raise CacheArtifactError(f"The Citry id_generator produced duplicate replay ID {render_id!r}.")
        occupied.add(render_id)
        id_by_instance.append(render_id)

    (
        ownership_snapshot,
        external_sources,
        external_invocations,
        external_fills,
        external_regions,
    ) = _decode_ownership_snapshot(
        artifact.ownership,
        instances=instances,
        id_by_instance=id_by_instance,
        boundary=boundary,
        graph=graph,
        preserve_unmatched_writer_locations=not component_root,
    )
    for invocation in ownership_snapshot.component_invocations:
        try:
            target_class = boundary.citry.get_component_by_class_id(invocation.target_class_id)
        except KeyError as err:
            raise CacheArtifactError(
                "Artifact component invocation refers to a target class_id with no registered component."
            ) from err
        try:
            validate_client_props_target(
                target_class,
                (binding.key for binding in invocation.client_bindings),
                tag_name=f"c-{invocation.authored_tag}",
            )
        except RuntimeError as err:
            raise CacheArtifactError(str(err)) from err
    staged = boundary.citry.extensions._stage_render_cache(
        artifact.extensions,
        instance_ids=tuple(id_by_instance),
        instance_class_ids=tuple(instance.class_id for instance in instances),
    )
    staged_frame_markers = _validate_replay_plan(
        artifact,
        staged,
        instance_count=len(instances),
        region_count=len(ownership_snapshot.physical_regions),
        existing_extra=context.extra,
    )
    cache_extension = boundary.citry.extensions.get_extension("cache")
    if revision is not None and cast("Any", cache_extension)._revision_snapshot() != revision:
        raise CacheArtifactError("The render-cache revision changed while the artifact was staged.")

    written_cleanup_keys: list[str] = []
    original_extra = context.extra
    try:
        for contribution in staged:
            for write in contribution.cache_writes:
                previous = boundary.citry.cache.get(write.key)
                if previous == write.value:
                    continue
                boundary.citry.cache.set(write.key, write.value, ttl=write.ttl)
                if write.rollback_delete and previous is None:
                    written_cleanup_keys.append(write.key)
        with cast("Any", cache_extension)._stable_revision(revision):
            with graph.replay_transaction():
                region_ids = graph.import_replayed_snapshot(
                    ownership_snapshot,
                    external_source_ids=external_sources,
                    external_invocation_ids=external_invocations,
                    external_fill_ids=external_fills,
                    external_region_ids=external_regions,
                )
                context.extra = dict(original_extra)
                for contribution in staged:
                    for key, value in contribution.extra_items:
                        context.extra[key] = value
                replayed = _build_replayed_tree(
                    artifact,
                    root_frame=artifact.root_frame,
                    id_by_instance=id_by_instance,
                    boundary=boundary,
                    boundary_context=context,
                    graph=graph,
                    region_ids=region_ids,
                    staged_frame_markers=staged_frame_markers,
                )
    except Exception:
        context.extra = original_extra
        for key in reversed(written_cleanup_keys):
            boundary.citry.cache.delete(key)
        raise
    return replayed


def _validate_replay_plan(
    artifact: CachedRenderArtifact,
    staged: tuple[StagedRenderCacheContribution, ...],
    *,
    instance_count: int,
    region_count: int,
    existing_extra: dict[str, Any],
) -> dict[int, tuple[str, ...]]:
    """Cross-check every staged reference before any repair write occurs."""
    for frame_index, frame in enumerate(artifact.frames):
        pending = list(frame.parts)
        while pending:
            part = pending.pop()
            if type(part) is ArtifactRegionPart:
                if not 0 <= part.region < region_count:
                    raise CacheArtifactError(
                        f"artifact.frames[{frame_index}] refers to missing ownership region {part.region}."
                    )
                pending.append(part.part)

    extra_keys = set(existing_extra)
    frame_markers: dict[int, list[str]] = {}
    for contribution in staged:
        for key, _value in contribution.extra_items:
            if type(key) is not str or not key:
                raise CacheArtifactError("Render-cache replay contribution has an invalid context key.")
            if key in extra_keys:
                raise CacheArtifactError(f"Render-cache replay contribution duplicates context key {key!r}.")
            extra_keys.add(key)
        for marker_instance, markers in contribution.frame_markers:
            if not 0 <= marker_instance < instance_count:
                raise CacheArtifactError(
                    f"Render-cache replay contribution refers to missing instance {marker_instance}."
                )
            frame_markers.setdefault(marker_instance, []).extend(markers)
    return {instance: tuple(dict.fromkeys(markers)) for instance, markers in frame_markers.items()}


def _decode_instances(value: FrozenJsonObject) -> tuple[_ArtifactInstance, ...]:
    wire = _thaw_json(value)
    expected_fields = {"fills", "init", "instances", "invocations", "locations", "queue", "regions"}
    if type(wire) is not dict or set(wire) != expected_fields:
        raise CacheArtifactError("artifact.ownership has an invalid field set.")
    instance_values = wire["instances"]
    if type(instance_values) is not list:
        raise CacheArtifactError("artifact.ownership.instances must be an array.")
    result: list[_ArtifactInstance] = []
    for index, item in enumerate(instance_values):
        path = f"artifact.ownership.instances[{index}]"
        if type(item) is not dict or set(item) != {
            "class_id",
            "class_name",
            "invocation",
            "order",
            "parent",
            "transparent",
        }:
            raise CacheArtifactError(f"{path} has an invalid field set.")
        class_id = item["class_id"]
        class_name = item["class_name"]
        parent = _decode_render_ref(item["parent"], path=f"{path}.parent", instance_count=index)
        transparent = item["transparent"]
        if type(class_id) is not str or not class_id:
            raise CacheArtifactError(f"{path}.class_id must be a non-empty string.")
        if type(class_name) is not str or not class_name:
            raise CacheArtifactError(f"{path}.class_name must be a non-empty string.")
        if index == 0 and parent is not None:
            raise CacheArtifactError("The artifact cache boundary cannot have an archived parent.")
        if index > 0 and parent is None:
            raise CacheArtifactError(f"{path}.parent is required for a descendant.")
        if type(transparent) is not bool:
            raise CacheArtifactError(f"{path}.transparent must be a bool.")
        result.append(
            _ArtifactInstance(
                class_id=class_id,
                class_name=class_name,
                parent=parent,
                transparent=transparent,
            )
        )
    return tuple(result)


def _writer_path_to_wire(path: _WriterPath) -> object:
    """Keep direct Slot anchors compatible while encoding transitive paths."""
    if len(path) == 1:
        return path[0]
    return list(path)


def _writer_path_from_wire(value: object, path: str) -> _WriterPath:
    """Decode one direct Slot name or a canonical transitive Slot path."""
    if type(value) is str:
        return (_nonempty_string(value, path),)
    items = _exact_list(value, path)
    if len(items) < 2:
        raise CacheArtifactError(f"{path} transitive Slot path must contain at least two names.")
    return tuple(_nonempty_string(item, f"{path}[{index}]") for index, item in enumerate(items))


def _decode_render_ref(value: object, *, path: str, instance_count: int) -> _ArtifactRenderRef | None:
    if value is None:
        return None
    if type(value) is int:
        if not 0 <= value < instance_count:
            raise CacheArtifactError(f"{path} must refer to an earlier artifact instance.")
        return _ArtifactRenderRef(instance=value)
    mapping = _exact_object(value, {"anchor", "slot"}, path)
    if mapping["anchor"] != "writer":
        raise CacheArtifactError(f"{path}.anchor must be 'writer'.")
    return _ArtifactRenderRef(
        anchor="writer",
        slot=_writer_path_from_wire(mapping["slot"], f"{path}.slot"),
    )


def _validate_instance_frames(
    artifact: CachedRenderArtifact,
    instances: tuple[_ArtifactInstance, ...],
    *,
    boundary_component_root: bool,
) -> None:
    roots = [0] * len(instances)
    for frame_index, frame in enumerate(artifact.frames):
        if frame.instance is None:
            continue
        if not 0 <= frame.instance < len(instances):
            raise CacheArtifactError(
                f"artifact.frames[{frame_index}].instance refers to a missing ownership instance."
            )
        instance = instances[frame.instance]
        if frame.class_id != instance.class_id or frame.class_name != instance.class_name:
            raise CacheArtifactError(
                f"artifact.frames[{frame_index}] class identity does not match its ownership instance."
            )
        if frame.is_component_root:
            roots[frame.instance] += 1
    root_frame = artifact.frames[artifact.root_frame]
    if root_frame.instance != 0 or root_frame.is_component_root is not boundary_component_root:
        expected = "component root" if boundary_component_root else "transparent fragment boundary"
        raise CacheArtifactError(f"The artifact root frame must be the cache-boundary {expected}.")
    if instances[0].transparent is boundary_component_root:
        raise CacheArtifactError("The artifact cache boundary has invalid transparency for its cache kind.")
    for index, (instance, count) in enumerate(zip(instances, roots, strict=True)):
        expected_roots = 0 if instance.transparent else 1
        if count != expected_roots:
            raise CacheArtifactError(
                f"artifact ownership instance {index} requires {expected_roots} component-root frame(s), got {count}."
            )


def _decode_ownership_snapshot(
    value: FrozenJsonObject,
    *,
    instances: tuple[_ArtifactInstance, ...],
    id_by_instance: list[str],
    boundary: Component,
    graph: OwnershipGraph,
    preserve_unmatched_writer_locations: bool = False,
) -> tuple[
    OwnershipSnapshot,
    dict[SourceLocationId, SourceLocationId],
    dict[ComponentInvocationId, ComponentInvocationId],
    dict[LogicalFillId, LogicalFillId],
    dict[PhysicalRegionId, PhysicalRegionId],
]:
    wire = _thaw_json(value)
    root = _exact_object(
        wire,
        {"fills", "init", "instances", "invocations", "locations", "queue", "regions"},
        "artifact.ownership",
    )
    instance_values = _exact_list(root["instances"], "artifact.ownership.instances")
    if len(instance_values) != len(instances):
        raise CacheArtifactError("artifact.ownership.instances changed during validation.")

    graph_snapshot = graph.snapshot()
    current_instances = {
        record.render_id: record
        for record in graph_snapshot.logical_instances
        if record.state == OwnershipState.ACTIVE
    }
    current_fills = {record.id: record for record in graph_snapshot.logical_fills}
    current_locations = {record.id: record for record in graph_snapshot.source_locations}
    boundary_instance = current_instances.get(boundary.id)
    if boundary_instance is None:
        raise CacheArtifactError("The current cache boundary is absent from its ownership graph.")
    boundary_invocation_id = boundary_instance.invocation_id
    boundary_invocation = next(
        (
            record
            for record in graph_snapshot.component_invocations
            if record.id == boundary_invocation_id and record.state == OwnershipState.ACTIVE
        ),
        None,
    )

    writer_by_path: dict[_WriterPath, str] = {}
    current_fill_by_path: dict[_WriterPath, LogicalFillId] = {}
    current_fill_location_by_path: dict[_WriterPath, SourceLocationRecord] = {}
    live_ancestors: dict[str, Component] = {}
    ancestor_depth: dict[str, int] = {}
    current: Component | None = boundary
    depth = 0
    while current is not None:
        live_ancestors[current.id] = current
        ancestor_depth[current.id] = depth
        current = current.parent
        depth += 1
    pending_receivers: list[tuple[Component, _WriterPath]] = [(boundary, ())]
    visited_receiver_paths: set[tuple[str, _WriterPath]] = set()
    while pending_receivers:
        receiver, prefix = pending_receivers.pop()
        receiver_key = (receiver.id, prefix)
        if receiver_key in visited_receiver_paths:
            continue
        visited_receiver_paths.add(receiver_key)
        for slot_name in receiver.raw_slots:
            current_fill_id = graph.supplied_fill_id(receiver, slot_name)
            if current_fill_id is None:
                continue
            writer_path = (*prefix, slot_name)
            fill = current_fills.get(current_fill_id)
            if fill is None or fill.state != OwnershipState.ACTIVE:
                raise CacheArtifactError(f"Current supplied Slot path {writer_path!r} has no active ownership fill.")
            current_fill_by_path[writer_path] = current_fill_id
            writer_id = fill.lexical_owner_render_id
            if writer_id is None:
                continue
            writer_by_path[writer_path] = writer_id
            if fill.source_location_id is None or fill.source_location_id not in current_locations:
                raise CacheArtifactError(f"Current supplied Slot path {writer_path!r} has no source location.")
            current_fill_location_by_path[writer_path] = current_locations[fill.source_location_id]
            writer = live_ancestors.get(writer_id)
            if writer is not None and ancestor_depth[writer.id] > ancestor_depth[receiver.id]:
                pending_receivers.append((writer, writer_path))

    def writer_anchor_path(value: object, path: str) -> _WriterPath | None:
        if type(value) is not dict:
            return None
        anchor = _exact_object(value, {"anchor", "slot"}, path)
        if anchor["anchor"] != "writer":
            raise CacheArtifactError(f"{path}.anchor must be 'writer'.")
        return _writer_path_from_wire(anchor["slot"], f"{path}.slot")

    def resolve_render_ref(value: object, path: str, *, allow_none: bool = True) -> str | None:
        if value is None:
            if allow_none:
                return None
            raise CacheArtifactError(f"{path} is required.")
        if type(value) is int:
            if not 0 <= value < len(id_by_instance):
                raise CacheArtifactError(f"{path} refers to a missing artifact instance.")
            return id_by_instance[value]
        anchor = _exact_object(value, {"anchor", "slot"}, path)
        if anchor["anchor"] != "writer":
            raise CacheArtifactError(f"{path}.anchor must be 'writer'.")
        writer_path = _writer_path_from_wire(anchor["slot"], f"{path}.slot")
        try:
            return writer_by_path[writer_path]
        except KeyError as err:
            raise CacheArtifactError(
                f"{path} requires a current lexical writer for supplied Slot path {writer_path!r}."
            ) from err

    location_values = _exact_list(root["locations"], "artifact.ownership.locations")
    location_count = len(location_values)
    location_ids_by_index: list[SourceLocationId] = []

    def location_id(value: object, path: str, *, optional: bool = False) -> SourceLocationId | None:
        if value is None and optional:
            return None
        index = _bounded_index(value, location_count, path)
        try:
            return location_ids_by_index[index]
        except IndexError as err:  # defensive: all callers run after location decoding
            raise CacheArtifactError(f"{path} was resolved before source-location staging completed.") from err

    invocation_values = _exact_list(root["invocations"], "artifact.ownership.invocations")
    invocation_count = len(invocation_values)
    external_invocations: dict[ComponentInvocationId, ComponentInvocationId] = {}

    def invocation_id(value: object, path: str, *, optional: bool = False) -> ComponentInvocationId | None:
        if value is None and optional:
            return None
        if type(value) is int:
            return ComponentInvocationId(_bounded_index(value, invocation_count, path) + 1)
        anchor = _exact_object(value, {"anchor"}, path)
        if anchor["anchor"] != "invocation" or boundary_invocation_id is None:
            raise CacheArtifactError(f"{path} requires the current cache-boundary invocation.")
        sentinel = ComponentInvocationId(-1)
        external_invocations[sentinel] = boundary_invocation_id
        return sentinel

    fill_values = _exact_list(root["fills"], "artifact.ownership.fills")
    fill_count = len(fill_values)
    external_fills: dict[LogicalFillId, LogicalFillId] = {}
    fill_anchor_sentinels: dict[_WriterPath, LogicalFillId] = {}

    def resolve_fill_id(value: object, path: str) -> LogicalFillId:
        if type(value) is int:
            return LogicalFillId(_bounded_index(value, fill_count, path) + 1)
        anchor = _exact_object(value, {"anchor", "slot"}, path)
        if anchor["anchor"] != "fill":
            raise CacheArtifactError(f"{path}.anchor must be 'fill'.")
        writer_path = _writer_path_from_wire(anchor["slot"], f"{path}.slot")
        try:
            current_id = current_fill_by_path[writer_path]
        except KeyError as err:
            raise CacheArtifactError(f"{path} requires current supplied Slot path {writer_path!r}.") from err
        sentinel = fill_anchor_sentinels.get(writer_path)
        if sentinel is None:
            sentinel = LogicalFillId(-(len(fill_anchor_sentinels) + 1))
            fill_anchor_sentinels[writer_path] = sentinel
            external_fills[sentinel] = current_id
        return sentinel

    region_values = _exact_list(root["regions"], "artifact.ownership.regions")
    region_count = len(region_values)
    external_regions: dict[PhysicalRegionId, PhysicalRegionId] = {}

    def region_id(value: object, path: str, *, optional: bool = False) -> PhysicalRegionId | None:
        if value is None and optional:
            return None
        if type(value) is int:
            return PhysicalRegionId(_bounded_index(value, region_count, path) + 1)
        anchor = _exact_object(value, {"anchor"}, path)
        if (
            anchor["anchor"] != "containing-region"
            or boundary_invocation is None
            or boundary_invocation.physical_parent_region_id is None
        ):
            raise CacheArtifactError(f"{path} requires the current containing physical region.")
        sentinel = PhysicalRegionId(-1)
        external_regions[sentinel] = boundary_invocation.physical_parent_region_id
        return sentinel

    locations: list[SourceLocationRecord] = []
    external_sources: dict[SourceLocationId, SourceLocationId] = {}
    source_anchor_sentinels: dict[_WriterPath, SourceLocationId] = {}
    for index, item in enumerate(location_values):
        path = f"artifact.ownership.locations[{index}]"
        record = _exact_object(
            item,
            {
                "byte_span",
                "column",
                "id",
                "kind",
                "line",
                "mapping_index",
                "mapping_key",
                "order",
                "origin",
                "owner",
                "owner_class",
                "source",
                "span",
                "writer_occurrence",
                "writer_slot",
            },
            path,
        )
        _sequential_id(record["id"], index, f"{path}.id")
        archived_source = _string(record["source"], f"{path}.source")
        archived_byte_span = _span(record["byte_span"], f"{path}.byte_span", len(archived_source.encode()))
        archived_span = _span(record["span"], f"{path}.span", len(archived_source))
        archived_origin = _optional_string(record["origin"], f"{path}.origin")
        archived_line = _positive_int(record["line"], f"{path}.line")
        archived_column = _positive_int(record["column"], f"{path}.column")
        location_writer_path = (
            None
            if record["writer_slot"] is None
            else _writer_path_from_wire(record["writer_slot"], f"{path}.writer_slot")
        )
        writer_occurrence = _optional_nonnegative_int(record["writer_occurrence"], f"{path}.writer_occurrence")
        owner_anchor_path = writer_anchor_path(record["owner"], f"{path}.owner")
        if location_writer_path != owner_anchor_path:
            raise CacheArtifactError(f"{path} writer metadata does not match its owner reference.")
        owner = cast("str", resolve_render_ref(record["owner"], f"{path}.owner", allow_none=False))
        archived_owner_class = _nonempty_string(record["owner_class"], f"{path}.owner_class")
        expected_class = _class_id_for_render(owner, id_by_instance, instances, current_instances)
        if expected_class is None:
            raise CacheArtifactError(f"{path}.owner does not identify an active component instance.")
        if location_writer_path is None and expected_class != archived_owner_class:
            raise CacheArtifactError(f"{path}.owner_class does not match its owner instance.")
        kind = _enum(SourceLocationKind, record["kind"], f"{path}.kind")
        source = archived_source
        byte_span = archived_byte_span
        span = archived_span
        origin = archived_origin
        line = archived_line
        column = archived_column
        mapping_key = _optional_string(record["mapping_key"], f"{path}.mapping_key")
        mapping_index = _optional_nonnegative_int(record["mapping_index"], f"{path}.mapping_index")
        if location_writer_path is not None:
            try:
                fill_location = current_fill_location_by_path[location_writer_path]
            except KeyError as err:
                raise CacheArtifactError(
                    f"{path} requires a current source location for supplied Slot path {location_writer_path!r}."
                ) from err
            source = fill_location.source
            origin = fill_location.origin
            if writer_occurrence is None:
                if kind != fill_location.kind:
                    raise CacheArtifactError(f"{path}.kind does not match the current supplied Slot location.")
                sentinel = source_anchor_sentinels.get(location_writer_path)
                if sentinel is None:
                    sentinel = SourceLocationId(-(len(source_anchor_sentinels) + 1))
                    source_anchor_sentinels[location_writer_path] = sentinel
                    external_sources[sentinel] = fill_location.id
                location_ids_by_index.append(sentinel)
                continue
            snippet = archived_source[archived_span[0] : archived_span[1]]
            if not snippet:
                raise CacheArtifactError(f"{path} has an empty writer-relative source span.")
            starts: list[int] = []
            cursor = fill_location.span[0]
            while True:
                found = source.find(snippet, cursor, fill_location.span[1])
                if found < 0:
                    break
                starts.append(found)
                cursor = found + 1
            if writer_occurrence >= len(starts):
                if not preserve_unmatched_writer_locations:
                    raise CacheArtifactError(
                        f"{path} cannot find occurrence {writer_occurrence} in the current supplied Slot."
                    )
                # A named fragment key deliberately does not include or
                # constrain its body. Another call site may therefore reuse
                # the artifact even when its authored body differs. Keep the
                # archived source span as provenance while the owner IDs and
                # class below still bind to the current lexical writer.
                source = archived_source
                byte_span = archived_byte_span
                span = archived_span
                origin = archived_origin
                line = archived_line
                column = archived_column
            else:
                start = starts[writer_occurrence]
                span = (start, start + len(snippet))
                byte_span = (len(source[:start].encode()), len(source[: span[1]].encode()))
                source_prefix = source[:start]
                line = source_prefix.count("\n") + 1
                newline = source_prefix.rfind("\n")
                column = start + 1 if newline < 0 else start - newline
        local_location_id = SourceLocationId(len(locations) + 1)
        location_ids_by_index.append(local_location_id)
        locations.append(
            SourceLocationRecord(
                id=local_location_id,
                order=_positive_int(record["order"], f"{path}.order"),
                kind=kind,
                owner_render_id=owner,
                owner_class_id=expected_class,
                origin=origin,
                source=source,
                byte_span=byte_span,
                span=span,
                line=line,
                column=column,
                mapping_key=mapping_key,
                mapping_index=mapping_index,
            )
        )

    invocations: list[ComponentInvocationRecord] = []
    for index, item in enumerate(invocation_values):
        path = f"artifact.ownership.invocations[{index}]"
        record = _exact_object(
            item,
            {
                "authored_tag",
                "id",
                "location",
                "morph_key",
                "morph_mode",
                "order",
                "parent_region",
                "client_bindings",
                "selectors",
                "source",
                "source_class",
                "target",
                "target_class",
            },
            path,
        )
        _sequential_id(record["id"], index, f"{path}.id")
        source_path = f"{path}.source"
        source_writer_path = writer_anchor_path(record["source"], source_path)
        source = cast("str", resolve_render_ref(record["source"], source_path, allow_none=False))
        archived_source_class = _nonempty_string(record["source_class"], f"{path}.source_class")
        source_class = _class_id_for_render(source, id_by_instance, instances, current_instances)
        if source_class is None:
            raise CacheArtifactError(f"{path}.source does not identify an active component instance.")
        if source_writer_path is None and source_class != archived_source_class:
            raise CacheArtifactError(f"{path}.source_class does not match its source instance.")
        target = resolve_render_ref(record["target"], f"{path}.target")
        selectors_raw = _exact_list(record["selectors"], f"{path}.selectors")
        selectors = tuple(
            cast("str", resolve_render_ref(value, f"{path}.selectors[{selector_index}]", allow_none=False))
            for selector_index, value in enumerate(selectors_raw)
        )
        invocations.append(
            ComponentInvocationRecord(
                id=ComponentInvocationId(index + 1),
                order=_positive_int(record["order"], f"{path}.order"),
                source_render_id=source,
                source_class_id=source_class,
                source_location_id=cast("SourceLocationId", location_id(record["location"], f"{path}.location")),
                authored_tag=_nonempty_string(record["authored_tag"], f"{path}.authored_tag"),
                target_class_id=_nonempty_string(record["target_class"], f"{path}.target_class"),
                morph_key=_optional_string(record["morph_key"], f"{path}.morph_key"),
                morph_mode=_morph_mode(record["morph_mode"], f"{path}.morph_mode"),
                target_render_id=target,
                physical_parent_region_id=region_id(record["parent_region"], f"{path}.parent_region", optional=True),
                client_bindings=tuple(
                    _client_binding_from_wire(
                        client_binding,
                        path=f"{path}.client_bindings[{client_binding_index}]",
                        location_ids=location_ids_by_index,
                    )
                    for client_binding_index, client_binding in enumerate(
                        _exact_list(record["client_bindings"], f"{path}.client_bindings")
                    )
                ),
                selector_render_ids=selectors,
            )
        )

    logical_instances: list[LogicalInstanceRecord] = []
    for index, (item, instance) in enumerate(zip(instance_values[1:], instances[1:], strict=True), start=1):
        path = f"artifact.ownership.instances[{index}]"
        record = cast("dict[str, object]", item)
        logical_instances.append(
            LogicalInstanceRecord(
                order=_positive_int(record["order"], f"{path}.order"),
                render_id=id_by_instance[index],
                class_id=instance.class_id,
                class_name=instance.class_name,
                invocation_id=invocation_id(record["invocation"], f"{path}.invocation", optional=True),
                logical_parent_render_id=cast(
                    "str", resolve_render_ref(record["parent"], f"{path}.parent", allow_none=False)
                ),
                transparent=instance.transparent,
            )
        )

    init_records: list[InitAncestryRecord] = []
    for index, item in enumerate(_exact_list(root["init"], "artifact.ownership.init")):
        path = f"artifact.ownership.init[{index}]"
        record = _exact_object(item, {"child", "invocation", "order", "parent"}, path)
        init_records.append(
            InitAncestryRecord(
                order=_positive_int(record["order"], f"{path}.order"),
                invocation_id=cast(
                    "ComponentInvocationId",
                    invocation_id(record["invocation"], f"{path}.invocation"),
                ),
                parent_render_id=cast("str", resolve_render_ref(record["parent"], f"{path}.parent", allow_none=False)),
                child_render_id=cast("str", resolve_render_ref(record["child"], f"{path}.child", allow_none=False)),
            )
        )

    fills: list[LogicalFillRecord] = []
    for index, item in enumerate(fill_values):
        path = f"artifact.ownership.fills[{index}]"
        record = _exact_object(
            item,
            {
                "fallback_location",
                "id",
                "kind",
                "lexical_class",
                "lexical_owner",
                "order",
                "receiver",
                "receiver_class",
                "slot",
                "source_invocation",
                "source_location",
                "source_policy",
            },
            path,
        )
        _sequential_id(record["id"], index, f"{path}.id")
        lexical_owner = resolve_render_ref(record["lexical_owner"], f"{path}.lexical_owner")
        lexical_class = _optional_nonempty_string(record["lexical_class"], f"{path}.lexical_class")
        if writer_anchor_path(record["lexical_owner"], f"{path}.lexical_owner") is not None:
            if lexical_owner is None:
                raise CacheArtifactError(f"{path}.lexical_owner is required for a writer anchor.")
            lexical_class = _class_id_for_render(
                lexical_owner,
                id_by_instance,
                instances,
                current_instances,
            )
        fill_receiver = resolve_render_ref(record["receiver"], f"{path}.receiver")
        receiver_class = _optional_nonempty_string(record["receiver_class"], f"{path}.receiver_class")
        if writer_anchor_path(record["receiver"], f"{path}.receiver") is not None:
            if fill_receiver is None:
                raise CacheArtifactError(f"{path}.receiver is required for a writer anchor.")
            receiver_class = _class_id_for_render(fill_receiver, id_by_instance, instances, current_instances)
        fills.append(
            LogicalFillRecord(
                id=LogicalFillId(index + 1),
                order=_positive_int(record["order"], f"{path}.order"),
                kind=_enum(LogicalFillKind, record["kind"], f"{path}.kind"),
                slot_name=_nonempty_string(record["slot"], f"{path}.slot"),
                source_policy=_enum(SourcePolicy, record["source_policy"], f"{path}.source_policy"),
                lexical_owner_render_id=lexical_owner,
                lexical_owner_class_id=lexical_class,
                source_location_id=location_id(record["source_location"], f"{path}.source_location", optional=True),
                source_invocation_id=invocation_id(
                    record["source_invocation"], f"{path}.source_invocation", optional=True
                ),
                receiver_render_id=fill_receiver,
                receiver_class_id=receiver_class,
                fallback_slot_site_location_id=location_id(
                    record["fallback_location"], f"{path}.fallback_location", optional=True
                ),
            )
        )

    regions: list[PhysicalRegionRequestRecord] = []
    for index, item in enumerate(region_values):
        path = f"artifact.ownership.regions[{index}]"
        record = _exact_object(
            item,
            {
                "containing",
                "fill",
                "id",
                "lexical_owner",
                "order",
                "receiver",
                "result_owner",
                "slot_location",
                "source_location",
                "transition_from",
            },
            path,
        )
        _sequential_id(record["id"], index, f"{path}.id")
        regions.append(
            PhysicalRegionRequestRecord(
                id=PhysicalRegionId(index + 1),
                order=_positive_int(record["order"], f"{path}.order"),
                logical_fill_id=resolve_fill_id(record["fill"], f"{path}.fill"),
                receiver_render_id=resolve_render_ref(record["receiver"], f"{path}.receiver"),
                slot_site_location_id=location_id(record["slot_location"], f"{path}.slot_location", optional=True),
                lexical_owner_render_id=resolve_render_ref(record["lexical_owner"], f"{path}.lexical_owner"),
                source_location_id=location_id(record["source_location"], f"{path}.source_location", optional=True),
                containing_region_id=region_id(record["containing"], f"{path}.containing", optional=True),
                transition_from_render_id=resolve_render_ref(record["transition_from"], f"{path}.transition_from"),
                result_owner_render_id=resolve_render_ref(record["result_owner"], f"{path}.result_owner"),
                state=RegionState.CAPTURED,
            )
        )

    queues: list[RenderQueueRecord] = []
    for index, item in enumerate(_exact_list(root["queue"], "artifact.ownership.queue")):
        path = f"artifact.ownership.queue[{index}]"
        record = _exact_object(
            item,
            {"enqueued", "invocation", "rendered", "settled", "state", "target"},
            path,
        )
        state = _enum(QueueState, record["state"], f"{path}.state")
        if state != QueueState.SETTLED:
            raise CacheArtifactError(f"{path}.state must be 'settled'.")
        queues.append(
            RenderQueueRecord(
                invocation_id=cast(
                    "ComponentInvocationId",
                    invocation_id(record["invocation"], f"{path}.invocation"),
                ),
                enqueued_order=_positive_int(record["enqueued"], f"{path}.enqueued"),
                target_render_id=resolve_render_ref(record["target"], f"{path}.target"),
                rendered_order=_optional_positive_int(record["rendered"], f"{path}.rendered"),
                settled_order=_optional_positive_int(record["settled"], f"{path}.settled"),
                state=state,
            )
        )

    return (
        OwnershipSnapshot(
            source_locations=tuple(locations),
            component_invocations=tuple(invocations),
            logical_instances=tuple(logical_instances),
            init_ancestry=tuple(init_records),
            logical_fills=tuple(fills),
            physical_regions=tuple(regions),
            render_queue=tuple(queues),
        ),
        external_sources,
        external_invocations,
        external_fills,
        external_regions,
    )


def _mint_render_id(citry: Any) -> str:
    generated = citry.id_generator() if citry.id_generator is not None else gen_render_id()
    return validate_render_id(generated)


def _class_id_for_render(
    render_id: str,
    id_by_instance: list[str],
    instances: tuple[_ArtifactInstance, ...],
    current_instances: dict[str, LogicalInstanceRecord],
) -> str | None:
    try:
        index = id_by_instance.index(render_id)
    except ValueError:
        current = current_instances.get(render_id)
        return None if current is None else current.class_id
    return instances[index].class_id


def _client_binding_from_wire(
    value: object,
    *,
    path: str,
    location_ids: list[SourceLocationId],
) -> ComponentTagClientBindingRecord:
    record = _exact_object(value, {"key", "location", "payload", "source"}, path)
    payload_path = f"{path}.payload"
    payload = _exact_object(record["payload"], None, payload_path)
    payload_type = payload.get("type")
    parsed_payload: ComponentTagClientBindingPayload
    if payload_type == "props":
        _require_keys(payload, {"expression", "type"}, payload_path)
        parsed_payload = PropsClientBindingPayload(
            type="props",
            expression=_string(payload["expression"], f"{payload_path}.expression"),
        )
    elif payload_type == "alpine-handler":
        _require_keys(payload, {"expression", "type"}, payload_path)
        parsed_payload = AlpineHandlerClientBindingPayload(
            type="alpine-handler",
            expression=_string(payload["expression"], f"{payload_path}.expression"),
        )
    elif payload_type == "citry-dom-event":
        _require_keys(
            payload,
            {
                "args",
                "class_id",
                "debounce",
                "event",
                "handler",
                "key",
                "once",
                "prevent",
                "self",
                "stop",
                "throttle",
                "type",
            },
            payload_path,
        )
        parsed_payload = CitryDomEventClientBindingPayload(
            type="citry-dom-event",
            class_id=_nonempty_string(payload["class_id"], f"{payload_path}.class_id"),
            event=_nonempty_string(payload["event"], f"{payload_path}.event"),
            handler=_nonempty_string(payload["handler"], f"{payload_path}.handler"),
            args=_optional_string(payload["args"], f"{payload_path}.args"),
            prevent=_bool(payload["prevent"], f"{payload_path}.prevent"),
            stop=_bool(payload["stop"], f"{payload_path}.stop"),
            self_=_bool(payload["self"], f"{payload_path}.self"),
            once=_bool(payload["once"], f"{payload_path}.once"),
            key=_optional_string(payload["key"], f"{payload_path}.key"),
            debounce=_optional_nonnegative_int(payload["debounce"], f"{payload_path}.debounce"),
            throttle=_optional_nonnegative_int(payload["throttle"], f"{payload_path}.throttle"),
        )
    elif payload_type == "citry-poll":
        _require_keys(payload, {"args", "class_id", "handler", "interval", "type"}, payload_path)
        parsed_payload = CitryPollClientBindingPayload(
            type="citry-poll",
            class_id=_nonempty_string(payload["class_id"], f"{payload_path}.class_id"),
            handler=_nonempty_string(payload["handler"], f"{payload_path}.handler"),
            args=_optional_string(payload["args"], f"{payload_path}.args"),
            interval=_positive_int(payload["interval"], f"{payload_path}.interval"),
        )
    else:
        raise CacheArtifactError(f"{payload_path}.type is unknown.")
    try:
        source = ComponentTagClientBindingSource(_nonempty_string(record["source"], f"{path}.source"))
    except ValueError as err:
        raise CacheArtifactError(f"{path}.source is unknown.") from err
    return ComponentTagClientBindingRecord(
        key=_nonempty_string(record["key"], f"{path}.key"),
        payload=parsed_payload,
        source=source,
        source_location_id=location_ids[_bounded_index(record["location"], len(location_ids), f"{path}.location")],
    )


def _exact_object(
    value: object,
    fields: set[str] | None,
    path: str,
) -> dict[str, object]:
    if type(value) is not dict:
        raise CacheArtifactError(f"{path} must be a JSON object.")
    result = cast("dict[str, object]", value)
    if fields is not None:
        _require_keys(result, fields, path)
    return result


def _require_keys(value: dict[str, object], fields: set[str], path: str) -> None:
    if set(value) != fields:
        raise CacheArtifactError(f"{path} has an invalid field set.")


def _exact_list(value: object, path: str) -> list[object]:
    if type(value) is not list:
        raise CacheArtifactError(f"{path} must be a JSON array.")
    return cast("list[object]", value)


def _string(value: object, path: str) -> str:
    if type(value) is not str:
        raise CacheArtifactError(f"{path} must be an exact string.")
    return value


def _nonempty_string(value: object, path: str) -> str:
    result = _string(value, path)
    if not result:
        raise CacheArtifactError(f"{path} must not be empty.")
    return result


def _optional_string(value: object, path: str) -> str | None:
    return None if value is None else _string(value, path)


def _morph_mode(value: object, path: str) -> MorphMode | None:
    if value is None:
        return None
    mode = _string(value, path)
    if mode == "ignore":
        return "ignore"
    raise CacheArtifactError(f"{path} contains unknown value {mode!r}.")


def _optional_nonempty_string(value: object, path: str) -> str | None:
    return None if value is None else _nonempty_string(value, path)


def _bool(value: object, path: str) -> bool:
    if type(value) is not bool:
        raise CacheArtifactError(f"{path} must be a bool.")
    return value


def _positive_int(value: object, path: str) -> int:
    if type(value) is not int or value <= 0:
        raise CacheArtifactError(f"{path} must be an exact positive integer.")
    return value


def _optional_positive_int(value: object, path: str) -> int | None:
    return None if value is None else _positive_int(value, path)


def _optional_nonnegative_int(value: object, path: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise CacheArtifactError(f"{path} must be an exact non-negative integer or null.")
    return value


def _bounded_index(value: object, count: int, path: str) -> int:
    if type(value) is not int or not 0 <= value < count:
        raise CacheArtifactError(f"{path} must refer to an existing local record.")
    return value


def _sequential_id(value: object, expected: int, path: str) -> None:
    if type(value) is not int or value != expected:
        raise CacheArtifactError(f"{path} must equal its zero-based record position {expected}.")


def _span(value: object, path: str, maximum: int) -> tuple[int, int]:
    items = _exact_list(value, path)
    if len(items) != 2 or any(type(item) is not int for item in items):
        raise CacheArtifactError(f"{path} must contain two exact integers.")
    start, end = cast("list[int]", items)
    if not 0 <= start <= end <= maximum:
        raise CacheArtifactError(f"{path} falls outside its source text.")
    return start, end


def _enum(enum_type: Any, value: object, path: str) -> Any:
    if type(value) is not str:
        raise CacheArtifactError(f"{path} must be an exact string enum value.")
    try:
        return enum_type(value)
    except ValueError as err:
        raise CacheArtifactError(f"{path} contains unknown value {value!r}.") from err


def _build_replayed_tree(
    artifact: CachedRenderArtifact,
    *,
    root_frame: int,
    id_by_instance: list[str],
    boundary: Component,
    boundary_context: CitryContext,
    graph: OwnershipGraph,
    region_ids: dict[PhysicalRegionId, PhysicalRegionId],
    staged_frame_markers: dict[int, tuple[str, ...]],
) -> CitryRender:
    built: dict[int, CitryRender] = {}
    pending: list[tuple[int, bool]] = [(root_frame, False)]
    while pending:
        frame_index, ready = pending.pop()
        if ready:
            frame = artifact.frames[frame_index]
            if frame_index == root_frame:
                frame_context = boundary_context
            else:
                frame_context = CitryContext(
                    component=None,
                    ownership=graph,
                    sandboxed=boundary.citry.settings.sandbox_expressions,
                )

            def build_part(part: ArtifactPart) -> Any:
                if type(part) is ArtifactTextPart:
                    return part.text
                if type(part) is ArtifactFramePart:
                    return built[part.frame]
                if type(part) is ArtifactPlaceholderPart:
                    return Placeholder(part.key)
                if type(part) is ArtifactRegionPart:
                    local_region_id = PhysicalRegionId(part.region + 1)
                    try:
                        fresh_region_id = region_ids[local_region_id]
                    except KeyError as err:
                        raise CacheArtifactError(
                            f"Artifact frame refers to missing ownership region {part.region}."
                        ) from err
                    nested = build_part(part.part)
                    wrapper = (
                        PhysicalRegionRender(graph, fresh_region_id, nested)
                        if isinstance(nested, CitryRender)
                        else PhysicalRegionPart(graph, fresh_region_id, nested)
                    )
                    graph.register_replayed_region_result(fresh_region_id, wrapper)
                    return wrapper
                raise CacheArtifactError(f"Unsupported replay part {type(part).__name__}.")

            parts = [build_part(part) for part in frame.parts]
            instance = frame.instance
            if instance is None:
                render_frame = RenderFrame(
                    render_id=None,
                    class_id=None,
                    class_name=None,
                    is_component_root=False,
                    root_markers=(),
                )
            else:
                markers = tuple(dict.fromkeys((*frame.root_markers, *staged_frame_markers.get(instance, ()))))
                if frame_index == root_frame:
                    markers = tuple(dict.fromkeys((*boundary_context._get_root_markers(), *markers)))
                render_frame = RenderFrame(
                    render_id=id_by_instance[instance],
                    class_id=frame.class_id,
                    class_name=frame.class_name,
                    is_component_root=frame.is_component_root,
                    root_markers=markers,
                )
            built[frame_index] = CitryRender(parts=parts, context=frame_context, frame=render_frame)
            continue
        pending.append((frame_index, True))
        frame = artifact.frames[frame_index]
        child_frames = _child_frame_indexes(frame.parts)
        pending.extend((child, False) for child in reversed(child_frames))
    return built[root_frame]


def _child_frame_indexes(parts: tuple[ArtifactPart, ...]) -> list[int]:
    children: list[int] = []
    pending = list(reversed(parts))
    while pending:
        part = pending.pop()
        if type(part) is ArtifactFramePart:
            children.append(part.frame)
        elif type(part) is ArtifactRegionPart:
            pending.append(part.part)
    return children


__all__: list[str] = []
