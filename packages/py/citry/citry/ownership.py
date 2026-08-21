"""
Typed server ownership captured before component output is flattened.

This module is internal. A render owns one :class:`OwnershipGraph`; its
immutable snapshot records executed nested component tags, component-tag client
bindings,
logical instances, fills, physical region requests, and initialization order.
Serialization does not consume these records until A2.
"""

from __future__ import annotations

from bisect import bisect_right
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, NewType, TypeAlias, cast
from weakref import WeakKeyDictionary

from citry.client_directives import ComponentTagClientBindingKind, ComponentTagClientBindingSource

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping
    from typing import TypeVar

    from citry.citry_context import CitryContext
    from citry.citry_element import CitryElement
    from citry.citry_render import RenderPart
    from citry.component import Component
    from citry.slots import Slot

    TResult = TypeVar("TResult")


SourceLocationId = NewType("SourceLocationId", int)
ComponentInvocationId = NewType("ComponentInvocationId", int)
LogicalFillId = NewType("LogicalFillId", int)
PhysicalRegionId = NewType("PhysicalRegionId", int)
MorphMode: TypeAlias = Literal["ignore"]


class SourceLocationKind(str, Enum):
    """The operation whose compiled runtime source executes at a location."""

    COMPONENT_CALL = "component-call"
    COMPONENT_TAG_CLIENT_BINDING = "component-tag-client-binding"
    IMPLICIT_FILL = "implicit-fill"
    NAMED_FILL = "named-fill"
    FALLBACK_FILL = "fallback-fill"
    SLOT_OUTLET = "slot-outlet"


class LogicalFillKind(str, Enum):
    """How one logical slot supply was created."""

    IMPLICIT = "implicit"
    NAMED = "named"
    FALLBACK = "fallback"
    PYTHON = "python"
    TYPED_DEFAULT = "typed-default"


class SourcePolicy(str, Enum):
    """Whether a fill has a usable template-authored client source."""

    TEMPLATE = "template"
    PYTHON = "python-detached"
    TYPED_DEFAULT = "typed-default-detached"


class QueueState(str, Enum):
    """How far one deferred component invocation progressed."""

    ENQUEUED = "enqueued"
    RENDERED = "rendered"
    SETTLED = "settled"
    FAILED = "failed"
    RETIRED = "retired"


class OwnershipState(str, Enum):
    """Whether an ownership record still belongs to selected output."""

    ACTIVE = "active"
    RETIRED = "retired"


class RegionState(str, Enum):
    """Whether a requested physical placement remains usable."""

    CAPTURED = "captured"
    FAILED = "failed"
    RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class _SourceSite:
    """Immutable class/template metadata shared by executed occurrences."""

    origin: str | None
    source: str
    byte_span: tuple[int, int]
    span: tuple[int, int]
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class SourceLocationRecord:
    """One execution of one post-template-hook runtime source span."""

    id: SourceLocationId
    order: int
    kind: SourceLocationKind
    owner_render_id: str
    owner_class_id: str
    _site: _SourceSite
    mapping_key: str | None = None
    mapping_index: int | None = None

    @classmethod
    def _from_values(
        cls,
        *,
        location_id: SourceLocationId,
        order: int,
        kind: SourceLocationKind,
        owner_render_id: str,
        owner_class_id: str,
        origin: str | None,
        source: str,
        byte_span: tuple[int, int],
        span: tuple[int, int],
        line: int,
        column: int,
        mapping_key: str | None = None,
        mapping_index: int | None = None,
    ) -> SourceLocationRecord:
        """Build a detached record, primarily for validated cache replay."""
        return cls(
            id=location_id,
            order=order,
            kind=kind,
            owner_render_id=owner_render_id,
            owner_class_id=owner_class_id,
            _site=_SourceSite(
                origin=origin,
                source=source,
                byte_span=byte_span,
                span=span,
                line=line,
                column=column,
            ),
            mapping_key=mapping_key,
            mapping_index=mapping_index,
        )

    @property
    def origin(self) -> str | None:
        """Source origin shared by every execution of this site."""
        return self._site.origin

    @property
    def source(self) -> str:
        """Compiled runtime source shared by every execution of this site."""
        return self._site.source

    @property
    def byte_span(self) -> tuple[int, int]:
        """UTF-8 byte offsets of the executed site."""
        return self._site.byte_span

    @property
    def span(self) -> tuple[int, int]:
        """Python character offsets of the executed site."""
        return self._site.span

    @property
    def line(self) -> int:
        """One-based source line of the executed site."""
        return self._site.line

    @property
    def column(self) -> int:
        """One-based source column of the executed site."""
        return self._site.column

    @property
    def snippet(self) -> str:
        """The exact text covered by ``span`` in the compiled source."""
        return self.source[self.span[0] : self.span[1]]


@dataclass(frozen=True, slots=True)
class PropsClientBindingPayload:
    """A ``$c-props`` Alpine expression supplied to a child instance."""

    type: Literal["props"]
    expression: str


@dataclass(frozen=True, slots=True)
class AlpineHandlerClientBindingPayload:
    """An Alpine event-handler expression authored on a child tag."""

    type: Literal["alpine-handler"]
    expression: str


@dataclass(frozen=True, slots=True)
class CitryDomEventClientBindingPayload:
    """A compiled Citry DOM-event binding, owned by the source parent."""

    type: Literal["citry-dom-event"]
    class_id: str
    event: str
    handler: str
    args: str | None
    prevent: bool
    stop: bool
    self_: bool
    once: bool
    key: str | None
    debounce: int | None
    throttle: int | None


@dataclass(frozen=True, slots=True)
class CitryPollClientBindingPayload:
    """A compiled Citry polling binding, owned by the source parent."""

    type: Literal["citry-poll"]
    class_id: str
    handler: str
    args: str | None
    interval: int


ComponentTagClientBindingPayload: TypeAlias = (
    "PropsClientBindingPayload | "
    "AlpineHandlerClientBindingPayload | "
    "CitryDomEventClientBindingPayload | "
    "CitryPollClientBindingPayload"
)


@dataclass(frozen=True, slots=True)
class ComponentTagClientBindingRecord:
    """
    One winning browser-side binding resolved from a nested component tag.

    For example, ``<c-card $c-props="{ theme }" @click="select()" />``
    contributes two records. The parent owns each expression while the child
    supplies the component boundary where the browser applies it.
    """

    key: str
    payload: ComponentTagClientBindingPayload
    source: ComponentTagClientBindingSource
    source_location_id: SourceLocationId

    @property
    def kind(self) -> ComponentTagClientBindingKind:
        """The stable A1 channel classification derived from the payload."""
        if isinstance(self.payload, PropsClientBindingPayload):
            return ComponentTagClientBindingKind.PROPS
        if isinstance(self.payload, AlpineHandlerClientBindingPayload):
            return ComponentTagClientBindingKind.ALPINE_HANDLER
        return ComponentTagClientBindingKind.CITRY_HANDLER


@dataclass(frozen=True, slots=True)
class ComponentInvocationRecord:
    """One executed component tag, eventually bound to its actual target."""

    id: ComponentInvocationId
    order: int
    source_render_id: str
    source_class_id: str
    source_location_id: SourceLocationId
    authored_tag: str
    target_class_id: str
    morph_key: str | None
    morph_mode: MorphMode | None
    target_render_id: str | None
    physical_parent_region_id: PhysicalRegionId | None
    client_bindings: tuple[ComponentTagClientBindingRecord, ...]
    selector_render_ids: tuple[str, ...] = ()
    state: OwnershipState = OwnershipState.ACTIVE

    def _bind_selector(self, render_id: str) -> ComponentInvocationRecord:
        return ComponentInvocationRecord(
            self.id,
            self.order,
            self.source_render_id,
            self.source_class_id,
            self.source_location_id,
            self.authored_tag,
            self.target_class_id,
            self.morph_key,
            self.morph_mode,
            self.target_render_id,
            self.physical_parent_region_id,
            self.client_bindings,
            (*self.selector_render_ids, render_id),
            self.state,
        )

    def _bind_target(self, class_id: str, render_id: str) -> ComponentInvocationRecord:
        return ComponentInvocationRecord(
            self.id,
            self.order,
            self.source_render_id,
            self.source_class_id,
            self.source_location_id,
            self.authored_tag,
            class_id,
            self.morph_key,
            self.morph_mode,
            render_id,
            self.physical_parent_region_id,
            self.client_bindings,
            self.selector_render_ids,
            self.state,
        )

    def _with_state(self, state: OwnershipState) -> ComponentInvocationRecord:
        return ComponentInvocationRecord(
            self.id,
            self.order,
            self.source_render_id,
            self.source_class_id,
            self.source_location_id,
            self.authored_tag,
            self.target_class_id,
            self.morph_key,
            self.morph_mode,
            self.target_render_id,
            self.physical_parent_region_id,
            self.client_bindings,
            self.selector_render_ids,
            state,
        )


@dataclass(frozen=True, slots=True)
class LogicalInstanceRecord:
    """One server-rendered component instance in the ownership graph."""

    order: int
    render_id: str
    class_id: str
    class_name: str
    invocation_id: ComponentInvocationId | None
    logical_parent_render_id: str | None
    transparent: bool
    state: OwnershipState = OwnershipState.ACTIVE

    def _with_state(self, state: OwnershipState) -> LogicalInstanceRecord:
        return LogicalInstanceRecord(
            self.order,
            self.render_id,
            self.class_id,
            self.class_name,
            self.invocation_id,
            self.logical_parent_render_id,
            self.transparent,
            state,
        )


