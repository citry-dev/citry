"""
CitryRender - the output of rendering a CitryElement.

The rendering pipeline has three phases, each with its own struct (see
docs/design/component_rendering.md):

    Component(**kwargs)       -> CitryElement   compose: "what to render"
    CitryElement.render()     -> CitryRender    render: parts + collected metadata
    CitryRender.serialize()   -> str (HTML)     serialize: join + place deps

``CitryRender`` is the middle struct, and on purpose it is NOT a string. Keeping
the render output as an object lets an already-rendered piece be composed into
a larger render. You can pass a ``CitryRender`` to another component (as a
kwarg, inside ``{{ ... }}``, or in an attribute); the component that receives
it pulls in its HTML and copies up its collected data (JS/CSS dependencies).
Turning it into a string
(``str()``/``serialize()``) is the final step that produces the HTML. This is the
structured render pipeline motivated by django-components #1650.

A live ``CitryRender`` represents one render occurrence. Repeated serialization
preserves its component IDs and render-scoped context, so it is not a
cross-request output-cache value. The output-cache design uses a detached,
validated replay artifact (docs/design/caching.md).

A ``CitryRender`` holds:

- ``parts``: an ordered list whose items can be different types. Each part is a
  ``str`` (static or already-rendered text) or a nested ``CitryRender`` (a piece
  not yet joined into text). Joining only at the end keeps reuse cheap and keeps
  the dependencies readable until the final serialize.
- ``context``: the ``CitryContext`` used during the render. For now the whole
  context is kept (the collected data lives in its ``extra``); this can be
  narrowed to specific fields once we know what serialize needs.

Serialization joins the parts, adds static or prepared-runtime ownership
metadata as needed, and places collected dependencies into the page per the
``deps_strategy`` / ``deps_position`` arguments
(docs/design/dependencies.md section 7), including the ``fragment`` strategy
for HTML partials.

Example:
    Render and serialize a component::

        from citry import Component

        class Hello(Component):
            template = "<p>Hello!</p>"

        rendered = Hello().render()      # -> CitryRender
        html = rendered.serialize()      # -> "<p>Hello!</p>"
        assert str(rendered) == html     # str() is a convenience for serialize()

"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from html import unescape
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, cast, final

from citry.citry_element import _DEFAULT_CITRY_ELEMENT, CitryElement
from citry.component_like import _DEFAULT_COMPONENT_LIKE, ComponentLike, _resolve_component_like
from citry.constness import const_value
from citry.slots import Slot
from citry.util.html import escape

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

    from citry._vue.capture import (
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
    from citry._vue.direct import DirectExecutionFrame
    from citry._vue.leaf_program import PreparedLeafProgram
    from citry.citry import Citry
    from citry.citry_context import CitryContext
    from citry.citry_element import _PreparedCallMetadata
    from citry.client_directives import ComponentTagClientBindingKind
    from citry.component import Component
    from citry.settings import SecurityCspMode, SecurityJavascriptMode, SecurityScriptIntegrityMode

_VALUE_CONTEXT: ContextVar[CitryContext | None] = ContextVar("citry_value_context", default=None)

# A component's after-render hooks (its `on_render` generator and the
# extensions' `on_component_rendered`) may serialize the component's own live
# result and return that HTML as its new output. The returned HTML becomes the
# component's root output again, and the final serialization marks its root
# tags then. So while those hooks run, serializing that same render must leave
# the component's own root markers off, or the page would carry each marker
# twice on one tag (and on tags that are not roots of the returned HTML, when
# the hook wraps the result). This holds the render id of the component whose hooks run.
_AFTER_RENDER_HOOKS_RENDER_ID: ContextVar[str | None] = ContextVar(
    "citry_after_render_hooks_render_id",
    default=None,
)


@contextmanager
def _after_render_hooks_scope(render_id: str | None) -> Iterator[None]:
    """Mark `render_id` as the component whose after-render hooks are running."""
    # The token restores the outer value, so a hook that renders another
    # component (with hooks of its own) gets its scope back afterwards.
    token = _AFTER_RENDER_HOOKS_RENDER_ID.set(render_id)
    try:
        yield
    finally:
        _AFTER_RENDER_HOOKS_RENDER_ID.reset(token)


# One piece of rendered output. It is one of:
#   - str: final text.
#   - CitryRender: a nested render not yet joined into text.
#   - DeferredComponent: a child component not yet rendered (render() renders it
#     before any serialize()).
#   - Placeholder: a spot whose final text an extension supplies at serialize
#     time (the <c-js>/<c-css> built-ins render these).
#   - Typed prepared records: source, text, elements, and leaf programs kept
#     structured for native Vue assembly.
# A CitryRender's `parts`, and what a node's render() returns, are made of these.
PreparedRenderPart: TypeAlias = (
    "PreparedSourceText | PreparedVerbatimHtml | PreparedTextValue | PreparedTrustedHtmlValue | "
    "PreparedElementOpen | PreparedElementClose | PreparedDynamicElementOpen | PreparedDynamicElementClose | "
    "PreparedStaticRun | PreparedLeafProgram"
)
RenderPart: TypeAlias = "str | CitryRender | DeferredComponent | Placeholder | PreparedRenderPart | SimpleVueRecord"

# How collected JS/CSS dependencies are handled when serializing (see
# CitryRender.serialize and docs/design/dependencies.md section 7.1).
DepsStrategy: TypeAlias = Literal["document", "simple", "fragment", "ignore"]

# Where the dependency tags go for the "document"/"simple" strategies.
DepsPosition: TypeAlias = Literal["smart", "prepend", "append"]


@dataclass(frozen=True, slots=True)
class SerializedScriptSecurity:
    """
    Security metadata for one structured script in serialized output.

    ``digests`` uses the unquoted SRI form, such as ``"sha384-..."``.
    ``provenance`` states whether Citry computed or verified those bytes.
    ``origin_class_id`` identifies the component class when one owns the tag.
    """

    location: Literal["inline", "external"]
    url: str | None
    digests: tuple[str, ...]
    provenance: Literal["citry-computed", "declared-verified", "declared-unverified"]
    origin_class_id: str | None


@dataclass(frozen=True, slots=True)
class SerializedSecurity:
    """
    Security contributions produced by one serialization call.

    ``csp_script_hashes`` is the deduplicated document-order tuple of quoted
    hash sources that a host can add to ``script-src``. It and ``scripts`` are
    empty when digest-producing security features are disabled.
    """

    scripts: tuple[SerializedScriptSecurity, ...] = ()
    csp_script_hashes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SerializedRender:
    """Final HTML plus host-facing security metadata for those exact bytes."""

    html: str
    security: SerializedSecurity


# What ``Component.on_render`` may return to replace the component's whole
# output (docs/design/component_on_render.md section 3): text (a plain ``str``,
# escaped like a ``{{ ... }}`` value), trusted HTML (``Markup``, which is a
# ``str`` subclass, inserted as-is), a composed element (rendered in the
# component's place), an already-rendered subtree, a ``Slot`` (invoked with no
# data), or a ``ComponentLike`` value (resolved against the Citry instance
# rendering it). Any other object with ``__html__`` is accepted as trusted HTML
# too, the same as in ``{{ ... }}``, though the type alias has no way to
# express it.
# ``None`` is not part of the alias: returning ``None`` means "no
# replacement, render the template as usual".
RenderReplacement: TypeAlias = "str | CitryElement | CitryRender | Slot | ComponentLike"

# The shape of ``Component.on_render`` when it contains a ``yield`` (the
# generator form, docs/design/component_on_render.md section 3.2). The generator yields
# a replacement (or ``None`` for "render my template as usual"), receives
# back ``(result, error)`` once that content has fully settled (children
# included), and may end with ``return <replacement>`` to set the final
# output. Exactly one of ``result`` / ``error`` is set.
OnRenderGenerator: TypeAlias = (
    "Generator[RenderReplacement | None, tuple[CitryRender | None, Exception | None], RenderReplacement | None]"
)


@dataclass(frozen=True, slots=True)
class PreparedOccurrenceMetadata:
    """Immutable prepared-call facts retained after the live component is gone."""

    call: _PreparedCallMetadata | None
    raw_slots_present: bool
    component_tag_client_bindings: tuple[PreparedComponentBinding, ...]


# Final because the Vue assembler matches it by exact type.
@final
@dataclass(frozen=True, slots=True)
class SimpleVueRecord:
    """
    Carry one ``simple="vue"`` occurrence's identity and data without a Python component.

    The render loop puts this record where an ordinary child ``CitryRender``
    would go. Serialization reads the row's recorded template values
    (``leaf``) from it and gives the occurrence its own Vue instance, as it
    would for an ordinary component.
    """

    component_class: type[Component]
    class_id: str
    render_id: str
    call_metadata: _PreparedCallMetadata | None
    js_data: dict[str, object]
    leaf: PreparedLeafProgram
    prepared_data: dict[str, object]
    css_vars_hash: str | None = None
    root_markers: tuple[str, ...] = ()
    # True when a Python expression, public Slot call or render hook placed
    # this occurrence. Such a call has no parser record, so the Vue assembler
    # reads this flag, set only by `wrap_python_composition_result()`, to tell it
    # apart from an authored tag whose call record went missing.
    python_composition: bool = False


@dataclass(frozen=True, slots=True)
class PreparedComponentBinding:
    """Authenticated component-call binding detached from its parser node."""

    kind: ComponentTagClientBindingKind
    key: str
    value: str
    source: str
    span: tuple[int, int]
    authenticated: bool
    provenance: Literal["authored", "runtime-spread"] = "authored"


@dataclass(frozen=True, slots=True)
class RenderFrame:
    """Immutable identity needed to traverse and serialize one render frame."""

    render_id: str | None
    class_id: str | None
    class_name: str | None
    is_component_root: bool
    root_markers: tuple[str, ...]
    is_transparent_root: bool = False
    """True for a transparent component's whole output, excluding caller-owned interiors."""
    prepared_occurrence: PreparedOccurrenceMetadata | None = None

    @classmethod
    def from_context(
        cls, context: CitryContext, *, is_component_root: bool, is_transparent_root: bool = False
    ) -> RenderFrame:
        """Snapshot the identity-bearing portion of one live render context."""
        component = context.component
        if component is None:
            return cls(
                render_id=None,
                class_id=None,
                class_name=None,
                is_component_root=is_component_root,
                is_transparent_root=is_transparent_root,
                root_markers=tuple(context._get_root_markers()) if is_component_root else (),
                prepared_occurrence=None,
            )
        component_class = type(component)
        from citry.client_directives import (  # noqa: PLC0415
            ComponentTagClientBinding,
            ComponentTagClientBindingKind,
            RuntimeComponentEventBinding,
            is_authenticated_component_tag_client_binding,
            is_authenticated_runtime_component_event_binding,
        )

        prepared_bindings: list[PreparedComponentBinding] = []
        for binding in component._component_tag_client_bindings:
            if type(binding) is RuntimeComponentEventBinding:
                if type(binding.key) is not str or type(binding.value) is not str or type(binding.source) is not str:
                    raise TypeError("runtime component event key, handler, and source must be exact strings")
                prepared_bindings.append(
                    PreparedComponentBinding(
                        ComponentTagClientBindingKind.CITRY_HANDLER,
                        binding.key,
                        binding.value,
                        binding.source,
                        binding.span,
                        is_authenticated_runtime_component_event_binding(binding),
                        "runtime-spread",
                    )
                )
                continue
            if type(binding) is not ComponentTagClientBinding:
                raise TypeError("component-call binding metadata changed after resolution")
            if type(binding.source) is not str:
                raise TypeError("component-call binding source must be template text")
            prepared_bindings.append(
                PreparedComponentBinding(
                    binding.kind,
                    binding.key,
                    binding.value,
                    binding.source,
                    binding.span,
                    is_authenticated_component_tag_client_binding(binding),
                )
            )
        return cls(
            render_id=component.id,
            class_id=component._citry_class_id,
            class_name=component_class.__name__,
            is_component_root=is_component_root,
            is_transparent_root=is_transparent_root,
            root_markers=tuple(context._get_root_markers()) if is_component_root else (),
            prepared_occurrence=PreparedOccurrenceMetadata(
                call=component._prepared_call_metadata,
                raw_slots_present=bool(component.raw_slots),
                component_tag_client_bindings=tuple(prepared_bindings),
            ),
        )


