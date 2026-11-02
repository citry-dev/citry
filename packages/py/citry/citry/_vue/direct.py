"""Render-local relationships for the private graph-free Vue target."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Protocol, TypeVar

from citry.citry_render import (
    _AFTER_RENDER_HOOKS_RENDER_ID,
    _VALUE_CONTEXT,
    CitryRender,
    RenderDecoration,
    RenderPart,
    SimpleVueRecord,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from contextvars import Token

    from citry.citry_context import CitryContext
    from citry.component import Component
    from citry.slots import Slot


# Any value a template prints; bind_received_output returns it unchanged or projected.
_Value = TypeVar("_Value")


@dataclass(frozen=True, slots=True)
class DirectFillSource:
    session: DirectRenderSession
    lexical_render_id: str
    kind: str
    public_name: str
    source: object
    span: tuple[int, int]
    origin: str | None
    strict_session: bool
    # The fill's `v-slot` pattern, which reads the Vue slot props the
    # receiving `<c-slot>` passes; `None` for a fill without one.
    vue_pattern: str | None = None


@dataclass(slots=True)
class DirectExecutionFrame:
    index: int
    parent: DirectExecutionFrame | None
    fill_source: DirectFillSource
    public_name: str
    receiver_render_id: str
    source: object
    span: tuple[int, int]
    consumed: bool = False
    # The receiving `<c-slot>`'s Vue slot props, as `(attribute, expression)`
    # pairs written in its template, such as `(":row", "row")`.
    vue_props: tuple[tuple[str, str], ...] = ()
    # Whether a `<c-slot>` outlet opened this frame, rather than a Slot printed
    # as a value, such as `{{ icon }}`, which Python passed to the template;
    # an error names which it was.
    from_outlet: bool = False


class DirectProjectionRender(CitryRender):
    """Authenticated lexical projection into one receiving component."""

    __slots__ = (
        "execution_index",
        "fill_source",
        "from_outlet",
        "parent_execution",
        "public_name",
        "receiver_render_id",
        "result_render_id",
        "selected",
        "source",
        "span",
        "vue_props",
    )

    def __init__(
        self,
        selected: CitryRender,
        *,
        execution_index: int,
        fill_source: DirectFillSource,
        parent_execution: DirectExecutionFrame | None,
        public_name: str,
        receiver_render_id: str,
        source: object,
        span: tuple[int, int],
        preserve_selected: bool = False,
        vue_props: tuple[tuple[str, str], ...] = (),
        from_outlet: bool = False,
    ) -> None:
        if not isinstance(selected, CitryRender):
            raise TypeError("a direct projection must wrap structured template output")
        if type(execution_index) is not int or execution_index <= 0:
            raise ValueError("a direct projection execution must be a positive integer")
        if not isinstance(fill_source, DirectFillSource):
            raise TypeError("a direct projection must carry an authenticated fill source")
        if type(public_name) is not str or not public_name:
            raise ValueError("a direct projection must have a public source name")
        if type(receiver_render_id) is not str or not receiver_render_id:
            raise ValueError("a direct projection must have a receiver render identity")
        if (
            type(source) is not str
            or type(span) is not tuple
            or len(span) != 2
            or any(type(value) is not int for value in span)
            or not 0 <= span[0] <= span[1] <= len(source.encode("utf-8"))
        ):
            raise ValueError("a direct projection must have a valid template source span")
        parts: list[RenderPart]
        if (
            preserve_selected
            or isinstance(selected, (DirectProjectionRender, DirectCallRunRender))
            or selected.frame.is_component_root
        ):
            parts = [selected]
        else:
            parts = list(selected.parts)
        super().__init__(parts=parts, context=selected.context)
        self.execution_index = execution_index
        self.fill_source = fill_source
        self.parent_execution = parent_execution
        self.public_name = public_name
        self.receiver_render_id = receiver_render_id
        self.result_render_id = selected.frame.render_id if selected.frame.is_component_root else None
        self.selected = selected
        self.source = source
        self.span = span
        self.vue_props = vue_props
        self.from_outlet = from_outlet


class DirectSlotRender(DirectProjectionRender):
    """Transparent selected result of one actual slot-outlet execution."""

    __slots__ = ()


class DirectNestedTemplateRender(DirectProjectionRender):
    """A nested template projected with its authored lexical Vue scope."""

    __slots__ = ()

    # The parameters are repeated rather than forwarded as **kwargs so that a
    # caller passing the wrong projection field is caught here, at the nested
    # template, instead of inside the base class's validation.
    def __init__(
        self,
        selected: CitryRender,
        *,
        execution_index: int,
        fill_source: DirectFillSource,
        parent_execution: DirectExecutionFrame | None,
        public_name: str,
        receiver_render_id: str,
        source: object,
        span: tuple[int, int],
    ) -> None:
        super().__init__(
            selected,
            execution_index=execution_index,
            fill_source=fill_source,
            parent_execution=parent_execution,
            public_name=public_name,
            receiver_render_id=receiver_render_id,
            source=source,
            span=span,
            preserve_selected=True,
        )


class UnboundNestedTemplateRender(CitryRender):
    """
    A nested template value as the receiving component gets it, before each print binds it.

    The template was rendered once, where its attribute was evaluated, and
    the components inside it are still waiting to render. Each place the
    receiving component prints it renders separately, as each outlet of a
    slot does: the first print takes the render made at the attribute, and
    every later print calls ``render_again``, so the components inside
    render once per print.
    """

    __slots__ = ("fill_source", "printed", "public_name", "render_again", "selected", "source", "span")

    def __init__(
        self,
        selected: CitryRender,
        *,
        fill_source: DirectFillSource,
        render_again: Callable[[], CitryRender],
    ) -> None:
        super().__init__(parts=list(selected.parts), context=selected.context, frame=selected.frame)
        self.fill_source = fill_source
        self.public_name = fill_source.public_name
        self.selected = selected
        self.source = fill_source.source
        self.span = fill_source.span
        # Renders the template again in the scope its attribute was written
        # in, for each print after the first.
        self.render_again = render_again
        # Whether a print has taken ``selected``. The render queue replaces
        # the placeholders in its parts as their components render, so a
        # second print of the same parts would render each component twice.
        self.printed = False


class AuthoredCallAnchor(Protocol):
    """
    The template position a Python loop call site is pinned to.

    A live render supplies the parsed component node itself, while a replayed one
    supplies a small stand-in rebuilt from the artifact. Only the position is shared,
    so that is all this names.
    """

    @property
    def source(self) -> str: ...

    @property
    def position(self) -> tuple[int, int]: ...


class DirectCallRunRender(CitryRender):
    """Transparent selected output retaining one exact authored Python loop call site."""

    __slots__ = ("call_node", "child_type_key")

    def __init__(self, selected: CitryRender, *, call_node: AuthoredCallAnchor, child_type_key: str) -> None:
        super().__init__(parts=list(selected.parts), context=selected.context, frame=selected.frame)
        self.call_node = call_node
        self.child_type_key = child_type_key


class DirectPythonComponentRender(CitryRender):
    """One component returned directly by a Python composition site."""

    __slots__ = ("local_ordinal",)

    def __init__(self, selected: CitryRender, *, local_ordinal: int) -> None:
        if not selected.frame.is_component_root:
            raise TypeError("a Python component call must wrap one component root")
        prepared = selected.frame.prepared_occurrence
        if prepared is not None and prepared.call is not None:
            raise TypeError("an authored component call cannot become a Python composition call")
        if type(local_ordinal) is not int or local_ordinal < 0:
            raise ValueError("a Python component call ordinal must be a nonnegative integer")
        super().__init__(parts=list(selected.parts), context=selected.context, frame=selected.frame)
        self.local_ordinal = local_ordinal


class DirectRenderSession:
    """Small live scope for graph-free prepared rendering."""

    __slots__ = ("active", "composition_count", "execution_count")

    def __init__(self) -> None:
        self.active = True
        self.composition_count = 0
        self.execution_count = 0

    def next_composition(self) -> int:
        if not self.active:
            raise RuntimeError("a prepared composition cannot run after its direct render session closed")
        result = self.composition_count
        self.composition_count += 1
        return result

    def next_execution(self) -> int:
        if not self.active:
            raise RuntimeError("a prepared Slot cannot run after its direct render session closed")
        self.execution_count += 1
        return self.execution_count


_DIRECT_SESSION: ContextVar[DirectRenderSession | None] = ContextVar("citry_vue_direct_session", default=None)
_ACTIVE_EXECUTION: ContextVar[DirectExecutionFrame | None] = ContextVar("citry_vue_direct_execution", default=None)
_ACTIVE_RECEIVER: ContextVar[CitryContext | None] = ContextVar("citry_vue_direct_receiver", default=None)


def receiving_context() -> CitryContext | None:
    """Return the context of the component a Python ``Slot`` call is landing in, when one is known."""
    return _VALUE_CONTEXT.get() or _ACTIVE_RECEIVER.get()


def direct_session() -> DirectRenderSession | None:
    return _DIRECT_SESSION.get()


def active_execution() -> DirectExecutionFrame | None:
    return _ACTIVE_EXECUTION.get()


@contextmanager
def direct_receiver_scope(context: CitryContext) -> Iterator[None]:
    """Retain the component receiving Python Slot calls during data and hooks."""
    token = _ACTIVE_RECEIVER.set(context)
    try:
        yield
    finally:
        _ACTIVE_RECEIVER.reset(token)


@contextmanager
def direct_render_scope() -> Iterator[DirectRenderSession]:
    existing = _DIRECT_SESSION.get()
    if existing is not None:
        if not existing.active:
            raise RuntimeError("cannot reuse a closed direct prepared-render session")
        yield existing
        return
    session = DirectRenderSession()
    token = _DIRECT_SESSION.set(session)
    try:
        yield session
    finally:
        session.active = False
        _DIRECT_SESSION.reset(token)


class _DirectExecutionScope:
    """
    Make one direct execution frame current until the ``with`` block ends.

    The renderer enters this once per child component, so it is a small class:
    a generator-based context manager costs about four times as much.
    """

    __slots__ = ("_execution", "_token")
    _token: Token[DirectExecutionFrame | None]

    def __init__(self, execution: DirectExecutionFrame | None) -> None:
        self._execution = execution

    def __enter__(self) -> None:
        self._token = _ACTIVE_EXECUTION.set(self._execution)

    def __exit__(self, *exc_info: object) -> None:
        _ACTIVE_EXECUTION.reset(self._token)


# Keep the function-style name so callers write `with direct_execution_scope(frame):`
# like the other scopes in this module.
direct_execution_scope = _DirectExecutionScope


def bind_template_fill(
    slot: Slot,
    *,
    lexical_render_id: str,
    kind: str,
    public_name: str,
    source: object,
    span: tuple[int, int],
    origin: str | None,
    vue_pattern: str | None = None,
) -> None:
    session = direct_session()
    if session is None:
        return
    from citry._vue.capture import vue_render_active  # noqa: PLC0415

    slot._direct_fill_source = DirectFillSource(
        session,
        lexical_render_id,
        kind,
        public_name,
        source,
        span,
        origin,
        vue_render_active(),
        vue_pattern,
    )


def direct_fill_source(slot: Slot) -> DirectFillSource | None:
    value = slot._direct_fill_source
    return value if isinstance(value, DirectFillSource) else None


def wrap_slot_result(
    selected: RenderPart,
    *,
    fill_source: DirectFillSource,
    public_name: str,
    receiver_render_id: str,
    source: object,
    span: tuple[int, int],
    execution: DirectExecutionFrame,
) -> DirectSlotRender:
    session = direct_session()
    if session is None or session is not fill_source.session or not session.active:
        raise RuntimeError("prepared Slot belongs to a different or closed direct render session")
    if not isinstance(selected, CitryRender):
        raise TypeError("direct prepared slots must select structured template output")
    if isinstance(selected, RenderDecoration):
        # DirectSlotRender carries the selected frame by copying its body.
        # Keep an atomic decoration as the body so its edge metadata survives.
        selected = CitryRender(parts=[selected], context=selected.context, frame=selected.frame)
    wrapped = (
        DirectPythonComponentRender(selected, local_ordinal=0)
        if type(selected) is CitryRender
        and selected.frame.is_component_root
        and (selected.frame.prepared_occurrence is None or selected.frame.prepared_occurrence.call is None)
        else selected
    )
    return DirectSlotRender(
        wrapped,
        execution_index=execution.index,
        fill_source=fill_source,
        parent_execution=execution.parent,
        public_name=public_name,
        receiver_render_id=receiver_render_id,
        source=source,
        span=span,
        vue_props=execution.vue_props,
        from_outlet=execution.from_outlet,
    )


def wrap_nested_template(
    selected: CitryRender,
    *,
    render_again: Callable[[], CitryRender],
    lexical_render_id: str,
    public_name: str,
    source: object,
    span: tuple[int, int],
    origin: str | None,
) -> CitryRender:
    session = direct_session()
    if session is None:
        return selected
    return UnboundNestedTemplateRender(
        selected,
        render_again=render_again,
        fill_source=DirectFillSource(
            session=session,
            lexical_render_id=lexical_render_id,
            kind="nested-template",
            public_name=public_name,
            source=source,
            span=span,
            origin=origin,
            strict_session=True,
        ),
    )


def bind_nested_template(value: object, context: CitryContext) -> object:
    if not isinstance(value, UnboundNestedTemplateRender):
        return value
    session = direct_session()
    fill = value.fill_source
    component = context.component
    if session is None or session is not fill.session or not session.active:
        raise RuntimeError("prepared nested template belongs to a different or closed direct render session")
    if component is None or component.id is None:
        raise TypeError("prepared nested template has no receiving component context")
    # The first print takes the render made at the attribute, which keeps
    # the order its components render in when the value is printed once.
    # Each later print gets a render of its own.
    if value.printed:
        selected = value.render_again()
    else:
        value.printed = True
        selected = value.selected
    execution = session.next_execution()
    return DirectNestedTemplateRender(
        selected,
        execution_index=execution,
        fill_source=fill,
        parent_execution=active_execution(),
        public_name=value.public_name,
        receiver_render_id=component.id,
        source=value.source,
        span=value.span,
    )


def _passed_on_by_its_component(author_id: str, receiver: Component) -> bool:
    """
    Whether the component ``author_id`` passed its own output on to ``receiver``.

    Its hook did when the receiver sits inside the author's output, as with
    ``return Frame(body=result)`` in ``on_render``, or when the receiver
    renders while the author's hook runs, as with
    ``Frame(body=ctx.render).render()`` in ``on_component_rendered``. Any
    other component printing the output, such as a parent printing
    ``Row().render()``, gets it as it is.
    """
    if _AFTER_RENDER_HOOKS_RENDER_ID.get() == author_id:
        return True
    current = receiver.parent
    while current is not None:
        if current.id == author_id:
            return True
        current = current.parent
    return False


def bind_received_output(value: _Value, context: CitryContext) -> _Value | CitryRender:
    """
    Return a component's own output as content that component wrote, when its hook passed the output on.

    ``context`` is the component printing the value. A hook that passes the
    output it received to another component, as in
    ``return Frame(body=result)``, still means that output as its own
    component's content. It becomes a nested template written by that
    component (a ``DirectNestedTemplateRender``), so Vue compiles it in that
    component and passes it to the receiver as a slot, instead of placing a
    second copy of the component inside itself. Every render runs this,
    with Vue or without: a page without Vue writes the projection as the
    output it holds. Any other value is returned unchanged.
    """
    session = direct_session()
    if session is None or not isinstance(value, CitryRender):
        return value
    frame = value.frame
    author = value.context.component
    receiver = context.component
    if (
        not (frame.is_component_root or frame.is_transparent_root)
        or author is None
        or author.id is None
        or frame.render_id != author.id
        or receiver is None
    ):
        return value
    if receiver.id == author.id:
        # The component prints its own output inside its own output, as a
        # simple=True receiver does, which renders in its caller's context.
        # Only a hook can hand a component its own output, and the output
        # is already this component's content, so it joins in place, as a
        # returned result does.
        return CitryRender(parts=list(value.parts), context=value.context)
    # A transparent receiver has no Vue definition to print a slot in, as
    # with a nested template, so it gets the output as it is. This includes
    # the root of a standalone template, where a simple=True component
    # rendered on its own prints.
    if type(receiver).transparent is True or not _passed_on_by_its_component(author.id, receiver):
        return value
    template = value.context.template_record
    # The whole template is the place the content was written. A component
    # with no template gets an empty span of an empty source.
    source = template.source if template is not None else ""
    fill = DirectFillSource(
        session=session,
        lexical_render_id=author.id,
        kind="nested-template",
        public_name="on_render result",
        source=source,
        span=(0, len(source.encode("utf-8"))),
        origin=template.origin if template is not None else None,
        strict_session=True,
    )
    # The projection keeps the output with its component's frame, so a cache
    # entry stores it as that component's output, and a page without Vue
    # writes it inside the receiver without its own root markers (see
    # _EnclosingFrames). The Vue capture compiles the parts inside it as the
    # content (see _projected_content).
    return DirectNestedTemplateRender(
        value,
        execution_index=session.next_execution(),
        fill_source=fill,
        parent_execution=active_execution(),
        public_name=fill.public_name,
        receiver_render_id=receiver.id,
        source=fill.source,
        span=fill.span,
    )


def wrap_python_composition_result(selected: RenderPart) -> RenderPart:
    """Mark component roots produced at one Python expression or public Slot boundary."""
    session = direct_session()
    if session is None:
        return selected
    if isinstance(selected, SimpleVueRecord):
        return _mark_python_simple_vue(selected)
    selected_prepared = selected.frame.prepared_occurrence if isinstance(selected, RenderDecoration) else None
    if (
        isinstance(selected, RenderDecoration)
        and selected.frame.is_component_root
        and (selected_prepared is None or selected_prepared.call is None)
    ):
        preserved = CitryRender(parts=[selected], context=selected.context, frame=selected.frame)
        return DirectPythonComponentRender(preserved, local_ordinal=session.next_composition())
    if type(selected) is not CitryRender:
        return selected
    if selected.frame.is_component_root:
        prepared = selected.frame.prepared_occurrence
        if prepared is None or prepared.call is None:
            return DirectPythonComponentRender(selected, local_ordinal=session.next_composition())
        return selected
    parts: list[RenderPart] = []
    changed = False
    for part in selected.parts:
        # A simple="vue" root render is a plain wrapper around one record, so
        # the record itself carries the Python composition mark.
        if isinstance(part, SimpleVueRecord):
            marked = _mark_python_simple_vue(part)
            parts.append(marked)
            changed = changed or marked is not part
            continue
        part_prepared = part.frame.prepared_occurrence if isinstance(part, RenderDecoration) else None
        if (
            isinstance(part, RenderDecoration)
            and part.frame.is_component_root
            and (part_prepared is None or part_prepared.call is None)
        ):
            preserved = CitryRender(parts=[part], context=part.context, frame=part.frame)
            parts.append(DirectPythonComponentRender(preserved, local_ordinal=session.next_composition()))
            changed = True
            continue
        prepared = part.frame.prepared_occurrence if type(part) is CitryRender else None
        if type(part) is CitryRender and part.frame.is_component_root and (prepared is None or prepared.call is None):
            parts.append(DirectPythonComponentRender(part, local_ordinal=session.next_composition()))
            changed = True
        else:
            parts.append(part)
    if not changed:
        return selected
    return CitryRender(parts=parts, context=selected.context, frame=selected.frame)


def _mark_python_simple_vue(record: SimpleVueRecord) -> SimpleVueRecord:
    """Mark a ``simple="vue"`` record that a Python composition site placed."""
    # An authored tag's record keeps its parser call record; only a record
    # rendered as its own root reaches here without one.
    if record.call_metadata is not None or record.python_composition:
        return record
    return replace(record, python_composition=True)


def begin_slot_execution(
    fill_source: DirectFillSource,
    *,
    public_name: str,
    receiver_render_id: str,
    source: object,
    span: tuple[int, int],
    vue_props: tuple[tuple[str, str], ...] = (),
    from_outlet: bool = False,
) -> DirectExecutionFrame:
    session = direct_session()
    if session is None or session is not fill_source.session or not session.active:
        raise RuntimeError("prepared Slot belongs to a different or closed direct render session")
    return DirectExecutionFrame(
        session.next_execution(),
        active_execution(),
        fill_source,
        public_name,
        receiver_render_id,
        source,
        span,
        vue_props=vue_props,
        from_outlet=from_outlet,
    )


@dataclass(frozen=True, slots=True)
class _PythonSlotAtPropsOutlet:
    """A Python Slot rendering at a `<c-slot>` that passes Vue slot props."""

    component_name: str
    slot_name: str
    # The frame that was current when the Slot started. A component the Slot
    # renders opens frames of its own, and a fill called inside one of those
    # has its own outlet, so only a call made directly at this level loses props.
    execution: DirectExecutionFrame | None


_PYTHON_SLOT_AT_PROPS_OUTLET: ContextVar[_PythonSlotAtPropsOutlet | None] = ContextVar(
    "citry_vue_python_slot_at_props_outlet", default=None
)


@contextmanager
def python_slot_at_props_outlet(component_name: str, slot_name: str, *, has_props: bool) -> Iterator[None]:
    """
    Mark a Python Slot that renders at an outlet, so a scoped fill it calls can fail clearly.

    Only an outlet with Vue slot props sets the mark. One without props
    clears it, so a fill that a nested Python Slot calls is judged by the
    outlet it actually renders at.
    """
    marker = _PythonSlotAtPropsOutlet(component_name, slot_name, active_execution()) if has_props else None
    token = _PYTHON_SLOT_AT_PROPS_OUTLET.set(marker)
    try:
        yield
    finally:
        _PYTHON_SLOT_AT_PROPS_OUTLET.reset(token)


def _scoped_fill_through_python_slot(fill_source: DirectFillSource, outlet: _PythonSlotAtPropsOutlet) -> RuntimeError:
    """Explain why a fill with `v-slot` cannot receive props through a Python Slot."""
    return RuntimeError(
        f'{outlet.component_name}\'s <c-slot name="{outlet.slot_name}"> passes Vue slot props, but it renders '
        f"a Python Slot, which calls the fill for slot '{fill_source.public_name}' "
        f'(v-slot="{fill_source.vue_pattern}") from Python. A Python Slot cannot pass Vue slot props on, so '
        "the fill would read nothing. Pass the fill to that component in a template, or read Python slot data "
        "with 'data=\"...\"'."
    )


def capture_slot_call(slot: Slot, callback: Callable[[], RenderPart]) -> RenderPart:
    """Wrap every selected template Slot call, including an invoked fallback handle."""
    fill_source = direct_fill_source(slot)
    session = direct_session()
    if fill_source is None or session is None:
        return callback()
    current = active_execution()
    if fill_source.vue_pattern is not None:
        outlet = _PYTHON_SLOT_AT_PROPS_OUTLET.get()
        if outlet is not None and outlet.execution is current:
            raise _scoped_fill_through_python_slot(fill_source, outlet)
    if current is not None and current.fill_source is fill_source and not current.consumed:
        execution = current
        current.consumed = True
    elif current is not None:
        receiver_render_id = current.receiver_render_id
        if fill_source.kind != "fallback":
            context = receiving_context()
            component = None if context is None else context.component
            if component is not None and component.id is not None:
                receiver_render_id = component.id
        execution = begin_slot_execution(
            fill_source,
            public_name=current.public_name,
            receiver_render_id=receiver_render_id,
            source=current.source,
            span=current.span,
            # The outlet's props belong to the fill it called. Another Slot
            # printed inside that fill lands in another component, where the
            # props' expressions would read that component's data.
            vue_props=current.vue_props if current.fill_source is fill_source else (),
        )
    else:
        # A Slot remains a public Python callable and may be invoked through a
        # template expression (for example ``{{ content(slot_data) }}``).  In
        # that form there is no SlotNode execution frame, but the value
        # renderer still carries the exact receiving component context.
        context = receiving_context()
        component = None if context is None else context.component
        # Named apart from the retained execution's receiver above: this one is the
        # component the call is landing in right now.
        receiver_id = None if component is None else component.id
        if receiver_id is None:
            raise TypeError("direct prepared template Slot call has no receiving component context")
        execution = begin_slot_execution(
            fill_source,
            public_name=fill_source.public_name,
            receiver_render_id=receiver_id,
            source=fill_source.source,
            span=fill_source.span,
        )
    with direct_execution_scope(execution):
        selected = callback()
    return wrap_slot_result(
        selected,
        fill_source=fill_source,
        public_name=execution.public_name,
        receiver_render_id=execution.receiver_render_id,
        source=execution.source,
        span=execution.span,
        execution=execution,
    )