@dataclass(frozen=True, slots=True)
class InitAncestryRecord:
    """One explicit parent-before-child initialization dependency."""

    order: int
    invocation_id: ComponentInvocationId
    parent_render_id: str
    child_render_id: str
    state: OwnershipState = OwnershipState.ACTIVE

    def _with_state(self, state: OwnershipState) -> InitAncestryRecord:
        return InitAncestryRecord(
            self.order,
            self.invocation_id,
            self.parent_render_id,
            self.child_render_id,
            state,
        )


@dataclass(frozen=True, slots=True)
class LogicalFillRecord:
    """One supplied fill or receiver fallback, independent of outlet count."""

    id: LogicalFillId
    order: int
    kind: LogicalFillKind
    slot_name: str
    source_policy: SourcePolicy
    lexical_owner_render_id: str | None
    lexical_owner_class_id: str | None
    source_location_id: SourceLocationId | None
    source_invocation_id: ComponentInvocationId | None
    receiver_render_id: str | None
    receiver_class_id: str | None
    fallback_slot_site_location_id: SourceLocationId | None = None
    state: OwnershipState = OwnershipState.ACTIVE

    def _with_source_invocation(self, invocation_id: ComponentInvocationId) -> LogicalFillRecord:
        return LogicalFillRecord(
            self.id,
            self.order,
            self.kind,
            self.slot_name,
            self.source_policy,
            self.lexical_owner_render_id,
            self.lexical_owner_class_id,
            self.source_location_id,
            invocation_id,
            self.receiver_render_id,
            self.receiver_class_id,
            self.fallback_slot_site_location_id,
            self.state,
        )

    def _with_receiver(
        self,
        render_id: str,
        class_id: str | None,
        *,
        state: OwnershipState | None = None,
    ) -> LogicalFillRecord:
        return LogicalFillRecord(
            self.id,
            self.order,
            self.kind,
            self.slot_name,
            self.source_policy,
            self.lexical_owner_render_id,
            self.lexical_owner_class_id,
            self.source_location_id,
            self.source_invocation_id,
            render_id,
            class_id,
            self.fallback_slot_site_location_id,
            self.state if state is None else state,
        )

    def _with_state(self, state: OwnershipState) -> LogicalFillRecord:
        return LogicalFillRecord(
            self.id,
            self.order,
            self.kind,
            self.slot_name,
            self.source_policy,
            self.lexical_owner_render_id,
            self.lexical_owner_class_id,
            self.source_location_id,
            self.source_invocation_id,
            self.receiver_render_id,
            self.receiver_class_id,
            self.fallback_slot_site_location_id,
            state,
        )


@dataclass(frozen=True, slots=True)
class PhysicalRegionRequestRecord:
    """One actual occurrence of a logical fill, before A2 chooses DOM caps."""

    id: PhysicalRegionId
    order: int
    logical_fill_id: LogicalFillId
    receiver_render_id: str | None
    slot_site_location_id: SourceLocationId | None
    lexical_owner_render_id: str | None
    source_location_id: SourceLocationId | None
    containing_region_id: PhysicalRegionId | None
    transition_from_render_id: str | None
    result_owner_render_id: str | None
    state: RegionState

    def _with_result_owner(self, render_id: str | None) -> PhysicalRegionRequestRecord:
        return PhysicalRegionRequestRecord(
            self.id,
            self.order,
            self.logical_fill_id,
            self.receiver_render_id,
            self.slot_site_location_id,
            self.lexical_owner_render_id,
            self.source_location_id,
            self.containing_region_id,
            self.transition_from_render_id,
            render_id,
            self.state,
        )

    def _with_receiver(self, render_id: str) -> PhysicalRegionRequestRecord:
        return PhysicalRegionRequestRecord(
            self.id,
            self.order,
            self.logical_fill_id,
            render_id,
            self.slot_site_location_id,
            self.lexical_owner_render_id,
            self.source_location_id,
            self.containing_region_id,
            render_id if self.containing_region_id is None else self.transition_from_render_id,
            self.result_owner_render_id,
            self.state,
        )

    def _with_state(self, state: RegionState) -> PhysicalRegionRequestRecord:
        return PhysicalRegionRequestRecord(
            self.id,
            self.order,
            self.logical_fill_id,
            self.receiver_render_id,
            self.slot_site_location_id,
            self.lexical_owner_render_id,
            self.source_location_id,
            self.containing_region_id,
            self.transition_from_render_id,
            self.result_owner_render_id,
            state,
        )


@dataclass(frozen=True, slots=True)
class RenderQueueRecord:
    """One invocation's passage through deferred component rendering."""

    invocation_id: ComponentInvocationId
    enqueued_order: int
    target_render_id: str | None
    rendered_order: int | None
    settled_order: int | None
    state: QueueState

    def _rendered(self, render_id: str, order: int) -> RenderQueueRecord:
        return RenderQueueRecord(
            self.invocation_id,
            self.enqueued_order,
            render_id,
            order,
            self.settled_order,
            QueueState.RENDERED,
        )

    def _settled(self, order: int, state: QueueState) -> RenderQueueRecord:
        return RenderQueueRecord(
            self.invocation_id,
            self.enqueued_order,
            self.target_render_id,
            self.rendered_order,
            order,
            state,
        )


@dataclass(frozen=True, slots=True)
class OwnershipSnapshot:
    """Immutable deterministic view of one render's captured ownership."""

    source_locations: tuple[SourceLocationRecord, ...]
    component_invocations: tuple[ComponentInvocationRecord, ...]
    logical_instances: tuple[LogicalInstanceRecord, ...]
    init_ancestry: tuple[InitAncestryRecord, ...]
    logical_fills: tuple[LogicalFillRecord, ...]
    physical_regions: tuple[PhysicalRegionRequestRecord, ...]
    render_queue: tuple[RenderQueueRecord, ...]


@dataclass(frozen=True, slots=True)
class ReplayedInstanceRecord:
    """One validated descendant instance ready to append during cache replay."""

    render_id: str
    class_id: str
    class_name: str
    logical_parent_render_id: str | None
    transparent: bool


@dataclass(slots=True)
class _ReplayMutationSnapshot:
    """Complete mutable graph state needed to roll back a replay apply."""

    counters: tuple[int, int, int, int, int]
    source_locations: list[SourceLocationRecord]
    component_invocations: list[ComponentInvocationRecord]
    logical_instances: list[LogicalInstanceRecord]
    init_ancestry: list[InitAncestryRecord]
    logical_fills: list[LogicalFillRecord]
    physical_regions: list[PhysicalRegionRequestRecord]
    render_queue: list[RenderQueueRecord]
    invocation_index: dict[ComponentInvocationId, int]
    instance_invocation: dict[str, ComponentInvocationId]
    fill_index: dict[LogicalFillId, int]
    region_index: dict[PhysicalRegionId, int]
    region_results: dict[PhysicalRegionId, object]
    queue_index: dict[ComponentInvocationId, int]
    template_fill_by_slot_object: dict[Slot, LogicalFillId]
    receiver_fill: dict[tuple[str, str], LogicalFillId]


@dataclass(frozen=True, slots=True)
class _SlotSite:
    graph: OwnershipGraph
    receiver_render_id: str
    source_location_id: SourceLocationId


@dataclass(frozen=True, slots=True)
class _SelectedSupply:
    graph: OwnershipGraph
    slot: Slot
    logical_fill_id: LogicalFillId


_CURRENT_GRAPH: ContextVar[OwnershipGraph | None] = ContextVar("citry_ownership_graph", default=None)
_ACTIVE_REGION: ContextVar[tuple[OwnershipGraph, PhysicalRegionId] | None] = ContextVar(
    "citry_ownership_region",
    default=None,
)
_SLOT_SITE: ContextVar[_SlotSite | None] = ContextVar("citry_ownership_slot_site", default=None)
_SELECTED_SUPPLY: ContextVar[_SelectedSupply | None] = ContextVar("citry_ownership_supply", default=None)


