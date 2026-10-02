"""The ``<c-mark>`` built-in component."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from citry.citry_element import CitryElement
from citry.citry_render import CitryRender, SimpleVueRecord
from citry.component import Component
from citry.constness import const_value

if TYPE_CHECKING:
    from citry.citry import Citry
    from citry.citry_render import RenderPart
    from citry.slots import SlotInput


_MARK_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")


class _SyntheticMarkElement(CitryElement):
    """Exact private element type for one replacement wrapper."""


def synthetic_mark_replacement(mark_class: type[Component], name: str, body: CitryRender) -> CitryElement:
    """Build one exact private wrapper without authorizing nested Marks."""
    return _SyntheticMarkElement(mark_class, {"name": name}, {"default": body})


def validate_mark_name(value: object) -> str:
    """Return one validated, case-sensitive marker name."""
    name = const_value(value)
    if type(name) is not str or _MARK_NAME.fullmatch(name) is None:
        raise ValueError("<c-mark> name must match [A-Za-z][A-Za-z0-9_-]*.")
    return name


def repeated_mark_name_error(component_name: str, name: str) -> ValueError:
    """Build the error for one component that rendered two ``<c-mark>`` regions with the same name."""
    msg = (
        f"Component {component_name!r} rendered more than one <c-mark name={name!r}>. An event handler picks "
        f"the region to update by its name (target='mark:{name}'), so each name can render only once per "
        "component. Give each <c-mark> its own name. If the <c-mark> sits inside <c-for>, wrap the whole "
        "loop in one <c-mark>, or move the loop body into its own component so each item has its own regions."
    )
    return ValueError(msg)


def _note_rendered_mark(mark: Component, name: str) -> None:
    """Record that ``mark`` rendered in the component whose template or fill wrote it."""
    # `parent` is the component that wrote the tag (a fill's author, not the
    # component whose slot shows it), which is the component a handler's
    # `target="mark:<name>"` searches. A mark with no such component, or the
    # wrapper the Events extension builds around a replacement, names no
    # region of anyone's template, so it has nothing to clash with.
    owner = mark.parent
    if owner is None or mark._citry_mark_replacement:
        return
    names = owner._citry_mark_names
    if names is None:
        owner._citry_mark_names = {name}
    elif name in names:
        # Only a flag here: an on_render hook or an error boundary may still
        # throw this output away, so the owner checks what it kept once its
        # render settles.
        owner._citry_mark_name_repeated = True
    else:
        names.add(name)


def reject_repeated_mark_names(owner: Component, render: CitryRender) -> None:
    """
    Raise when ``render`` still holds two ``<c-mark>`` regions with one name owned by ``owner``.

    The render loop calls this when ``owner`` settles, and only after
    ``_note_rendered_mark`` saw a name twice, so ordinary renders never walk
    the tree. Walking the settled output skips regions that an ``on_render``
    hook or ``<c-error-fallback>`` replaced, so a fallback may reuse the name
    of the content it stands in for.
    """
    # One Mark instance per name. A wrapper render can repeat its child's
    # component, so the same instance seen twice is one region, not two.
    seen: dict[str, Component] = {}
    # An explicit stack, because a page can nest deeper than Python's
    # recursion limit; this mirrors how the render loop finds child components.
    pending: list[RenderPart] = list(render.parts)
    while pending:
        part = pending.pop()
        if isinstance(part, CitryRender):
            component = part.context.component
            if (
                part.frame.is_component_root
                and component is not None
                and component.parent is owner
                and not component._citry_mark_replacement
            ):
                name = getattr(component, "_citry_mark_name", None)
                if type(name) is str and seen.setdefault(name, component) is not component:
                    raise repeated_mark_name_error(type(owner).__name__, name)
            pending.extend(part.parts)
        elif type(part) is SimpleVueRecord and part.leaf.call_children is not None:
            # A simple='vue' occurrence keeps the components it called in its
            # leaf instead of in `parts`.
            pending.extend(part.leaf.call_children.parts)


def make_mark_component(citry_instance: Citry) -> type[Component]:
    """Create the engine-owned, nontransparent ``<c-mark>`` component."""

    class Mark(Component, _citry_builtin=citry_instance._registry._builtin_registration_token):
        """
        Name part of a component's template so an event handler can update only that part.

        ``name`` (required) is case-sensitive, starts with a letter, and
        contains only letters, digits, hyphens, and underscores. The tag
        accepts no other attribute and only its default slot.

        Each name may render only once per component: a ``<c-mark>`` inside a
        ``<c-for>`` that runs more than once, or two tags with the same name
        that both render, raise ``ValueError`` when the component renders.
        Tags in different ``<c-if>``/``<c-else>`` branches may share a name,
        because only one of them renders. A ``<c-mark>`` written inside a
        ``<c-fill>`` belongs to the component whose template holds the fill,
        and one in a ``simple=True`` component's template belongs to the
        component that calls it.
        """

        citry = citry_instance
        name = "mark"
        template = "<c-slot />"

        class Kwargs:
            name: str

        class Slots:
            default: SlotInput | None = None

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002
            if set(self.raw_kwargs) != {"name"}:
                raise ValueError("<c-mark> requires exactly one 'name' attribute.")
            unexpected_slots = set(self.raw_slots) - {"default"}
            if unexpected_slots:
                raise ValueError("<c-mark> accepts only its default slot.")
            self._citry_mark_name = validate_mark_name(kwargs.name)
            _note_rendered_mark(self, self._citry_mark_name)
            return {}

    return Mark


__all__ = [
    "make_mark_component",
    "reject_repeated_mark_names",
    "repeated_mark_name_error",
    "synthetic_mark_replacement",
    "validate_mark_name",
]
