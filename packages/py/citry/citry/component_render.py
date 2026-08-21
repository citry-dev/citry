"""
Component render pipeline.

This module contains the core rendering logic. When a CitryElement is
rendered (via ``.render()``), it calls ``render_impl`` which:

1. Creates a real Component instance (via ``_create_instance``), which
   normalizes inputs and sets instance state (id, kwargs, slots, parent, root)
2. Calls ``template_data()`` and validates it against ``TemplateData``
3. Builds a ``CitryContext`` (the render-scoped state) and the template body
   (a node list), walks the body into a parts list, and returns a
   ``CitryRender`` wrapping the parts plus the context

``render_impl`` returns a ``CitryRender`` (not a string). Serialization to HTML
happens later, via ``CitryRender.serialize()`` (or ``str()``). See
docs/design/component_rendering.md for the three-phase model.

The slow step, compiling the template (parse + compile + exec) into a
body-generating function, runs once per **component class** and is cached on
the class, since it is the same for a given template. On top of that sits the
``Const`` optimization: parts of the template that depend only on inputs
marked ``Const()`` ("same value on every render") are computed once and the
result is cached per component class and per set of ``Const`` values, so
repeat renders skip that work. See docs/design/component_constness.md and
citry/constness.py.

Rendering is deferred and stack-driven (no recursion limit on nesting depth),
collects each component's JS/CSS dependencies, and drives the ``on_render``
hook; see docs/design/component_rendering_defer.md and component_on_render.md. Django's
context snapshotting is deliberately not ported: a component receives only
its own props and slots, never an inherited context.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import replace
from difflib import get_close_matches
from typing import TYPE_CHECKING, Any, NamedTuple

from citry._pure import (
    PureBodyPlan,
    PureInteriorBody,
    PureLiveBodyItem,
    pure_body_cache_scope,
    pure_body_lookup,
    store_pure_body,
)
from citry.assets import load_template
from citry.citry_context import CitryContext
from citry.citry_element import CitryElement
from citry.citry_render import (
    CitryRender,
    DeferredComponent,
    _PhysicalRegion,
    unwrap_physical_region,
)
from citry.citry_template import CitryTemplate, DeclaredSlot
from citry.client_directives import CLIENT_PROPS_ATTR, validate_client_props_target
from citry.component_like import ComponentLike, _component_like_render_scope, _resolve_component_like
from citry.constness import const_value, extract_const_vars, precompute_const_parts
from citry.ext.cache.errors import CacheArtifactError, _CacheRevisionChanged
from citry.ext.cache.extension import CacheExtension, _CacheHit, _CacheMissPlan
from citry.ext.cache.replay import _replay_component_artifact, _replay_fragment_artifact
from citry.nodes import (
    ComponentNode,
    ElementAttrsNode,
    ElementKeyNode,
    ExprHtmlAttr,
    ExprNode,
    FillDataBinding,
    FillNode,
    ForNode,
    IfNode,
    SlotNode,
    StaticHtmlAttr,
    TemplateHtmlAttr,
    TemplateNode,
)
from citry.ownership import current_ownership_graph, ownership_render_scope, resume_ownership_graph
from citry.slots import Slot
from citry.util.exception import (
    set_component_error_message,
    set_template_origin_error_message,
    set_template_position_error_message,
)
from citry.util.logger import is_tracing, trace_component_msg, trace_node_msg
from citry.util.misc import get_fields, is_generator, to_dict
from citry_core.template_parser import compile_template, parse_template

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry.citry_render import OnRenderGenerator, RenderPart, RenderReplacement
    from citry.component import Component
    from citry.nodes import BodyItem, Node
    from citry.ownership import OwnershipGraph, PhysicalRegionId
    from citry_core.template_parser import TagRules


# Per-render template globals: the variables passed to a single render through
# Component.render(template_globals=...). Held in a context variable because the
# value is the same for the whole render and must reach every nested render
# (deferred children, embedded {{ element }} values, slot content) without being
# threaded through each node and slot; a concurrent render on another thread or
# task keeps its own value. None means no per-render override was given.
_render_globals: ContextVar[dict[str, Any] | None] = ContextVar("citry_render_globals", default=None)


def render_impl(
    element: CitryElement,
    parent: Component | None = None,
    provides: dict[str, Any] | None = None,
    *,
    render_globals: dict[str, Any] | None = None,
) -> CitryRender:
    """
    Render a component and everything inside it into a finished ``CitryRender``.

    The public render entry: ``CitryElement.render`` calls it, and a composed
    element found in a ``{{ ... }}`` expression renders through it too.

    ``render_globals`` are the per-render template variables from
    ``Component.render(template_globals=...)``. They are merged into every
    component in this render, on top of the instance's ``citry.template_globals``
    and under a component's own ``template_data``. They are kept in a context
    variable for the duration of the render, so every nested render sees them
    without being passed the value. ``None`` (the default) adds no override and
    leaves any enclosing render's globals in place, so a nested ``render_impl``
    call does not disturb the render it runs inside.
    """
    owns_ownership_graph = current_ownership_graph() is None
    with (
        ownership_render_scope() as ownership,
        _component_like_render_scope(element.comp_cls.citry),
        pure_body_cache_scope(),
    ):
        try:
            if render_globals is None:
                return _render_tree(element, parent, provides)
            token = _render_globals.set(render_globals)
            try:
                return _render_tree(element, parent, provides)
            finally:
                _render_globals.reset(token)
        finally:
            if owns_ownership_graph:
                ownership.release_transient_region_results()


def _render_tree(
    element: CitryElement,
    parent: Component | None = None,
    provides: dict[str, Any] | None = None,
) -> CitryRender:
    """
    Render a component and everything inside it, returning a finished CitryRender.

    Called by ``CitryElement.render()``. It renders the top component with
    ``_render_one``, which leaves each nested ``<c-child>`` as an unrendered
    ``DeferredComponent``. This function then renders those children one at a
    time, working through a list instead of calling itself, so a deeply nested
    page never hits Python's recursion limit (see
    docs/design/component_rendering_defer.md).

    A component's after-render hooks run once everything inside that component
    has been rendered (so children run before their parents): first its own
    ``on_render`` generator is resumed with the settled result (it may replace
    the output, any number of times), then extensions' ``on_component_rendered``
    runs, and the child's collected dependencies are copied into its parent.

    When a component's render fails, the error travels up the component tree:
    each enclosing component's ``on_render`` generator, then extensions'
    ``on_component_rendered``, runs with the error and may swallow it by
    producing replacement output. An error nothing handles is raised from
    here, carrying the component path in its message
    (docs/design/component_on_render.md sections 5-6).

    Args:
        element: The component to render (its class, kwargs, slots, and cached
            template body).
        parent: The parent Component instance when rendering inside another
            component's template. Sets the parent/root links.
        provides: The provide/inject entries the rendered component inherits
            (see docs/design/component_provide.md). Empty for a plain user call; set
            when an element is rendered from inside another render (an
            embedded ``{{ element }}`` or slot content), so the subtree keeps
            the provides active at its render site.

    Returns:
        A finished ``CitryRender`` with every child rendered (no
        ``DeferredComponent`` parts left). Call ``.serialize()`` (or ``str()``)
        on it to get the HTML.

    """
    root = _render_one_traced(element, parent, provides)
    return _settle_render(
        root.render,
        root.generator,
        root_cache_plan=root.cache_plan,
        root_cache_hit=root.cache_hit,
    )


def _settle_render(
    root_render: CitryRender,
    root_generator: OnRenderGenerator | None = None,
    *,
    finalize_root: bool = True,
    root_cache_plan: _CacheMissPlan | None = None,
    root_cache_hit: _CacheHit | None = None,
) -> CitryRender:
    """
    Resolve deferred components inside an existing render tree.

    ``_render_tree`` uses the normal ``finalize_root=True`` path after
    rendering the root component once. ``Slot.__str__`` uses
    ``finalize_root=False`` for a template-defined fill body: that body is an
    interior render owned by an already-rendered component, so only deferred
    descendants need rendering and finalization. The shared stack keeps both
    paths non-recursive and preserves child hooks, error boundaries, and
    dependency merging.
    """
    # We keep a stack of two kinds of work:
    #   - _RenderTask: render one deferred child, and put its result where the
    #     DeferredComponent was.
    #   - _FinalizeTask: run that child's after-render hooks and copy its
    #     dependencies into the parent.
    # When we render a child we add its _FinalizeTask first, then its own
    # children on top. We always take from the top of the stack, so a child and
    # everything inside it finish before we run the parent's _FinalizeTask. (This
    # is the approach django-components uses, but on objects instead of HTML
    # strings.)
    stack: list[_RenderTask | _FinalizeTask | _ContextMergeTask] = []
    if finalize_root:
        stack.append(
            _FinalizeTask(
                root_render,
                None,
                root_generator,
                cache_plan=root_cache_plan,
                cache_hit=root_cache_hit,
            )
        )
    stack.extend(reversed(_scan_deferred(root_render)))

    root_result = root_render

    def commit(old: CitryRender, final: CitryRender, position: _DeferredComponentPosition | None) -> None:
        # Put a component's settled output where it belongs: at its recorded
        # position in the parent's parts (copying its collected dependencies
        # up), or as the new root result.
        nonlocal root_result
        if position is None:
            root_result = final
        else:
            _replace_in_parts(position.parts, position.idx, old, final)
            _merge_dependencies(position.parent_context, final.context)

    def requeue(
        task: _FinalizeTask,
        content: RenderReplacement,
        generator: OnRenderGenerator | None,
        *,
        hook_checkpoint: int,
        hook_through_order: int,
    ) -> None:
        # The component's on_render generator replaced its output. Render the
        # new content in its place (children deferred as usual) and finalize
        # the component again once the new content settles; the generator (if
        # still live) is then resumed with that result.
        old = task.render
        component = old.context.component
        if component is None:
            msg = "an on_render generator settled on a render that has no component."
            raise RuntimeError(msg)
        ownership = old.context.ownership
        ownership_checkpoint = ownership.checkpoint() if ownership is not None else None
        new_render = CitryRender(
            parts=_replacement_parts(content, old.context, component),
            context=old.context,
            is_component_root=old.is_component_root,
        )
        if ownership is not None:
            selected_render_ids, selected_object_ids = _render_selection(new_render)
            selected_region_ids = ownership.selected_region_ids(render_object_ids=selected_object_ids)
            ownership.retire_unselected_after(
                hook_checkpoint,
                through_order=hook_through_order,
                preserved_render_ids=selected_render_ids,
                preserved_region_ids=selected_region_ids,
            )
        if ownership is not None and ownership_checkpoint is not None and id(old) not in selected_object_ids:
            ownership.retire_component_output(
                component.id,
                through_order=ownership_checkpoint,
                descendant_render_ids=_render_ids(old, exclude_render_id=component.id),
                preserved_render_ids=selected_render_ids - {component.id},
                preserved_region_ids=selected_region_ids,
            )
        if task.position is not None:
            _replace_in_parts(task.position.parts, task.position.idx, old, new_render)
        stack.append(
            _FinalizeTask(
                new_render,
                task.position,
                generator,
                cache_plan=task.cache_plan,
                physical_parent_region_id=task.physical_parent_region_id,
            )
        )
        stack.extend(reversed(_scan_deferred(new_render)))

    def settle(task: _FinalizeTask, error: Exception | None) -> CitryRender | None:
        # Settle a component whose subtree has finished rendering (or, when
        # ``error`` is set, whose subtree failed): drive its on_render
        # generator, then run the extension hook via _finalize.
        #
        # Returns the final render to commit, or None when the generator
        # produced new content that was queued for re-processing (this task's
        # replacement finalize is then on the stack). Raises when the error,
        # incoming or raised here, was not handled, so the caller bubbles it.
        render: CitryRender | None = task.render if error is None else None
        generator = task.generator
        ownership = task.render.context.ownership
        if error is not None:
            task.render.context._error_tainted = True
        if task.cache_hit is not None:
            if error is not None:
                raise error
            component = task.render.context.component
            if component is None:
                raise RuntimeError("A component cache hit has no live boundary component.")
            if ownership is not None:
                ownership.settle_component(component.id)
            cache_extension = component.citry.extensions.get_extension("cache")
            if not isinstance(cache_extension, CacheExtension):
                raise TypeError("The built-in Cache extension has an invalid runtime type.")
            cache_extension._notify_component_hit(task.cache_hit, component)
            return task.render
        generator_checkpoint = ownership.checkpoint() if ownership is not None else None
        while generator is not None:
            try:
                yielded = generator.send((render, error))
            except StopIteration as stop:
                if stop.value is not None:
                    # `return <content>`: the final output; the generator is
                    # done, so the re-queued finalize carries no generator.
                    requeue(
                        task,
                        stop.value,
                        None,
                        hook_checkpoint=generator_checkpoint or 0,
                        hook_through_order=ownership.checkpoint() if ownership is not None else 0,
                    )
                    return None
                # Plain `return`: keep the current result (and error).
                if ownership is not None and generator_checkpoint is not None:
                    generator_through_order = ownership.checkpoint()
                    if generator_checkpoint < generator_through_order:
                        preserved_render_ids = _render_ids(render) if render is not None else set()
                        selected_objects = _render_objects(render) if render is not None else None
                        ownership.retire_unselected_after(
                            generator_checkpoint,
                            through_order=generator_through_order,
                            preserved_render_ids=preserved_render_ids,
                            preserved_region_ids=(
                                _selected_region_ids(ownership, selected_objects)
                                if selected_objects is not None
                                else set()
                            ),
                        )
                break
            except Exception as gen_error:  # noqa: BLE001
                # The generator raised: that becomes the component's error.
                # A fresh error gets this component's path; re-raising the
                # error it was sent keeps the original frames.
                if gen_error is not error:
                    set_component_error_message(gen_error, _component_path(task.render.context.component))
                if ownership is not None and generator_checkpoint is not None:
                    ownership.retire_unselected_after(
                        generator_checkpoint,
                        through_order=ownership.checkpoint(),
                        preserved_render_ids=set(),
                    )
                task.render.context._error_tainted = True
                render, error = None, gen_error
                break
            if yielded is None:
                # Bare yield after the first: answer immediately with the
                # unchanged result.
                continue
            try:
                requeue(
                    task,
                    yielded,
                    generator,
                    hook_checkpoint=generator_checkpoint or 0,
                    hook_through_order=ownership.checkpoint() if ownership is not None else 0,
                )
            except TypeError as bad_yield:
                # The yielded value was not renderable; deliver the failure
                # back to this generator, like any error in its content.
                set_component_error_message(bad_yield, _component_path(task.render.context.component))
                task.render.context._error_tainted = True
                render, error = None, bad_yield
                continue
            return None
        finalized = _finalize(task.render, error)
        if finalized.frame.is_component_root and finalized.context.component is not None:
            finalized.frame = replace(
                finalized.frame,
                root_markers=tuple(dict.fromkeys(finalized.context._get_root_markers())),
            )
        if task.cache_plan is not None:
            component = finalized.context.component
            if component is None:
                raise RuntimeError("A component cache miss has no live boundary component.")
            cache_extension = component.citry.extensions.get_extension("cache")
            if not isinstance(cache_extension, CacheExtension):
                raise TypeError("The built-in Cache extension has an invalid runtime type.")
            cache_extension._publish_component(task.cache_plan, finalized)
        return finalized

    def settle_in_invocation_region(task: _FinalizeTask, error: Exception | None) -> CitryRender | None:
        """Finalize under the physical region that contains this invocation."""
        component = task.render.context.component
        ownership = task.render.context.ownership
        invocation_id = component._ownership_invocation_id if component is not None else None
        if ownership is None:
            return settle(task, error)
        if task.physical_parent_region_id is not None:
            with ownership.active_region(task.physical_parent_region_id):
                return settle(task, error)
        with ownership.active_invocation_region(invocation_id):
            return settle(task, error)

    def bubble(error: Exception) -> None:
        # A component's render failed; give its ancestors a chance to handle
        # the error (docs/design/component_on_render.md section 5).
        #
        # The stack is pushed depth-first, so everything above an ancestor's
        # _FinalizeTask is exactly that ancestor's pending subtree work.
        # Popping to the nearest _FinalizeTask therefore discards the dead
        # output's remaining work and lands on the nearest enclosing
        # component. That component's on_render generator, then extensions,
        # may swallow the error by producing replacement output, which ends
        # the unwind. Otherwise the error continues to the next ancestor, and
        # out of render_impl at the root.
        while stack:
            task = stack.pop()
            if isinstance(task, _ContextMergeTask):
                continue
            if not isinstance(task, _FinalizeTask):
                ownership = task.deferred.element.ownership_graph or task.position.parent_context.ownership
                if ownership is not None:
                    ownership.retire_invocation(task.deferred.element.ownership_invocation_id)
                continue
            try:
                final = settle_in_invocation_region(task, error)
            except Exception as unhandled:  # noqa: BLE001
                error = unhandled
                continue
            if final is not None:
                commit(task.render, final, task.position)
            # final is None: the generator queued replacement output, which
            # also ends the unwind (the component is re-processing).
            return
        raise error

    while stack:
        task = stack.pop()
        # Case: A foreign-context interior render has now had every deferred
        # descendant settled. Merge its completed extension state into the
        # enclosing context before that enclosing component finalizes.
        if isinstance(task, _ContextMergeTask):
            _merge_dependencies(task.parent_context, task.child_context)
            continue
        # Case: Render nested component
        if isinstance(task, _RenderTask):
            try:
                ownership = task.deferred.element.ownership_graph or task.position.parent_context.ownership
                if ownership is None:
                    child = _render_one_traced(
                        task.deferred.element,
                        task.deferred.parent,
                        task.deferred.provides,
                    )
                elif task.deferred.physical_parent_region_id is not None:
                    with ownership.active_region(task.deferred.physical_parent_region_id):
                        child = _render_one_traced(
                            task.deferred.element,
                            task.deferred.parent,
                            task.deferred.provides,
                        )
                else:
                    with ownership.active_invocation_region(task.deferred.element.ownership_invocation_id):
                        child = _render_one_traced(
                            task.deferred.element,
                            task.deferred.parent,
                            task.deferred.provides,
                        )
            except Exception as error:  # noqa: BLE001
                bubble(error)
                continue
            _replace_in_parts(task.position.parts, task.position.idx, task.deferred, child.render)
            stack.append(
                _FinalizeTask(
                    child.render,
                    task.position,
                    child.generator,
                    cache_plan=child.cache_plan,
                    cache_hit=child.cache_hit,
                    physical_parent_region_id=task.deferred.physical_parent_region_id,
                )
            )
            stack.extend(reversed(_scan_deferred(child.render)))
        # Case: Finalize nested component
        else:
            try:
                final = settle_in_invocation_region(task, None)
            except Exception as error:  # noqa: BLE001
                bubble(error)
                continue
            if final is not None:
                commit(task.render, final, task.position)

    return root_result


class _DeferredComponentPosition(NamedTuple):
    """Where a ``DeferredComponent`` sits, so we can put its rendered result there."""

    parts: list[RenderPart]  # the list the DeferredComponent is in
    idx: int  # its position in that list (named `idx`, not `index`, so it doesn't hide tuple.index)
    parent_context: CitryContext  # the parent component's context; where this child's dependencies go


class _RenderTask(NamedTuple):
    """Render one deferred child component."""

    deferred: DeferredComponent
    position: _DeferredComponentPosition


class _FinalizeTask(NamedTuple):
    """Run a rendered component's after-render hooks and copy its dependencies up."""

    render: CitryRender
    position: _DeferredComponentPosition | None  # None for the top (root) component
    # The component's live on_render generator when the hook yielded; resumed
    # with the settled result when this task runs (None for most components).
    generator: OnRenderGenerator | None = None
    cache_plan: _CacheMissPlan | None = None
    cache_hit: _CacheHit | None = None
    physical_parent_region_id: PhysicalRegionId | None = None


