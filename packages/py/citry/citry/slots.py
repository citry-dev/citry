"""
The Slot value: the one normalized form for slot content.

Slot content can be supplied many ways: a ``<c-fill>`` body in a template, the
implicit default-slot body, a plain string, a Python function, an already
composed ``CitryElement``, or an already rendered ``CitryRender``. All of them
normalize to a ``Slot``: a callable that is invoked at the ``<c-slot>`` site
with the slot data and a handle to the slot's fallback content. See
docs/design/component_slots.md section 3.

A Slot is:

- **Lazy.** Nothing renders until the Slot is called.
- **Repeatable.** The same Slot may be called many times with different data
  (for example a ``<c-slot>`` inside a loop calls its fill once per item).
- **Standalone.** Calling a Slot needs no component or render context::

      slot = Slot(lambda ctx: f"Hello, {ctx.data.name}!")
      slot({"name": "John"})   # 'Hello, John!'

The slot's fallback content is itself a ``Slot`` (``SlotContext.fallback``),
not a separate type, so ``{{ fallback }}`` in a fill body renders through the
same path as any other slot value.

Escaping: a plain string (or scalar) is escaped when the Slot is constructed;
a function's return value is escaped when the Slot is called. A
``Markup``, ``CitryElement``, or ``CitryRender`` result is trusted and is
not escaped. This matches how ``{{ expr }}`` results are escaped.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeAlias, TypeVar, cast

from typing_extensions import TypeAliasType

from citry.citry_element import CitryElement
from citry.component_like import ComponentLike
from citry.util.html import Markup, escape

if TYPE_CHECKING:
    from citry.citry_render import CitryRender, RenderPart

TSlotData = TypeVar("TSlotData")

SlotName: TypeAlias = str


@dataclass(frozen=True, slots=True, eq=False)
class SlotData(Mapping[str, Any]):
    """
    Immutable data passed from a slot outlet to its fill.

    Identifier-like keys are available as attributes, while every key remains
    available through mapping access. Keys beginning with an underscore and
    keys that collide with mapping methods intentionally require bracket
    access or fill-data destructuring.

    Args:
        values: The slot data values. Citry takes a shallow copy so later
            changes to the input mapping do not change a retained slot call.

    Example:
        ::

            data = SlotData({"label": "Save", "aria-label": "Save item"})
            data.label
            data["aria-label"]

    """

    _values: Mapping[str, Any]

    def __init__(self, values: Mapping[str, Any] | None = None) -> None:
        copied = {} if values is None else dict(values)
        object.__setattr__(self, "_values", MappingProxyType(copied))

    def __getitem__(self, key: str) -> Any:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __getattr__(self, name: str) -> Any:
        if not name.startswith("_") and name.isidentifier():
            try:
                return self._values[name]
            except KeyError:
                pass
        msg = f"{type(self).__name__!s} has no attribute {name!r}"
        raise AttributeError(msg)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({dict(self._values)!r})"


_EMPTY_SLOT_DATA = SlotData()


def _normalize_slot_data(data: Mapping[str, Any] | SlotData | None) -> SlotData:
    if data is None:
        return _EMPTY_SLOT_DATA
    if isinstance(data, SlotData):
        return data
    if not isinstance(data, Mapping):
        msg = f"Slot data must be a mapping, got {type(data).__name__}."
        raise TypeError(msg)
    return SlotData(data)


SlotResult = TypeAliasType(
    "SlotResult",
    "str | Markup | CitryRender | ComponentLike",
)
"""
What a slot function may return.

