"""Convert typed prepared render parts into a reusable prepared component view."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import TYPE_CHECKING, TypeAlias, TypeGuard, TypeVar, cast

from citry.attrs import _html_attr_identity, validate_html_attr_name
from citry.citry_render import CitryRender, Placeholder, PreparedComponentBinding, RenderDecoration, RenderPart
from citry.client_directives import ComponentTagClientBindingKind
from citry.components.mark import validate_mark_name
from citry.constness import const_value, is_const
from citry.util.html import Markup

from .capture import (
    PreparedDynamicElementClose,
    PreparedDynamicElementOpen,
    PreparedElementClose,
    PreparedElementOpen,
    PreparedSourceText,
    PreparedStaticRun,
    PreparedTextValue,
    PreparedTrustedHtmlValue,
    PreparedVerbatimHtml,
    StaticRunOpening,
    is_authenticated_browser_binding,
    is_authenticated_dynamic_element_open,
    is_native_state_tag,
    vue_owned_native_marker,
    vue_owned_native_properties,
)
from .compiler import (
    DefinitionCompileInput,
    _DynamicElementDeclaration,
    _ElementBindingDeclaration,
    _generated_event_args,
    _generated_vue_attr,
    _LocalCallBindingDeclaration,
    _LocalCallDeclaration,
    _LocalCallRunDeclaration,
    _OpaqueHtmlDeclaration,
    _RuntimeEventDeclaration,
    _vue_attribute_escape,
)
from .direct import (
    DirectCallRunRender,
    DirectNestedTemplateRender,
    DirectProjectionRender,
    DirectPythonComponentRender,
)
from .leaf_program import (
    PreparedLeafProgram,
)
from .leaf_program import (
    _Close as _LeafClose,
)
from .leaf_program import (
    _For as _LeafFor,
)
from .leaf_program import (
    _If as _LeafIf,
)
from .leaf_program import (
    _Open as _LeafOpen,
)
from .leaf_program import (
    _Static as _LeafStatic,
)
from .leaf_program import (
    _Text as _LeafText,
)
from .opaque_html import mark_opaque_html, reject_cross_boundary_html
from .prepared import (
    PreparedMarker,
    PreparedOccurrence,
    RuntimeDirective,
)

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.citry_context import CitryContext
    from citry.component import Component

TagForType = Callable[[str], str]
ComponentMetadataForType = Callable[[str, type[object] | None], str]


@dataclass(frozen=True, slots=True)
class Assembly:
    """One selected-tree pass result shared by the compiler and extensions."""

    view: AssembledView
    render_to_occurrence: Mapping[str, str]
    occurrence_to_render: Mapping[str, str]
    compile_inputs: Mapping[str, DefinitionCompileInput]


@dataclass(frozen=True, slots=True)
class _AssembledDefinition:
    """Protocol identity for a definition whose compiler input is held by Assembly."""

    id: str
    type_key: str
    directive_signature: tuple[RuntimeDirective, ...] = ()


@dataclass(frozen=True, slots=True)
class AssembledView:
    """Production wire view whose definitions are backed by Assembly compiler inputs."""

    revision: int
    root_id: str
    occurrences: tuple[PreparedOccurrence, ...]
    definitions: tuple[_AssembledDefinition, ...]
    markers: tuple[PreparedMarker, ...] = ()


class UnsupportedPreparedView(TypeError):
    pass


@dataclass(frozen=True, slots=True)
class _CacheReplayIdentity:
    """Registry identity retained from validated cache decoding."""

    citry: Citry
    component_class: type[Component]


_CACHE_REPLAY_IDENTITY_KEY = object()


def _issue_cache_replay_identity(
    context: CitryContext,
    citry: Citry,
    component_class: type[Component],
) -> None:
    """Attach decoder-validated identity to one detached occurrence context."""
    if getattr(context, "component", None) is not None:
        raise TypeError("cache replay identity requires a componentless context")
    class_id = getattr(component_class, "class_id", None)
    try:
        current_class = None if not class_id else citry.get_component_by_class_id(class_id)
    except KeyError:
        current_class = None
    if current_class is not component_class:
        raise TypeError("cache replay identity requires the current exact registry class")
    cast("dict[object, object]", context.extra)[_CACHE_REPLAY_IDENTITY_KEY] = _CacheReplayIdentity(
        citry, component_class
    )


def _matches_cache_replay_identity(
    context: CitryContext,
    citry: Citry,
    component_class: type[Component],
) -> bool:
    if getattr(context, "component", None) is not None:
        return False
    token = getattr(context, "extra", {}).get(_CACHE_REPLAY_IDENTITY_KEY)
    if type(token) is not _CacheReplayIdentity:
        return False
    if token.citry is not citry or token.component_class is not component_class:
        return False
    try:
        return citry.get_component_by_class_id(component_class.class_id) is component_class
    except KeyError:
        return False


def _run_eligible_component(value: object) -> TypeGuard[CitryRender]:
    """Whether one selected child has the exact bounded call-run proof."""
    if type(value) is not CitryRender or not value.frame.is_component_root:
        return False
    prepared = value.frame.prepared_occurrence
    metadata = prepared.call if prepared is not None else None
    return bool(
        metadata is not None
        and getattr(metadata, "slot_free_body", False) is True
        and type(metadata.source) is str
        and type(metadata.source_span) is tuple
        and type(metadata.explicit_key) is str
        and prepared is not None
        and not prepared.raw_slots_present
        and not prepared.component_tag_client_bindings
        and value.frame.class_id
    )


@dataclass(slots=True)
class _DefinitionFragment:
    """Compiler text plus byte-relative metadata, assembled in one selected-tree visit."""

    chunks: list[str]
    byte_length: int
    local_calls: list[_LocalCallDeclaration]
    element_bindings: list[_ElementBindingDeclaration]
    local_call_runs: list[_LocalCallRunDeclaration]
    dynamic_elements: list[_DynamicElementDeclaration]
    opaque_html_sites: list[_OpaqueHtmlDeclaration]
    runtime_event_sites: list[_RuntimeEventDeclaration]

    @classmethod
    def empty(cls) -> _DefinitionFragment:
        return cls([], 0, [], [], [], [], [], [])

    def append(self, text: str) -> None:
        self.chunks.append(text)
        self.byte_length += len(text.encode())

    def extend(self, other: _DefinitionFragment) -> None:
        offset = self.byte_length
        self.chunks.extend(other.chunks)
        self.byte_length += other.byte_length
        self.local_calls.extend(_rebase_metadata(other.local_calls, offset))
        self.element_bindings.extend(_rebase_metadata(other.element_bindings, offset))
        self.local_call_runs.extend(_rebase_metadata(other.local_call_runs, offset))
        self.dynamic_elements.extend(_rebase_metadata(other.dynamic_elements, offset))
        self.opaque_html_sites.extend(_rebase_metadata(other.opaque_html_sites, offset))
        self.runtime_event_sites.extend(_rebase_metadata(other.runtime_event_sites, offset))

    def compile_input(self, template_context_names: tuple[str, ...] = ()) -> DefinitionCompileInput:
        return DefinitionCompileInput(
            "".join(self.chunks),
            cast("tuple[dict[str, object], ...]", tuple(self.local_calls)),
            cast("tuple[dict[str, object], ...]", tuple(self.element_bindings)),
            cast("tuple[dict[str, object], ...]", tuple(self.local_call_runs)),
            cast("tuple[dict[str, object], ...]", tuple(self.dynamic_elements)),
            template_context_names,
            cast("tuple[dict[str, object], ...]", tuple(self.opaque_html_sites)),
            cast("tuple[dict[str, object], ...]", tuple(self.runtime_event_sites)),
        )


@dataclass(slots=True)
class _SlotKeyScope:
    """One active keyed element whose slot descendants need stable VNode keys."""

    expression: str
    ordinal: int = 0


@dataclass(frozen=True, slots=True)
class _FillFragment:
    site_id: str
    public_name: str
    lexical_owner: str
    body: _DefinitionFragment


_AUTHORED_VUE_BINDING = re.compile(r"^(?:v-|:|@|#)")


def _has_authored_vue_binding(attributes: object) -> bool:
    """Return whether structured attributes contain an authored Vue binding."""
    return any(
        getattr(attribute, "origin", None) == "source"
        and _AUTHORED_VUE_BINDING.match(str(getattr(attribute, "name", "")))
        for attribute in tuple(attributes or ())
    )


class _VueBindingAttributeParser(HTMLParser):
    """Find Vue binding names in opening tags, never in ordinary text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.found = False

    def _inspect(self, attributes: list[tuple[str, str | None]]) -> None:
        self.found = self.found or any(_AUTHORED_VUE_BINDING.match(name) for name, _ in attributes)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        self._inspect(attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        self._inspect(attrs)


def _contains_vue_binding_in_template(template: str) -> bool:
    parser = _VueBindingAttributeParser()
    parser.feed(template)
    parser.close()
    return parser.found


def _structured_leaf_vue_binding(value: object) -> tuple[bool, bool]:
    """Return ``(metadata_complete, has_binding)`` for leaf operations."""
    if isinstance(value, (tuple, list)):
        results = [_structured_leaf_vue_binding(item) for item in value]
        return all(complete for complete, _ in results), any(found for _, found in results)
    if isinstance(value, _LeafOpen):
        return True, _has_authored_vue_binding(value.authored_attributes)
    if isinstance(value, (_LeafStatic, _LeafText, _LeafClose)):
        return True, False
    if isinstance(value, _LeafIf):
        complete, found = _structured_leaf_vue_binding(value.branches)
        return complete, found
    if isinstance(value, _LeafFor):
        body_complete, body_found = _structured_leaf_vue_binding(value.body)
        empty_complete, empty_found = _structured_leaf_vue_binding(value.empty)
        return body_complete and empty_complete, body_found or empty_found
    return False, False


def _contains_authored_vue_binding(parts: Sequence[RenderPart]) -> bool:
    """Whether projected authored markup needs its lexical Vue scope."""
    for part in parts:
        if isinstance(part, PreparedElementOpen):
            if _has_authored_vue_binding(part.attrs):
                return True
            continue
        if isinstance(part, PreparedDynamicElementOpen):
            if _has_authored_vue_binding(part.authored_attrs):
                return True
            continue
        if isinstance(part, PreparedLeafProgram):
            metadata_complete, has_binding = _structured_leaf_vue_binding(part.operations)
            if has_binding or (not metadata_complete and _contains_vue_binding_in_template(part.fragment.template)):
                return True
            continue
        if isinstance(part, (CitryRender, RenderDecoration)):
            # A nested component owns its own Vue scope. Its internal
            # directives must not force the containing projection to move out
            # of the physical definition.
            if part.frame.is_component_root:
                continue
            if _contains_authored_vue_binding(tuple(part.parts)):
                return True
    return False


@dataclass(frozen=True, slots=True)
class _LeafDefinitionArtifact:
    definition_id: str
    compile_input: DefinitionCompileInput


_RebasableMetadata: TypeAlias = (
    _LocalCallDeclaration
    | _ElementBindingDeclaration
    | _LocalCallRunDeclaration
    | _DynamicElementDeclaration
    | _OpaqueHtmlDeclaration
    | _RuntimeEventDeclaration
)

# citry supports Python 3.10, so the generic is spelled with an explicit TypeVar
# rather than the 3.12 type-parameter syntax, which is a syntax error on 3.10/3.11.
_RebasableMetadataT = TypeVar("_RebasableMetadataT", bound=_RebasableMetadata)


def _rebase_metadata(values: list[_RebasableMetadataT], offset: int) -> list[_RebasableMetadataT]:
    return cast(
        "list[_RebasableMetadataT]",
        [
            {
                **value,
                "sourceStart": value["sourceStart"] + offset,
                "sourceEnd": value["sourceEnd"] + offset,
                **(
                    {
                        "bindings": [
                            {
                                **binding,
                                "sourceStart": binding["sourceStart"] + offset,
                                "sourceEnd": binding["sourceEnd"] + offset,
                            }
                            for binding in cast("_LocalCallDeclaration", value)["bindings"]
                        ]
                    }
                    if "bindings" in value
                    else {}
                ),
                **(
                    {
                        "loopSourceStart": cast("_LocalCallRunDeclaration", value)["loopSourceStart"] + offset,
                        "loopSourceEnd": cast("_LocalCallRunDeclaration", value)["loopSourceEnd"] + offset,
                    }
                    if "loopSourceStart" in value
                    else {}
                ),
            }
            for value in values
        ],
    )


def _json_plain(value: object, _ancestors: set[int] | None = None) -> object:
    if is_const(value):
        return _json_plain(const_value(value), _ancestors)
    from citry.ext.i18n.bindings import CapturedTranslationText  # noqa: PLC0415

    if type(value) is CapturedTranslationText:
        return str(value)
    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("prepared Vue data must contain only finite numbers")
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("prepared Vue data object keys must be strings")
        ancestors = set() if _ancestors is None else _ancestors
        if id(value) in ancestors:
            raise ValueError("prepared Vue data must not contain a cycle")
        ancestors.add(id(value))
        try:
            return {str(key): _json_plain(item, ancestors) for key, item in value.items()}
        finally:
            ancestors.remove(id(value))
    if isinstance(value, (list, tuple)):
        ancestors = set() if _ancestors is None else _ancestors
        if id(value) in ancestors:
            raise ValueError("prepared Vue data must not contain a cycle")
        ancestors.add(id(value))
        try:
            return [_json_plain(item, ancestors) for item in value]
        finally:
            ancestors.remove(id(value))
    raise TypeError(f"prepared Vue data must be strict JSON, got {type(value).__name__}")


def _json_attribute_map(values: Mapping[str, object]) -> dict[str, object]:
    """
    Encode resolved HTML attributes for Vue's object binding.

    Keep JSON booleans intact. Vue's object binding serializes a custom
    attribute whose value is ``true`` as ``"true"``; converting it to the
    empty string here would change the public prepared-attribute contract.
    """
    return {name: _json_plain(value) for name, value in values.items()}


def _json_presence_attribute_map(values: Mapping[str, object]) -> dict[str, object]:
    """Encode internal presence-only root markers for Vue's object binding."""
    return {name: "" if (plain := _json_plain(value)) is True else plain for name, value in values.items()}


def assemble_typed_render(
    render: CitryRender,
    *,
    revision: int,
    tag_for_type: TagForType,
    component_metadata_for_type: ComponentMetadataForType | None = None,
    server_data: Mapping[str, Mapping[str, object]] | None = None,
    root_occurrence_id: str | None = None,
    template_context_names: tuple[str, ...] = (),
    expected_citry: object | None = None,
) -> Assembly:
    """Assemble the final view, render map, and native compiler inputs together."""
    from citry._simple_runtime import SimpleRender  # noqa: PLC0415

    if render.render_target != "prepared":
        raise UnsupportedPreparedView("direct capture requires a prepared render")
    if type(revision) is not int or revision < 0:
        raise ValueError("prepared revision must be a nonnegative exact integer")
    root_component = render.context.component
    if root_component is None:
        raise UnsupportedPreparedView("prepared root has no current component registry")
    citry = root_component.citry
    if expected_citry is not None and citry is not expected_citry:
        raise UnsupportedPreparedView("prepared root belongs to a different Citry engine")
    mark_class = citry.get("mark")
    if not citry._is_builtin_component(mark_class) or mark_class.name != "mark":
        raise UnsupportedPreparedView("prepared marker built-in identity is invalid")
    from citry.browser_render import _validate_template_context_names  # noqa: PLC0415

    _validate_template_context_names(template_context_names, "Prepared")
    occurrence_fields: list[tuple[str, str, str | None, str | None, Mapping[str, object], dict[str, object]]] = []
    occurrence_definition_ids: list[str | None] = []
    compile_inputs: dict[str, DefinitionCompileInput] = {}
    definitions: dict[str, _AssembledDefinition] = {}
    render_to_occurrence: dict[str, str] = {}
    occurrence_to_render: dict[str, str] = {}
    prepared_by_occurrence: dict[str, dict[str, object]] = {}
    occurrence_types: dict[str, str] = {}
    occurrence_parents: dict[str, str | None] = {}
    occurrence_placement_keys: dict[str, str | None] = {}
    reference_parents: defaultdict[str, list[str]] = defaultdict(list)
    binding_counts_by_owner: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    call_counts_by_owner: defaultdict[str, defaultdict[tuple[object, ...], int]] = defaultdict(
        lambda: defaultdict(int)
    )
    seen_render_ids: set[str] = set()
    seen_occurrence_ids: set[str] = set()
    flattened_transparent_receivers: set[str] = set()
    # A flattened projection can copy lexical bindings into a physical
    # occurrence before that occurrence emits its own bindings.  Keep the
    # physical namespace reservations separate from the lexical counters so a
    # later physical binding cannot reuse a copied key.
    projected_data_keys_by_occurrence: defaultdict[str, set[str]] = defaultdict(set)
    supplied_fills: defaultdict[str, list[_FillFragment]] = defaultdict(list)
    tags_by_type: dict[str, str] = {}
    types_by_tag: dict[str, str] = {}
    leaf_artifacts: dict[tuple[str, int], _LeafDefinitionArtifact] = {}
    markers: list[PreparedMarker] = []

    context_binding_attrs = "".join(f' :{name}="{name}"' for name in template_context_names)
    context_binding_pattern = "" if not template_context_names else '="{ ' + ", ".join(template_context_names) + ' }"'

    def attach_leaf_data(
        part: PreparedLeafProgram,
        data_values: dict[str, object],
        projected_data_keys: set[str] | None = None,
    ) -> None:
        if part.vue_errors:
            raise UnsupportedPreparedView(part.vue_errors[0])
        for key, prepared_value in part.prepared_data.items():
            if key in data_values:
                raise UnsupportedPreparedView("duplicate prepared leaf-program binding key")
            data_values[key] = _json_plain(prepared_value)
            if projected_data_keys is not None:
                projected_data_keys.add(key)

    def merge_projected_data(
        lexical_values: dict[str, object],
        physical_values: dict[str, object],
        keys: set[str],
        containers: set[str],
        physical_occurrence_id: str,
    ) -> None:
        """Expose lexical bindings in a definition that flattened their body."""
        reserved_keys = projected_data_keys_by_occurrence[physical_occurrence_id]
        for key in keys:
            if key in {"calls", "callRuns", "selectedSlots"} or key not in lexical_values:
                continue
            value = lexical_values[key]
            if key not in physical_values:
                physical_values[key] = _json_plain(value)
                reserved_keys.add(key)
                continue
            if physical_values[key] == value:
                if key in reserved_keys:
                    continue
                raise UnsupportedPreparedView(f"flattened projection reused a physical prepared binding key: {key!r}")
            raise UnsupportedPreparedView(
                f"flattened projection reused a prepared binding key with conflicting physical data: {key!r}"
            )
        for name in containers:
            if name in {"calls", "callRuns", "selectedSlots"} or name not in lexical_values:
                continue
            value = lexical_values[name]
            if type(value) is not dict:
                raise AssertionError(f"prepared projected {name} container changed type")
            existing = physical_values.setdefault(name, {})
            if type(existing) is not dict:
                raise UnsupportedPreparedView(
                    f"flattened projection reused a prepared container with conflicting physical data: {name!r}"
                )
            for nested_key, item in value.items():
                prior = existing.setdefault(nested_key, _json_plain(item))
                if prior != item:
                    raise UnsupportedPreparedView(
                        "flattened projection reused a prepared container entry with conflicting physical data: "
                        f"{name}.{nested_key}"
                    )

    def component_tag(type_key: str, rendered_class: type[object] | None = None) -> str:
        tag = _checked_component_tag(
            type_key,
            tag_for_type
            if component_metadata_for_type is None
            else lambda value: component_metadata_for_type(value, rendered_class),
        )
        prior_tag = tags_by_type.setdefault(type_key, tag)
        if prior_tag != tag:
            raise UnsupportedPreparedView("component tag mapping is not deterministic")
        prior_type = types_by_tag.setdefault(tag, type_key)
        if prior_type != type_key:
            raise UnsupportedPreparedView("component tag mapping is not injective")
        return tag

    def transform_component(
        value: CitryRender,
        parent_id: str | None,
        occurrence_id: str,
        placement_key: str | None = None,
        inherited_root_markers: tuple[tuple[str, object], ...] = (),
        physical_parent_stack: tuple[str, ...] = (),
        marker_owner_id: str | None = None,
    ) -> str:
        frame = value.frame
        selected_transparent_root = parent_id is None and frame.is_transparent_root
        ordinary_component_root = frame.is_component_root and not frame.is_transparent_root
        if not (selected_transparent_root or ordinary_component_root) or frame.render_id is None:
            raise UnsupportedPreparedView("prepared component must be a nontransparent component root")
        if frame.render_id in seen_render_ids:
            raise UnsupportedPreparedView("render occurrence appears more than once")
        if occurrence_id in seen_occurrence_ids:
            raise UnsupportedPreparedView("prepared occurrence identity collided")
        seen_render_ids.add(frame.render_id)
        seen_occurrence_ids.add(occurrence_id)
        occurrence_to_render[occurrence_id] = frame.render_id
        raw_frame_data: object = value.context.js_data
        if server_data is not None:
            if frame.render_id not in server_data:
                raise UnsupportedPreparedView("component occurrence has no captured js_data")
            raw_frame_data = server_data[frame.render_id]
        if raw_frame_data is None:
            raise UnsupportedPreparedView("component occurrence has no captured js_data")
        frame_data = _json_plain(raw_frame_data)
        if type(frame_data) is not dict:
            raise TypeError("component occurrence js_data must be a JSON object")
        type_key = frame.class_id
        if not type_key:
            raise UnsupportedPreparedView("component occurrence has no stable class id")
        try:
            component_class = citry.get_component_by_class_id(type_key)
        except KeyError as error:
            raise UnsupportedPreparedView("component occurrence has no current registered class") from error
        component_tag(type_key, component_class)
        live_component = value.context.component
        live_identity = (
            live_component is not None and live_component.citry is citry and type(live_component) is component_class
        )
        if not live_identity and not _matches_cache_replay_identity(value.context, citry, component_class):
            raise UnsupportedPreparedView("prepared component does not match its engine registry identity")
        if component_class is mark_class:
            if not live_identity:
                raise UnsupportedPreparedView("prepared marker lost its engine-owned component identity")
            marker_name = validate_mark_name(getattr(live_component, "_citry_mark_name", None))
            if not getattr(live_component, "_citry_mark_replacement", False):
                markers.append(PreparedMarker(marker_owner_id or occurrence_id, marker_name, occurrence_id))
        prepared_values: dict[str, object] = {"calls": {}}
        prepared_by_occurrence[occurrence_id] = prepared_values
        occurrence_types[occurrence_id] = type_key
        occurrence_parents[occurrence_id] = parent_id
        occurrence_placement_keys[occurrence_id] = placement_key
        occurrence_index = len(occurrence_fields)
        occurrence_fields.append((occurrence_id, type_key, parent_id, placement_key, frame_data, prepared_values))
        occurrence_definition_ids.append(None)
        render_to_occurrence[frame.render_id] = occurrence_id
        local_identity_keys: set[tuple[tuple[object, ...], tuple[str, ...], object]] = set()
        # Transparent roots keep their own key namespace: the wrapper we emit for a
        # transparent render sits at the same source span and route as the ordinary
        # call it wraps, so sharing `local_identity_keys` would reject that pair as a
        # duplicate even though only one of them owns the key.
        local_transparent_identity_keys: set[tuple[tuple[object, ...], tuple[str, ...], object]] = set()
        python_counts_by_route: defaultdict[tuple[str, ...], int] = defaultdict(int)
        slot_site_counts: defaultdict[tuple[tuple[object, ...], tuple[str, ...]], int] = defaultdict(int)
        dynamic_site_index = 0
        active_projected_data_keys: list[set[str] | None] = []
        active_projected_data_containers: list[set[str] | None] = []
        own_root_markers = _prepared_root_markers((*frame.root_markers, *value.context._get_root_markers()))
        root_marker_values = dict(own_root_markers)
        marker_identities = {_html_attr_identity(name) for name in root_marker_values}
        for name, marker_value in inherited_root_markers:
            identity = _html_attr_identity(name)
            if identity not in marker_identities:
                root_marker_values[name] = marker_value
                marker_identities.add(identity)
        root_markers = tuple(root_marker_values.items())

        def data_key(prefix: str, source: str, span: tuple[int, int], owner_id: str) -> str:
            del source, span
            binding_counts = binding_counts_by_owner[owner_id]
            index = binding_counts[prefix]
            binding_counts[prefix] += 1
            key = f"citry{prefix}{index}"
            projected = (
                owner_id != occurrence_id and active_projected_data_keys and active_projected_data_keys[-1] is not None
            )
            physical_values = prepared_by_occurrence[occurrence_id]
            reserved_keys = projected_data_keys_by_occurrence[occurrence_id]
            if owner_id == occurrence_id:
                # Leaf data and an earlier flattened projection may already
                # occupy this compact key. Advance the physical owner counter
                # rather than aliasing two independently changing values.
                while key in physical_values or key in reserved_keys:
                    index = binding_counts[prefix]
                    binding_counts[prefix] += 1
                    key = f"citry{prefix}{index}"
            elif projected:
                if key in physical_values or key in reserved_keys:
                    # The lexical owner already uses this compact ordinal in
                    # its own namespace, but the physical definition cannot
                    # reuse it. Keep the ordinary key when possible and use a
                    # deterministic owner/occurrence suffix only on collision.
                    key = f"citry{prefix}p{_digest(occurrence_id, owner_id, prefix, index)[:20]}"
                    suffix = 0
                    while key in physical_values or key in reserved_keys:
                        suffix += 1
                        key = f"citry{prefix}p{_digest(occurrence_id, owner_id, prefix, index, suffix)[:20]}"
                reserved_keys.add(key)
                projected_keys = active_projected_data_keys[-1]
                if projected_keys is not None:
                    projected_keys.add(key)
            return key

        def projected_data_container(name: str) -> None:
            if active_projected_data_containers:
                projected_containers = active_projected_data_containers[-1]
                if projected_containers is not None:
                    projected_containers.add(name)

        def validate_flattened_render_identity(part: CitryRender, label: str) -> None:
            if type(part) is SimpleRender:
                scope = part.context._simple_scope
                simple_class = None if scope is None else scope.component_class
                if simple_class is None:
                    raise UnsupportedPreparedView("prepared simple render has no simple component class")
                try:
                    registered_simple = citry.get_component_by_class_id(simple_class.class_id)
                except KeyError as error:
                    raise UnsupportedPreparedView(
                        "prepared simple render has no class in the encoding engine"
                    ) from error
                if simple_class.citry is not citry or registered_simple is not simple_class:
                    raise UnsupportedPreparedView("prepared simple render belongs to a different engine or class")
            component = part.context.component
            if component is None:
                return
            try:
                registered = citry.get_component_by_class_id(part.frame.class_id or "")
            except KeyError as error:
                raise UnsupportedPreparedView(
                    f"prepared {label} render has no class in the encoding engine"
                ) from error
            if component.citry is not citry or registered is not type(component):
                raise UnsupportedPreparedView(f"prepared {label} render belongs to a different engine or class")

        def append_child_fills(
            output: _DefinitionFragment,
            fills: tuple[_FillFragment, ...],
            *,
            definition_owner_id: str,
            slot_key_scopes: Sequence[_SlotKeyScope] = (),
        ) -> None:
            if len({fill.site_id for fill in fills}) != len(fills):
                raise UnsupportedPreparedView("prepared component call has duplicate supplied fill sites")
            for fill in fills:
                output.append(f"<template v-slot:['{fill.site_id}']{context_binding_pattern}>")
                if fill.lexical_owner == definition_owner_id:
                    output.extend(fill.body)
                else:
                    ancestor = occurrence_id
                    visited: set[str] = set()
                    while ancestor != fill.lexical_owner:
                        if ancestor in visited:
                            raise UnsupportedPreparedView("prepared component ancestry contains a cycle")
                        visited.add(ancestor)
                        parent = occurrence_parents.get(ancestor)
                        if parent is None:
                            raise UnsupportedPreparedView(
                                "deferred direct slot lexical owner is not an ancestor of its receiver"
                            )
                        ancestor = parent
                    supplied_fills[occurrence_id].append(fill)
                    output.append(
                        f'<slot name="{fill.site_id}"{context_binding_attrs}'
                        f"{_slot_key_attr(_next_slot_key(slot_key_scopes))}></slot>"
                    )
                output.append("</template>")

        def receiver_placement_path(receiver_owner: str, lexical_owner: str) -> tuple[str, ...] | None:
            """Return a receiver's stable path below its lexical owner."""
            if receiver_owner == lexical_owner:
                return ()
            path: list[str] = []
            cursor = receiver_owner
            visited: set[str] = set()
            while cursor != lexical_owner:
                if cursor in visited:
                    raise UnsupportedPreparedView("prepared component ancestry contains a cycle")
                visited.add(cursor)
                parent = occurrence_parents.get(cursor)
                placement_key = occurrence_placement_keys.get(cursor)
                if parent is None or placement_key is None:
                    return None
                path.append(placement_key)
                cursor = parent
            path.reverse()
            return tuple(path)

        def transform_parts(
            parts: Sequence[RenderPart],
            *,
            placement_route: tuple[str, ...] = (),
            data_owner_id: str = occurrence_id,
            call_owner_id: str = occurrence_id,
            containing_slot: DirectProjectionRender | None = None,
            call_run: DirectCallRunRender | None = None,
            project_root_markers: bool = True,
            parent_element_stack: tuple[str, ...] = (),
            projected_data: bool = False,
            slot_key_scopes: Sequence[_SlotKeyScope] = (),
        ) -> _DefinitionFragment:
            nonlocal dynamic_site_index
            output = _DefinitionFragment.empty()
            dynamic_stack: list[tuple[str, str]] = []
            element_stack = list(parent_element_stack)
            inherited_element_depth = len(element_stack)
            element_key_scopes: list[_SlotKeyScope | None] = [None] * inherited_element_depth
            active_slot_key_scopes = list(slot_key_scopes)
            dom_depth = 0
            data_values = prepared_by_occurrence[data_owner_id]
            projected_keys: set[str] | None = set() if projected_data and data_owner_id != occurrence_id else None
            projected_containers: set[str] | None = (
                set() if projected_data and data_owner_id != occurrence_id else None
            )
            active_projected_data_keys.append(projected_keys)
            active_projected_data_containers.append(projected_containers)
            # A projected body keeps the lexical data owner for values, but its
            # component declarations and prepared call bindings belong to the
            # definition that receives the body.  These owners coincide for an
            # ordinary component body and diverge only while a transparent
            # projection is being folded into another definition.
            call_values = prepared_by_occurrence[call_owner_id]
            run_first: dict[int, list[CitryRender]] = {}
            run_followers: set[int] = set()

            if call_run is not None:
                if (
                    data_owner_id != occurrence_id
                    or call_owner_id != occurrence_id
                    or placement_route
                    or containing_slot is not None
                ):
                    raise UnsupportedPreparedView("prepared call run crossed its component body boundary")
                call_node = call_run.call_node
                matching = not root_markers and all(
                    _run_eligible_component(candidate)
                    and candidate.frame.class_id == call_run.child_type_key
                    and candidate.frame.prepared_occurrence is not None
                    and candidate.frame.prepared_occurrence.call is not None
                    and candidate.frame.prepared_occurrence.call.source is call_node.source
                    and candidate.frame.prepared_occurrence.call.source_span == call_node.position
                    for candidate in parts
                )
                if not matching:
                    return transform_parts(
                        parts,
                        placement_route=placement_route,
                        data_owner_id=data_owner_id,
                        call_owner_id=call_owner_id,
                        containing_slot=containing_slot,
                        project_root_markers=project_root_markers,
                        parent_element_stack=tuple(element_stack),
                        projected_data=projected_data,
                        slot_key_scopes=tuple(active_slot_key_scopes),
                    )
                if parts:
                    run_first[0] = [candidate for candidate in parts if _run_eligible_component(candidate)]
                    run_followers.update(range(1, len(parts)))
                else:
                    run_values = call_values.setdefault("callRuns", {})
                    if type(run_values) is not dict:
                        raise AssertionError("prepared callRuns container changed type")
                    run_id = f"citryRun{len(run_values)}"
                    run_values[run_id] = []
                    tag = component_tag(call_run.child_type_key)
                    start = output.byte_length
                    output.append(
                        f'<component v-for="citryOccurrenceId in preparedData.callRuns.{run_id}" '
                        f':is="\'{tag}\'" :citry-id="citryOccurrenceId" :key="citryOccurrenceId">'
                    )
                    source_end = output.byte_length
                    output.append("</component>")
                    output.local_call_runs.append(
                        {
                            "runId": run_id,
                            "typeKey": call_run.child_type_key,
                            "componentTag": tag,
                            "sourceStart": start,
                            "sourceEnd": source_end,
                            "loopSourceStart": start,
                            "loopSourceEnd": source_end,
                        }
                    )

            for part_index, part in enumerate(parts):
                if part_index in run_followers:
                    continue
                if isinstance(part, DirectProjectionRender):
                    nested_template = isinstance(part, DirectNestedTemplateRender)
                    fill_source = part.fill_source
                    if not isinstance(fill_source.source, str):
                        raise UnsupportedPreparedView("direct slot source must be template text")
                    receiver_owner = _stable_owner(part.receiver_render_id, render_to_occurrence)
                    if receiver_owner is None:
                        raise UnsupportedPreparedView("direct slot ownership has no prepared occurrence")
                    lexical_owner = _stable_owner(fill_source.lexical_render_id, render_to_occurrence)
                    if lexical_owner is None:
                        raise UnsupportedPreparedView("direct slot ownership has no prepared occurrence")
                    relative_receiver_path = receiver_placement_path(receiver_owner, lexical_owner)
                    source_key = (
                        occurrence_types[occurrence_id],
                        fill_source.kind,
                        part.source,
                        part.span,
                        receiver_owner,
                    )
                    if not placement_route or receiver_owner == occurrence_id:
                        # A slot site is part of the receiver's reusable
                        # definition.  Occurrence IDs are unique per
                        # instance, so an unscoped site and a site rooted at
                        # the current component receiver must use the stable
                        # receiver type in their identity.
                        receiver_type = occurrence_types.get(receiver_owner)
                        if receiver_type is None:
                            raise UnsupportedPreparedView("direct slot receiver has no prepared component type")
                        source_key = (*source_key[:-1], receiver_type)
                    # The reusable definition being assembled must not inherit
                    # the receiver's path under its lexical caller.  That
                    # path distinguishes flattened descendants when they are
                    # projected into another definition, but it would make
                    # ordinary instances of the same component produce
                    # occurrence-specific definitions.
                    if relative_receiver_path is not None and receiver_owner != occurrence_id:
                        source_key = (*source_key, relative_receiver_path)
                    site_identity = (source_key, placement_route)
                    site_index = slot_site_counts[site_identity]
                    slot_site_counts[site_identity] += 1
                    # Keep the ordinal scoped by the transparent placement
                    # route and the receiver path relative to the lexical
                    # owner, so sibling wrappers retain distinct stable sites
                    # when their keyed order changes.
                    site_digest = (
                        _digest(source_key, site_index)
                        if not placement_route
                        else _digest(source_key, placement_route, site_index)
                    )
                    site_id = f"citrySlot{site_digest[:16]}"
                    flattened_transparent_receiver = (
                        not nested_template and part.receiver_render_id in flattened_transparent_receivers
                    )
                    # The selection predicate below is emitted into the
                    # current fragment. A supplied outer slot can project that
                    # fragment into its lexical owner's definition, so store
                    # the value in the preparedData context that evaluates it.
                    # When the result moves to a different receiver, that
                    # receiver still owns the eventual outlet predicate.
                    if not nested_template and not flattened_transparent_receiver:
                        selection_owner = receiver_owner if receiver_owner != occurrence_id else data_owner_id
                        selection_data = prepared_by_occurrence[selection_owner]
                        selected_slots = selection_data.setdefault("selectedSlots", {})
                        if type(selected_slots) is not dict:
                            raise AssertionError("prepared selectedSlots container changed type")
                        selection = "fallback" if lexical_owner == receiver_owner else "supplied"
                        previous_selection = selected_slots.setdefault(site_id, selection)
                        if previous_selection != selection:
                            raise UnsupportedPreparedView("one prepared slot site selected conflicting sources")
                    selected = transform_parts(
                        list(part.parts),
                        placement_route=(*placement_route, site_id),
                        data_owner_id=lexical_owner,
                        # A flattened transparent receiver contributes its
                        # selected body directly to this definition.  A real
                        # receiver instead carries a supplied fill back to its
                        # lexical caller, where Vue creates the slot closure.
                        # Keep those destinations separate from the lexical
                        # value owner: using the intermediate receiver here
                        # makes every forwarded call declaration land in the
                        # wrong preparedData.calls table.
                        call_owner_id=occurrence_id if flattened_transparent_receiver else lexical_owner,
                        containing_slot=part,
                        project_root_markers=project_root_markers and dom_depth == 0,
                        parent_element_stack=tuple(element_stack),
                        projected_data=projected_data or flattened_transparent_receiver,
                        slot_key_scopes=tuple(active_slot_key_scopes),
                    )
                    if flattened_transparent_receiver:
                        if lexical_owner == occurrence_id or not _contains_authored_vue_binding(tuple(part.parts)):
                            output.extend(selected)
                            continue

                        # A transparent receiver can be folded into a
                        # physical definition without making its authored
                        # body part of that definition's Vue scope.  Keep
                        # the body as a native slot closure owned by the
                        # lexical caller.  This is the same relationship we
                        # use for an ordinary supplied fill; the only
                        # difference is that the transparent receiver has no
                        # component tag at which to emit the outlet.
                        selected_slots = prepared_by_occurrence[occurrence_id].setdefault("selectedSlots", {})
                        if type(selected_slots) is not dict:
                            raise AssertionError("prepared selectedSlots container changed type")
                        previous_selection = selected_slots.setdefault(site_id, "supplied")
                        if previous_selection != "supplied":
                            raise UnsupportedPreparedView("one prepared slot site selected conflicting sources")
                        supplied_fills[occurrence_id].append(
                            _FillFragment(site_id, part.public_name, lexical_owner, selected)
                        )
                        _append_slot_outlet(
                            output,
                            site_id,
                            _DefinitionFragment.empty(),
                            context_binding_attrs,
                            _next_slot_key(active_slot_key_scopes),
                        )
                        continue
                    fill = _FillFragment(site_id, part.public_name, lexical_owner, selected)
                    output_owner = (
                        data_owner_id
                        if containing_slot is not None
                        # A fallback body belongs to its receiver. Once an
                        # enclosing projection has carried it into that
                        # receiver's data scope, emit it there. A supplied
                        # fill still belongs to its caller and must continue
                        # through the ordinary forwarding path.
                        and fill_source.kind == "fallback"
                        and receiver_owner == data_owner_id
                        else occurrence_id
                    )
                    if receiver_owner != output_owner:
                        if containing_slot is None:
                            raise UnsupportedPreparedView("direct slot result moved outside its receiver")
                        containing_lexical = _stable_owner(
                            containing_slot.fill_source.lexical_render_id, render_to_occurrence
                        )
                        if containing_lexical != receiver_owner:
                            raise UnsupportedPreparedView(
                                "direct slot result moved across unrelated receivers: "
                                f"current={occurrence_id!r}, receiver={receiver_owner!r}, "
                                f"container_lexical={containing_lexical!r}"
                            )
                        supplied_fills[receiver_owner].append(fill)
                        output.append(
                            f'<slot name="{site_id}"{context_binding_attrs}'
                            f"{_slot_key_attr(_next_slot_key(active_slot_key_scopes))}></slot>"
                        )
                    elif nested_template:
                        supplied_fills[output_owner].append(fill)
                        output.append(
                            f'<slot name="{site_id}"{context_binding_attrs}'
                            f"{_slot_key_attr(_next_slot_key(active_slot_key_scopes))}></slot>"
                        )
                    elif lexical_owner == output_owner:
                        _append_slot_outlet(
                            output,
                            site_id,
                            selected,
                            context_binding_attrs,
                            _next_slot_key(active_slot_key_scopes),
                        )
                    else:
                        supplied_fills[output_owner].append(fill)
                        _append_slot_outlet(
                            output,
                            site_id,
                            _DefinitionFragment.empty(),
                            context_binding_attrs,
                            _next_slot_key(active_slot_key_scopes),
                        )
                    continue
                if isinstance(part, RenderDecoration) and (
                    not part.frame.is_component_root or part.frame.render_id == frame.render_id
                ):
                    decorated = transform_parts(
                        list(part.parts),
                        placement_route=placement_route,
                        data_owner_id=data_owner_id,
                        call_owner_id=call_owner_id,
                        containing_slot=containing_slot,
                        call_run=call_run,
                        project_root_markers=project_root_markers,
                        parent_element_stack=tuple(element_stack),
                        projected_data=projected_data,
                        slot_key_scopes=tuple(active_slot_key_scopes),
                    )
                    wrapped = _DefinitionFragment.empty()
                    wrapped.extend(
                        transform_parts(
                            list(cast("Sequence[RenderPart]", part.opening)),
                            placement_route=placement_route,
                            data_owner_id=data_owner_id,
                            call_owner_id=call_owner_id,
                            containing_slot=containing_slot,
                            project_root_markers=False,
                            parent_element_stack=tuple(element_stack),
                            projected_data=projected_data,
                            slot_key_scopes=tuple(active_slot_key_scopes),
                        )
                    )
                    wrapped.extend(decorated)
                    for edge in part.closing:
                        if type(edge) is not PreparedElementClose:
                            raise UnsupportedPreparedView("render decoration closing structure is invalid")
                        wrapped.append(f"</{edge.tag}>")
                    output.extend(wrapped)
                    continue
                if isinstance(part, DirectCallRunRender):
                    eligible_run = (
                        part
                        if data_owner_id == occurrence_id and not placement_route and containing_slot is None
                        else None
                    )
                    output.extend(
                        transform_parts(
                            list(part.parts),
                            placement_route=placement_route,
                            data_owner_id=data_owner_id,
                            call_owner_id=call_owner_id,
                            containing_slot=containing_slot,
                            call_run=eligible_run,
                            project_root_markers=project_root_markers and dom_depth == 0,
                            parent_element_stack=tuple(element_stack),
                            projected_data=projected_data,
                            slot_key_scopes=tuple(active_slot_key_scopes),
                        )
                    )
                    continue
                if type(part) is SimpleRender:
                    validate_flattened_render_identity(part, "simple")
                    output.extend(
                        transform_parts(
                            list(part.parts),
                            placement_route=placement_route,
                            data_owner_id=data_owner_id,
                            call_owner_id=call_owner_id,
                            containing_slot=containing_slot,
                            project_root_markers=project_root_markers and dom_depth == 0,
                            parent_element_stack=tuple(element_stack),
                            projected_data=projected_data,
                            slot_key_scopes=tuple(active_slot_key_scopes),
                        )
                    )
                    continue
                if type(part) in {CitryRender, DirectPythonComponentRender, RenderDecoration}:
                    render_part = cast("CitryRender", part)
                    if not render_part.frame.is_component_root:
                        validate_flattened_render_identity(render_part, "transparent")
                        transparent_render_id = render_part.frame.render_id
                        if transparent_render_id is not None:
                            if render_part.frame.is_transparent_root and (
                                transparent_render_id not in render_to_occurrence
                                or transparent_render_id in flattened_transparent_receivers
                            ):
                                flattened_transparent_receivers.add(transparent_render_id)
                            prior_owner = render_to_occurrence.setdefault(transparent_render_id, occurrence_id)
                            # A supplied slot can carry an ordinary transparent
                            # Python render through the receiver's physical
                            # occurrence. Its values remain owned by the slot's
                            # lexical occurrence via data_owner_id.
                            projected_slot_render = (
                                containing_slot is not None
                                and bool(placement_route)
                                and transparent_render_id == containing_slot.fill_source.lexical_render_id
                                and _stable_owner(
                                    containing_slot.fill_source.lexical_render_id,
                                    render_to_occurrence,
                                )
                                == data_owner_id
                            )
                            if prior_owner != occurrence_id and not projected_slot_render:
                                receiver = containing_slot.receiver_render_id if containing_slot else None
                                receiver_owner = _stable_owner(receiver, render_to_occurrence) if receiver else None
                                lexical = containing_slot.fill_source.lexical_render_id if containing_slot else None
                                lexical_owner = _stable_owner(lexical, render_to_occurrence) if lexical else None
                                raise UnsupportedPreparedView(
                                    "transparent prepared render crossed physical occurrence owners: "
                                    f"render={transparent_render_id!r}, prior={prior_owner!r}, "
                                    f"current={occurrence_id!r}, data={data_owner_id!r}, "
                                    f"receiver={receiver!r}, receiver_owner={receiver_owner!r}, "
                                    f"lexical={lexical!r}, lexical_owner={lexical_owner!r}, "
                                    f"route={placement_route!r}"
                                )
                        prepared = (
                            render_part.frame.prepared_occurrence if render_part.frame.is_transparent_root else None
                        )
                        transparent_call = prepared.call if prepared is not None else None
                        explicit_key = transparent_call.explicit_key if transparent_call is not None else None
                        transparent_route = placement_route
                        wrapper_key: str | None = None
                        if explicit_key is not None:
                            if type(explicit_key) is not str:
                                raise UnsupportedPreparedView("prepared #c-key must evaluate to a string")
                            if (
                                transparent_call is None
                                or type(transparent_call.source) is not str
                                or type(transparent_call.source_span) is not tuple
                                or not render_part.frame.class_id
                            ):
                                raise UnsupportedPreparedView(
                                    "transparent prepared #c-key has incomplete call metadata"
                                )
                            transparent_call_base = (
                                transparent_call.source,
                                *transparent_call.source_span,
                                render_part.frame.class_id,
                            )
                            transparent_identity = (transparent_call_base, placement_route, explicit_key)
                            if transparent_identity in local_transparent_identity_keys:
                                raise UnsupportedPreparedView(
                                    "repeated component call has a duplicate explicit #c-key"
                                )
                            local_transparent_identity_keys.add(transparent_identity)
                            wrapper_digest = _digest(
                                transparent_call_base, placement_route, ("explicit", explicit_key)
                            )
                            wrapper_key = f"citryTransparent{wrapper_digest[:24]}"
                            transparent_route = (*placement_route, wrapper_key)
                            wrapper_binding = data_key(
                                "Key",
                                transparent_call.source,
                                transparent_call.source_span,
                                call_owner_id,
                            )
                            call_values[wrapper_binding] = wrapper_key
                        transparent_body = transform_parts(
                            list(render_part.parts),
                            placement_route=transparent_route,
                            data_owner_id=data_owner_id,
                            call_owner_id=call_owner_id,
                            containing_slot=containing_slot,
                            project_root_markers=project_root_markers and dom_depth == 0,
                            parent_element_stack=tuple(element_stack),
                            projected_data=projected_data,
                            slot_key_scopes=tuple(active_slot_key_scopes),
                        )
                        if wrapper_key is None:
                            output.extend(transparent_body)
                            continue

                        # The false template keeps a keyed Fragment root even
                        # when the transparent body has zero or one root node.
                        keyed_body = _DefinitionFragment.empty()
                        wrapper_start = keyed_body.byte_length
                        keyed_body.append(f'<template v-if="true" :key="preparedData.{wrapper_binding}">')
                        keyed_body.element_bindings.append(
                            {
                                "sourceStart": wrapper_start,
                                "sourceEnd": keyed_body.byte_length,
                                "attrsBindingKey": None,
                                "keyBindingKey": wrapper_binding,
                            }
                        )
                        keyed_body.extend(transparent_body)
                        keyed_body.append('<template v-if="false"></template></template>')
                        output.extend(keyed_body)
                        continue
                    child_prepared = render_part.frame.prepared_occurrence
                    metadata = child_prepared.call if child_prepared is not None else None
                    python_call = type(part) is DirectPythonComponentRender
                    if metadata is None and not python_call:
                        raise UnsupportedPreparedView("nested component has no prepared call metadata")
                    child_type = render_part.frame.class_id
                    if not child_type:
                        raise UnsupportedPreparedView("nested component has no stable class id")
                    if python_call:
                        python_ordinal = python_counts_by_route[placement_route]
                        python_counts_by_route[placement_route] += 1
                        call_base: tuple[object, ...] = ("python", child_type, python_ordinal)
                        explicit_key = None
                    else:
                        if metadata is None or not isinstance(metadata.source, str):
                            raise UnsupportedPreparedView("prepared component call source must be template text")
                        call_base = (metadata.source, *metadata.source_span, child_type)
                        explicit_key = metadata.explicit_key
                    run_group = run_first.get(part_index)
                    if run_group is not None:
                        run_values = call_values.setdefault("callRuns", {})
                        if type(run_values) is not dict:
                            raise AssertionError("prepared callRuns container changed type")
                        run_id = f"citryRun{len(run_values)}"
                        members: list[tuple[str, str, str, tuple[_FillFragment, ...]]] = []
                        run_component_tag: str | None = None
                        for member in run_group:
                            member_prepared = member.frame.prepared_occurrence
                            member_metadata = member_prepared.call if member_prepared is not None else None
                            if member_metadata is None:
                                raise UnsupportedPreparedView("call-run member has no prepared call metadata")
                            member_type = member.frame.class_id
                            if not member_type:
                                raise UnsupportedPreparedView("call-run member has no stable class id")
                            member_base = (
                                member_metadata.source,
                                *member_metadata.source_span,
                                member_type,
                            )
                            member_counts = call_counts_by_owner[call_owner_id]
                            member_counts[(member_base, placement_route)] += 1
                            member_key = member_metadata.explicit_key
                            if type(member_key) is not str:
                                raise UnsupportedPreparedView("prepared #c-key must evaluate to a string")
                            member_identity = (member_base, placement_route, member_key)
                            if member_identity in local_identity_keys:
                                raise UnsupportedPreparedView(
                                    "repeated component call has a duplicate explicit #c-key"
                                )
                            local_identity_keys.add(member_identity)
                            member_placement_digest = _digest(member_base, placement_route, ("explicit", member_key))
                            member_placement_key = f"citryPlacement{member_placement_digest[:24]}"
                            member_child_id = f"citryOccurrence{_digest(occurrence_id, member_placement_key)[:24]}"
                            transform_component(
                                member,
                                occurrence_id,
                                member_child_id,
                                member_placement_key,
                                physical_parent_stack=tuple(element_stack),
                                marker_owner_id=data_owner_id,
                            )
                            member_tag = component_tag(member_type)
                            if run_component_tag is None:
                                run_component_tag = member_tag
                            elif member_tag != run_component_tag:
                                raise UnsupportedPreparedView("prepared call run changed component tag")
                            reference_parents[member_child_id].append(occurrence_id)
                            member_fills = tuple(supplied_fills.pop(member_child_id, ()))
                            members.append((member_child_id, member_placement_key, member_type, member_fills))
                        if run_component_tag is None:
                            raise AssertionError("nonempty prepared call run produced no component tag")
                        if not any(member_fills for _, _, _, member_fills in members):
                            run_values[run_id] = [member_id for member_id, _, _, _ in members]
                            start = output.byte_length
                            output.append(
                                f'<component v-for="citryOccurrenceId in preparedData.callRuns.{run_id}" '
                                f':is="\'{run_component_tag}\'" :citry-id="citryOccurrenceId" '
                                ':key="citryOccurrenceId">'
                            )
                            opening_end = output.byte_length
                            output.append("</component>")
                            output.local_call_runs.append(
                                {
                                    "runId": run_id,
                                    "typeKey": child_type,
                                    "componentTag": run_component_tag,
                                    "sourceStart": start,
                                    "sourceEnd": opening_end,
                                    "loopSourceStart": start,
                                    "loopSourceEnd": opening_end,
                                }
                            )
                            continue
                        calls = call_values["calls"]
                        if type(calls) is not dict:
                            raise AssertionError("prepared calls container changed type")
                        for member_id, member_placement_key, member_type, member_fills in members:
                            local_id = f"citryCall{_digest('run-member', member_placement_key)[:16]}"
                            calls[local_id] = {"id": member_id, "key": member_id, "parentId": occurrence_id}
                            start = output.byte_length
                            output.append(
                                f'<{tag} :citry-id="preparedData.calls.{local_id}.id" '
                                f':key="preparedData.calls.{local_id}.key">'
                            )
                            opening_end = output.byte_length
                            append_child_fills(
                                output,
                                member_fills,
                                definition_owner_id=call_owner_id,
                                slot_key_scopes=tuple(active_slot_key_scopes),
                            )
                            output.append(f"</{tag}>")
                            output.local_calls.append(
                                {
                                    "localId": local_id,
                                    "typeKey": member_type,
                                    "componentTag": tag,
                                    "sourceStart": start,
                                    "sourceEnd": opening_end,
                                    "bindings": [],
                                }
                            )
                        continue
                    call_counts = call_counts_by_owner[call_owner_id]
                    call_site = (call_base, placement_route)
                    call_index = call_counts[call_site]
                    call_counts[call_site] += 1
                    if call_index and explicit_key is None:
                        raise UnsupportedPreparedView("repeated component call requires an explicit #c-key")
                    if explicit_key is None:
                        local_id = f"citryCall{_digest(call_base, placement_route, 0)[:16]}"
                        identity_key = local_id
                    else:
                        if type(explicit_key) is not str:
                            raise UnsupportedPreparedView("prepared #c-key must evaluate to a string")
                        identity = (call_base, placement_route, explicit_key)
                        if identity in local_identity_keys:
                            raise UnsupportedPreparedView("repeated component call has a duplicate explicit #c-key")
                        local_identity_keys.add(identity)
                        local_id = f"citryCall{_digest(call_base, placement_route, call_index)[:16]}"
                        identity_key = explicit_key
                    placement_digest = _digest(
                        call_base,
                        placement_route,
                        ("unkeyed",) if explicit_key is None else ("explicit", identity_key),
                    )
                    placement_key = f"citryPlacement{placement_digest[:24]}"
                    child_id = f"citryOccurrence{_digest(occurrence_id, placement_key)[:24]}"
                    transform_component(
                        render_part,
                        occurrence_id,
                        child_id,
                        placement_key,
                        root_markers if project_root_markers and dom_depth == 0 else (),
                        tuple(element_stack),
                        data_owner_id,
                    )
                    calls = call_values["calls"]
                    if type(calls) is not dict:
                        raise AssertionError("prepared calls container changed type")
                    calls[local_id] = {"id": child_id, "key": child_id, "parentId": occurrence_id}
                    reference_parents[child_id].append(occurrence_id)
                    tag = component_tag(child_type)
                    start = output.byte_length
                    output.append(f"<{tag}")
                    call_bindings: list[_LocalCallBindingDeclaration] = []
                    seen_binding_spans: set[tuple[int, int]] = set()
                    emitted_listener_names: set[str] = set()
                    if child_prepared is None:
                        raise UnsupportedPreparedView("nested component has no prepared occurrence metadata")
                    for component_binding in child_prepared.component_tag_client_bindings:
                        if type(component_binding) is not PreparedComponentBinding:
                            raise UnsupportedPreparedView(
                                "component call component_binding metadata changed after capture"
                            )
                        if not component_binding.authenticated:
                            raise UnsupportedPreparedView(
                                "component call component_binding lost its authenticated authored parser record"
                            )
                        if type(component_binding.kind) is not ComponentTagClientBindingKind:
                            raise UnsupportedPreparedView("component call binding kind changed after capture")
                        if component_binding.kind is ComponentTagClientBindingKind.CITRY_HANDLER:
                            if component_binding.provenance not in {"authored", "runtime-spread"}:
                                raise UnsupportedPreparedView("component event binding has unknown provenance")
                            from citry.ext.events.bindings import (  # noqa: PLC0415
                                _CHANNEL_EVENT,
                                _line_column,
                                compile_citry_boundary_binding,
                            )
                            from citry.ext.events.extension import EventsExtension  # noqa: PLC0415

                            events_extension = citry.extensions.get_extension("events")
                            if type(events_extension) is not EventsExtension:
                                raise UnsupportedPreparedView(
                                    "component-boundary Events binding requires the built-in Events compiler"
                                )
                            line, column = _line_column(str(component_binding.source), component_binding.span[0])
                            child_class = citry.get_component_by_class_id(child_type)
                            # Component-tag Events are authored by the
                            # lexical caller. A slot body can be physically
                            # assembled while visiting its receiver (for
                            # example CForm), but the handler still belongs to
                            # the component that supplied that slot. Resolve
                            # against the data owner instead of the physical
                            # receiver so nested library components retain the
                            # caller's Events contract.
                            binding_owner_type = occurrence_types[data_owner_id]
                            binding_owner_class = citry.get_component_by_class_id(binding_owner_type)
                            compiled_event = compile_citry_boundary_binding(
                                events_extension.resolve(binding_owner_class),
                                binding_owner_class.__name__,
                                f"c-{getattr(child_class, 'name', None) or child_class.__name__}",
                                component_binding.key,
                                component_binding.value,
                                line=line,
                                column=column,
                            )
                            if compiled_event.channel != _CHANNEL_EVENT:
                                raise UnsupportedPreparedView(
                                    "component-boundary polling is unsupported in prepared Vue"
                                )
                            spec = dict(compiled_event.spec)
                            if component_binding.provenance == "runtime-spread" and spec["args"] is not None:
                                raise UnsupportedPreparedView(
                                    "runtime component-boundary Events bindings accept a handler name "
                                    "without arguments"
                                )
                            modifiers = [name for name in ("prevent", "stop", "self", "once") if spec[name] is True]
                            if spec["key"] is not None:
                                modifiers.append(str(spec["key"]))
                            suffix = "" if not modifiers else "." + ".".join(modifiers)
                            generated_name = f"v-on:{spec['event']}{suffix}"
                            if generated_name in emitted_listener_names:
                                raise UnsupportedPreparedView(
                                    f"component call resolves more than one listener named {generated_name!r}"
                                )
                            emitted_listener_names.add(generated_name)
                            component_binding_id = f"citryEvent{_digest(local_id, generated_name)[:16]}"
                            event_component_binding = {"id": component_binding_id, **spec}
                            if (
                                event_component_binding["debounce"] is not None
                                or event_component_binding["throttle"] is not None
                            ):
                                raise UnsupportedPreparedView(
                                    "timed component-boundary Events bindings are unsupported in prepared Vue"
                                )
                            event_values = data_values.setdefault("eventBindings", {})
                            if type(event_values) is not dict:
                                raise AssertionError("prepared eventBindings container changed type")
                            serialized_event = _json_plain(event_component_binding)
                            previous_event = event_values.setdefault(component_binding_id, serialized_event)
                            if previous_event != serialized_event:
                                raise UnsupportedPreparedView(
                                    "one prepared component event site has conflicting authored metadata"
                                )
                            authored_args = _generated_event_args(
                                event_component_binding["args"],
                                el_expression=f"$citryEvents.componentRoot(preparedData.calls.{local_id}.id)",
                            )
                            generated_value = (
                                f"$citryEvents.dispatchComponent('{component_binding_id}', $event{authored_args})"
                            )
                            output.append(" ")
                            component_binding_start = output.byte_length
                            output.append(_generated_vue_attr(generated_name, generated_value))
                            call_bindings.append(
                                {
                                    "kind": ComponentTagClientBindingKind.EVENT.value,
                                    "name": generated_name,
                                    "value": generated_value,
                                    "sourceStart": component_binding_start,
                                    "sourceEnd": output.byte_length,
                                }
                            )
                            continue
                        if (
                            type(component_binding.source) is not str
                            or type(component_binding.span) is not tuple
                            or len(component_binding.span) != 2
                            or component_binding.span in seen_binding_spans
                        ):
                            raise UnsupportedPreparedView(
                                "component call component_binding lost authored source provenance"
                            )
                        seen_binding_spans.add(component_binding.span)
                        if component_binding.provenance != "authored":
                            raise UnsupportedPreparedView(
                                "runtime component component_binding provenance is valid only for Citry handlers"
                            )
                        if component_binding.kind is ComponentTagClientBindingKind.EVENT:
                            listener_name = (
                                f"v-on:{component_binding.key[1:]}"
                                if component_binding.key.startswith("@")
                                else component_binding.key
                            )
                            if listener_name in emitted_listener_names:
                                raise UnsupportedPreparedView(
                                    f"component call resolves more than one listener named {listener_name!r}"
                                )
                            emitted_listener_names.add(listener_name)
                        output.append(" ")
                        component_binding_start = output.byte_length
                        source_attr = f'{component_binding.key}="{_vue_attribute_escape(component_binding.value)}"'
                        output.append(source_attr)
                        call_bindings.append(
                            {
                                "kind": component_binding.kind.value,
                                "name": component_binding.key,
                                "value": component_binding.value,
                                "sourceStart": component_binding_start,
                                "sourceEnd": output.byte_length,
                            }
                        )
                    output.append(f' :citry-id="preparedData.calls.{local_id}.id"')
                    output.append(f' :key="preparedData.calls.{local_id}.key"')
                    output.append(">")
                    opening_end = output.byte_length
                    fills = tuple(supplied_fills.pop(child_id, ()))
                    append_child_fills(
                        output,
                        fills,
                        definition_owner_id=call_owner_id,
                        slot_key_scopes=tuple(active_slot_key_scopes),
                    )
                    output.append(f"</{tag}>")
                    output.local_calls.append(
                        {
                            "localId": local_id,
                            "typeKey": child_type,
                            "componentTag": tag,
                            "sourceStart": start,
                            "sourceEnd": opening_end,
                            "bindings": call_bindings,
                        }
                    )
                    continue
                if isinstance(part, PreparedSourceText):
                    output.append(part.text)
                    continue
                if isinstance(part, PreparedVerbatimHtml):
                    parent_tag = element_stack[-1] if element_stack else None
                    if any(tag in {"svg", "math"} for tag in element_stack):
                        raise UnsupportedPreparedView("c-raw is unsupported inside a prepared SVG or MathML parent")
                    if parent_tag in {"script", "style", "textarea", "title"}:
                        raise UnsupportedPreparedView(
                            f"c-raw is unsupported inside prepared <{parent_tag}> raw-text or RCDATA content"
                        )
                    reject_cross_boundary_html(part.html)
                    html = mark_opaque_html(
                        part.html,
                        root_markers if project_root_markers and dom_depth == 0 else (),
                    )
                    key = data_key("Opaque", part.source, part.span, data_owner_id)
                    projected_data_container("opaqueHtml")
                    opaque_values = data_values.setdefault("opaqueHtml", {})
                    if type(opaque_values) is not dict:
                        raise AssertionError("prepared opaqueHtml container changed type")
                    prior = opaque_values.setdefault(key, {"html": html})
                    if prior != {"html": html}:
                        raise UnsupportedPreparedView("one prepared opaque HTML site produced conflicting bytes")
                    start = output.byte_length
                    output.append(f'<citry-opaque-html :record="preparedData.opaqueHtml.{key}">')
                    end = output.byte_length
                    output.append("</citry-opaque-html>")
                    output.opaque_html_sites.append(
                        {"key": key, "sourceStart": start, "sourceEnd": end, "origin": "raw"}
                    )
                    continue
                if isinstance(part, PreparedStaticRun):
                    structure = part.root_structure
                    if project_root_markers and root_markers:
                        if structure is None:
                            raise UnsupportedPreparedView(
                                "prepared static root projection requires typed structural metadata"
                            )
                        root_openings = tuple(
                            opening for opening in structure.openings if dom_depth + opening.relative_depth == 0
                        )
                        if root_openings:
                            marker_identities = {_html_attr_identity(name) for name, _ in root_markers}
                            if any(opening.attr_identities & marker_identities for opening in root_openings):
                                raise UnsupportedPreparedView(
                                    "prepared root marker conflicts with an authored root attribute"
                                )
                            attrs_key = data_key("Attrs", part.html, (0, len(part.html.encode())), data_owner_id)
                            data_values[attrs_key] = _json_presence_attribute_map(dict(root_markers))
                            _append_static_root_projection(output, part.html, attrs_key, root_openings)
                        else:
                            output.append(part.html)
                    else:
                        output.append(part.html)
                    if structure is not None:
                        for operation, tag in structure.tag_transitions:
                            if operation == "open":
                                element_stack.append(tag)
                                element_key_scopes.append(None)
                            elif (
                                operation == "close"
                                and len(element_stack) > inherited_element_depth
                                and element_stack[-1] == tag
                            ):
                                element_stack.pop()
                                element_scope = element_key_scopes.pop()
                                if element_scope is not None:
                                    if not active_slot_key_scopes or active_slot_key_scopes[-1] is not element_scope:
                                        raise UnsupportedPreparedView(
                                            "prepared static key scope changed during text capture"
                                        )
                                    active_slot_key_scopes.pop()
                            else:
                                raise UnsupportedPreparedView(
                                    "prepared static tag transitions changed during text capture"
                                )
                        dom_depth += structure.final_depth_delta
                    continue
                if isinstance(part, PreparedTextValue):
                    key = data_key("Text", part.source, part.span, data_owner_id)
                    if key in data_values:
                        raise UnsupportedPreparedView("duplicate prepared text binding key")
                    data_values[key] = _json_plain(part.value)
                    text_browser_binding = part.browser_binding
                    if text_browser_binding is None:
                        output.append(f"{{{{ preparedData.{key} }}}}")
                    else:
                        if (
                            not is_authenticated_browser_binding(text_browser_binding)
                            or text_browser_binding.target != "text"
                        ):
                            raise UnsupportedPreparedView("prepared text browser text_browser_binding is invalid")
                        if text_browser_binding.helper not in template_context_names:
                            raise UnsupportedPreparedView(
                                "prepared browser text_browser_binding helper is not reserved"
                            )
                        operand_key = data_key("Binding", part.source, part.span, data_owner_id)
                        data_values[operand_key] = _json_plain(text_browser_binding.operand)
                        thunk = (
                            ""
                            if text_browser_binding.values_expression is None
                            else f", () => ({text_browser_binding.values_expression})"
                        )
                        output.append(f"{{{{ {text_browser_binding.helper}(preparedData.{operand_key}{thunk}) }}}}")
                    continue
                if isinstance(part, (PreparedTrustedHtmlValue, Markup)):
                    serialized = part.html if isinstance(part, PreparedTrustedHtmlValue) else str(part)
                    parent_tag = element_stack[-1] if element_stack else None
                    if any(tag in {"svg", "math"} for tag in element_stack):
                        raise UnsupportedPreparedView(
                            "trusted HTML is unsupported inside a prepared SVG or MathML parent"
                        )
                    if parent_tag in {"script", "style", "textarea", "title"}:
                        raise UnsupportedPreparedView(
                            f"trusted HTML is unsupported inside prepared <{parent_tag}> raw-text or RCDATA content"
                        )
                    if "<" not in serialized:
                        value = unescape(serialized)
                        if parent_tag == "textarea" and serialized.startswith("\n"):
                            value = value[1:]
                        key = data_key("Text", serialized, (0, len(serialized.encode())), data_owner_id)
                        data_values[key] = value
                        output.append(f"{{{{ preparedData.{key} }}}}")
                        continue
                    reject_cross_boundary_html(serialized)
                    html = mark_opaque_html(
                        serialized,
                        root_markers if project_root_markers and dom_depth == 0 else (),
                    )
                    key = data_key("Opaque", serialized, (0, len(serialized.encode())), data_owner_id)
                    projected_data_container("opaqueHtml")
                    opaque_values = data_values.setdefault("opaqueHtml", {})
                    if type(opaque_values) is not dict:
                        raise AssertionError("prepared opaqueHtml container changed type")
                    prior = opaque_values.setdefault(key, {"html": html})
                    if prior != {"html": html}:
                        raise UnsupportedPreparedView("one prepared opaque HTML site produced conflicting bytes")
                    start = output.byte_length
                    output.append(f'<citry-opaque-html :record="preparedData.opaqueHtml.{key}">')
                    end = output.byte_length
                    output.append("</citry-opaque-html>")
                    output.opaque_html_sites.append(
                        {"key": key, "sourceStart": start, "sourceEnd": end, "origin": "markup"}
                    )
                    continue
                if isinstance(part, PreparedLeafProgram):
                    attach_leaf_data(part, data_values, projected_keys)
                    fragment = _DefinitionFragment(
                        [part.fragment.template],
                        len(part.fragment.template.encode()),
                        [],
                        [cast("_ElementBindingDeclaration", dict(value)) for value in part.fragment.element_bindings],
                        [],
                        [],
                        [],
                        [cast("_RuntimeEventDeclaration", dict(value)) for value in part.fragment.runtime_event_sites],
                    )
                    output.extend(fragment)
                    continue
                if isinstance(part, PreparedElementOpen):
                    browser_attrs: list[str] = []
                    browser_keys: list[str] = []
                    for browser_binding in part.browser_bindings:
                        if not is_authenticated_browser_binding(browser_binding):
                            raise UnsupportedPreparedView("prepared browser browser_binding lacks producer provenance")
                        if browser_binding.helper not in template_context_names:
                            raise UnsupportedPreparedView("prepared browser browser_binding helper is not reserved")
                        if browser_binding.target != "attribute":
                            raise UnsupportedPreparedView("element browser browser_binding must target an attribute")
                        operand_key = data_key("Binding", part.source, part.span, data_owner_id)
                        while operand_key in data_values:
                            operand_key += "x"
                        data_values[operand_key] = _json_plain(browser_binding.operand)
                        browser_keys.append(operand_key)
                        thunk = (
                            ""
                            if browser_binding.values_expression is None
                            else f", () => ({browser_binding.values_expression})"
                        )
                        expression = _vue_attribute_escape(
                            f"{browser_binding.helper}(preparedData.{operand_key}{thunk})"
                        )
                        directive = f":{browser_binding.name}"
                        browser_attrs.append(f'{directive}="{expression}"')
                    effective_data_attrs = dict(part.data_attrs)
                    if project_root_markers and root_markers and dom_depth == 0:
                        marker_identities = {_html_attr_identity(name) for name, _ in root_markers}
                        source_marker_targets = {
                            _html_attr_identity(target)
                            for attr in part.attrs
                            for target in [_source_attribute_target(attr.name)]
                            if target is not None
                        }
                        existing_identities = source_marker_targets | {
                            _html_attr_identity(name) for name in effective_data_attrs
                        }
                        ambiguous_source_target = any(
                            attr.name == "v-bind" or attr.name.startswith((":[", "v-bind:["))
                            for attr in part.attrs
                            if attr.origin == "source"
                        )
                        if marker_identities & existing_identities or ambiguous_source_target:
                            raise UnsupportedPreparedView(
                                "prepared root marker conflicts with an authored or resolved root attribute"
                            )
                        effective_data_attrs.update(dict(root_markers))
                    if part.event_bindings:
                        projected_data_container("eventBindings")
                        event_values = data_values.setdefault("eventBindings", {})
                        if type(event_values) is not dict:
                            raise AssertionError("prepared eventBindings container changed type")
                        for binding in part.event_bindings:
                            authored_event_id = binding["id"]
                            serialized_binding = _json_plain(dict(binding))
                            previous_binding = event_values.setdefault(authored_event_id, serialized_binding)
                            if previous_binding != serialized_binding:
                                raise UnsupportedPreparedView(
                                    "one prepared event site has conflicting authored metadata"
                                )
                    if part.runtime_event_bindings:
                        projected_data_container("eventBindings")
                        event_values = data_values.setdefault("eventBindings", {})
                        if type(event_values) is not dict:
                            raise AssertionError("prepared eventBindings container changed type")
                        for binding in part.runtime_event_bindings:
                            runtime_event_id = binding["id"]
                            serialized_binding = _json_plain(dict(binding))
                            previous_binding = event_values.setdefault(runtime_event_id, serialized_binding)
                            if previous_binding != serialized_binding:
                                raise UnsupportedPreparedView(
                                    "one prepared runtime event site has conflicting metadata"
                                )
                    if part.poll_bindings or part.runtime_poll_bindings:
                        projected_data_container("pollBindings")
                        poll_values = data_values.setdefault("pollBindings", {})
                        if type(poll_values) is not dict:
                            raise AssertionError("prepared pollBindings container changed type")
                        for binding in part.poll_bindings:
                            authored_poll_id = binding["id"]
                            serialized_binding = _json_plain(dict(binding))
                            previous_binding = poll_values.setdefault(authored_poll_id, serialized_binding)
                            if previous_binding != serialized_binding:
                                raise UnsupportedPreparedView(
                                    "one prepared poll site has conflicting authored metadata"
                                )
                        for binding in part.runtime_poll_bindings:
                            runtime_poll_id = binding["id"]
                            serialized_binding = _json_plain(dict(binding))
                            previous_binding = poll_values.setdefault(runtime_poll_id, serialized_binding)
                            if previous_binding != serialized_binding:
                                raise UnsupportedPreparedView(
                                    "one prepared runtime poll site has conflicting metadata"
                                )
                    if part.control_bindings:
                        projected_data_container("controlBindings")
                        control_values = data_values.setdefault("controlBindings", {})
                        if type(control_values) is not dict:
                            raise AssertionError("prepared controlBindings container changed type")
                        for binding in part.control_bindings:
                            control_binding_id = binding["id"]
                            serialized_binding = _json_plain(dict(binding))
                            previous_binding = control_values.setdefault(control_binding_id, serialized_binding)
                            if previous_binding != serialized_binding:
                                raise UnsupportedPreparedView(
                                    "one prepared control site has conflicting authored metadata"
                                )
                    unsafe_data_attrs = [name for name in effective_data_attrs if _unsafe_dynamic_dom_property(name)]
                    executable_data_attrs = [
                        name for name in effective_data_attrs if name.startswith(("v-", "@", ":"))
                    ]
                    if executable_data_attrs:
                        raise UnsupportedPreparedView(
                            f"Python-resolved attributes cannot introduce Vue syntax: {executable_data_attrs!r}"
                        )
                    if unsafe_data_attrs:
                        raise UnsupportedPreparedView(
                            "prepared dynamic DOM property is unsafe for the bounded Vue target: "
                            f"{unsafe_data_attrs!r}"
                        )
                    source_targets = {
                        _html_attr_identity(target): attr.name
                        for attr in part.attrs
                        if attr.origin == "source"
                        for target in [_source_attribute_target(attr.name)]
                        if target is not None
                    }
                    data_targets = {_html_attr_identity(name): name for name in effective_data_attrs}
                    element_metadata = dict(part.element_metadata)
                    if "key" in element_metadata and ("key" in source_targets or "key" in data_targets):
                        raise UnsupportedPreparedView("prepared #c-key conflicts with another authored key")
                    conflict = source_targets.keys() & data_targets.keys()
                    if conflict:
                        names = [
                            f"{source_targets[identity]!r} / {data_targets[identity]!r}"
                            for identity in sorted(conflict)
                        ]
                        raise UnsupportedPreparedView(
                            f"authored Vue and prepared Python attributes target the same HTML name: {names!r}"
                        )
                    has_object_binding = any(attr.name == "v-bind" for attr in part.attrs if attr.origin == "source")
                    has_prepared_target = bool(effective_data_attrs) or "key" in element_metadata
                    if has_prepared_target and has_object_binding:
                        raise UnsupportedPreparedView(
                            "authored object v-bind cannot yet be combined with prepared Python attributes"
                        )
                    dynamic_bindings = [
                        attr.name
                        for attr in part.attrs
                        if attr.origin == "source" and attr.name.startswith((":[", "v-bind:["))
                    ]
                    if has_prepared_target and dynamic_bindings:
                        raise UnsupportedPreparedView(
                            "authored dynamic-argument Vue bindings cannot be proven unrelated to prepared Python "
                            f"attributes: {dynamic_bindings!r}"
                        )
                    element_attrs_key = (
                        data_key("Attrs", part.source, part.span, data_owner_id) if effective_data_attrs else None
                    )
                    prepared_key_binding = None
                    if element_attrs_key is not None:
                        serialized_attrs = _json_attribute_map(effective_data_attrs)
                        if project_root_markers and root_markers and dom_depth == 0:
                            serialized_attrs.update(_json_presence_attribute_map(dict(root_markers)))
                        data_values[element_attrs_key] = serialized_attrs
                    if "key" in element_metadata:
                        prepared_key_binding = data_key("Key", part.source, part.span, data_owner_id)
                        data_values[prepared_key_binding] = _json_plain(element_metadata["key"])
                    runtime_events_key = None
                    if part.runtime_events_candidate:
                        projected_data_container("eventBindings")
                        runtime_events_key = data_key("RuntimeEvents", part.source, part.span, data_owner_id)
                        data_values[runtime_events_key] = ",".join(
                            str(binding["id"])
                            for binding in (*part.runtime_event_bindings, *part.runtime_poll_bindings)
                        )
                    _append_element_open(
                        output,
                        part,
                        element_attrs_key,
                        prepared_key_binding,
                        browser_attrs,
                        browser_keys,
                        runtime_events_key,
                    )
                    if not part.is_void:
                        element_scope = (
                            None
                            if prepared_key_binding is None
                            else _SlotKeyScope(f"preparedData.{prepared_key_binding}")
                        )
                        element_key_scopes.append(element_scope)
                        if element_scope is not None:
                            active_slot_key_scopes.append(element_scope)
                        element_stack.append(part.tag.lower())
                        dom_depth += 1
                    continue
                if isinstance(part, PreparedDynamicElementOpen):
                    if not is_authenticated_dynamic_element_open(part):
                        raise UnsupportedPreparedView(
                            "dynamic element opening lacks exact validated producer provenance"
                        )
                    invalid_attrs = [
                        name
                        for name in part.attrs
                        if type(name) is not str
                        or name.startswith(("@", ":", "v-", "#"))
                        or _unsafe_dynamic_dom_property(name)
                    ]
                    if invalid_attrs:
                        raise UnsupportedPreparedView(
                            f"dynamic element opening contains unsafe prepared attributes: {invalid_attrs!r}"
                        )
                    if part.tag.lower() in {"script", "style", "template"}:
                        raise UnsupportedPreparedView(
                            "dynamic script/style/template elements are unsupported in prepared Vue"
                        )
                    source_targets = {
                        _html_attr_identity(target): attr.name
                        for attr in part.authored_attrs
                        for target in [_source_attribute_target(attr.name)]
                        if target is not None
                    }
                    effective_dynamic_attrs = dict(part.attrs)
                    if part.key is not None:
                        effective_dynamic_attrs.pop("data-citry-key", None)
                    data_targets = {_html_attr_identity(name): name for name in effective_dynamic_attrs}
                    conflict = source_targets.keys() & data_targets.keys()
                    if conflict:
                        names = [
                            f"{source_targets[identity]!r} / {data_targets[identity]!r}"
                            for identity in sorted(conflict)
                        ]
                        raise UnsupportedPreparedView(
                            f"authored Vue and prepared Python attributes target the same HTML name: {names!r}"
                        )
                    has_prepared_target = bool(effective_dynamic_attrs) or part.key is not None
                    if has_prepared_target and any(attr.name == "v-bind" for attr in part.authored_attrs):
                        raise UnsupportedPreparedView(
                            "authored object v-bind cannot yet be combined with prepared Python attributes"
                        )
                    dynamic_bindings = [
                        attr.name for attr in part.authored_attrs if attr.name.startswith((":[", "v-bind:["))
                    ]
                    if has_prepared_target and dynamic_bindings:
                        raise UnsupportedPreparedView(
                            "authored dynamic-argument Vue bindings cannot be proven unrelated to prepared Python "
                            f"attributes: {dynamic_bindings!r}"
                        )
                    if part.key is not None and "key" in source_targets:
                        raise UnsupportedPreparedView("prepared #c-key conflicts with another authored key")
                    alias = f"citry-dynamic-{_digest(occurrence_types[occurrence_id], dynamic_site_index)[:16]}"
                    dynamic_site_index += 1
                    attrs_key = data_key("Attrs", alias, (0, 0), data_owner_id)
                    dynamic_attrs = effective_dynamic_attrs
                    if project_root_markers and root_markers and dom_depth == 0:
                        marker_identities = {_html_attr_identity(name) for name, _ in root_markers}
                        source_marker_targets = {
                            _html_attr_identity(target)
                            for attr in part.authored_attrs
                            for target in [_source_attribute_target(attr.name)]
                            if target is not None
                        }
                        ambiguous_source_target = any(
                            attr.name == "v-bind" or attr.name.startswith((":[", "v-bind:["))
                            for attr in part.authored_attrs
                        )
                        if (
                            marker_identities
                            & (source_marker_targets | {_html_attr_identity(name) for name in dynamic_attrs})
                            or ambiguous_source_target
                        ):
                            raise UnsupportedPreparedView(
                                "prepared root marker conflicts with a resolved dynamic root attribute"
                            )
                        dynamic_attrs.update(dict(root_markers))
                    serialized_attrs = _json_attribute_map(dynamic_attrs)
                    if project_root_markers and root_markers and dom_depth == 0:
                        serialized_attrs.update(_json_presence_attribute_map(dict(root_markers)))
                    data_values[attrs_key] = serialized_attrs
                    projected_data_container("eventBindings")
                    projected_data_container("pollBindings")
                    projected_data_container("controlBindings")
                    _register_dynamic_binding_data(data_values, part)
                    start = output.byte_length
                    output.append(f"<{alias}")
                    for attr in part.authored_attrs:
                        output.append(f" {attr.value}")
                    native_marker = (
                        vue_owned_native_marker(
                            vue_owned_native_properties(
                                part.tag,
                                part.authored_attrs,
                                effective_dynamic_attrs,
                                has_spread=part.has_spread,
                            )
                        )
                        if is_native_state_tag(part.tag)
                        else ""
                    )
                    output.append(f' v-bind="preparedData.{attrs_key}"')
                    if native_marker:
                        output.append(f" {native_marker}")
                    key_key = None
                    if part.key is not None:
                        key_key = data_key("Key", alias, (0, 0), data_owner_id)
                        data_values[key_key] = _json_plain(part.key)
                        output.append(f' :key="preparedData.{key_key}"')
                    for generated_attr in _event_directive_attrs(part):
                        output.append(f" {generated_attr}")
                    runtime_events_key = None
                    if part.runtime_events_candidate:
                        projected_data_container("eventBindings")
                        runtime_events_key = data_key("RuntimeEvents", alias, (0, 0), data_owner_id)
                        data_values[runtime_events_key] = ",".join(
                            str(binding["id"])
                            for binding in (*part.runtime_event_bindings, *part.runtime_poll_bindings)
                        )
                        output.append(
                            f' v-citry-runtime-events="$citryEvents.runtimeEvents(preparedData.{runtime_events_key})"'
                        )
                    # The generated alias is a custom element to the parser even
                    # when its validated runtime tag is void. Emit an ordinary
                    # opening boundary so Vue can compile it without rewriting
                    # invalid custom-element self-closing syntax.
                    output.append(">")
                    output.dynamic_elements.append(
                        {"alias": alias, "tag": part.tag, "sourceStart": start, "sourceEnd": output.byte_length}
                    )
                    output.element_bindings.append(
                        {
                            "sourceStart": start,
                            "sourceEnd": output.byte_length,
                            "attrsBindingKey": attrs_key,
                            "keyBindingKey": key_key,
                            "runtimeEventsBindingKey": runtime_events_key,
                        }
                    )
                    if runtime_events_key is not None:
                        output.runtime_event_sites.append(
                            {
                                "sourceStart": start,
                                "sourceEnd": output.byte_length,
                                "bindingKey": runtime_events_key,
                                "steps": [],
                            }
                        )
                    if part.is_void:
                        # Balance the parser-level custom alias even though its
                        # validated runtime tag is void, so following siblings
                        # cannot become children of the generated alias.
                        output.append(f"</{alias}>")
                    else:
                        dynamic_stack.append((part.tag, alias))
                        element_scope = None if key_key is None else _SlotKeyScope(f"preparedData.{key_key}")
                        element_key_scopes.append(element_scope)
                        if element_scope is not None:
                            active_slot_key_scopes.append(element_scope)
                        element_stack.append(part.tag.lower())
                        dom_depth += 1
                    continue
                if isinstance(part, PreparedDynamicElementClose):
                    if not dynamic_stack or dynamic_stack[-1][0] != part.tag:
                        raise UnsupportedPreparedView("dynamic element close has no opening")
                    _, alias = dynamic_stack.pop()
                    output.append(f"</{alias}>")
                    if len(element_stack) <= inherited_element_depth or element_stack.pop() != part.tag.lower():
                        raise UnsupportedPreparedView("dynamic element stack changed during text capture")
                    element_scope = element_key_scopes.pop()
                    if element_scope is not None:
                        if not active_slot_key_scopes or active_slot_key_scopes[-1] is not element_scope:
                            raise UnsupportedPreparedView("prepared dynamic key scope changed during text capture")
                        active_slot_key_scopes.pop()
                    dom_depth -= 1
                    continue
                if isinstance(part, PreparedElementClose):
                    output.append(f"</{part.tag}>")
                    if len(element_stack) <= inherited_element_depth or element_stack.pop() != part.tag.lower():
                        raise UnsupportedPreparedView("prepared element stack changed during text capture")
                    element_scope = element_key_scopes.pop()
                    if element_scope is not None:
                        if not active_slot_key_scopes or active_slot_key_scopes[-1] is not element_scope:
                            raise UnsupportedPreparedView("prepared element key scope changed during text capture")
                        active_slot_key_scopes.pop()
                    dom_depth -= 1
                    continue
                if isinstance(part, Placeholder) and part.key in {"deps:css", "deps:js"}:
                    continue
                if part == "" and type(part) is str:
                    continue
                raise UnsupportedPreparedView(f"unsupported typed render part: {type(part).__name__}")
            if dynamic_stack:
                raise UnsupportedPreparedView("dynamic element opening has no close")
            if projected_keys is not None and projected_containers is not None:
                merge_projected_data(
                    data_values,
                    prepared_by_occurrence[occurrence_id],
                    projected_keys,
                    projected_containers,
                    occurrence_id,
                )
            active_projected_data_keys.pop()
            active_projected_data_containers.pop()
            return output

        raw_parts = list(value.parts)
        logical_parts = _logical_typed_body(raw_parts)
        selected_parts: list[RenderPart] = (
            [value]
            if isinstance(value, RenderDecoration) and not (value.omit_around_document and logical_parts != raw_parts)
            else logical_parts
        )
        leaf = selected_parts[0] if len(selected_parts) == 1 else None
        if root_markers and isinstance(leaf, PreparedLeafProgram):
            from citry._vue.leaf_program import typed_leaf_parts  # noqa: PLC0415

            selected_parts = typed_leaf_parts(leaf)
            leaf = None
        artifact = leaf_artifacts.get((type_key, id(leaf.fragment))) if isinstance(leaf, PreparedLeafProgram) else None
        if isinstance(leaf, PreparedLeafProgram):
            from citry._vue.leaf_program import typed_leaf_parts  # noqa: PLC0415

            typed_leaf = typed_leaf_parts(leaf)
            if any(isinstance(part, PreparedElementOpen) and part.browser_bindings for part in typed_leaf):
                selected_parts = typed_leaf
                leaf = None
                artifact = None
        if isinstance(leaf, PreparedLeafProgram):
            attach_leaf_data(leaf, prepared_by_occurrence[occurrence_id])
        if artifact is None:
            if isinstance(leaf, PreparedLeafProgram):
                compile_input = DefinitionCompileInput(
                    leaf.fragment.template,
                    (),
                    tuple(dict(value) for value in leaf.fragment.element_bindings),
                    (),
                    (),
                    template_context_names,
                    (),
                    tuple(dict(value) for value in leaf.fragment.runtime_event_sites),
                )
            else:
                fragment = transform_parts(selected_parts, parent_element_stack=physical_parent_stack)
                compile_input = fragment.compile_input(template_context_names)
            structural = json.dumps(
                {
                    "template": compile_input.template,
                    "localCalls": compile_input.local_calls,
                    "elementBindings": compile_input.element_bindings,
                    "localCallRuns": compile_input.local_call_runs,
                    "dynamicElements": compile_input.dynamic_elements,
                    "runtimeEventSites": compile_input.runtime_event_sites,
                    "templateContextNames": compile_input.template_context_names,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            definition_id = hashlib.sha256((type_key + "\0" + structural).encode()).hexdigest()
            artifact = _LeafDefinitionArtifact(definition_id, compile_input)
            if isinstance(leaf, PreparedLeafProgram):
                leaf_artifacts[(type_key, id(leaf.fragment))] = artifact
        else:
            definition_id = artifact.definition_id
            compile_input = artifact.compile_input
        definition = _AssembledDefinition(definition_id, type_key)
        existing = definitions.get(definition_id)
        existing_input = compile_inputs.get(definition_id)
        if existing is not None:
            if existing.type_key != type_key or existing_input != compile_input:
                raise AssertionError("prepared definition hash collision")
        else:
            definitions[definition_id] = definition
            compile_inputs[definition_id] = compile_input
        occurrence_definition_ids[occurrence_index] = definition_id
        return occurrence_id

    root_type = render.frame.class_id
    if not root_type:
        raise UnsupportedPreparedView("root component has no stable class id")
    root_id = f"citryOccurrence{_digest('root', root_type)[:24]}" if root_occurrence_id is None else root_occurrence_id
    if type(root_id) is not str:
        raise UnsupportedPreparedView("prepared root occurrence id is not a string")
    if re.fullmatch(r"citryOccurrence[0-9A-Za-z]+", root_id) is None:
        raise UnsupportedPreparedView("prepared root occurrence id is not generated-safe")
    transform_component(render, None, root_id, marker_owner_id=root_id)
    if any(supplied_fills.values()):
        raise UnsupportedPreparedView("selected direct fills were not consumed by their receiver call")
    placements: set[tuple[str, str]] = set()
    for occurrence_id, _type_key, parent_id, _placement_key, _frame_data, _prepared_values in occurrence_fields:
        references = reference_parents[occurrence_id]
        if occurrence_id == root_id:
            if references or parent_id is not None or _placement_key is not None:
                raise UnsupportedPreparedView("prepared root was referenced as a child")
        else:
            if references != [parent_id]:
                raise UnsupportedPreparedView(
                    "prepared nonroot occurrence must have one exact physical-parent call reference"
                )
            if type(parent_id) is not str or type(_placement_key) is not str or not _placement_key:
                raise UnsupportedPreparedView("prepared nonroot occurrence has no placement key")
            placement = (parent_id, _placement_key)
            if placement in placements:
                raise UnsupportedPreparedView(
                    "prepared occurrence placement key is duplicated within one physical parent"
                )
            placements.add(placement)
    if any(definition_id is None for definition_id in occurrence_definition_ids):
        raise AssertionError("prepared occurrence definition was not finalized")
    occurrences = tuple(
        PreparedOccurrence._from_assembly(
            occurrence_id,
            type_key,
            definition_id,
            dict(frame_data),
            prepared_values,
            parent_id,
            placement_key,
        )
        for (occurrence_id, type_key, parent_id, placement_key, frame_data, prepared_values), definition_id in zip(
            occurrence_fields, occurrence_definition_ids, strict=True
        )
        if definition_id is not None  # narrowed by the invariant above
    )
    ordered_markers = tuple(sorted(markers, key=lambda item: (item.owner_id, item.name, item.occurrence_id)))
    if len({(item.owner_id, item.name) for item in ordered_markers}) != len(ordered_markers):
        raise UnsupportedPreparedView("prepared marker name is duplicated within its lexical owner")
    if len({item.occurrence_id for item in ordered_markers}) != len(ordered_markers):
        raise UnsupportedPreparedView("prepared marker occurrence has more than one alias")
    view = AssembledView(revision, root_id, occurrences, tuple(definitions.values()), ordered_markers)
    occurrence_ids = {item.id for item in view.occurrences}
    if set(occurrence_to_render) != occurrence_ids or len(set(occurrence_to_render.values())) != len(
        occurrence_to_render
    ):
        raise AssertionError("canonical prepared occurrence render identities must be bijective")
    if any(
        render_to_occurrence.get(render_id) != occurrence_id
        for occurrence_id, render_id in occurrence_to_render.items()
    ):
        raise AssertionError("canonical prepared occurrence render identity changed ownership")
    return Assembly(view, dict(render_to_occurrence), dict(occurrence_to_render), compile_inputs)


def _logical_typed_body(parts: list[RenderPart]) -> list[RenderPart]:
    """Select logical body UI before assembling document-shell components."""
    has_shell = any(
        (isinstance(part, PreparedSourceText) and part.text.lstrip().lower().startswith("<!doctype"))
        or (isinstance(part, PreparedElementOpen) and part.tag.lower() in {"html", "head", "body"})
        for part in parts
    )
    if not has_shell:
        return parts
    body_start = next(
        (
            index
            for index, part in enumerate(parts)
            if isinstance(part, PreparedElementOpen) and part.tag.lower() == "body"
        ),
        None,
    )
    if body_start is None:
        raise UnsupportedPreparedView("interactive document component requires one authored body element")
    depth = 1
    for index in range(body_start + 1, len(parts)):
        part = parts[index]
        if isinstance(part, PreparedElementOpen) and part.tag.lower() == "body":
            depth += 1
        elif isinstance(part, PreparedElementClose) and part.tag.lower() == "body":
            depth -= 1
            if depth == 0:
                return parts[body_start + 1 : index]
    raise UnsupportedPreparedView("interactive document component has an unclosed body element")


def _stable_owner(render_id: str | None, owners: Mapping[str, str]) -> str | None:
    if render_id is None:
        return None
    owner = owners.get(render_id)
    if owner is None:
        raise UnsupportedPreparedView("ownership record refers to an unprepared occurrence")
    return owner


def _digest(*values: object) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _checked_component_tag(type_key: str, tag_for_type: TagForType) -> str:
    tag = tag_for_type(type_key)
    if type(tag) is not str:
        raise UnsupportedPreparedView("component tag mapping must return an exact string")
    if re.fullmatch(r"[a-z][a-z0-9.-]*-[a-z0-9.-]+", tag) is None:
        raise UnsupportedPreparedView("component tag mapping must return a safe custom-element name")
    return tag


def _source_attribute_target(name: str) -> str | None:
    if name.startswith(":"):
        return name[1:].split(".", 1)[0]
    match = re.fullmatch(r"v-bind:([^\.]+)(?:\..*)?", name)
    if match is not None:
        return match.group(1)
    if not name.startswith(("v-", "@", "#")):
        return name
    return None


def _unsafe_dynamic_dom_property(name: str) -> bool:
    normalized = name.casefold()
    return normalized in {"innerhtml", "outerhtml", "textcontent", "innertext"} or normalized.startswith("on")


_ROOT_MARKER_RE = re.compile(r'(?P<name>[A-Za-z_:][A-Za-z0-9_.:-]*)(?:="(?P<value>[^"]*)")?\Z')


def _prepared_root_markers(markers: tuple[str, ...]) -> tuple[tuple[str, object], ...]:
    """Parse internal root markers into safe data-origin attribute values."""
    values: dict[str, object] = {}
    identities: set[str] = set()
    for marker in markers:
        if type(marker) is not str or (match := _ROOT_MARKER_RE.fullmatch(marker)) is None:
            raise UnsupportedPreparedView("prepared root marker must be one plain HTML attribute")
        name = validate_html_attr_name(match["name"], where="prepared component root marker")
        if not name.casefold().startswith("data-") or _unsafe_dynamic_dom_property(name):
            raise UnsupportedPreparedView(f"prepared root marker {name!r} is unsafe")
        marker_value: object = True if match["value"] is None else unescape(match["value"])
        identity = _html_attr_identity(name)
        if identity not in identities:
            values[name] = marker_value
            identities.add(identity)
    return tuple(values.items())


def _append_static_root_projection(
    output: _DefinitionFragment,
    html: str,
    attrs_key: str,
    openings: tuple[StaticRunOpening, ...],
) -> None:
    """Add one generated data binding to every physical root in authored static HTML."""
    replacement = f'v-bind="preparedData.{attrs_key}"'
    cursor = 0
    for opening in openings:
        output.append(html[cursor : opening.insert_at])
        binding_start = output.byte_length - len(html[opening.start_at : opening.insert_at].encode())
        output.append(" ")
        output.append(replacement)
        output.append(html[opening.insert_at : opening.end_at])
        cursor = opening.end_at
        output.element_bindings.append(
            {
                "sourceStart": binding_start,
                "sourceEnd": output.byte_length,
                "attrsBindingKey": attrs_key,
                "keyBindingKey": None,
            }
        )
    output.append(html[cursor:])


def _next_slot_key(scopes: Sequence[_SlotKeyScope]) -> str | None:
    """Return a stable key for one slot under the nearest keyed element."""
    if not scopes:
        return None
    scope = scopes[-1]
    ordinal = scope.ordinal
    scope.ordinal += 1
    return f"JSON.stringify([{scope.expression}, {ordinal}])"


def _slot_key_attr(expression: str | None) -> str:
    return "" if expression is None else f' :key="{expression}"'


def _append_slot_outlet(
    output: _DefinitionFragment,
    site_id: str,
    fallback: _DefinitionFragment,
    context_binding_attrs: str = "",
    slot_key_expression: str | None = None,
) -> None:
    output.append(
        f"<slot v-if=\"preparedData.selectedSlots[{site_id!r}] === 'supplied'\" "
        f'name="{site_id}"{context_binding_attrs}{_slot_key_attr(slot_key_expression)}></slot>'
    )
    if fallback.chunks:
        output.append(f"<template v-else-if=\"preparedData.selectedSlots[{site_id!r}] === 'fallback'\">")
        output.extend(fallback)
        output.append("</template>")


def _append_element_open(
    output: _DefinitionFragment,
    part: PreparedElementOpen,
    attrs_binding_key: str | None,
    key_binding_key: str | None,
    browser_attrs: list[str] | None = None,
    browser_binding_keys: list[str] | None = None,
    runtime_events_key: str | None = None,
) -> None:
    start = output.byte_length
    attrs = list(part.authored_attrs)
    native_marker = (
        vue_owned_native_marker(
            vue_owned_native_properties(part.tag, part.attrs, part.data_attrs, has_spread=part.has_spread)
        )
        if is_native_state_tag(part.tag)
        else ""
    )
    if native_marker:
        attrs.append(native_marker)
    if attrs_binding_key is not None:
        attrs.append(f'v-bind="preparedData.{attrs_binding_key}"')
    if key_binding_key is not None:
        attrs.append(f':key="preparedData.{key_binding_key}"')
    # Reactive projections own their checked destinations after the static
    # prepared fallback spread has supplied the initial server value.
    attrs.extend(browser_attrs or ())
    if runtime_events_key is not None:
        attrs.append(f'v-citry-runtime-events="$citryEvents.runtimeEvents(preparedData.{runtime_events_key})"')
    attrs.extend(_event_directive_attrs(part))
    rendered_attrs = "" if not attrs else " " + " ".join(attrs)
    output.append(f"<{part.tag}{rendered_attrs}>")
    if attrs_binding_key is not None or key_binding_key is not None or browser_binding_keys or runtime_events_key:
        output.element_bindings.append(
            {
                "sourceStart": start,
                "sourceEnd": output.byte_length,
                "attrsBindingKey": attrs_binding_key,
                "keyBindingKey": key_binding_key,
                "browserBindingKeys": browser_binding_keys or [],
                "runtimeEventsBindingKey": runtime_events_key,
            }
        )
    if runtime_events_key is not None:
        output.runtime_event_sites.append(
            {
                "sourceStart": start,
                "sourceEnd": output.byte_length,
                "bindingKey": runtime_events_key,
                "steps": [],
            }
        )


def _event_directive_attrs(part: PreparedElementOpen | PreparedDynamicElementOpen) -> list[str]:
    attrs: list[str] = []
    seen_events: set[str] = set()
    for binding in part.event_bindings:
        event = str(binding["event"])
        if event in seen_events:
            raise UnsupportedPreparedView("prepared Vue target supports one Events binding per DOM event")
        seen_events.add(event)
        modifiers = [name for name in ("prevent", "stop", "self", "once") if binding[name] is True]
        if binding["key"] is not None:
            modifiers.append(str(binding["key"]))
        suffix = "" if not modifiers else "." + ".".join(modifiers)
        authored_args = _generated_event_args(binding["args"])
        attrs.append(
            _generated_vue_attr(
                f"v-on:{event}{suffix}",
                f"$citryEvents.dispatch('{binding['id']}', $event{authored_args})",
            )
        )
    timed_ids = ",".join(
        str(binding["id"])
        for binding in part.event_bindings
        if binding["debounce"] is not None or binding["throttle"] is not None
    )
    poll_entries = ",".join(
        "{id:'"
        + str(binding["id"])
        + "',args:"
        + ("undefined" if binding["args"] is None else f"()=>({binding['args']})")
        + "}"
        for binding in part.poll_bindings
    )
    if timed_ids or poll_entries:
        timing_expression = (
            f"$citryEvents.timings('{timed_ids}',[{poll_entries}])"
            if poll_entries
            else f"$citryEvents.timings('{timed_ids}')"
        )
        attrs.append(
            _generated_vue_attr(
                "v-citry-event-timing",
                timing_expression,
            )
        )
    if part.control_bindings:
        ids = ",".join(str(binding["id"]) for binding in part.control_bindings)
        attrs.append(f"v-citry-control=\"$citryEvents.controls('{ids}')\"")
    return attrs


def _register_dynamic_binding_data(data_values: dict[str, object], part: PreparedDynamicElementOpen) -> None:
    for name, bindings in (
        ("eventBindings", (*part.event_bindings, *part.runtime_event_bindings)),
        ("pollBindings", (*part.poll_bindings, *part.runtime_poll_bindings)),
        ("controlBindings", part.control_bindings),
    ):
        if not bindings:
            continue
        values = data_values.setdefault(name, {})
        if type(values) is not dict:
            raise AssertionError(f"prepared {name} container changed type")
        for binding in bindings:
            binding_id = binding["id"]
            serialized = _json_plain(dict(binding))
            previous = values.setdefault(binding_id, serialized)
            if previous != serialized:
                raise UnsupportedPreparedView(f"one prepared binding site has conflicting {name} metadata")
