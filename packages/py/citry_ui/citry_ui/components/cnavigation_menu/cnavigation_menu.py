"""Persistent website navigation with optional disclosure panels."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, overload

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CNavigationMenuOrientation = Literal["horizontal", "vertical"]
CNavigationMenuVariant = Literal["plain", "surface"]
CNavigationMenuSize = Literal["sm", "md", "lg"]


class CNavigationMenuValueChangeDetail(TypedDict):
    value: str | None
    previousValue: str | None
    reason: Literal[
        "trigger",
        "hover",
        "escape",
        "outside",
        "focus-outside",
        "link",
        "disabled",
        "structure",
    ]
    controlled: bool
    forced: bool
    source: object | None


class CNavigationMenuDefaultSlotData:
    pass


class CNavigationMenuLinkDefaultSlotData:
    pass


class CNavigationMenuItemLabelSlotData:
    pass


class CNavigationMenuItemDefaultSlotData:
    pass


_CONTEXT_KEY = "citry_ui_navigation_menu"
_NESTING_KEY = "citry_ui_navigation_menu_descendant"
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
        "data-citry-navigation-menu-initialized",
        "data-citry-navigation-menu-root",
        "data-citry-ui-part",
        "data-disabled",
        "data-loop",
        "data-orientation",
        "data-size",
        "data-value",
        "data-variant",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_LINK_ITEM_OWNED = frozenset(
    {"aria-hidden", "contenteditable", "data-citry-ui-part", "hidden", "inert", "popover", "role", "tabindex"}
)
_LINK_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-hidden",
        "aria-roledescription",
        "data-citry-navigation-menu-link",
        "data-citry-ui-part",
        "href",
        "role",
        "tabindex",
    }
)
_ITEM_OWNED = frozenset(
    {
        "aria-hidden",
        "contenteditable",
        "data-citry-navigation-menu-item",
        "data-citry-ui-part",
        "data-disabled",
        "data-open",
        "data-value",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_TRIGGER_OWNED = frozenset(
    {
        "aria-controls",
        "aria-disabled",
        "aria-expanded",
        "aria-hidden",
        "aria-roledescription",
        "data-citry-navigation-menu-trigger",
        "data-citry-ui-part",
        "data-disabled",
        "data-open",
        "data-value",
        "disabled",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
        "type",
    }
)
_PANEL_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "data-citry-navigation-menu-panel",
        "data-citry-ui-part",
        "data-open",
        "data-value",
        "hidden",
        "id",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)


@dataclass(slots=True)
class _NavigationMenuContext:
    root_id: str
    selected_value: str | None
    disabled: bool
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


def _choice(component: str, name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(f"{component} {name}", value)
    if plain not in allowed:
        raise ValueError(f"{component} {name} must be one of {allowed!r}, got {plain!r}.")
    return plain


def _milliseconds(component: str, name: str, value: object) -> int:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError(f"{component} {name} must be an integer, got {raw!r}.")
    if raw < 0 or raw > 60_000:
        raise ValueError(f"{component} {name} must be between 0 and 60000, got {raw!r}.")
    return raw


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


def _context(component: LibraryComponent) -> _NavigationMenuContext:
    value = component.inject(_CONTEXT_KEY, None)
    if value is None:
        raise ValueError(f"{type(component).__name__} must be rendered directly inside CNavigationMenu.")
    return value.context


class CNavigationMenu(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        id: str | None = None
        value: str | None = None
        orientation: CNavigationMenuOrientation = "horizontal"
        disabled: bool = False
        delay: int = 200
        close_delay: int = 300
        loop: bool = False
        variant: CNavigationMenuVariant = "plain"
        size: CNavigationMenuSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CNavigationMenuDefaultSlotData]

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_navigation_menu_snapshot", None)
        if cached is not None:
            return cached
        if self.inject(_NESTING_KEY, None) is not None:
            raise ValueError("Nested CNavigationMenu declarations are deferred in v1.")
        label = _plain("CNavigationMenu label", kwargs.label)
        root_id = _html_id("CNavigationMenu id", kwargs.id, f"cui-navigation-menu-{self.id}")
        value = _plain("CNavigationMenu value", kwargs.value, optional=True)
        orientation = _choice("CNavigationMenu", "orientation", kwargs.orientation, _ORIENTATIONS)
        variant = _choice("CNavigationMenu", "variant", kwargs.variant, _VARIANTS)
        size = _choice("CNavigationMenu", "size", kwargs.size, _SIZES)
        validate_boolean("CNavigationMenu", "disabled", kwargs.disabled)
        validate_boolean("CNavigationMenu", "loop", kwargs.loop)
        context = _NavigationMenuContext(
            root_id=root_id,
            selected_value=value,
            disabled=bool(kwargs.disabled),
        )
        self.provide(_CONTEXT_KEY, context=context)
        self.provide(_NESTING_KEY, context=True)
        self._navigation_menu_context = context
        snapshot: dict[str, object] = {
            "label": label,
            "root_id": root_id,
            "value": value,
            "orientation": orientation,
            "disabled": bool(kwargs.disabled),
            "delay": _milliseconds("CNavigationMenu", "delay", kwargs.delay),
            "close_delay": _milliseconds("CNavigationMenu", "close_delay", kwargs.close_delay),
            "loop": bool(kwargs.loop),
            "variant": variant,
            "size": size,
            "attrs": merge_root_attrs(
                _attrs("CNavigationMenu", kwargs.attrs, _ROOT_OWNED),
                kwargs.class_,
                kwargs.style,
            ),
        }
        self._cui_navigation_menu_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "value": snapshot["value"],
            "orientation": snapshot["orientation"],
            "disabled": snapshot["disabled"],
            "delay": snapshot["delay"],
            "closeDelay": snapshot["close_delay"],
            "loop": snapshot["loop"],
            "variant": snapshot["variant"],
            "size": snapshot["size"],
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            raise RuntimeError("CNavigationMenu completed without a render result.")
        context = self._navigation_menu_context
        if context.count == 0:
            raise ValueError("CNavigationMenu requires at least one direct Link or Item.")
        if context.selected_value is not None and context.selected_value not in context.values:
            raise ValueError(f"CNavigationMenu value {context.selected_value!r} does not identify an Item.")

    template = """
      <nav
        class="cui-navigation-menu"
        c-id="root_id"
        c-bind="attrs"
        c-aria-label="label"
        c-data-value="value"
        c-data-orientation="orientation"
        c-data-disabled="disabled"
        c-data-loop="loop"
        c-data-variant="variant"
        c-data-size="size"
        data-citry-navigation-menu-root
        data-citry-ui-part="navigation-menu"
      >
        <ul data-citry-ui-part="list"><c-slot required /></ul>
      </nav>
    """

    js = r"""
      $component({
        props: {
          value: {},
          disabled: {},
          delay: {},
          closeDelay: {},
          loop: {},
          orientation: {},
          variant: {},
          size: {},
          onValueChange: {},
        },
        init: ({ els, data, props, effect }) => {
          const root = els[0];
          const list = root.querySelector(':scope > [data-citry-ui-part="list"]');
          if (!(root instanceof HTMLElement) || !(list instanceof HTMLUListElement)) {
            throw new Error("[citry-ui] CNavigationMenu requires its owned nav/list anatomy.");
          }
          const handoffKey = Symbol.for("citry-ui:navigation-menu-handoff");
          const previous = root[handoffKey];
          delete root[handoffKey];
          let active = true;
          let controlled = false;
          let internalValue = previous?.serverValue === data.value ? previous.value : data.value;
          let effectiveValue = null;
          let onValueChange = null;
          let entries = [];
          let invalidStructure = false;
          let openTimer = null;
          let closeTimer = null;
          let reconcileFrame = null;
          let geometryFrame = null;
          let geometryListening = false;
          let outsideListening = false;
          const invalidEpisodes = new Set();
          let configuration = {
            disabled: data.disabled,
            delay: data.delay,
            closeDelay: data.closeDelay,
            loop: data.loop,
            orientation: data.orientation,
            variant: data.variant,
            size: data.size,
          };

          const reportInvalid = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CNavigationMenu ${name} received invalid client value.`, value, root);
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
          const resolveDelay = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (Number.isInteger(value) && value >= 0 && value <= 60000) {
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
            const value = props.onValueChange;
            if (value === undefined || value === null || typeof value === "function") {
              invalidEpisodes.delete("onValueChange");
              return value ?? null;
            }
            reportInvalid("onValueChange", value);
            return null;
          };
          const clearTimers = () => {
            clearTimeout(openTimer);
            clearTimeout(closeTimer);
            openTimer = null;
            closeTimer = null;
          };
          const directChildren = () => [...list.children].filter((element) => (
            element.matches(':scope[data-citry-ui-part="link-item"], :scope[data-citry-ui-part="item"]')
          ));
          const collect = () => {
            const children = directChildren();
            const next = [];
            const values = new Set();
            let valid = children.length > 0 && children.length === list.children.length;
            for (const child of children) {
              const trigger = child.querySelector(':scope > [data-citry-navigation-menu-trigger]');
              if (!trigger) continue;
              const panel = child.querySelector(':scope > [data-citry-navigation-menu-panel]');
              const value = trigger.dataset.value;
              if (
                !(trigger instanceof HTMLButtonElement)
                || trigger.type !== "button"
                || !panel
                || !value
                || values.has(value)
              ) {
                valid = false;
                continue;
              }
              values.add(value);
              next.push({ item: child, trigger, panel, value });
            }
            entries = next;
            invalidStructure = !valid;
            if (!valid) reportInvalid("structure", children.length);
            else invalidEpisodes.delete("structure");
          };
          const entryFor = (value) => entries.find((entry) => entry.value === value) ?? null;
          const deepActive = () => {
            let current = root.ownerDocument.activeElement;
            while (current?.shadowRoot?.activeElement) current = current.shadowRoot.activeElement;
            return current;
          };
          const composedContains = (container, target) => {
            let current = target;
            while (current) {
              if (current === container) return true;
              current = current.parentNode ?? current.getRootNode?.()?.host ?? null;
            }
            return false;
          };
          const focusTargets = () => [...list.querySelectorAll(
            ':scope > li > a[href], :scope > li > button:not(:disabled)',
          )].filter((element) => element.offsetParent !== null);
          const panelFocusTarget = (panel) => panel.querySelector(
            'a[href], button:not(:disabled), input:not(:disabled), '
              + 'select:not(:disabled), textarea:not(:disabled), '
              + '[tabindex]:not([tabindex="-1"])',
          );
          const alignOpenPanel = () => {
            geometryFrame = null;
            for (const entry of entries) {
              entry.panel.removeAttribute("data-cui-navigation-menu-align-end");
              entry.panel.style.removeProperty("--_cui-navigation-menu-panel-shift");
            }
            if (configuration.orientation !== "horizontal") return;
            const entry = entryFor(effectiveValue);
            if (!entry || entry.panel.hidden) return;
            const view = root.ownerDocument.defaultView;
            const viewportWidth = view?.visualViewport?.width ?? view?.innerWidth ?? 0;
            if (!viewportWidth) return;
            const margin = 16;
            let rect = entry.panel.getBoundingClientRect();
            const rtl = getComputedStyle(root).direction === "rtl";
            const overInlineEnd = rtl ? rect.left < margin : rect.right > viewportWidth - margin;
            entry.panel.toggleAttribute("data-cui-navigation-menu-align-end", overInlineEnd);
            rect = entry.panel.getBoundingClientRect();
            let shift = 0;
            if (rect.right > viewportWidth - margin) shift -= rect.right - (viewportWidth - margin);
            if (rect.left + shift < margin) shift += margin - (rect.left + shift);
            if (Math.abs(shift) > 0.5) {
              entry.panel.style.setProperty("--_cui-navigation-menu-panel-shift", `${shift}px`);
            }
          };
          const scheduleGeometry = () => {
            if (geometryFrame !== null) return;
            geometryFrame = requestAnimationFrame(alignOpenPanel);
          };
          const startGeometry = () => {
            if (!geometryListening) {
              geometryListening = true;
              root.ownerDocument.defaultView?.addEventListener("resize", scheduleGeometry);
              root.ownerDocument.addEventListener("scroll", scheduleGeometry, true);
            }
            scheduleGeometry();
          };
          const stopGeometry = () => {
            if (geometryListening) {
              geometryListening = false;
              root.ownerDocument.defaultView?.removeEventListener("resize", scheduleGeometry);
              root.ownerDocument.removeEventListener("scroll", scheduleGeometry, true);
            }
            cancelAnimationFrame(geometryFrame);
            geometryFrame = null;
          };
          const startOutside = () => {
            if (outsideListening || effectiveValue === null) return;
            outsideListening = true;
            root.ownerDocument.addEventListener("pointerdown", onDocumentPointerDown, true);
            root.ownerDocument.addEventListener("focusin", onDocumentFocusIn, true);
          };
          const stopOutside = () => {
            if (!outsideListening) return;
            outsideListening = false;
            root.ownerDocument.removeEventListener("pointerdown", onDocumentPointerDown, true);
            root.ownerDocument.removeEventListener("focusin", onDocumentFocusIn, true);
          };
          const apply = (value) => {
            const next = configuration.disabled || invalidStructure || !entryFor(value) ? null : value;
            effectiveValue = next;
            root.toggleAttribute("data-disabled", configuration.disabled);
            root.dataset.orientation = configuration.orientation;
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            root.toggleAttribute("data-loop", configuration.loop);
            if (next === null) delete root.dataset.value;
            else root.dataset.value = next;
            for (const entry of entries) {
              const open = entry.value === next;
              const disabled = configuration.disabled || entry.trigger.disabled;
              entry.item.toggleAttribute("data-open", open);
              entry.item.toggleAttribute("data-disabled", disabled);
              entry.trigger.toggleAttribute("data-open", open);
              entry.trigger.toggleAttribute("data-disabled", disabled);
              entry.trigger.setAttribute("aria-expanded", String(open));
              entry.panel.toggleAttribute("data-open", open);
              entry.panel.hidden = !open;
              entry.panel.inert = !open;
            }
            if (next === null) {
              stopOutside();
              stopGeometry();
            } else {
              startOutside();
              startGeometry();
            }
          };
          const notify = (next, previousValue, reason, source, forced = false) => {
            onValueChange?.(next, {
              value: next,
              previousValue,
              reason,
              controlled,
              forced,
              source,
            });
          };
          const request = (next, reason, source, forced = false) => {
            clearTimers();
            const previousValue = effectiveValue;
            if (forced) {
              internalValue = null;
              apply(null);
              if (previousValue !== null) notify(null, previousValue, reason, source, true);
              return;
            }
            if (!controlled) {
              internalValue = next;
              apply(next);
            }
            if (next !== previousValue) notify(next, previousValue, reason, source, false);
          };
          function onDocumentPointerDown(event) {
            if (!event.composedPath().includes(root)) request(null, "outside", event.target);
          }
          function onDocumentFocusIn(event) {
            if (!event.composedPath().includes(root)) request(null, "focus-outside", event.target);
          }
          const onClick = (event) => {
            const path = event.composedPath();
            const trigger = path.find((element) => element?.matches?.("[data-citry-navigation-menu-trigger]"));
            if (trigger && root.contains(trigger)) {
              const entry = entries.find((candidate) => candidate.trigger === trigger);
              if (entry && !configuration.disabled && !trigger.disabled) {
                request(effectiveValue === entry.value ? null : entry.value, "trigger", trigger);
              }
              return;
            }
            const link = path.find((element) => element?.matches?.("a[href]"));
            if (link && root.contains(link) && effectiveValue !== null) request(null, "link", link);
          };
          const onKeyDown = (event) => {
            const target = event.target;
            const controls = focusTargets();
            const index = controls.indexOf(target);
            if (event.key === "Escape" && effectiveValue !== null) {
              const entry = entryFor(effectiveValue);
              request(null, "escape", target);
              entry?.trigger.focus();
              event.preventDefault();
              return;
            }
            if (index < 0) return;
            const rtl = getComputedStyle(root).direction === "rtl";
            let delta = 0;
            if (configuration.orientation === "horizontal") {
              if (event.key === (rtl ? "ArrowLeft" : "ArrowRight")) delta = 1;
              if (event.key === (rtl ? "ArrowRight" : "ArrowLeft")) delta = -1;
              if (event.key === "ArrowDown") {
                const entry = entries.find((candidate) => (
                  candidate.trigger === target && candidate.value === effectiveValue
                ));
                const focusTarget = entry && panelFocusTarget(entry.panel);
                if (focusTarget) {
                  focusTarget.focus();
                  event.preventDefault();
                  return;
                }
              }
            } else {
              if (event.key === "ArrowDown") delta = 1;
              if (event.key === "ArrowUp") delta = -1;
            }
            if (event.key === "Home") {
              controls[0]?.focus();
              event.preventDefault();
              return;
            }
            if (event.key === "End") {
              controls.at(-1)?.focus();
              event.preventDefault();
              return;
            }
            if (!delta) return;
            let next = index + delta;
            if (configuration.loop) next = (next + controls.length) % controls.length;
            if (next >= 0 && next < controls.length) controls[next].focus();
            event.preventDefault();
          };
          const hoverEligible = (event) => event.pointerType === "mouse" || (
            event.pointerType === "pen" && event.buttons === 0 && event.pressure === 0
          );
          const onPointerOver = (event) => {
            if (!hoverEligible(event) || configuration.disabled) return;
            const trigger = event.target.closest?.("[data-citry-navigation-menu-trigger]");
            if (!trigger || !root.contains(trigger) || trigger.disabled) return;
            const entry = entries.find((candidate) => candidate.trigger === trigger);
            if (!entry || trigger.contains(event.relatedTarget)) return;
            clearTimeout(closeTimer);
            clearTimeout(openTimer);
            openTimer = setTimeout(() => request(entry.value, "hover", trigger), configuration.delay);
          };
          const onPointerOut = (event) => {
            if (!hoverEligible(event) || root.contains(event.relatedTarget)) return;
            clearTimeout(openTimer);
            clearTimeout(closeTimer);
            closeTimer = setTimeout(() => request(null, "hover", event.target), configuration.closeDelay);
          };
          const reconcile = () => {
            reconcileFrame = null;
            const previousValue = effectiveValue;
            collect();
            if (invalidStructure) {
              apply(null);
              if (previousValue !== null) notify(null, previousValue, "structure", root, true);
              return;
            }
            if (previousValue !== null && !entryFor(previousValue)) {
              internalValue = null;
              apply(null);
              notify(null, previousValue, "structure", root, true);
              return;
            }
            apply(controlled ? effectiveValue : internalValue);
          };
          const scheduleReconcile = () => {
            if (reconcileFrame !== null) return;
            reconcileFrame = requestAnimationFrame(reconcile);
          };
          const observer = new MutationObserver(scheduleReconcile);
          observer.observe(list, { childList: true, subtree: true, attributes: true, attributeFilter: ["disabled"] });
          root.addEventListener("click", onClick, true);
          root.addEventListener("keydown", onKeyDown, true);
          root.addEventListener("pointerover", onPointerOver);
          root.addEventListener("pointerout", onPointerOut);
          collect();

          effect(() => {
            configuration = {
              disabled: resolveBoolean("disabled"),
              delay: resolveDelay("delay"),
              closeDelay: resolveDelay("closeDelay"),
              loop: resolveBoolean("loop"),
              orientation: resolveChoice("orientation", ["horizontal", "vertical"]),
              variant: resolveChoice("variant", ["plain", "surface"]),
              size: resolveChoice("size", ["sm", "md", "lg"]),
            };
            onValueChange = resolveCallback();
            const supplied = props.value !== undefined;
            let next = internalValue;
            if (supplied) {
              if (props.value === null || (typeof props.value === "string" && entryFor(props.value))) {
                controlled = true;
                invalidEpisodes.delete("value");
                next = props.value;
                internalValue = props.value;
              } else {
                controlled = false;
                reportInvalid("value", props.value);
                next = internalValue;
              }
            } else {
              controlled = false;
              invalidEpisodes.delete("value");
            }
            if (configuration.disabled && effectiveValue !== null) {
              request(null, "disabled", root, true);
            } else {
              apply(next);
            }
            root.setAttribute("data-citry-navigation-menu-initialized", "");
          });

          return () => {
            active = false;
            clearTimers();
            cancelAnimationFrame(reconcileFrame);
            stopGeometry();
            observer.disconnect();
            stopOutside();
            root.removeEventListener("click", onClick, true);
            root.removeEventListener("keydown", onKeyDown, true);
            root.removeEventListener("pointerover", onPointerOver);
            root.removeEventListener("pointerout", onPointerOut);
            root[handoffKey] = { value: internalValue, serverValue: data.value };
            root.removeAttribute("data-citry-navigation-menu-initialized");
          };
        },
      });
    """

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="navigation-menu"]) {
          --_cui-navigation-menu-background: var(--cui-navigation-menu-background, transparent);
          --_cui-navigation-menu-foreground: var(--cui-navigation-menu-foreground, CanvasText);
          --_cui-navigation-menu-border-color: var(--cui-navigation-menu-border-color, light-dark(#e7e5e4, #44403c));
          --_cui-navigation-menu-trigger-background: var(--cui-navigation-menu-trigger-background, transparent);
          --_cui-navigation-menu-trigger-hover-background:
            var(--cui-navigation-menu-trigger-hover-background, light-dark(#f5f5f4, #292524));
          --_cui-navigation-menu-trigger-open-background:
            var(--cui-navigation-menu-trigger-open-background, light-dark(#e7e5e4, #44403c));
          --_cui-navigation-menu-focus-color: var(--cui-navigation-menu-focus-color, Highlight);
          --_cui-navigation-menu-radius: var(--cui-navigation-menu-radius, 0.75rem);
          --_cui-navigation-menu-gap: var(--cui-navigation-menu-gap, 0.25rem);
          --_cui-navigation-menu-padding: var(--cui-navigation-menu-padding, 0.35rem);
          --_cui-navigation-menu-panel-background: var(--cui-navigation-menu-panel-background, Canvas);
          --_cui-navigation-menu-panel-inline-size: var(--cui-navigation-menu-panel-inline-size, 24rem);
          --_cui-navigation-menu-panel-max-inline-size:
            var(--cui-navigation-menu-panel-max-inline-size, calc(100vw - 2rem));
          --_cui-navigation-menu-panel-padding: var(--cui-navigation-menu-panel-padding, 1rem);
          --_cui-navigation-menu-panel-shadow:
            var(--cui-navigation-menu-panel-shadow,
              0 18px 45px light-dark(rgb(28 25 23 / 0.16), rgb(0 0 0 / 0.45)));
          --_cui-navigation-menu-offset: var(--cui-navigation-menu-offset, 0.45rem);
          --_cui-navigation-menu-duration: var(--cui-navigation-menu-duration, 150ms);
          --_cui-navigation-menu-easing: var(--cui-navigation-menu-easing, ease-out);
          position: relative;
          z-index: 1;
          color: var(--_cui-navigation-menu-foreground);
          background: var(--_cui-navigation-menu-background);
        }
        :where([data-citry-ui-part="navigation-menu"] > [data-citry-ui-part="list"]) {
          display: flex;
          align-items: center;
          gap: var(--_cui-navigation-menu-gap);
          margin: 0;
          padding: var(--_cui-navigation-menu-padding);
          list-style: none;
        }
        :where([data-citry-ui-part="navigation-menu"][data-orientation="vertical"] > [data-citry-ui-part="list"]) {
          display: grid;
          align-items: stretch;
        }
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="link-item"]),
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="item"]) {
          position: relative;
          min-inline-size: 0;
        }
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="link"]),
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="trigger"]) {
          box-sizing: border-box;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 0.45rem;
          min-block-size: 2.5rem;
          padding: 0.55rem 0.8rem;
          border: 0;
          border-radius: calc(var(--_cui-navigation-menu-radius) - 0.2rem);
          color: inherit;
          background: var(--_cui-navigation-menu-trigger-background);
          font: inherit;
          font-weight: 620;
          line-height: 1.2;
          text-align: start;
          text-decoration: none;
          cursor: pointer;
        }
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="link"]:hover),
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="trigger"]:hover) {
          background: var(--_cui-navigation-menu-trigger-hover-background);
        }
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="trigger"][data-open]) {
          background: var(--_cui-navigation-menu-trigger-open-background);
        }
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="link"]:focus-visible),
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="trigger"]:focus-visible),
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="panel"] :focus-visible) {
          outline: 3px solid var(--_cui-navigation-menu-focus-color);
          outline-offset: 2px;
        }
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="indicator"]) {
          inline-size: 0.48rem;
          block-size: 0.48rem;
          border-inline-end: 0.12rem solid currentColor;
          border-block-end: 0.12rem solid currentColor;
          transform: translateY(-0.12rem) rotate(45deg);
          transition: transform var(--_cui-navigation-menu-duration) var(--_cui-navigation-menu-easing);
        }
        :where([data-citry-ui-part="navigation-menu"]
          [data-citry-ui-part="trigger"][data-open]
          [data-citry-ui-part="indicator"]) {
          transform: translateY(0.08rem) rotate(225deg);
        }
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="panel"]) {
          box-sizing: border-box;
          position: absolute;
          inset-block-start: calc(100% + var(--_cui-navigation-menu-offset));
          inset-inline-start: 0;
          z-index: 2;
          inline-size:
            min(var(--_cui-navigation-menu-panel-inline-size), var(--_cui-navigation-menu-panel-max-inline-size));
          min-inline-size: 0;
          max-inline-size: var(--_cui-navigation-menu-panel-max-inline-size);
          padding: var(--_cui-navigation-menu-panel-padding);
          overflow-wrap: anywhere;
          border: 1px solid var(--_cui-navigation-menu-border-color);
          border-radius: var(--_cui-navigation-menu-radius);
          color: var(--_cui-navigation-menu-foreground);
          background: var(--_cui-navigation-menu-panel-background);
          box-shadow: var(--_cui-navigation-menu-panel-shadow);
          transform: translateX(var(--_cui-navigation-menu-panel-shift, 0px));
        }
        :where([data-citry-ui-part="navigation-menu"]
          [data-citry-ui-part="panel"][data-cui-navigation-menu-align-end]) {
          inset-inline-start: auto;
          inset-inline-end: 0;
        }
        :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="panel"][hidden]) {
          display: none !important;
        }
        :where([data-citry-ui-part="navigation-menu"][data-orientation="vertical"] [data-citry-ui-part="panel"]) {
          position: static;
          inline-size: 100%;
          margin-block-start: var(--_cui-navigation-menu-offset);
          box-shadow: none;
        }
        :where([data-citry-ui-part="navigation-menu"][data-variant="surface"]) {
          border: 1px solid var(--_cui-navigation-menu-border-color);
          border-radius: var(--_cui-navigation-menu-radius);
          background: var(--_cui-navigation-menu-panel-background);
        }
        :where([data-citry-ui-part="navigation-menu"][data-size="sm"]) {
          font-size: 0.875rem;
          --_cui-navigation-menu-padding: 0.25rem;
        }
        :where([data-citry-ui-part="navigation-menu"][data-size="lg"]) {
          font-size: 1.0625rem;
          --_cui-navigation-menu-padding: 0.45rem;
        }
        :where([data-citry-ui-part="navigation-menu"][data-disabled]),
        :where([data-citry-ui-part="navigation-menu"] [data-disabled]) {
          opacity: 0.55;
        }
        :where([data-citry-ui-part="navigation-menu"][data-disabled] [data-citry-ui-part="link"]),
        :where([data-citry-ui-part="navigation-menu"] [data-disabled] [data-citry-ui-part="trigger"]) {
          cursor: not-allowed;
        }
        @media (prefers-reduced-motion: reduce) {
          :where([data-citry-ui-part="navigation-menu"]) {
            --_cui-navigation-menu-duration: 0ms;
          }
        }
        @media (forced-colors: active) {
          :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="panel"]) {
            border-color: CanvasText;
            box-shadow: none;
          }
          :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="trigger"][data-open]) {
            outline: 1px solid CanvasText;
          }
        }
        @media print {
          :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="item"]) {
            display: none;
          }
          :where([data-citry-ui-part="navigation-menu"] [data-citry-ui-part="link"]) {
            color: black;
            background: transparent;
          }
        }
      }
    """


class CNavigationMenuLink(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        href: str
        current: bool = False
        target: str | None = None
        rel: str | None = None
        download: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        link_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CNavigationMenuLinkDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        context = _context(self)
        context.count += 1
        self.unprovide(_CONTEXT_KEY)
        validate_boolean("CNavigationMenuLink", "current", kwargs.current)
        return {
            "href": _plain("CNavigationMenuLink href", kwargs.href),
            "current": bool(kwargs.current),
            "target": _plain("CNavigationMenuLink target", kwargs.target, optional=True),
            "rel": _plain("CNavigationMenuLink rel", kwargs.rel, optional=True),
            "download": _plain("CNavigationMenuLink download", kwargs.download, optional=True),
            "attrs": merge_root_attrs(
                _attrs("CNavigationMenuLink", kwargs.attrs, _LINK_ITEM_OWNED),
                kwargs.class_,
                kwargs.style,
            ),
            "link_attrs": _attrs("CNavigationMenuLink link", kwargs.link_attrs, _LINK_OWNED),
        }

    template = """
      <li class="cui-navigation-menu__link-item" c-bind="attrs" data-citry-ui-part="link-item">
        <a
          c-bind="link_attrs"
          c-href="href"
          c-target="target"
          c-rel="rel"
          c-download="download"
          c-aria-current="'page' if current else None"
          data-citry-navigation-menu-link
          data-citry-ui-part="link"
        ><c-slot required /></a>
      </li>
    """


class CNavigationMenuItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        disabled: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        trigger_attrs: Mapping[str, object] | None = None
        panel_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        label: SlotInput[CNavigationMenuItemLabelSlotData]
        default: SlotInput[CNavigationMenuItemDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        context = _context(self)
        value = _plain("CNavigationMenuItem value", kwargs.value)
        if value in context.values:
            raise ValueError(f"CNavigationMenuItem value {value!r} is duplicated.")
        context.values.add(value)
        context.count += 1
        self.unprovide(_CONTEXT_KEY)
        validate_boolean("CNavigationMenuItem", "disabled", kwargs.disabled)
        token = f"{self.id}"
        trigger_id = f"{context.root_id}-trigger-{token}"
        panel_id = f"{context.root_id}-panel-{token}"
        open_ = context.selected_value == value and not context.disabled and not kwargs.disabled
        return {
            "value": value,
            "disabled": bool(kwargs.disabled) or context.disabled,
            "open": open_,
            "trigger_id": trigger_id,
            "panel_id": panel_id,
            "attrs": merge_root_attrs(
                _attrs("CNavigationMenuItem", kwargs.attrs, _ITEM_OWNED),
                kwargs.class_,
                kwargs.style,
            ),
            "trigger_attrs": _attrs("CNavigationMenuItem trigger", kwargs.trigger_attrs, _TRIGGER_OWNED),
            "panel_attrs": _attrs("CNavigationMenuItem panel", kwargs.panel_attrs, _PANEL_OWNED),
        }

    template = """
      <li
        class="cui-navigation-menu__item"
        c-bind="attrs"
        c-data-value="value"
        c-data-disabled="disabled"
        c-data-open="open"
        data-citry-navigation-menu-item
        data-citry-ui-part="item"
      >
        <button
          class="cui-navigation-menu__trigger"
          c-bind="trigger_attrs"
          c-id="trigger_id"
          type="button"
          c-disabled="disabled"
          c-aria-controls="panel_id"
          c-aria-expanded="'true' if open else 'false'"
          c-data-value="value"
          c-data-disabled="disabled"
          c-data-open="open"
          data-citry-navigation-menu-trigger
          data-citry-ui-part="trigger"
        >
          <span><c-slot name="label" required /></span>
          <span aria-hidden="true" data-citry-ui-part="indicator"></span>
        </button>
        <div
          class="cui-navigation-menu__panel"
          c-bind="panel_attrs"
          c-id="panel_id"
          c-data-value="value"
          c-data-open="open"
          c-hidden="not open"
          c-inert="not open"
          data-citry-navigation-menu-panel
          data-citry-ui-part="panel"
        ><c-slot required /></div>
      </li>
    """


__all__ = [
    "CNavigationMenu",
    "CNavigationMenuDefaultSlotData",
    "CNavigationMenuItem",
    "CNavigationMenuItemDefaultSlotData",
    "CNavigationMenuItemLabelSlotData",
    "CNavigationMenuLink",
    "CNavigationMenuLinkDefaultSlotData",
    "CNavigationMenuOrientation",
    "CNavigationMenuSize",
    "CNavigationMenuValueChangeDetail",
    "CNavigationMenuVariant",
]
