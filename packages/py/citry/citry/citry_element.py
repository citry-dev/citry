"""
CitryElement - the intermediate representation returned by Component().

When a user writes ``MyCard(title="Hello")``, they get back a
CitryElement, not a rendered string and not a Component instance.
The CitryElement holds the component class, kwargs, and slots,
and can be rendered later with ``.render()`` or ``str()``.

This is analogous to React's RenderElement. The split between
composition (creating the CitryElement) and rendering (calling
``.render()``) enables:

- Reusing the CitryElement as composition data while every ``.render()`` call
  creates fresh per-instance state.
- Passing render objects as values to other components or slots.
- Different render targets (HTML string, streaming, etc.).
- The render pipeline minting fresh per-instance state (render_id,
  JS/CSS variables) on each ``.render()`` call.

Example:
    Compose a component tree without rendering::

        from citry import Component

        class Card(Component):
            template = '<div class="card">{{ title }}</div>'

        class Page(Component):
            template = '<main>{{ content }}</main>'

        # Composition phase - no rendering happens yet
        card = Card(title="Hello")
        page = Page(content=card)

        # Rendering phase - produces a CitryRender, then serialize to HTML
        rendered = page.render()        # -> CitryRender
        html = rendered.serialize()     # -> str
        # Or in one step with defaults: html = str(page)

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry_render import CitryRender
    from citry.component import Component
    from citry.ownership import ComponentInvocationId, ComponentTagClientBindingRecord, OwnershipGraph


class CitryElement:
    """
    Intermediate representation of a component invocation.

    Created by ``Component()``. Holds the component class and the
    kwargs/slots that were passed. Rendering is deferred until
    ``.render()`` is called.

    Attributes:
        comp_cls: The Component subclass to render.
        kwargs: The keyword arguments passed to the component.
        slots: The slot fills passed to the component. Filled from either
            channel: the reserved ``slots=`` kwarg when composing from Python
            (``MyComp(title="x", slots={...})``), or the collected ``<c-fill>``
            tags / implicit default body when composed by a parent template.
            Values are raw inputs here (strings, functions, elements, Slots);
            they normalize to ``Slot`` instances when the component instance is
            created at render time.
        morph_key: The evaluated ``#c-key`` value from the parent's template
            tag, or ``None`` when the tag carried no key. Framework metadata,
            not an input: the render pipeline stamps it (scoped by the child's
            ``class_id``) onto the child's root element(s) as the
            ``data-citry-key`` attribute, so the client can keep the child
            instance's identity across the parent's re-renders (see
            docs/design/events.md section 5.3). Set by ``ComponentNode``; in
            v1 the key is template-authored only.
        component_tag_client_bindings: The final source-ordered ``$c-props``, Alpine event,
            and Citry event contributions captured from a component tag. They
            are framework metadata, not Python kwargs.
        ownership_invocation_id: The render-local component call record that
            this element will bind to its concrete component instance.
        ownership_graph: The render-local graph that allocated
            ``ownership_invocation_id``. Retained explicitly so a lazy value
            invoked during another root render cannot bind a graph-local ID
            against the wrong graph.
        forward_ownership_invocation: Whether this element is the transparent
            dynamic selector and must forward the invocation to its selected
            target instead of consuming it.

    """

    __slots__ = (
        "comp_cls",
        "component_tag_client_bindings",
        "forward_ownership_invocation",
        "kwargs",
        "morph_key",
        "ownership_graph",
        "ownership_invocation_id",
        "slots",
    )

    def __init__(
        self,
        comp_cls: type[Component],
        kwargs: dict[str, Any],
        slots: dict[str, Any] | None = None,
        morph_key: str | None = None,
        *,
        component_tag_client_bindings: tuple[ComponentTagClientBindingRecord, ...] = (),
        ownership_invocation_id: ComponentInvocationId | None = None,
        ownership_graph: OwnershipGraph | None = None,
        forward_ownership_invocation: bool = False,
    ) -> None:
        self.comp_cls = comp_cls
        self.kwargs = kwargs
        self.slots = slots or {}
        self.morph_key = morph_key
        self.component_tag_client_bindings = component_tag_client_bindings
        self.ownership_invocation_id = ownership_invocation_id
        self.ownership_graph = ownership_graph
        self.forward_ownership_invocation = forward_ownership_invocation

    def render(self, *, template_globals: Mapping[str, Any] | None = None) -> CitryRender:
        """
        Render this component into a ``CitryRender``.

        Each call mints fresh per-instance state (render_id, etc.), so the same
        CitryElement can be rendered multiple times with distinct identities.

        ``template_globals`` adds or overrides template variables for this one
        render, layered on top of the instance's ``citry.template_globals`` and
        under each component's own ``template_data``. They reach every component
        in the render, including nested children, embedded elements, and slot
        content, which suits per-request values (the current user, a request id)
        that should not be stored on the shared instance.

        Returns a ``CitryRender`` (the render-phase output), not a string. Call
        ``.serialize()`` on it (or ``str()``) to get the HTML. ``str()`` on the
        element itself runs the full chain with sensible defaults (and no
        ``template_globals``).
        """
        # Imported lazily to break the import cycle: component_render imports the
        # node classes, the nodes import CitryElement (for auto-rendering a
        # composed element found in an expression), so CitryElement must not pull
        # in component_render at module load.
        from citry.component_render import render_impl  # noqa: PLC0415

        return render_impl(self, render_globals=dict(template_globals) if template_globals is not None else None)

    def __str__(self) -> str:
        # Convenience: str(element) runs the full pipeline
        # (render -> serialize) with default options.
        return str(self.render())

    def __repr__(self) -> str:
        cls_name = self.comp_cls.__name__
        kwargs_str = ", ".join(f"{k}={v!r}" for k, v in self.kwargs.items())
        return f"{cls_name}({kwargs_str})"