class _ContextMergeTask(NamedTuple):
    """Merge an interior render only after all of its deferred children settle."""

    parent_context: CitryContext
    child_context: CitryContext


class _InitialRender(NamedTuple):
    """The first render result plus its render-local cache decision."""

    render: CitryRender
    generator: OnRenderGenerator | None
    cache_plan: _CacheMissPlan | None
    cache_hit: _CacheHit | None


def _scan_deferred_parts(
    parts: list[RenderPart],
    parent_context: CitryContext,
    tasks: list[_RenderTask | _ContextMergeTask],
) -> bool:
    """Append deferred work without creating one recursive closure per scan."""
    has_deferred = False
    for i, part in enumerate(parts):
        if isinstance(part, DeferredComponent):
            tasks.append(_RenderTask(part, _DeferredComponentPosition(parts, i, parent_context)))
            has_deferred = True
        else:
            unwrapped = unwrap_physical_region(part)
            if isinstance(unwrapped, CitryRender):
                nested_has_deferred = _scan_deferred_parts(unwrapped.parts, unwrapped.context, tasks)
                has_deferred = has_deferred or nested_has_deferred
                if nested_has_deferred and unwrapped.context is not parent_context:
                    tasks.append(_ContextMergeTask(parent_context, unwrapped.context))
    return has_deferred