class CitryRender:
    """
    The result of rendering a ``CitryElement`` (the render-phase output).

    Attributes:
        parts: Ordered list of ``str`` or nested ``CitryRender`` fragments.
        context: The ``CitryContext`` used to produce this render.
        is_component_root: True for a nontransparent component's whole output.
            Transparent whole outputs and interior renders (a ``<c-if>``/``<c-for>`` block, a
            nested template, slot-fill content rendered in the enclosing
            scope) are False. Serialization uses this to tell a completed
            child-component subtree (which becomes its own marked frame) from
            content that joins into the surrounding frame; the component on
            the context cannot tell these apart, because slot-fill content
            carries the context of the component that wrote it, not the one
            it renders inside.

    """

    __slots__ = ("__weakref__", "context", "frame", "owner_citry", "parts", "render_target")

    def __init__(
        self,
        parts: list[RenderPart],
        context: CitryContext,
        *,
        is_component_root: bool = False,
        frame: RenderFrame | None = None,
        is_transparent_root: bool = False,
        render_target: Literal["html", "prepared"] | None = None,
        owner_citry: Citry | None = None,
    ) -> None:
        self.parts = parts
        self.context = context
        context_citry = context.component.citry if context.component is not None else None
        if owner_citry is not None and context_citry is not None and owner_citry is not context_citry:
            raise ValueError("CitryRender owner must match its component context.")
        self.owner_citry = owner_citry if owner_citry is not None else context_citry
        self.frame = frame or RenderFrame.from_context(
            context, is_component_root=is_component_root, is_transparent_root=is_transparent_root
        )
        if render_target is None:
            from citry._vue.capture import direct_prepared_render_active  # noqa: PLC0415

            render_target = "prepared" if direct_prepared_render_active() else "html"
        self.render_target = render_target

    @property
    def is_component_root(self) -> bool:
        """Whether this render is the whole output frame of one component."""
        return self.frame.is_component_root

    def serialize(
        self,
        deps_strategy: DepsStrategy = "document",
        deps_position: DepsPosition = "smart",
        *,
        csp_nonce: str | None = None,
        security_csp: SecurityCspMode | None = None,
        security_javascript: SecurityJavascriptMode | None = None,
        security_script_integrity: SecurityScriptIntegrityMode | None = None,
        ssr: bool | None = None,
    ) -> str:
        """
        Turn this render into a final HTML string.

        In static output, each component's root element gets a
        ``data-cid-<id>`` attribute. When a rendered component needs Vue in
        the browser, Citry keeps the surrounding page markup, puts the
        rendered content (the page body, for a full document) in one element
        where Vue mounts, and adds the data and scripts Vue needs to mount
        it. Citry places the collected JS/CSS according to
        ``deps_strategy`` and ``deps_position``.

        With ``security_csp="warn"``, Citry reports content that would break
        under a Content Security Policy but leaves the output unchanged. With
        ``"strict"``, it uses the CSP-safe browser runtime and raises on
        incompatible content. With ``security_javascript="warn"``, it reports
        which components need JavaScript; ``"omit"`` drops Citry's scripts but
        keeps the HTML and CSS; ``"forbid"`` raises when a rendered component
        needs browser behavior.

        Args:
            deps_strategy: How to handle the collected JS/CSS.

                - ``"document"`` (default): emit the tags, plus Citry's
                  Vue browser runtime and the data it needs to mount the
                  page when a component needs per-instance browser
                  behavior, such as ``js_data()`` values on its Vue
                  instance or ``$component`` callbacks.
                - ``"simple"``: the tags only, no JavaScript runtime. For
                  static pages and emails; per-instance JS does not run
                  (CSS variables still work, they are pure CSS).
                - ``"fragment"``: HTML meant to be inserted into an
                  already-loaded page (an HTMX swap, ``fetch`` +
                  ``innerHTML``, ...). A fragment without browser behavior
                  carries its tags directly. An interactive fragment
                  carries a script that loads Citry's browser runtime if
                  the page does not have it yet, plus JSON that tells the
                  runtime which assets to load before it mounts the
                  fragment. A fragment that carries JS, CSS, or browser
                  behavior requires a mounted web integration.
                - ``"ignore"``: no tags inserted.
            deps_position: Where the tags go (``document``/``simple`` only).

                - ``"smart"`` (default): into the ``<c-js>``/``<c-css>``
                  placeholders when present, else CSS before the first
                  ``</head>`` and JS before the last ``</body>``, else
                  CSS is prepended and JS appended.
                - ``"prepend"`` / ``"append"``: all tags before/after the
                  whole output.
            csp_nonce: Raw request nonce to add to structured scripts and
                inline styles. The host owns nonce generation and the matching
                Content-Security-Policy response header.
            security_csp: Override this render's engine-level CSP policy.
            security_javascript: Override this render's engine-level
                JavaScript delivery policy.
            security_script_integrity: Override this render's engine-level
                script integrity policy.
            ssr: Override the engine's initial Vue HTML hydration setting.
                ``None`` uses the [`ssr`][citry.CitrySettings.ssr] setting.

        Raises:
            RuntimeError: If a child component was left unrendered, which can
                only happen when this render did not come from ``render()``;
                if the same render is placed more than once in the output;
                or if ``deps_strategy="fragment"`` needs a mounted web
                integration and none is mounted.
            ValueError: If an argument is invalid; if
                ``security_csp="strict"`` rejects the output or the output
                needs ``csp_nonce`` and none was given; or if
                ``security_javascript="forbid"`` finds a component that
                needs browser behavior; or if a component uses ``Events``
                and no web integration is mounted.
            TypeError: If ``ssr`` is not a bool or ``None``.

        """
        return self.serialize_result(
            deps_strategy=deps_strategy,
            deps_position=deps_position,
            csp_nonce=csp_nonce,
            security_csp=security_csp,
            security_javascript=security_javascript,
            security_script_integrity=security_script_integrity,
            ssr=ssr,
        ).html

    def serialize_result(
        self,
        deps_strategy: DepsStrategy = "document",
        deps_position: DepsPosition = "smart",
        *,
        csp_nonce: str | None = None,
        security_csp: SecurityCspMode | None = None,
        security_javascript: SecurityJavascriptMode | None = None,
        security_script_integrity: SecurityScriptIntegrityMode | None = None,
        ssr: bool | None = None,
    ) -> SerializedRender:
        """
        Return final HTML together with security metadata for those exact bytes.

        Arguments and validation match
        [`serialize()`][citry.CitryRender.serialize]; this method also returns
        the security metadata a host needs, while ``serialize()`` returns only
        ``result.html``.
        """
        # Imported here, not at module load, to avoid an import cycle:
        # serialize.py imports CitryRender from this module.
        from citry.serialize import serialize_render_result  # noqa: PLC0415

        return serialize_render_result(
            self,
            deps_strategy=deps_strategy,
            deps_position=deps_position,
            csp_nonce=csp_nonce,
            security_csp=security_csp,
            security_javascript=security_javascript,
            security_script_integrity=security_script_integrity,
            ssr=ssr,
        )

    def __str__(self) -> str:
        return self.serialize()

    def __bytes__(self) -> bytes:
        return self.serialize().encode()

    def __repr__(self) -> str:
        return f"CitryRender(parts={len(self.parts)})"


