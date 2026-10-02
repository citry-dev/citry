"""Convert typed prepared render parts into a reusable prepared component view."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from html import escape, unescape
from itertools import pairwise
from typing import TYPE_CHECKING, Any, TypeAlias, TypeGuard, TypeVar, cast

from citry.attrs import _html_attr_identity, format_attrs, validate_html_attr_name
from citry.citry_render import (
    CitryRender,
    Placeholder,
    PreparedComponentBinding,
    RenderDecoration,
    RenderFrame,
    RenderPart,
    SimpleVueRecord,
)
from citry.client_directives import ComponentTagClientBindingKind
from citry.components.mark import repeated_mark_name_error, validate_mark_name
from citry.util.html import Markup, escape_to_str
from citry_core.template_parser import analyze_browser_source

from .capture import (
    PreparedAttribute,
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
    conflicting_attribute_targets,
    format_prepared_element_attrs,
    is_authenticated_browser_binding,
    is_authenticated_dynamic_element_open,
    is_ignored_element_open,
    is_native_state_tag,
    is_vue_directive_name,
    prepared_spread_index,
    vue_owned_native_marker,
    vue_owned_native_properties,
)
from .compiler import (
    DefinitionCompileInput,
    _authored_vue_attr,
    _DynamicElementDeclaration,
    _ElementBindingDeclaration,
    _generated_event_args,
    _generated_vue_attr,
    _LocalCallBindingDeclaration,
    _LocalCallDeclaration,
    _LocalCallRunDeclaration,
    _OpaqueHtmlDeclaration,
    _RuntimeEventDeclaration,
)
from .direct import (
    DirectCallRunRender,
    DirectNestedTemplateRender,
    DirectProjectionRender,
    DirectPythonComponentRender,
)
from .json_data import _copy_evaluated_json, _json_plain, _vue_attribute_value
from .leaf_program import (
    LeafCallChildren,
    LeafProgramFragment,
    PreparedLeafProgram,
    typed_leaf_parts,
)
from .opaque_html import mark_opaque_html, opaque_html_record, reject_cross_boundary_html
from .prepared import (
    PreparedMarker,
    PreparedOccurrence,
    RuntimeDirective,
)

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.citry_context import CitryContext
    from citry.citry_element import _PreparedCallMetadata
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
    # Occurrences whose caller wrote `v-show` or a custom directive on the
    # component tag, mapped to the child's class name, the authored tag, and
    # the first such directive, so the compiled child's root can be checked
    # once every definition is compiled.
    root_directive_occurrences: Mapping[str, tuple[str, str, str]] = field(default_factory=dict)


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


def _run_eligible_component(value: object) -> TypeGuard[CitryRender | SimpleVueRecord]:
    """Whether one selected child has the exact bounded call-run proof."""
    if type(value) is SimpleVueRecord:
        from citry.citry_element import _PreparedCallMetadata  # noqa: PLC0415

        metadata = value.call_metadata
        return bool(
            value.component_class.simple == "vue"
            and value.component_class.class_id == value.class_id
            and type(value.leaf) is PreparedLeafProgram
            and type(metadata) is _PreparedCallMetadata
            and metadata.slot_free_body is True
            and type(metadata.source) is str
            and type(metadata.source_span) is tuple
            and type(metadata.explicit_key) is str
        )
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


def _run_member_metadata(
    value: CitryRender | SimpleVueRecord,
) -> tuple[str | None, Any | None]:
    # The type checker forbids subclasses of the final SimpleVueRecord, so
    # isinstance acts like an exact type check and narrows ``value`` to
    # CitryRender below.
    if isinstance(value, SimpleVueRecord):
        return value.class_id, value.call_metadata
    prepared = value.frame.prepared_occurrence
    return value.frame.class_id, None if prepared is None else prepared.call


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
        self.byte_length += len(text.encode("utf-8"))

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


@dataclass(frozen=True, slots=True)
class _FillFragment:
    site_id: str
    public_name: str
    lexical_owner: str
    body: _DefinitionFragment


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


def _json_attribute_map(values: Mapping[str, object]) -> dict[str, object]:
    """
    Encode resolved HTML attributes for Vue's object binding.

    Each value except ``True`` is sent as the text Python's HTML output gives
    it (see _vue_attribute_value), so a client render sets the same attribute
    text as the server HTML. Keep JSON booleans intact. Vue's object binding serializes a custom
    attribute whose value is ``true`` as ``"true"``; converting it to the
    empty string here would change the public prepared-attribute contract.
    """
    return {name: _json_plain(_vue_attribute_value(value)) for name, value in values.items()}


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
    root_simple_record: SimpleVueRecord | None = None
    if root_component is None:
        if len(render.parts) == 1 and type(render.parts[0]) is SimpleVueRecord:
            root_simple_record = cast("SimpleVueRecord", render.parts[0])
        citry = render.owner_citry
        if (
            root_simple_record is None
            or citry is None
            or root_simple_record.component_class.citry is not citry
            or citry.get_component_by_class_id(root_simple_record.class_id) is not root_simple_record.component_class
        ):
            raise UnsupportedPreparedView("prepared root has no matching owning component registry")
    else:
        citry = root_component.citry
        if render.owner_citry is not None and render.owner_citry is not citry:
            raise UnsupportedPreparedView("prepared root owner does not match its current component registry")
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
    root_directive_occurrences: dict[str, tuple[str, str, str]] = {}
    definitions: dict[str, _AssembledDefinition] = {}
    render_to_occurrence: dict[str, str] = {}
    occurrence_to_render: dict[str, str] = {}
    prepared_by_occurrence: dict[str, dict[str, object]] = {}
    occurrence_types: dict[str, str] = {}
    occurrence_parents: dict[str, str | None] = {}
    # Each child occurrence's placement key names its call site and explicit
    # key without any occurrence id; slot names are built from these.
    occurrence_placement_keys: dict[str, str | None] = {}
    reference_parents: defaultdict[str, list[str]] = defaultdict(list)
    binding_counts_by_owner: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    call_counts_by_owner: defaultdict[str, defaultdict[tuple[object, ...], int]] = defaultdict(
        lambda: defaultdict(int)
    )
    seen_render_ids: set[str] = set()
    seen_occurrence_ids: set[str] = set()
    flattened_transparent_receivers: set[str] = set()
    # A transparent component has no Vue definition: its template is copied
    # into the template of the component whose calls the assembler was
    # building when it reached it. Vue compiles a fill in the template of
    # its author, so a fill written by a transparent component belongs to
    # that component's template, recorded here by render id.
    transparent_template_owners: dict[str, str] = {}
    # Class names of transparent renders, so an error about a fill can name
    # the transparent component that wrote or received it.
    transparent_class_names: dict[str, str] = {}
    # While a fill that must be copied outside its author's component tree
    # is assembled, each entry collects the bindings in it that read the
    # author's browser data, keyed by the author's occurrence. It stays
    # empty on every other path, so ordinary pages pay one list check.
    # The component whose template receives the copy is tracked too: a
    # transparent component reached inside the fill is compiled there, so
    # its reads count against the fill as well.
    browser_read_trackers: list[tuple[str, str, list[str]]] = []
    # A flattened projection can copy lexical bindings into a physical
    # occurrence before that occurrence emits its own bindings.  Keep the
    # physical namespace reservations separate from the lexical counters so a
    # later physical binding cannot reuse a copied key.
    projected_data_keys_by_occurrence: defaultdict[str, set[str]] = defaultdict(set)
    supplied_fills: defaultdict[str, list[_FillFragment]] = defaultdict(list)
    tags_by_type: dict[str, str] = {}
    types_by_tag: dict[str, str] = {}
    leaf_artifacts: dict[tuple[str, int], _LeafDefinitionArtifact] = {}
    # Definitions of simple='vue' templates that call children, keyed by
    # class, template and the element text written for each call.
    leaf_call_artifacts: dict[tuple[str, int, tuple[str, ...]], _LeafDefinitionArtifact] = {}
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
        # The generated evaluator writes only strict JSON (see
        # _copy_evaluated_json), so its data only needs a copy. Other leaf
        # data is still checked and converted value by value.
        convert = _copy_evaluated_json if part.prepared_data_evaluated_plain else _json_plain
        for key, prepared_value in part.prepared_data.items():
            if key in data_values:
                raise UnsupportedPreparedView("duplicate prepared leaf-program binding key")
            # PreparedOccurrence owns this public boundary; keep it isolated
            # even when the evaluator used a private direct projection path.
            data_values[key] = convert(prepared_value)
            if projected_data_keys is not None:
                projected_data_keys.add(key)

    def note_browser_read(owner_id: str, description: str) -> None:
        """Record a binding that reads the browser data of ``owner_id``'s Vue instance."""
        # Only fills being copied outside their author's tree are checked,
        # and only bindings that read that author's data count against them.
        for author_owner, receiving_owner, reads in browser_read_trackers:
            if owner_id in {author_owner, receiving_owner}:
                reads.append(description)

    def class_name_of(render_id: str | None, occurrence: str) -> str:
        """Name the component that owns a render, preferring the transparent component itself."""
        if render_id is not None and render_id in transparent_class_names:
            return transparent_class_names[render_id]
        try:
            return citry.get_component_by_class_id(occurrence_types[occurrence]).__name__
        except KeyError:
            return occurrence_types.get(occurrence, "an unknown component")

    def describe_fill_outside_author(
        part: DirectProjectionRender, author_owner: str, physical_owner: str, first_read: str
    ) -> str:
        fill_source = part.fill_source
        author = class_name_of(fill_source.lexical_render_id, author_owner)
        receiver = class_name_of(part.receiver_render_id, physical_owner)
        physical = class_name_of(None, physical_owner)
        location = ""
        if isinstance(fill_source.source, str):
            # Spans are byte offsets into the author's template source.
            line = fill_source.source.encode("utf-8")[: fill_source.span[0]].count(b"\n") + 1
            location = f" at line {line} of {author}'s template"
        return (
            f"the {fill_source.public_name!r} fill written by {author}{location} uses {author}'s Vue data or "
            f"handlers ({first_read}), but {receiver} renders it inside {physical}, which {author} does not "
            f"contain. Vue gives a fill its author's data only inside the author's component tree. Write the "
            f"fill in a component that contains {physical} (for a citry_ui group such as CTabs, write the "
            f"declarations inside the group's tag or in a transparent component), or make the fill read only "
            f"Python values."
        )

    def note_attribute_reads(owner_id: str, tag: str, attrs: Sequence[PreparedAttribute]) -> None:
        for attr in attrs:
            if attr.origin == "source" and _source_attribute_reads_instance(
                attr.name, str(attr.value), template_context_names
            ):
                note_browser_read(owner_id, f"{attr.name} on <{tag}>")

    def note_event_reads(owner_id: str, tag: str, part: PreparedElementOpen | PreparedDynamicElementOpen) -> None:
        # The browser sends a Citry Events binding for the component whose
        # template holds it, so a copied binding reaches the wrong handler
        # even when its arguments are literals.
        if (
            part.event_bindings
            or part.poll_bindings
            or part.control_bindings
            or part.runtime_event_bindings
            or part.runtime_poll_bindings
            or part.runtime_events_candidate
        ):
            note_browser_read(owner_id, f"a Citry Events binding on <{tag}>")

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

    def call_path(ancestor: str, descendant: str, error: str) -> tuple[str, ...]:
        """Return the placement keys of the calls leading from ancestor down to descendant."""
        # Placement keys come from the call site and its explicit key, never
        # from an occurrence id, so this path is the same for every instance
        # of the ancestor. It is empty when both are the same occurrence.
        path: list[str] = []
        current = descendant
        while current != ancestor:
            placement = occurrence_placement_keys.get(current)
            parent = occurrence_parents.get(current)
            if placement is None or parent is None or len(path) > len(occurrence_parents):
                raise UnsupportedPreparedView(error)
            path.append(placement)
            current = parent
        return tuple(reversed(path))

    def transform_component(
        value: CitryRender | SimpleVueRecord,
        parent_id: str | None,
        occurrence_id: str,
        placement_key: str | None = None,
        inherited_root_markers: tuple[tuple[str, object], ...] = (),
        physical_parent_stack: tuple[str, ...] = (),
        marker_owner_id: str | None = None,
    ) -> str:
        # A simple='vue' record is its own frame. The type checker
        # forbids subclasses of the final SimpleVueRecord, so isinstance acts
        # like an exact type check and narrows
        # ``value`` for the checker at each branch below.
        is_simple = isinstance(value, SimpleVueRecord)
        frame: SimpleVueRecord | RenderFrame = value if isinstance(value, SimpleVueRecord) else value.frame
        selected_transparent_root = (
            not isinstance(value, SimpleVueRecord) and parent_id is None and value.frame.is_transparent_root
        )
        ordinary_component_root = isinstance(value, SimpleVueRecord) or (
            value.frame.is_component_root and not value.frame.is_transparent_root
        )
        if not (selected_transparent_root or ordinary_component_root) or frame.render_id is None:
            raise UnsupportedPreparedView("prepared component must be a nontransparent component root")
        if frame.render_id in seen_render_ids:
            raise UnsupportedPreparedView("render occurrence appears more than once")
        if occurrence_id in seen_occurrence_ids:
            raise UnsupportedPreparedView("prepared occurrence identity collided")
        seen_render_ids.add(frame.render_id)
        seen_occurrence_ids.add(occurrence_id)
        occurrence_to_render[occurrence_id] = frame.render_id
        raw_frame_data: object = value.js_data if isinstance(value, SimpleVueRecord) else value.context.js_data
        if server_data is not None and not is_simple:
            if frame.render_id not in server_data:
                raise UnsupportedPreparedView("component occurrence has no captured js_data")
            raw_frame_data = server_data[frame.render_id]
        if raw_frame_data is None:
            raise UnsupportedPreparedView("component occurrence has no captured js_data")
        try:
            frame_data = _json_plain(raw_frame_data)
        except (TypeError, ValueError) as error:
            # js_data() is the author's code, and the bare conversion error
            # names neither the component nor what to return instead.
            msg = f"js_data() of component {frame.class_id!r} returned a value the browser cannot receive: {error}."
            raise type(error)(msg) from error
        if type(frame_data) is not dict:
            raise TypeError(
                f"js_data() of component {frame.class_id!r} must return a dict, got {type(frame_data).__name__}"
            )
        type_key = frame.class_id
        if not type_key:
            raise UnsupportedPreparedView("component occurrence has no stable class id")
        try:
            component_class = citry.get_component_by_class_id(type_key)
        except KeyError as error:
            raise UnsupportedPreparedView("component occurrence has no current registered class") from error
        component_tag(type_key, component_class)
        live_component = None if isinstance(value, SimpleVueRecord) else value.context.component
        live_identity = (
            value.component_class is component_class and component_class.citry is citry
            if isinstance(value, SimpleVueRecord)
            else live_component is not None
            and live_component.citry is citry
            and type(live_component) is component_class
        )
        cache_replay_identity = not isinstance(value, SimpleVueRecord) and _matches_cache_replay_identity(
            value.context, citry, component_class
        )
        if not live_identity and not cache_replay_identity:
            raise UnsupportedPreparedView("prepared component does not match its engine registry identity")
        if component_class is mark_class:
            if is_simple:
                raise UnsupportedPreparedView("a simple='vue' record cannot own a prepared marker")
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
        own_root_markers = (
            _prepared_root_markers(value.root_markers)
            if isinstance(value, SimpleVueRecord)
            else _prepared_root_markers((*value.frame.root_markers, *value.context._get_root_markers()))
        )
        root_marker_values = dict(own_root_markers)
        marker_identities = {_html_attr_identity(name) for name in root_marker_values}
        for name, marker_value in inherited_root_markers:
            identity = _html_attr_identity(name)
            if identity not in marker_identities:
                root_marker_values[name] = marker_value
                marker_identities.add(identity)
        root_markers = tuple(root_marker_values.items())

        value_parts = [value.leaf] if isinstance(value, SimpleVueRecord) else value.parts
        if (
            isinstance(value, SimpleVueRecord)
            and value.leaf.call_children is not None
            and (root_markers or not value.leaf.fragment.calls_unconditional)
        ):
            # Which calls a row makes depends on its c-if branches and c-for
            # items, and root markers go onto the elements themselves, so
            # this occurrence's definition is built from its recorded values
            # (with each child at its call) the way an ordinary one is.
            value_parts = typed_leaf_parts(value.leaf)

        if not root_markers and not isinstance(value, RenderDecoration):
            parts = value_parts
            if len(parts) == 1 and isinstance(parts[0], PreparedLeafProgram):
                candidate_leaf = parts[0]
                candidate_artifact = leaf_artifacts.get((type_key, id(candidate_leaf.fragment)))
                if (
                    candidate_artifact is not None
                    and candidate_leaf.cached_typed_parts is not None
                    and any(
                        isinstance(part, PreparedElementOpen) and part.browser_bindings
                        for part in candidate_leaf.cached_typed_parts
                    )
                ):
                    candidate_artifact = None
                if candidate_artifact is not None:
                    existing_definition = definitions.get(candidate_artifact.definition_id)
                    if existing_definition is not None:
                        attach_leaf_data(candidate_leaf, prepared_values)
                        existing_input = compile_inputs.get(candidate_artifact.definition_id)
                        if (
                            existing_definition.type_key != type_key
                            or existing_input != candidate_artifact.compile_input
                        ):
                            raise AssertionError("prepared definition hash collision")
                        occurrence_definition_ids[occurrence_index] = candidate_artifact.definition_id
                        return occurrence_id  # early cached leaf return

        local_identity_keys: set[tuple[tuple[object, ...], tuple[str, ...], object]] = set()
        # Transparent roots keep their own key namespace: the wrapper we emit for a
        # transparent render sits at the same source span and route as the ordinary
        # call it wraps, so sharing `local_identity_keys` would reject that pair as a
        # duplicate even though only one of them owns the key.
        local_transparent_identity_keys: set[tuple[tuple[object, ...], tuple[str, ...], object]] = set()
        python_counts_by_route: defaultdict[tuple[str, ...], int] = defaultdict(int)
        slot_site_counts: defaultdict[tuple[tuple[object, ...], tuple[str, ...]], int] = defaultdict(int)
        keyed_slot_counts: defaultdict[tuple[tuple[object, ...], tuple[str, ...], tuple[str, ...]], int] = defaultdict(
            int
        )
        dynamic_site_index = 0

        active_projected_data_keys: list[set[str] | None] = []
        active_projected_data_containers: list[set[str] | None] = []

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
                    # deterministic suffix only on collision. The key lands in
                    # the compiled template, so it is built from the binding's
                    # position alone, which is the same for every instance;
                    # the loop below keeps it unique.
                    key = f"citry{prefix}p{_digest('projected', prefix, index)[:20]}"
                    suffix = 0
                    while key in physical_values or key in reserved_keys:
                        suffix += 1
                        key = f"citry{prefix}p{_digest('projected', prefix, index, suffix)[:20]}"
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
            child_placement_key: str,
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
                    # The fill's author is further up, so pass it on through a
                    # slot outlet written here. This text is compiled into the
                    # definition of definition_owner_id (a component body
                    # carried into a child keeps its own owner), and Vue
                    # resolves the outlet against that component's own slots,
                    # so its call is the one that must carry the fill.
                    #
                    # Slot names are built without occurrence ids so instances
                    # can share definitions, which lets two receivers below one
                    # definition use the same name. Rename the passed-on slot
                    # after the child call it goes through; that call's
                    # placement key is the same for every instance.
                    forwarded_site_id = f"citrySlot{_digest('forwarded', fill.site_id, child_placement_key)[:16]}"
                    supplied_fills[definition_owner_id].append(
                        _FillFragment(forwarded_site_id, fill.public_name, fill.lexical_owner, fill.body)
                    )
                    output.append(f'<slot name="{forwarded_site_id}"{context_binding_attrs}></slot>')
                output.append("</template>")

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
            parent_element_keys: tuple[str | None, ...] | None = None,
            projected_data: bool = False,
        ) -> _DefinitionFragment:
            nonlocal dynamic_site_index
            output = _DefinitionFragment.empty()
            dynamic_stack: list[tuple[str, str]] = []
            element_stack = list(parent_element_stack)
            # The `#c-key` of each open element, in step with element_stack
            # (None for an unkeyed one). A slot outlet inside keyed rows takes
            # its identity from these keys, so it follows its row when the rows
            # reorder. A body that starts a new component inherits no keys.
            element_keys: list[str | None] = (
                [None] * len(element_stack) if parent_element_keys is None else list(parent_element_keys)
            )
            if len(element_keys) != len(element_stack):
                raise AssertionError("prepared element keys must follow the element stack")
            inherited_element_depth = len(element_stack)
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

            run_first: dict[int, list[CitryRender | SimpleVueRecord]] = {}
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
                    and (member_type := _run_member_metadata(candidate)[0]) == call_run.child_type_key
                    and (member_metadata := _run_member_metadata(candidate)[1]) is not None
                    and member_metadata.source is call_node.source
                    and member_metadata.source_span == call_node.position
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
                        parent_element_keys=tuple(element_keys),
                        projected_data=projected_data,
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
                        f'<component v-for="citryOccurrenceId in $citryPrepared.callRuns.{run_id}" '
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

            def append_ignored_contents(
                output: _DefinitionFragment,
                parts: Sequence[RenderPart],
                open_index: int,
                data_values: dict[str, object],
            ) -> int:
                """Write a `#c-ignore` element's contents as one pinned HTML block; return the close index."""
                opening = cast("PreparedElementOpen", parts[open_index])
                label = _ignored_element_label(opening)
                # The browser keeps the block as HTML parsed in an HTML parent,
                # so an SVG or MathML parent or a text-only element cannot hold it.
                if any(tag in {"svg", "math"} for tag in element_stack):
                    raise UnsupportedPreparedView(
                        f"{label} is inside SVG or MathML, whose contents the browser cannot keep as HTML."
                        " Put '#c-ignore' on an HTML element that wraps the <svg> or <math> element."
                    )
                if opening.tag.lower() in {"script", "style", "textarea", "title"}:
                    raise UnsupportedPreparedView(
                        f"{label} has text contents, not elements, so there is nothing to keep. Remove '#c-ignore'."
                    )
                close_index = _ignored_element_close_index(parts, open_index)
                html = _ignored_contents_html(
                    opening,
                    parts[open_index + 1 : close_index],
                    lambda class_id: citry.get_component_by_class_id(class_id).__name__,
                )
                reject_cross_boundary_html(html, origin=f"The HTML inside {label.removesuffix(',')}")
                key = data_key("Opaque", opening.source, opening.span, data_owner_id)
                projected_data_container("opaqueHtml")
                opaque_values = data_values.setdefault("opaqueHtml", {})
                if type(opaque_values) is not dict:
                    raise AssertionError("prepared opaqueHtml container changed type")
                record = opaque_html_record(html, pinned=True)
                if opaque_values.setdefault(key, record) != record:
                    raise UnsupportedPreparedView("one prepared opaque HTML site produced conflicting bytes")
                start = output.byte_length
                output.append(f'<citry-opaque-html :record="$citryPrepared.opaqueHtml.{key}">')
                end = output.byte_length
                output.append("</citry-opaque-html>")
                output.opaque_html_sites.append({"key": key, "sourceStart": start, "sourceEnd": end, "origin": "raw"})
                return close_index

            # Parts before this index are a `#c-ignore` element's contents,
            # already written as one block of HTML the browser keeps.
            ignored_contents_end = 0
            for part_index, part in enumerate(parts):
                if part_index in run_followers or part_index < ignored_contents_end:
                    continue
                if isinstance(part, DirectProjectionRender):
                    nested_template = isinstance(part, DirectNestedTemplateRender)
                    fill_source = part.fill_source
                    if not isinstance(fill_source.source, str):
                        raise UnsupportedPreparedView("direct slot source must be template text")
                    receiver_owner = _stable_owner(part.receiver_render_id, render_to_occurrence)
                    if receiver_owner is None:
                        raise UnsupportedPreparedView("direct slot ownership has no prepared occurrence")
                    # The slot name is written into the compiled templates, so
                    # it must be the same for every instance and every render
                    # of this structure. Occurrence ids differ per instance,
                    # and an Events update renders its target under the id the
                    # browser already holds, so they cannot be used. Name the
                    # receiver by the placement keys from it down to this
                    # occurrence: they are the same for every instance and
                    # still separate one outlet passed into several keyed
                    # children of the same receiver.
                    source_key = (
                        occurrence_types[occurrence_id],
                        fill_source.kind,
                        part.source,
                        part.span,
                        # A receiver always encloses the outlets it forwards, so
                        # a receiver that is not an ancestor means the slot
                        # result was moved.
                        call_path(receiver_owner, occurrence_id, "direct slot result moved outside its receiver"),
                    )
                    site_identity = (source_key, placement_route)
                    site_index = slot_site_counts[site_identity]
                    slot_site_counts[site_identity] += 1
                    # Positional ordinals alone make a slot inside a keyed
                    # transparent wrapper change identity when sibling wrappers
                    # reorder. Scope the ordinal by its placement route instead.
                    site_digest = (
                        _digest(source_key, site_index)
                        if not placement_route
                        else _digest(source_key, placement_route, site_index)
                    )
                    site_id = f"citrySlot{site_digest[:16]}"
                    # Python writes one outlet per row of a keyed element (a
                    # table row), and the slot name stays positional so the
                    # compiled template does not change with the row data. Vue
                    # keys the outlet's content by its position too, so a row
                    # that moves would rebuild it. Give the outlet a key from
                    # the enclosing element keys, sent as data, so the content
                    # moves with its row.
                    element_key_route = tuple(key for key in element_keys if key is not None)
                    slot_key = None
                    if element_key_route:
                        keyed_identity = (source_key, placement_route, element_key_route)
                        keyed_index = keyed_slot_counts[keyed_identity]
                        keyed_slot_counts[keyed_identity] += 1
                        slot_key = f"citrySlotKey{_digest(*keyed_identity, keyed_index)[:24]}"
                    lexical_owner = _stable_owner(fill_source.lexical_render_id, render_to_occurrence)
                    if lexical_owner is None:
                        raise UnsupportedPreparedView("direct slot ownership has no prepared occurrence")
                    # Vue compiles a fill in its author's render function and
                    # reads the fill's values from that component's
                    # $citryPrepared. A transparent author has no render
                    # function of its own: its template, and so every fill it
                    # writes, is compiled in the template it was copied into.
                    # That component owns the fill, not the occurrence where
                    # the assembler happened to reach the transparent author.
                    lexical_owner = transparent_template_owners.get(fill_source.lexical_render_id, lexical_owner)
                    # A transparent receiver has no Vue definition to take a
                    # slot, so its fill is copied into the template being
                    # built when that template is its author's.
                    flattened_transparent_receiver = (
                        not nested_template
                        and part.receiver_render_id in flattened_transparent_receivers
                        and lexical_owner == call_owner_id
                    )
                    # Otherwise the template being built belongs to another
                    # component. When the author encloses the receiver, the
                    # ordinary branch below turns the fill into a Vue slot
                    # that is passed up to the author's call. Vue passes slots
                    # only down the component tree, so an author outside it
                    # (a sibling) cannot supply one: copying is the only way
                    # to place the fill, and it is safe only when the fill
                    # reads no browser data.
                    copied_outside_author = False
                    if (
                        not nested_template
                        and not flattened_transparent_receiver
                        and part.receiver_render_id in flattened_transparent_receivers
                    ):
                        try:
                            call_path(lexical_owner, receiver_owner, "fill author does not enclose its receiver")
                        except UnsupportedPreparedView:
                            flattened_transparent_receiver = True
                            copied_outside_author = True
                    # Calls inside this body are counted and keyed in the
                    # lexical owner's namespace, so two receivers that share
                    # one slot name must still give their bodies different
                    # routes. The keyed call path from the lexical owner to
                    # the receiver separates them without an occurrence id.
                    # A receiver outside the owner's subtree is rejected
                    # further down, so it only needs some route here.
                    try:
                        receiver_route = call_path(lexical_owner, receiver_owner, "slot receiver is outside its owner")
                    except UnsupportedPreparedView:
                        receiver_route = ()
                    body_route_step = site_id if not receiver_route else f"{site_id}@{_digest(receiver_route)[:16]}"
                    # The selection predicate below is emitted into the
                    # current fragment. A supplied outer slot can project that
                    # fragment into its lexical owner's definition, so store
                    # the value in the occurrence data (`$citryPrepared`) that evaluates it.
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
                        if slot_key is not None:
                            # The outlet's key is read where its selection is.
                            slot_keys = selection_data.setdefault("slotKeys", {})
                            if type(slot_keys) is not dict:
                                raise AssertionError("prepared slotKeys container changed type")
                            if slot_keys.setdefault(site_id, slot_key) != slot_key:
                                raise UnsupportedPreparedView("one prepared slot site received conflicting keys")
                    fill_reads: list[str] = []
                    if copied_outside_author:
                        browser_read_trackers.append((lexical_owner, call_owner_id, fill_reads))
                    selected = transform_parts(
                        list(part.parts),
                        placement_route=(*placement_route, body_route_step),
                        data_owner_id=lexical_owner,
                        # A flattened transparent receiver contributes its
                        # selected body directly to the fragment being built,
                        # which belongs to this fragment's call owner (the fill
                        # author when this body sits inside a fill).  A real
                        # receiver instead carries a supplied fill back to its
                        # lexical caller, where Vue creates the slot closure.
                        # Keep those destinations separate from the lexical
                        # value owner: using the intermediate receiver here
                        # makes every forwarded call declaration land in the
                        # wrong $citryPrepared.calls table.
                        call_owner_id=call_owner_id if flattened_transparent_receiver else lexical_owner,
                        containing_slot=part,
                        project_root_markers=project_root_markers and dom_depth == 0,
                        parent_element_stack=tuple(element_stack),
                        parent_element_keys=tuple(element_keys),
                        projected_data=projected_data or flattened_transparent_receiver,
                    )
                    if copied_outside_author:
                        browser_read_trackers.pop()
                        if fill_reads:
                            raise UnsupportedPreparedView(
                                describe_fill_outside_author(part, lexical_owner, receiver_owner, fill_reads[0])
                            )
                    if flattened_transparent_receiver:
                        output.extend(selected)
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
                        output.append(f'<slot name="{site_id}"{context_binding_attrs}></slot>')
                    elif nested_template:
                        supplied_fills[output_owner].append(fill)
                        output.append(f'<slot name="{site_id}"{context_binding_attrs}></slot>')
                    elif lexical_owner == output_owner:
                        _append_slot_outlet(
                            output, site_id, selected, context_binding_attrs, keyed=slot_key is not None
                        )
                    else:
                        supplied_fills[output_owner].append(fill)
                        _append_slot_outlet(
                            output,
                            site_id,
                            _DefinitionFragment.empty(),
                            context_binding_attrs,
                            keyed=slot_key is not None,
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
                        parent_element_keys=tuple(element_keys),
                        projected_data=projected_data,
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
                            parent_element_keys=tuple(element_keys),
                            projected_data=projected_data,
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
                            parent_element_keys=tuple(element_keys),
                            projected_data=projected_data,
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
                            parent_element_keys=tuple(element_keys),
                            projected_data=projected_data,
                        )
                    )
                    continue
                if type(part) in {CitryRender, DirectPythonComponentRender, RenderDecoration, SimpleVueRecord}:
                    # The other two classes in the set subclass CitryRender, so
                    # ``part`` is a CitryRender or a SimpleVueRecord. The type
                    # checker forbids record subclasses, so isinstance agrees
                    # with an exact check.
                    render_part = cast("CitryRender | SimpleVueRecord", part)
                    simple_part = isinstance(render_part, SimpleVueRecord)
                    if not isinstance(render_part, SimpleVueRecord) and not render_part.frame.is_component_root:
                        validate_flattened_render_identity(render_part, "transparent")
                        transparent_render_id = render_part.frame.render_id
                        if transparent_render_id is not None:
                            if render_part.frame.is_transparent_root and (
                                transparent_render_id not in render_to_occurrence
                                or transparent_render_id in flattened_transparent_receivers
                            ):
                                flattened_transparent_receivers.add(transparent_render_id)
                            prior_owner = render_to_occurrence.setdefault(transparent_render_id, occurrence_id)
                            # The body below is copied into the template that
                            # call_owner_id compiles, so fills this component
                            # writes are compiled there too.
                            prior_template_owner = transparent_template_owners.setdefault(
                                transparent_render_id, call_owner_id
                            )
                            if prior_template_owner != call_owner_id:
                                raise UnsupportedPreparedView(
                                    "transparent prepared render was copied into two component templates"
                                )
                            if render_part.frame.class_name:
                                transparent_class_names[transparent_render_id] = render_part.frame.class_name
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
                            parent_element_keys=tuple(element_keys),
                            projected_data=projected_data,
                        )
                        if wrapper_key is None:
                            output.extend(transparent_body)
                            continue

                        # The false template keeps a keyed Fragment root even
                        # when the transparent body has zero or one root node.
                        keyed_body = _DefinitionFragment.empty()
                        wrapper_start = keyed_body.byte_length
                        keyed_body.append(f'<template v-if="true" :key="$citryPrepared.{wrapper_binding}">')
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
                    child_prepared = (
                        None if isinstance(render_part, SimpleVueRecord) else render_part.frame.prepared_occurrence
                    )
                    metadata = (
                        render_part.call_metadata
                        if isinstance(render_part, SimpleVueRecord)
                        else child_prepared.call
                        if child_prepared is not None
                        else None
                    )
                    python_call = type(part) is DirectPythonComponentRender or (
                        isinstance(render_part, SimpleVueRecord) and render_part.python_composition
                    )
                    if metadata is None and not python_call:
                        raise UnsupportedPreparedView("nested component has no prepared call metadata")
                    child_type = (
                        render_part.class_id
                        if isinstance(render_part, SimpleVueRecord)
                        else render_part.frame.class_id
                    )
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
                            member_type, member_metadata = _run_member_metadata(member)
                            if member_metadata is None:
                                raise UnsupportedPreparedView("call-run member has no prepared call metadata")
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
                                f'<component v-for="citryOccurrenceId in $citryPrepared.callRuns.{run_id}" '
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
                                f'<{tag} :citry-id="$citryPrepared.calls.{local_id}.id" '
                                f':key="$citryPrepared.calls.{local_id}.key">'
                            )
                            opening_end = output.byte_length
                            append_child_fills(
                                output,
                                member_fills,
                                definition_owner_id=call_owner_id,
                                child_placement_key=member_placement_key,
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
                    # A simple='vue' record carries no component-tag bindings;
                    # every other nested component must have its prepared metadata.
                    component_bindings: tuple[PreparedComponentBinding, ...] = ()
                    child_call: _PreparedCallMetadata | None = None
                    if child_prepared is not None:
                        component_bindings = child_prepared.component_tag_client_bindings
                        child_call = child_prepared.call
                    elif not simple_part:
                        raise UnsupportedPreparedView("nested component has no prepared occurrence metadata")
                    for component_binding in component_bindings:
                        if type(component_binding) is not PreparedComponentBinding:
                            raise UnsupportedPreparedView(
                                "component call component_binding metadata changed after capture"
                            )
                        if browser_read_trackers and (
                            component_binding.kind is ComponentTagClientBindingKind.CITRY_HANDLER
                            or _vue_binding_reads_instance(
                                component_binding.key,
                                component_binding.value if component_binding.value != "" else None,
                                template_context_names,
                            )
                        ):
                            note_browser_read(
                                data_owner_id,
                                f"{component_binding.key} on the call to "
                                f"{citry.get_component_by_class_id(child_type).__name__}",
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
                            # The binding is stored on the data owner and the
                            # browser dispatches it from that instance, so its
                            # handler must come from that class. Inside a
                            # supplied fill this is the fill's author, not the
                            # receiver whose occurrence is being captured.
                            handler_class = citry.get_component_by_class_id(occurrence_types[data_owner_id])
                            compiled_event = compile_citry_boundary_binding(
                                events_extension.resolve(handler_class),
                                handler_class.__name__,
                                f"c-{getattr(child_class, 'name', None) or child_class.__name__}",
                                component_binding.key,
                                component_binding.value,
                                line=line,
                                column=column,
                            )
                            # Vue gives a component tag no element of its own to
                            # run a timer on, so a polling or timed binding must
                            # move onto an element inside the child's template.
                            child_tag = _authored_call_tag(
                                child_call,
                                f"c-{(getattr(child_class, 'name', None) or child_class.__name__).lower()}",
                            )
                            # Quote the example so it stays valid HTML whatever the value holds.
                            quote = "'" if '"' in component_binding.value else '"'
                            example_value = f"{quote}{component_binding.value}{quote}"
                            move_hint = (
                                f"Put the binding on an element inside the template of {child_class.__name__}"
                                f" instead, for example <div {component_binding.key}={example_value}>."
                                f" The handler then runs on {child_class.__name__}, so declare it in"
                                f" {child_class.__name__}.Events."
                            )
                            if compiled_event.channel != _CHANNEL_EVENT:
                                raise UnsupportedPreparedView(
                                    f"'{component_binding.key}' on <{child_tag}> (line {line}, column {column})"
                                    f" cannot poll, because a component tag has no element to poll from. {move_hint}"
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
                                    f"'{component_binding.key}' on <{child_tag}> (line {line}, column {column})"
                                    " cannot use '.debounce' or '.throttle', because a component tag has no element"
                                    f" to time the event on. {move_hint} Or remove the timing modifier."
                                )
                            # A body folded into another definition must carry
                            # this table along, as the element event sites do.
                            projected_data_container("eventBindings")
                            event_values = data_values.setdefault("eventBindings", {})
                            if type(event_values) is not dict:
                                raise AssertionError("prepared eventBindings container changed type")
                            serialized_event = _json_plain(event_component_binding)
                            previous_event = event_values.setdefault(component_binding_id, serialized_event)
                            if previous_event != serialized_event:
                                raise UnsupportedPreparedView(
                                    "one prepared component event site has conflicting authored metadata"
                                )
                            # Vue calls a component listener from the parent's
                            # render, and the emitted payload need not be an
                            # Event, so `$el` is the child's root element that
                            # the runtime looks up from the call id.
                            authored_args = _generated_event_args(
                                event_component_binding["args"],
                                el_expression=f"$citryEvents.componentRoot($citryPrepared.calls.{local_id}.id)",
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
                        # Vue hands `v-show` and a custom directive to the
                        # element the child renders at its root, so that root
                        # is checked after compilation. The first one names
                        # the error.
                        if (
                            component_binding.kind
                            in {ComponentTagClientBindingKind.SHOW, ComponentTagClientBindingKind.DIRECTIVE}
                            and child_id not in root_directive_occurrences
                        ):
                            child_class = citry.get_component_by_class_id(child_type)
                            root_directive_occurrences[child_id] = (
                                child_class.__name__,
                                _authored_call_tag(
                                    child_call,
                                    f"c-{(getattr(child_class, 'name', None) or child_class.__name__).lower()}",
                                ),
                                component_binding.key,
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
                        try:
                            # `v-else` and a valueless custom directive keep
                            # their bare authored form.
                            source_attr = (
                                component_binding.key
                                if component_binding.value == ""
                                else _authored_vue_attr(component_binding.key, component_binding.value)
                            )
                        except ValueError as error:
                            raise UnsupportedPreparedView(str(error)) from error
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
                    output.append(f' :citry-id="$citryPrepared.calls.{local_id}.id"')
                    output.append(f' :key="$citryPrepared.calls.{local_id}.key"')
                    output.append(">")
                    opening_end = output.byte_length
                    fills = tuple(supplied_fills.pop(child_id, ()))
                    append_child_fills(
                        output,
                        fills,
                        definition_owner_id=call_owner_id,
                        child_placement_key=placement_key,
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
                        raise UnsupportedPreparedView(
                            "<c-raw> cannot sit inside <svg> or <math> in an interactive component, because Vue"
                            " inserts its HTML with the HTML parser. Move the <c-raw> block outside, or write the"
                            " SVG or MathML markup directly in the template."
                        )
                    if parent_tag in {"script", "style", "textarea", "title"}:
                        raise UnsupportedPreparedView(
                            f"<c-raw> cannot sit inside <{parent_tag}> in an interactive component, because"
                            f" <{parent_tag}> holds text, not HTML. Write the text directly inside <{parent_tag}>."
                        )
                    from citry.ext.events.bindings import _line_column  # noqa: PLC0415

                    raw_line, raw_column = _line_column(part.source, part.span[0])
                    reject_cross_boundary_html(
                        part.html, origin=f"The <c-raw> block at line {raw_line}, column {raw_column}"
                    )
                    html = mark_opaque_html(
                        part.html,
                        root_markers if project_root_markers and dom_depth == 0 else (),
                    )
                    key = data_key("Opaque", part.source, part.span, data_owner_id)
                    projected_data_container("opaqueHtml")
                    opaque_values = data_values.setdefault("opaqueHtml", {})
                    if type(opaque_values) is not dict:
                        raise AssertionError("prepared opaqueHtml container changed type")
                    record = opaque_html_record(html)
                    prior = opaque_values.setdefault(key, record)
                    if prior != record:
                        raise UnsupportedPreparedView("one prepared opaque HTML site produced conflicting bytes")
                    start = output.byte_length
                    output.append(f'<citry-opaque-html :record="$citryPrepared.opaqueHtml.{key}">')
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
                                element_keys.append(None)
                            elif (
                                operation == "close"
                                and len(element_stack) > inherited_element_depth
                                and element_stack[-1] == tag
                            ):
                                element_stack.pop()
                                element_keys.pop()
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
                    if (
                        browser_read_trackers
                        and text_browser_binding is not None
                        and text_browser_binding.values_expression is not None
                        and _vue_expression_reads_instance(
                            text_browser_binding.values_expression,
                            handler=False,
                            allowed_names=template_context_names,
                        )
                    ):
                        note_browser_read(data_owner_id, f"the values of {text_browser_binding.helper}() in text")
                    if text_browser_binding is None:
                        output.append(f"{{{{ $citryPrepared.{key} }}}}")
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
                        output.append(f"{{{{ {text_browser_binding.helper}($citryPrepared.{operand_key}{thunk}) }}}}")
                    continue
                if isinstance(part, (PreparedTrustedHtmlValue, Markup)):
                    serialized = part.html if isinstance(part, PreparedTrustedHtmlValue) else str(part)
                    parent_tag = element_stack[-1] if element_stack else None
                    if any(tag in {"svg", "math"} for tag in element_stack):
                        raise UnsupportedPreparedView(
                            "A Markup value (trusted HTML from Python) cannot sit inside <svg> or <math> in an"
                            " interactive component, because Vue inserts it with the HTML parser. Write the SVG or"
                            " MathML markup in the template, or render the whole <svg> element from the value."
                        )
                    if parent_tag in {"script", "style", "textarea", "title"}:
                        raise UnsupportedPreparedView(
                            f"A Markup value (trusted HTML from Python) cannot sit inside <{parent_tag}> in an"
                            f" interactive component, because <{parent_tag}> holds text, not HTML. Pass a plain"
                            " string instead."
                        )
                    if "<" not in serialized:
                        value = unescape(serialized)
                        if parent_tag == "textarea" and serialized.startswith("\n"):
                            value = value[1:]
                        key = data_key("Text", serialized, (0, len(serialized.encode())), data_owner_id)
                        data_values[key] = value
                        output.append(f"{{{{ $citryPrepared.{key} }}}}")
                        continue
                    reject_cross_boundary_html(serialized, origin="A Markup value (trusted HTML from Python)")
                    html = mark_opaque_html(
                        serialized,
                        root_markers if project_root_markers and dom_depth == 0 else (),
                    )
                    key = data_key("Opaque", serialized, (0, len(serialized.encode())), data_owner_id)
                    projected_data_container("opaqueHtml")
                    opaque_values = data_values.setdefault("opaqueHtml", {})
                    if type(opaque_values) is not dict:
                        raise AssertionError("prepared opaqueHtml container changed type")
                    record = opaque_html_record(html)
                    prior = opaque_values.setdefault(key, record)
                    if prior != record:
                        raise UnsupportedPreparedView("one prepared opaque HTML site produced conflicting bytes")
                    start = output.byte_length
                    output.append(f'<citry-opaque-html :record="$citryPrepared.opaqueHtml.{key}">')
                    end = output.byte_length
                    output.append("</citry-opaque-html>")
                    output.opaque_html_sites.append(
                        {"key": key, "sourceStart": start, "sourceEnd": end, "origin": "markup"}
                    )
                    continue
                if isinstance(part, PreparedLeafProgram):
                    if browser_read_trackers and part.fragment.browser_requirements:
                        # A compiled leaf keeps its bindings only as template
                        # text, so a leaf that needs Vue or Events counts as
                        # reading its component rather than being parsed here.
                        note_browser_read(data_owner_id, "a compiled Vue or Events binding")
                    attach_leaf_data(part, data_values, projected_keys)
                    fragment = _DefinitionFragment(
                        [part.fragment.template],
                        len(part.fragment.template.encode()),
                        [],
                        [cast("_ElementBindingDeclaration", dict(value)) for value in part.fragment.element_bindings],
                        [],
                        [],
                        # Leaf programs write no opaque HTML, so they add no sites.
                        [],
                        [cast("_RuntimeEventDeclaration", dict(value)) for value in part.fragment.runtime_event_sites],
                    )
                    output.extend(fragment)
                    continue
                if isinstance(part, PreparedElementOpen):
                    if browser_read_trackers:
                        note_attribute_reads(data_owner_id, part.tag, part.attrs)
                        note_event_reads(data_owner_id, part.tag, part)
                        for browser_binding in part.browser_bindings:
                            if browser_binding.values_expression is not None and _vue_expression_reads_instance(
                                browser_binding.values_expression, handler=False, allowed_names=template_context_names
                            ):
                                note_browser_read(data_owner_id, f"{browser_binding.name} on <{part.tag}>")
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
                        expression = escape(
                            f"{browser_binding.helper}($citryPrepared.{operand_key}{thunk})", quote=True
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
                    executable_data_attrs = [name for name in effective_data_attrs if is_vue_directive_name(name)]
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
                    conflict = conflicting_attribute_targets(source_targets, data_targets)
                    if conflict:
                        names = [f"{source_targets[identity]!r} / {data_targets[identity]!r}" for identity in conflict]
                        raise UnsupportedPreparedView(
                            f"authored Vue and prepared Python attributes target the same HTML name: {names!r}"
                        )
                    has_object_binding = any(
                        attr.name == "v-bind" or attr.name.startswith("v-bind.")
                        for attr in part.attrs
                        if attr.origin == "source"
                    )
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
                        element_stack.append(part.tag.lower())
                        element_keys.append(
                            json.dumps(element_metadata["key"], sort_keys=True, separators=(",", ":"))
                            if "key" in element_metadata
                            else None
                        )
                        dom_depth += 1
                    if is_ignored_element_open(part) and not part.is_void:
                        ignored_contents_end = append_ignored_contents(output, parts, part_index, data_values)
                    continue
                if isinstance(part, PreparedDynamicElementOpen):
                    if not is_authenticated_dynamic_element_open(part):
                        raise UnsupportedPreparedView(
                            "dynamic element opening lacks exact validated producer provenance"
                        )
                    if browser_read_trackers:
                        note_attribute_reads(data_owner_id, part.tag, part.authored_attrs)
                        note_event_reads(data_owner_id, part.tag, part)
                    invalid_attrs = [
                        name
                        for name in part.attrs
                        if type(name) is not str or is_vue_directive_name(name) or _unsafe_dynamic_dom_property(name)
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
                    conflict = conflicting_attribute_targets(source_targets, data_targets)
                    if conflict:
                        names = [f"{source_targets[identity]!r} / {data_targets[identity]!r}" for identity in conflict]
                        raise UnsupportedPreparedView(
                            f"authored Vue and prepared Python attributes target the same HTML name: {names!r}"
                        )
                    has_prepared_target = bool(effective_dynamic_attrs) or part.key is not None
                    if has_prepared_target and any(
                        attr.name == "v-bind" or attr.name.startswith("v-bind.") for attr in part.authored_attrs
                    ):
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
                    # The Python values go before an authored `:class` or
                    # `:style` (see `prepared_spread_index`), and otherwise
                    # after every authored attribute, beside the marker below.
                    spread_index = prepared_spread_index(attr.value for attr in part.authored_attrs)
                    for index, attr in enumerate(part.authored_attrs):
                        if index == spread_index:
                            output.append(f' v-bind="$citryPrepared.{attrs_key}"')
                        output.append(f" {attr.value}")
                    # A native form control marks which of its properties an
                    # authored or Python binding owns, so the browser keeps a
                    # user's unsaved edit only in the properties nothing binds.
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
                    if spread_index is None:
                        output.append(f' v-bind="$citryPrepared.{attrs_key}"')
                    if native_marker:
                        output.append(f" {native_marker}")
                    key_key = None
                    if part.key is not None:
                        key_key = data_key("Key", alias, (0, 0), data_owner_id)
                        data_values[key_key] = _json_plain(part.key)
                        output.append(f' :key="$citryPrepared.{key_key}"')
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
                            " v-citry-runtime-events="
                            f'"$citryEvents.runtimeEvents($citryPrepared.{runtime_events_key})"'
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
                        element_stack.append(part.tag.lower())
                        element_keys.append(
                            None if part.key is None else json.dumps(part.key, sort_keys=True, separators=(",", ":"))
                        )
                        dom_depth += 1
                    continue
                if isinstance(part, PreparedDynamicElementClose):
                    if not dynamic_stack or dynamic_stack[-1][0] != part.tag:
                        raise UnsupportedPreparedView("dynamic element close has no opening")
                    _, alias = dynamic_stack.pop()
                    output.append(f"</{alias}>")
                    if len(element_stack) <= inherited_element_depth or element_stack.pop() != part.tag.lower():
                        raise UnsupportedPreparedView("dynamic element stack changed during text capture")
                    element_keys.pop()
                    dom_depth -= 1
                    continue
                if isinstance(part, PreparedElementClose):
                    output.append(f"</{part.tag}>")
                    if len(element_stack) <= inherited_element_depth or element_stack.pop() != part.tag.lower():
                        raise UnsupportedPreparedView("prepared element stack changed during text capture")
                    element_keys.pop()
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

        if isinstance(value, SimpleVueRecord) and value.leaf.call_children is not None and value_parts == [value.leaf]:
            # Every row of this template makes the same calls at the same
            # places, so all its rows share one definition: the compiled
            # template with each child's component element written at its
            # call. Each child is still assembled as an ordinary call.
            call_leaf = value.leaf
            call_fragment_source = call_leaf.fragment
            call_children = cast("LeafCallChildren", call_leaf.call_children).parts
            if len(call_children) != len(call_fragment_source.calls):
                raise UnsupportedPreparedView("simple='vue' called children do not match the template's calls")
            attach_leaf_data(call_leaf, prepared_values)
            call_outputs = [
                transform_parts([child], parent_element_stack=(*physical_parent_stack, *call.element_stack))
                for call, child in zip(call_fragment_source.calls, call_children, strict=True)
            ]
            # The element text names the child's tag and call id, both fixed
            # by the call site and the child's class, so equal text means an
            # equal definition.
            call_artifact_key = (
                type_key,
                id(call_fragment_source),
                tuple("".join(item.chunks) for item in call_outputs),
            )
            call_artifact = leaf_call_artifacts.get(call_artifact_key)
            if call_artifact is None:
                combined = _DefinitionFragment.empty()
                segments = _leaf_template_segments(call_fragment_source)
                for segment, call_output in zip(segments, [*call_outputs, None], strict=True):
                    combined.extend(segment)
                    if call_output is not None:
                        combined.extend(call_output)
                call_compile_input = combined.compile_input(template_context_names)
                call_artifact = _LeafDefinitionArtifact(
                    _definition_id(type_key, call_compile_input), call_compile_input
                )
                leaf_call_artifacts[call_artifact_key] = call_artifact
            call_definition_id = call_artifact.definition_id
            existing_call_definition = definitions.get(call_definition_id)
            if existing_call_definition is not None:
                if (
                    existing_call_definition.type_key != type_key
                    or compile_inputs.get(call_definition_id) != call_artifact.compile_input
                ):
                    raise AssertionError("prepared definition hash collision")
            else:
                definitions[call_definition_id] = _AssembledDefinition(call_definition_id, type_key)
                compile_inputs[call_definition_id] = call_artifact.compile_input
            occurrence_definition_ids[occurrence_index] = call_definition_id
            return occurrence_id

        raw_parts = list(value_parts)
        logical_parts = _logical_typed_body(raw_parts)
        selected_parts: list[RenderPart] = (
            [value]
            if isinstance(value, RenderDecoration) and not (value.omit_around_document and logical_parts != raw_parts)
            else logical_parts
        )
        leaf = selected_parts[0] if len(selected_parts) == 1 else None
        if root_markers and isinstance(leaf, PreparedLeafProgram):
            selected_parts = typed_leaf_parts(leaf)
            leaf = None
        artifact = leaf_artifacts.get((type_key, id(leaf.fragment))) if isinstance(leaf, PreparedLeafProgram) else None
        if isinstance(leaf, PreparedLeafProgram) and leaf.cached_typed_parts is not None:
            # Generated leaf programs cannot carry extension browser bindings;
            # only a cached typed fallback needs this scan.  Avoid rebuilding
            # ordinary generated parts just to discover that fact.
            typed_leaf = leaf.cached_typed_parts
            if any(isinstance(part, PreparedElementOpen) and part.browser_bindings for part in typed_leaf):
                selected_parts = list(typed_leaf)
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
                fragment = transform_parts(
                    selected_parts,
                    parent_element_stack=physical_parent_stack,
                )
                compile_input = fragment.compile_input(template_context_names)
            definition_id = _definition_id(type_key, compile_input)
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

    root_record: SimpleVueRecord | None = root_simple_record
    root_type = render.frame.class_id
    if root_record is not None:
        root_type = root_record.class_id
    elif not root_type and len(render.parts) == 1 and type(render.parts[0]) is SimpleVueRecord:
        root_record = cast("SimpleVueRecord", render.parts[0])
        root_type = root_record.class_id
    if not root_type:
        raise UnsupportedPreparedView("root component has no stable class id")
    root_id = f"citryOccurrence{_digest('root', root_type)[:24]}" if root_occurrence_id is None else root_occurrence_id
    if type(root_id) is not str:
        raise UnsupportedPreparedView("prepared root occurrence id is not a string")
    if re.fullmatch(r"citryOccurrence[0-9A-Za-z]+", root_id) is None:
        raise UnsupportedPreparedView("prepared root occurrence id is not generated-safe")
    transform_component(root_record or render, None, root_id, marker_owner_id=root_id)
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
    owned_names: set[tuple[str, str]] = set()
    for item in ordered_markers:
        if (item.owner_id, item.name) in owned_names:
            # The render loop already rejects this when the owner settles, so
            # this runs only if the two disagree about which component owns a
            # region. Even then the author should see the same plain message.
            raise repeated_mark_name_error(class_name_of(None, item.owner_id), item.name)
        owned_names.add((item.owner_id, item.name))
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
    return Assembly(
        view,
        dict(render_to_occurrence),
        dict(occurrence_to_render),
        compile_inputs,
        root_directive_occurrences,
    )


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


def _authored_call_tag(call: _PreparedCallMetadata | None, fallback: str) -> str:
    """Return the tag name the author wrote for a call, for error messages."""
    if call is None:
        return fallback
    # Call spans are byte offsets into the authored template source.
    start = call.source_span[0]
    head = call.source.encode()[start : start + 256].decode(errors="ignore")
    match = re.match(r"<([^\s/>]+)", head)
    return match.group(1) if match else fallback


def _digest(*values: object) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _definition_id(type_key: str, compile_input: DefinitionCompileInput) -> str:
    """Name a definition by a hash of its class and everything the native compiler reads."""
    structural = json.dumps(
        {
            "template": compile_input.template,
            "localCalls": compile_input.local_calls,
            "elementBindings": compile_input.element_bindings,
            "localCallRuns": compile_input.local_call_runs,
            "dynamicElements": compile_input.dynamic_elements,
            "opaqueHtmlSites": compile_input.opaque_html_sites,
            "runtimeEventSites": compile_input.runtime_event_sites,
            "templateContextNames": compile_input.template_context_names,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256((type_key + "\0" + structural).encode()).hexdigest()


def _leaf_template_segments(fragment: LeafProgramFragment) -> list[_DefinitionFragment]:
    """
    Cut a simple='vue' template at its call positions, keeping each binding with its piece.

    The template holds no element for its calls, so the pieces are the text
    between calls (one more piece than calls). Each element binding and
    runtime event site lies inside one piece, because a call never falls
    inside an element's opening tag; its byte offsets are moved to count
    from the start of that piece.
    """
    encoded = fragment.template.encode("utf-8")
    cuts = [0, *(call.offset for call in fragment.calls), len(encoded)]
    segments: list[_DefinitionFragment] = []
    for start, end in pairwise(cuts):
        segment = _DefinitionFragment.empty()
        segment.append(encoded[start:end].decode("utf-8"))
        segment.element_bindings.extend(
            _rebase_metadata(
                [
                    cast("_ElementBindingDeclaration", dict(value))
                    for value in fragment.element_bindings
                    if start <= cast("int", value["sourceStart"]) and cast("int", value["sourceEnd"]) <= end
                ],
                -start,
            )
        )
        segment.runtime_event_sites.extend(
            _rebase_metadata(
                [
                    cast("_RuntimeEventDeclaration", dict(value))
                    for value in fragment.runtime_event_sites
                    if start <= cast("int", value["sourceStart"]) and cast("int", value["sourceEnd"]) <= end
                ],
                -start,
            )
        )
        segments.append(segment)
    placed = sum(len(item.element_bindings) + len(item.runtime_event_sites) for item in segments)
    if placed != len(fragment.element_bindings) + len(fragment.runtime_event_sites):
        raise UnsupportedPreparedView("a simple='vue' call split an element binding")
    return segments


def _checked_component_tag(type_key: str, tag_for_type: TagForType) -> str:
    tag = tag_for_type(type_key)
    if type(tag) is not str:
        raise UnsupportedPreparedView("component tag mapping must return an exact string")
    if re.fullmatch(r"[a-z][a-z0-9.-]*-[a-z0-9.-]+", tag) is None:
        raise UnsupportedPreparedView("component tag mapping must return a safe custom-element name")
    return tag


def _source_attribute_target(name: str) -> str | None:
    # `.name` and `^name` are Vue's short forms of `:name.prop` and `:name.attr`.
    if name.startswith((":", ".", "^")):
        return name[1:].split(".", 1)[0]
    match = re.fullmatch(r"v-bind:([^\.]+)(?:\..*)?", name)
    if match is not None:
        return match.group(1)
    if not name.startswith(("v-", "@", "#")):
        return name
    return None


# Names a Vue template expression may read without a component instance.
# This is Vue's own list of template globals (runtime-core
# `isGloballyAllowed`, 3.5.42); any other free name reads the instance.
_VUE_TEMPLATE_GLOBALS = frozenset(
    {
        "Array",
        "BigInt",
        "Boolean",
        "Date",
        "Error",
        "Infinity",
        "Intl",
        "JSON",
        "Map",
        "Math",
        "NaN",
        "Number",
        "Object",
        "RegExp",
        "Set",
        "String",
        "Symbol",
        "console",
        "decodeURI",
        "decodeURIComponent",
        "encodeURI",
        "encodeURIComponent",
        "isFinite",
        "isNaN",
        "parseFloat",
        "parseInt",
        "undefined",
    }
)
_THIS_KEYWORD = re.compile(r"(?<![\w$.])this(?![\w$])")
# Directives that take no expression and so read nothing.
_VALUELESS_VUE_DIRECTIVES = frozenset({"v-else", "v-cloak", "v-pre", "v-once"})


def _vue_expression_reads_instance(value: str, *, handler: bool, allowed_names: Sequence[str]) -> bool:
    """Return whether one Vue expression reads data from the component instance that compiles it."""
    # `this` is the instance itself, and the analyzer does not report it
    # as a free name.
    if _THIS_KEYWORD.search(value):
        return True
    valid, references = analyze_browser_source(value, "statement" if handler else "expression")
    # An expression the analyzer cannot parse cannot be shown to be safe.
    if not valid:
        return True
    for name, _start, _end in references:
        if name in _VUE_TEMPLATE_GLOBALS or name in allowed_names:
            continue
        # Vue gives an inline handler its event as `$event`, not from the instance.
        if handler and name == "$event":
            continue
        return True
    return False


def _vue_binding_reads_instance(name: str, value: str | None, allowed_names: Sequence[str]) -> bool:
    """
    Return whether one authored Vue binding reads its component instance.

    ``value`` is None for a binding written without a value. The answer is
    used to reject a fill that Vue would compile in the wrong component, so
    every form this function cannot prove harmless counts as a read.
    """
    folded = name.casefold()
    # A template ref registers on the instance that compiles it.
    if folded == "ref" or _source_attribute_target(name) == "ref":
        return True
    if not is_vue_directive_name(name):
        return False
    if folded in _VALUELESS_VUE_DIRECTIVES:
        return False
    # These always read or write instance state (v-model assigns to it,
    # v-for and v-slot bind names used below them), and a dynamic argument
    # is itself an expression read from the instance.
    if folded.startswith(("v-model", "v-for", "v-slot", "#", ":[", ".[", "^[", "@[", "v-bind:[", "v-on:[")):
        return True
    handler = folded.startswith(("@", "v-on"))
    expression = folded.startswith((":", ".", "^", "v-bind", "v-if", "v-else-if", "v-show", "v-text", "v-html"))
    if not handler and not expression:
        # A custom directive resolves against the instance's registered
        # directives, so it cannot move to another component.
        return True
    if value is None:
        # `@click` alone does nothing; `:id` alone is Vue's shorthand for `:id="id"`.
        return not handler
    return _vue_expression_reads_instance(value, handler=handler, allowed_names=allowed_names)


def _source_attribute_reads_instance(name: str, text: str, allowed_names: Sequence[str]) -> bool:
    """Return whether one authored attribute, given as its source text, reads its component instance."""
    if not (name.casefold() == "ref" or is_vue_directive_name(name)):
        return False
    if not text.startswith(name):
        return True
    rest = text[len(name) :].lstrip()
    if not rest:
        return _vue_binding_reads_instance(name, None, allowed_names)
    if not rest.startswith("="):
        return True
    raw = rest[1:].strip()
    # The parser keeps the attribute exactly as written, quoted or not.
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
        raw = raw[1:-1]
    return _vue_binding_reads_instance(name, unescape(raw), allowed_names)


def _unsafe_dynamic_dom_property(name: str) -> bool:
    # A `.` or `^` prefix only selects how Vue writes the name, so check the
    # name it writes: `^onclick` would still install an inline handler.
    normalized = name.casefold().lstrip(".^")
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
    replacement = f'v-bind="$citryPrepared.{attrs_key}"'
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


def _append_slot_outlet(
    output: _DefinitionFragment,
    site_id: str,
    fallback: _DefinitionFragment,
    context_binding_attrs: str = "",
    *,
    keyed: bool = False,
) -> None:
    # Vue keys each v-if branch by its position in the template. Inside a
    # keyed row that position moves with the data, so the branch then takes
    # its key from `slotKeys`, which follows the row key.
    key = f' :key="$citryPrepared.slotKeys[{site_id!r}]"' if keyed else ""
    fallback_key = f" :key=\"$citryPrepared.slotKeys[{site_id!r}] + ':fallback'\"" if keyed else ""
    output.append(
        f"<slot v-if=\"$citryPrepared.selectedSlots[{site_id!r}] === 'supplied'\"{key} "
        f'name="{site_id}"{context_binding_attrs}></slot>'
    )
    if fallback.chunks:
        output.append(
            f"<template v-else-if=\"$citryPrepared.selectedSlots[{site_id!r}] === 'fallback'\"{fallback_key}>"
        )
        output.extend(fallback)
        output.append("</template>")


_IGNORED_CONTENTS_ALLOWED = (
    "Inside a '#c-ignore' element, write plain HTML, '{{ }}' expressions, '<c-if>', '<c-for>', and '<c-raw>'."
)


def _ignored_element_label(part: PreparedElementOpen) -> str:
    """Name a `#c-ignore` element and where the template writes it."""
    from citry.ext.events.bindings import _line_column  # noqa: PLC0415

    line, column = _line_column(part.source, part.span[0])
    return f"'#c-ignore' on the <{part.tag}> element that starts at line {line}, column {column},"


def _ignored_element_close_index(parts: Sequence[RenderPart], open_index: int) -> int:
    """Return the index of the close that ends the `#c-ignore` element opened at ``open_index``."""
    opening = cast("PreparedElementOpen", parts[open_index])
    depth = 0
    for index in range(open_index + 1, len(parts)):
        part = parts[index]
        if isinstance(part, (PreparedElementOpen, PreparedDynamicElementOpen)):
            depth += 0 if part.is_void else 1
        elif isinstance(part, PreparedStaticRun):
            # A static run can open an element here and close it later, as in
            # `<ul>` ... `</ul>` around a loop, so follow its depth change.
            if part.root_structure is None:
                if "<" in part.html:
                    raise UnsupportedPreparedView(
                        f"{_ignored_element_label(opening)} holds markup whose structure is unknown"
                    )
            else:
                depth += part.root_structure.final_depth_delta
        elif isinstance(part, (PreparedElementClose, PreparedDynamicElementClose)):
            if depth == 0:
                if not isinstance(part, PreparedElementClose) or part.tag != opening.tag:
                    break
                return index
            depth -= 1
    raise UnsupportedPreparedView(f"{_ignored_element_label(opening)} has no matching close tag in the same template")


def _ignored_contents_html(
    opening: PreparedElementOpen,
    parts: Sequence[RenderPart],
    component_name: Callable[[str], str],
) -> str:
    """
    Write a `#c-ignore` element's contents as HTML the browser keeps.

    The contents are rendered once, like the static serializer writes them.
    Anything that needs Vue to render or run is rejected, because the browser
    never builds Vue nodes for these contents. The template parser already
    rejects what the template spells directly; this check catches what a
    Python value or a `c-bind` spread brings in at render time.
    """
    label = _ignored_element_label(opening)
    out: list[str] = []

    def reject(what: str) -> UnsupportedPreparedView:
        return UnsupportedPreparedView(
            f"{label} keeps the element's contents exactly as the server first rendered them, so they cannot"
            f" hold {what}. {_IGNORED_CONTENTS_ALLOWED} Move it outside the <{opening.tag}> element."
        )

    def visit(items: Sequence[RenderPart]) -> None:
        for part in items:
            if type(part) is str and part == "":
                continue
            if isinstance(part, PreparedSourceText):
                out.append(part.text)
            elif isinstance(part, PreparedStaticRun):
                out.append(part.html)
            elif isinstance(part, PreparedTextValue):
                if part.browser_binding is not None:
                    raise reject(f"the browser value {part.browser_binding.helper}()")
                out.append(escape_to_str(part.value))
            elif isinstance(part, PreparedTrustedHtmlValue):
                out.append(part.html)
            elif isinstance(part, Markup):
                out.append(str(part))
            elif isinstance(part, PreparedVerbatimHtml):
                out.append(part.html)
            elif isinstance(part, PreparedElementOpen):
                if (
                    any(attr.origin == "source" and is_vue_directive_name(attr.name) for attr in part.attrs)
                    or part.event_bindings
                    or part.poll_bindings
                    or part.control_bindings
                    or part.browser_bindings
                    or part.runtime_event_bindings
                    or part.runtime_poll_bindings
                ):
                    # A `c-bind` spread in an Events component only may add a
                    # server event; the resolved bindings above say whether it did.
                    raise reject(f"a Vue or Events binding on <{part.tag}>")
                rendered = format_prepared_element_attrs(part)
                suffix = "" if not rendered else " " + " ".join(rendered)
                ending = "/>" if part.is_void and part.is_self_closing else ">"
                out.append(f"<{part.tag}{suffix}{ending}")
            elif isinstance(part, (PreparedElementClose, PreparedDynamicElementClose)):
                out.append(f"</{part.tag}>")
            elif isinstance(part, PreparedDynamicElementOpen):
                formatted = str(format_attrs(part.attrs))
                # Match the page serializer: a selected void tag stays compact.
                ending = "/>" if part.is_void else ">"
                out.append(f"<{part.tag}{' ' + formatted if formatted else ''}{ending}")
            elif type(part) is CitryRender and not part.frame.is_component_root and not part.frame.is_transparent_root:
                # A `<c-if>` or `<c-for>` body renders as a nested part of the
                # same component, so its markup belongs to these contents.
                visit(part.parts)
            elif isinstance(part, CitryRender) and part.frame.class_id:
                raise reject(f"the component {component_name(part.frame.class_id)}")
            else:
                raise reject(f"content that needs Vue to render it ({type(part).__name__})")

    visit(parts)
    return "".join(out)


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
    # Same property-ownership marker as a dynamic element; see there.
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
        spread = f'v-bind="$citryPrepared.{attrs_binding_key}"'
        index = prepared_spread_index(part.authored_attrs)
        if index is None:
            attrs.append(spread)
        else:
            attrs.insert(index, spread)
    if key_binding_key is not None:
        attrs.append(f':key="$citryPrepared.{key_binding_key}"')
    # Reactive projections own their checked destinations after the static
    # prepared fallback spread has supplied the initial server value.
    attrs.extend(browser_attrs or ())
    if runtime_events_key is not None:
        attrs.append(f'v-citry-runtime-events="$citryEvents.runtimeEvents($citryPrepared.{runtime_events_key})"')
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