class OwnershipGraph:
    """Mutable capture collector whose public result is an immutable snapshot."""

    def __init__(self) -> None:
        self._order = 0
        self._source_id = 0
        self._invocation_id = 0
        self._fill_id = 0
        self._region_id = 0

        self._source_locations: list[SourceLocationRecord] = []
        self._component_invocations: list[ComponentInvocationRecord] = []
        self._logical_instances: list[LogicalInstanceRecord] = []
        self._init_ancestry: list[InitAncestryRecord] = []
        self._logical_fills: list[LogicalFillRecord] = []
        self._physical_regions: list[PhysicalRegionRequestRecord] = []
        self._render_queue: list[RenderQueueRecord] = []

        self._invocation_index: dict[ComponentInvocationId, int] = {}
        self._instance_invocation: dict[str, ComponentInvocationId] = {}
        self._fill_index: dict[LogicalFillId, int] = {}
        self._region_index: dict[PhysicalRegionId, int] = {}
        # Region wrappers must remain live through the root component's final
        # selection hooks: a hook may return a nested render after its outer
        # wrapper left the selected tree. The root render clears this transient
        # index before returning, breaking graph/result/context cycles.
        self._region_results: dict[PhysicalRegionId, object] = {}
        self._queue_index: dict[ComponentInvocationId, int] = {}

        # Output replacement repeatedly follows the same graph relations.
        # Build these indexes only when replacement occurs so the ordinary
        # append-only capture path stays cheap.
        self._logical_parent_by_render_id: dict[str, str] = {}
        self._invocation_ids_by_source: dict[str, list[ComponentInvocationId]] = {}
        self._invocation_ids_by_target: dict[str, list[ComponentInvocationId]] = {}
        self._invocation_ids_by_region: dict[PhysicalRegionId, list[ComponentInvocationId]] = {}
        self._init_parents_by_child: dict[str, list[str]] = {}
        self._region_ids_by_receiver: dict[str, list[PhysicalRegionId]] = {}
        self._region_ids_by_containing: dict[PhysicalRegionId, list[PhysicalRegionId]] = {}
        self._region_ids_by_fill: dict[LogicalFillId, list[PhysicalRegionId]] = {}
        self._relation_indexes_current = False

        # Weak object keys preserve exact Slot identity without extending a
        # template closure's lifetime through the ownership graph. A Slot can
        # be attached more than once, so its receiver-specific supply is kept
        # in the second mapping instead.
        self._template_fill_by_slot_object: WeakKeyDictionary[Slot, LogicalFillId] = WeakKeyDictionary()
        self._receiver_fill: dict[tuple[str, str], LogicalFillId] = {}
        # Source spans are class/template facts. A large render executes the
        # same compiled node hundreds of times with different component IDs;
        # cache the UTF-8-to-Python span conversion while still emitting one
        # owner-specific record per occurrence.
        self._source_site_cache: dict[tuple[str, tuple[int, int], str | None], _SourceSite] = {}

    def _next_order(self) -> int:
        self._order += 1
        return self._order

    @staticmethod
    def _ordered_indexes_between(records: list[Any], after: int, through: int) -> range:
        """Return the capture-list indexes in one exclusive/inclusive order segment."""
        start = bisect_right(records, after, key=lambda record: record.order)
        stop = bisect_right(records, through, key=lambda record: record.order)
        return range(start, stop)

    def _rebuild_relation_indexes(self) -> None:
        """Index relations used to retire output replaced by a render hook."""
        self._logical_parent_by_render_id = {}
        self._invocation_ids_by_source = {}
        self._invocation_ids_by_target = {}
        self._invocation_ids_by_region = {}
        self._init_parents_by_child = {}
        self._region_ids_by_receiver = {}
        self._region_ids_by_containing = {}
        self._region_ids_by_fill = {}
        for invocation in self._component_invocations:
            self._invocation_ids_by_source.setdefault(invocation.source_render_id, []).append(invocation.id)
            if invocation.target_render_id is not None:
                self._invocation_ids_by_target.setdefault(invocation.target_render_id, []).append(invocation.id)
            if invocation.physical_parent_region_id is not None:
                self._invocation_ids_by_region.setdefault(invocation.physical_parent_region_id, []).append(
                    invocation.id,
                )
        for instance in self._logical_instances:
            if instance.logical_parent_render_id is not None:
                self._logical_parent_by_render_id[instance.render_id] = instance.logical_parent_render_id
        for init_edge in self._init_ancestry:
            self._init_parents_by_child.setdefault(init_edge.child_render_id, []).append(init_edge.parent_render_id)
        for region in self._physical_regions:
            if region.receiver_render_id is not None:
                self._region_ids_by_receiver.setdefault(region.receiver_render_id, []).append(region.id)
            if region.containing_region_id is not None:
                self._region_ids_by_containing.setdefault(region.containing_region_id, []).append(region.id)
            self._region_ids_by_fill.setdefault(region.logical_fill_id, []).append(region.id)
        self._relation_indexes_current = True

    def _ensure_relation_indexes(self) -> None:
        """Build replacement indexes after the capture journals change."""
        if not self._relation_indexes_current:
            self._rebuild_relation_indexes()

    def snapshot(self) -> OwnershipSnapshot:
        """Return an immutable view in capture order."""
        return OwnershipSnapshot(
            source_locations=tuple(self._source_locations),
            component_invocations=tuple(self._component_invocations),
            logical_instances=tuple(self._logical_instances),
            init_ancestry=tuple(self._init_ancestry),
            logical_fills=tuple(self._logical_fills),
            physical_regions=tuple(self._physical_regions),
            render_queue=tuple(self._render_queue),
        )

    def checkpoint(self) -> int:
        """Return the latest capture order for output-lifecycle retirement."""
        return self._order

    def _capture_replay_mutation(self) -> _ReplayMutationSnapshot:
        """Capture all mutable fields before an atomic replay apply."""
        return _ReplayMutationSnapshot(
            counters=(self._order, self._source_id, self._invocation_id, self._fill_id, self._region_id),
            source_locations=list(self._source_locations),
            component_invocations=list(self._component_invocations),
            logical_instances=list(self._logical_instances),
            init_ancestry=list(self._init_ancestry),
            logical_fills=list(self._logical_fills),
            physical_regions=list(self._physical_regions),
            render_queue=list(self._render_queue),
            invocation_index=dict(self._invocation_index),
            instance_invocation=dict(self._instance_invocation),
            fill_index=dict(self._fill_index),
            region_index=dict(self._region_index),
            region_results=dict(self._region_results),
            queue_index=dict(self._queue_index),
            template_fill_by_slot_object=dict(self._template_fill_by_slot_object),
            receiver_fill=dict(self._receiver_fill),
        )

    def _restore_replay_mutation(self, snapshot: _ReplayMutationSnapshot) -> None:
        """Restore a graph snapshot after a failed replay apply."""
        self._order, self._source_id, self._invocation_id, self._fill_id, self._region_id = snapshot.counters
        self._source_locations = snapshot.source_locations
        self._component_invocations = snapshot.component_invocations
        self._logical_instances = snapshot.logical_instances
        self._init_ancestry = snapshot.init_ancestry
        self._logical_fills = snapshot.logical_fills
        self._physical_regions = snapshot.physical_regions
        self._render_queue = snapshot.render_queue
        self._invocation_index = snapshot.invocation_index
        self._instance_invocation = snapshot.instance_invocation
        self._fill_index = snapshot.fill_index
        self._region_index = snapshot.region_index
        self._region_results = dict(snapshot.region_results)
        self._queue_index = snapshot.queue_index
        self._template_fill_by_slot_object = WeakKeyDictionary(snapshot.template_fill_by_slot_object)
        self._receiver_fill = snapshot.receiver_fill
        self._relation_indexes_current = False

    @contextmanager
    def replay_transaction(self) -> Iterator[None]:
        """Roll back every ownership mutation if replay apply raises."""
        snapshot = self._capture_replay_mutation()
        try:
            yield
        except Exception:
            self._restore_replay_mutation(snapshot)
            raise

    def import_replayed_instances(self, records: tuple[ReplayedInstanceRecord, ...]) -> None:
        """Append validated detached descendant instances under fresh IDs."""
        existing_ids = {record.render_id for record in self._logical_instances}
        for record in records:
            if record.render_id in existing_ids:
                msg = f"Cannot replay duplicate component render ID {record.render_id!r}."
                raise RuntimeError(msg)
            existing_ids.add(record.render_id)
            instance = LogicalInstanceRecord(
                order=self._next_order(),
                render_id=record.render_id,
                class_id=record.class_id,
                class_name=record.class_name,
                invocation_id=None,
                logical_parent_render_id=record.logical_parent_render_id,
                transparent=record.transparent,
            )
            self._logical_instances.append(instance)
            self._relation_indexes_current = False

    def import_replayed_snapshot(
        self,
        snapshot: OwnershipSnapshot,
        *,
        external_source_ids: Mapping[SourceLocationId, SourceLocationId] | None = None,
        external_invocation_ids: Mapping[ComponentInvocationId, ComponentInvocationId] | None = None,
        external_fill_ids: Mapping[LogicalFillId, LogicalFillId] | None = None,
        external_region_ids: Mapping[PhysicalRegionId, PhysicalRegionId] | None = None,
    ) -> dict[PhysicalRegionId, PhysicalRegionId]:
        """
        Import a validated local-ID snapshot and return its fresh region-ID map.

        Positive identifiers in ``snapshot`` are artifact-local. Negative
        identifiers are symbolic anchors resolved by the corresponding
        ``external_*`` mapping. The caller owns the surrounding
        :meth:`replay_transaction` and registers physical result wrappers only
        after rebuilding the detached render tree.
        """
        external_source_ids = external_source_ids or {}
        external_invocation_ids = external_invocation_ids or {}
        external_fill_ids = external_fill_ids or {}
        external_region_ids = external_region_ids or {}

        existing_render_ids = {record.render_id for record in self._logical_instances}
        imported_render_ids = [record.render_id for record in snapshot.logical_instances]
        if len(imported_render_ids) != len(set(imported_render_ids)):
            msg = "Cannot replay duplicate component render IDs in one ownership snapshot."
            raise RuntimeError(msg)
        duplicate_render_ids = existing_render_ids.intersection(imported_render_ids)
        if duplicate_render_ids:
            render_id = sorted(duplicate_render_ids)[0]
            msg = f"Cannot replay duplicate component render ID {render_id!r}."
            raise RuntimeError(msg)

        local_source_ids = {record.id for record in snapshot.source_locations}
        local_invocation_ids = {record.id for record in snapshot.component_invocations}
        local_fill_ids = {record.id for record in snapshot.logical_fills}
        local_region_ids = {record.id for record in snapshot.physical_regions}
        if any(int(record_id) <= 0 for record_id in local_source_ids):
            raise RuntimeError("Replayed source-location IDs must be positive artifact-local integers.")
        if any(int(record_id) <= 0 for record_id in local_invocation_ids):
            raise RuntimeError("Replayed invocation IDs must be positive artifact-local integers.")
        if any(int(record_id) <= 0 for record_id in local_fill_ids):
            raise RuntimeError("Replayed fill IDs must be positive artifact-local integers.")
        if any(int(record_id) <= 0 for record_id in local_region_ids):
            raise RuntimeError("Replayed region IDs must be positive artifact-local integers.")

        source_ids = dict(external_source_ids)
        for local_source_id in sorted(local_source_ids, key=int):
            self._source_id += 1
            source_ids[local_source_id] = SourceLocationId(self._source_id)
        invocation_ids = dict(external_invocation_ids)
        for local_invocation_id in sorted(local_invocation_ids, key=int):
            self._invocation_id += 1
            invocation_ids[local_invocation_id] = ComponentInvocationId(self._invocation_id)
        fill_ids = dict(external_fill_ids)
        for local_fill_id in sorted(local_fill_ids, key=int):
            self._fill_id += 1
            fill_ids[local_fill_id] = LogicalFillId(self._fill_id)
        region_ids = dict(external_region_ids)
        local_to_fresh_regions: dict[PhysicalRegionId, PhysicalRegionId] = {}
        for local_region_id in sorted(local_region_ids, key=int):
            self._region_id += 1
            fresh_region_id = PhysicalRegionId(self._region_id)
            region_ids[local_region_id] = fresh_region_id
            local_to_fresh_regions[local_region_id] = fresh_region_id

        order_values = {
            record.order
            for records in (
                snapshot.source_locations,
                snapshot.component_invocations,
                snapshot.logical_instances,
                snapshot.init_ancestry,
                snapshot.logical_fills,
                snapshot.physical_regions,
            )
            for record in records
        }
        for queue in snapshot.render_queue:
            order_values.add(queue.enqueued_order)
            if queue.rendered_order is not None:
                order_values.add(queue.rendered_order)
            if queue.settled_order is not None:
                order_values.add(queue.settled_order)
        order_map = {old: self._next_order() for old in sorted(order_values)}

        def source_id(value: SourceLocationId | None) -> SourceLocationId | None:
            if value is None:
                return None
            try:
                return source_ids[value]
            except KeyError as err:
                raise RuntimeError(f"Unknown replayed source-location ID {int(value)}.") from err

        def invocation_id(value: ComponentInvocationId | None) -> ComponentInvocationId | None:
            if value is None:
                return None
            try:
                return invocation_ids[value]
            except KeyError as err:
                raise RuntimeError(f"Unknown replayed invocation ID {int(value)}.") from err

        def fill_id(value: LogicalFillId) -> LogicalFillId:
            try:
                return fill_ids[value]
            except KeyError as err:
                raise RuntimeError(f"Unknown replayed fill ID {int(value)}.") from err

        def region_id(value: PhysicalRegionId | None) -> PhysicalRegionId | None:
            if value is None:
                return None
            try:
                return region_ids[value]
            except KeyError as err:
                raise RuntimeError(f"Unknown replayed region ID {int(value)}.") from err

        for source_record in snapshot.source_locations:
            self._source_locations.append(
                replace(
                    source_record,
                    id=source_ids[source_record.id],
                    order=order_map[source_record.order],
                )
            )
        for invocation_record in snapshot.component_invocations:
            fresh_invocation_id = cast("ComponentInvocationId", invocation_id(invocation_record.id))
            client_bindings = tuple(
                replace(
                    client_binding,
                    source_location_id=cast("SourceLocationId", source_id(client_binding.source_location_id)),
                )
                for client_binding in invocation_record.client_bindings
            )
            fresh_invocation = replace(
                invocation_record,
                id=fresh_invocation_id,
                order=order_map[invocation_record.order],
                source_location_id=cast("SourceLocationId", source_id(invocation_record.source_location_id)),
                physical_parent_region_id=region_id(invocation_record.physical_parent_region_id),
                client_bindings=client_bindings,
            )
            self._invocation_index[fresh_invocation_id] = len(self._component_invocations)
            self._component_invocations.append(fresh_invocation)
            self._relation_indexes_current = False
            if fresh_invocation.target_render_id is not None:
                self._instance_invocation[fresh_invocation.target_render_id] = fresh_invocation_id
        for instance_record in snapshot.logical_instances:
            fresh_instance = replace(
                instance_record,
                order=order_map[instance_record.order],
                invocation_id=invocation_id(instance_record.invocation_id),
            )
            self._logical_instances.append(fresh_instance)
            self._relation_indexes_current = False
        for init_record in snapshot.init_ancestry:
            fresh_init = replace(
                init_record,
                order=order_map[init_record.order],
                invocation_id=cast("ComponentInvocationId", invocation_id(init_record.invocation_id)),
            )
            self._init_ancestry.append(fresh_init)
            self._relation_indexes_current = False
        for fill_record in snapshot.logical_fills:
            fresh_fill_id = fill_id(fill_record.id)
            fresh_fill = replace(
                fill_record,
                id=fresh_fill_id,
                order=order_map[fill_record.order],
                source_location_id=source_id(fill_record.source_location_id),
                source_invocation_id=invocation_id(fill_record.source_invocation_id),
                fallback_slot_site_location_id=source_id(fill_record.fallback_slot_site_location_id),
            )
            self._fill_index[fresh_fill_id] = len(self._logical_fills)
            self._logical_fills.append(fresh_fill)
            if fresh_fill.receiver_render_id is not None:
                self._receiver_fill[(fresh_fill.receiver_render_id, fresh_fill.slot_name)] = fresh_fill_id
        for region_record in snapshot.physical_regions:
            fresh_region_id = cast("PhysicalRegionId", region_id(region_record.id))
            fresh_region = replace(
                region_record,
                id=fresh_region_id,
                order=order_map[region_record.order],
                logical_fill_id=fill_id(region_record.logical_fill_id),
                slot_site_location_id=source_id(region_record.slot_site_location_id),
                source_location_id=source_id(region_record.source_location_id),
                containing_region_id=region_id(region_record.containing_region_id),
            )
            self._region_index[fresh_region_id] = len(self._physical_regions)
            self._physical_regions.append(fresh_region)
            self._relation_indexes_current = False
        for queue_record in snapshot.render_queue:
            fresh_invocation_id = cast("ComponentInvocationId", invocation_id(queue_record.invocation_id))
            fresh_queue = replace(
                queue_record,
                invocation_id=fresh_invocation_id,
                enqueued_order=order_map[queue_record.enqueued_order],
                rendered_order=(
                    None if queue_record.rendered_order is None else order_map[queue_record.rendered_order]
                ),
                settled_order=(None if queue_record.settled_order is None else order_map[queue_record.settled_order]),
            )
            self._queue_index[fresh_invocation_id] = len(self._render_queue)
            self._render_queue.append(fresh_queue)
        return local_to_fresh_regions

    def register_replayed_region_result(self, region_id: PhysicalRegionId, result: object) -> None:
        """Attach one rebuilt physical wrapper to an imported captured region."""
        if region_id not in self._region_index:
            raise RuntimeError(f"Unknown replayed physical region ID {int(region_id)}.")
        if region_id in self._region_results:
            raise RuntimeError(f"Replayed physical region {int(region_id)} already has a result.")
        self._region_results[region_id] = result

    def release_transient_region_results(self) -> None:
        """Drop selection-only wrapper roots after the outer render settles."""
        self._region_results.clear()

    def source_location(self, location_id: SourceLocationId) -> SourceLocationRecord:
        """Return a captured source location by its graph-local identifier."""
        index = int(location_id) - 1
        if index < 0 or index >= len(self._source_locations):
            msg = f"Unknown source-location id {int(location_id)}."
            raise RuntimeError(msg)
        location = self._source_locations[index]
        if location.id != location_id:
            msg = f"Source-location index corruption for id {int(location_id)}."
            raise RuntimeError(msg)
        return location

    def record_source_location(
        self,
        context: CitryContext,
        *,
        kind: SourceLocationKind,
        source: object,
        position: tuple[int, int],
        mapping_key: str | None = None,
        mapping_index: int | None = None,
    ) -> SourceLocationId:
        """Capture one executed span against post-template-hook runtime source."""
        component = context.component
        if component is None:
            msg = "A template source location requires a component-owned render context."
            raise RuntimeError(msg)
        component_class = type(component)
        template = getattr(component_class, "_citry_template", None)
        origin = template.origin if template is not None else None
        source_text = str(source)
        site_key = (source_text, position, origin)
        site = self._source_site_cache.get(site_key)
        if site is None:
            source_bytes = source_text.encode()
            start_byte, end_byte = position
            if not 0 <= start_byte <= end_byte <= len(source_bytes):
                msg = f"Runtime source byte span {position!r} is outside a {len(source_bytes)}-byte template."
                raise RuntimeError(msg)
            try:
                start = len(source_bytes[:start_byte].decode())
                end = len(source_bytes[:end_byte].decode())
            except UnicodeDecodeError as err:
                msg = f"Runtime source byte span {position!r} does not fall on UTF-8 character boundaries."
                raise RuntimeError(msg) from err
            prefix = source_text[:start]
            line = prefix.count("\n") + 1
            last_newline = prefix.rfind("\n")
            column = start + 1 if last_newline < 0 else start - last_newline
            site = _SourceSite(
                origin=origin,
                source=source_text,
                byte_span=position,
                span=(start, end),
                line=line,
                column=column,
            )
            self._source_site_cache[site_key] = site

        self._source_id += 1
        location_id = SourceLocationId(self._source_id)
        self._source_locations.append(
            SourceLocationRecord(
                id=location_id,
                order=self._next_order(),
                kind=kind,
                owner_render_id=component.id,
                owner_class_id=component._citry_class_id,
                _site=site,
                mapping_key=mapping_key,
                mapping_index=mapping_index,
            )
        )
        return location_id

    def record_component_invocation(
        self,
        context: CitryContext,
        *,
        authored_tag: str,
        target_class_id: str,
        morph_key: str | None,
        morph_mode: MorphMode | None,
        source: object,
        position: tuple[int, int],
        client_bindings: tuple[ComponentTagClientBindingRecord, ...],
    ) -> ComponentInvocationId:
        """Capture an executed component call before it enters the queue."""
        component = context.component
        if component is None:
            msg = "A component invocation requires a component-owned render context."
            raise RuntimeError(msg)
        source_location_id = self.record_source_location(
            context,
            kind=SourceLocationKind.COMPONENT_CALL,
            source=source,
            position=position,
        )
        active = _ACTIVE_REGION.get()
        parent_region = active[1] if active is not None and active[0] is self else None

        self._invocation_id += 1
        invocation_id = ComponentInvocationId(self._invocation_id)
        record = ComponentInvocationRecord(
            id=invocation_id,
            order=self._next_order(),
            source_render_id=component.id,
            source_class_id=component._citry_class_id,
            source_location_id=source_location_id,
            authored_tag=authored_tag,
            target_class_id=target_class_id,
            morph_key=morph_key,
            morph_mode=morph_mode,
            target_render_id=None,
            physical_parent_region_id=parent_region,
            client_bindings=client_bindings,
        )
        self._invocation_index[invocation_id] = len(self._component_invocations)
        self._component_invocations.append(record)
        self._relation_indexes_current = False
        self._queue_index[invocation_id] = len(self._render_queue)
        self._render_queue.append(
            RenderQueueRecord(
                invocation_id=invocation_id,
                enqueued_order=self._next_order(),
                target_render_id=None,
                rendered_order=None,
                settled_order=None,
                state=QueueState.ENQUEUED,
            )
        )
        return invocation_id

    def record_template_fill(
        self,
        slot: Slot,
        context: CitryContext,
        *,
        kind: LogicalFillKind,
        slot_name: str,
        source: object,
        position: tuple[int, int],
        fallback_slot_site_location_id: SourceLocationId | None = None,
    ) -> LogicalFillId:
        """Capture one template-authored fill closure and its lexical owner."""
        component = context.component
        if component is None:
            msg = "A template fill requires a component-owned render context."
            raise RuntimeError(msg)
        location_kind = {
            LogicalFillKind.IMPLICIT: SourceLocationKind.IMPLICIT_FILL,
            LogicalFillKind.NAMED: SourceLocationKind.NAMED_FILL,
            LogicalFillKind.FALLBACK: SourceLocationKind.FALLBACK_FILL,
        }[kind]
        source_location_id = self.record_source_location(
            context,
            kind=location_kind,
            source=source,
            position=position,
        )
        fill_id = self._append_fill(
            kind=kind,
            slot_name=slot_name,
            source_policy=SourcePolicy.TEMPLATE,
            lexical_owner_render_id=component.id,
            lexical_owner_class_id=component._citry_class_id,
            source_location_id=source_location_id,
            source_invocation_id=None,
            receiver_render_id=component.id if kind == LogicalFillKind.FALLBACK else None,
            receiver_class_id=component._citry_class_id if kind == LogicalFillKind.FALLBACK else None,
            fallback_slot_site_location_id=fallback_slot_site_location_id,
        )
        self._template_fill_by_slot_object[slot] = fill_id
        return fill_id

    def _append_fill(
        self,
        *,
        kind: LogicalFillKind,
        slot_name: str,
        source_policy: SourcePolicy,
        lexical_owner_render_id: str | None,
        lexical_owner_class_id: str | None,
        source_location_id: SourceLocationId | None,
        source_invocation_id: ComponentInvocationId | None,
        receiver_render_id: str | None,
        receiver_class_id: str | None,
        fallback_slot_site_location_id: SourceLocationId | None = None,
    ) -> LogicalFillId:
        self._fill_id += 1
        fill_id = LogicalFillId(self._fill_id)
        self._fill_index[fill_id] = len(self._logical_fills)
        self._logical_fills.append(
            LogicalFillRecord(
                id=fill_id,
                order=self._next_order(),
                kind=kind,
                slot_name=slot_name,
                source_policy=source_policy,
                lexical_owner_render_id=lexical_owner_render_id,
                lexical_owner_class_id=lexical_owner_class_id,
                source_location_id=source_location_id,
                source_invocation_id=source_invocation_id,
                receiver_render_id=receiver_render_id,
                receiver_class_id=receiver_class_id,
                fallback_slot_site_location_id=fallback_slot_site_location_id,
            )
        )
        return fill_id

    def bind_template_fill_sources(
        self,
        slots: Mapping[str, Slot],
        invocation_id: ComponentInvocationId,
    ) -> None:
        """Bind freshly collected template supplies to their exact call site."""
        invocation = self._component_invocations[self._invocation_index[invocation_id]]
        for slot in slots.values():
            fill_id = self._template_fill_by_slot_object.get(slot)
            if fill_id is None:
                continue
            fill_index = self._fill_index[fill_id]
            fill = self._logical_fills[fill_index]
            if fill.source_policy != SourcePolicy.TEMPLATE or fill.kind == LogicalFillKind.FALLBACK:
                continue
            if fill.lexical_owner_render_id != invocation.source_render_id:
                msg = "A template fill source invocation must belong to the fill's lexical owner."
                raise RuntimeError(msg)
            if fill.source_invocation_id is not None and fill.source_invocation_id != invocation_id:
                msg = "A template fill cannot be rebound to a second source invocation."
                raise RuntimeError(msg)
            self._logical_fills[fill_index] = fill._with_source_invocation(invocation_id)

    def bind_instance(self, component: Component, element: CitryElement) -> None:
        """Bind a fresh render ID to its invocation and supplied fills."""
        invocation_id = element.ownership_invocation_id
        logical_parent = None
        bound_invocation: ComponentInvocationId | None = invocation_id

        if invocation_id is not None:
            index = self._invocation_index[invocation_id]
            invocation = self._component_invocations[index]
            logical_parent = invocation.source_render_id
            if element.forward_ownership_invocation:
                self._component_invocations[index] = invocation._bind_selector(component.id)
                bound_invocation = None
            else:
                self._component_invocations[index] = invocation._bind_target(component._citry_class_id, component.id)
                self._instance_invocation[component.id] = invocation_id
                queue_index = self._queue_index[invocation_id]
                queue = self._render_queue[queue_index]
                self._render_queue[queue_index] = queue._rendered(component.id, self._next_order())
                init_edge = InitAncestryRecord(
                    order=self._next_order(),
                    invocation_id=invocation_id,
                    parent_render_id=invocation.source_render_id,
                    child_render_id=component.id,
                )
                self._init_ancestry.append(init_edge)
            # Target and selector IDs participate in replacement closure even
            # when this invocation was indexed before its deferred child ran.
            self._relation_indexes_current = False

        instance = LogicalInstanceRecord(
            order=self._next_order(),
            render_id=component.id,
            class_id=component._citry_class_id,
            class_name=type(component).__name__,
            invocation_id=bound_invocation,
            logical_parent_render_id=logical_parent,
            transparent=type(component).transparent,
        )
        self._logical_instances.append(instance)
        self._relation_indexes_current = False

    def bind_supplied_slots(self, component: Component) -> None:
        """Attach each normalized supplied slot to this rendered receiver."""
        component_class_id = getattr(component, "_citry_class_id", None)
        if component_class_id is None:
            # Preserve the narrow structural test/adapter boundary: real
            # Components cache this value during construction.
            component_class_id = type(component).class_id
        for slot_name, slot in component.raw_slots.items():
            key = (component.id, slot_name)
            fill_id = self._template_fill_by_slot_object.get(slot)
            if fill_id is not None:
                fill_id = self._revive_retired_template_fill(
                    slot,
                    fill_id,
                    receiver_render_id=component.id,
                    receiver_class_id=component_class_id,
                )
                fill_index = self._fill_index[fill_id]
                fill = self._logical_fills[fill_index]
                if fill.receiver_render_id is None or fill.receiver_render_id == component.id:
                    self._logical_fills[fill_index] = fill._with_receiver(component.id, component_class_id)
                else:
                    # One stored template Slot can be forwarded to several
                    # receiver instances. Each receiver is a distinct logical
                    # attachment; only repeated outlets on the same receiver
                    # are mirror regions of one attachment.
                    fill_id = self._append_fill(
                        kind=fill.kind,
                        slot_name=slot_name,
                        source_policy=fill.source_policy,
                        lexical_owner_render_id=fill.lexical_owner_render_id,
                        lexical_owner_class_id=fill.lexical_owner_class_id,
                        source_location_id=fill.source_location_id,
                        source_invocation_id=fill.source_invocation_id,
                        receiver_render_id=component.id,
                        receiver_class_id=component_class_id,
                        fallback_slot_site_location_id=fill.fallback_slot_site_location_id,
                    )
            else:
                fill_id = self._append_fill(
                    kind=LogicalFillKind.PYTHON,
                    slot_name=slot_name,
                    source_policy=SourcePolicy.PYTHON,
                    lexical_owner_render_id=None,
                    lexical_owner_class_id=None,
                    source_location_id=None,
                    source_invocation_id=None,
                    receiver_render_id=component.id,
                    receiver_class_id=component_class_id,
                )
            self._receiver_fill[key] = fill_id

    def _revive_retired_template_fill(
        self,
        slot: Slot,
        fill_id: LogicalFillId,
        *,
        receiver_render_id: str | None,
        receiver_class_id: str | None,
    ) -> LogicalFillId:
        """Give a reused retired Slot a new active logical-fill occurrence."""
        fill = self._logical_fills[self._fill_index[fill_id]]
        if fill.state == OwnershipState.ACTIVE:
            return fill_id

        lexical_owner_is_active = any(
            instance.render_id == fill.lexical_owner_render_id and instance.state == OwnershipState.ACTIVE
            for instance in self._logical_instances
        )
        if lexical_owner_is_active:
            kind = fill.kind
            source_policy = fill.source_policy
            lexical_owner_render_id = fill.lexical_owner_render_id
            lexical_owner_class_id = fill.lexical_owner_class_id
            source_location_id = fill.source_location_id
            source_invocation_id = fill.source_invocation_id
        else:
            kind = LogicalFillKind.PYTHON
            source_policy = SourcePolicy.PYTHON
            lexical_owner_render_id = None
            lexical_owner_class_id = None
            source_location_id = None
            source_invocation_id = None

        revived_id = self._append_fill(
            kind=kind,
            slot_name=fill.slot_name,
            source_policy=source_policy,
            lexical_owner_render_id=lexical_owner_render_id,
            lexical_owner_class_id=lexical_owner_class_id,
            source_location_id=source_location_id,
            source_invocation_id=source_invocation_id,
            receiver_render_id=receiver_render_id,
            receiver_class_id=receiver_class_id,
        )
        self._template_fill_by_slot_object[slot] = revived_id
        if receiver_render_id is not None:
            self._receiver_fill[(receiver_render_id, fill.slot_name)] = revived_id
        return revived_id

    def bind_typed_default(self, component: Component, slot_name: str) -> LogicalFillId:
        """Attach one typed default without inventing a lexical browser owner."""
        key = (component.id, slot_name)
        existing = self._receiver_fill.get(key)
        if existing is not None:
            return existing
        fill_id = self._append_fill(
            kind=LogicalFillKind.TYPED_DEFAULT,
            slot_name=slot_name,
            source_policy=SourcePolicy.TYPED_DEFAULT,
            lexical_owner_render_id=None,
            lexical_owner_class_id=None,
            source_location_id=None,
            source_invocation_id=None,
            receiver_render_id=component.id,
            receiver_class_id=component._citry_class_id,
        )
        self._receiver_fill[key] = fill_id
        return fill_id

    def supplied_fill_id(self, component: Component, slot_name: str) -> LogicalFillId | None:
        """Return the logical supply bound to one receiver slot."""
        return self._receiver_fill.get((component.id, slot_name))

    @contextmanager
    def slot_site(
        self,
        context: CitryContext,
        *,
        source: object,
        position: tuple[int, int],
    ) -> Iterator[SourceLocationId]:
        """Make one executed slot outlet visible to nested fill calls."""
        component = context.component
        if component is None:
            msg = "A slot outlet requires a component-owned render context."
            raise RuntimeError(msg)
        location_id = self.record_source_location(
            context,
            kind=SourceLocationKind.SLOT_OUTLET,
            source=source,
            position=position,
        )
        token = _SLOT_SITE.set(
            _SlotSite(
                graph=self,
                receiver_render_id=component.id,
                source_location_id=location_id,
            )
        )
        try:
            yield location_id
        finally:
            _SLOT_SITE.reset(token)

    @contextmanager
    def select_supply(self, slot: Slot, fill_id: LogicalFillId) -> Iterator[None]:
        """Select a receiver-specific supply for the next call of ``slot``."""
        token = _SELECTED_SUPPLY.set(_SelectedSupply(graph=self, slot=slot, logical_fill_id=fill_id))
        try:
            yield
        finally:
            _SELECTED_SUPPLY.reset(token)

    def capture_slot_call(self, slot: Slot, callback: Callable[[], TResult]) -> TResult:
        """Record one logical fill occurrence while preserving its Python result."""
        selected = _SELECTED_SUPPLY.get()
        fill_id: LogicalFillId | None
        if selected is not None and selected.graph is self and selected.slot is slot:
            fill_id = selected.logical_fill_id
        else:
            fill_id = self._template_fill_by_slot_object.get(slot)
        if fill_id is None:
            return callback()

        site = _SLOT_SITE.get()
        old_fill = self._logical_fills[self._fill_index[fill_id]]
        standalone_receiver_id = old_fill.lexical_owner_render_id
        standalone_receiver_class_id = old_fill.lexical_owner_class_id
        receiver_render_id: str | None
        receiver_class_id: str | None
        site_location_id: SourceLocationId | None
        if site is not None and site.graph is self:
            receiver_render_id = site.receiver_render_id
            receiver_class_id = None
            site_location_id = site.source_location_id
        else:
            receiver_render_id = standalone_receiver_id
            receiver_class_id = standalone_receiver_class_id
            site_location_id = old_fill.fallback_slot_site_location_id
        fill_id = self._revive_retired_template_fill(
            slot,
            fill_id,
            receiver_render_id=receiver_render_id,
            receiver_class_id=receiver_class_id,
        )
        fill = self._logical_fills[self._fill_index[fill_id]]
        if site is None or site.graph is not self:
            receiver_render_id = fill.receiver_render_id
            site_location_id = fill.fallback_slot_site_location_id
        active = _ACTIVE_REGION.get()
        containing_region_id = active[1] if active is not None and active[0] is self else None
        if containing_region_id is not None:
            parent = self._physical_regions[self._region_index[containing_region_id]]
            transition_from = parent.lexical_owner_render_id
        else:
            transition_from = receiver_render_id

        self._region_id += 1
        region_id = PhysicalRegionId(self._region_id)
        region_index = len(self._physical_regions)
        self._region_index[region_id] = region_index
        region = PhysicalRegionRequestRecord(
            id=region_id,
            order=self._next_order(),
            logical_fill_id=fill_id,
            receiver_render_id=receiver_render_id,
            slot_site_location_id=site_location_id,
            lexical_owner_render_id=fill.lexical_owner_render_id,
            source_location_id=fill.source_location_id,
            containing_region_id=containing_region_id,
            transition_from_render_id=transition_from,
            result_owner_render_id=None,
            state=RegionState.CAPTURED,
        )
        self._physical_regions.append(region)
        self._relation_indexes_current = False
        token = _ACTIVE_REGION.set((self, region_id))
        try:
            result = callback()
        except Exception:
            self._physical_regions[region_index] = self._physical_regions[region_index]._with_state(RegionState.FAILED)
            raise
        finally:
            _ACTIVE_REGION.reset(token)

        result_context = getattr(result, "context", None)
        result_frame = getattr(result, "frame", None)
        result_render_id = getattr(result_frame, "render_id", None)
        result_owner = (
            result_render_id
            if result_render_id is not None and getattr(result_context, "ownership", None) is self
            else None
        )
        self._physical_regions[region_index] = self._physical_regions[region_index]._with_result_owner(result_owner)
        from citry.citry_render import CitryRender, PhysicalRegionPart, PhysicalRegionRender  # noqa: PLC0415

        wrapped = (
            PhysicalRegionRender(self, region_id, result)
            if isinstance(result, CitryRender)
            else PhysicalRegionPart(self, region_id, cast("RenderPart", result))
        )
        self._region_results[region_id] = wrapped
        return cast("TResult", wrapped)

    def resolve_slot_region(self, slot_site_location_id: SourceLocationId) -> PhysicalRegionId:
        """Resolve the outer region created by one executed slot outlet."""
        matching = [
            region
            for region in self._physical_regions
            if region.slot_site_location_id == slot_site_location_id and region.state == RegionState.CAPTURED
        ]
        matching_ids = {region.id for region in matching}
        outer = [region for region in matching if region.containing_region_id not in matching_ids]
        if len(outer) != 1:
            msg = f"A rendered slot outlet must own exactly one captured outer physical region, got {len(outer)}."
            raise RuntimeError(msg)
        return outer[0].id

    @contextmanager
    def active_region(self, region_id: PhysicalRegionId) -> Iterator[None]:
        """Capture hook-created Slot calls as children of an outlet region."""
        token = _ACTIVE_REGION.set((self, region_id))
        try:
            yield
        finally:
            _ACTIVE_REGION.reset(token)

    def current_region_id(self) -> PhysicalRegionId | None:
        """Return this graph's active physical region, if one is in scope."""
        active = _ACTIVE_REGION.get()
        return active[1] if active is not None and active[0] is self else None

    @contextmanager
    def active_invocation_region(self, invocation_id: ComponentInvocationId | None) -> Iterator[None]:
        """Restore a deferred invocation's physical parent while it renders."""
        parent_region_id = (
            None
            if invocation_id is None
            else self._component_invocations[self._invocation_index[invocation_id]].physical_parent_region_id
        )
        if parent_region_id is None:
            yield
            return
        with self.active_region(parent_region_id):
            yield

    def rebind_slot_region(self, region_id: PhysicalRegionId, result: TResult) -> TResult:
        """Bind a slot hook's selected output to the existing outlet region."""
        region_index = self._region_index[region_id]
        region = self._physical_regions[region_index]
        if region.state != RegionState.CAPTURED:
            msg = f"Cannot rebind non-captured physical region {region_id}."
            raise RuntimeError(msg)
        result_context = getattr(result, "context", None)
        result_frame = getattr(result, "frame", None)
        result_render_id = getattr(result_frame, "render_id", None)
        result_owner = (
            result_render_id
            if result_render_id is not None and getattr(result_context, "ownership", None) is self
            else None
        )
        self._physical_regions[region_index] = region._with_result_owner(result_owner)
        from citry.citry_render import CitryRender, PhysicalRegionPart, PhysicalRegionRender  # noqa: PLC0415

        wrapped = (
            PhysicalRegionRender(self, region_id, result)
            if isinstance(result, CitryRender)
            else PhysicalRegionPart(self, region_id, cast("RenderPart", result))
        )
        self._region_results[region.id] = wrapped
        return cast("TResult", wrapped)

    def selected_region_ids(
        self,
        *,
        render_object_ids: set[int],
    ) -> set[PhysicalRegionId]:
        """Resolve selected render objects to transient physical occurrences."""
        # Every occurrence has its own wrapper. The wrapper itself is the
        # unambiguous signal. A hook may intentionally select a nested
        # CitryRender out of the occurrence, though, so preserve its ownership
        # ancestry when that exact render object survives. Plain descendant
        # strings never count: equal or interned text is not occurrence
        # identity.
        from citry.citry_render import CitryRender, _PhysicalRegion  # noqa: PLC0415

        selected: set[PhysicalRegionId] = set()
        # Region results are intentionally nested: an outer slot wrapper can
        # contain several inner region wrappers, and every one of those is
        # also present in ``_region_results``. Walking from each dictionary
        # entry independently therefore revisits the same subtree once per
        # ancestor region. Cache the identity-based containment answer for
        # this selection pass so each live render object is inspected once.
        contains_selected: dict[int, bool] = {}
        visiting: set[int] = set()

        def subtree_contains_selected(current: object) -> bool:
            object_id = id(current)
            cached = contains_selected.get(object_id)
            if cached is not None:
                return cached
            if object_id in visiting:
                return False
            visiting.add(object_id)
            try:
                if isinstance(current, _PhysicalRegion):
                    result = subtree_contains_selected(current.part)
                elif isinstance(current, CitryRender):
                    result = object_id in render_object_ids or any(
                        subtree_contains_selected(part) for part in current.parts
                    )
                else:
                    result = False
            finally:
                visiting.remove(object_id)
            contains_selected[object_id] = result
            return result

        for region_id, result in self._region_results.items():
            # A selected occurrence wrapper is an exact region selection.
            # Nested wrappers do not imply that their ancestors were
            # selected; only nested CitryRender identity carries ancestry.
            if id(result) in render_object_ids or subtree_contains_selected(result):
                selected.add(region_id)
        return selected

    def settle_component(self, render_id: str, *, failed: bool = False) -> None:
        """Mark a bound deferred invocation settled or failed."""
        invocation_id = self._instance_invocation.get(render_id)
        if invocation_id is None:
            return
        if failed:
            self.fail_invocation(invocation_id)
            return
        queue_index = self._queue_index[invocation_id]
        queue = self._render_queue[queue_index]
        self._render_queue[queue_index] = queue._settled(self._next_order(), QueueState.SETTLED)

    def retire_invocation(self, invocation_id: ComponentInvocationId | None) -> None:
        """Retire deferred work discarded before it rendered."""
        if invocation_id is None:
            return
        invocation_index = self._invocation_index[invocation_id]
        invocation = self._component_invocations[invocation_index]
        self._component_invocations[invocation_index] = invocation._with_state(OwnershipState.RETIRED)
        queue_index = self._queue_index[invocation_id]
        queue = self._render_queue[queue_index]
        if queue.state != QueueState.FAILED:
            self._render_queue[queue_index] = queue._settled(self._next_order(), QueueState.RETIRED)

    def retire_unselected_after(
        self,
        checkpoint: int,
        *,
        through_order: int,
        preserved_render_ids: set[str],
        preserved_region_ids: set[PhysicalRegionId] | None = None,
    ) -> None:
        """Retire hook side effects that are absent from the selected result."""
        direct_preserved_render_ids = set(preserved_render_ids)
        preserved_region_ids = set(preserved_region_ids or ())
        region_receiver_ids = {
            region.receiver_render_id
            for region_id in preserved_region_ids
            if region_id in self._region_index
            for region in (self._physical_regions[self._region_index[region_id]],)
            if checkpoint < region.order <= through_order
            and region.slot_site_location_id is not None
            and region.receiver_render_id is not None
        }
        preserved_render_ids = self._with_ownership_ancestors(preserved_render_ids | region_receiver_ids)
        instance_indexes = self._ordered_indexes_between(self._logical_instances, checkpoint, through_order)
        discarded_render_ids = {
            self._logical_instances[index].render_id
            for index in instance_indexes
            if self._logical_instances[index].render_id not in preserved_render_ids
        }
        invocation_indexes = self._ordered_indexes_between(self._component_invocations, checkpoint, through_order)
        discarded_invocation_ids = {
            self._component_invocations[index].id
            for index in invocation_indexes
            if self._component_invocations[index].target_render_id not in preserved_render_ids
        }
        for invocation_id in discarded_invocation_ids:
            self.retire_invocation(invocation_id)

        for index in instance_indexes:
            instance = self._logical_instances[index]
            if instance.render_id in discarded_render_ids:
                self._logical_instances[index] = instance._with_state(OwnershipState.RETIRED)

        for index in self._ordered_indexes_between(self._init_ancestry, checkpoint, through_order):
            edge = self._init_ancestry[index]
            if edge.child_render_id not in preserved_render_ids:
                self._init_ancestry[index] = edge._with_state(OwnershipState.RETIRED)

        preserved_fill_ids = {
            region.logical_fill_id
            for region_id in preserved_region_ids
            if region_id in self._region_index
            for region in (self._physical_regions[self._region_index[region_id]],)
            if checkpoint < region.order <= through_order
        }
        region_indexes = self._ordered_indexes_between(self._physical_regions, checkpoint, through_order)
        segment_fill_ids = {self._physical_regions[index].logical_fill_id for index in region_indexes}
        discarded_fill_ids: set[LogicalFillId] = set()
        for index in self._ordered_indexes_between(self._logical_fills, checkpoint, through_order):
            fill = self._logical_fills[index]
            has_region = fill.id in segment_fill_ids
            if fill.id not in preserved_fill_ids and (
                has_region or fill.receiver_render_id not in direct_preserved_render_ids
            ):
                discarded_fill_ids.add(fill.id)
                self._logical_fills[index] = fill._with_state(OwnershipState.RETIRED)

        for index in region_indexes:
            region = self._physical_regions[index]
            if region.logical_fill_id in discarded_fill_ids or region.id not in preserved_region_ids:
                self._physical_regions[index] = region._with_state(RegionState.RETIRED)

    def _with_ownership_ancestors(self, render_ids: set[str]) -> set[str]:
        """Close selected render IDs over active logical/init ancestry."""
        self._ensure_relation_indexes()
        closed = set(render_ids)
        pending = list(closed)
        while pending:
            render_id = pending.pop()
            additions: list[str] = []
            logical_parent = self._logical_parent_by_render_id.get(render_id)
            if logical_parent is not None:
                additions.append(logical_parent)
            for invocation_id in self._invocation_ids_by_target.get(render_id, ()):
                invocation = self._component_invocations[self._invocation_index[invocation_id]]
                if invocation.target_render_id == render_id:
                    additions.append(invocation.source_render_id)
                    additions.extend(invocation.selector_render_ids)
            additions.extend(self._init_parents_by_child.get(render_id, ()))
            for addition in additions:
                if addition not in closed:
                    closed.add(addition)
                    pending.append(addition)
        return closed

    def retire_range(self, checkpoint: int, *, through_order: int) -> None:
        """Retire every ownership record captured by one discarded output attempt."""
        for index in self._ordered_indexes_between(self._component_invocations, checkpoint, through_order):
            self.retire_invocation(self._component_invocations[index].id)
        for index in self._ordered_indexes_between(self._logical_instances, checkpoint, through_order):
            instance = self._logical_instances[index]
            self._logical_instances[index] = instance._with_state(OwnershipState.RETIRED)
        for index in self._ordered_indexes_between(self._init_ancestry, checkpoint, through_order):
            edge = self._init_ancestry[index]
            self._init_ancestry[index] = edge._with_state(OwnershipState.RETIRED)
        for index in self._ordered_indexes_between(self._logical_fills, checkpoint, through_order):
            fill = self._logical_fills[index]
            self._logical_fills[index] = fill._with_state(OwnershipState.RETIRED)
        for index in self._ordered_indexes_between(self._physical_regions, checkpoint, through_order):
            region = self._physical_regions[index]
            self._physical_regions[index] = region._with_state(RegionState.RETIRED)

    def retire_component_output(
        self,
        render_id: str,
        *,
        through_order: int,
        descendant_render_ids: set[str] | None = None,
        preserved_render_ids: set[str] | None = None,
        preserved_region_ids: set[PhysicalRegionId] | None = None,
    ) -> None:
        """Retire records belonging to one replaced component output."""
        direct_preserved_render_ids = set(preserved_render_ids or ())
        explicit_preserved_region_ids = set(preserved_region_ids or ())
        region_receiver_ids = {
            region.receiver_render_id
            for region_id in explicit_preserved_region_ids
            if region_id in self._region_index
            for region in (self._physical_regions[self._region_index[region_id]],)
            if region.order <= through_order and region.receiver_render_id is not None
        }
        preserved_render_ids = self._with_ownership_ancestors(direct_preserved_render_ids | region_receiver_ids)
        # Slot-fill renders carry the lexical owner's frame through the
        # receiver's physical output. That owner can be a logical ancestor of
        # the component whose output is being replaced, so it is not a
        # discardable descendant even when `_render_ids()` finds its frame in
        # the old physical subtree.
        ownership_ancestors = self._with_ownership_ancestors({render_id})
        retired_render_ids = set(descendant_render_ids or ()) - preserved_render_ids - ownership_ancestors
        retired_region_ids: set[PhysicalRegionId] = set()
        retired_invocation_ids: set[ComponentInvocationId] = set()

        preserved_region_ids = set(explicit_preserved_region_ids)
        for preserved_render_id in preserved_render_ids:
            for invocation_id in self._invocation_ids_by_target.get(preserved_render_id, ()):
                invocation = self._component_invocations[self._invocation_index[invocation_id]]
                if (
                    invocation.order <= through_order
                    and invocation.target_render_id == preserved_render_id
                    and invocation.physical_parent_region_id is not None
                ):
                    preserved_region_ids.add(invocation.physical_parent_region_id)
        pending_preserved_regions = list(preserved_region_ids)
        while pending_preserved_regions:
            region_id = pending_preserved_regions.pop()
            region = self._physical_regions[self._region_index[region_id]] if region_id in self._region_index else None
            containing_region_id = None if region is None else region.containing_region_id
            if containing_region_id is not None and containing_region_id not in preserved_region_ids:
                preserved_region_ids.add(containing_region_id)
                pending_preserved_regions.append(containing_region_id)

        pending_source_or_receiver_ids = [render_id, *retired_render_ids]
        pending_retired_render_ids = list(retired_render_ids)
        pending_retired_region_ids: list[PhysicalRegionId] = []
        expanded_source_or_receiver_ids: set[str] = set()
        expanded_retired_render_ids: set[str] = set()
        expanded_retired_region_ids: set[PhysicalRegionId] = set()

        def retire_region(region_id: PhysicalRegionId) -> None:
            if region_id in retired_region_ids or region_id in preserved_region_ids:
                return
            region = self._physical_regions[self._region_index[region_id]]
            if region.order > through_order:
                return
            retired_region_ids.add(region_id)
            pending_retired_region_ids.append(region_id)

        def retire_invocation_record(invocation_id: ComponentInvocationId) -> None:
            if invocation_id in retired_invocation_ids:
                return
            invocation = self._component_invocations[self._invocation_index[invocation_id]]
            if invocation.order > through_order or invocation.target_render_id in preserved_render_ids:
                return
            retired_invocation_ids.add(invocation_id)
            target_render_id = invocation.target_render_id
            if target_render_id is not None and target_render_id not in retired_render_ids:
                retired_render_ids.add(target_render_id)
                pending_source_or_receiver_ids.append(target_render_id)
                pending_retired_render_ids.append(target_render_id)

        while pending_source_or_receiver_ids or pending_retired_render_ids or pending_retired_region_ids:
            while pending_source_or_receiver_ids:
                owner_render_id = pending_source_or_receiver_ids.pop()
                if owner_render_id in expanded_source_or_receiver_ids:
                    continue
                expanded_source_or_receiver_ids.add(owner_render_id)
                for region_id in self._region_ids_by_receiver.get(owner_render_id, ()):
                    region = self._physical_regions[self._region_index[region_id]]
                    if region.receiver_render_id == owner_render_id:
                        retire_region(region_id)
                for invocation_id in self._invocation_ids_by_source.get(owner_render_id, ()):
                    invocation = self._component_invocations[self._invocation_index[invocation_id]]
                    if invocation.source_render_id == owner_render_id:
                        retire_invocation_record(invocation_id)

            while pending_retired_render_ids:
                retired_render_id = pending_retired_render_ids.pop()
                if retired_render_id in expanded_retired_render_ids:
                    continue
                expanded_retired_render_ids.add(retired_render_id)
                for invocation_id in self._invocation_ids_by_target.get(retired_render_id, ()):
                    invocation = self._component_invocations[self._invocation_index[invocation_id]]
                    if invocation.target_render_id == retired_render_id:
                        retire_invocation_record(invocation_id)

            while pending_retired_region_ids:
                retired_region_id = pending_retired_region_ids.pop()
                if retired_region_id in expanded_retired_region_ids:
                    continue
                expanded_retired_region_ids.add(retired_region_id)
                for region_id in self._region_ids_by_containing.get(retired_region_id, ()):
                    region = self._physical_regions[self._region_index[region_id]]
                    if region.containing_region_id == retired_region_id:
                        retire_region(region_id)
                for invocation_id in self._invocation_ids_by_region.get(retired_region_id, ()):
                    invocation = self._component_invocations[self._invocation_index[invocation_id]]
                    if invocation.physical_parent_region_id == retired_region_id:
                        retire_invocation_record(invocation_id)

        for invocation_id in retired_invocation_ids:
            self.retire_invocation(invocation_id)

        for index, instance in enumerate(self._logical_instances):
            if instance.order <= through_order and instance.render_id in retired_render_ids:
                self._logical_instances[index] = instance._with_state(OwnershipState.RETIRED)

        for index, edge in enumerate(self._init_ancestry):
            if edge.order <= through_order and (
                edge.invocation_id in retired_invocation_ids or edge.child_render_id in retired_render_ids
            ):
                self._init_ancestry[index] = edge._with_state(OwnershipState.RETIRED)

        active_receiver_ids = {
            instance.render_id for instance in self._logical_instances if instance.state == OwnershipState.ACTIVE
        }
        active_class_by_render_id = {
            instance.render_id: instance.class_id
            for instance in self._logical_instances
            if instance.state == OwnershipState.ACTIVE
        }
        retired_fill_ids: set[LogicalFillId] = set()
        for index, fill in enumerate(self._logical_fills):
            if fill.order > through_order:
                continue
            fill_region_entries = [
                (self._region_index[region_id], self._physical_regions[self._region_index[region_id]])
                for region_id in self._region_ids_by_fill.get(fill.id, ())
            ]
            selected_regions = [
                (region_index, region)
                for region_index, region in fill_region_entries
                if region.order > through_order and region.state == RegionState.CAPTURED
            ]
            if selected_regions:
                selected_receiver_id = fill.receiver_render_id
                if selected_receiver_id not in active_receiver_ids:
                    selected_receiver_id = next(
                        (
                            region.receiver_render_id
                            for _, region in selected_regions
                            if region.receiver_render_id in active_receiver_ids
                        ),
                        render_id,
                    )
                selected_receiver_class_id = active_class_by_render_id.get(selected_receiver_id)
                self._logical_fills[index] = fill._with_receiver(
                    selected_receiver_id,
                    selected_receiver_class_id,
                    state=OwnershipState.ACTIVE,
                )
                self._receiver_fill[(selected_receiver_id, fill.slot_name)] = fill.id
                for region_index, region in selected_regions:
                    if region.receiver_render_id not in active_receiver_ids:
                        rebound = region._with_receiver(selected_receiver_id)
                        self._physical_regions[region_index] = rebound
                        self._relation_indexes_current = False
                continue
            fill_regions = [region for _, region in fill_region_entries]
            if any(region.id in preserved_region_ids for region in fill_regions) or (
                not fill_regions and fill.receiver_render_id in direct_preserved_render_ids
            ):
                continue
            if (
                fill.lexical_owner_render_id == render_id
                or fill.lexical_owner_render_id in retired_render_ids
                or fill.receiver_render_id in retired_render_ids
            ):
                retired_fill_ids.add(fill.id)
                self._logical_fills[index] = fill._with_state(OwnershipState.RETIRED)

        regions_to_retire = set(retired_region_ids)
        for fill_id in retired_fill_ids:
            regions_to_retire.update(self._region_ids_by_fill.get(fill_id, ()))
        for region_id in regions_to_retire:
            index = self._region_index[region_id]
            region = self._physical_regions[index]
            if region.order <= through_order:
                self._physical_regions[index] = region._with_state(RegionState.RETIRED)

    def fail_invocation(self, invocation_id: ComponentInvocationId | None) -> None:
        """Mark an invocation that raised before normal finalization."""
        if invocation_id is None:
            return
        queue_index = self._queue_index[invocation_id]
        queue = self._render_queue[queue_index]
        invocation_index = self._invocation_index[invocation_id]
        invocation = self._component_invocations[invocation_index]
        self._component_invocations[invocation_index] = invocation._with_state(OwnershipState.RETIRED)
        selector_ids = set(invocation.selector_render_ids)
        if selector_ids:
            for index, instance in enumerate(self._logical_instances):
                if instance.render_id in selector_ids:
                    self._logical_instances[index] = instance._with_state(OwnershipState.RETIRED)
        if invocation.target_render_id is not None:
            self.retire_component_output(
                invocation.target_render_id,
                through_order=self.checkpoint(),
            )
            for index, instance in enumerate(self._logical_instances):
                if instance.render_id == invocation.target_render_id:
                    self._logical_instances[index] = instance._with_state(OwnershipState.RETIRED)
            for index, edge in enumerate(self._init_ancestry):
                if edge.invocation_id == invocation_id:
                    self._init_ancestry[index] = edge._with_state(OwnershipState.RETIRED)
        self._render_queue[queue_index] = queue._settled(self._next_order(), QueueState.FAILED)