class RenderDecoration(CitryRender):
    """Atomic transparent visual wrapper around one structured render body."""

    __slots__ = ("closing", "omit_around_document", "opening")

    def __init__(
        self,
        parts: list[RenderPart],
        context: CitryContext,
        *,
        opening: tuple[object, ...],
        closing: tuple[object, ...],
        omit_around_document: bool = False,
        frame: RenderFrame | None = None,
    ) -> None:
        from citry._vue.capture import PreparedElementClose, PreparedElementOpen, PreparedTextValue  # noqa: PLC0415

        if type(opening) is not tuple or type(closing) is not tuple:
            raise TypeError("render decoration edges must be immutable tuples")
        allowed = (PreparedElementOpen, PreparedElementClose, PreparedTextValue)
        if not opening or not closing or any(type(part) not in allowed for part in (*opening, *closing)):
            raise TypeError("render decoration edges must be nonempty fixed typed structure")
        for part in (*opening, *closing):
            if type(part) is PreparedElementOpen and (
                part.event_bindings
                or part.poll_bindings
                or part.control_bindings
                or part.browser_bindings
                or part.runtime_event_bindings
                or part.runtime_poll_bindings
                or part.runtime_events_candidate
                or any(attr.name.startswith(("v-", "@", ":", "#")) for attr in part.attrs)
            ):
                raise TypeError("render decoration element structure must be inert")
        if type(omit_around_document) is not bool:
            raise TypeError("render decoration document policy must be a boolean")
        super().__init__(parts=parts, context=context, frame=frame)
        self.opening = opening
        self.closing = closing
        self.omit_around_document = omit_around_document

    def _with_frame(self, context: CitryContext, frame: RenderFrame) -> RenderDecoration:
        return RenderDecoration(
            self.parts,
            context,
            opening=self.opening,
            closing=self.closing,
            omit_around_document=self.omit_around_document,
            frame=frame,
        )