def _scan_deferred(render: CitryRender) -> list[_RenderTask | _ContextMergeTask]:
    """
    Find the child components inside ``render`` that still need rendering.

    Returns one ``_RenderTask`` per ``DeferredComponent``, descending into
    every nested ``CitryRender``. Most nested renders share this component's
    context (``<c-if>``/``<c-for>`` blocks, nested templates), but slot-fill
    content invoked during this render carries the context of the component
    that *wrote* the fill, and components inside it defer like any other, so
    cross-context renders are searched too. Descending into an embedded,
    already-completed subtree is harmless: ``render_impl`` finished its queue,
    so it contains no ``DeferredComponent`` parts.

    Each task's ``parent_context`` is the context of the nested render the
    deferred sits in: that is the lexical owner (for fill content, the
    component whose template wrote it), which is where the child's
    dependencies belong (see docs/design/component_slots.md section 8).
    """
    tasks: list[_RenderTask | _ContextMergeTask] = []
    _scan_deferred_parts(render.parts, render.context, tasks)
    return tasks


def _contains_deferred(render: CitryRender) -> bool:
    """Whether a nested render still has any deferred component work."""
    pending = [render]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        object_id = id(current)
        if object_id in seen:
            continue
        seen.add(object_id)
        for part in current.parts:
            if isinstance(part, DeferredComponent):
                return True
            unwrapped = unwrap_physical_region(part)
            if isinstance(unwrapped, CitryRender):
                pending.append(unwrapped)
    return False


def _render_ids(render: CitryRender, *, exclude_render_id: str | None = None) -> set[str]:
    """Collect component render IDs reachable through one render tree."""
    render_ids: set[str] = set()
    pending: list[CitryRender] = [render]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        object_id = id(current)
        if object_id in seen:
            continue
        seen.add(object_id)
        render_id = current.frame.render_id
        if render_id is not None and render_id != exclude_render_id:
            render_ids.add(render_id)
        for part in current.parts:
            nested_part = unwrap_physical_region(part)
            if isinstance(nested_part, CitryRender):
                pending.append(nested_part)
    return render_ids


def _selected_region_ids(ownership: OwnershipGraph, selected: set[int]) -> set[PhysicalRegionId]:
    """Resolve selected render objects to their physical regions."""
    return ownership.selected_region_ids(render_object_ids=selected)


def _render_selection(render: CitryRender) -> tuple[set[str], set[int]]:
    """Collect selected render IDs and object identities in one tree walk."""
    render_ids: set[str] = set()
    object_ids: set[int] = set()
    pending: list[RenderPart] = [render]
    while pending:
        current = pending.pop()
        object_id = id(current)
        if object_id in object_ids:
            continue
        object_ids.add(object_id)
        if isinstance(current, _PhysicalRegion):
            pending.append(current.part)
        elif isinstance(current, CitryRender):
            render_id = current.frame.render_id
            if render_id is not None:
                render_ids.add(render_id)
            pending.extend(current.parts)
    return render_ids, object_ids


