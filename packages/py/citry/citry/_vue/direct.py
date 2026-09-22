"""Render-local relationships for the private graph-free Vue target."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from citry.citry_render import CitryRender, RenderPart

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from citry.citry_context import CitryContext
    from citry.slots import Slot


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


class DirectProjectionRender(CitryRender):
    """Authenticated lexical projection into one receiving component."""

    __slots__ = (
        "execution_index",
        "fill_source",
        "parent_execution",
        "public_name",
        "receiver_render_id",
        "result_render_id",
        "selected",
        "source",
        "span",
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
    """Nested template value awaiting one concrete component insertion."""

    __slots__ = ("fill_source", "public_name", "selected", "source", "span")

    def __init__(self, selected: CitryRender, *, fill_source: DirectFillSource) -> None:
        super().__init__(parts=list(selected.parts), context=selected.context, frame=selected.frame)
        self.fill_source = fill_source
        self.public_name = fill_source.public_name
        self.selected = selected
        self.source = fill_source.source
        self.span = fill_source.span


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


@contextmanager
def direct_execution_scope(execution: DirectExecutionFrame | None) -> Iterator[None]:
    token = _ACTIVE_EXECUTION.set(execution)
    try:
        yield
    finally:
        _ACTIVE_EXECUTION.reset(token)


def bind_template_fill(
    slot: Slot,
    *,
    lexical_render_id: str,
    kind: str,
    public_name: str,
    source: object,
    span: tuple[int, int],
    origin: str | None,
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
    from citry.citry_render import RenderDecoration  # noqa: PLC0415

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
    )


def wrap_nested_template(
    selected: CitryRender,
    *,
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
    execution = session.next_execution()
    return DirectNestedTemplateRender(
        value.selected,
        execution_index=execution,
        fill_source=fill,
        parent_execution=active_execution(),
        public_name=value.public_name,
        receiver_render_id=component.id,
        source=value.source,
        span=value.span,
    )


def wrap_python_composition_result(selected: RenderPart) -> RenderPart:
    """Mark component roots produced at one Python expression or public Slot boundary."""
    from citry.citry_render import RenderDecoration  # noqa: PLC0415

    session = direct_session()
    if session is None:
        return selected
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


def begin_slot_execution(
    fill_source: DirectFillSource,
    *,
    public_name: str,
    receiver_render_id: str,
    source: object,
    span: tuple[int, int],
) -> DirectExecutionFrame:
    session = direct_session()
    if session is None or session is not fill_source.session or not session.active:
        raise RuntimeError("prepared Slot belongs to a different or closed direct render session")
    return DirectExecutionFrame(
        session.next_execution(), active_execution(), fill_source, public_name, receiver_render_id, source, span
    )


def capture_slot_call(slot: Slot, callback: Callable[[], RenderPart]) -> RenderPart:
    """Wrap every selected template Slot call, including an invoked fallback handle."""
    fill_source = direct_fill_source(slot)
    session = direct_session()
    if fill_source is None or session is None:
        return callback()
    current = active_execution()
    if current is not None and current.fill_source is fill_source and not current.consumed:
        execution = current
        current.consumed = True
    elif current is not None:
        receiver_render_id = current.receiver_render_id
        if fill_source.kind != "fallback":
            from citry.citry_render import _VALUE_CONTEXT  # noqa: PLC0415

            context = _VALUE_CONTEXT.get() or _ACTIVE_RECEIVER.get()
            component = None if context is None else context.component
            if component is not None and component.id is not None:
                receiver_render_id = component.id
        execution = begin_slot_execution(
            fill_source,
            public_name=current.public_name,
            receiver_render_id=receiver_render_id,
            source=current.source,
            span=current.span,
        )
    else:
        # A Slot remains a public Python callable and may be invoked through a
        # template expression (for example ``{{ content(slot_data) }}``).  In
        # that form there is no SlotNode execution frame, but the value
        # renderer still carries the exact receiving component context.
        from citry.citry_render import _VALUE_CONTEXT  # noqa: PLC0415

        context = _VALUE_CONTEXT.get() or _ACTIVE_RECEIVER.get()
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