A plain ``str`` is escaped when the slot renders; ``Markup`` or a
``CitryRender`` is trusted and inlined as-is. A ``ComponentLike`` resolves
against the Citry instance rendering the slot.
"""


@dataclass(frozen=True, slots=True)
class SlotContext(Generic[TSlotData]):
    """
    The single argument a slot function receives.

    Example:
        ::

            def my_slot(ctx: SlotContext) -> str:
                return f"Hello, {ctx.data.name}!"

    """

    data: TSlotData
    """
    Data passed to the slot by the ``<c-slot>`` tag (its extra attributes), or
    by the caller when the Slot is invoked directly. At runtime this is an
    immutable [`SlotData`][citry.SlotData]; the type parameter may describe a
    more precise component-specific field shape.
    """

    fallback: Slot | None = None
    """
    The slot's fallback content (the body of the ``<c-slot>`` tag), as a Slot.

    ``None`` when the Slot is called directly, outside a ``<c-slot>`` site.
    Coerce it to a string (or render it via ``{{ fallback }}``) to render the
    fallback.
    """

    provides: Mapping[str, Any] | None = None
    """
    The provide/inject entries active where the Slot was invoked (the
    ``<c-slot>`` site or expression site). ``None`` when the Slot is called
    directly, outside a render. Template-defined fills use this so their
    bodies render with the invoking site's provides; a slot function may read
    it to inspect provided data.
    """


class SlotFunc(Protocol[TSlotData]):
    """
    The signature of a slot content function.

    Example:
        ::

            def header(ctx: SlotContext) -> str:
                if ctx.data.get("name"):
                    return f"Hello, {ctx.data.name}!"
                return str(ctx.fallback)

    """

    # `ctx` is positional-only: the slot machinery always passes it positionally,
    # so implementations may name the parameter anything.
    def __call__(self, ctx: SlotContext[TSlotData], /) -> SlotResult | CitryElement: ...


class Slot(Generic[TSlotData]):
    """
    Normalized slot content: a lazy, repeatable, standalone callable.

    Construct it from a string, a function, a ``CitryElement``, a
    ``ComponentLike``, or a ``CitryRender``. Calling the Slot returns a render
    part; ``str(slot)`` renders and serializes in one step. A standalone Slot
    containing a ``ComponentLike`` cannot resolve without an active component
    render.

    Example:
        ::

            Slot("Hello!")                                # static content
            Slot(lambda ctx: f"Hi {ctx.data.name}!")   # content function
            Slot(Card(title="Hi"))                        # composed element

    """

    __slots__ = (
        "__weakref__",
        "component_name",
        "content_func",
        "contents",
        "extra",
        "slot_name",
        "source_position",
    )

    def __init__(
        self,
        contents: Any,
        *,
        content_func: SlotFunc[TSlotData] | None = None,
        component_name: str | None = None,
        slot_name: str | None = None,
        source_position: tuple[int, int] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        # A Slot wrapping another Slot is ambiguous (whose metadata wins?), the
        # same rule as django-components. To copy a Slot, construct a new one
        # from its `contents` and `content_func` (see `normalize_slot_fills`).
        if isinstance(contents, Slot):
            msg = "Slot received another Slot instance as `contents`"
            raise TypeError(msg)

        self.contents = contents
        """The original value the Slot was created from."""
        self.component_name = component_name
        """Name of the component this slot content was given to (for debugging)."""
        self.slot_name = slot_name
        """Name of the slot this content fills (for debugging)."""
        self.source_position = source_position
        """The ``(start, end)`` span of the ``<c-fill>`` in its template, if any."""
        self.extra: dict[str, Any] = extra if extra is not None else {}
        """Scratch space for extensions to attach per-slot metadata."""

        if content_func is None:
            content_func = self._resolve_content_func(contents)
        if not callable(content_func):
            msg = f"Slot 'content_func' must be a callable, got: {content_func!r}"
            raise TypeError(msg)
        self.content_func: SlotFunc[TSlotData] = content_func
        """The content function. Call the Slot itself instead of calling this directly."""

    def __call__(
        self,
        data: Mapping[str, Any] | SlotData | None = None,
        fallback: Slot | None = None,
        *,
        provides: dict[str, Any] | None = None,
    ) -> RenderPart:
        """
        Render the slot content and return it as a render part.

        The result is a ``str`` (escaped text), a ``CitryRender`` (a rendered
        subtree with its collected data intact), or another structural render
        part. Pass ``data`` to expose slot data to the content function; pass
        ``fallback`` to give it access to the slot's fallback content.
        ``provides`` carries the provide/inject entries active at the invoking
        site (set by the ``<c-slot>`` and expression machinery); content
        rendered here inherits them. A ``ComponentLike`` result requires an
        active component render so its Citry instance is unambiguous.
        """
        # Imported here, not at module load: citry_render imports Slot (for the
        # `{{ my_slot }}` detection in _render_value), so a top-level import
        # back into it would be circular.
        from citry.citry_render import _render_value  # noqa: PLC0415

        ctx: SlotContext[TSlotData] = SlotContext(
            data=cast("TSlotData", _normalize_slot_data(data)),
            fallback=fallback,
            provides=provides,
        )

        def invoke() -> RenderPart:
            result = self.content_func(ctx)
            return _render_value(result, provides=provides)

        # Imported lazily so Slot remains usable without pulling the render
        # ownership module into the slots/citry_render import cycle.
        from citry.ownership import capture_current_slot_call  # noqa: PLC0415

        return capture_current_slot_call(self, invoke)

    def __str__(self) -> str:
        """
        Render with no data and serialize to an HTML string.

        Like ``CitryRender.serialize()``, this is one-shot: the string can no
        longer merge its collected data (JS/CSS dependencies) into another
        tree. Keep the value a Slot for as long as you compose.
        """
        from citry.citry_render import (  # noqa: PLC0415
            CitryRender,
            _PhysicalRegion,
            unwrap_physical_region,
        )

        part = self()
        unwrapped = unwrap_physical_region(part)
        if isinstance(unwrapped, CitryRender):
            # A template-defined fill returns an interior render. When the
            # Slot is invoked as part of its owning page, that page's render
            # queue settles deferred components in the fill body. Invoked
            # standalone, there is no outer queue, so settle those descendants
            # here before serialization without finalizing the already-rendered
            # owner component a second time.
            from citry.component_render import _settle_render  # noqa: PLC0415
            from citry.ownership import resume_ownership_graph  # noqa: PLC0415

            with resume_ownership_graph(unwrapped.context.ownership):
                settled = _settle_render(unwrapped, finalize_root=False)
                if isinstance(part, _PhysicalRegion):
                    part.part = settled
                    return CitryRender(parts=[part], context=settled.context).serialize()
                return settled.serialize()
        return str(part)

    def __repr__(self) -> str:
        comp_name = f"'{self.component_name}'" if self.component_name else None
        slot_name = f"'{self.slot_name}'" if self.slot_name else None
        return f"<{type(self).__name__} component_name={comp_name} slot_name={slot_name}>"

    @staticmethod
    def _resolve_content_func(contents: Any) -> SlotFunc[TSlotData]:
        """
        Build the content function for a non-function ``contents`` value.

        - A callable is the content function itself.
        - Anything else becomes a function returning a fixed value: a
          ``CitryElement``/``CitryRender`` is returned as-is (rendered or
          inlined at call time), and any other value is escaped NOW, so unsafe
          text is neutralized as early as possible. ``escape`` respects
          ``__html__``, so ``Markup`` stays trusted.
        """
        # Imported here, not at module load: citry_render imports this module.
        from citry.citry_render import CitryRender  # noqa: PLC0415

        if isinstance(contents, ComponentLike):
            value: Any = contents
        elif callable(contents):
            return contents
        else:
            value = contents if isinstance(contents, (CitryElement, CitryRender)) else escape(contents)

        def render_func(_ctx: SlotContext[TSlotData]) -> Any:
            return value

        return render_func


SlotInput = TypeAliasType(
    "SlotInput",
    "SlotResult | SlotFunc[TSlotData] | Slot[TSlotData] | CitryElement",
    type_params=(TSlotData,),
)
"""
All forms in which slot content can be passed to a component.

