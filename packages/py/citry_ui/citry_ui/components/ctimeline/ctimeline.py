"""Chronological event and activity Timelines."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, cast

from citry import CitryRender, LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs

CTimelineOrientation = Literal["vertical", "horizontal"]
CTimelineSide = Literal["start", "end", "alternate"]
CTimelineItemSide = Literal["auto", "start", "end"]
CTimelineLineStyle = Literal["solid", "dashed"]
CTimelineDensity = Literal["comfortable", "compact"]
CTimelineSize = Literal["sm", "md", "lg"]
CTimelineState = Literal["neutral", "complete", "current", "pending", "error"]

_ORIENTATIONS = ("vertical", "horizontal")
_SIDES = ("start", "end", "alternate")
_ITEM_SIDES = ("auto", "start", "end")
_LINE_STYLES = ("solid", "dashed")
_DENSITIES = ("comfortable", "compact")
_SIZES = ("sm", "md", "lg")
_STATES = ("neutral", "complete", "current", "pending", "error")
_TIMELINE_CONTEXT = "citry_ui_timeline"
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "contenteditable",
        "data-citry-ui-part",
        "data-density",
        "data-has-opposite",
        "data-line-style",
        "data-orientation",
        "data-side",
        "data-size",
        "hidden",
        "inert",
        "reversed",
        "role",
        "start",
        "tabindex",
    }
)
_ITEM_OWNED = frozenset(
    {
        "aria-current",
        "aria-hidden",
        "contenteditable",
        "data-citry-ui-part",
        "data-has-opposite",
        "data-index",
        "data-side",
        "data-state",
        "hidden",
        "inert",
        "role",
        "tabindex",
    }
)


class CTimelineDefaultSlotData:
    pass


class CTimelineItemDefaultSlotData(TypedDict):
    index: int
    state: CTimelineState
    side: Literal["start", "end"]
    is_first: bool
    is_last: bool


class CTimelineItemOppositeSlotData(CTimelineItemDefaultSlotData):
    pass


class CTimelineItemIndicatorSlotData(CTimelineItemDefaultSlotData):
    pass


@dataclass(frozen=True, slots=True)
class _TimelineDeclaration:
    state: CTimelineState
    side: CTimelineItemSide
    attrs: dict[str, object]
    content: Slot[CTimelineItemDefaultSlotData]
    opposite: Slot[CTimelineItemOppositeSlotData] | None
    indicator: Slot[CTimelineItemIndicatorSlotData] | None


@dataclass(slots=True)
class _TimelineRegistry:
    items: list[_TimelineDeclaration] = field(default_factory=list)


def _plain(name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        raise TypeError(f"{name} must be a string{' or None' if optional else ''}, got {raw!r}.")
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip() or "\x00" in plain:
        raise ValueError(f"{name} must be nonempty and cannot contain U+0000.")
    return plain


def _choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        raise ValueError(f"{name} must be one of {expected}, got {plain!r}.")
    return cast("str", plain)


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(
    owner: str,
    attrs: Mapping[str, object] | None,
    owned: frozenset[str],
    class_: CClassValue | None,
    style: CStyleValue | None,
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        raise TypeError(f"{owner} attrs must be a mapping or None, got {attrs!r}.")
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, f"{owner} attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"{owner} attrs cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _DIRECTIVES:
            raise ValueError(f"{owner} attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in owned:
            raise ValueError(f"{owner} attrs cannot dynamically bind owned attribute {key!r}.")
    return merge_root_attrs(copied, class_, style)


def _registry(component: LibraryComponent) -> _TimelineRegistry:
    provided = component.inject(_TIMELINE_CONTEXT, None)
    if provided is None:
        raise ValueError("CTimelineItem is a declaration component and must be rendered directly inside CTimeline.")
    return cast("_TimelineRegistry", provided.registry)


def _validate_declaration_output(result: CitryRender) -> None:
    if result.serialize(deps_strategy="ignore").strip():
        raise ValueError(
            "CTimeline default content may contain only CTimelineItem declarations, formatting whitespace, "
            "and transparent components that produce no other output."
        )


class CTimeline(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        orientation: CTimelineOrientation = "vertical"
        side: CTimelineSide = "end"
        line_style: CTimelineLineStyle = "solid"
        density: CTimelineDensity = "comfortable"
        size: CTimelineSize = "md"
        label: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTimelineDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        if self.inject(_TIMELINE_CONTEXT, None) is not None:
            raise ValueError(
                "Nested CTimeline must be rendered inside CTimelineItem content, not as a direct item declaration."
            )
        if "default" not in self.raw_slots:
            raise ValueError("CTimeline requires a default slot with at least one CTimelineItem declaration.")
        registry = _TimelineRegistry()
        self.provide(_TIMELINE_CONTEXT, registry=registry)
        return {
            "orientation": _choice("CTimeline orientation", kwargs.orientation, _ORIENTATIONS),
            "side": _choice("CTimeline side", kwargs.side, _SIDES),
            "line_style": _choice("CTimeline line_style", kwargs.line_style, _LINE_STYLES),
            "density": _choice("CTimeline density", kwargs.density, _DENSITIES),
            "size": _choice("CTimeline size", kwargs.size, _SIZES),
            "label": _plain("CTimeline label", kwargs.label, optional=True),
            "attrs": _attrs("CTimeline", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "registry": registry,
        }

    template = """
      <c-CInternalTimelineDeclarations><c-slot required /></c-CInternalTimelineDeclarations>
      <c-CInternalTimeline
        c-orientation="orientation"
        c-side="side"
        c-line_style="line_style"
        c-density="density"
        c-size="size"
        c-label="label"
        c-attrs="attrs"
        c-registry="registry"
      />
    """

    css_file = "runtime.min.css"


class CTimelineItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        state: CTimelineState = "neutral"
        side: CTimelineItemSide = "auto"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTimelineItemDefaultSlotData]
        opposite: SlotInput[CTimelineItemOppositeSlotData] | None = None
        indicator: SlotInput[CTimelineItemIndicatorSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        if "default" not in self.raw_slots:
            raise ValueError("CTimelineItem requires a default content slot.")
        registry = _registry(self)
        registry.items.append(
            _TimelineDeclaration(
                state=cast("CTimelineState", _choice("CTimelineItem state", kwargs.state, _STATES)),
                side=cast("CTimelineItemSide", _choice("CTimelineItem side", kwargs.side, _ITEM_SIDES)),
                attrs=_attrs("CTimelineItem", kwargs.attrs, _ITEM_OWNED, kwargs.class_, kwargs.style),
                content=cast("Slot[CTimelineItemDefaultSlotData]", slots.default),
                opposite=cast("Slot[CTimelineItemOppositeSlotData] | None", slots.opposite),
                indicator=cast("Slot[CTimelineItemIndicatorSlotData] | None", slots.indicator),
            )
        )
        self.unprovide(_TIMELINE_CONTEXT)
        return {}

    def on_render(self) -> str:
        return ""


class CInternalTimelineDeclarations(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTimelineDefaultSlotData]

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CTimeline declaration collection completed without a render result.")
        _validate_declaration_output(result)

    template = "<c-slot required />"


class CInternalTimeline(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        orientation: CTimelineOrientation
        side: CTimelineSide
        line_style: CTimelineLineStyle
        density: CTimelineDensity
        size: CTimelineSize
        label: str | None
        attrs: dict[str, object]
        registry: _TimelineRegistry

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        if not kwargs.registry.items:
            raise ValueError("CTimeline requires at least one CTimelineItem declaration.")
        current_count = sum(item.state == "current" for item in kwargs.registry.items)
        if current_count > 1:
            raise ValueError("CTimeline permits at most one CTimelineItem with state='current'.")
        self.unprovide(_TIMELINE_CONTEXT)
        return {
            "attrs": {
                **kwargs.attrs,
                "aria-label": kwargs.label,
                "data-orientation": kwargs.orientation,
                "data-side": kwargs.side,
                "data-line-style": kwargs.line_style,
                "data-density": kwargs.density,
                "data-has-opposite": any(item.opposite is not None for item in kwargs.registry.items),
                "data-size": kwargs.size,
            },
            "items": [
                {
                    "declaration": declaration,
                    "index": index,
                    "side": (
                        declaration.side
                        if declaration.side != "auto"
                        else ("end" if kwargs.side == "alternate" and index % 2 == 0 else "start")
                        if kwargs.side == "alternate"
                        else kwargs.side
                    ),
                }
                for index, declaration in enumerate(kwargs.registry.items)
            ],
            "count": len(kwargs.registry.items),
        }

    template = """
      <ol class="cui-timeline" c-bind="attrs" data-citry-ui-part="timeline">
        <c-for each="item in items">
          <c-CInternalTimelineItem
            c-declaration="item['declaration']"
            c-index="item['index']"
            c-count="count"
            c-side="item['side']"
          />
        </c-for>
      </ol>
    """


class CInternalTimelineItem(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        declaration: _TimelineDeclaration
        index: int
        count: int
        side: Literal["start", "end"]

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        declaration = kwargs.declaration
        slot_data: CTimelineItemDefaultSlotData = {
            "index": kwargs.index,
            "state": declaration.state,
            "side": kwargs.side,
            "is_first": kwargs.index == 0,
            "is_last": kwargs.index == kwargs.count - 1,
        }
        self.unprovide(_TIMELINE_CONTEXT)
        return {
            "attrs": {
                **declaration.attrs,
                "aria-current": "true" if declaration.state == "current" else None,
                "data-index": kwargs.index,
                "data-state": declaration.state,
                "data-side": kwargs.side,
                "data-has-opposite": declaration.opposite is not None,
            },
            "morph_key": f"timeline-item-{kwargs.index}",
            "content": Slot(lambda ctx: declaration.content(slot_data, provides=dict(ctx.provides or {}))),
            "opposite": (
                Slot(lambda ctx: declaration.opposite(slot_data, provides=dict(ctx.provides or {})))
                if declaration.opposite is not None
                else None
            ),
            "indicator": (
                Slot(lambda ctx: declaration.indicator(slot_data, provides=dict(ctx.provides or {})))
                if declaration.indicator is not None
                else None
            ),
        }

    template = """
      <li class="cui-timeline__item" #c-key="morph_key" c-bind="attrs" data-citry-ui-part="item">
        <c-if cond="opposite is not None">
          <div class="cui-timeline__opposite" data-citry-ui-part="opposite">{{ opposite }}</div>
        </c-if>
        <div class="cui-timeline__track" aria-hidden="true" data-citry-ui-part="track">
          <span class="cui-timeline__before" data-citry-ui-part="before"></span>
          <span class="cui-timeline__indicator" data-citry-ui-part="indicator">
            <c-if cond="indicator is not None">{{ indicator }}</c-if>
          </span>
          <span class="cui-timeline__after" data-citry-ui-part="after"></span>
        </div>
        <div class="cui-timeline__content" data-citry-ui-part="content">{{ content }}</div>
      </li>
    """


__all__ = [
    "CTimeline",
    "CTimelineDefaultSlotData",
    "CTimelineDensity",
    "CTimelineItem",
    "CTimelineItemDefaultSlotData",
    "CTimelineItemIndicatorSlotData",
    "CTimelineItemOppositeSlotData",
    "CTimelineItemSide",
    "CTimelineLineStyle",
    "CTimelineOrientation",
    "CTimelineSide",
    "CTimelineSize",
    "CTimelineState",
]
