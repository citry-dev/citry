"""Accessible multi-panel percentage Splitter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Literal, TypedDict, cast

from citry import CitryRender, LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CSplitterOrientation = Literal["horizontal", "vertical"]
CSplitterVariant = Literal["plain", "soft", "outline"]
CSplitterSize = Literal["sm", "md", "lg"]
CSplitterResizeSource = Literal["pointer", "keyboard"]

_ORIENTATIONS = ("horizontal", "vertical")
_VARIANTS = ("plain", "soft", "outline")
_SIZES = ("sm", "md", "lg")
_CONTEXT = "citry_ui_splitter"
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-hidden",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-orientation",
        "data-resizing",
        "data-size",
        "data-variant",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)
_PANEL_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "contenteditable",
        "data-citry-ui-part",
        "data-index",
        "data-panel-id",
        "data-size-percent",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)


class CSplitterDefaultSlotData:
    pass


class CSplitterPanelDefaultSlotData(TypedDict):
    id: str
    index: int
    size: float
    is_first: bool
    is_last: bool


class CSplitterResizeDetail(TypedDict):
    sizes: list[float]
    previousSizes: list[float]
    handleIndex: int
    controlled: bool
    source: CSplitterResizeSource
    sourceEvent: object


@dataclass(frozen=True, slots=True)
class _PanelDeclaration:
    id: str
    label: str
    min_size: float
    max_size: float
    attrs: dict[str, object]
    content: Slot[CSplitterPanelDefaultSlotData]


@dataclass(slots=True)
class _SplitterRegistry:
    panels: list[_PanelDeclaration] = field(default_factory=list)


def _plain(owner: str, name: str, value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        raise TypeError(f"{owner} {name} must be a string, got {raw!r}.")
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip() or "\x00" in plain:
        raise ValueError(f"{owner} {name} must be nonempty and cannot contain U+0000.")
    return plain


def _identifier(value: object) -> str:
    plain = _plain("CSplitterPanel", "id", value)
    if any(character in "\t\n\f\r " for character in plain):
        raise ValueError("CSplitterPanel id cannot contain ASCII whitespace.")
    return plain


def _choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain("CSplitter", name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        raise ValueError(f"CSplitter {name} must be one of {expected}, got {plain!r}.")
    return plain


def _number(owner: str, name: str, value: object, *, minimum: float, maximum: float) -> float:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        raise TypeError(f"{owner} {name} must be a number, got {raw!r}.")
    result = float(raw)
    if not minimum <= result <= maximum:
        raise ValueError(f"{owner} {name} must be between {minimum:g} and {maximum:g}, got {result:g}.")
    return result


def _sizes(value: object) -> tuple[float, ...] | None:
    raw = const_value(value)
    if raw is None:
        return None
    if isinstance(raw, str | bytes | bytearray | Mapping) or not isinstance(raw, Sequence):
        raise TypeError(f"CSplitter sizes must be a sequence of numbers or None, got {raw!r}.")
    values = tuple(_number("CSplitter", "sizes entry", item, minimum=0, maximum=100) for item in raw)
    if not values:
        raise ValueError("CSplitter sizes cannot be empty.")
    if abs(sum(values) - 100) > 0.01:
        raise ValueError(f"CSplitter sizes must total 100, got {sum(values):g}.")
    return values


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


def _context(component: LibraryComponent) -> _SplitterRegistry:
    context = component.inject(_CONTEXT, None)
    if context is None:
        raise ValueError("CSplitterPanel must be rendered directly inside CSplitter.")
    return cast("_SplitterRegistry", context.registry)


def _token(value: str) -> str:
    return sha256(value.encode()).hexdigest()[:12]


def _default_sizes(count: int) -> tuple[float, ...]:
    item = 100 / count
    values = [item for _ in range(count - 1)]
    values.append(100 - sum(values))
    return tuple(values)


def _validate_output(result: CitryRender) -> None:
    if result.serialize(deps_strategy="ignore").strip():
        raise ValueError(
            "CSplitter default content may contain only CSplitterPanel declarations, "
            "formatting whitespace, and transparent components that produce no other output."
        )


class CSplitter(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        sizes: Sequence[int | float] | None = None
        orientation: CSplitterOrientation = "horizontal"
        disabled: bool = False
        keyboard_step: float = 2
        variant: CSplitterVariant = "plain"
        size: CSplitterSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CSplitterDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        if self.inject(_CONTEXT, None) is not None:
            raise ValueError("Nested CSplitter must be rendered inside panel content, not as a direct declaration.")
        sizes = _sizes(kwargs.sizes)
        orientation = _choice("orientation", kwargs.orientation, _ORIENTATIONS)
        validate_boolean("CSplitter", "disabled", kwargs.disabled)
        keyboard_step = _number("CSplitter", "keyboard_step", kwargs.keyboard_step, minimum=0.1, maximum=25)
        variant = _choice("variant", kwargs.variant, _VARIANTS)
        size = _choice("size", kwargs.size, _SIZES)
        if "default" not in self.raw_slots:
            raise ValueError("CSplitter requires at least two CSplitterPanel declarations.")
        registry = _SplitterRegistry()
        self.provide(_CONTEXT, registry=registry)
        data: dict[str, object] = {
            "sizes": list(sizes) if sizes is not None else None,
            "orientation": orientation,
            "disabled": bool(kwargs.disabled),
            "keyboardStep": keyboard_step,
            "variant": variant,
            "size": size,
        }
        self._splitter_data = data
        return {
            **data,
            "group_id": f"cui-splitter-{self.id}",
            "attrs": _attrs("CSplitter", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "registry": registry,
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return self._splitter_data

    template = """
      <c-CInternalSplitterDeclarations><c-slot required /></c-CInternalSplitterDeclarations>
      <c-CInternalSplitter
        c-group_id="group_id"
        c-sizes="sizes"
        c-orientation="orientation"
        c-disabled="disabled"
        c-keyboard_step="keyboardStep"
        c-variant="variant"
        c-size="size"
        c-attrs="attrs"
        c-registry="registry"
      />
    """

    js = r"""
      $component({
        props: {
          sizes: {}, orientation: {}, disabled: {}, keyboardStep: {}, variant: {}, size: {},
          onResizeStart: {}, onResize: {}, onResizeEnd: {},
        },
        init: ({els, data, props, effect}) => {
          const root = els[0];
          const invalidEpisodes = new Set();
          const panels = () => [...root.querySelectorAll(':scope > [data-citry-ui-part="panel"]')];
          const handles = () => [...root.querySelectorAll(':scope > [data-citry-ui-part="handle"]')];
          const initial = panels().map((panel) => Number(panel.dataset.sizePercent));
          const panelIds = panels().map((panel) => panel.dataset.panelId);
          const fingerprint = JSON.stringify(data.sizes ?? initial);
          const prior = root.__citryUiSplitterRuntime;
          let committed = prior && prior.serverFingerprint === fingerprint
            && JSON.stringify(prior.panelIds) === JSON.stringify(panelIds)
            ? [...prior.committed]
            : [...initial];
          let current = [...committed];
          let controlled = false;
          let callbackStart = null;
          let callbackResize = null;
          let callbackEnd = null;
          let configuration = {
            orientation: data.orientation,
            disabled: data.disabled,
            keyboardStep: data.keyboardStep,
            variant: data.variant,
            size: data.size,
          };
          let drag = null;
          let task = null;
          let generation = 0;
          let structureValid = false;

          const report = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CSplitter ${name} received invalid client value`, value);
          };
          const resolveBoolean = (name, fallback) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'boolean') { invalidEpisodes.delete(name); return supplied; }
            report(name, supplied); return fallback;
          };
          const resolveNumber = (name, fallback, minimum, maximum) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'number' && Number.isFinite(supplied)
                && supplied >= minimum && supplied <= maximum) {
              invalidEpisodes.delete(name); return supplied;
            }
            report(name, supplied); return fallback;
          };
          const resolveChoice = (name, fallback, allowed) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'string' && allowed.includes(supplied)) {
              invalidEpisodes.delete(name); return supplied;
            }
            report(name, supplied); return fallback;
          };
          const effectivelyDisabled = () => {
            if (configuration.disabled) return true;
            for (let node = root.parentElement; node; node = node.parentElement) {
              if (!(node instanceof HTMLFieldSetElement) || !node.disabled) continue;
              const legend = [...node.children].find((child) => child instanceof HTMLLegendElement);
              if (!(legend instanceof Element) || !legend.contains(root)) return true;
            }
            return false;
          };
          const limits = (index, sizes = current) => {
            const entries = panels();
            const before = entries[index];
            const after = entries[index + 1];
            const total = sizes[index] + sizes[index + 1];
            return {
              minimum: Math.max(Number(before.dataset.minSize), total - Number(after.dataset.maxSize)),
              maximum: Math.min(Number(before.dataset.maxSize), total - Number(after.dataset.minSize)),
            };
          };
          const validSizes = (value) => {
            const entries = panels();
            if (!Array.isArray(value) || value.length !== entries.length) return false;
            if (!value.every((item) => typeof item === 'number' && Number.isFinite(item))) return false;
            if (Math.abs(value.reduce((sum, item) => sum + item, 0) - 100) > 0.01) return false;
            return value.every((item, index) => item >= Number(entries[index].dataset.minSize)
              && item <= Number(entries[index].dataset.maxSize));
          };
          const invalidStructure = () => {
            const children = [...root.children];
            const entries = panels();
            const bars = handles();
            if (entries.length < 2 || bars.length !== entries.length - 1) return 'requires two or more panels';
            if (children.length !== entries.length + bars.length) return 'contains an unknown direct child';
            for (let index = 0; index < children.length; index += 1) {
              const expected = index % 2 === 0 ? 'panel' : 'handle';
              if (children[index].dataset.citryUiPart !== expected) return 'panel and handle order is invalid';
            }
            return null;
          };
          const sync = () => {
            const problem = invalidStructure();
            if (problem) {
              structureValid = false;
              report('structure', problem);
              root.removeAttribute('data-citry-splitter-initialized');
              handles().forEach((handle) => { handle.tabIndex = -1; handle.setAttribute('aria-disabled', 'true'); });
              return;
            }
            invalidEpisodes.delete('structure');
            structureValid = true;
            let supplied = props.sizes;
            if (supplied === null) supplied = undefined;
            if (supplied === undefined) {
              invalidEpisodes.delete('sizes');
              if (controlled) committed = [...current];
              controlled = false;
              current = [...committed];
            } else if (validSizes(supplied)) {
              invalidEpisodes.delete('sizes');
              controlled = true;
              current = [...supplied];
            } else {
              report('sizes', supplied);
              controlled = true;
              current = [...committed];
            }
            const disabled = effectivelyDisabled();
            if (disabled && drag) endDrag(drag.lastEvent, true);
            root.dataset.orientation = configuration.orientation;
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            root.toggleAttribute('data-disabled', disabled);
            panels().forEach((panel, index) => {
              const value = Math.round(current[index] * 10000) / 10000;
              panel.dataset.sizePercent = String(value);
              panel.style.flex = `${value} 1 0px`;
            });
            handles().forEach((handle, index) => {
              const range = limits(index);
              handle.setAttribute(
                'aria-orientation', configuration.orientation === 'horizontal' ? 'vertical' : 'horizontal'
              );
              handle.setAttribute('aria-valuemin', String(Math.round(range.minimum * 100) / 100));
              handle.setAttribute('aria-valuemax', String(Math.round(range.maximum * 100) / 100));
              handle.setAttribute('aria-valuenow', String(Math.round(current[index] * 100) / 100));
              handle.setAttribute('aria-disabled', disabled ? 'true' : 'false');
              handle.tabIndex = disabled ? -1 : 0;
              handle.toggleAttribute('data-disabled', disabled);
            });
            root.__citryUiSplitterRuntime = {
              serverFingerprint: fingerprint, panelIds, committed: [...committed],
            };
            root.setAttribute('data-citry-splitter-initialized', '');
          };
          const schedule = () => {
            if (task !== null) return;
            const scheduled = generation;
            task = setTimeout(() => { task = null; if (scheduled === generation) sync(); }, 0);
          };
          const detail = (sizes, previous, index, source, event) => ({
            sizes: [...sizes], previousSizes: [...previous], handleIndex: index,
            controlled, source, sourceEvent: event,
          });
          const request = (next, previous, index, source, event) => {
            callbackResize?.([...next], detail(next, previous, index, source, event));
            if (!controlled) { committed = [...next]; current = [...next]; sync(); }
            else schedule();
          };
          const handleForEvent = (event) => event.composedPath().find(
            (node) => node instanceof Element && node.matches?.('[data-citry-ui-part="handle"]')
              && node.closest('[data-citry-ui-part="splitter"]') === root
          );
          const coordinate = (event) => configuration.orientation === 'horizontal' ? event.clientX : event.clientY;
          const onPointerDown = (event) => {
            const handle = handleForEvent(event);
            if (!(handle instanceof HTMLElement) || event.button !== 0
                || effectivelyDisabled() || !structureValid) return;
            event.preventDefault();
            const index = Number(handle.dataset.handleIndex);
            const startSizes = [...current];
            drag = {
              handle, index, pointerId: event.pointerId, start: coordinate(event),
              startSizes, lastSizes: startSizes, lastEvent: event,
            };
            handle.setPointerCapture(event.pointerId);
            handle.setAttribute('data-active', '');
            root.setAttribute('data-resizing', '');
            callbackStart?.(detail(startSizes, startSizes, index, 'pointer', event));
          };
          const onPointerMove = (event) => {
            if (!drag || event.pointerId !== drag.pointerId) return;
            const rect = root.getBoundingClientRect();
            const dimension = configuration.orientation === 'horizontal' ? rect.width : rect.height;
            if (!(dimension > 0)) return;
            let delta = (coordinate(event) - drag.start) / dimension * 100;
            if (configuration.orientation === 'horizontal' && getComputedStyle(root).direction === 'rtl') delta *= -1;
            const range = limits(drag.index, drag.startSizes);
            const before = Math.max(range.minimum, Math.min(range.maximum, drag.startSizes[drag.index] + delta));
            const next = [...drag.startSizes];
            const total = drag.startSizes[drag.index] + drag.startSizes[drag.index + 1];
            next[drag.index] = before;
            next[drag.index + 1] = total - before;
            drag.lastSizes = next;
            drag.lastEvent = event;
            request(next, drag.startSizes, drag.index, 'pointer', event);
          };
          function endDrag(event, cancelled = false) {
            if (!drag) return;
            const transaction = drag;
            drag = null;
            if (transaction.handle.hasPointerCapture?.(transaction.pointerId)) {
              transaction.handle.releasePointerCapture(transaction.pointerId);
            }
            transaction.handle.removeAttribute('data-active');
            root.removeAttribute('data-resizing');
            const finalSizes = cancelled ? current : transaction.lastSizes;
            callbackEnd?.([...finalSizes], detail(
              finalSizes, transaction.startSizes, transaction.index, 'pointer', event ?? transaction.lastEvent
            ));
          }
          const onPointerEnd = (event) => {
            if (drag && event.pointerId === drag.pointerId) endDrag(event);
          };
          const onKeyDown = (event) => {
            const handle = handleForEvent(event);
            if (!(handle instanceof HTMLElement) || effectivelyDisabled() || !structureValid) return;
            const index = Number(handle.dataset.handleIndex);
            const range = limits(index);
            let nextBefore = null;
            const multiplier = event.shiftKey ? 4 : 1;
            const amount = configuration.keyboardStep * multiplier;
            if (event.key === 'Home') nextBefore = range.minimum;
            else if (event.key === 'End') nextBefore = range.maximum;
            else if (configuration.orientation === 'horizontal' && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
              const physical = event.key === 'ArrowRight' ? amount : -amount;
              nextBefore = current[index] + (getComputedStyle(root).direction === 'rtl' ? -physical : physical);
            } else if (configuration.orientation === 'vertical' && ['ArrowUp', 'ArrowDown'].includes(event.key)) {
              nextBefore = current[index] + (event.key === 'ArrowDown' ? amount : -amount);
            }
            if (nextBefore === null) return;
            event.preventDefault();
            nextBefore = Math.max(range.minimum, Math.min(range.maximum, nextBefore));
            if (Math.abs(nextBefore - current[index]) < 0.0001) return;
            const previous = [...current];
            const total = current[index] + current[index + 1];
            const next = [...current];
            next[index] = nextBefore;
            next[index + 1] = total - nextBefore;
            callbackStart?.(detail(previous, previous, index, 'keyboard', event));
            request(next, previous, index, 'keyboard', event);
            callbackEnd?.([...next], detail(next, previous, index, 'keyboard', event));
          };
          root.addEventListener('pointerdown', onPointerDown);
          root.addEventListener('pointermove', onPointerMove);
          root.addEventListener('pointerup', onPointerEnd);
          root.addEventListener('pointercancel', onPointerEnd);
          root.addEventListener('keydown', onKeyDown);
          const observer = new MutationObserver(schedule);
          observer.observe(root, {childList: true});
          const fieldsets = [];
          for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (!(ancestor instanceof HTMLFieldSetElement)) continue;
            const item = new MutationObserver(schedule);
            item.observe(ancestor, {childList: true, attributes: true, attributeFilter: ['disabled']});
            fieldsets.push(item);
          }
          const stop = effect(() => {
            callbackStart = typeof props.onResizeStart === 'function' ? props.onResizeStart : null;
            callbackResize = typeof props.onResize === 'function' ? props.onResize : null;
            callbackEnd = typeof props.onResizeEnd === 'function' ? props.onResizeEnd : null;
            configuration = {
              orientation: resolveChoice('orientation', data.orientation, ['horizontal', 'vertical']),
              disabled: resolveBoolean('disabled', data.disabled),
              keyboardStep: resolveNumber('keyboardStep', data.keyboardStep, 0.1, 25),
              variant: resolveChoice('variant', data.variant, ['plain', 'soft', 'outline']),
              size: resolveChoice('size', data.size, ['sm', 'md', 'lg']),
            };
            schedule();
          });
          schedule();
          return () => {
            generation += 1;
            if (task !== null) clearTimeout(task);
            if (drag) endDrag(drag.lastEvent, true);
            root.__citryUiSplitterRuntime = {serverFingerprint: fingerprint, panelIds, committed: [...committed]};
            stop?.(); observer.disconnect(); fieldsets.forEach((item) => item.disconnect());
            root.removeEventListener('pointerdown', onPointerDown);
            root.removeEventListener('pointermove', onPointerMove);
            root.removeEventListener('pointerup', onPointerEnd);
            root.removeEventListener('pointercancel', onPointerEnd);
            root.removeEventListener('keydown', onKeyDown);
            root.removeAttribute('data-resizing');
            root.removeAttribute('data-citry-splitter-initialized');
          };
        },
      })
    """

    css_file = "runtime.min.css"


class CSplitterPanel(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        id: str
        label: str
        min_size: float = 10
        max_size: float = 100
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CSplitterPanelDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        panel_id = _identifier(kwargs.id)
        label = _plain("CSplitterPanel", "label", kwargs.label)
        minimum = _number("CSplitterPanel", "min_size", kwargs.min_size, minimum=0, maximum=100)
        maximum = _number("CSplitterPanel", "max_size", kwargs.max_size, minimum=0, maximum=100)
        if minimum > maximum:
            raise ValueError("CSplitterPanel min_size cannot exceed max_size.")
        if "default" not in self.raw_slots:
            raise ValueError("CSplitterPanel requires default content.")
        registry = _context(self)
        registry.panels.append(
            _PanelDeclaration(
                id=panel_id,
                label=label,
                min_size=minimum,
                max_size=maximum,
                attrs=_attrs("CSplitterPanel", kwargs.attrs, _PANEL_OWNED, kwargs.class_, kwargs.style),
                content=cast("Slot[CSplitterPanelDefaultSlotData]", slots.default),
            )
        )
        self.unprovide(_CONTEXT)
        return {}

    def on_render(self) -> str:
        return ""


class CInternalSplitterDeclarations(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CSplitterDefaultSlotData]

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CSplitter declaration collection completed without a render result.")
        _validate_output(result)

    template = "<c-slot required />"


class CInternalSplitter(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        group_id: str
        sizes: list[float] | None
        orientation: CSplitterOrientation
        disabled: bool
        keyboard_step: float
        variant: CSplitterVariant
        size: CSplitterSize
        attrs: dict[str, object]
        registry: _SplitterRegistry

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        panels = kwargs.registry.panels
        if len(panels) < 2:
            raise ValueError("CSplitter requires at least two CSplitterPanel declarations.")
        ids = [panel.id for panel in panels]
        if len(ids) != len(set(ids)):
            raise ValueError("CSplitter requires every panel id to be unique.")
        sizes = tuple(kwargs.sizes) if kwargs.sizes is not None else _default_sizes(len(panels))
        if len(sizes) != len(panels):
            raise ValueError(f"CSplitter sizes has {len(sizes)} entries for {len(panels)} panels.")
        if sum(panel.min_size for panel in panels) > 100.01:
            raise ValueError("CSplitter panel minimum sizes cannot total more than 100.")
        if sum(panel.max_size for panel in panels) < 99.99:
            raise ValueError("CSplitter panel maximum sizes cannot total less than 100.")
        for panel, panel_size in zip(panels, sizes, strict=True):
            if not panel.min_size <= panel_size <= panel.max_size:
                raise ValueError(
                    f"CSplitter size {panel_size:g} for panel {panel.id!r} is outside "
                    f"its {panel.min_size:g} to {panel.max_size:g} constraint."
                )
        self.unprovide(_CONTEXT)
        items: list[dict[str, object]] = []
        for index, panel in enumerate(panels):
            items.append({"kind": "panel", "panel": panel, "index": index, "size": sizes[index]})
            if index < len(panels) - 1:
                items.append(
                    {
                        "kind": "handle",
                        "index": index,
                        "before": panel,
                        "after": panels[index + 1],
                        "before_size": sizes[index],
                        "pair_total": sizes[index] + sizes[index + 1],
                    }
                )
        return {
            "group_id": kwargs.group_id,
            "orientation": kwargs.orientation,
            "attrs": {
                **kwargs.attrs,
                "data-orientation": kwargs.orientation,
                "data-disabled": kwargs.disabled,
                "data-variant": kwargs.variant,
                "data-size": kwargs.size,
            },
            "items": items,
            "count": len(panels),
        }

    template = """
      <div class="cui-splitter" c-bind="attrs" data-citry-ui-part="splitter">
        <c-for each="item in items">
          <c-if cond="item['kind'] == 'panel'">
            <c-CInternalSplitterPanel
              c-group_id="group_id"
              c-declaration="item['panel']"
              c-index="item['index']"
              c-count="count"
              c-size="item['size']"
            />
          </c-if>
          <c-else>
            <c-CInternalSplitterHandle
              c-group_id="group_id"
              c-index="item['index']"
              c-before="item['before']"
              c-after="item['after']"
              c-before_size="item['before_size']"
              c-pair_total="item['pair_total']"
              c-orientation="orientation"
            />
          </c-else>
        </c-for>
      </div>
    """


class CInternalSplitterPanel(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        group_id: str
        declaration: _PanelDeclaration
        index: int
        count: int
        size: float

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        panel = kwargs.declaration
        slot_data: CSplitterPanelDefaultSlotData = {
            "id": panel.id,
            "index": kwargs.index,
            "size": kwargs.size,
            "is_first": kwargs.index == 0,
            "is_last": kwargs.index == kwargs.count - 1,
        }
        self.unprovide(_CONTEXT)
        style = str(panel.attrs.get("style") or "").rstrip("; ")
        if style:
            style += "; "
        style += f"flex: {kwargs.size:g} 1 0px"
        return {
            "morph_key": panel.id,
            "attrs": {
                **panel.attrs,
                "id": f"{kwargs.group_id}-panel-{_token(panel.id)}",
                "role": "group",
                "aria-label": panel.label,
                "data-panel-id": panel.id,
                "data-index": kwargs.index,
                "data-size-percent": kwargs.size,
                "data-min-size": panel.min_size,
                "data-max-size": panel.max_size,
                "style": style,
            },
            "content": Slot(lambda ctx: panel.content(slot_data, provides=dict(ctx.provides or {}))),
        }

    template = """
      <div class="cui-splitter__panel" #c-key="morph_key" c-bind="attrs" data-citry-ui-part="panel">
        {{ content }}
      </div>
    """


class CInternalSplitterHandle(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        group_id: str
        index: int
        before: _PanelDeclaration
        after: _PanelDeclaration
        before_size: float
        pair_total: float
        orientation: CSplitterOrientation

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        minimum = max(kwargs.before.min_size, kwargs.pair_total - kwargs.after.max_size)
        maximum = min(kwargs.before.max_size, kwargs.pair_total - kwargs.after.min_size)
        self.unprovide(_CONTEXT)
        return {
            "index": kwargs.index,
            "label": f"{kwargs.before.label} / {kwargs.after.label}",
            "controls": (
                f"{kwargs.group_id}-panel-{_token(kwargs.before.id)} {kwargs.group_id}-panel-{_token(kwargs.after.id)}"
            ),
            "aria_orientation": "vertical" if kwargs.orientation == "horizontal" else "horizontal",
            "minimum": minimum,
            "maximum": maximum,
            "value": kwargs.before_size,
        }

    template = """
      <div
        class="cui-splitter__handle"
        role="separator"
        tabindex="0"
        c-aria-label="label"
        c-aria-controls="controls"
        c-aria-orientation="aria_orientation"
        c-aria-valuemin="minimum"
        c-aria-valuemax="maximum"
        c-aria-valuenow="value"
        c-data-handle-index="index"
        data-citry-ui-part="handle"
      >
        <span class="cui-splitter__handle-line" aria-hidden="true" data-citry-ui-part="handle-line"></span>
        <span class="cui-splitter__handle-grip" aria-hidden="true" data-citry-ui-part="handle-grip"></span>
      </div>
    """


__all__ = [
    "CSplitter",
    "CSplitterDefaultSlotData",
    "CSplitterOrientation",
    "CSplitterPanel",
    "CSplitterPanelDefaultSlotData",
    "CSplitterResizeDetail",
    "CSplitterResizeSource",
    "CSplitterSize",
    "CSplitterVariant",
]