class Placeholder:
    """
    A spot in the output whose final text is supplied at serialize time.

    Rendered output is normally text and nested renders, fixed once rendered.
    A Placeholder marks a position whose content is only known when the whole
    page is serialized: the ``<c-js>`` / ``<c-css>`` built-ins render one
    each, and the dependencies extension fills them with the collected
    script/style tags via the ``on_serialize`` hook.

    Attributes:
        key: What belongs at this spot (e.g. ``"deps:js"``). The serializer
            reports each occurrence to the ``on_serialize`` hook under this
            key plus a counter and a private per-serialization identity. An
            extension that knows the key supplies the text; an occurrence no
            extension fills serializes to nothing. The private identity keeps
            cleanup from matching an authored ``<template c-render-id>`` with
            the same key and counter.

    """

    __slots__ = ("key",)

    def __init__(self, key: str) -> None:
        self.key = key

    def __repr__(self) -> str:
        return f"Placeholder({self.key!r})"


class DeferredComponent:
    """
    A child component that has not been rendered yet.

    When the parent's template reaches a ``<c-child>`` tag, citry does not render
    the child right there. Doing so would mean one component renders the next,
    which renders the next, so a deeply nested page would hit Python's recursion
    limit. Instead the parent records the child as a ``DeferredComponent`` (with
    its inputs already worked out) and carries on. ``render_impl`` later renders
    the recorded children one at a time, swapping each ``DeferredComponent`` for
    the child's ``CitryRender``. See docs/design/component_rendering_defer.md section 4.

    Attributes:
        element: The child to render: its component class plus the inputs
            (kwargs/slots), already worked out. The inputs are read while the
            parent is still rendering, so a loop variable from an enclosing
            ``<c-for>`` keeps the right value.
        parent: The parent ``Component`` instance. Used to set the child's
            ``parent``/``root`` links when it is rendered.
        provides: The provide/inject entries active where the ``<c-child>``
            tag sits, read while the parent is still rendering, at the same
            time as the kwargs (see docs/design/component_provide.md section 4.2). The
            child inherits these when the queue renders it.
        physical_parent_region_id: The Slot region containing this deferred
            occurrence, retained because Python-composed replacements may not
            have a template invocation record from which to recover it later.

    """

    __slots__ = ("direct_parent_execution", "element", "parent", "provides")

    def __init__(
        self,
        element: CitryElement,
        parent: Component,
        provides: dict[str, Any] | None = None,
        *,
        direct_parent_execution: DirectExecutionFrame | None = None,
    ) -> None:
        self.element = element
        self.parent = parent
        self.provides = provides if provides is not None else {}
        self.direct_parent_execution = direct_parent_execution

    def __repr__(self) -> str:
        return f"DeferredComponent({self.element!r})"


