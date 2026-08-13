"""Native-scroll content Carousel component family."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, Literal, TypedDict, overload

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._scroll_geometry import SCROLL_GEOMETRY_RUNTIME_DEPENDENCY
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CCarouselOrientation = Literal["horizontal", "vertical"]
CCarouselVariant = Literal["plain", "surface"]
CCarouselSize = Literal["sm", "md", "lg"]


class CCarouselIndexChangeDetail(TypedDict):
    index: int
    previousIndex: int
    value: str
    reason: Literal["previous", "next", "picker", "scroll", "structure"]
    controlled: bool
    forced: bool
    source: object | None


class CCarouselDefaultSlotData:
    pass


class CCarouselSlideDefaultSlotData:
    pass


_CONTEXT_KEY = "citry_ui_carousel"
_ORIENTATIONS = ("horizontal", "vertical")
_VARIANTS = ("plain", "surface")
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-citry-carousel-initialized",
        "data-citry-carousel-root",
        "data-citry-ui-part",
        "data-disabled",
        "data-draggable",
        "data-index",
        "data-loop",
        "data-orientation",
        "data-size",
        "data-variant",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_SLIDE_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-active",
        "data-citry-carousel-slide",
        "data-citry-ui-part",
        "data-index",
        "data-value",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)


@dataclass(slots=True)
class _CarouselContext:
    selected_index: int
    count: int = 0
    values: set[str] = field(default_factory=set)


@overload
def _plain(name: str, value: object, *, optional: Literal[False] = False) -> str: ...


@overload
def _plain(name: str, value: object, *, optional: Literal[True]) -> str | None: ...


def _plain(name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        raise TypeError(f"{name} must be a string{' or None' if optional else ''}, got {raw!r}.")
    plain = "".join(raw)
    if not plain.strip() or "\x00" in plain:
        raise ValueError(f"{name} must be nonempty and cannot contain U+0000.")
    return plain


def _html_id(name: str, value: object, fallback: str) -> str:
    plain = _plain(name, value, optional=True) or fallback
    if any(character in "\t\n\f\r " for character in plain):
        raise ValueError(f"{name} cannot contain ASCII whitespace.")
    return plain


def _index(name: str, value: object) -> int:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError(f"{name} must be a nonnegative integer, got {raw!r}.")
    if raw < 0:
        raise ValueError(f"{name} must be nonnegative, got {raw!r}.")
    return raw


def _choice(component: str, name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(f"{component} {name}", value)
    if plain not in allowed:
        raise ValueError(f"{component} {name} must be one of {allowed!r}, got {plain!r}.")
    return plain


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(component: str, value: Mapping[str, object] | None, owned: frozenset[str]) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"{component} attrs must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, owned, f"{component} attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"{component} attrs cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _DIRECTIVES:
            raise ValueError(f"{component} attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in owned:
            raise ValueError(f"{component} attrs cannot dynamically bind owned attribute {key!r}.")
    return copied


class CCarousel(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    class Dependencies:
        js: ClassVar = [SCROLL_GEOMETRY_RUNTIME_DEPENDENCY]

    @dataclass(slots=True)
    class Kwargs:
        label: str
        id: str | None = None
        index: int = 0
        orientation: CCarouselOrientation = "horizontal"
        loop: bool = False
        disabled: bool = False
        controls: bool = True
        indicators: bool = True
        draggable: bool = True
        variant: CCarouselVariant = "plain"
        size: CCarouselSize = "md"
        previous_label: str = "Previous slide"
        next_label: str = "Next slide"
        picker_label: str = "Choose slide"
        role_description: str | None = "carousel"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CCarouselDefaultSlotData]

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_carousel_snapshot", None)
        if cached is not None:
            return cached
        root_id = _html_id("CCarousel id", kwargs.id, f"cui-carousel-{self.id}")
        selected_index = _index("CCarousel index", kwargs.index)
        orientation = _choice("CCarousel", "orientation", kwargs.orientation, _ORIENTATIONS)
        variant = _choice("CCarousel", "variant", kwargs.variant, _VARIANTS)
        size = _choice("CCarousel", "size", kwargs.size, _SIZES)
        for name in ("loop", "disabled", "controls", "indicators", "draggable"):
            validate_boolean("CCarousel", name, getattr(kwargs, name))
        context = _CarouselContext(selected_index=selected_index)
        self.provide(_CONTEXT_KEY, context=context)
        self._carousel_context = context
        snapshot: dict[str, object] = {
            "root_id": root_id,
            "label": _plain("CCarousel label", kwargs.label),
            "index": selected_index,
            "orientation": orientation,
            "loop": bool(kwargs.loop),
            "disabled": bool(kwargs.disabled),
            "controls": bool(kwargs.controls),
            "indicators": bool(kwargs.indicators),
            "draggable": bool(kwargs.draggable),
            "variant": variant,
            "size": size,
            "previous_label": _plain(
                "CCarousel previous_label",
                kwargs.previous_label
                if "previous_label" in self.raw_kwargs
                else self.i18n.tr("citry-ui-carousel-previous"),
            ),
            "catalog_previous_label": uses_catalog_default(self, "previous_label"),
            "next_label": _plain(
                "CCarousel next_label",
                kwargs.next_label if "next_label" in self.raw_kwargs else self.i18n.tr("citry-ui-carousel-next"),
            ),
            "catalog_next_label": uses_catalog_default(self, "next_label"),
            "picker_label": _plain(
                "CCarousel picker_label",
                kwargs.picker_label if "picker_label" in self.raw_kwargs else self.i18n.tr("citry-ui-carousel-picker"),
            ),
            "catalog_picker_label": uses_catalog_default(self, "picker_label"),
            "role_description": _plain(
                "CCarousel role_description",
                kwargs.role_description
                if "role_description" in self.raw_kwargs
                else self.i18n.tr("citry-ui-carousel-role"),
                optional=True,
            ),
            "catalog_role_description": uses_catalog_default(self, "role_description"),
            "attrs": merge_root_attrs(
                _attrs("CCarousel", kwargs.attrs, _ROOT_OWNED),
                kwargs.class_,
                kwargs.style,
            ),
        }
        self._cui_carousel_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "index": snapshot["index"],
            "orientation": snapshot["orientation"],
            "loop": snapshot["loop"],
            "disabled": snapshot["disabled"],
            "controls": snapshot["controls"],
            "indicators": snapshot["indicators"],
            "draggable": snapshot["draggable"],
            "variant": snapshot["variant"],
            "size": snapshot["size"],
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            raise RuntimeError("CCarousel completed without a render result.")
        context = self._carousel_context
        if context.count == 0:
            raise ValueError("CCarousel requires at least one direct CCarouselSlide.")
        if context.selected_index >= context.count:
            raise ValueError(f"CCarousel index {context.selected_index} is outside its {context.count} Slides.")

    template = """
      <section
        class="cui-carousel"
        c-id="root_id"
        c-bind="attrs"
        role="region"
        c-aria-label="label"
        c-aria-roledescription="tr('citry-ui-carousel-role') if catalog_role_description else role_description"
        c-$c-tr:citry-ui-carousel-role[aria-roledescription]="True if catalog_role_description else None"
        c-data-index="index"
        c-data-orientation="orientation"
        c-data-loop="loop"
        c-data-disabled="disabled"
        c-data-draggable="draggable"
        c-data-variant="variant"
        c-data-size="size"
        data-citry-carousel-root
        data-citry-ui-part="carousel"
      >
        <div c-hidden="not controls" data-citry-ui-part="controls">
          <button
            type="button"
            c-aria-label="tr('citry-ui-carousel-previous') if catalog_previous_label else previous_label"
            c-$c-tr:citry-ui-carousel-previous[aria-label]="True if catalog_previous_label else None"
            c-disabled="disabled or (index == 0 and not loop)"
            data-citry-carousel-previous
            data-citry-ui-part="previous"
          ><span aria-hidden="true">&#x2190;</span></button>
          <button
            type="button"
            c-aria-label="tr('citry-ui-carousel-next') if catalog_next_label else next_label"
            c-$c-tr:citry-ui-carousel-next[aria-label]="True if catalog_next_label else None"
            c-disabled="disabled"
            data-citry-carousel-next
            data-citry-ui-part="next"
          ><span aria-hidden="true">&#x2192;</span></button>
        </div>
        <div tabindex="0" data-citry-carousel-viewport data-citry-ui-part="viewport">
          <div data-citry-ui-part="track"><c-slot required /></div>
        </div>
        <div
          c-hidden="not indicators"
          role="group"
          c-aria-label="tr('citry-ui-carousel-picker') if catalog_picker_label else picker_label"
          c-$c-tr:citry-ui-carousel-picker[aria-label]="True if catalog_picker_label else None"
          data-citry-carousel-indicators
          data-citry-ui-part="indicators"
        ></div>
      </section>
    """

    js = """
      $component({
        props: {
          index: {},
          orientation: {},
          loop: {},
          disabled: {},
          controls: {},
          indicators: {},
          draggable: {},
          variant: {},
          size: {},
          onIndexChange: {},
        },
        init: ({ els, data, props, effect }) => {
          const root = els[0];
          const geometry = globalThis[Symbol.for("citry-ui:scroll-geometry")];
          if (geometry?.generation !== 1) {
            throw new Error("[citry-ui] CCarousel scroll geometry dependency did not load.");
          }
          const viewport = root.querySelector("[data-citry-carousel-viewport]");
          const track = viewport?.querySelector(':scope > [data-citry-ui-part="track"]');
          const previousButton = root.querySelector("[data-citry-carousel-previous]");
          const nextButton = root.querySelector("[data-citry-carousel-next]");
          const controls = root.querySelector(':scope > [data-citry-ui-part="controls"]');
          const indicators = root.querySelector("[data-citry-carousel-indicators]");
          if (!viewport || !track || !previousButton || !nextButton || !controls || !indicators) {
            throw new Error("[citry-ui] CCarousel requires its owned controls, viewport, track, and indicators.");
          }
          const handoffKey = Symbol.for("citry-ui:carousel-handoff");
          const previous = root[handoffKey];
          delete root[handoffKey];
          let active = true;
          let controlled = false;
          let internalIndex = previous?.serverIndex === data.index ? previous.index : data.index;
          let effectiveIndex = -1;
          let onIndexChange = null;
          let slides = [];
          let invalidStructure = false;
          let scrollFrame = null;
          let scrollTimer = null;
          let suppressionTimer = null;
          let reconcileFrame = null;
          let suppressScroll = false;
          let drag = null;
          let configuration = {
            orientation: data.orientation,
            loop: data.loop,
            disabled: data.disabled,
            controls: data.controls,
            indicators: data.indicators,
            draggable: data.draggable,
            variant: data.variant,
            size: data.size,
          };
          const invalidEpisodes = new Set();

          const reportInvalid = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CCarousel ${name} received invalid client value.`, value, root);
          };
          const resolveBoolean = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return data[name];
          };
          const resolveChoice = (name, allowed) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (allowed.includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return data[name];
          };
          const resolveCallback = () => {
            const value = props.onIndexChange;
            if (value === undefined || value === null || typeof value === "function") {
              invalidEpisodes.delete("onIndexChange");
              return value ?? null;
            }
            reportInvalid("onIndexChange", value);
            return null;
          };
          const collect = () => {
            const children = [...track.children];
            const next = children.filter((element) => element.matches("[data-citry-carousel-slide]"));
            const values = new Set();
            let valid = next.length > 0 && next.length === children.length;
            next.forEach((slide, index) => {
              const value = slide.dataset.value;
              if (!value || values.has(value)) valid = false;
              values.add(value);
              slide.dataset.index = String(index);
            });
            slides = next;
            invalidStructure = !valid;
            if (!valid) reportInvalid("structure", children.length);
            else invalidEpisodes.delete("structure");
          };
          const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
          const horizontalMaximum = () => geometry.maximum(viewport.scrollWidth, viewport.clientWidth);
          const horizontalRtl = () => getComputedStyle(viewport).direction === "rtl";
          const horizontalPosition = () => geometry.horizontalFromRaw(
            viewport.scrollLeft,
            horizontalMaximum(),
            horizontalRtl(),
          );
          const horizontalRaw = (position) => geometry.horizontalToRaw(
            position,
            horizontalMaximum(),
            horizontalRtl(),
          );
          const horizontalSlidePosition = (slide) => Math.abs(slide.offsetLeft - track.offsetLeft);
          const scrollPosition = (index) => {
            const slide = slides[index];
            if (!slide) return 0;
            return configuration.orientation === "horizontal"
              ? horizontalSlidePosition(slide)
              : slide.offsetTop - track.offsetTop;
          };
          const scrollToIndex = (index, instant = false) => {
            const position = scrollPosition(index);
            const currentPosition = configuration.orientation === "horizontal"
              ? horizontalPosition()
              : viewport.scrollTop;
            if (Math.abs(currentPosition - position) <= 1) {
              suppressScroll = false;
              return;
            }
            suppressScroll = true;
            viewport.scrollTo({
              left: configuration.orientation === "horizontal" ? horizontalRaw(position) : 0,
              top: configuration.orientation === "vertical" ? position : 0,
              behavior: instant || reducedMotion() ? "instant" : "smooth",
            });
            clearTimeout(suppressionTimer);
            suppressionTimer = setTimeout(() => { suppressScroll = false; }, instant ? 0 : 350);
          };
          const syncIndicators = () => {
            indicators.replaceChildren();
            slides.forEach((slide, index) => {
              const button = document.createElement("button");
              button.type = "button";
              button.dataset.citryUiPart = "indicator";
              button.dataset.index = String(index);
              button.setAttribute(
                "aria-label",
                slide.getAttribute("aria-label") ?? slide.dataset.value ?? String(index + 1),
              );
              indicators.append(button);
            });
          };
          const apply = (index, { scroll = false, instant = false } = {}) => {
            const next = invalidStructure || slides.length === 0
              ? -1
              : Math.min(Math.max(index, 0), slides.length - 1);
            effectiveIndex = next;
            root.dataset.orientation = configuration.orientation;
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            root.toggleAttribute("data-loop", configuration.loop);
            root.toggleAttribute("data-disabled", configuration.disabled);
            root.toggleAttribute("data-draggable", configuration.draggable);
            if (next < 0) delete root.dataset.index;
            else root.dataset.index = String(next);
            controls.hidden = !configuration.controls;
            indicators.hidden = !configuration.indicators;
            previousButton.disabled = configuration.disabled || (!configuration.loop && next <= 0);
            nextButton.disabled = configuration.disabled || (!configuration.loop && next >= slides.length - 1);
            slides.forEach((slide, slideIndex) => slide.toggleAttribute("data-active", slideIndex === next));
            [...indicators.children].forEach((button, buttonIndex) => {
              button.toggleAttribute("aria-current", buttonIndex === next);
              button.disabled = configuration.disabled;
            });
            if (scroll && next >= 0) scrollToIndex(next, instant);
          };
          const notify = (index, previousIndex, reason, source, forced = false) => {
            onIndexChange?.(index, {
              index,
              previousIndex,
              value: slides[index]?.dataset.value ?? "",
              reason,
              controlled,
              forced,
              source,
            });
          };
          const request = (requested, reason, source, forced = false) => {
            if (!slides.length || configuration.disabled) return;
            let next = requested;
            if (configuration.loop) next = (next + slides.length) % slides.length;
            else next = Math.min(Math.max(next, 0), slides.length - 1);
            const previousIndex = effectiveIndex;
            if (next === previousIndex) return;
            if (!controlled || forced) {
              internalIndex = next;
              apply(next, { scroll: true });
            }
            notify(next, previousIndex, reason, source, forced);
          };
          const nearestIndex = () => {
            const position = configuration.orientation === "horizontal" ? horizontalPosition() : viewport.scrollTop;
            let best = 0;
            let distance = Number.POSITIVE_INFINITY;
            slides.forEach((slide, index) => {
              const candidate = configuration.orientation === "horizontal"
                ? horizontalSlidePosition(slide)
                : slide.offsetTop - track.offsetTop;
              const currentDistance = Math.abs(position - candidate);
              if (currentDistance < distance) {
                best = index;
                distance = currentDistance;
              }
            });
            return best;
          };
          const settleScroll = () => {
            scrollFrame = null;
            if (!active || suppressScroll || drag) return;
            const next = nearestIndex();
            if (next === effectiveIndex) return;
            const previousIndex = effectiveIndex;
            if (controlled) scrollToIndex(effectiveIndex);
            else {
              internalIndex = next;
              apply(next);
            }
            notify(next, previousIndex, "scroll", viewport);
          };
          const onScroll = () => {
            if (scrollFrame !== null) cancelAnimationFrame(scrollFrame);
            clearTimeout(scrollTimer);
            scrollTimer = setTimeout(() => {
              scrollFrame = requestAnimationFrame(settleScroll);
            }, 90);
          };
          const onClick = (event) => {
            if (configuration.disabled) return;
            const path = event.composedPath();
            if (path.includes(previousButton)) request(effectiveIndex - 1, "previous", previousButton);
            else if (path.includes(nextButton)) request(effectiveIndex + 1, "next", nextButton);
            else {
              const picker = path.find((element) => element?.matches?.('[data-citry-ui-part="indicator"]'));
              if (picker && indicators.contains(picker)) request(Number(picker.dataset.index), "picker", picker);
            }
          };
          const axisPosition = (event) => configuration.orientation === "horizontal" ? event.clientX : event.clientY;
          const axisScroll = () => configuration.orientation === "horizontal"
            ? horizontalPosition()
            : viewport.scrollTop;
          const onPointerDown = (event) => {
            if (
              !configuration.draggable
              || configuration.disabled
              || event.button !== 0
              || event.pointerType === "touch"
            ) return;
            drag = { id: event.pointerId, start: axisPosition(event), scroll: axisScroll() };
            viewport.setPointerCapture(event.pointerId);
            viewport.toggleAttribute("data-dragging", true);
          };
          const onPointerMove = (event) => {
            if (!drag || drag.id !== event.pointerId) return;
            const position = drag.scroll + drag.start - axisPosition(event);
            if (configuration.orientation === "horizontal") viewport.scrollLeft = horizontalRaw(position);
            else viewport.scrollTop = position;
            event.preventDefault();
          };
          const onPointerEnd = (event) => {
            if (!drag || drag.id !== event.pointerId) return;
            drag = null;
            viewport.toggleAttribute("data-dragging", false);
            if (viewport.hasPointerCapture(event.pointerId)) viewport.releasePointerCapture(event.pointerId);
            requestAnimationFrame(settleScroll);
          };
          const reconcile = () => {
            reconcileFrame = null;
            const previousSlides = slides;
            const previousValue = previousSlides[effectiveIndex]?.dataset.value ?? null;
            const previousIndex = effectiveIndex;
            collect();
            syncIndicators();
            if (invalidStructure) {
              apply(-1);
              return;
            }
            let next = previousValue === null
              ? internalIndex
              : slides.findIndex((slide) => slide.dataset.value === previousValue);
            let forced = false;
            if (next < 0) {
              next = Math.min(previousIndex, slides.length - 1);
              forced = previousIndex >= 0;
            }
            if (!controlled) internalIndex = next;
            apply(controlled ? effectiveIndex : next, { scroll: true, instant: true });
            if (forced) notify(next, previousIndex, "structure", root, true);
          };
          const scheduleReconcile = () => {
            if (reconcileFrame !== null) return;
            reconcileFrame = requestAnimationFrame(reconcile);
          };
          const observer = new MutationObserver(scheduleReconcile);
          observer.observe(track, { childList: true });
          const resizeObserver = new ResizeObserver(() => {
            if (effectiveIndex >= 0) scrollToIndex(effectiveIndex, true);
          });
          resizeObserver.observe(viewport);
          root.addEventListener("click", onClick, true);
          viewport.addEventListener("scroll", onScroll, { passive: true });
          viewport.addEventListener("pointerdown", onPointerDown);
          viewport.addEventListener("pointermove", onPointerMove);
          viewport.addEventListener("pointerup", onPointerEnd);
          viewport.addEventListener("pointercancel", onPointerEnd);
          collect();
          syncIndicators();

          effect(() => {
            configuration = {
              orientation: resolveChoice("orientation", ["horizontal", "vertical"]),
              loop: resolveBoolean("loop"),
              disabled: resolveBoolean("disabled"),
              controls: resolveBoolean("controls"),
              indicators: resolveBoolean("indicators"),
              draggable: resolveBoolean("draggable"),
              variant: resolveChoice("variant", ["plain", "surface"]),
              size: resolveChoice("size", ["sm", "md", "lg"]),
            };
            onIndexChange = resolveCallback();
            const supplied = props.index !== undefined;
            let next = internalIndex;
            if (supplied) {
              if (Number.isInteger(props.index) && props.index >= 0 && props.index < slides.length) {
                controlled = true;
                invalidEpisodes.delete("index");
                next = props.index;
                internalIndex = props.index;
              } else {
                controlled = false;
                reportInvalid("index", props.index);
              }
            } else {
              controlled = false;
              invalidEpisodes.delete("index");
            }
            apply(next, { scroll: true, instant: effectiveIndex < 0 });
            root.setAttribute("data-citry-carousel-initialized", "");
          });

          return () => {
            active = false;
            clearTimeout(scrollTimer);
            clearTimeout(suppressionTimer);
            cancelAnimationFrame(scrollFrame);
            cancelAnimationFrame(reconcileFrame);
            observer.disconnect();
            resizeObserver.disconnect();
            root.removeEventListener("click", onClick, true);
            viewport.removeEventListener("scroll", onScroll);
            viewport.removeEventListener("pointerdown", onPointerDown);
            viewport.removeEventListener("pointermove", onPointerMove);
            viewport.removeEventListener("pointerup", onPointerEnd);
            viewport.removeEventListener("pointercancel", onPointerEnd);
            root[handoffKey] = { index: internalIndex, serverIndex: data.index };
            root.removeAttribute("data-citry-carousel-initialized");
          };
        },
      });
    """

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="carousel"]) {
          --_cui-carousel-background: var(--cui-carousel-background, transparent);
          --_cui-carousel-foreground: var(--cui-carousel-foreground, CanvasText);
          --_cui-carousel-border-color: var(--cui-carousel-border-color, light-dark(#e7e5e4, #44403c));
          --_cui-carousel-radius: var(--cui-carousel-radius, 0.9rem);
          --_cui-carousel-gap: var(--cui-carousel-gap, 1rem);
          --_cui-carousel-padding: var(--cui-carousel-padding, 0.75rem);
          --_cui-carousel-block-size: var(--cui-carousel-block-size, 20rem);
          --_cui-carousel-control-background: var(--cui-carousel-control-background, light-dark(#f5f5f4, #292524));
          --_cui-carousel-control-foreground: var(--cui-carousel-control-foreground, CanvasText);
          --_cui-carousel-control-size: var(--cui-carousel-control-size, 2.5rem);
          --_cui-carousel-focus-color: var(--cui-carousel-focus-color, Highlight);
          --_cui-carousel-indicator-size: var(--cui-carousel-indicator-size, 0.65rem);
          --_cui-carousel-indicator-color: var(--cui-carousel-indicator-color, light-dark(#a8a29e, #78716c));
          --_cui-carousel-indicator-active-color: var(--cui-carousel-indicator-active-color, Highlight);
          --_cui-carousel-duration: var(--cui-carousel-duration, 260ms);
          --_cui-carousel-easing: var(--cui-carousel-easing, ease-out);
          display: grid;
          gap: var(--_cui-carousel-gap);
          min-inline-size: 0;
          padding: var(--_cui-carousel-padding);
          color: var(--_cui-carousel-foreground);
          background: var(--_cui-carousel-background);
        }
        :where([data-citry-ui-part="carousel"][data-variant="surface"]) {
          border: 1px solid var(--_cui-carousel-border-color);
          border-radius: var(--_cui-carousel-radius);
          background: light-dark(#fafaf9, #1c1917);
        }
        :where([data-citry-ui-part="carousel"] > [data-citry-ui-part="controls"]) {
          display: flex;
          justify-content: end;
          gap: 0.45rem;
        }
        :where([data-citry-ui-part="carousel"] > [data-citry-ui-part="controls"][hidden]),
        :where([data-citry-ui-part="carousel"] > [data-citry-ui-part="indicators"][hidden]) {
          display: none !important;
        }
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="previous"]),
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="next"]) {
          display: inline-grid;
          place-items: center;
          inline-size: var(--_cui-carousel-control-size);
          block-size: var(--_cui-carousel-control-size);
          padding: 0;
          border: 1px solid var(--_cui-carousel-border-color);
          border-radius: 999px;
          color: var(--_cui-carousel-control-foreground);
          background: var(--_cui-carousel-control-background);
          font: inherit;
          font-size: 1.25rem;
          cursor: pointer;
        }
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="previous"]:disabled),
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="next"]:disabled) {
          opacity: 0.45;
          cursor: not-allowed;
        }
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="viewport"]) {
          min-inline-size: 0;
          overflow: auto;
          overscroll-behavior: contain;
          scrollbar-width: none;
          scroll-behavior: smooth;
          scroll-snap-type: inline mandatory;
          border-radius: var(--_cui-carousel-radius);
          cursor: grab;
        }
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="viewport"]::-webkit-scrollbar) {
          display: none;
        }
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="viewport"][data-dragging]) {
          cursor: grabbing;
          user-select: none;
          scroll-snap-type: none;
        }
        :where([data-citry-ui-part="carousel"][data-orientation="vertical"] [data-citry-ui-part="viewport"]) {
          block-size: var(--_cui-carousel-block-size);
          scroll-snap-type: block mandatory;
        }
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="track"]) {
          display: flex;
          gap: var(--_cui-carousel-gap);
          margin: 0;
          padding: 0;
          list-style: none;
        }
        :where([data-citry-ui-part="carousel"][data-orientation="vertical"] [data-citry-ui-part="track"]) {
          flex-direction: column;
          min-block-size: 100%;
        }
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="slide"]) {
          box-sizing: border-box;
          flex: 0 0 100%;
          min-inline-size: 0;
          overflow-wrap: anywhere;
          scroll-snap-align: start;
        }
        :where([data-citry-ui-part="carousel"][data-orientation="vertical"] [data-citry-ui-part="slide"]) {
          min-block-size: var(--_cui-carousel-block-size);
        }
        :where([data-citry-ui-part="carousel"] > [data-citry-ui-part="indicators"]) {
          display: flex;
          justify-content: center;
          gap: 0.55rem;
        }
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="indicator"]) {
          inline-size: var(--_cui-carousel-indicator-size);
          block-size: var(--_cui-carousel-indicator-size);
          padding: 0;
          border: 0;
          border-radius: 999px;
          background: var(--_cui-carousel-indicator-color);
          cursor: pointer;
        }
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="indicator"][aria-current]) {
          background: var(--_cui-carousel-indicator-active-color);
          outline: 1px solid Canvas;
          outline-offset: -2px;
        }
        :where([data-citry-ui-part="carousel"] button:focus-visible),
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="viewport"]:focus-visible),
        :where([data-citry-ui-part="carousel"] [data-citry-ui-part="slide"] :focus-visible) {
          outline: 3px solid var(--_cui-carousel-focus-color);
          outline-offset: 2px;
        }
        :where([data-citry-ui-part="carousel"][data-size="sm"]) {
          --_cui-carousel-gap: 0.7rem;
          --_cui-carousel-padding: 0.55rem;
          --_cui-carousel-control-size: 2.15rem;
          font-size: 0.875rem;
        }
        :where([data-citry-ui-part="carousel"][data-size="lg"]) {
          --_cui-carousel-gap: 1.25rem;
          --_cui-carousel-padding: 1rem;
          --_cui-carousel-control-size: 2.85rem;
          font-size: 1.0625rem;
        }
        @media (prefers-reduced-motion: reduce) {
          :where([data-citry-ui-part="carousel"] [data-citry-ui-part="viewport"]) {
            scroll-behavior: auto;
          }
          :where([data-citry-ui-part="carousel"]) {
            --_cui-carousel-duration: 0ms;
          }
        }
        @media (forced-colors: active) {
          :where([data-citry-ui-part="carousel"][data-variant="surface"]),
          :where([data-citry-ui-part="carousel"] [data-citry-ui-part="previous"]),
          :where([data-citry-ui-part="carousel"] [data-citry-ui-part="next"]) {
            border-color: CanvasText;
          }
          :where([data-citry-ui-part="carousel"] [data-citry-ui-part="indicator"][aria-current]) {
            background: Highlight;
          }
        }
        @media print {
          :where([data-citry-ui-part="carousel"] > [data-citry-ui-part="controls"]),
          :where([data-citry-ui-part="carousel"] > [data-citry-ui-part="indicators"]) {
            display: none !important;
          }
          :where([data-citry-ui-part="carousel"] [data-citry-ui-part="viewport"]) {
            block-size: auto;
            overflow: visible;
          }
          :where([data-citry-ui-part="carousel"] [data-citry-ui-part="track"]) {
            display: grid;
          }
          :where([data-citry-ui-part="carousel"] [data-citry-ui-part="slide"]) {
            min-block-size: 0;
            break-inside: avoid;
          }
        }
      }
    """

    messages = """
      citry-ui-carousel-previous = Previous slide
      citry-ui-carousel-next = Next slide
      citry-ui-carousel-picker = Choose slide
      citry-ui-carousel-role = carousel
    """


class CCarouselSlide(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        value: str
        label: str
        role_description: str | None = "slide"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CCarouselSlideDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        provided = self.inject(_CONTEXT_KEY, None)
        if provided is None:
            raise ValueError("CCarouselSlide must be rendered directly inside CCarousel.")
        context: _CarouselContext = provided.context
        value = _plain("CCarouselSlide value", kwargs.value)
        if value in context.values:
            raise ValueError(f"CCarouselSlide value {value!r} is duplicated.")
        index = context.count
        context.count += 1
        context.values.add(value)
        self.unprovide(_CONTEXT_KEY)
        return {
            "value": value,
            "label": _plain("CCarouselSlide label", kwargs.label),
            "index": index,
            "active": index == context.selected_index,
            "role_description": _plain(
                "CCarouselSlide role_description",
                kwargs.role_description
                if "role_description" in self.raw_kwargs
                else self.i18n.tr("citry-ui-carousel-slide-role"),
                optional=True,
            ),
            "catalog_role_description": uses_catalog_default(self, "role_description"),
            "attrs": merge_root_attrs(
                _attrs("CCarouselSlide", kwargs.attrs, _SLIDE_OWNED),
                kwargs.class_,
                kwargs.style,
            ),
        }

    template = """
      <div
        class="cui-carousel__slide"
        c-bind="attrs"
        role="group"
        c-aria-label="label"
        c-aria-roledescription="tr('citry-ui-carousel-slide-role') if catalog_role_description else role_description"
        c-$c-tr:citry-ui-carousel-slide-role[aria-roledescription]="True if catalog_role_description else None"
        c-data-value="value"
        c-data-index="index"
        c-data-active="active"
        data-citry-carousel-slide
        data-citry-ui-part="slide"
      ><c-slot required /></div>
    """

    messages = """
      citry-ui-carousel-slide-role = slide
    """


__all__ = [
    "CCarousel",
    "CCarouselDefaultSlotData",
    "CCarouselIndexChangeDetail",
    "CCarouselOrientation",
    "CCarouselSize",
    "CCarouselSlide",
    "CCarouselSlideDefaultSlotData",
    "CCarouselVariant",
]
