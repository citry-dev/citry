"""
Turn a rendered ``CitryRender`` tree into final HTML, tagging each component's
root element(s) with a ``data-cid-<id>`` marker.

This is the serialize half of the pipeline: rendering builds the
``CitryRender`` tree, and this turns it into a string. Each component's HTML
gets a marker attribute on its root element(s), so the browser can tell which
component rendered which part of the page. When one component's root element is
itself another component, that element carries both markers, e.g.
``<div data-cid-child="" data-cid-parent="">``.

It works in two passes, and neither pass calls itself, so a deeply nested page
does not run into Python's recursion limit (the same reason the render side uses
a queue):

1. Top-down: for each component, build its own HTML with its child components
   left as ``<template c-render-id="...">`` placeholders, then call
   ``mark_html`` once. In a single scan it splices the markers onto that
   component's root element(s) and splits the HTML around the child
   placeholders, reporting which markers each placeholder received (a
   placeholder at the root inherits the parent's markers; that is how a
   parent's marker reaches a child that is its root element).
2. Bottom-up: join each component's segments back together with each child's
   finished HTML in its placeholder's slot.

See docs/design/deferred_rendering.md section 6.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, get_args

from citry.citry_render import CitryRender, DepsPosition, DepsStrategy, Placeholder
from citry_core.html_transform import mark_html

if TYPE_CHECKING:
    from citry.citry_render import RenderPart
    from citry.component import Component

# The attribute name the placeholders carry, and that mark_html splits the
# HTML around.
_RENDER_ID_ATTR = "c-render-id"

# The allowed strategy/position values, computed once (get_args walks the
# Literal type, so doing it per serialize would be needless work on a path that
# runs once per page).
_DEPS_STRATEGIES = get_args(DepsStrategy)
_DEPS_POSITIONS = get_args(DepsPosition)

# One scanned frame: the HTML split around child placeholders (always one more
# segment than placeholders), and per placeholder its id, its own text (with
# any spliced markers), and the markers it received.
_Frame = tuple[list[str], list[tuple[str, str, list[str]]]]


def serialize_render(
    root: CitryRender,
    *,
    deps_strategy: DepsStrategy = "document",
    deps_position: DepsPosition = "smart",
) -> str:
    """Serialize a render tree to HTML, adding ``data-cid-<id>`` markers (see module doc)."""
    if deps_strategy not in _DEPS_STRATEGIES:
        msg = f"Invalid deps_strategy {deps_strategy!r}; must be one of {_DEPS_STRATEGIES}"
        raise ValueError(msg)
    if deps_position not in _DEPS_POSITIONS:
        msg = f"Invalid deps_position {deps_position!r}; must be one of {_DEPS_POSITIONS}"
        raise ValueError(msg)
    # Pass 1 (top-down): build each component's HTML with its children still as
    # placeholders, add its markers, and work out which markers each child
    # inherits. An explicit stack keeps depth off the Python call stack.
    #
    # `frame_by_key` holds each component's scanned frame (children still
    # placeholders), keyed by the component's render id. `order` records the
    # order components were reached, so pass 2 can walk it in reverse (children
    # before parents). The root has no parent and may have no component, so it
    # uses the key "".
    frame_by_key: dict[str, _Frame] = {}
    order: list[str] = []
    root_key = ""

    # Placeholder parts found while building frames: unique placeholder id
    # (the Placeholder.key plus a counter) -> the exact text standing in for
    # it. The text rides the same <template c-render-id> machinery as child
    # components, but nothing fills it during pass 2, so it survives into the
    # joined HTML; the on_serialize hook replaces it there.
    placeholder_map: dict[str, str] = {}

    # Each stack item is (render, markers_inherited_from_parent, key).
    stack: list[tuple[CitryRender, list[str], str]] = [(root, [], root_key)]
    while stack:
        render, inherited, key = stack.pop()
        component = render.context.component

        children: list[tuple[CitryRender, str]] = []
        frame = _build_frame(render, component, children, placeholder_map)

        # A render only gets its component's marker when it is that component's
        # root render; a transparent component's output (is_component_root
        # False, e.g. <c-provide>) stays unmarked even when serialized directly.
        # Extensions add per-instance markers (e.g. the CSS-variables hash)
        # under the well-known extra key on the component's own context.
        if component is not None and render.is_component_root:
            own_markers = [f"data-cid-{component.id}", *render.context._get_root_markers()]
        else:
            own_markers = []
        root_markers = own_markers + inherited
        if frame and (root_markers or children):
            segments, placeholders = mark_html(frame, root_markers, _RENDER_ID_ATTR)
        else:
            # Nothing to mark and no placeholders to find (a render with no
            # component and no children, e.g. a manually built CitryRender),
            # or an empty frame: the frame is a single segment as-is.
            segments, placeholders = [frame], []

        frame_by_key[key] = (segments, placeholders)
        order.append(key)
        added_by_child = {child_id: added for child_id, _, added in placeholders}
        for child_render, child_id in children:
            stack.append((child_render, added_by_child.get(child_id, []), child_id))
        # mark_html may have spliced markers onto a Placeholder's template
        # tag (when it sits at a component root); record the exact final
        # text, since that is what the on_serialize hook must find in the
        # joined HTML. Markers spliced onto a placeholder are dropped with
        # it when the hook replaces the text.
        for child_id, placeholder_html, _ in placeholders:
            if child_id in placeholder_map:
                placeholder_map[child_id] = placeholder_html

    # Pass 2 (bottom-up): join each frame's segments with its children's
    # finished HTML in the placeholder slots. Walking `order` in reverse means
    # a child is finished before its parent needs it. An unknown id (a literal
    # <template c-render-id> a user wrote) keeps its placeholder text as-is.
    finished: dict[str, str] = {}
    for key in reversed(order):
        segments, placeholders = frame_by_key[key]
        parts = [segments[0]]
        for (child_id, placeholder_html, _), segment in zip(placeholders, segments[1:], strict=True):
            parts.append(finished.get(child_id, placeholder_html))
            parts.append(segment)
        finished[key] = "".join(parts)

    html = finished[root_key]

    # The serialize hook: extensions do whole-page work here, e.g. the
    # dependencies extension places the collected JS/CSS (filling the
    # placeholder texts and the default head/body locations). A render with
    # no component has no Citry instance to reach extensions through, and
    # nothing was collected for it either.
    root_component = root.context.component
    if root_component is not None:
        html = root_component.citry.extensions.on_serialize(
            context=root.context,
            html=html,
            placeholders=placeholder_map,
            deps_strategy=deps_strategy,
            deps_position=deps_position,
        )

    return html


def _build_frame(
    render: CitryRender,
    component: Component | None,
    children: list[tuple[CitryRender, str]],
    placeholder_map: dict[str, str],
) -> str:
    """
    Join one component's parts into an HTML string.

    Plain text passes through. A nested render that is another component's
    completed root render (``is_component_root``) is a child component: it
    becomes a ``<template c-render-id="...">`` placeholder, recorded in
    ``children`` for pass 2 to fill in. A ``Placeholder`` part (a spot an
    extension fills at serialize time, e.g. ``<c-js>``) becomes the same kind
    of template tag under a unique id recorded in ``placeholder_map``; pass 2
    keeps its text, and the ``on_serialize`` hook replaces it in the joined
    HTML. Every other nested render joins in directly:
    ``<c-if>``/``<c-for>`` blocks and nested templates (same component), and
    slot-fill content (which carries the context of the component that
    *wrote* the fill, but renders as part of this frame). Walking the
    joined-in blocks only follows the template's own nesting, so it does not
    recurse deeply.
    """
    out: list[str] = []

    def walk(parts: list[RenderPart]) -> None:
        for part in parts:
            if isinstance(part, str):
                out.append(part)
            elif isinstance(part, CitryRender):
                part_component = part.context.component
                if part.is_component_root and part_component is not None and part_component is not component:
                    # Another component's whole output: leave a placeholder for pass 2.
                    out.append(f'<template c-render-id="{part_component.id}"></template>')
                    children.append((part, part_component.id))
                else:
                    # Interior content (control flow, nested template, slot-fill
                    # content) or a component-less render: join in directly.
                    walk(part.parts)
            elif isinstance(part, Placeholder):
                # The counter makes each occurrence's id (and so its text)
                # unique, so the hook can address occurrences individually.
                placeholder_id = f"{part.key}:{len(placeholder_map) + 1}"
                text = f'<template c-render-id="{placeholder_id}"></template>'
                placeholder_map[placeholder_id] = text
                out.append(text)
            else:
                # A DeferredComponent here means render() never resolved it.
                # RuntimeError (not TypeError): the render is unfinished, nothing
                # was given the wrong type.
                msg = "unresolved DeferredComponent at serialize(); render() must process the queue first"
                raise RuntimeError(msg)  # noqa: TRY004

    walk(render.parts)
    return "".join(out)