# The imported identities come from their defining modules; the local classes
# are captured here before callers can replace any dispatch aliases.
_DEFAULT_VALUE_TYPES = (_DEFAULT_COMPONENT_LIKE, _DEFAULT_CITRY_ELEMENT, CitryRender)


def _default_value_dispatch_for(kind: type[object]) -> bool:
    """Whether an exact built-in type still has the renderer's default protocol meaning."""
    return (
        ComponentLike is _DEFAULT_VALUE_TYPES[0]
        and CitryElement is _DEFAULT_VALUE_TYPES[1]
        and CitryRender is _DEFAULT_VALUE_TYPES[2]
        and not issubclass(kind, ComponentLike)
    )


def _render_slot_value(slot: Slot, data: Any, fallback: Slot | None, context: CitryContext) -> RenderPart:
    """Keep the insertion context while a Python slot produces a component value."""
    token = _VALUE_CONTEXT.set(context)
    try:
        rendered = slot(data, fallback=fallback, provides=context.provides)
        from citry._vue.capture import PreparedTextValue, vue_render_active  # noqa: PLC0415
        from citry.slots import _EscapedSlotText  # noqa: PLC0415

        if vue_render_active() and isinstance(rendered, _EscapedSlotText) and "<" not in rendered:
            source = "python-slot-text"
            return PreparedTextValue(source, (0, len(source)), unescape(str(rendered)))
        return rendered
    finally:
        _VALUE_CONTEXT.reset(token)