def _render_ids_from_parts(parts: list[RenderPart]) -> set[str]:
    """Collect component render IDs reachable from a selected parts list."""
    render_ids: set[str] = set()
    for part in parts:
        nested_part = unwrap_physical_region(part)
        if isinstance(nested_part, CitryRender):
            render_ids.update(_render_ids(nested_part))
    return render_ids


def _render_objects(render: RenderPart) -> set[int]:
    """Collect transient part identities reachable through a render tree."""
    object_ids: set[int] = set()
    pending: list[RenderPart] = [render]
    while pending:
        current = pending.pop()
        object_id = id(current)
        if object_id in object_ids:
            continue
        object_ids.add(object_id)
        if isinstance(current, _PhysicalRegion):
            pending.append(current.part)
        elif isinstance(current, CitryRender):
            pending.extend(current.parts)
    return object_ids


def _render_objects_from_parts(parts: list[RenderPart]) -> set[int]:
    """Collect transient part identities reachable from selected parts."""
    object_ids: set[int] = set()
    for part in parts:
        if isinstance(part, (CitryRender, _PhysicalRegion)):
            object_ids.update(_render_objects(part))
        else:
            object_ids.add(id(part))
    return object_ids


def _contains_render(container: CitryRender, target: CitryRender) -> bool:
    """Return whether ``target`` remains reachable inside ``container``."""
    pending: list[CitryRender] = [container]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if current is target:
            return True
        object_id = id(current)
        if object_id in seen:
            continue
        seen.add(object_id)
        for part in current.parts:
            nested_part = unwrap_physical_region(part)
            if isinstance(nested_part, CitryRender):
                pending.append(nested_part)
    return False


def _replace_in_parts(parts: list[RenderPart], index: int, target: object, new: RenderPart) -> None:
    """
    Put ``new`` where ``target`` currently is in ``parts``.

    ``index`` is where ``target`` was last seen, so we check that spot first. If
    the list has changed (for example user code or an extension edited
    ``parts``), we scan the whole list for ``target`` instead. Each render step
    swaps one item for one item, so positions normally stay put.
    """
    if 0 <= index < len(parts) and parts[index] is target:
        parts[index] = new
        return
    for i, part in enumerate(parts):
        if part is target:
            parts[i] = new
            return
    msg = "deferred part vanished from its .parts list before resolution"
    raise RuntimeError(msg)


def _component_path(component: Component | None) -> list[str]:
    """
    The class names from the root component down to ``component``, inclusive.

    Walks the ``parent`` links upward and reverses, so the root comes first.
    These names are the path frames put into error messages ("MyPage > Card >
    Avatar"; see docs/design/component_on_render.md section 6). An embedded element
    rendered from an expression has no parent link; its chain starts at
    itself, and the path of the component it is embedded in is prepended when
    the error passes through that component's render (``_render_one_traced``).
    """
    names: list[str] = []
    while component is not None:
        names.append(type(component).__name__)
        component = component.parent
    names.reverse()
    return names


def _render_one_traced(
    element: CitryElement,
    parent: Component | None = None,
    provides: dict[str, Any] | None = None,
) -> _InitialRender:
    """
    ``_render_one``, with the component path added to any error raised.

    The path is the parent chain plus this component's class name, which is
    the same chain the created instance would report (its ``parent`` is set
    from this ``parent`` argument), and is available even when the failure
    happens before the instance exists (e.g. kwargs validation).
    """
    with resume_ownership_graph(element.ownership_graph):
        try:
            return _render_one(element, parent, provides)
        except Exception as err:
            ownership = element.ownership_graph or current_ownership_graph()
            if ownership is not None:
                ownership.fail_invocation(element.ownership_invocation_id)
            set_component_error_message(err, [*_component_path(parent), element.comp_cls.__name__])
            raise


def _finalize(render: CitryRender, error: Exception | None) -> CitryRender:
    """
    Settle a rendered component: run ``on_component_rendered`` and apply the result.

    Runs once the component and everything inside it have been rendered, or,
    when ``error`` is set, when a component inside it failed and the error is
    bubbling up (docs/design/component_on_render.md section 5). The extension hook
    receives the rendered output, or ``None`` together with the error when
    rendering failed. An extension may replace the output with a new
    ``CitryRender`` or ``str`` (which also swallows the error), or raise to
    replace the error. An error that is not swallowed is raised here, to
    continue bubbling.
    """
    component = render.context.component
    if component is None:
        if error is not None:
            raise error
        return render
    ownership = render.context.ownership
    ownership_checkpoint = ownership.checkpoint() if ownership is not None else None
    if error is not None:
        render.context._error_tainted = True
    try:
        new_render, out_error, had_error = component.citry.extensions.on_component_rendered(
            component,
            None if error is not None else render,
            error,
        )
    except Exception:
        if ownership is not None:
            if ownership_checkpoint is not None:
                ownership.retire_unselected_after(
                    ownership_checkpoint,
                    through_order=ownership.checkpoint(),
                    preserved_render_ids=set(),
                )
            ownership.settle_component(component.id, failed=True)
        raise
    if had_error:
        render.context._error_tainted = True
    ownership_through_order = ownership.checkpoint() if ownership is not None else None
    if (
        ownership is not None
        and ownership_checkpoint is not None
        and ownership_through_order is not None
        and ownership_checkpoint < ownership_through_order
    ):
        # A no-op hook creates no ownership records, so there is nothing to
        # retire and no reason to rescan every physical region captured so far.
        selected_render_ids = (
            _render_ids(new_render, exclude_render_id=None) if isinstance(new_render, CitryRender) else set()
        )
        selected_objects = _render_objects(new_render) if isinstance(new_render, CitryRender) else None
        ownership.retire_unselected_after(
            ownership_checkpoint,
            through_order=ownership_through_order,
            preserved_render_ids=selected_render_ids,
            preserved_region_ids=(
                _selected_region_ids(ownership, selected_objects) if selected_objects is not None else set()
            ),
        )
    if out_error is not None:
        # A fresh error (raised by an extension just now) gets this
        # component's path; a bubbling error passing through unchanged
        # already carries the frames from where it happened.
        if out_error is not error:
            set_component_error_message(out_error, _component_path(component))
        if ownership is not None:
            ownership.settle_component(component.id, failed=True)
        raise out_error
    if ownership is not None:
        ownership.settle_component(component.id)
    replacement_selected = isinstance(new_render, str) or (new_render is not None and new_render is not render)
    if replacement_selected and ownership is not None and ownership_checkpoint is not None:
        replacement_contains_old = isinstance(new_render, CitryRender) and _contains_render(new_render, render)
        if not replacement_contains_old:
            selected_objects = _render_objects(new_render) if isinstance(new_render, CitryRender) else None
            preserved_render_ids = (
                _render_ids(new_render, exclude_render_id=component.id)
                if isinstance(new_render, CitryRender)
                else set()
            )
            ownership.retire_component_output(
                component.id,
                through_order=ownership_checkpoint,
                descendant_render_ids=_render_ids(render, exclude_render_id=component.id),
                preserved_render_ids=preserved_render_ids,
                preserved_region_ids=(
                    _selected_region_ids(ownership, selected_objects) if selected_objects is not None else set()
                ),
            )
    if isinstance(new_render, str):
        return CitryRender(parts=[new_render], context=render.context, is_component_root=render.is_component_root)
    if isinstance(new_render, CitryRender) and new_render is not render:
        if new_render.context is render.context:
            return CitryRender(
                parts=new_render.parts,
                context=render.context,
                is_component_root=render.is_component_root,
            )
        _merge_dependencies(render.context, new_render.context)
        return CitryRender(parts=[new_render], context=render.context, is_component_root=render.is_component_root)
    if new_render is not None:
        return new_render
    return render


