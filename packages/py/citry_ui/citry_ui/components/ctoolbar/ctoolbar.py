"""Named Toolbar composite with roving focus navigation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CToolbarOrientation = Literal["horizontal", "vertical"]
CToolbarVariant = Literal["plain", "soft", "outline"]
CToolbarSize = Literal["sm", "md", "lg"]

_ORIENTATIONS = ("horizontal", "vertical")
_VARIANTS = ("plain", "soft", "outline")
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {
        "x-bind",
        "x-for",
        "x-html",
        "x-if",
        "x-ignore",
        "x-model",
        "x-modelable",
        "x-show",
        "x-teleport",
        "x-text",
    }
)
_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-orientation",
        "aria-roledescription",
        "contenteditable",
        "data-citry-ui-part",
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


class CToolbarDefaultSlotData:
    pass


def _plain(input_name: str, value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CToolbar {input_name} must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip() or "\x00" in plain:
        msg = f"CToolbar {input_name} must be nonempty and cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CToolbar {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _dynamic_target(attribute: str) -> str | None:
    if attribute.startswith("x-bind:"):
        return attribute.removeprefix("x-bind:").split(".", 1)[0]
    if attribute.startswith((":", ".")):
        return attribute[1:].split(".", 1)[0]
    return None


def _copy_attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"CToolbar attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, _OWNED_ATTRS, "CToolbar attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CToolbar attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CToolbar attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if _dynamic_target(normalized) in _OWNED_ATTRS:
            msg = f"CToolbar attrs cannot dynamically bind owned attribute {key!r}."
            raise ValueError(msg)
    return copied


class CToolbar(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        orientation: CToolbarOrientation = "horizontal"
        loop: bool = True
        variant: CToolbarVariant = "plain"
        size: CToolbarSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CToolbarDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        label = _plain("label", kwargs.label)
        orientation = _choice("orientation", kwargs.orientation, _ORIENTATIONS)
        variant = _choice("variant", kwargs.variant, _VARIANTS)
        size = _choice("size", kwargs.size, _SIZES)
        validate_boolean("CToolbar", "loop", kwargs.loop)
        if "default" not in self.raw_slots:
            raise ValueError("CToolbar requires a default slot with at least three controls.")
        return {
            "label": label,
            "orientation": orientation,
            "loop": bool(kwargs.loop),
            "variant": variant,
            "size": size,
            "attrs": merge_root_attrs(_copy_attrs(kwargs.attrs), kwargs.class_, kwargs.style),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "orientation": _choice("orientation", kwargs.orientation, _ORIENTATIONS),
            "loop": bool(kwargs.loop),
            "variant": _choice("variant", kwargs.variant, _VARIANTS),
            "size": _choice("size", kwargs.size, _SIZES),
        }

    template = """
      <div
        class="cui-toolbar"
        c-bind="attrs"
        data-citry-ui-part="toolbar"
        role="toolbar"
        c-aria-label="label"
        c-aria-orientation="orientation"
        c-data-orientation="orientation"
        c-data-loop="loop"
        c-data-variant="variant"
        c-data-size="size"
      ><c-slot required /></div>
    """

    js = r"""
      $component({
        props: {orientation: {}, loop: {}, variant: {}, size: {}},
        init: ({els, data, props, effect}) => {
          const root = els[0];
          const invalidEpisodes = new Set();
          const originalTabindex = new Map();
          const excludedComposite = '[role="menu"], [role="listbox"], [role="tree"], '
            + '[role="grid"], [role="tablist"], dialog, [popover]';
          let controls = [];
          let current = null;
          let currentIndex = 0;
          let configuration = {
            orientation: data.orientation,
            loop: data.loop,
            variant: data.variant,
            size: data.size,
          };
          let generation = 0;
          let reconciliationTask = null;
          let structureValid = false;

          const report = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CToolbar ${name} received invalid value`, value);
          };
          const resolveChoice = (name, fallback, allowed) => {
            const supplied = props[name];
            if (supplied === undefined) {
              invalidEpisodes.delete(name);
              return fallback;
            }
            if (typeof supplied === "string" && allowed.includes(supplied)) {
              invalidEpisodes.delete(name);
              return supplied;
            }
            report(name, supplied);
            return fallback;
          };
          const resolveBoolean = (name, fallback) => {
            const supplied = props[name];
            if (supplied === undefined) {
              invalidEpisodes.delete(name);
              return fallback;
            }
            if (typeof supplied === "boolean") {
              invalidEpisodes.delete(name);
              return supplied;
            }
            report(name, supplied);
            return fallback;
          };
          const ownedRegion = (element) => {
            if (!(element instanceof Element)) return false;
            if (element.closest('[data-citry-ui-part="toolbar"]') !== root) return false;
            const composite = element.closest(excludedComposite);
            return composite === null || !root.contains(composite);
          };
          const candidateControls = () => [...root.querySelectorAll('button, a[href]')]
            .filter(ownedRegion);
          const unavailable = (element) => {
            if (!element.isConnected) return true;
            if (element instanceof HTMLButtonElement && element.matches(':disabled')) return true;
            if (element.getAttribute("aria-disabled") === "true") return true;
            for (let node = element; node && node !== root; node = node.parentElement) {
              if (node.hidden || node.inert) return true;
            }
            return false;
          };
          const enabledControls = () => controls.filter((element) => !unavailable(element));
          const restoreTabindex = () => {
            originalTabindex.forEach((value, element) => {
              if (!element.isConnected) return;
              if (value === null) element.removeAttribute("tabindex");
              else element.setAttribute("tabindex", value);
            });
          };
          const invalidStructure = () => {
            if (root.querySelector('[role="toolbar"]')) return "nested Toolbar";
            const unsupported = [...root.querySelectorAll(
              'input, select, textarea, [contenteditable]:not([contenteditable="false"]), [tabindex]'
            )].find((element) => {
              if (!ownedRegion(element)) return false;
              if (element.matches('button, a[href]') && originalTabindex.has(element)) {
                if (originalTabindex.get(element) !== null) return true;
                const expected = element === current ? "0" : "-1";
                return element.getAttribute("tabindex") !== expected;
              }
              return true;
            });
            if (unsupported) return unsupported.outerHTML;
            return null;
          };
          const syncTabStops = (focusReplacement = false) => {
            const enabled = enabledControls();
            if (!enabled.includes(current)) {
              const bounded = Math.min(currentIndex, Math.max(0, enabled.length - 1));
              current = enabled[bounded] ?? enabled[0] ?? null;
            }
            controls.forEach((element) => {
              element.tabIndex = element === current && !unavailable(element) ? 0 : -1;
            });
            currentIndex = current ? enabled.indexOf(current) : 0;
            if (focusReplacement && current) current.focus();
          };
          const reconcileStructure = () => {
            reconciliationTask = null;
            const active = root.ownerDocument.activeElement;
            const priorControls = controls;
            const priorCurrent = current;
            const priorIndex = Math.max(0, priorControls.indexOf(current));
            const focusWasInside = active instanceof Element && root.contains(active);
            controls = candidateControls();
            controls.forEach((element) => {
              if (!originalTabindex.has(element)) {
                originalTabindex.set(element, element.getAttribute("tabindex"));
              }
            });
            currentIndex = priorIndex;
            const problem = invalidStructure();
            if (problem || controls.length < 3) {
              structureValid = false;
              report("structure", problem ?? `expected at least three controls, got ${controls.length}`);
              restoreTabindex();
              root.removeAttribute("data-citry-toolbar-initialized");
              return;
            }
            invalidEpisodes.delete("structure");
            structureValid = true;
            if (!controls.includes(current)) current = controls[Math.min(priorIndex, controls.length - 1)];
            const nativeDisabledFocusFallback = active === root.ownerDocument.body
              && priorControls.includes(priorCurrent)
              && unavailable(priorCurrent);
            syncTabStops(
              (focusWasInside
                && priorControls.includes(active)
                && (!controls.includes(active) || unavailable(active)))
                || nativeDisabledFocusFallback
            );
            root.setAttribute("data-citry-toolbar-initialized", "");
          };
          const scheduleReconcile = () => {
            if (reconciliationTask !== null) return;
            const scheduledGeneration = generation;
            reconciliationTask = setTimeout(() => {
              if (scheduledGeneration !== generation) return;
              reconcileStructure();
            }, 0);
          };
          const move = (direction) => {
            const enabled = enabledControls();
            if (!enabled.length) return;
            let index = enabled.indexOf(current);
            if (index < 0) index = 0;
            let next = index + direction;
            if (configuration.loop) next = (next + enabled.length) % enabled.length;
            else next = Math.max(0, Math.min(enabled.length - 1, next));
            current = enabled[next];
            syncTabStops();
            current.focus();
          };
          const edge = (last) => {
            const enabled = enabledControls();
            if (!enabled.length) return;
            current = enabled[last ? enabled.length - 1 : 0];
            syncTabStops();
            current.focus();
          };
          const controlForEvent = (event) => event.composedPath()
            .find((node) => controls.includes(node));
          const onFocusIn = (event) => {
            const control = controlForEvent(event);
            if (!(control instanceof Element) || unavailable(control)) return;
            current = control;
            syncTabStops();
          };
          const onKeyDown = (event) => {
            if (!structureValid || event.isComposing || event.ctrlKey || event.metaKey || event.altKey) return;
            const control = controlForEvent(event);
            if (!(control instanceof Element) || unavailable(control)) return;
            let direction = 0;
            if (configuration.orientation === "horizontal") {
              const rtl = getComputedStyle(root).direction === "rtl";
              if (event.key === "ArrowRight") direction = rtl ? -1 : 1;
              if (event.key === "ArrowLeft") direction = rtl ? 1 : -1;
            } else {
              if (event.key === "ArrowDown") direction = 1;
              if (event.key === "ArrowUp") direction = -1;
            }
            if (direction) {
              event.preventDefault();
              move(direction);
            } else if (event.key === "Home" || event.key === "End") {
              event.preventDefault();
              edge(event.key === "End");
            }
          };
          const observer = new MutationObserver((records) => {
            const meaningful = records.some((record) => {
              if (record.attributeName !== "tabindex") return true;
              const target = record.target;
              if (!controls.includes(target)) return true;
              const expected = target === current && !unavailable(target) ? "0" : "-1";
              return target.getAttribute("tabindex") !== expected;
            });
            if (meaningful) scheduleReconcile();
          });
          observer.observe(root, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: [
              "aria-disabled", "class", "contenteditable", "disabled", "hidden",
              "href", "inert", "style", "tabindex"
            ],
          });
          const fieldsetObservers = [];
          for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (!(ancestor instanceof HTMLFieldSetElement)) continue;
            const fieldsetObserver = new MutationObserver(scheduleReconcile);
            fieldsetObserver.observe(ancestor, {
              childList: true,
              attributes: true,
              attributeFilter: ["disabled"],
            });
            fieldsetObservers.push(fieldsetObserver);
          }
          root.addEventListener("focusin", onFocusIn, true);
          root.addEventListener("keydown", onKeyDown, true);
          const stop = effect(() => {
            configuration = {
              orientation: resolveChoice("orientation", data.orientation, ["horizontal", "vertical"]),
              loop: resolveBoolean("loop", data.loop),
              variant: resolveChoice("variant", data.variant, ["plain", "soft", "outline"]),
              size: resolveChoice("size", data.size, ["sm", "md", "lg"]),
            };
            root.dataset.orientation = configuration.orientation;
            root.setAttribute("aria-orientation", configuration.orientation);
            root.toggleAttribute("data-loop", configuration.loop);
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            scheduleReconcile();
          });

          return () => {
            generation += 1;
            if (reconciliationTask !== null) clearTimeout(reconciliationTask);
            stop?.();
            observer.disconnect();
            fieldsetObservers.forEach((item) => item.disconnect());
            root.removeEventListener("focusin", onFocusIn, true);
            root.removeEventListener("keydown", onKeyDown, true);
            restoreTabindex();
            root.removeAttribute("data-citry-toolbar-initialized");
          };
        },
      })
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-toolbar) {
          --_cui-toolbar-gap: var(--cui-toolbar-gap, 0.5rem);
          --_cui-toolbar-padding: var(--cui-toolbar-padding, 0.375rem);
          --_cui-toolbar-min-height: var(--cui-toolbar-min-height, 2.75rem);
          --_cui-toolbar-radius: var(--cui-toolbar-radius, 0.75rem);
          --_cui-toolbar-background: var(--cui-toolbar-background, transparent);
          --_cui-toolbar-foreground: var(--cui-toolbar-foreground, CanvasText);
          --_cui-toolbar-border-color: var(
            --cui-toolbar-border-color,
            color-mix(in srgb, CanvasText 16%, transparent)
          );
          --_cui-toolbar-focus-color: var(--cui-toolbar-focus-color, Highlight);

          box-sizing: border-box;
          display: flex;
          flex-direction: row;
          align-items: center;
          gap: var(--_cui-toolbar-gap);
          min-inline-size: 0;
          max-inline-size: 100%;
          min-block-size: var(--_cui-toolbar-min-height);
          padding: var(--_cui-toolbar-padding);
          overflow-x: auto;
          overflow-y: hidden;
          border: 1px solid transparent;
          border-radius: var(--_cui-toolbar-radius);
          background: var(--_cui-toolbar-background);
          color: var(--_cui-toolbar-foreground);
          scrollbar-width: thin;
        }

        :where(.cui-toolbar[data-orientation="vertical"]) {
          flex-direction: column;
          align-items: stretch;
          overflow-x: hidden;
          overflow-y: auto;
        }

        :where(.cui-toolbar[data-variant="soft"]) {
          --_cui-toolbar-background: var(
            --cui-toolbar-background,
            color-mix(in srgb, CanvasText 7%, Canvas)
          );
        }

        :where(.cui-toolbar[data-variant="outline"]) {
          border-color: var(--_cui-toolbar-border-color);
        }

        :where(.cui-toolbar[data-size="sm"]) {
          --_cui-toolbar-gap: var(--cui-toolbar-gap, 0.375rem);
          --_cui-toolbar-padding: var(--cui-toolbar-padding, 0.25rem);
          --_cui-toolbar-min-height: var(--cui-toolbar-min-height, 2.25rem);
        }

        :where(.cui-toolbar[data-size="lg"]) {
          --_cui-toolbar-gap: var(--cui-toolbar-gap, 0.625rem);
          --_cui-toolbar-padding: var(--cui-toolbar-padding, 0.5rem);
          --_cui-toolbar-min-height: var(--cui-toolbar-min-height, 3.25rem);
        }

        :where(.cui-toolbar :focus-visible) {
          outline-color: var(--_cui-toolbar-focus-color);
          outline-offset: 2px;
        }

        @media (forced-colors: active) {
          :where(.cui-toolbar) {
            border-color: CanvasText;
          }
        }

        @media print {
          :where(.cui-toolbar) {
            overflow: visible;
            border-color: currentcolor;
            background: transparent;
            box-shadow: none;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          :where(.cui-toolbar) {
            scroll-behavior: auto;
          }
        }
      }
    """


__all__ = [
    "CToolbar",
    "CToolbarDefaultSlotData",
    "CToolbarOrientation",
    "CToolbarSize",
    "CToolbarVariant",
]