def _render_value(
    value: Any,
    provides: dict[str, Any] | None = None,
    *,
    citry: Citry | None = None,
    context: CitryContext | None = None,
) -> RenderPart:
    """
    Convert an evaluated expression value into a body part.

    This is the bridge from an arbitrary Python value (the result of evaluating
    a ``{{ ... }}`` expression, or a value handed into an attribute) to a
    ``RenderPart``. The rules (see docs/design/component_rendering.md section 3.1 and
    docs/design/component_slots.md section 3.5):

    - ``None`` renders as the empty string (not the literal ``"None"``).
    - A ``Slot`` is invoked with no data, so ``{{ my_slot }}`` renders slot
      content in place. (Calling it with data, ``{{ my_slot(d) }}``, also lands
      here: the call already produced a render part, handled by the rules
      below.) The slot's fallback handle is a Slot too, so ``{{ fallback }}``
      renders through this same branch.
    - A ``ComponentLike`` is asked for a ``CitryElement`` using the Citry
      instance rendering this tree. The result must belong to that exact
      instance. This lets packages expose import-time composition values while
      keeping their concrete component classes per Citry instance.
    - A ``CitryElement`` (a composed-but-unrendered element handed into an
      expression) is rendered now, so its output and dependencies flow into the
      surrounding tree.
    - A ``CitryRender`` (an already-rendered subtree) is inlined as-is; it is
      trusted HTML, and the surrounding ``_render_body`` merges its dependencies.
    - Anything else is autoescaped. ``escape`` respects the ``__html__``
      protocol, so ``Markup`` (trusted HTML) passes through unescaped.

    ``provides`` are the provide/inject entries active where the value was
    found; an element rendered here inherits them, so a component embedded
    via ``{{ element }}`` or slot content can ``inject`` what its render site
    provides (docs/design/component_provide.md section 4.4).

    A ``Const`` marker is unwrapped first: the value is becoming output here,
    so the marker has no further role, and the identity check below
    (``value is None``) must see the real value, not the proxy.
    """
    if context is None:
        context = _VALUE_CONTEXT.get()
    value = const_value(value)
    if value is None:
        return ""
    if isinstance(value, Slot):
        if context is not None:
            return _render_slot_value(value, None, None, context._with_provides(provides))
        return value(provides=provides)

    # Exact strings and ordinary slotted renders have no instance-level
    # protocol members. Keep registration and class changes visible on each call.
    kind = type(value)
    if kind is str and _default_value_dispatch_for(kind):
        return escape(value)
    if (
        kind is _DEFAULT_VALUE_TYPES[2]
        and _default_value_dispatch_for(kind)
        and kind.__bases__ == (object,)
        and "__citry_element__" not in kind.__dict__
        and "__getattribute__" not in kind.__dict__
        and "__getattr__" not in kind.__dict__
        and "__class__" not in kind.__dict__
    ):
        return value
    if isinstance(value, ComponentLike):
        value = _resolve_component_like(value, citry)
    if isinstance(value, CitryElement):
        # Imported here, not at module load: component_render imports this
        # module, so a top-level import back into it would be circular.
        from citry.component_render import render_impl  # noqa: PLC0415

        if value.comp_cls.simple is True and context is not None:
            from citry._simple_runtime import render_simple_value  # noqa: PLC0415

            return render_simple_value(value, context, provides)

        value = render_impl(value, provides=provides)
        # A component supplied by a Python expression renders in its own tree,
        # rather than through the surrounding tree's DeferredComponent commit
        # path. Mark that finalized root with the same composition carrier so
        # prepared assembly can distinguish it from an unauthenticated
        # authored child missing parser call metadata.
        from citry._vue.direct import wrap_python_composition_result  # noqa: PLC0415

        value = wrap_python_composition_result(value)
    if isinstance(value, CitryRender):
        return value
    # Prepared slot text can pass through another expression while a simple
    # component flattens its callback result.  Keep that checked render part
    # intact; treating the dataclass as an ordinary Python value serializes
    # its repr instead of the captured text.
    from citry._vue.capture import PreparedTextValue  # noqa: PLC0415

    if isinstance(value, PreparedTextValue):
        return value
    return escape(value)