def _validate_client_props_target(element: CitryElement) -> None:
    """Validate the final dynamic target and retain the authored call-site diagnostic."""
    if element.forward_ownership_invocation:
        return
    binding_keys = tuple(binding.key for binding in element.component_tag_client_bindings)
    if CLIENT_PROPS_ATTR not in binding_keys:
        return

    invocation = None
    location = None
    ownership = element.ownership_graph or current_ownership_graph()
    if ownership is not None and element.ownership_invocation_id is not None:
        invocation = next(
            (
                record
                for record in ownership.snapshot().component_invocations
                if record.id == element.ownership_invocation_id
            ),
            None,
        )
        if invocation is not None:
            location = ownership.source_location(invocation.source_location_id)

    comp_cls = element.comp_cls
    tag_name = (
        f"c-{invocation.authored_tag}"
        if invocation is not None
        else f"c-{getattr(comp_cls, 'name', None) or comp_cls.__name__}"
    )
    try:
        validate_client_props_target(comp_cls, binding_keys, tag_name=tag_name)
    except RuntimeError as err:
        if location is not None and invocation is not None:
            try:
                source_class = comp_cls.citry.get_component_by_class_id(invocation.source_class_id)
            except KeyError:
                component_name = None
            else:
                component_name = source_class.__name__
            set_template_position_error_message(
                err,
                location.source,
                location.span,
                component_name,
                location.origin,
            )
        raise


def _render_one(
    element: CitryElement,
    parent: Component | None = None,
    provides: dict[str, Any] | None = None,
) -> _InitialRender:
    """
    Render one component, without rendering the components inside it.

    Creates the Component instance, runs the data methods, calls the
    ``on_render`` hook, builds (or reuses) the template body, and turns it
    into a ``CitryRender``. Any ``<c-child>`` tags in the template become
    unrendered ``DeferredComponent`` parts; rendering those, and running
    ``on_component_rendered``, is done by ``render_impl``.

    Args:
        element: The CitryElement to render. Carries the component class,
            kwargs, slots, and the cached body (node list).
        parent: The parent Component instance if rendering inside another
            component's template. Used to set parent/root references.
        provides: The provide/inject entries this component inherits (captured
            where its tag sits, or passed by the caller). Readable via
            ``Component.inject`` and passed on to its own descendants.

    Returns:
        The initial render whose parts may contain unresolved
        ``DeferredComponent`` values, plus its generator and render-local cache
        decision. ``render_impl`` settles all three together.

    """
    comp_cls = element.comp_cls
    _validate_client_props_target(element)
    citry_instance = comp_cls.citry
    extensions = citry_instance.extensions

    # 1. Create component instance with all state.
    #    Uses _create_instance() which bypasses ComponentMeta.__call__
    #    (that returns a CitryElement) and calls Component.__init__.
    #    __init__ handles input normalization (dict/NamedTuple/dataclass ->
    #    dict, copied), id generation, typed kwargs/slots, raw_ variants,
    #    inherited provides, and parent/root references.
    component = comp_cls._create_instance(
        kwargs=element.kwargs,
        slots=element.slots,
        parent=parent,
        provides=provides,
        _defer_input_finalization=True,
    )
    component._component_tag_client_bindings = element.component_tag_client_bindings
    # Private dynamic-element directives must be visible to input hooks, but
    # never enter the user kwargs those hooks can replace.
    component._element_morph_metadata = element.element_morph_metadata
    component._ownership_invocation_id = element.ownership_invocation_id
    ownership = element.ownership_graph or current_ownership_graph()
    if ownership is None:
        msg = "Component rendering requires an active ownership graph."
        raise RuntimeError(msg)
    ownership.bind_instance(component, element)
    component._ownership_graph = ownership

    # 2. Attach the per-component extension configs (eg `component.view`,
    #    AKA `component.<ext.name>`), then run on_component_input.
    #    Typed construction is deliberately deferred until every input hook
    #    finishes, so hook mutations and the values used to render cannot drift.
    #    Defaults, factories, coercion, and validation run exactly once.
    extensions._init_component_instance(component)
    extensions.on_component_input(component)
    component._finalize_inputs()

    # Trace the authoritative post-hook inputs. The ancestor path is O(depth),
    # so build it only when TRACE is enabled.
    if is_tracing():
        trace_component_msg(
            "RENDER",
            type(component).__name__,
            component.id,
            component_path=_component_path(component),
            slot_fills=component.raw_slots,
        )
    if not element.forward_ownership_invocation:
        # Input hooks may replace raw slot supplies. Bind ownership after the
        # hook so the graph records the slots the component will actually use.
        ownership.bind_supplied_slots(component)

    # 3. Build the current-call boundary before component data executes. A
    #    cache replay keeps this component, its input-hook mutations, ownership
    #    anchors, provides, and invocation-owned range key while replacing only
    #    archived output.
    active_provides = component._provides_inherited
    if component._provides_own:
        active_provides = {**active_provides, **component._provides_own}
    context = CitryContext(
        component=component,
        provides=active_provides,
        sandboxed=citry_instance.settings.sandbox_expressions,
        ownership=ownership,
    )

    cache_extension = extensions.get_extension("cache")
    if not isinstance(cache_extension, CacheExtension):
        raise TypeError("The built-in Cache extension has an invalid runtime type.")
    cache_plan: _CacheMissPlan | None = None
    while True:
        try:
            cache_decision = cache_extension._lookup_component(component, context)
        except _CacheRevisionChanged:
            continue
        if not isinstance(cache_decision, _CacheHit):
            cache_plan = cache_decision
            break
        try:
            replay = (
                _replay_fragment_artifact if cache_decision.miss.kind == "fragment" else _replay_component_artifact
            )
            replayed = replay(
                cache_decision.artifact,
                boundary=component,
                context=context,
                revision=cache_decision.miss.revision,
            )
        except CacheArtifactError as error:
            if cache_extension._revision_snapshot() != cache_decision.miss.revision:
                continue
            cache_extension._record_replay_rejection(cache_decision, component, error)
            cache_plan = cache_decision.miss
            break
        return _InitialRender(
            render=replayed,
            generator=None,
            cache_plan=None,
            cache_hit=cache_decision,
        )

    # 4. Call the data methods on a miss or bypass.
    #    template_data() feeds the template variables; js_data() / css_data()
    #    feed the component's JS/CSS variables, consumed by the built-in
    #    `dependencies` extension (docs/design/dependencies.md section 5).
    #    Each may return a dict, a NamedTuple, or the component's typed
    #    dataclass; `_normalize_data` validates it and converts the validated
    #    instance to a plain dict, so schema defaults and coercions become the
    #    values consumers see. No defensive copy is needed here: an override
    #    produces its result fresh each render, and the default returns the
    #    component's own kwargs, which __init__ already copied per render
    #    (raw_kwargs), so the result is never shared across renders.
    tpl_data = _normalize_data(component.template_data(component.kwargs, component.slots), comp_cls.TemplateData)
    js_data = _normalize_data(component.js_data(component.kwargs, component.slots), comp_cls.JsData)
    css_data = _normalize_data(component.css_data(component.kwargs, component.slots), comp_cls.CssData)

    # 3.5 Overlay template globals: variables exposed to every component's
    #     template without being returned from each template_data(). Two layers,
    #     lowest precedence first: this instance's citry.template_globals, then
    #     any per-render globals from Component.render(template_globals=...). The
    #     component's own data wins over both, so all globals go under tpl_data.
    #     Merged after the schema check above, so a global need not appear in a
    #     component's declared TemplateData. Skipped when there are none, so a
    #     render with no globals pays nothing here.
    instance_globals = citry_instance.template_globals
    render_globals = _render_globals.get()
    if instance_globals or render_globals:
        tpl_data = {**instance_globals, **(render_globals or {}), **tpl_data}

    context.variables = tpl_data

    # 4.5 on_component_data: extensions may add/modify the data, and stash
    #     tree-wide state into ``context.extra`` (e.g. the dependencies
    #     extension's render records).
    extensions.on_component_data(component, context, tpl_data, js_data, css_data)

    # 5. ``provides`` are the entries this component inherited plus any
    #    provide or block changes it registered during template_data; a new
    #    mapping is built only when outgoing state changed (see
    #    docs/design/component_provide.md section 4.1).
    active_provides = component._provides_inherited
    if component._provides_own:
        active_provides = {**active_provides, **component._provides_own}
    context.provides = active_provides

    # 5.5 The per-component render hook (docs/design/component_on_render.md section 3).
    #     Returning None (the default) renders the template as usual.
    #     Returning content makes it the component's whole output, and the
    #     template body below is never built or walked. A generator runs up
    #     to its first yield here (the "before" phase), and what it yielded
    #     picks the output the same way; the live generator then travels with
    #     the component's finalize task and is resumed with the settled
    #     result once the whole subtree has rendered (``settle`` in
    #     ``render_impl``).
    hook_checkpoint = ownership.checkpoint()
    generator: OnRenderGenerator | None = None
    parts: list[RenderPart] | None = None
    try:
        hook_result = component.on_render()
        if is_generator(hook_result):
            # Prime the generator (runs the before-phase, up to the first
            # yield). A bare first yield means "render the template as usual";
            # yielded or returned content becomes the output instead.
            generator = hook_result
            parts, generator = _send_into_generator(generator, None, context, component, default_on_none=True)
        elif hook_result is not None:
            parts = _replacement_parts(hook_result, context, component)
    except Exception:
        ownership.retire_unselected_after(
            hook_checkpoint,
            through_order=ownership.checkpoint(),
            preserved_render_ids=set(),
        )
        raise
    hook_through_order = ownership.checkpoint()

    if parts is not None:
        if hook_checkpoint < hook_through_order:
            selected_render_ids = _render_ids_from_parts(parts)
            selected_objects = _render_objects_from_parts(parts)
            ownership.retire_unselected_after(
                hook_checkpoint,
                through_order=hook_through_order,
                preserved_render_ids=selected_render_ids,
                preserved_region_ids=_selected_region_ids(ownership, selected_objects),
            )
        return _InitialRender(
            render=CitryRender(parts=parts, context=context, is_component_root=not comp_cls.transparent),
            generator=generator,
            cache_plan=cache_plan,
            cache_hit=None,
        )

    # 6. Build the body (the list of static strings and node objects the
    #    template compiles to). Parsing and compiling the template runs once
    #    per component class (cached on the class).
    #
    #    Then the Const optimization kicks in. extract_const_vars() collects
    #    the template variables wrapped in Const() ("same value on every
    #    render") and turns them into a cache key. The first render with a
    #    given set of Const values builds the node list and runs precompute_const_parts()
    #    on it, which does the work that depends only on those values right
    #    away: e.g. "{{ cols }}" with cols=Const(3) becomes the text "3", and
    #    a <c-if> whose condition uses only Const values keeps just the
    #    branch that matches. The result is cached, so later renders with the
    #    same Const values reuse it and skip all of that work. See
    #    docs/design/component_constness.md and citry/constness.py.
    #
    #    on_template_compiled fires here (per built node list, before the
    #    optimization and caching), so an extension can transform the node
    #    list once and have the transform cached. See
    #    docs/design/extensions.md section 7.4.
    #
    #    Only Const values the template actually uses (``compiled.used_vars``)
    #    go into the value part of the cache key; a Const value the template
    #    never reads cannot change the output. The presence of every variable
    #    name is keyed separately because c-for/c-fill reject binding a name
    #    already in scope, including one the template otherwise never reads.
    #    A node injected by an extension may use a value outside the compiled
    #    set; that value stays un-optimized and re-evaluates each render.
    template_output_checkpoint = ownership.checkpoint()
    try:
        compiled = _get_compiled_template(comp_cls)
        generate = compiled.generate if compiled is not None else None
        if compiled is None or generate is None:
            body: list[BodyItem] = []
        else:
            const_vars, signature = extract_const_vars(tpl_data, used_vars=compiled.used_vars)
            visible_names = frozenset(tpl_data)

            def build() -> list[BodyItem]:
                return precompute_const_parts(
                    extensions.on_template_compiled(comp_cls, generate()),
                    const_vars,
                    # Precomputing an attribute region bakes its dict before extensions
                    # see it, so keep the regions live when anyone subscribes.
                    precompute_attrs=not extensions.has_hook("on_attrs_resolved"),
                    sandboxed=citry_instance.settings.sandbox_expressions,
                    visible_names=visible_names,
                )

            body = citry_instance._const_body_cache.get_or_build(
                comp_cls,
                signature,
                build,
                visible_names=visible_names,
            )

        # 7. Walk the body into a parts list and wrap it in a CitryRender. Any nested
        #    components are left as unrendered DeferredComponent parts; render_impl
        #    renders them and runs on_component_rendered for each one once everything
        #    inside it has been rendered. This render is the component's whole
        #    output, so it is marked as the component's root render (serialization
        #    relies on the flag to find component frame boundaries). A transparent
        #    component opts out: its output joins the surrounding frame and gets no
        #    data-cid marker (e.g. the <c-provide> built-in).
        if comp_cls.pure:
            pure_lookup = pure_body_lookup(
                comp_cls,
                body,
                context.variables,
                compiled.used_vars if compiled is not None else (),
            )
        else:
            pure_lookup = None
        if pure_lookup is not None and pure_lookup[1] is not None:
            parts = _replay_pure_body(pure_lookup[1], context)
        elif pure_lookup is not None:
            parts, pure_plan, cached_node_count = _render_and_capture_pure_body(body, context, component)
            if cached_node_count:
                store_pure_body(pure_lookup[0], pure_plan)
        else:
            parts = _render_body(body, context)
    except Exception as render_error:
        context._error_tainted = True
        failed_output_through_order = ownership.checkpoint()
        if generator is None:
            raise
        # The component's own template failed; deliver the error to its live
        # on_render generator, the same ``(None, error)`` it would receive
        # for a failing child. This is what lets an error boundary guard its
        # own slot content, which renders right here in its body walk. The
        # generator may produce replacement output; if it does not (plain
        # return), the error continues out as usual.
        recovery_checkpoint = ownership.checkpoint()
        parts, generator = _send_into_generator(
            generator,
            (None, render_error),
            context,
            component,
            default_on_none=False,
        )
        recovery_through_order = ownership.checkpoint()
        if parts is None:
            raise
        selected_objects = _render_objects_from_parts(parts)
        ownership.retire_unselected_after(
            recovery_checkpoint,
            through_order=recovery_through_order,
            preserved_render_ids=_render_ids_from_parts(parts),
            preserved_region_ids=_selected_region_ids(ownership, selected_objects),
        )
        ownership.retire_range(
            template_output_checkpoint,
            through_order=failed_output_through_order,
        )

    if hook_checkpoint < hook_through_order:
        # Most components use the default hook. Keep that render path linear
        # in component count by doing selection work only for captured effects.
        selected_render_ids = _render_ids_from_parts(parts)
        selected_objects = _render_objects_from_parts(parts)
        ownership.retire_unselected_after(
            hook_checkpoint,
            through_order=hook_through_order,
            preserved_render_ids=selected_render_ids,
            preserved_region_ids=_selected_region_ids(ownership, selected_objects),
        )
    return _InitialRender(
        render=CitryRender(parts=parts, context=context, is_component_root=not comp_cls.transparent),
        generator=generator,
        cache_plan=cache_plan,
        cache_hit=None,
    )


