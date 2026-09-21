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
from dataclasses import dataclass, field
from secrets import token_hex
from typing import TYPE_CHECKING, get_args

from citry._csp_validation import _CspRenderValidator
from citry._javascript_policy import _JavascriptPolicy
from citry._serialization_security import _ScriptSecurityMaterializer
from citry.attrs import format_attrs
from citry.citry_render import (
    CitryRender,
    DepsPosition,
    DepsStrategy,
    Placeholder,
    RenderDecoration,
    SerializedRender,
    SerializedSecurity,
)
from citry.settings import (
    SecurityCspMode,
    SecurityJavascriptMode,
    SecurityScriptIntegrityMode,
    _validate_security_csp,
    _validate_security_javascript,
    _validate_security_script_integrity,
)
from citry.util.html import escape_to_str
from citry_core.html_transform import mark_html

if TYPE_CHECKING:
    from collections.abc import Iterator

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
_CSP_NONCE_RE = re.compile(r"^[A-Za-z0-9+/_-]+={0,2}$")
_DOCUMENT_ROOT_RE = re.compile(
    r"\A\s*(?:\ufeff\s*)?(?:(?:<!--.*?-->)\s*)*(?:<!doctype\s+html(?:\s[^>]*)?>|<html(?:\s|>))",
    flags=re.IGNORECASE | re.DOTALL,
)


def _looks_like_document(html: str) -> bool:
    return _DOCUMENT_ROOT_RE.match(html) is not None


def _serialize_decoration_edge(parts: tuple[object, ...]) -> str:
    from citry._vue.capture import (  # noqa: PLC0415
        PreparedElementClose,
        PreparedElementOpen,
        PreparedTextValue,
        format_prepared_element_attrs,
    )

    output: list[str] = []
    for part in parts:
        if type(part) is PreparedTextValue:
            output.append(escape_to_str(part.value))
        elif type(part) is PreparedElementOpen:
            attrs = list(format_prepared_element_attrs(part))
            suffix = "" if not attrs else " " + " ".join(attrs)
            output.append(f"<{part.tag}{suffix}>")
        elif type(part) is PreparedElementClose:
            output.append(f"</{part.tag}>")
        else:
            raise TypeError(f"unsupported render decoration edge part: {type(part).__name__}")
    return "".join(output)