Use this to type the fields of a component's ``Slots`` class::

    class Table(Component):
        class Slots:
            header: SlotInput
            footer: SlotInput[FooterSlotData]

A field without a default must be filled whenever the component is used. A
field annotated as ``SlotInput | None`` with a ``None`` default is optional.
The ``required`` attribute on ``<c-slot>`` checks something different: it
raises an error only if Citry renders that tag without content.
"""


def normalize_slot_fills(
    fills: Mapping[SlotName, Any],
    component_name: str | None = None,
) -> dict[SlotName, Slot]:
    """
    Normalize a mapping of slot inputs into ``Slot`` instances.

    This is the boundary where Python-passed slots
    (``MyComp(slots={"header": ...})``) become ``Slot`` values:

    - ``None`` values are dropped (same as not passing the slot).
    - A ``Slot`` that already carries its names is kept as-is; one with
      missing names is copied (not mutated) with the names filled in.
    - A function becomes a ``Slot`` around it.
    - Anything else (string, ``Markup``, ``CitryElement``,
      ``CitryRender``, scalar) becomes a static ``Slot``.
    """
    norm_fills: dict[SlotName, Slot] = {}

    for slot_name, content in fills.items():
        # No content given for this slot.
        if content is None:
            continue

        if isinstance(content, Slot):
            # Already a Slot with its names assigned: keep it.
            if content.slot_name and content.component_name:
                norm_fills[slot_name] = content
                continue
            # Copy the Slot (so the caller's instance is not mutated) and fill
            # in the missing names for tracing.
            norm_fills[slot_name] = Slot(
                content.contents,
                content_func=content.content_func,
                component_name=content.component_name or component_name,
                slot_name=content.slot_name or slot_name,
                source_position=content.source_position,
                extra=dict(content.extra),
            )
            continue

        # A function, or a static value (string, element, render, scalar).
        norm_fills[slot_name] = Slot(
            content,
            component_name=component_name,
            slot_name=slot_name,
        )

    return norm_fills