def _i18n_body_capture_is_empty(component: Component) -> bool:
    """Whether skipping this component's body would omit no i18n metadata."""
    usage = component.i18n._usage_state
    if usage is not None and not usage.empty:
        return False
    bindings = component.i18n._bindings_state
    return bindings is None or not (bindings.records or bindings.markers or bindings._pending_text)


def _capture_pure_part(part: RenderPart, context: CitryContext) -> str | PureInteriorBody | None:
    """Detach one ownership-free output part for a render-local pure plan."""
    if isinstance(part, str):
        return part
    # Exact type matters: PhysicalRegionRender is a CitryRender subclass whose
    # wrapper identity and graph record must be recreated by the slot runtime.
    if type(part) is not CitryRender or part.context is not context or part.is_component_root:
        return None
    plan: list[str | PureInteriorBody] = []
    for nested_part in part.parts:
        captured = _capture_pure_part(nested_part, context)
        if captured is None:
            return None
        plan.append(captured)
    return PureInteriorBody(tuple(plan))


def _render_and_capture_pure_body(
    body: list[BodyItem],
    context: CitryContext,
    component: Component,
) -> tuple[list[RenderPart], PureBodyPlan, int]:
    """Render once while compiling safe values around live transaction holes."""
    ownership = context.ownership
    if ownership is None:
        msg = "Pure component rendering requires an active ownership graph."
        raise RuntimeError(msg)
    parts: list[RenderPart] = []
    plan: list[str | PureInteriorBody | PureLiveBodyItem] = []
    cached_node_count = 0
    tracing = is_tracing()
    for item in body:
        if isinstance(item, str):
            parts.append(item)
            plan.append(item)
            continue
        checkpoint = ownership.checkpoint()
        i18n_empty_before = _i18n_body_capture_is_empty(component)
        part = _render_pure_live_item(item, context, tracing=tracing)
        parts.append(part)
        if ownership.checkpoint() == checkpoint and i18n_empty_before and _i18n_body_capture_is_empty(component):
            captured = _capture_pure_part(part, context)
            if captured is not None:
                plan.append(captured)
                cached_node_count += 1
                continue
        plan.append(PureLiveBodyItem(item))
    return parts, tuple(plan), cached_node_count


