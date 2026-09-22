"""
Typed render-cache export and replay primitives.

The boundary orchestration validates a complete artifact before calling these
helpers. They deliberately accept only the typed render forms whose detached
shape is exact; a leaf program is rejected until its operation stream has a
behavior-preserving codec.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from types import MappingProxyType
from typing import TYPE_CHECKING

from citry._vue.capture import (
    PreparedAttribute,
    PreparedBrowserBinding,
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
    StaticRunStructure,
    is_authenticated_browser_binding,
    is_authenticated_dynamic_element_open,
    prepared_browser_binding,
    prepared_dynamic_element_open,
)
from citry._vue.direct import (
    DirectCallRunRender,
    DirectExecutionFrame,
    DirectFillSource,
    DirectNestedTemplateRender,
    DirectProjectionRender,
    DirectPythonComponentRender,
    DirectRenderSession,
    DirectSlotRender,
    active_execution,
    direct_session,
)
from citry._vue.leaf_program import (
    LeafProgramFragment,
    PreparedLeafProgram,
    static_leaf_parts,
    typed_leaf_parts,
)
from citry.assets import load_template
from citry.citry_context import CitryContext
from citry.citry_element import _PreparedCallMetadata
from citry.citry_render import (
    CitryRender,
    Placeholder,
    PreparedComponentBinding,
    PreparedOccurrenceMetadata,
    RenderFrame,
    RenderPart,
)
from citry.client_directives import ComponentTagClientBindingKind
from citry.extension import OnRenderCacheExportContext, RenderCacheInstance
from citry.util.id import gen_render_id, validate_render_id

from .artifact import (
    ArtifactAttribute,
    ArtifactBrowserBinding,
    ArtifactDirectCallRunPart,
    ArtifactDirectPythonComponentPart,
    ArtifactDirectSlotPart,
    ArtifactDynamicElementClosePart,
    ArtifactDynamicElementOpenPart,
    ArtifactElementClosePart,
    ArtifactElementOpenPart,
    ArtifactExtension,
    ArtifactFrame,
    ArtifactFramePart,
    ArtifactLeafProgramPart,
    ArtifactPart,
    ArtifactPlaceholderPart,
    ArtifactPreparedBinding,
    ArtifactPreparedCall,
    ArtifactSourceTextPart,
    ArtifactStaticRunOpening,
    ArtifactStaticRunPart,
    ArtifactStaticRunStructure,
    ArtifactTextValuePart,
    ArtifactTrustedHtmlPart,
    ArtifactVerbatimHtmlPart,
    CachedRenderArtifact,
    FrozenJsonObject,
    FrozenJsonValue,
    _freeze_json_value,
    _freeze_object,
    _require_attribute_origin,
    _thaw_json,
)
from .errors import CacheArtifactError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.component import Component


class _UnsupportedTypedCachePart(CacheArtifactError):
    """A successful render part whose exact cache codec is not available."""


@dataclass(frozen=True, slots=True)
class _CachedCallNode:
    source: str
    position: tuple[int, int]


def _export_component_artifact(render: CitryRender) -> CachedRenderArtifact:
    """Detach a fully settled prepared component tree."""
    if not render.frame.is_component_root or render.frame.is_transparent_root:
        raise CacheArtifactError("component cache boundary is not a component-root prepared frame")
    return _export_boundary_artifact(render)


def _export_fragment_artifact(render: CitryRender) -> CachedRenderArtifact:
    """Detach a fully settled prepared transparent fragment tree."""
    if not render.frame.is_transparent_root:
        raise CacheArtifactError("fragment cache boundary is not a transparent-root prepared frame")
    return _export_boundary_artifact(render)


def _export_boundary_artifact(render: CitryRender) -> CachedRenderArtifact:
    if render.render_target != "prepared":
        raise _UnsupportedTypedCachePart("only settled prepared renders can be stored")
    component = render.context.component
    if component is None:
        raise CacheArtifactError("cache boundary has no live component")
    frames: list[ArtifactFrame | None] = []
    instances: list[RenderCacheInstance] = []
    instance_by_id: dict[str, int] = {}
    selected_ids: set[str] = set()
    active: set[int] = set()
    local_execution_by_live: dict[int, int] = {}
    mark_class = component.citry.get("mark")
    if not component.citry._is_builtin_component(mark_class) or mark_class.name != "mark":
        raise CacheArtifactError("cache marker built-in identity is invalid")

    def collect_instances(current: CitryRender, seen: set[int]) -> None:
        if id(current) in seen:
            return
        seen.add(id(current))
        live = current.frame
        live_component = current.context.component
        if live_component is not None and type(live_component) is mark_class:
            raise _UnsupportedTypedCachePart("marker aliases are not stored by cache artifact version 1")
        if (
            live.render_id is not None
            and live.render_id not in instance_by_id
            and (live.is_component_root or live.is_transparent_root)
        ):
            if live.class_id is None:
                raise CacheArtifactError("render occurrence has no stable class id")
            index = len(instances)
            instance_by_id[live.render_id] = index
            instances.append(RenderCacheInstance(index, live.render_id, live.class_id))
            selected_ids.add(live.render_id)
        for value in current.parts:
            if isinstance(value, CitryRender):
                collect_instances(value, seen)

    collect_instances(render, set())

    def detach(current: CitryRender) -> int:
        from citry.citry_render import RenderDecoration  # noqa: PLC0415

        if isinstance(current, RenderDecoration):
            raise _UnsupportedTypedCachePart("render decorations are not stored by cache artifact version 1")
        identity = id(current)
        if identity in active:
            raise CacheArtifactError("typed render frame graph contains a cycle")
        active.add(identity)
        frame_index = len(frames)
        frames.append(None)
        live = current.frame
        prepared = live.prepared_occurrence
        if prepared is not None and any(
            not binding.authenticated for binding in prepared.component_tag_client_bindings
        ):
            raise _UnsupportedTypedCachePart("component call binding lost producer authentication")
        instance: int | None = None
        if live.render_id is not None:
            instance = instance_by_id.get(live.render_id)
            if instance is not None:
                selected_ids.add(live.render_id)
        parts: list[ArtifactPart] = []
        for part in current.parts:
            if isinstance(part, DirectProjectionRender):
                fill = part.fill_source
                if part.execution_index in local_execution_by_live:
                    raise _UnsupportedTypedCachePart("direct slot execution identity is duplicated")
                local_execution = len(local_execution_by_live) + 1
                local_execution_by_live[part.execution_index] = local_execution
                parent_execution = None
                external_parent_execution = False
                if part.parent_execution is not None:
                    parent_execution = local_execution_by_live.get(part.parent_execution.index)
                    if parent_execution is None:
                        external_parent_execution = True
                lexical = instance_by_id.get(fill.lexical_render_id)
                receiver = instance_by_id.get(part.receiver_render_id)
                lexical_parent_depth = None
                if lexical is None:
                    ancestor = component.parent
                    depth = 1
                    while ancestor is not None and ancestor.id != fill.lexical_render_id:
                        ancestor = ancestor.parent
                        depth += 1
                    if ancestor is None:
                        raise _UnsupportedTypedCachePart("direct slot has an unknown external writer anchor")
                    lexical_parent_depth = depth
                receiver_parent_depth = None
                if receiver is None:
                    ancestor = component.parent
                    depth = 1
                    while ancestor is not None and ancestor.id != part.receiver_render_id:
                        ancestor = ancestor.parent
                        depth += 1
                    if ancestor is None:
                        raise _UnsupportedTypedCachePart("direct slot has an unknown external receiver anchor")
                    receiver_parent_depth = depth
                if type(fill.source) is not str or type(part.source) is not str:
                    raise _UnsupportedTypedCachePart("direct slot has a non-text writer anchor")
                parts.append(
                    ArtifactDirectSlotPart(
                        frame=detach(
                            CitryRender(
                                parts=list(part.parts),
                                context=part.selected.context,
                                frame=part.selected.frame,
                                render_target="prepared",
                            )
                        ),
                        execution=local_execution,
                        parent_execution=parent_execution,
                        external_parent_execution=external_parent_execution,
                        lexical_instance=lexical,
                        lexical_parent_depth=lexical_parent_depth,
                        receiver_instance=receiver,
                        receiver_parent_depth=receiver_parent_depth,
                        kind=fill.kind,
                        public_name=part.public_name,
                        fill_source=fill.source,
                        source=part.source,
                        span=part.span,
                        origin=fill.origin,
                    )
                )
            elif isinstance(part, DirectCallRunRender):
                call_node = part.call_node
                # The anchor is only declared, not guaranteed: a live call node is
                # built by the parser, so an incomplete one means the export is not
                # replayable and must be refused rather than written half-anchored.
                call_source = call_node.source
                call_position = call_node.position
                if type(call_source) is not str or type(call_position) is not tuple:
                    raise _UnsupportedTypedCachePart("direct call run has no authored source anchor")
                selected = CitryRender(
                    parts=list(part.parts), context=part.context, frame=part.frame, render_target="prepared"
                )
                parts.append(
                    ArtifactDirectCallRunPart(detach(selected), part.child_type_key, call_source, call_position)
                )
            elif isinstance(part, DirectPythonComponentRender):
                selected = CitryRender(
                    parts=list(part.parts), context=part.context, frame=part.frame, render_target="prepared"
                )
                parts.append(ArtifactDirectPythonComponentPart(detach(selected), part.local_ordinal))
            elif type(part) is CitryRender:
                parts.append(ArtifactFramePart(detach(part)))
            elif isinstance(part, CitryRender):
                raise _UnsupportedTypedCachePart(
                    f"typed wrapper {type(part).__name__} requires its relationship codec"
                )
            elif isinstance(part, Placeholder):
                from .artifact import ArtifactPlaceholderPart  # noqa: PLC0415

                parts.append(ArtifactPlaceholderPart(part.key))
            else:
                parts.append(_export_typed_leaf(part))
        try:
            data = _freeze_object(dict(current.context.js_data), f"frame {frame_index} prepared data")
        except CacheArtifactError as error:
            raise _UnsupportedTypedCachePart(str(error)) from error
        frames[frame_index] = ArtifactFrame(
            instance=instance,
            class_id=live.class_id if instance is not None else None,
            class_name=live.class_name if instance is not None else None,
            is_component_root=live.is_component_root,
            root_markers=live.root_markers,
            parts=tuple(parts),
            is_transparent_root=live.is_transparent_root,
            data=data,
            prepared_call=(
                None
                if prepared is None or prepared.call is None
                else ArtifactPreparedCall(
                    source=prepared.call.source,
                    span=prepared.call.source_span,
                    explicit_key=prepared.call.explicit_key,
                    origin=prepared.call.origin,
                    slot_free_body=prepared.call.slot_free_body,
                    raw_slots_present=prepared.raw_slots_present,
                    bindings=tuple(
                        ArtifactPreparedBinding(
                            kind=binding.kind.value,
                            key=binding.key,
                            value=binding.value,
                            source=binding.source,
                            span=binding.span,
                            provenance=binding.provenance,
                        )
                        for binding in prepared.component_tag_client_bindings
                    ),
                )
            ),
            source_fingerprint=(
                _source_fingerprint(
                    type(current.context.component)
                    if current.context.component is not None
                    else component.citry.get_component_by_class_id(live.class_id)
                )
                if instance is not None and live.class_id is not None
                else None
            ),
        )
        active.remove(identity)
        return frame_index

    root_frame = detach(render)
    extensions = component.citry.extensions._export_render_cache(
        OnRenderCacheExportContext(
            citry=component.citry,
            root_context=render.context,
            instances=tuple(instances),
            selected_render_ids=frozenset(selected_ids),
        )
    )
    if any(type(item) is not ArtifactExtension for item in extensions):
        raise CacheArtifactError("render-cache extension exporter returned an invalid payload")
    if any(item is None for item in frames):
        raise AssertionError("typed artifact frame export was incomplete")
    return CachedRenderArtifact(root_frame, tuple(frames), extensions)  # type: ignore[arg-type]


def _replay_component_artifact(
    artifact: CachedRenderArtifact,
    *,
    boundary: object,
    context: CitryContext,
    revision: int | None = None,
) -> CitryRender:
    return _replay_boundary_artifact(
        artifact, boundary=boundary, context=context, revision=revision, component_root=True
    )


def _replay_fragment_artifact(
    artifact: CachedRenderArtifact,
    *,
    boundary: object,
    context: CitryContext,
    revision: int | None = None,
) -> CitryRender:
    return _replay_boundary_artifact(
        artifact, boundary=boundary, context=context, revision=revision, component_root=False
    )


def _replay_boundary_artifact(
    artifact: CachedRenderArtifact,
    *,
    boundary: object,
    context: CitryContext,
    revision: int | None,
    component_root: bool,
) -> CitryRender:
    from citry.component import Component  # noqa: PLC0415

    if not isinstance(boundary, Component) or context.component is not boundary:
        raise CacheArtifactError("replay context does not belong to its live cache boundary")
    root = artifact.frames[artifact.root_frame]
    boundary_class = type(boundary)
    mark_class = boundary.citry.get("mark")
    if root.class_id != boundary_class.class_id or root.is_component_root is not component_root:
        raise CacheArtifactError("cached boundary does not match the current component class and kind")
    instances: dict[int, tuple[str, str]] = {}
    for frame in artifact.frames:
        if frame.instance is None:
            continue
        if frame.class_id is None or frame.class_name is None:
            raise CacheArtifactError("cached occurrence has incomplete class identity")
        previous = instances.setdefault(frame.instance, (frame.class_id, frame.class_name))
        if previous != (frame.class_id, frame.class_name):
            raise CacheArtifactError("cached occurrence index has conflicting class identity")
    if set(instances) != set(range(len(instances))) or not instances or instances[0][0] != boundary_class.class_id:
        raise CacheArtifactError("cached occurrence identities are not dense from the boundary")
    # Every entry comes from the registry lookup below, so replay works with the
    # live component classes rather than reconstructing them from the artifact.
    validated_classes: dict[int, type[Component]] = {}
    for index, (class_id, class_name) in instances.items():
        try:
            current_class = boundary.citry.get_component_by_class_id(class_id)
        except KeyError as error:
            raise CacheArtifactError(f"cached occurrence {index} has no current registered class") from error
        if current_class.__name__ != class_name:
            raise CacheArtifactError(f"cached occurrence {index} class contract changed")
        fingerprints = {frame.source_fingerprint for frame in artifact.frames if frame.instance == index}
        if len(fingerprints) != 1 or None in fingerprints:
            raise CacheArtifactError(f"cached occurrence {index} has inconsistent source fingerprints")
        if not (not component_root and index == 0) and _source_fingerprint(current_class) not in fingerprints:
            raise CacheArtifactError(f"cached occurrence {index} source contract changed")
        validated_classes[index] = current_class
    instance_ids = [boundary.id]
    occupied = {boundary.id}
    for _ in range(1, len(instances)):
        generated = boundary.citry.id_generator() if boundary.citry.id_generator is not None else gen_render_id()
        render_id = validate_render_id(generated)
        if render_id in occupied:
            raise CacheArtifactError("id generator produced a duplicate cached occurrence identity")
        occupied.add(render_id)
        instance_ids.append(render_id)
    parent_ids: list[str] = []
    ancestor = boundary.parent
    while ancestor is not None:
        parent_ids.append(ancestor.id)
        ancestor = ancestor.parent
    provided_render_ids: dict[str, str] = {}
    for name, value in context.provides.items():
        if type(name) is not str or type(value) is not str:
            continue
        try:
            provided_render_ids[name] = validate_render_id(value)
        except (TypeError, ValueError):
            continue
    staged = boundary.citry.extensions._stage_render_cache(
        artifact.extensions,
        instance_ids=tuple(instance_ids),
        instance_class_ids=tuple(instances[index][0] for index in range(len(instances))),
        parent_ids=tuple(parent_ids),
        provided_render_ids=MappingProxyType(provided_render_ids),
    )
    typed_replacements: dict[str, str] = {}
    marker_prefix = 'data-citry-i18n-binding="'
    for contribution in staged:
        for old, new in contribution.text_replacements:
            if (
                not old.startswith(marker_prefix)
                or not old.endswith('"')
                or not new.startswith(marker_prefix)
                or not new.endswith('"')
            ):
                raise CacheArtifactError("extension staged a replacement outside typed i18n binding data")
            old_value = old[len(marker_prefix) : -1]
            new_value = new[len(marker_prefix) : -1]
            previous_value = typed_replacements.setdefault(old_value, new_value)
            if previous_value != new_value:
                raise CacheArtifactError("extension staged conflicting typed binding replacements")
            old_ids = old_value.split()
            new_ids = new_value.split()
            if len(old_ids) != len(new_ids):
                raise CacheArtifactError("extension changed the number of typed binding identities")
            for old_id, new_id in zip(old_ids, new_ids, strict=True):
                previous_id = typed_replacements.setdefault(old_id, new_id)
                if previous_id != new_id:
                    raise CacheArtifactError("extension staged conflicting typed binding identity replacements")
    from .extension import CacheExtension  # noqa: PLC0415 - extension imports replay back

    # The registry hands back the base Extension, but the revision guards below are
    # this extension's own. Narrow once so a foreign extension registered under
    # "cache" is caught here rather than midway through writing replayed state.
    cache_extension = boundary.citry.extensions.get_extension("cache")
    if not isinstance(cache_extension, CacheExtension):
        raise CacheArtifactError("the 'cache' extension slot must hold a CacheExtension")
    if revision is not None and cache_extension._revision_snapshot() != revision:
        raise CacheArtifactError("render-cache revision changed while replay was staged")
    marker_by_instance: dict[int, list[str]] = {}
    replay_session = direct_session() or DirectRenderSession()
    executions: dict[int, DirectExecutionFrame] = {}
    merged_extra = dict(context.extra)
    for contribution in staged:
        for key, value in contribution.extra_items:
            if key in merged_extra:
                raise CacheArtifactError(f"staged extension context key {key!r} conflicts with current context")
            merged_extra[key] = value
        for instance, markers in contribution.frame_markers:
            if not 0 <= instance < len(instances):
                raise CacheArtifactError("staged frame marker refers to a missing occurrence")
            marker_by_instance.setdefault(instance, []).extend(markers)

    def build(frame_index: int) -> CitryRender:
        saved = artifact.frames[frame_index]
        if saved.instance is None:
            render_id = None
        else:
            render_id = instance_ids[saved.instance]
        if frame_index == artifact.root_frame:
            frame_context = context
            prepared_occurrence = RenderFrame.from_context(
                context,
                is_component_root=component_root,
                is_transparent_root=not component_root,
            ).prepared_occurrence
        else:
            frame_context = CitryContext(component=None, sandboxed=context.sandboxed)
            if saved.instance is not None and validated_classes[saved.instance] is not mark_class:
                from citry._vue.direct_capture import _issue_cache_replay_identity  # noqa: PLC0415

                _issue_cache_replay_identity(
                    frame_context,
                    boundary.citry,
                    validated_classes[saved.instance],
                )
            prepared = saved.prepared_call
            prepared_occurrence = PreparedOccurrenceMetadata(
                call=(
                    None
                    if prepared is None
                    else _PreparedCallMetadata(
                        prepared.source,
                        prepared.span,
                        prepared.explicit_key,
                        prepared.origin,
                        prepared.slot_free_body,
                    )
                ),
                raw_slots_present=False if prepared is None else prepared.raw_slots_present,
                component_tag_client_bindings=(
                    ()
                    if prepared is None
                    else tuple(
                        PreparedComponentBinding(
                            kind=ComponentTagClientBindingKind(item.kind),
                            key=item.key,
                            value=item.value,
                            source=item.source,
                            span=item.span,
                            authenticated=True,
                            provenance=item.provenance,
                        )
                        for item in prepared.bindings
                    )
                ),
            )
        frame_context.js_data = _as_dict(saved.data, "frame prepared data")
        # Rebuilt in the render's own part vocabulary, so the frame below can be
        # constructed without re-checking each entry.
        parts: list[RenderPart] = []
        for item in saved.parts:
            if type(item) is ArtifactFramePart:
                parts.append(build(item.frame))
            elif type(item) is ArtifactPlaceholderPart:
                parts.append(Placeholder(item.key))
            elif type(item) is ArtifactDirectSlotPart:
                if (item.lexical_instance is None) == (item.lexical_parent_depth is None):
                    raise CacheArtifactError("cached direct slot must have exactly one lexical writer anchor")
                if (item.receiver_instance is None) == (item.receiver_parent_depth is None):
                    raise CacheArtifactError("cached direct slot must have exactly one receiver anchor")
                if item.lexical_instance is not None and not 0 <= item.lexical_instance < len(instances):
                    raise CacheArtifactError("cached direct slot refers to a missing lexical occurrence")
                if item.receiver_instance is not None and not 0 <= item.receiver_instance < len(instances):
                    raise CacheArtifactError("cached direct slot refers to a missing occurrence")
                if item.execution in executions:
                    raise CacheArtifactError("cached direct execution identity is duplicated")
                parent_execution = None
                if item.parent_execution is not None:
                    parent_execution = executions.get(item.parent_execution)
                    if parent_execution is None:
                        raise CacheArtifactError("cached direct execution parent is not ordered before its child")
                elif item.external_parent_execution:
                    parent_execution = active_execution()
                    if parent_execution is None:
                        raise CacheArtifactError("cached direct execution external parent is unavailable")
                if item.lexical_instance is not None:
                    lexical_render_id = instance_ids[item.lexical_instance]
                else:
                    lexical_boundary = boundary
                    for _ in range(item.lexical_parent_depth or 0):
                        if lexical_boundary.parent is None:
                            raise CacheArtifactError("cached supplied slot lexical parent path is unavailable")
                        lexical_boundary = lexical_boundary.parent
                    lexical_render_id = lexical_boundary.id
                if lexical_render_id is None:
                    raise CacheArtifactError("cached supplied slot has no current lexical parent")
                if item.receiver_instance is not None:
                    receiver_render_id = instance_ids[item.receiver_instance]
                else:
                    receiver_boundary = boundary
                    for _ in range(item.receiver_parent_depth or 0):
                        if receiver_boundary.parent is None:
                            raise CacheArtifactError("cached supplied slot receiver parent path is unavailable")
                        receiver_boundary = receiver_boundary.parent
                    receiver_render_id = receiver_boundary.id
                fill_source = DirectFillSource(
                    session=replay_session,
                    lexical_render_id=lexical_render_id,
                    kind=item.kind,
                    public_name=item.public_name,
                    source=item.fill_source,
                    span=item.span,
                    origin=item.origin,
                    strict_session=True,
                )
                live_execution = replay_session.next_execution()
                execution = DirectExecutionFrame(
                    live_execution,
                    parent_execution,
                    fill_source,
                    item.public_name,
                    receiver_render_id,
                    item.source,
                    item.span,
                    consumed=True,
                )
                executions[item.execution] = execution
                selected = build(item.frame)
                projection_type = DirectNestedTemplateRender if item.kind == "nested-template" else DirectSlotRender
                parts.append(
                    projection_type(
                        selected,
                        execution_index=live_execution,
                        fill_source=fill_source,
                        parent_execution=parent_execution,
                        public_name=item.public_name,
                        receiver_render_id=receiver_render_id,
                        source=item.source,
                        span=item.span,
                    )
                )
            elif type(item) is ArtifactDirectCallRunPart:
                selected = build(item.frame)
                call_node = _CachedCallNode(item.source, item.span)
                _rebind_call_run_sources(selected, call_node, item.child_class_id)
                parts.append(
                    DirectCallRunRender(
                        selected,
                        call_node=call_node,
                        child_type_key=item.child_class_id,
                    )
                )
            elif type(item) is ArtifactDirectPythonComponentPart:
                parts.append(DirectPythonComponentRender(build(item.frame), local_ordinal=item.local_ordinal))
            else:
                parts.append(_apply_typed_replacements(_replay_typed_leaf(item), typed_replacements))
        markers = list(saved.root_markers)
        if saved.instance is not None:
            markers.extend(marker_by_instance.get(saved.instance, ()))
        return CitryRender(
            parts=parts,
            context=frame_context,
            frame=RenderFrame(
                render_id=render_id,
                class_id=saved.class_id,
                class_name=saved.class_name,
                is_component_root=saved.is_component_root,
                root_markers=tuple(markers),
                is_transparent_root=saved.is_transparent_root,
                prepared_occurrence=prepared_occurrence,
            ),
            render_target="prepared",
        )

    replayed = build(artifact.root_frame)
    written: list[str] = []
    original_extra = context.extra
    try:
        with cache_extension._stable_revision(revision):
            for contribution in staged:
                for write in contribution.cache_writes:
                    previous_cached = boundary.citry.cache.get(write.key)
                    if previous_cached == write.value:
                        continue
                    boundary.citry.cache.set(write.key, write.value, ttl=write.ttl)
                    if write.rollback_delete and previous_cached is None:
                        written.append(write.key)
            context.extra = merged_extra
    except Exception:
        context.extra = original_extra
        for key in reversed(written):
            boundary.citry.cache.delete(key)
        raise
    return replayed


def _rebind_call_run_sources(render: CitryRender, call_node: _CachedCallNode, child_class_id: str) -> None:
    pending = [render]
    while pending:
        current = pending.pop()
        prepared = current.frame.prepared_occurrence
        call = None if prepared is None else prepared.call
        if (
            prepared is not None
            and call is not None
            and current.frame.class_id == child_class_id
            and call.source == call_node.source
            and call.source_span == call_node.position
        ):
            current.frame = replace(
                current.frame,
                prepared_occurrence=replace(prepared, call=replace(call, source=call_node.source)),
            )
        pending.extend(part for part in current.parts if isinstance(part, CitryRender))


def _apply_typed_replacements(value: RenderPart, replacements: dict[str, str]) -> RenderPart:
    if not replacements:
        return value
    if type(value) is PreparedElementOpen:
        attrs = tuple(
            replace(attr, value=replacements.get(attr.value, attr.value))
            if attr.name == "data-citry-i18n-binding" and type(attr.value) is str
            else attr
            for attr in value.attrs
        )
        browser_bindings = tuple(_replace_browser_binding(binding, replacements) for binding in value.browser_bindings)
        return replace(value, attrs=attrs, browser_bindings=browser_bindings)
    if type(value) is PreparedTextValue and value.browser_binding is not None:
        binding = _replace_browser_binding(value.browser_binding, replacements)
        return replace(value, browser_binding=binding)
    if type(value) is PreparedLeafProgram and value.cached_typed_parts is not None:
        return replace(
            value,
            cached_typed_parts=tuple(
                _apply_typed_replacements(item, replacements) for item in value.cached_typed_parts
            ),
            cached_static_parts=tuple(
                _replace_typed_marker_text(item, replacements) for item in value.cached_static_parts or ()
            ),
        )
    return value


def _replace_browser_binding(value: PreparedBrowserBinding, replacements: dict[str, str]) -> PreparedBrowserBinding:
    operand = replacements.get(value.operand, value.operand) if type(value.operand) is str else value.operand
    if operand == value.operand:
        return value
    return prepared_browser_binding(
        helper=value.helper,
        operand=operand,
        target=value.target,
        name=value.name,
        values_expression=value.values_expression,
    )


def _replace_typed_marker_text(value: str, replacements: dict[str, str]) -> str:
    for old, new in replacements.items():
        value = value.replace(f'data-citry-i18n-binding="{old}"', f'data-citry-i18n-binding="{new}"')
    return value


def _export_typed_leaf(part: object) -> ArtifactPart:
    if type(part) is PreparedSourceText:
        return ArtifactSourceTextPart(part.source, part.span, part.text)
    if type(part) is PreparedVerbatimHtml:
        return ArtifactVerbatimHtmlPart(part.source, part.span, part.html)
    if type(part) is PreparedTextValue:
        binding = part.browser_binding
        if binding is not None and not is_authenticated_browser_binding(binding):
            raise _UnsupportedTypedCachePart("text browser binding is not producer-authenticated")
        return ArtifactTextValuePart(
            part.source,
            part.span,
            _freeze_value(part.value, "text value"),
            None
            if binding is None
            else ArtifactBrowserBinding(
                binding.helper,
                _freeze_value(binding.operand, "browser binding operand"),
                binding.target,
                binding.name,
                binding.values_expression,
            ),
        )
    if type(part) is PreparedTrustedHtmlValue:
        return ArtifactTrustedHtmlPart(part.html)
    if type(part) is PreparedElementOpen:
        if any(not is_authenticated_browser_binding(value) for value in part.browser_bindings):
            raise _UnsupportedTypedCachePart("attribute browser binding is not producer-authenticated")
        if part.poll_bindings:
            raise _UnsupportedTypedCachePart("prepared polling bindings are not stored by cache artifact version 1")
        if part.runtime_events_candidate:
            raise _UnsupportedTypedCachePart("runtime-resolved event sites are not stored by cache artifact version 1")
        return ArtifactElementOpenPart(
            part.source,
            part.span,
            part.tag,
            tuple(
                ArtifactAttribute(attr.name, attr.origin, attr.span, _freeze_value(attr.value, "attribute value"))
                for attr in part.attrs
            ),
            part.is_void,
            part.is_self_closing,
            _freeze_value(_plain_metadata(part.element_metadata), "element metadata"),
            tuple(_freeze_mapping(value, "event binding") for value in part.event_bindings),
            tuple(_freeze_mapping(value, "control binding") for value in part.control_bindings),
            tuple(
                ArtifactBrowserBinding(
                    value.helper,
                    _freeze_value(value.operand, "browser binding operand"),
                    value.target,
                    value.name,
                    value.values_expression,
                )
                for value in part.browser_bindings
            ),
        )
    if type(part) is PreparedElementClose:
        return ArtifactElementClosePart(part.source, part.span, part.tag)
    if type(part) is PreparedDynamicElementOpen:
        if not is_authenticated_dynamic_element_open(part):
            raise _UnsupportedTypedCachePart("dynamic element opening is not producer-authenticated")
        if part.poll_bindings:
            raise _UnsupportedTypedCachePart("prepared polling bindings are not stored by cache artifact version 1")
        if part.runtime_events_candidate:
            raise _UnsupportedTypedCachePart("runtime-resolved event sites are not stored by cache artifact version 1")
        return ArtifactDynamicElementOpenPart(
            part.tag,
            _freeze_mapping(part.attrs, "dynamic attributes"),
            part.is_void,
            tuple(
                ArtifactAttribute(attr.name, attr.origin, attr.span, _freeze_value(attr.value, "dynamic source attr"))
                for attr in part.authored_attrs
            ),
            part.key,
            part.authored_source,
            tuple(_freeze_mapping(value, "event binding") for value in part.event_bindings),
            tuple(_freeze_mapping(value, "control binding") for value in part.control_bindings),
        )
    if type(part) is PreparedDynamicElementClose:
        return ArtifactDynamicElementClosePart(part.tag)
    if type(part) is PreparedStaticRun:
        structure = part.root_structure
        return ArtifactStaticRunPart(
            part.html,
            None
            if structure is None
            else ArtifactStaticRunStructure(
                tuple(
                    ArtifactStaticRunOpening(
                        item.start_at,
                        item.insert_at,
                        item.end_at,
                        item.relative_depth,
                        tuple(sorted(item.attr_identities)),
                    )
                    for item in structure.openings
                ),
                structure.final_depth_delta,
                structure.tag_transitions,
            ),
        )
    if isinstance(part, PreparedLeafProgram):
        typed: list[ArtifactPart] = []
        for item in typed_leaf_parts(part):
            typed.append(_export_typed_leaf(item))
        return ArtifactLeafProgramPart(
            template=part.fragment.template,
            element_bindings=tuple(
                _freeze_mapping(value, "leaf element binding") for value in part.fragment.element_bindings
            ),
            browser_requirements=tuple(sorted(part.fragment.browser_requirements)),
            safe_body=part.fragment.safe_body,
            prepared_data=_freeze_mapping(part.prepared_data, "leaf prepared data"),
            vue_errors=part.vue_errors,
            typed_parts=tuple(typed),
            static_parts=tuple(static_leaf_parts(part)),
        )
    raise _UnsupportedTypedCachePart(f"typed render part {type(part).__name__} has no cache codec")


def _replayed_element_metadata(value: object) -> tuple[tuple[str, object], ...]:
    """Rebuild one element's metadata pairs from the artifact's JSON form."""
    # JSON has no tuples, so the export wrote each pair as a two-item list and an
    # element with no metadata as an empty list.
    if value is None:
        return ()
    if not isinstance(value, list):
        raise CacheArtifactError("replayed element metadata is not a list of pairs")
    pairs: list[tuple[str, object]] = []
    for entry in value:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2 or not isinstance(entry[0], str):
            raise CacheArtifactError("replayed element metadata entry is not a name and value pair")
        pairs.append((entry[0], entry[1]))
    return tuple(pairs)


def _replay_typed_leaf(part: ArtifactPart) -> RenderPart:
    if type(part) is ArtifactSourceTextPart:
        return PreparedSourceText(part.source, part.span, part.text)
    if type(part) is ArtifactVerbatimHtmlPart:
        return PreparedVerbatimHtml(part.source, part.span, part.html)
    if type(part) is ArtifactTextValuePart:
        binding = part.browser_binding
        return PreparedTextValue(
            part.source,
            part.span,
            _thaw_json(part.value),
            browser_binding=(
                None
                if binding is None
                else prepared_browser_binding(
                    helper=binding.helper,
                    operand=_thaw_json(binding.operand),
                    target=binding.target,  # type: ignore[arg-type]
                    name=binding.name,
                    values_expression=binding.values_expression,
                )
            ),
        )
    if type(part) is ArtifactTrustedHtmlPart:
        return PreparedTrustedHtmlValue(part.html)
    if type(part) is ArtifactElementOpenPart:
        metadata = _thaw_json(part.element_metadata)
        return PreparedElementOpen(
            part.source,
            part.span,
            part.tag,
            tuple(
                PreparedAttribute(
                    item.name,
                    _require_attribute_origin(item.origin, f"attribute {item.name}"),
                    item.span,
                    _thaw_json(item.value),
                )
                for item in part.attrs
            ),
            part.is_void,
            part.is_self_closing,
            _replayed_element_metadata(metadata),
            tuple(MappingProxyType(_as_dict(value, "event binding")) for value in part.event_bindings),
            (),
            tuple(MappingProxyType(_as_dict(value, "control binding")) for value in part.control_bindings),
            tuple(
                prepared_browser_binding(
                    helper=value.helper,
                    operand=_thaw_json(value.operand),
                    target=value.target,  # type: ignore[arg-type]
                    name=value.name,
                    values_expression=value.values_expression,
                )
                for value in part.browser_bindings
            ),
        )
    if type(part) is ArtifactElementClosePart:
        return PreparedElementClose(part.source, part.span, part.tag)
    if type(part) is ArtifactDynamicElementOpenPart:
        normalized = PreparedElementOpen(
            "",
            (0, 0),
            part.tag,
            (),
            part.is_void,
            False,  # noqa: FBT003
            (),
            tuple(_as_dict(value, "event binding") for value in part.event_bindings),
            (),
            tuple(_as_dict(value, "control binding") for value in part.control_bindings),
        )
        rebuilt = prepared_dynamic_element_open(
            part.tag, _as_dict(part.attrs, "dynamic attributes"), key=part.key, normalized=normalized
        )
        object.__setattr__(
            rebuilt,
            "authored_attrs",
            tuple(
                PreparedAttribute(
                    attr.name,
                    _require_attribute_origin(attr.origin, f"authored attribute {attr.name}"),
                    attr.span,
                    _thaw_json(attr.value),
                )
                for attr in part.authored_attrs
            ),
        )
        object.__setattr__(rebuilt, "authored_source", part.authored_source)
        if rebuilt.is_void is not part.is_void:
            raise CacheArtifactError("cached dynamic element voidness does not match the current validator")
        return rebuilt
    if type(part) is ArtifactDynamicElementClosePart:
        return PreparedDynamicElementClose(part.tag)
    if type(part) is ArtifactStaticRunPart:
        structure = part.structure
        return PreparedStaticRun(
            part.html,
            None
            if structure is None
            else StaticRunStructure(
                tuple(
                    StaticRunOpening(
                        item.start_at,
                        item.insert_at,
                        item.end_at,
                        item.relative_depth,
                        frozenset(item.attr_identities),
                    )
                    for item in structure.openings
                ),
                structure.final_depth_delta,
                tuple(structure.tag_transitions),
            ),
        )
    if type(part) is ArtifactLeafProgramPart:
        return PreparedLeafProgram(
            fragment=LeafProgramFragment(
                template=part.template,
                element_bindings=tuple(_as_dict(value, "leaf element binding") for value in part.element_bindings),
                browser_requirements=frozenset(part.browser_requirements),
                safe_body=part.safe_body,
            ),
            prepared_data=_as_dict(part.prepared_data, "leaf prepared data"),
            operations=(),
            vue_errors=part.vue_errors,
            resolved_opens={},
            cached_typed_parts=tuple(_replay_typed_leaf(item) for item in part.typed_parts),
            cached_static_parts=part.static_parts,
        )
    raise CacheArtifactError(f"artifact part {type(part).__name__} is not a typed leaf")


def _freeze_value(value: object, path: str) -> FrozenJsonValue:
    try:
        return _freeze_json_value(value, path)
    except CacheArtifactError as error:
        raise _UnsupportedTypedCachePart(str(error)) from error


def _source_fingerprint(component_class: type[Component]) -> str:
    template = load_template(component_class)
    # ``origin`` is diagnostic provenance and commonly contains an absolute
    # checkout path. The registered class id already supplies stable class
    # identity; the template contract is therefore its authored source alone.
    payload = "none" if template is None else template.source
    return sha256(payload.encode("utf-8")).hexdigest()


def _freeze_mapping(value: Mapping[str, object], path: str) -> FrozenJsonObject:
    try:
        return _freeze_object(dict(value), path)
    except (TypeError, ValueError, CacheArtifactError) as error:
        raise _UnsupportedTypedCachePart(f"{path} is not strict JSON: {error}") from error


def _plain_metadata(value: tuple[tuple[str, object], ...] | None) -> object:
    # The artifact stores metadata as JSON, which has no tuples, so each pair
    # becomes a list here and is read back as a pair on replay.
    if value is None:
        return None
    return [list(item) for item in value]


def _as_dict(value: FrozenJsonObject, path: str) -> dict[str, object]:
    thawed = _thaw_json(value)
    if type(thawed) is not dict:
        raise CacheArtifactError(f"{path} must be an object")
    return thawed


__all__ = ["_UnsupportedTypedCachePart", "_export_typed_leaf", "_replay_typed_leaf"]