def _can_defer_vue_body_children(
    render: CitryRender,
    *,
    deps_strategy: DepsStrategy,
    deps_position: DepsPosition,
    security_csp: SecurityCspMode,
    security_javascript: SecurityJavascriptMode,
    security_script_integrity: SecurityScriptIntegrityMode,
    csp_nonce: str | None,
) -> bool:
    """Allow the existing Vue body shortcut only for a proven direct document."""
    if (
        deps_strategy != "document"
        or deps_position != "smart"
        or security_csp != "off"
        or security_javascript != "allow"
        or security_script_integrity != "off"
        or csp_nonce is not None
    ):
        return False
    component = render.context.component
    if component is None:
        return False
    from citry.ext.dependencies.extension import DependenciesExtension  # noqa: PLC0415

    hooks = component.citry.extensions._extensions_with_hook("on_serialize")
    if any(
        type(hook) is not DependenciesExtension
        or getattr(hook.on_serialize, "__func__", None) is not DependenciesExtension.on_serialize
        or getattr(hook._on_serialize_internal, "__func__", None) is not DependenciesExtension._on_serialize_internal
        for hook in hooks
    ):
        return False

    from citry._vue.capture import (  # noqa: PLC0415
        PreparedElementClose,
        PreparedElementOpen,
        PreparedSourceText,
        PreparedStaticRun,
        PreparedTextValue,
        PreparedTrustedHtmlValue,
        PreparedVerbatimHtml,
    )
    from citry._vue.leaf_program import PreparedLeafProgram  # noqa: PLC0415

    inert_parts = (PreparedSourceText, PreparedStaticRun, PreparedTextValue, PreparedVerbatimHtml)
    document_shell = any(
        isinstance(part, PreparedElementOpen) and part.tag.lower() in {"html", "head", "body"} for part in render.parts
    )

    body_depth = 0
    body_count = 0
    shell_state = "before-html"
    for part in render.parts:
        if isinstance(part, PreparedElementOpen):
            tag = part.tag.lower()
            if (
                document_shell
                and not body_depth
                and part.tag.lower() != "body"
                and any(attr.name.startswith(("@c-", ":c-", "v-", "@", ":", "#")) for attr in part.attrs)
            ):
                raise ValueError("Interactive Vue bindings are unsupported in the physical document head.")
            if tag == "html":
                if shell_state != "before-html":
                    return False
                shell_state = "in-html"
            elif tag == "head":
                if shell_state != "in-html":
                    return False
                shell_state = "in-head"
            elif tag == "body":
                if shell_state not in {"in-html", "after-head"}:
                    return False
                body_count += 1
                body_depth += 1
                shell_state = "in-body"
        elif isinstance(part, PreparedElementClose):
            tag = part.tag.lower()
            if tag == "head":
                if shell_state != "in-head":
                    return False
                shell_state = "after-head"
            elif tag == "body":
                if shell_state != "in-body":
                    return False
                body_depth -= 1
                if body_depth < 0:
                    return False
                shell_state = "after-body"
            elif tag == "html":
                if shell_state != "after-body":
                    return False
                shell_state = "after-html"
        elif isinstance(part, CitryRender):
            if body_depth != 1:
                return False
        elif isinstance(part, PreparedLeafProgram):
            if body_depth != 1 or not part.fragment.safe_body or part.vue_errors:
                return False
        elif isinstance(part, (Placeholder, PreparedTrustedHtmlValue)) or not isinstance(part, inert_parts):
            return False
    if body_count != 1 or body_depth or shell_state != "after-html":
        return False

    pending = [part for part in render.parts if isinstance(part, CitryRender)]
    while pending:
        child = pending.pop()
        markers = (*child.frame.root_markers, *child.context._get_root_markers())
        if any(not marker.startswith(('data-cid="', "data-citry")) for marker in markers):
            return False
        for part in child.parts:
            if isinstance(part, CitryRender):
                pending.append(part)
            elif isinstance(part, PreparedLeafProgram):
                if not part.fragment.safe_body or part.vue_errors:
                    return False
            elif (
                isinstance(part, (Placeholder, PreparedTrustedHtmlValue))
                or (
                    isinstance(part, (PreparedElementOpen, PreparedElementClose))
                    and part.tag.lower() in {"html", "head", "body"}
                )
                or not isinstance(part, (PreparedElementOpen, PreparedElementClose, *inert_parts))
            ):
                return False
    return True


# One scanned frame: the HTML split around child placeholders (always one more
# segment than placeholders), and per placeholder its id, its own text (with
# any spliced markers), and the markers it received.
_Frame = tuple[list[str], list[tuple[str, str, list[str]]]]