def _render_pure_live_item(item: Node, context: CitryContext, *, tracing: bool) -> RenderPart:
    """Execute one live plan hole with the ordinary body-walker contract."""
    if tracing:
        trace_node_msg("RENDER", type(item).__name__, getattr(item, "position", None))
    try:
        part = item.render(context)
    except Exception as err:
        _attach_template_position(err, item, context)
        raise
    unwrapped = unwrap_physical_region(part)
    if isinstance(unwrapped, CitryRender) and unwrapped.context is not context and not _contains_deferred(unwrapped):
        _merge_dependencies(context, unwrapped.context)
    return part


def _replay_pure_body(plan: PureBodyPlan, context: CitryContext) -> list[RenderPart]:
    """Recreate transparent render wrappers against the current component context."""
    parts: list[RenderPart] = []
    for item in plan:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, PureInteriorBody):
            parts.append(CitryRender(parts=_replay_pure_body(item.parts, context), context=context))
        else:
            parts.append(_render_pure_live_item(item.item, context, tracing=is_tracing()))
    return parts


def _send_into_generator(
    generator: OnRenderGenerator,
    send_arg: Any,
    context: CitryContext,
    component: Component,
    *,
    default_on_none: bool,
) -> tuple[list[RenderPart] | None, OnRenderGenerator | None]:
    """
    Send into an ``on_render`` generator until it produces an outcome.

    Used inside ``_render_one``, at priming time (``send_arg`` is ``None``)
    and when the component's own template render failed (``send_arg`` is
    ``(None, error)``). Returns ``(parts, generator)``: the replacement parts
    (``None`` for "no replacement") and the generator if it is still live
    (``None`` once it finished).

    An unrenderable yielded value (the ``TypeError`` from the coercion) is
    delivered back into the generator as ``(None, error)``, so every yield
    uniformly receives the settled result or failure of what it yielded.

    A bare yield (``yield`` / ``yield None``) means "render the template as
    usual" while priming (``default_on_none=True``). After an error was
    delivered (``default_on_none=False``) it means "answer again with the
    unchanged result", so the same value is re-sent, mirroring the settle
    loop in ``render_impl``.
    """
    while True:
        try:
            yielded = generator.send(send_arg)
        except StopIteration as stop:
            if stop.value is None:
                # Plain return: no replacement, generator done.
                return None, None
            return _replacement_parts(stop.value, context, component), None
        if yielded is None:
            if default_on_none:
                return None, generator
            continue
        try:
            return _replacement_parts(yielded, context, component), generator
        except TypeError as bad_yield:
            context._error_tainted = True
            set_component_error_message(bad_yield, _component_path(component))
            send_arg = (None, bad_yield)


def _replacement_parts(value: RenderReplacement, context: CitryContext, component: Component) -> list[RenderPart]:
    """
    Convert an ``on_render`` replacement value into the component's parts list.

    The accepted values mirror what a ``{{ ... }}`` expression accepts
    (``_render_value`` in citry_render.py), with two differences: a ``str``
    is the component's own output, so it is used as-is rather than
    autoescaped, and an unsupported type is an error rather than being
    escaped to text (docs/design/component_on_render.md section 3.1).
    """
    # A Const marker is unwrapped first (a replacement built from a literal
    # template attribute arrives Const-wrapped); the value becomes output
    # here, so the marker has no further role, and the proxy must not leak
    # into the parts.
    value = const_value(value)
    if isinstance(value, ComponentLike):
        value = _resolve_component_like(value, component.citry)
    if isinstance(value, str):
        return [value]
    if isinstance(value, Slot):
        # Invoked with no data, like {{ my_slot }}. Slot content renders with
        # the scope of the component that wrote it, so its collected data is
        # copied into this render (the same merge as _render_body does).
        part = value(provides=context.provides)
        unwrapped = unwrap_physical_region(part)
        if (
            isinstance(unwrapped, CitryRender)
            and unwrapped.context is not context
            and not _contains_deferred(unwrapped)
        ):
            _merge_dependencies(context, unwrapped.context)
        return [part]
    if isinstance(value, CitryElement):
        # Deferred like a <c-child> tag in the template: the render_impl loop
        # renders it, so a replacement chain can never exhaust the Python
        # call stack.
        ownership = context.ownership
        return [
            DeferredComponent(
                value,
                parent=component,
                provides=context.provides,
                physical_parent_region_id=(ownership.current_region_id() if ownership is not None else None),
            )
        ]
    if isinstance(value, CitryRender):
        # An already-rendered subtree is inlined; its collected data is
        # copied into this render.
        if value.context is not context:
            _merge_dependencies(context, value.context)
        return [value]
    msg = (
        f"{type(component).__name__}.on_render() returned {type(value).__name__!r}; "
        "expected a str, a composed element, a CitryRender, a Slot, or None."
    )
    raise TypeError(msg)


def _get_compiled_template(comp_cls: type[Component]) -> CitryTemplate | None:
    """
    Return the component's template with its compiled form filled in.

    The template is loaded via ``assets.load_template``, which resolves
    ``template`` / ``template_file``, reads the file when needed, fires
    ``on_template_loaded``, and caches the ``CitryTemplate`` on the class (see
    docs/design/asset_loading.md). On the first render this function compiles
    the source and fills the struct's ``generate`` / ``used_vars`` in place,
    so the loaded and compiled halves share one cache and one invalidation
    (``Component.reset_template()``). Each call to ``generate`` produces a
    fresh node list. Returns ``None`` when the component has no template.

    A parse or compile error is re-raised with the template's origin (the file
    path, or ``module::Class`` for inline) prefixed to its message, so a
    syntax error names where the template came from.
    """
    template = load_template(comp_cls)
    if template is None:
        return None
    if template.generate is None:
        try:
            generate = _compile_template(template, comp_cls.citry._tag_rules())
            _check_declared_slots(comp_cls, template)
            template.generate = generate
        except Exception as err:
            set_template_origin_error_message(err, template.origin)
            raise
    return template


def _check_declared_slots(comp_cls: type[Component], template: CitryTemplate) -> None:
    """
    Check a component's own ``<c-slot>`` tags against its ``Slots`` schema.

    Runs once, at first compile, and only when the component declares a closed
    ``Slots`` schema (an omitted ``Slots`` accepts any fills, so there is nothing
    to check; see docs/design/component_slots.md section 9.5). It catches a *dead slot*: a
    ``<c-slot name="X">`` whose ``X`` is not a declared slot, so no caller can
    ever fill it. Dynamic-name slots (``<c-slot c-name="...">``) are not in
    ``declared_slots``, so they are never flagged.

    A slot's ``required`` flag and a default on the matching ``Slots`` field are
    orthogonal (the fill may be passed from outside, or omitted), so that
    combination is deliberately not flagged.
    """
    slot_specs = get_fields(comp_cls.Slots)
    if slot_specs is None:
        return
    declared = {spec.name for spec in slot_specs}
    for slot in template.declared_slots:
        if slot.name not in declared:
            close = get_close_matches(slot.name, sorted(declared), n=1, cutoff=0.7)
            hint = f" Did you mean {close[0]!r}?" if close else ""
            msg = (
                f"Component {comp_cls.__name__!r} renders <c-slot name={slot.name!r}> "
                f"(line {slot.line}) but its Slots class does not declare {slot.name!r}, so no "
                f"caller can fill it.{hint} Add {slot.name!r} to Slots, or remove the slot."
            )
            raise RuntimeError(msg)