def simple_vue_called_components(record: SimpleVueRecord) -> Iterator[CitryRender | SimpleVueRecord]:
    """
    Yield the components a ``simple='vue'`` occurrence called, and the ones those records called.

    A record keeps its called children inside its leaf rather than in a
    render's ``parts``, so every walk over a render tree reaches them
    through this function. Called records are yielded and then searched in
    turn; an ordinary child render is yielded but not entered, since the
    caller already walks renders. Any other part (a child that has not been
    rendered yet) is yielded as well, so a checker can reject it.
    """
    pending: list[SimpleVueRecord] = [record]
    while pending:
        children = pending.pop().leaf.call_children
        if children is None:
            continue
        for part in children.parts:
            if type(part) is SimpleVueRecord:
                pending.append(part)
            yield cast("CitryRender | SimpleVueRecord", part)


def selected_render_ids(render: CitryRender) -> frozenset[str]:
    """Return component render IDs reachable through the final selected tree."""
    selected: set[str] = set()
    pending = [render]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if current.frame.is_component_root and current.frame.render_id is not None:
            selected.add(current.frame.render_id)
        for part in current.parts:
            if isinstance(part, SimpleVueRecord):
                selected.add(part.render_id)
                if part.leaf.call_children is None:
                    continue
                for called in simple_vue_called_components(part):
                    if isinstance(called, SimpleVueRecord):
                        selected.add(called.render_id)
                    elif isinstance(called, CitryRender):
                        pending.append(called)
            elif isinstance(part, CitryRender):
                pending.append(part)
    return frozenset(selected)