@dataclass(slots=True)
class _SerializationSession:
    """Mutable, call-local state that freezes into public security metadata."""

    security_csp: SecurityCspMode
    security_javascript: SecurityJavascriptMode
    security_script_integrity: SecurityScriptIntegrityMode
    csp_nonce: str | None
    _script_security: _ScriptSecurityMaterializer | None = field(init=False, default=None)
    _javascript_policy: _JavascriptPolicy | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        if self.security_javascript != "allow":
            self._javascript_policy = _JavascriptPolicy(self.security_javascript)
        if (
            self.security_script_integrity == "citry"
            or self.csp_nonce is not None
            or self.security_csp != "off"
            or self.security_javascript != "allow"
        ):
            materializer_csp = self.security_csp
            if (
                materializer_csp == "off"
                and self.security_javascript != "allow"
                and self.security_script_integrity == "off"
                and self.csp_nonce is None
            ):
                materializer_csp = "warn"
            self._script_security = _ScriptSecurityMaterializer(
                collect_integrity=self.security_script_integrity == "citry",
                csp_nonce=self.csp_nonce,
                csp_mode=materializer_csp,
            )

    @classmethod
    def for_render(
        cls,
        root: CitryRender,
        *,
        csp_nonce: str | None,
        security_csp: SecurityCspMode | None,
        security_javascript: SecurityJavascriptMode | None,
        security_script_integrity: SecurityScriptIntegrityMode | None,
    ) -> _SerializationSession:
        component = root.context.component
        settings = component.citry.settings if component is not None else None
        effective_csp = settings.security_csp if settings is not None else "off"
        effective_javascript = settings.security_javascript if settings is not None else "allow"
        effective_integrity = settings.security_script_integrity if settings is not None else "off"

        if security_csp is not None:
            effective_csp = _validate_security_csp(security_csp)
        if security_javascript is not None:
            effective_javascript = _validate_security_javascript(security_javascript)
        if security_script_integrity is not None:
            effective_integrity = _validate_security_script_integrity(security_script_integrity)
        effective_nonce = _validate_csp_nonce(csp_nonce)

        return cls(
            security_csp=effective_csp,
            security_javascript=effective_javascript,
            security_script_integrity=effective_integrity,
            csp_nonce=effective_nonce,
        )

    def freeze(self) -> SerializedSecurity:
        """Return an immutable, document-order snapshot for the caller."""
        if self._script_security is None:
            return SerializedSecurity()
        return SerializedSecurity(
            scripts=self._script_security.scripts,
            csp_script_hashes=self._script_security.csp_script_hashes,
        )

    def require_implemented_modes(self) -> None:
        """Retained as the phase boundary hook; every public mode is implemented."""


def serialize_render(
    root: CitryRender,
    *,
    deps_strategy: DepsStrategy = "document",
    deps_position: DepsPosition = "smart",
    csp_nonce: str | None = None,
    security_csp: SecurityCspMode | None = None,
    security_javascript: SecurityJavascriptMode | None = None,
    security_script_integrity: SecurityScriptIntegrityMode | None = None,
) -> str:
    """Compatibility wrapper returning only the serialized HTML string."""
    return serialize_render_result(
        root,
        deps_strategy=deps_strategy,
        deps_position=deps_position,
        csp_nonce=csp_nonce,
        security_csp=security_csp,
        security_javascript=security_javascript,
        security_script_integrity=security_script_integrity,
    ).html


