"""Framework-neutral prepared view produced after Python rendering."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True, slots=True)
class Html:
    text: str
    source: str


@dataclass(frozen=True, slots=True)
class TextBinding:
    key: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"citryText[0-9A-Za-z]+", self.key) is None:
            raise ValueError("prepared text binding key is not generated-safe")


@dataclass(frozen=True, slots=True)
class ElementOpen:
    """One authored HTML start tag plus optional evaluated data bindings."""

    tag: str
    authored_attrs: tuple[str, ...]
    attrs_binding_key: str | None
    key_binding_key: str | None
    source_span: tuple[int, int]
    event_bindings: tuple[dict[str, object], ...] = ()

    def __post_init__(self) -> None:
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", self.tag) is None:
            raise ValueError("prepared element tag is not generated-safe")
        for key in (self.attrs_binding_key, self.key_binding_key):
            if key is not None and re.fullmatch(r"citry(?:Attrs|Key)[0-9A-Za-z]+", key) is None:
                raise ValueError("prepared element binding key is not generated-safe")
        _valid_span(self.source_span)


@dataclass(frozen=True, slots=True)
class ElementClose:
    tag: str
    source_span: tuple[int, int]

    def __post_init__(self) -> None:
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", self.tag) is None:
            raise ValueError("prepared element tag is not generated-safe")
        _valid_span(self.source_span)


@dataclass(frozen=True, slots=True)
class ComponentCall:
    occurrence_id: str


@dataclass(frozen=True, slots=True)
class LocalComponentCall:
    """Reusable definition call whose absolute occurrence lives in preparedData."""

    local_id: str
    type_key: str
    component_tag: str
    source_span: tuple[int, int]
    fills: tuple[PreparedFill, ...] = ()

    def __post_init__(self) -> None:
        if re.fullmatch(r"citryCall[0-9A-Za-z]+", self.local_id) is None:
            raise ValueError("prepared local component call id is not generated-safe")
        _nonempty_string(self.type_key, "prepared local component call type key")
        if re.fullmatch(r"[a-z][a-z0-9.-]*-[a-z0-9.-]+", self.component_tag) is None:
            raise ValueError("prepared local component call tag is not a safe custom-element name")
        _valid_span(self.source_span)
        if len({fill.site_id for fill in self.fills}) != len(self.fills):
            raise ValueError("prepared component call has duplicate supplied fill sites")


@dataclass(frozen=True, slots=True)
class PreparedFill:
    """Caller-owned native Vue slot closure for one generated receiver site."""

    site_id: str
    public_name: str
    children: tuple[PreparedNode, ...]

    def __post_init__(self) -> None:
        _slot_identity(self.site_id, self.public_name)


@dataclass(frozen=True, slots=True)
class PreparedSlotOutlet:
    """Receiver-owned native Vue outlet and its actually prepared fallback."""

    site_id: str
    public_name: str
    fallback: tuple[PreparedNode, ...]

    def __post_init__(self) -> None:
        _slot_identity(self.site_id, self.public_name)


@dataclass(frozen=True, slots=True)
class ForwardedSlot:
    """Invoke a slot received by the current lexical component inside a supplied fill."""

    site_id: str
    public_name: str

    def __post_init__(self) -> None:
        _slot_identity(self.site_id, self.public_name)


@dataclass(frozen=True, slots=True)
class FillClosure:
    """Selected fill with stable Citry lexical and final-result ownership."""

    site_id: str
    public_name: str
    lexical_owner_id: str | None
    result_owner_id: str | None
    children: tuple[PreparedNode, ...]


@dataclass(frozen=True, slots=True)
class SlotOutlet:
    site_id: str
    public_name: str
    receiver_id: str
    selected: FillClosure


PreparedNode: TypeAlias = (
    "Html | TextBinding | ElementOpen | ElementClose | ComponentCall | "
    "LocalComponentCall | ForwardedSlot | PreparedSlotOutlet | SlotOutlet"
)


def _slot_identity(site_id: object, public_name: object) -> None:
    if type(site_id) is not str or re.fullmatch(r"citrySlot[0-9A-Za-z]+", site_id) is None:
        raise ValueError("slot site id is not generated-safe")
    _nonempty_string(public_name, "slot public name")


@dataclass(frozen=True, slots=True)
class PreparedDefinition:
    id: str
    type_key: str
    children: tuple[PreparedNode, ...]
    directive_signature: tuple[RuntimeDirective, ...] = ()

    def __post_init__(self) -> None:
        _nonempty_string(self.id, "definition id")
        _nonempty_string(self.type_key, "definition type key")
        sites: set[str] = set()
        for directive in self.directive_signature:
            if directive.site_id in sites:
                raise ValueError("runtime directive site id is duplicated")
            sites.add(directive.site_id)


@dataclass(frozen=True, slots=True)
class RuntimeDirective:
    site_id: str
    name: str
    arg: str | None = None
    modifiers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if re.fullmatch(r"citryDirective[0-9A-Za-z]+", self.site_id) is None:
            raise ValueError("runtime directive site id is not generated-safe")
        _nonempty_string(self.name, "runtime directive name")
        if self.arg is not None and type(self.arg) is not str:
            raise TypeError("runtime directive argument must be an exact string or None")
        if any(type(item) is not str or not item for item in self.modifiers):
            raise TypeError("runtime directive modifiers must be exact nonempty strings")
        if tuple(sorted(set(self.modifiers))) != self.modifiers:
            raise ValueError("runtime directive modifiers must be sorted and unique")


@dataclass(frozen=True, slots=True)
class PreparedOccurrence:
    """One stable Vue occurrence; parent_id is its physical Vue placement parent."""

    id: str
    type_key: str
    definition_id: str
    server_data: dict[str, object]
    prepared_data: dict[str, object]
    parent_id: str | None
    placement_key: str | None

    def __post_init__(self) -> None:
        _nonempty_string(self.id, "occurrence id")
        _nonempty_string(self.type_key, "occurrence type key")
        _nonempty_string(self.definition_id, "occurrence definition id")
        if self.parent_id is not None:
            _nonempty_string(self.parent_id, "occurrence parent id")
            _nonempty_string(self.placement_key, "occurrence placement key")
        elif self.placement_key is not None:
            raise ValueError("prepared root occurrence must not have a placement key")
        detached = _detach_object(self.server_data, "server_data")
        object.__setattr__(self, "server_data", detached)
        prepared = _detach_object(self.prepared_data, "prepared_data")
        object.__setattr__(self, "prepared_data", prepared)

    @classmethod
    def _from_assembly(
        cls,
        occurrence_id: str,
        type_key: str,
        definition_id: str,
        server_data: dict[str, object],
        prepared_data: dict[str, object],
        parent_id: str | None,
        placement_key: str | None,
    ) -> PreparedOccurrence:
        """Adopt trusted builder-owned prepared data and detach server data once."""
        _nonempty_string(occurrence_id, "occurrence id")
        _nonempty_string(type_key, "occurrence type key")
        _nonempty_string(definition_id, "occurrence definition id")
        if parent_id is not None:
            _nonempty_string(parent_id, "occurrence parent id")
            _nonempty_string(placement_key, "occurrence placement key")
        elif placement_key is not None:
            raise ValueError("prepared root occurrence must not have a placement key")
        if type(prepared_data) is not dict or any(type(key) is not str for key in prepared_data):
            raise TypeError("builder-owned prepared_data must be an exact dict with exact string keys")
        value = object.__new__(cls)
        object.__setattr__(value, "id", occurrence_id)
        object.__setattr__(value, "type_key", type_key)
        object.__setattr__(value, "definition_id", definition_id)
        object.__setattr__(value, "server_data", _detach_object(server_data, "server_data"))
        object.__setattr__(value, "prepared_data", prepared_data)
        object.__setattr__(value, "parent_id", parent_id)
        object.__setattr__(value, "placement_key", placement_key)
        return value


def _detach_object(value: object, name: str) -> dict[str, object]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise TypeError(f"{name} must be an exact dict with exact string keys")
    _validate_keys(value, name)
    return json.loads(json.dumps(value, allow_nan=False))


def _nonempty_string(value: object, name: str) -> None:
    if type(value) is not str or not value:
        raise TypeError(f"{name} must be an exact nonempty string")


def _valid_span(value: object) -> None:
    if (
        type(value) is not tuple
        or len(value) != 2
        or any(type(item) is not int for item in value)
        or value[0] < 0
        or value[1] < value[0]
    ):
        raise TypeError("prepared source span must be an ordered pair of nonnegative integers")


def _validate_keys(value: object, name: str) -> None:
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise TypeError(f"{name} contains a non-string object key")
        for item in value.values():
            _validate_keys(item, name)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _validate_keys(item, name)


@dataclass(frozen=True, slots=True)
class PreparedMarker:
    """Name a marker within its lexical owner and identify its mounted occurrence."""

    owner_id: str
    name: str
    occurrence_id: str

    def __post_init__(self) -> None:
        _nonempty_string(self.owner_id, "marker owner id")
        _nonempty_string(self.occurrence_id, "marker occurrence id")
        if type(self.name) is not str or re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", self.name) is None:
            raise ValueError("prepared marker name is invalid")


class PreparedDefinitionIdentity(Protocol):
    """Read-only definition identity available during browser preparation."""

    @property
    def id(self) -> str: ...

    @property
    def type_key(self) -> str: ...


class PreparedViewMetadata(Protocol):
    """Read-only occurrence and definition identity for a prepared browser view."""

    @property
    def revision(self) -> int: ...

    @property
    def root_id(self) -> str: ...

    @property
    def occurrences(self) -> tuple[PreparedOccurrence, ...]: ...

    @property
    def definitions(self) -> tuple[PreparedDefinitionIdentity, ...]: ...

    @property
    def markers(self) -> tuple[PreparedMarker, ...]: ...


@dataclass(frozen=True, slots=True)
class PreparedView:
    revision: int
    root_id: str
    occurrences: tuple[PreparedOccurrence, ...]
    definitions: tuple[PreparedDefinition, ...]
    markers: tuple[PreparedMarker, ...] = ()

    @classmethod
    def _from_assembly(
        cls,
        revision: int,
        root_id: str,
        occurrences: tuple[PreparedOccurrence, ...],
        definitions: tuple[PreparedDefinition, ...],
        markers: tuple[PreparedMarker, ...] = (),
    ) -> PreparedView:
        """Freeze a view whose single selected-tree builder proved graph invariants."""
        value = object.__new__(cls)
        object.__setattr__(value, "revision", revision)
        object.__setattr__(value, "root_id", root_id)
        object.__setattr__(value, "occurrences", occurrences)
        object.__setattr__(value, "definitions", definitions)
        object.__setattr__(value, "markers", markers)
        return value

    def __post_init__(self) -> None:
        _nonempty_string(self.root_id, "prepared root id")
        if type(self.revision) is not int or self.revision < 0:
            raise ValueError("prepared revision must be a nonnegative integer")
        occurrence_ids = {item.id for item in self.occurrences}
        definition_ids = {item.id for item in self.definitions}
        definitions = {item.id: item for item in self.definitions}
        if len(occurrence_ids) != len(self.occurrences):
            raise ValueError("duplicate prepared occurrence id")
        if len(definition_ids) != len(self.definitions):
            raise ValueError("duplicate prepared definition id")
        if self.root_id not in occurrence_ids:
            raise ValueError("prepared root occurrence is missing")
        occurrences = {item.id: item for item in self.occurrences}
        marker_keys: set[tuple[str, str]] = set()
        marker_occurrences: set[str] = set()
        prior_marker: tuple[str, str, str] | None = None
        for marker in self.markers:
            if type(marker) is not PreparedMarker:
                raise TypeError("prepared markers must be exact PreparedMarker values")
            if marker.owner_id not in occurrences or marker.occurrence_id not in occurrences:
                raise ValueError("prepared marker references an unknown occurrence")
            key = (marker.owner_id, marker.name)
            order = (*key, marker.occurrence_id)
            if key in marker_keys or marker.occurrence_id in marker_occurrences:
                raise ValueError("prepared marker aliases must be unique")
            if prior_marker is not None and order <= prior_marker:
                raise ValueError("prepared markers must be strictly sorted")
            marker_keys.add(key)
            marker_occurrences.add(marker.occurrence_id)
            prior_marker = order
        if occurrences[self.root_id].parent_id is not None:
            raise ValueError("prepared root occurrence has a parent")
        if sum(item.parent_id is None for item in self.occurrences) != 1:
            raise ValueError("prepared occurrences must form exactly one rooted tree")
        placement_keys: set[tuple[str, str]] = set()
        for occurrence in self.occurrences:
            if occurrence.definition_id not in definition_ids:
                raise ValueError(f"missing definition: {occurrence.definition_id}")
            if occurrence.parent_id is not None and occurrence.parent_id not in occurrence_ids:
                raise ValueError(f"missing parent occurrence: {occurrence.parent_id}")
            if occurrence.parent_id is not None:
                if occurrence.placement_key is None:
                    raise AssertionError("validated nonroot occurrence lost its placement key")
                placement = (occurrence.parent_id, occurrence.placement_key)
                if placement in placement_keys:
                    raise ValueError("duplicate prepared occurrence placement key within one physical parent")
                placement_keys.add(placement)
            if definitions[occurrence.definition_id].type_key != occurrence.type_key:
                raise ValueError("occurrence and definition type keys differ")
            seen: set[str] = set()
            cursor = occurrence
            while cursor.parent_id is not None:
                if cursor.id in seen:
                    raise ValueError("prepared occurrence parent cycle")
                seen.add(cursor.id)
                cursor = occurrences[cursor.parent_id]
        reference_parents: dict[str, list[str]] = {item.id: [] for item in self.occurrences}
        definition_owners: dict[str, list[str]] = {}
        for occurrence in self.occurrences:
            definition_owners.setdefault(occurrence.definition_id, []).append(occurrence.id)
        for definition in self.definitions:
            owners = definition_owners.get(definition.id, [])
            if not owners:
                raise ValueError("prepared definition has no occurrence owner")
            sites: set[str] = set()
            for outlet in _slot_outlets(definition.children):
                if outlet.site_id != outlet.selected.site_id or outlet.public_name != outlet.selected.public_name:
                    raise ValueError("slot outlet and selected closure identity differ")
                if re.fullmatch(r"citrySlot[0-9A-Za-z]+", outlet.site_id) is None:
                    raise ValueError("slot site id is not generated-safe")
                if outlet.site_id in sites:
                    raise ValueError("slot site id is duplicated within a definition")
                sites.add(outlet.site_id)
                if any(outlet.receiver_id != owner for owner in owners):
                    raise ValueError("slot outlet receiver is not its definition occurrence")
            for prepared_outlet in _prepared_slot_outlets(definition.children):
                if prepared_outlet.site_id in sites:
                    raise ValueError("slot site id is duplicated within a definition")
                sites.add(prepared_outlet.site_id)
            for receiver_id, lexical_id, result_id in _ownership_refs(definition.children):
                for referenced in (receiver_id, lexical_id, result_id):
                    if referenced is not None and referenced not in occurrence_ids:
                        raise ValueError(f"definition references unknown ownership occurrence: {referenced}")
            for owner_id in definition_owners.get(definition.id, []):
                owner = occurrences[owner_id]
                for child_id, placement_parent in _component_call_refs(
                    definition.children, owner.prepared_data, occurrences, owner_id
                ):
                    if child_id not in occurrence_ids:
                        raise ValueError(f"definition references unknown occurrence: {child_id}")
                    reference_parents[child_id].append(placement_parent)
        for occurrence in self.occurrences:
            references = reference_parents[occurrence.id]
            if occurrence.id == self.root_id:
                if references:
                    raise ValueError("prepared root must not be referenced as a child")
            elif occurrence.parent_id is None:
                # Only the root may lack a placement parent, so name that directly
                # instead of failing on the missing lookup in the message below.
                raise ValueError(f"nonroot occurrence {occurrence.id!r} has no placement parent")
            elif references != [occurrence.parent_id]:
                raise ValueError(
                    "nonroot occurrence must be referenced once by its placement parent: "
                    f"{occurrence.id!r}/{occurrence.type_key!r} expected "
                    f"{occurrence.parent_id!r}/{occurrences[occurrence.parent_id].type_key!r}, got "
                    f"{[(item, occurrences[item].type_key) for item in references]!r}"
                )


def replace_definition_ids(view: PreparedView, replacements: dict[str, str]) -> PreparedView:
    """Bind prepared definitions and occurrences to final compiled identities."""
    expected = {item.id for item in view.definitions}
    if set(replacements) != expected or any(type(value) is not str or not value for value in replacements.values()):
        raise ValueError("compiled definition replacements must exactly cover prepared definitions")
    if len(set(replacements.values())) != len(replacements):
        raise ValueError("compiled definition identities must be unique")
    definitions = tuple(
        PreparedDefinition(replacements[item.id], item.type_key, item.children, item.directive_signature)
        for item in view.definitions
    )
    occurrences = tuple(
        PreparedOccurrence(
            item.id,
            item.type_key,
            replacements[item.definition_id],
            item.server_data,
            item.prepared_data,
            item.parent_id,
            item.placement_key,
        )
        for item in view.occurrences
    )
    return PreparedView(view.revision, view.root_id, occurrences, definitions, view.markers)


def _component_call_refs(
    nodes: tuple[PreparedNode, ...],
    prepared_data: dict[str, object],
    occurrences: dict[str, PreparedOccurrence],
    placement_parent: str,
) -> Iterator[tuple[str, str]]:
    for node in nodes:
        if isinstance(node, ComponentCall):
            yield node.occurrence_id, placement_parent
        elif isinstance(node, LocalComponentCall):
            calls = prepared_data.get("calls")
            if type(calls) is not dict or node.local_id not in calls:
                raise ValueError(f"preparedData is missing local component call: {node.local_id}")
            binding = calls[node.local_id]
            if type(binding) is not dict or type(binding.get("id")) is not str or type(binding.get("key")) is not str:
                raise TypeError("prepared local component call binding must contain exact string id/key")
            child_id = binding["id"]
            if "parentId" not in binding:
                raise ValueError(f"preparedData local component call is missing parentId: {node.local_id}")
            bound_parent = binding["parentId"]
            if type(bound_parent) is not str:
                raise TypeError("prepared local component call parentId must be an exact string")
            yield child_id, bound_parent
            for fill in node.fills:
                yield from _component_call_refs(fill.children, prepared_data, occurrences, child_id)
        elif isinstance(node, SlotOutlet):
            lexical_data = prepared_data
            if node.selected.lexical_owner_id is not None:
                lexical_data = occurrences[node.selected.lexical_owner_id].prepared_data
            yield from _component_call_refs(node.selected.children, lexical_data, occurrences, node.receiver_id)
        elif isinstance(node, PreparedSlotOutlet):
            yield from _component_call_refs(node.fallback, prepared_data, occurrences, placement_parent)


def _ownership_refs(
    nodes: tuple[PreparedNode, ...],
) -> Iterator[tuple[str, str | None, str | None]]:
    for node in nodes:
        if isinstance(node, SlotOutlet):
            yield (
                node.receiver_id,
                node.selected.lexical_owner_id,
                node.selected.result_owner_id,
            )
            yield from _ownership_refs(node.selected.children)


def _slot_outlets(nodes: tuple[PreparedNode, ...]) -> Iterator[SlotOutlet]:
    for node in nodes:
        if isinstance(node, SlotOutlet):
            yield node
            yield from _slot_outlets(node.selected.children)


def _prepared_slot_outlets(nodes: tuple[PreparedNode, ...]) -> Iterator[PreparedSlotOutlet]:
    for node in nodes:
        if isinstance(node, PreparedSlotOutlet):
            yield node
            yield from _prepared_slot_outlets(node.fallback)
        elif isinstance(node, LocalComponentCall):
            for fill in node.fills:
                yield from _prepared_slot_outlets(fill.children)