def _compile_template(
    template: CitryTemplate,
    user_rules: dict[str, TagRules] | None = None,
) -> Callable[[], list[BodyItem]]:
    """
    Parse, compile, and exec a template's source.

    Uses the citry_core pipeline: parse -> compile -> exec. The
    ``generate_template`` function from the exec'd namespace is returned;
    calling it returns a fresh list of static strings and runtime node objects.
    The component-template caller publishes it only after its class-level slot
    validation succeeds. The parsed AST's root ``used_variables`` (which are
    transitive) become ``template.used_vars``.

    ``user_rules`` are the parse-time validation rules derived from the
    registered components' declarations (``Citry._tag_rules()``), so a
    template using a declared component fails here, at parse time, on unknown
    or missing kwargs/fills.

    The compiled code creates node objects (ExprNode, ComponentNode, etc.) by
    name. Those names are supplied through the ``ns`` namespace below, so the
    generated code can find them.
    """
    ast = parse_template(template.source, user_rules=user_rules)
    template.used_vars = frozenset(token.content for token in ast.used_variables)
    # The static <c-slot> declarations, kept for `_check_declared_slots` (the
    # caller runs it, since it has the component class and thus its Slots).
    template.declared_slots = tuple(
        DeclaredSlot(slot.token.content, slot.token.line_col[0], slot.token.line_col[1]) for slot in ast.slots
    )
    code = compile_template(ast)

    # Build the namespace for exec. "source" is the original template string,
    # passed to nodes for error reporting and diagnostics. This namespace
    # becomes the returned function's globals, so the node classes and source
    # stay bound to it.
    ns: dict[str, Any] = {
        "source": template.source,
        "ExprNode": ExprNode,
        "TemplateNode": TemplateNode,
        "ComponentNode": ComponentNode,
        "ElementAttrsNode": ElementAttrsNode,
        "ElementKeyNode": ElementKeyNode,
        "IfNode": IfNode,
        "ForNode": ForNode,
        "SlotNode": SlotNode,
        "FillDataBinding": FillDataBinding,
        "FillNode": FillNode,
        "StaticHtmlAttr": StaticHtmlAttr,
        "ExprHtmlAttr": ExprHtmlAttr,
        "TemplateHtmlAttr": TemplateHtmlAttr,
    }
    exec(code, ns)  # noqa: S102
    generate: Callable[[], list[BodyItem]] = ns["generate_template"]
    return generate


def _compile_nested_template(
    template_str: str,
    user_rules: dict[str, TagRules] | None = None,
    component_class: type[Component] | None = None,
) -> Callable[[], list[BodyItem]]:
    """
    Compile a nested template fragment into its body-generating function.

    Used by the nodes that carry a template *inside* an attribute value (a
    ``c-body="<span>{{ x }}</span>"`` on a component). Such a fragment is not
    a component class's template, so there is no class-level ``CitryTemplate``
    to fill; a throwaway one wraps the fragment for the shared compile step.
    Position-in-the-outer-template error context is attached by the node's
    render wrapper, not here. When an owning component class is available, the
    fragment passes through the same compiled-template extension hooks as that
    class's primary body. Nested-template bindings therefore remain in the
    owner's handler/State scope without rewriting the authored source string.
    """
    template = CitryTemplate(source=template_str, origin="<nested template>")
    generate = _compile_template(template, user_rules)
    if component_class is None:
        return generate
    compiled = component_class.citry.extensions.on_template_compiled(component_class, generate())
    return lambda: compiled


def _render_body(body: list[BodyItem], context: CitryContext) -> list[RenderPart]:
    """
    Render a body (a list of static strings and nodes) into a list of parts.

    Static strings pass through unchanged. Each node is rendered with
    ``context`` and adds a part: a ``str``, a nested ``CitryRender``, or a
    ``DeferredComponent`` (a ``<c-child>`` tag, rendered later by ``render_impl``).

    A node may return a ``CitryRender`` from a *different* render: an
    already-rendered value found in a ``{{ ... }}`` expression. When that happens
    its dependencies are copied into this render's context. A ``CitryRender`` from
    *this* render (for example a ``<c-if>`` block or a nested template, which use
    the same context) does not need copying.

    The parts are returned as a list, not joined into one string, so that an
    already-rendered value embedded in the middle can still be read later. Joining
    happens in ``CitryRender.serialize()``.
    """
    parts: list[RenderPart] = []
    tracing = is_tracing()  # hoisted: one level check per body walk, not per node
    for item in body:
        if isinstance(item, str):
            parts.append(item)
            continue
        if tracing:
            trace_node_msg("RENDER", type(item).__name__, getattr(item, "position", None))
        try:
            part = item.render(context)
        except Exception as err:
            _attach_template_position(err, item, context)
            raise
        unwrapped = unwrap_physical_region(part)
        if (
            isinstance(unwrapped, CitryRender)
            and unwrapped.context is not context
            and not _contains_deferred(unwrapped)
        ):
            _merge_dependencies(context, unwrapped.context)
        parts.append(part)

    return parts


def _attach_template_position(err: Exception, node: BodyItem, context: CitryContext) -> None:
    """
    Add the failing node's template snippet to the error message.

    Every compiler-emitted node carries ``source`` (the whole template
    string) and ``position`` (its start/end indices in it); a node injected
    by an extension may not, in which case this does nothing. The snippet is
    added once per error, by the innermost failing node: control-flow bodies
    render through ``_render_body`` recursively, so the enclosing node's
    pass through here is a no-op (see ``set_template_position_error_message``).

    The header names ``context.component`` as the template's owner. That
    holds for slot-fill content too: a fill body renders with the context of
    the component that wrote it, and its nodes come from that component's
    template.
    """
    source = getattr(node, "source", None)
    position = getattr(node, "position", None)
    if not isinstance(source, str) or not isinstance(position, tuple) or len(position) != 2:
        return
    component = context.component
    component_name = type(component).__name__ if component is not None else None
    # Best-effort: name where the template came from in the snippet header.
    # The template is already loaded and cached by the time a node renders, so
    # this is a cache read; any failure just drops the origin from the header.
    origin: str | None = None
    if component is not None:
        try:
            template = load_template(type(component))
        except Exception:  # noqa: BLE001 - error reporting must not raise
            template = None
        if template is not None:
            origin = template.origin
    set_template_position_error_message(err, source, position, component_name, origin)


def _normalize_data(maybe_data: Any, schema_cls: type | None) -> dict[str, Any]:
    """
    Normalize one data method's result to a plain dict and validate it.

    The result of ``template_data()`` / ``js_data()`` / ``css_data()`` may be
    a dict, a NamedTuple, or the component's typed dataclass, so convert with
    ``to_dict``. When the component declares the matching schema class
    (``TemplateData``/``JsData``/``CssData``), constructing
    ``schema_cls(**data)`` raises on invalid input and materializes schema
    defaults and coercions. Convert that validated instance back to a shallow
    dict so every downstream consumer observes the declared schema result.
    """
    data: dict[str, Any] = to_dict(maybe_data) if maybe_data is not None else {}
    if schema_cls is None:
        return data
    validated = maybe_data if isinstance(maybe_data, schema_cls) else schema_cls(**data)
    return to_dict(validated)


def _merge_dependencies(into: CitryContext, source: CitryContext) -> None:
    """
    Fire the ``on_render_context_merge`` hook: a nested render's output was consumed
    by an enclosing render, so each extension merges its own slice of
    ``source.extra`` into ``into.extra`` with its own policy (the dependencies
    extension appends its records preserving order; see
    docs/design/component_rendering.md section 6 and docs/design/extensions.md section
    9.1). The core owns only the firing, not the merge semantics.

    A render with no component on either context has no ``Citry`` instance to
    reach extensions through; there is nothing to merge for it either, since
    only component renders collect tree-wide state.
    """
    if source._error_tainted:
        into._error_tainted = True
    component = into.component if into.component is not None else source.component
    if component is None:
        return
    component.citry.extensions.on_render_context_merge(into, source)
