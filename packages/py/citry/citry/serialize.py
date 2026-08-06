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

See docs/design/component_rendering_defer.md section 6.
"""

from __future__ import annotations

import re
from secrets import token_hex
from typing import TYPE_CHECKING, get_args

from citry.citry_render import (
    CitryRender,
    DepsPosition,
    DepsStrategy,
    PhysicalRegionPart,
    PhysicalRegionRender,
    Placeholder,
)
from citry.ownership_manifest import EXTRA_KEY as OWNERSHIP_MANIFEST_KEY
from citry.ownership_manifest import (
    OwnershipManifestArtifact,
    ownership_manifest_required,
    prepare_ownership_manifest,
)
from citry_core.html_transform import mark_html

if TYPE_CHECKING:
    from citry.citry_render import RenderPart

# The attribute name the placeholders carry, and that mark_html splits the
# HTML around.
_RENDER_ID_ATTR = "c-render-id"

# A root marker written as a full `name="value"` attribute. The marking scan
# (mark_html) only splices bare `name=""` attributes, so valued markers are
# recognized here and spliced by this module instead; see _apply_valued_markers.
_VALUED_MARKER_RE = re.compile(r'^[^\s"\'=<>/]+="[^"<>]*"$')

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
    artifact: OwnershipManifestArtifact | None
    if (
        deps_strategy in ("document", "fragment")
        and root.context.component is not None
        and ownership_manifest_required(root)
    ):
        artifact = prepare_ownership_manifest(root)
        root.context.extra[OWNERSHIP_MANIFEST_KEY] = artifact
    else:
        artifact = None
        root.context.extra.pop(OWNERSHIP_MANIFEST_KEY, None)
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
    # (the Placeholder.key plus a counter and the private identity below) ->
    # the exact text standing in for it. The text rides the same
    # <template c-render-id> machinery as child components, but nothing fills
    # it during pass 2, so it survives into the joined HTML; the on_serialize
    # hook replaces it there.
    placeholder_map: dict[str, str] = {}
    # A per-serialization identity keeps generated placeholder ids distinct
    # from authored <template c-render-id> elements, even when an author writes
    # the same logical key and occurrence counter. It never reaches final HTML.
    placeholder_nonce = token_hex(16)

    # Each stack item is (render, plain markers inherited from the parent,
    # valued markers inherited from the parent, key). Valued markers are the
    # `name="value"` form, threaded separately because mark_html cannot splice
    # them (see _apply_valued_markers).
    stack: list[tuple[CitryRender, list[str], list[str], str]] = [(root, [], [], root_key)]
    while stack:
        render, inherited, inherited_valued, key = stack.pop()
        component = render.context.component
        render_frame = render.frame

        children: list[tuple[CitryRender, str]] = []
        frame = _build_frame(render, children, placeholder_map, placeholder_nonce, artifact)

        # A render only gets its component's marker when it is that component's
        # root render; a transparent component's output (is_component_root
        # False, e.g. <c-provide>) stays unmarked even when serialized directly.
        # Extensions add per-instance markers (e.g. the CSS-variables hash)
        # under the well-known extra key on the component's own context.
        if render_frame.render_id is not None and render_frame.is_component_root:
            graph = render.context.ownership
            client_active = (
                artifact is not None and graph is not None and artifact.is_client_active(graph, render_frame.render_id)
            )
            extension_markers = list(render_frame.root_markers)
            if component is not None:
                extension_markers.extend(render.context._get_root_markers())
            extension_markers = list(dict.fromkeys(extension_markers))
            fixed_id_marker = f'data-cid="{render_frame.render_id}"'
            own_markers = [
                f"data-cid-{render_frame.render_id}",
                *(["data-citry-root"] if client_active else []),
                *([fixed_id_marker] if client_active and fixed_id_marker not in extension_markers else []),
                *extension_markers,
            ]
        else:
            own_markers = []
        # A marker written as a full `name="value"` attribute cannot ride the
        # marking scan (which splices bare `name=""` attributes), so split the
        # valued ones out; they are spliced right after the scan below. Own
        # valued markers come before inherited ones, so the list reads
        # innermost component first.
        root_markers = list(dict.fromkeys([*[marker for marker in own_markers if "=" not in marker], *inherited]))
        valued_markers = [marker for marker in own_markers if "=" in marker] + inherited_valued
        if frame and (root_markers or children):
            segments, placeholders = mark_html(frame, root_markers, _RENDER_ID_ATTR)
        else:
            # Nothing to mark and no placeholders to find (a render with no
            # component and no children, e.g. a manually built CitryRender),
            # or an empty frame: the frame is a single segment as-is.
            segments, placeholders = [frame], []
        if valued_markers and root_markers:
            segments, placeholders = _apply_valued_markers(segments, placeholders, root_markers, valued_markers)

        if artifact is not None and render_frame.render_id is not None:
            graph = render.context.ownership
            if graph is None:
                msg = f"Component frame {render_frame.class_name!r} has no ownership graph at serialization."
                raise RuntimeError(msg)
            instance_in_manifest = render_frame.is_component_root or artifact.is_transparent_instance(
                graph, render_frame.render_id
            )
            if instance_in_manifest:
                segments[0] = artifact.instance_cap(graph, render_frame.render_id, "s") + segments[0]
                segments[-1] += artifact.instance_cap(graph, render_frame.render_id, "e")

        if key in frame_by_key:
            msg = (
                "The same rendered component id was encountered more than once during serialization; "
                "render a fresh occurrence for each physical position."
            )
            raise RuntimeError(msg)
        frame_by_key[key] = (segments, placeholders)
        order.append(key)
        added_by_child = {child_id: added for child_id, _, added in placeholders}
        for child_render, child_id in children:
            added = added_by_child.get(child_id, [])
            # Valued markers reach a child exactly when the plain markers did:
            # the child's placeholder sat at this component's root.
            stack.append((child_render, added, valued_markers if added else [], child_id))
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

    # A Placeholder is an optional serialize-time insertion point. Extensions
    # replace the exact placeholder text they own; anything left after every
    # hook has run has no value to supply and therefore serializes empty. Keep
    # this in core so the contract also holds for component-less roots and for
    # renders embedded from a different Citry instance whose root does not
    # install the producing extension.
    for placeholder_html in placeholder_map.values():
        html = html.replace(placeholder_html, "")
    if artifact is not None:
        artifact.assert_unchanged()

    return html


def _apply_valued_markers(
    segments: list[str],
    placeholders: list[tuple[str, str, list[str]]],
    plain_markers: list[str],
    valued_markers: list[str],
) -> tuple[list[str], list[tuple[str, str, list[str]]]]:
    """
    Splice ``name="value"`` root markers next to the plain ones.

    ``mark_html`` splices the plain markers onto every root-level tag as one
    contiguous run of ``name=""`` attributes, and cannot emit an attribute
    with a value. So the valued markers are added here instead: the exact
    text of that run is known (it contains the component's per-render
    ``data-cid-<id>`` marker, so it appears nowhere else), and the valued
    attributes are inserted right after each occurrence.

    Markers with the same name merge into one attribute whose values are
    space-separated. ``valued_markers`` arrives innermost component first
    (own markers before inherited ones), and the merged value is written
    outermost first, so the innermost component's value is last. This follows
    the same innermost-last convention that ``events.md`` section 5.5 pins
    for the separate ``data-cid`` instance-id list; the client does not use
    ``data-citry-key`` to resolve instance roots.
    """
    by_name: dict[str, list[str]] = {}
    for marker in valued_markers:
        if not _VALUED_MARKER_RE.match(marker):
            msg = (
                f"Invalid valued root marker {marker!r}: expected the form"
                f' name="value", with no quotes or angle brackets in the value.'
            )
            raise ValueError(msg)
        name, _, quoted = marker.partition("=")
        by_name.setdefault(name, []).append(quoted[1:-1])
    addition = "".join(f' {name}="{" ".join(reversed(values))}"' for name, values in by_name.items())
    splice = "".join(f' {marker}=""' for marker in plain_markers)
    new_segments = [segment.replace(splice, splice + addition) for segment in segments]
    new_placeholders = [
        (child_id, placeholder_html.replace(splice, splice + addition), added)
        for child_id, placeholder_html, added in placeholders
    ]
    return new_segments, new_placeholders


def _build_frame(
    render: CitryRender,
    children: list[tuple[CitryRender, str]],
    placeholder_map: dict[str, str],
    placeholder_nonce: str,
    artifact: OwnershipManifestArtifact | None,
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
            elif isinstance(part, (PhysicalRegionPart, PhysicalRegionRender)):
                region_artifact = (
                    artifact if artifact is not None and artifact.has_region(part.graph, part.region_id) else None
                )
                if region_artifact is not None:
                    out.append(region_artifact.region_cap(part.graph, part.region_id, "s"))
                walk([part.part])
                if region_artifact is not None:
                    out.append(region_artifact.region_cap(part.graph, part.region_id, "e"))
            elif isinstance(part, CitryRender):
                part_frame = part.frame
                if (
                    part_frame.is_component_root
                    and part_frame.render_id is not None
                    and part_frame.render_id != render.frame.render_id
                ):
                    # Another component's whole output: leave a placeholder for pass 2.
                    out.append(f'<template c-render-id="{part_frame.render_id}"></template>')
                    children.append((part, part_frame.render_id))
                else:
                    # Interior content (control flow, nested template, slot-fill
                    # content) or a component-less render: join in directly.
                    graph = part.context.ownership
                    render_id = part_frame.render_id
                    if (
                        artifact is not None
                        and graph is not None
                        and render_id is not None
                        and artifact.is_transparent_instance(graph, render_id)
                    ):
                        out.append(artifact.instance_cap(graph, render_id, "s"))
                        walk(part.parts)
                        out.append(artifact.instance_cap(graph, render_id, "e"))
                    else:
                        walk(part.parts)
            elif isinstance(part, Placeholder):
                # The counter makes each occurrence's id (and so its text)
                # unique, so the hook can address occurrences individually.
                placeholder_id = f"{part.key}:{len(placeholder_map) + 1}:{placeholder_nonce}"
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
