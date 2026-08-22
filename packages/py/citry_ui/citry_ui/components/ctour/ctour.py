"""Target-aware product Tours with interactive highlighted elements."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, cast

from citry import CitryRender, LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_html_id

CTourPlacement = Literal[
    "top-start",
    "top",
    "top-end",
    "bottom-start",
    "bottom",
    "bottom-end",
    "inline-start",
    "inline-end",
]
CTourScroll = Literal["auto", "smooth", "none"]
CTourMissingTarget = Literal["skip", "close"]
CTourSize = Literal["sm", "md", "lg"]
CTourOpenReason = Literal["activator", "close", "escape", "outside", "skip", "finish", "missing-target", "native"]
CTourActiveReason = Literal["next", "previous", "client", "missing-target"]

_PLACEMENTS = (
    "top-start",
    "top",
    "top-end",
    "bottom-start",
    "bottom",
    "bottom-end",
    "inline-start",
    "inline-end",
)
_SCROLL = ("auto", "smooth", "none")
_MISSING_TARGET = ("skip", "close")
_SIZES = ("sm", "md", "lg")
_TOUR_CONTEXT = "citry_ui_tour"
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-hidden",
        "contenteditable",
        "data-active",
        "data-citry-tour-host",
        "data-citry-tour-initialized",
        "data-citry-ui-part",
        "data-open",
        "data-size",
        "data-targeted",
        "data-value",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)
_STEP_OWNED = frozenset(
    {
        "aria-hidden",
        "contenteditable",
        "data-citry-ui-part",
        "data-current",
        "data-describe",
        "data-index",
        "data-placement",
        "data-target-id",
        "data-value",
        "hidden",
        "inert",
        "role",
        "tabindex",
    }
)


class CTourDefaultSlotData:
    pass


class CTourActivatorSlotData(TypedDict):
    activator_attrs: dict[str, object]


class CTourCloseSlotData:
    pass


class CTourStepSlotData(TypedDict):
    index: int
    total: int
    value: str


class CTourStepTitleSlotData(CTourStepSlotData):
    pass


class CTourStepDefaultSlotData(CTourStepSlotData):
    pass


class CTourStepMediaSlotData(CTourStepSlotData):
    pass


class CTourOpenChangeDetail(TypedDict):
    reason: CTourOpenReason
    active: int
    value: str
    controlled: bool
    source: object | None


class CTourActiveChangeDetail(TypedDict):
    previousActive: int
    value: str
    previousValue: str
    reason: CTourActiveReason
    controlled: bool
    source: object | None


@dataclass(frozen=True, slots=True)
class _TourDeclaration:
    value: str
    target_id: str | None
    placement: CTourPlacement
    arrow: bool
    describe: bool
    attrs: dict[str, object]
    title: Slot[CTourStepTitleSlotData]
    content: Slot[CTourStepDefaultSlotData]
    media: Slot[CTourStepMediaSlotData] | None


@dataclass(slots=True)
class _TourRegistry:
    steps: list[_TourDeclaration] = field(default_factory=list)


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


def _registry(component: LibraryComponent) -> _TourRegistry:
    provided = component.inject(_TOUR_CONTEXT, None)
    if provided is None:
        raise ValueError("CTourStep is a declaration component and must be rendered directly inside CTour.")
    return cast("_TourRegistry", provided.registry)


def _validate_declaration_output(result: CitryRender) -> None:
    if result.serialize(deps_strategy="ignore").strip():
        raise ValueError(
            "CTour default content may contain only CTourStep declarations, formatting whitespace, "
            "and transparent components that produce no other output."
        )


class CTour(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        open: bool = False
        active: int = 0
        dismissible: bool = True
        close_on_escape: bool = True
        close_on_outside: bool = False
        skippable: bool = True
        scroll: CTourScroll = "auto"
        missing_target: CTourMissingTarget = "skip"
        size: CTourSize = "md"
        close_label: str = "Close tour"
        previous_label: str = "Previous"
        next_label: str = "Next"
        finish_label: str = "Finish"
        skip_label: str = "Skip tour"
        progress_label: str = "Step {current} of {total}"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTourDefaultSlotData]
        activator: SlotInput[CTourActivatorSlotData] | None = None
        close: SlotInput[CTourCloseSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_tour_snapshot", None)
        if cached is not None:
            return cast("dict[str, object]", cached)
        if self.inject(_TOUR_CONTEXT, None) is not None:
            raise ValueError("Nested CTour must be rendered inside CTourStep content, not as a direct declaration.")
        validate_html_id("CTour", kwargs.id)
        for name in ("open", "dismissible", "close_on_escape", "close_on_outside", "skippable"):
            validate_boolean("CTour", name, getattr(kwargs, name))
        if isinstance(kwargs.active, bool) or not isinstance(kwargs.active, int) or kwargs.active < 0:
            raise ValueError(f"CTour active must be a nonnegative integer, got {kwargs.active!r}.")
        root_id = kwargs.id or f"cui-tour-{self.id}"
        registry = _TourRegistry()
        self.provide(_TOUR_CONTEXT, registry=registry)
        labels: dict[str, str] = {}
        catalog: dict[str, bool] = {}
        for name in ("close", "previous", "next", "finish", "skip", "progress"):
            field_name = f"{name}_label"
            key = f"citry-ui-tour-{name}"
            if field_name in self.raw_kwargs:
                raw = getattr(kwargs, field_name)
            elif name == "progress":
                raw = self.i18n.tr(key, current="1", total="1")
            else:
                raw = self.i18n.tr(key)
            labels[name] = cast("str", _plain(f"CTour {field_name}", raw))
            catalog[name] = uses_catalog_default(self, field_name)
        if not catalog["progress"] and ("{current}" not in labels["progress"] or "{total}" not in labels["progress"]):
            raise ValueError("CTour progress_label must contain {current} and {total}.")
        snapshot: dict[str, object] = {
            "root_id": root_id,
            "dialog_id": f"{root_id}-dialog",
            "open": bool(kwargs.open),
            "active": kwargs.active,
            "dismissible": bool(kwargs.dismissible),
            "close_on_escape": bool(kwargs.close_on_escape),
            "close_on_outside": bool(kwargs.close_on_outside),
            "skippable": bool(kwargs.skippable),
            "scroll": _choice("CTour scroll", kwargs.scroll, _SCROLL),
            "missing_target": _choice("CTour missing_target", kwargs.missing_target, _MISSING_TARGET),
            "size": _choice("CTour size", kwargs.size, _SIZES),
            "labels": labels,
            "catalog": catalog,
            "activator_attrs": {
                "aria-haspopup": "dialog",
                "aria-controls": f"{root_id}-dialog",
                "aria-expanded": "true" if kwargs.open else "false",
                "data-citry-tour-trigger": "",
            },
            "attrs": _attrs("CTour", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "registry": registry,
        }
        self._cui_tour_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        if "default" not in self.raw_slots:
            raise ValueError("CTour requires a default slot with at least one CTourStep declaration.")
        snapshot = self._snapshot(kwargs)
        activator_data: CTourActivatorSlotData = {
            "activator_attrs": cast("dict[str, object]", snapshot["activator_attrs"])
        }
        return {
            **snapshot,
            "activator": (
                Slot(
                    lambda ctx: cast("Slot[CTourActivatorSlotData]", slots.activator)(
                        activator_data,
                        provides=dict(ctx.provides or {}),
                    )
                )
                if slots.activator is not None
                else None
            ),
            "close": (
                Slot(
                    lambda ctx: cast("Slot[CTourCloseSlotData]", slots.close)(
                        {},
                        provides=dict(ctx.provides or {}),
                    )
                )
                if slots.close is not None
                else None
            ),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "open": snapshot["open"],
            "active": snapshot["active"],
            "dismissible": snapshot["dismissible"],
            "closeOnEscape": snapshot["close_on_escape"],
            "closeOnOutside": snapshot["close_on_outside"],
            "skippable": snapshot["skippable"],
            "scroll": snapshot["scroll"],
            "missingTarget": snapshot["missing_target"],
            "size": snapshot["size"],
        }

    template = """
      <c-CInternalTourDeclarations><c-slot required /></c-CInternalTourDeclarations>
      <c-CInternalTour
        c-root_id="root_id"
        c-dialog_id="dialog_id"
        c-open="open"
        c-active="active"
        c-dismissible="dismissible"
        c-skippable="skippable"
        c-size="size"
        c-labels="labels"
        c-catalog="catalog"
        c-activator="activator"
        c-close="close"
        c-attrs="attrs"
        c-registry="registry"
      />
    """

    js_file = "runtime.min.js"

    css_file = "runtime.min.css"

    messages = """
      citry-ui-tour-close = Close tour
      citry-ui-tour-previous = Previous
      citry-ui-tour-next = Next
      citry-ui-tour-finish = Finish
      citry-ui-tour-skip = Skip tour
      # @param {str} $current - One-based current step position.
      # @param {str} $total - Total number of steps in the Tour.
      citry-ui-tour-progress =
          Step { $current } of { $total }
    """


class CTourStep(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        target_id: str | None = None
        placement: CTourPlacement = "bottom"
        arrow: bool = True
        describe: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        title: SlotInput[CTourStepTitleSlotData]
        default: SlotInput[CTourStepDefaultSlotData]
        media: SlotInput[CTourStepMediaSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        if "title" not in self.raw_slots or "default" not in self.raw_slots:
            raise ValueError("CTourStep requires title and default content slots.")
        target_id = cast("str | None", _plain("CTourStep target_id", kwargs.target_id, optional=True))
        validate_html_id("CTourStep", target_id)
        validate_boolean("CTourStep", "arrow", kwargs.arrow)
        validate_boolean("CTourStep", "describe", kwargs.describe)
        registry = _registry(self)
        value = cast("str", _plain("CTourStep value", kwargs.value))
        if any(step.value == value for step in registry.steps):
            raise ValueError(f"CTourStep value {value!r} is duplicated.")
        registry.steps.append(
            _TourDeclaration(
                value=value,
                target_id=target_id,
                placement=cast("CTourPlacement", _choice("CTourStep placement", kwargs.placement, _PLACEMENTS)),
                arrow=bool(kwargs.arrow),
                describe=bool(kwargs.describe),
                attrs=_attrs("CTourStep", kwargs.attrs, _STEP_OWNED, kwargs.class_, kwargs.style),
                title=cast("Slot[CTourStepTitleSlotData]", slots.title),
                content=cast("Slot[CTourStepDefaultSlotData]", slots.default),
                media=cast("Slot[CTourStepMediaSlotData] | None", slots.media),
            )
        )
        self.unprovide(_TOUR_CONTEXT)
        return {}

    def on_render(self) -> str:
        return ""


class CInternalTourDeclarations(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTourDefaultSlotData]

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CTour declaration collection completed without a render result.")
        _validate_declaration_output(result)

    template = "<c-slot required />"


class CInternalTour(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        root_id: str
        dialog_id: str
        open: bool
        active: int
        dismissible: bool
        skippable: bool
        size: CTourSize
        labels: dict[str, str]
        catalog: dict[str, bool]
        activator: Slot[CTourActivatorSlotData] | None
        close: Slot[CTourCloseSlotData] | None
        attrs: dict[str, object]
        registry: _TourRegistry

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        if not kwargs.registry.steps:
            raise ValueError("CTour requires at least one CTourStep declaration.")
        if kwargs.active >= len(kwargs.registry.steps):
            raise ValueError(f"CTour active {kwargs.active} is outside its {len(kwargs.registry.steps)} Steps.")
        self.unprovide(_TOUR_CONTEXT)
        items = []
        total = len(kwargs.registry.steps)
        for index, declaration in enumerate(kwargs.registry.steps):
            slot_data: CTourStepSlotData = {"index": index, "total": total, "value": declaration.value}
            title_id = f"{kwargs.root_id}-title-{index}"
            description_id = f"{kwargs.root_id}-description-{index}"
            items.append(
                {
                    "declaration": declaration,
                    "index": index,
                    "total": total,
                    "title_id": title_id,
                    "description_id": description_id,
                    "active": index == kwargs.active,
                    "progress": (
                        self.i18n.tr("citry-ui-tour-progress", current=str(index + 1), total=str(total))
                        if kwargs.catalog["progress"]
                        else kwargs.labels["progress"]
                        .replace("{current}", str(index + 1))
                        .replace("{total}", str(total))
                    ),
                    "progress_current": str(index + 1),
                    "progress_total": str(total),
                    "progress_values": f"{{ current: '{index + 1}', total: '{total}' }}",
                    "step_positions": list(range(total)),
                    "title": Slot(
                        lambda ctx, d=declaration, sd=slot_data: d.title(sd, provides=dict(ctx.provides or {}))
                    ),
                    "content": Slot(
                        lambda ctx, d=declaration, sd=slot_data: d.content(sd, provides=dict(ctx.provides or {}))
                    ),
                    "media": (
                        Slot(lambda ctx, d=declaration, sd=slot_data: d.media(sd, provides=dict(ctx.provides or {})))
                        if declaration.media is not None
                        else None
                    ),
                    "morph_key": f"tour-step-{declaration.value}",
                }
            )
        return {
            "root_id": kwargs.root_id,
            "dialog_id": kwargs.dialog_id,
            "open": kwargs.open,
            "active": kwargs.active,
            "active_value": kwargs.registry.steps[kwargs.active].value,
            "active_title_id": items[kwargs.active]["title_id"],
            "active_description_id": (
                items[kwargs.active]["description_id"] if kwargs.registry.steps[kwargs.active].describe else None
            ),
            "dismissible": kwargs.dismissible,
            "skippable": kwargs.skippable,
            "size": kwargs.size,
            "labels": kwargs.labels,
            "catalog": kwargs.catalog,
            "attrs": kwargs.attrs,
            "items": items,
            "activator": kwargs.activator,
            "close": kwargs.close,
        }

    template = """
      <div
        class="cui-tour"
        c-id="root_id"
        c-bind="attrs"
        c-data-open="open"
        c-data-active="active"
        c-data-value="active_value"
        c-data-size="size"
        data-citry-tour-host
        data-citry-ui-part="tour"
      >
        <c-if cond="activator is not None">{{ activator }}</c-if>
        <dialog
          class="cui-tour__dialog"
          c-id="dialog_id"
          c-open="open"
          c-aria-labelledby="active_title_id"
          c-aria-describedby="active_description_id"
          aria-modal="false"
          c-data-open="open"
          data-citry-tour-dialog
          data-citry-ui-part="dialog"
        >
          <div class="cui-tour__spotlight" hidden aria-hidden="true" data-citry-ui-part="spotlight"></div>
          <div class="cui-tour__surface" c-data-size="size" data-placement="center" data-citry-ui-part="surface">
            <button
              type="button"
              c-hidden="not dismissible"
              c-aria-label="tr('citry-ui-tour-close') if catalog['close'] else labels['close']"
              c-$c-tr:citry-ui-tour-close[aria-label]="True if catalog['close'] else None"
              data-citry-tour-action="close"
              data-citry-ui-part="close"
            >
              <c-if cond="close is not None">{{ close }}</c-if>
              <c-else><span aria-hidden="true">&times;</span></c-else>
            </button>
            <c-for each="item in items">
              <c-CInternalTourStep
                c-item="item"
                c-skippable="skippable"
                c-labels="labels"
                c-catalog="catalog"
              />
            </c-for>
          </div>
        </dialog>
      </div>
    """


class CInternalTourStep(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        item: dict[str, object]
        skippable: bool
        labels: dict[str, str]
        catalog: dict[str, bool]

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        item = kwargs.item
        declaration = cast("_TourDeclaration", item["declaration"])
        index = cast("int", item["index"])
        total = cast("int", item["total"])
        return {
            **item,
            "attrs": {
                **declaration.attrs,
                "data-index": index,
                "data-value": declaration.value,
                "data-target-id": declaration.target_id,
                "data-placement": declaration.placement,
                "data-describe": "true" if declaration.describe else "false",
                "data-current": bool(item["active"]),
            },
            "target_id": declaration.target_id,
            "placement": declaration.placement,
            "describe": declaration.describe,
            "arrow": declaration.arrow and declaration.target_id is not None,
            "is_first": index == 0,
            "is_last": index == total - 1,
            "skippable": kwargs.skippable,
            "labels": kwargs.labels,
            "catalog": kwargs.catalog,
        }

    template = """
      <section
        class="cui-tour__panel"
        #c-key="morph_key"
        c-bind="attrs"
        c-hidden="not active"
        c-inert="not active"
        data-citry-tour-panel
        data-citry-ui-part="panel"
      >
        <c-if cond="media is not None"><div data-citry-ui-part="media">{{ media }}</div></c-if>
        <header data-citry-ui-part="header">
          <h2 c-id="title_id" tabindex="-1" data-citry-ui-part="title">{{ title }}</h2>
        </header>
        <div c-id="description_id" data-citry-ui-part="description">{{ content }}</div>
        <span c-hidden="not arrow" aria-hidden="true" data-citry-ui-part="arrow"></span>
        <footer data-citry-ui-part="footer">
          <div data-citry-ui-part="progress-group">
            <c-if cond="catalog['progress']">
              <span
                c-$c-tr:citry-ui-tour-progress="progress_values"
                aria-live="polite"
                data-citry-ui-part="progress"
              >{{ tr('citry-ui-tour-progress', current=progress_current, total=progress_total) }}</span>
            </c-if>
            <c-else><span aria-live="polite" data-citry-ui-part="progress">{{ progress }}</span></c-else>
            <span aria-hidden="true" data-citry-ui-part="steps">
              <c-for each="step_position in step_positions">
                <span c-data-current="step_position == index" data-citry-ui-part="step-dot"></span>
              </c-for>
            </span>
          </div>
          <div data-citry-ui-part="actions">
            <button
              type="button"
              c-hidden="not skippable"
              c-$c-tr:citry-ui-tour-skip="True if catalog['skip'] else None"
              data-citry-tour-action="skip"
            >{{ tr('citry-ui-tour-skip') if catalog['skip'] else labels['skip'] }}</button>
            <button
              type="button"
              c-hidden="is_first"
              c-$c-tr:citry-ui-tour-previous="True if catalog['previous'] else None"
              data-citry-tour-action="previous"
            >{{ tr('citry-ui-tour-previous') if catalog['previous'] else labels['previous'] }}</button>
            <button
              type="button"
              c-hidden="is_last"
              c-$c-tr:citry-ui-tour-next="True if catalog['next'] else None"
              data-citry-tour-action="next"
            >{{ tr('citry-ui-tour-next') if catalog['next'] else labels['next'] }}</button>
            <button
              type="button"
              c-hidden="not is_last"
              c-$c-tr:citry-ui-tour-finish="True if catalog['finish'] else None"
              data-citry-tour-action="finish"
            >{{ tr('citry-ui-tour-finish') if catalog['finish'] else labels['finish'] }}</button>
          </div>
        </footer>
      </section>
    """


__all__ = [
    "CTour",
    "CTourActivatorSlotData",
    "CTourActiveChangeDetail",
    "CTourActiveReason",
    "CTourCloseSlotData",
    "CTourDefaultSlotData",
    "CTourMissingTarget",
    "CTourOpenChangeDetail",
    "CTourOpenReason",
    "CTourPlacement",
    "CTourScroll",
    "CTourSize",
    "CTourStep",
    "CTourStepDefaultSlotData",
    "CTourStepMediaSlotData",
    "CTourStepSlotData",
    "CTourStepTitleSlotData",
]