def current_ownership_graph() -> OwnershipGraph | None:
    """Return the graph active in this render context, if any."""
    return _CURRENT_GRAPH.get()


@contextmanager
def ownership_render_scope() -> Iterator[OwnershipGraph]:
    """Reuse an enclosing render graph or create one for a root render."""
    graph = _CURRENT_GRAPH.get()
    if graph is not None:
        yield graph
        return
    graph = OwnershipGraph()
    token = _CURRENT_GRAPH.set(graph)
    try:
        yield graph
    finally:
        _CURRENT_GRAPH.reset(token)


@contextmanager
def resume_ownership_graph(graph: OwnershipGraph | None) -> Iterator[None]:
    """Temporarily resume the graph saved for delayed render settlement."""
    if graph is None or _CURRENT_GRAPH.get() is graph:
        yield
        return
    token = _CURRENT_GRAPH.set(graph)
    try:
        yield
    finally:
        _CURRENT_GRAPH.reset(token)


def capture_current_slot_call(slot: Slot, callback: Callable[[], TResult]) -> TResult:
    """Route a Slot call through the active ownership graph when present."""
    graph = _CURRENT_GRAPH.get()
    if graph is None:
        return callback()
    return graph.capture_slot_call(slot, callback)


__all__ = [
    "AlpineHandlerClientBindingPayload",
    "CitryDomEventClientBindingPayload",
    "CitryPollClientBindingPayload",
    "ComponentInvocationId",
    "ComponentInvocationRecord",
    "ComponentTagClientBindingKind",
    "ComponentTagClientBindingPayload",
    "ComponentTagClientBindingRecord",
    "ComponentTagClientBindingSource",
    "InitAncestryRecord",
    "LogicalFillId",
    "LogicalFillKind",
    "LogicalFillRecord",
    "LogicalInstanceRecord",
    "MorphMode",
    "OwnershipGraph",
    "OwnershipSnapshot",
    "OwnershipState",
    "PhysicalRegionId",
    "PhysicalRegionRequestRecord",
    "PropsClientBindingPayload",
    "QueueState",
    "RegionState",
    "RenderQueueRecord",
    "SourceLocationId",
    "SourceLocationKind",
    "SourceLocationRecord",
    "SourcePolicy",
]