def serialize_render_result(
    root: CitryRender,
    *,
    deps_strategy: DepsStrategy = "document",
    deps_position: DepsPosition = "smart",
    csp_nonce: str | None = None,
    security_csp: SecurityCspMode | None = None,
    security_javascript: SecurityJavascriptMode | None = None,
    security_script_integrity: SecurityScriptIntegrityMode | None = None,
) -> SerializedRender:
    """Serialize a render tree and return its HTML and security metadata."""
    if deps_strategy not in _DEPS_STRATEGIES:
        msg = f"Invalid deps_strategy {deps_strategy!r}; must be one of {_DEPS_STRATEGIES}"
        raise ValueError(msg)
    if deps_position not in _DEPS_POSITIONS:
        msg = f"Invalid deps_position {deps_position!r}; must be one of {_DEPS_POSITIONS}"
        raise ValueError(msg)
    session = _SerializationSession.for_render(
        root,
        csp_nonce=csp_nonce,
        security_csp=security_csp,
        security_javascript=security_javascript,
        security_script_integrity=security_script_integrity,
    )
    session.require_implemented_modes()
    csp_validator = None if session.security_csp == "off" else _CspRenderValidator(session.security_csp)
    javascript_policy = session._javascript_policy
    if javascript_policy is not None:
        javascript_policy.inspect_reached_bindings(root)
    if csp_validator is not None:
        csp_validator.validate_reached_bindings(root)
    from citry._vue.serialization import analyze_vue_serialization  # noqa: PLC0415

    vue_analysis = analyze_vue_serialization(root)
    if javascript_policy is not None:
        javascript_policy.inspect_selected_requirements(vue_analysis.active_policy_requirements)

    vue_required = (
        session.security_javascript not in {"omit", "forbid"}
        and root.render_target == "prepared"
        and bool(vue_analysis.runtime_requirements)
    )
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
    decorations: dict[str, RenderDecoration] = {}
    order: list[str] = []
    component_classes: dict[str, str] = {}
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
    omit_handler_marker = f"data-citry-omit-handler-{token_hex(16)}" if session.security_javascript == "omit" else None

    # Each stack item is (render, plain markers inherited from the parent,
    # valued markers inherited from the parent, key). Valued markers are the
    # `name="value"` form, threaded separately because mark_html cannot splice
    # them (see _apply_valued_markers).
    stack: list[tuple[CitryRender, list[str], list[str], str]] = [(root, [], [], root_key)]
    while stack:
        render, inherited, inherited_valued, key = stack.pop()
        component = render.context.component
        render_frame = render.frame
        if render_frame.render_id is not None:
            component_classes[render_frame.render_id] = render_frame.class_name or render_frame.class_id or "component"

        children: list[tuple[CitryRender, str]] = []
        frame = _build_frame(render, children, placeholder_map, placeholder_nonce, omit_handler_marker)

        # A render only gets its component's marker when it is that component's
        # root render; a transparent component's output (is_component_root
        # False, e.g. <c-provide>) stays unmarked even when serialized directly.
        # Extensions add per-instance markers (e.g. the CSS-variables hash)
        # under the well-known extra key on the component's own context.
        if render_frame.render_id is not None and render_frame.is_component_root:
            extension_markers = list(render_frame.root_markers)
            if component is not None:
                extension_markers.extend(render.context._get_root_markers())
            if session.security_javascript in {"omit", "forbid"}:
                extension_markers = [
                    marker
                    for marker in extension_markers
                    if not marker.startswith('data-cid="') and not marker.startswith("data-citry")
                ]
            extension_markers = list(dict.fromkeys(extension_markers))
            own_markers = [
                f"data-cid-{render_frame.render_id}",
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

        if key in frame_by_key:
            msg = (
                "The same rendered component id was encountered more than once during serialization; "
                "render a fresh occurrence for each physical position."
            )
            raise RuntimeError(msg)
        frame_by_key[key] = (segments, placeholders)
        if isinstance(render, RenderDecoration):
            decorations[key] = render
        order.append(key)
        added_by_child = {child_id: added for child_id, _, added in placeholders}
        defer_body_children = (
            vue_required
            and key == root_key
            and _can_defer_vue_body_children(
                render,
                deps_strategy=deps_strategy,
                deps_position=deps_position,
                security_csp=session.security_csp,
                security_javascript=session.security_javascript,
                security_script_integrity=session.security_script_integrity,
                csp_nonce=session.csp_nonce,
            )
        )
        for child_render, child_id in () if defer_body_children else children:
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
        body = "".join(parts)
        decoration = decorations.get(key)
        if decoration is not None and not (decoration.omit_around_document and _looks_like_document(body)):
            body = (
                _serialize_decoration_edge(decoration.opening) + body + _serialize_decoration_edge(decoration.closing)
            )
        finished[key] = body

    html = finished[root_key]

    if javascript_policy is not None:
        javascript_policy.validate_pre_extension_html(html, component_classes=component_classes)
    if csp_validator is not None:
        csp_validator.validate_pre_extension_html(html, component_classes=component_classes)

    # The serialize hook: extensions do whole-page work here, e.g. the
    # dependencies extension places the collected JS/CSS (filling the
    # placeholder texts and the default head/body locations). A render with
    # no component has no Citry instance to reach extensions through, and
    # nothing was collected for it either.
    root_component = root.context.component
    vue_plan = None
    if root_component is not None:
        from citry._vue.serialization import prepare_vue_serialization  # noqa: PLC0415
        from citry.extension import OnSerializeContext  # noqa: PLC0415

        vue_plan = prepare_vue_serialization(
            OnSerializeContext(
                citry=root_component.citry,
                context=root.context,
                selected_render=root,
                html=html,
                placeholders=placeholder_map,
                deps_strategy=deps_strategy,
                deps_position=deps_position,
            ),
            session._script_security,
            session.security_csp,
            javascript_policy,
            session.security_javascript,
            vue_analysis,
        )
        html = root_component.citry.extensions.on_serialize(
            context=root.context,
            selected_render=root,
            html=vue_plan.shell_html if vue_plan is not None else html,
            placeholders=placeholder_map,
            deps_strategy=deps_strategy,
            deps_position=deps_position,
            _script_security=session._script_security,
            _security_csp=session.security_csp,
            _javascript_policy=javascript_policy,
            _security_javascript=session.security_javascript,
        )
        if vue_plan is not None:
            html = vue_plan.finalize(html)

    # A Placeholder is an optional serialize-time insertion point. Extensions
    # replace the exact placeholder text they own; anything left after every
    # hook has run has no value to supply and therefore serializes empty. Keep
    # this in core so the contract also holds for component-less roots and for
    # renders embedded from a different Citry instance whose root does not
    # install the producing extension.
    for placeholder_html in placeholder_map.values():
        html = html.replace(placeholder_html, "")
    if javascript_policy is not None:
        html = javascript_policy.validate_settled_html(
            html,
            marker_prefix=session._script_security.marker_prefix if session._script_security is not None else "",
            trusted_tag_starts=(
                session._script_security.trusted_tag_starts(html)
                if session._script_security is not None
                else frozenset()
            ),
            component_classes=component_classes,
            omit_handler_marker=omit_handler_marker,
        )
        javascript_policy.report()
    if session._script_security is not None:
        session._script_security.require_strict_nonce(deps_strategy=deps_strategy)
    if csp_validator is not None:
        if session._script_security is not None:
            csp_validator.add_dependency_findings(session._script_security.csp_findings)
        csp_validator.validate_settled_html(
            html,
            marker_prefix=session._script_security.marker_prefix if session._script_security is not None else "",
            trusted_tag_starts=(
                session._script_security.trusted_tag_starts(html)
                if session._script_security is not None
                else frozenset()
            ),
            component_classes=component_classes,
        )
        csp_validator.report()
    if session._script_security is not None:
        html = session._script_security.finalize(html)

    return SerializedRender(html=html, security=session.freeze())


def _validate_csp_nonce(value: str | None) -> str | None:
    """Validate the CSP Level 3 base64-value syntax used by nonce sources."""
    if value is None:
        return None
    if type(value) is not str or _CSP_NONCE_RE.fullmatch(value) is None:
        raise ValueError(
            "Invalid csp_nonce: expected a non-empty CSP base64 value using letters, digits, '+', '/', '-', '_', "
            "and at most two trailing '=' characters."
        )
    return value


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


def _append_frame_parts(
    parts: list[RenderPart],
    *,
    render: CitryRender,
    children: list[tuple[CitryRender, str]],
    placeholder_map: dict[str, str],
    placeholder_nonce: str,
    omit_handler_marker: str | None,
    out: list[str],
) -> None:
    """Append nested content iteratively while preserving child order."""
    stack: list[Iterator[RenderPart]] = [iter(parts)]
    while stack:
        try:
            part = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue
        if isinstance(part, str):
            out.append(part)
        elif isinstance(part, RenderDecoration):
            part_frame = part.frame
            decoration_id = (
                part_frame.render_id
                if part_frame.is_component_root
                and part_frame.render_id is not None
                and part_frame.render_id != render.frame.render_id
                else f"decoration:{id(part)}:{len(children)}"
            )
            out.append(f'<template c-render-id="{decoration_id}"></template>')
            children.append((part, decoration_id))
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
                # Interior content joins this frame and may be nested beyond
                # Python's recursion limit.
                stack.append(iter(part.parts))
        elif isinstance(part, Placeholder):
            # Each occurrence needs its own identity for serialization hooks.
            placeholder_id = f"{part.key}:{len(placeholder_map) + 1}:{placeholder_nonce}"
            text = f'<template c-render-id="{placeholder_id}"></template>'
            placeholder_map[placeholder_id] = text
            out.append(text)
        else:
            from citry._vue.capture import (  # noqa: PLC0415
                PreparedDynamicElementClose,
                PreparedDynamicElementOpen,
                PreparedElementClose,
                PreparedElementOpen,
                PreparedSourceText,
                PreparedStaticRun,
                PreparedTextValue,
                PreparedTrustedHtmlValue,
                PreparedVerbatimHtml,
            )
            from citry._vue.leaf_program import (  # noqa: PLC0415
                PreparedLeafProgram,
                static_leaf_parts,
                typed_leaf_parts,
            )

            if isinstance(part, PreparedLeafProgram):
                stack.append(
                    iter(typed_leaf_parts(part) if omit_handler_marker is not None else static_leaf_parts(part))
                )
                continue

            if isinstance(part, PreparedDynamicElementOpen):
                formatted = str(format_attrs(part.attrs))
                suffix = f" {formatted}" if formatted else ""
                out.append(f"<{part.tag}{suffix}>")
                continue
            if isinstance(part, PreparedDynamicElementClose):
                out.append(f"</{part.tag}>")
                continue

            if isinstance(part, PreparedSourceText):
                out.append(part.text)
                continue
            if isinstance(part, PreparedStaticRun):
                out.append(part.html)
                continue
            if isinstance(part, PreparedTextValue):
                out.append(escape_to_str(part.value))
                continue
            if isinstance(part, PreparedTrustedHtmlValue):
                out.append(part.html)
                continue
            if isinstance(part, PreparedVerbatimHtml):
                out.append(part.html)
                continue
            if isinstance(part, PreparedElementOpen):
                from citry._vue.capture import format_prepared_element_attrs  # noqa: PLC0415

                rendered_attrs = list(format_prepared_element_attrs(part))
                if omit_handler_marker is not None and (
                    part.event_bindings
                    or part.poll_bindings
                    or part.runtime_event_bindings
                    or part.runtime_poll_bindings
                ):
                    rendered_attrs.append(omit_handler_marker)
                suffix = "" if not rendered_attrs else " " + " ".join(rendered_attrs)
                # The prepared compiler emits an explicit close part for
                # non-void self-closing syntax (including SVG). Only authored
                # void ``<img/>``-style tags keep the slash here.
                ending = "/>" if part.is_void and part.is_self_closing else ">"
                out.append(f"<{part.tag}{suffix}{ending}")
                continue
            if isinstance(part, PreparedElementClose):
                out.append(f"</{part.tag}>")
                continue
            # A DeferredComponent here means render() never resolved it.
            msg = "unresolved DeferredComponent at serialize(); render() must process the queue first"
            raise RuntimeError(msg)


def _build_frame(
    render: CitryRender,
    children: list[tuple[CitryRender, str]],
    placeholder_map: dict[str, str],
    placeholder_nonce: str,
    omit_handler_marker: str | None,
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
    *wrote* the fill, but renders as part of this frame). The explicit
    stack also handles deeply nested interior content.
    """
    out: list[str] = []
    _append_frame_parts(
        render.parts,
        render=render,
        children=children,
        placeholder_map=placeholder_map,
        placeholder_nonce=placeholder_nonce,
        omit_handler_marker=omit_handler_marker,
        out=out,
    )
    return "".join(out)
