"""Styled noninteractive Tooltip component family."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._anchored_layer import (
    ANCHORED_LAYER_RUNTIME_DEPENDENCY,
    ANCHORED_LAYER_RUNTIME_JS,
)
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CTooltipPlacement = Literal[
    "top-start",
    "top",
    "top-end",
    "bottom-start",
    "bottom",
    "bottom-end",
]


class CTooltipOpenChangeDetail(TypedDict):
    reason: Literal[
        "hover",
        "focus",
        "pointer-leave",
        "blur",
        "escape",
        "press",
        "peer",
        "native",
        "ancestor",
        "modal",
    ]
    controlled: bool
    forced: bool
    source: object | None


class CTooltipActivatorSlotData:
    activator_attrs: dict[str, object]
    tooltip_id: str


class CTooltipDefaultSlotData:
    pass


_PLACEMENTS = (
    "top-start",
    "top",
    "top-end",
    "bottom-start",
    "bottom",
    "bottom-end",
)
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
_SURFACE_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-live",
        "aria-roledescription",
        "autofocus",
        "contenteditable",
        "data-citry-tooltip-exiting",
        "data-citry-tooltip-initialized",
        "data-citry-ui-part",
        "data-open",
        "data-placement",
        "hidden",
        "id",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)


def _plain_optional_string(input_name: str, value: object) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CTooltip {input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CTooltip could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain


def _plain_html_id(value: object) -> str | None:
    plain = _plain_optional_string("id", value)
    if plain is None:
        return None
    if not plain or any(character in "\t\n\f\r " for character in plain):
        msg = "CTooltip id must be non-empty and cannot contain ASCII whitespace."
        raise ValueError(msg)
    if "\0" in plain:
        msg = "CTooltip id cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _plain_text(value: object) -> str | None:
    plain = _plain_optional_string("text", value)
    if plain is not None and (not plain.strip() or "\0" in plain):
        msg = "CTooltip text must be nonempty and cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _plain_placement(value: object) -> str:
    plain = _plain_optional_string("placement", value)
    if plain is None or plain not in _PLACEMENTS:
        expected = ", ".join(repr(item) for item in _PLACEMENTS)
        msg = f"CTooltip placement must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _milliseconds(input_name: str, value: object) -> int:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        msg = f"CTooltip {input_name} must be an integer, got {raw!r}."
        raise TypeError(msg)
    if raw < 0 or raw > 60_000:
        msg = f"CTooltip {input_name} must be between 0 and 60000, got {raw!r}."
        raise ValueError(msg)
    return raw


def _copy_attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        msg = f"CTooltip attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    return dict(attrs)


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _validate_attrs(attrs: dict[str, object]) -> None:
    reject_owned_attrs(attrs, _SURFACE_OWNED_ATTRS, "CTooltip")
    for key in attrs:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CTooltip attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CTooltip attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in _SURFACE_OWNED_ATTRS:
            msg = f"CTooltip attrs cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)


class CTooltip(LibraryComponent):
    class Dependencies:
        js = (ANCHORED_LAYER_RUNTIME_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        text: str | None = None
        open: bool = False
        disabled: bool = False
        delay: int = 600
        close_delay: int = 100
        placement: CTooltipPlacement = "top"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        activator: SlotInput[CTooltipActivatorSlotData]
        default: SlotInput[CTooltipDefaultSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_tooltip_snapshot", None)
        if cached is not None:
            return cached

        tooltip_id = _plain_html_id(kwargs.id) or f"cui-tooltip-{self.id}"
        text = _plain_text(kwargs.text)
        has_default = "default" in self.raw_slots
        if (text is None) == (not has_default):
            msg = "CTooltip requires exactly one of text or a default fill."
            raise ValueError(msg)
        validate_boolean("CTooltip", "open", kwargs.open)
        validate_boolean("CTooltip", "disabled", kwargs.disabled)
        delay = _milliseconds("delay", kwargs.delay)
        close_delay = _milliseconds("close_delay", kwargs.close_delay)
        placement = _plain_placement(kwargs.placement)
        attrs = _copy_attrs(kwargs.attrs)
        _validate_attrs(attrs)
        anchor_name = f"--_cui-tooltip-anchor-ref-{self.id}"
        generated_anchor_style = {"--_cui-tooltip-anchor": anchor_name}
        surface_style: CStyleValue = (
            generated_anchor_style if kwargs.style is None else (kwargs.style, generated_anchor_style)
        )
        snapshot: dict[str, object] = {
            "tooltip_id": tooltip_id,
            "tooltip_text": text,
            "uses_text": text is not None,
            "open": bool(kwargs.open),
            "disabled": bool(kwargs.disabled),
            "delay": delay,
            "close_delay": close_delay,
            "placement": placement,
            "activator_attrs": {
                "aria-describedby": tooltip_id,
                "data-citry-tooltip-trigger": "",
                "style": {"anchor-name": anchor_name},
            },
            "attrs": merge_root_attrs(attrs, kwargs.class_, surface_style),
        }
        self._cui_tooltip_snapshot = snapshot
        return snapshot

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return self._snapshot(kwargs)

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        snapshot = self._snapshot(kwargs)
        return {
            "text": snapshot["tooltip_text"],
            "usesText": snapshot["uses_text"],
            "open": snapshot["open"],
            "disabled": snapshot["disabled"],
            "delay": snapshot["delay"],
            "closeDelay": snapshot["close_delay"],
            "placement": snapshot["placement"],
        }

    template = """
      <div
        class="cui-tooltip-host"
        data-citry-tooltip-host
      >
        <c-slot
          name="activator"
          c-activator_attrs="activator_attrs"
          c-tooltip_id="tooltip_id"
          required
        />
        <div
          class="cui-tooltip"
          c-id="tooltip_id"
          c-data-open="open and not disabled"
          c-data-placement="placement"
          c-bind="attrs"
          popover="manual"
          role="tooltip"
          data-citry-ui-part="tooltip"
        >
          <c-if cond="uses_text">
            <span data-citry-tooltip-text>
              {{ tooltip_text }}
            </span>
          </c-if>
          <c-else>
            <c-slot />
          </c-else>
        </div>
      </div>
    """

    js = (
        ANCHORED_LAYER_RUNTIME_JS
        + r"""
      const handoffKey = Symbol.for("citry-ui:tooltip-handoff");

      $component({
        props: {
          open: {},
          text: {},
          disabled: {},
          delay: {},
          closeDelay: {},
          placement: {},
          onOpenChange: {},
        },
        init: ({ els, data, props, effect }) => {
          const host = els[0];
          const nearestHost = (element) => (
            element?.closest?.("[data-citry-tooltip-host]") ?? null
          );
          const surface = [...host.querySelectorAll('[data-citry-ui-part="tooltip"]')]
            .find((candidate) => nearestHost(candidate) === host);
          const triggers = [...host.querySelectorAll("[data-citry-tooltip-trigger]")]
            .filter((candidate) => nearestHost(candidate) === host);
          if (
            !surface
            || triggers.length !== 1
            || !(triggers[0] instanceof HTMLElement)
            || triggers[0].parentElement !== host
          ) {
            throw new Error(
              "[citry-ui] CTooltip activator must spread activator_attrs onto exactly one HTMLElement.",
            );
          }
          const trigger = triggers[0];
          const layerCoordinator = anchoredLayerRuntime.coordinatorFor(surface);
          if (
            trigger.matches(":disabled")
            || trigger.matches('[aria-disabled="true"]')
            || trigger.tabIndex < 0
          ) {
            throw new Error("[citry-ui] CTooltip activator must be enabled and focusable.");
          }
          const anchorName = getComputedStyle(surface)
            .getPropertyValue("--_cui-tooltip-anchor")
            .trim();
          if (!anchorName.startsWith("--")) {
            throw new Error("[citry-ui] CTooltip could not resolve its CSS anchor name.");
          }
          // Reassert private CSS-anchor ownership after authored trigger and
          // surface styles have initialized.
          trigger.style.setProperty("anchor-name", anchorName);
          surface.style.setProperty("position-anchor", anchorName);

          const idTokens = new Set(
            (trigger.getAttribute("aria-describedby") ?? "")
              .split(/\s+/)
              .filter(Boolean),
          );
          idTokens.add(surface.id);
          trigger.setAttribute("aria-describedby", [...idTokens].join(" "));

          const interactiveSelector = [
            "a[href]",
            "area[href]",
            "button",
            "input",
            "select",
            "textarea",
            "summary",
            "details",
            "iframe",
            "object",
            "embed",
            "audio[controls]",
            "video[controls]",
            "[contenteditable]:not([contenteditable='false'])",
            "[tabindex]",
            "[role='button']",
            "[role='link']",
            "[role='checkbox']",
            "[role='radio']",
            "[role='switch']",
            "[role='textbox']",
            "[role='combobox']",
            "[role='menuitem']",
            "[role='option']",
            "[role='tooltip']",
            "[data-citry-tooltip-host]",
          ].join(",");
          if (surface.querySelector(interactiveSelector)) {
            throw new Error("[citry-ui] CTooltip content must be noninteractive.");
          }

          const allowedPlacements = [
            "top-start",
            "top",
            "top-end",
            "bottom-start",
            "bottom",
            "bottom-end",
          ];
          const invalidEpisodes = new Set();
          const initialHandoff = surface[handoffKey];
          delete surface[handoffKey];
          let active = true;
          let controlled = false;
          let logicalOpen = false;
          let internalOpen = initialHandoff?.open ?? data.open;
          let onOpenChange = null;
          let animation = null;
          let generation = 0;
          let pendingRequest = null;
          let openTimer = null;
          let closeTimer = null;
          let triggerHovered = false;
          let surfaceHovered = false;
          let triggerFocused = false;
          let suppressedTouchFocus = false;
          let dismissedWhileActive = false;
          let configuration = {
            disabled: data.disabled,
            delay: data.delay,
            closeDelay: data.closeDelay,
            placement: data.placement,
          };

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value) => {
            if (invalidEpisodes.has(name)) {
              return;
            }
            invalidEpisodes.add(name);
            console.error(
              `[citry-ui] CTooltip ${name} received invalid client value `
                + `${describeValue(value)}; using the server-rendered fallback.`,
              surface,
            );
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
          const resolveMilliseconds = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (Number.isInteger(value) && value >= 0 && value <= 60000) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return data[name];
          };
          const resolvePlacement = () => {
            const value = props.placement === undefined ? data.placement : props.placement;
            if (allowedPlacements.includes(value)) {
              invalidEpisodes.delete("placement");
              return value;
            }
            reportInvalid("placement", value);
            return data.placement;
          };
          const resolveCallback = () => {
            const value = props.onOpenChange;
            if (value === undefined || value === null || typeof value === "function") {
              invalidEpisodes.delete("onOpenChange");
              return value ?? null;
            }
            reportInvalid("onOpenChange", value);
            return null;
          };
          const resolveText = () => {
            if (!data.usesText) {
              if (props.text !== undefined && props.text !== null) {
                reportInvalid("text", props.text);
              } else {
                invalidEpisodes.delete("text");
              }
              return;
            }
            const value = props.text === undefined ? data.text : props.text;
            if (typeof value !== "string" || !value.trim() || value.includes("\0")) {
              reportInvalid("text", value);
              surface.querySelector("[data-citry-tooltip-text]").textContent = data.text;
              return;
            }
            invalidEpisodes.delete("text");
            surface.querySelector("[data-citry-tooltip-text]").textContent = value;
          };
          const clearOpenTimer = () => {
            clearTimeout(openTimer);
            openTimer = null;
          };
          const clearCloseTimer = () => {
            clearTimeout(closeTimer);
            closeTimer = null;
          };
          const cancelAnimation = () => {
            generation += 1;
            animation?.cancel();
            animation = null;
          };
          const duration = () => {
            const raw = getComputedStyle(surface)
              .getPropertyValue("--_cui-tooltip-duration")
              .trim();
            if (raw.endsWith("ms")) {
              return Math.max(0, Number.parseFloat(raw) || 0);
            }
            if (raw.endsWith("s")) {
              return Math.max(0, (Number.parseFloat(raw) || 0) * 1000);
            }
            return Math.max(0, Number.parseFloat(raw) || 0);
          };
          const easing = () => getComputedStyle(surface)
            .getPropertyValue("--_cui-tooltip-easing")
            .trim() || "ease";
          const finishNativeClose = (currentGeneration) => {
            if (!active || logicalOpen || currentGeneration !== generation) {
              return;
            }
            if (surface.matches(":popover-open")) {
              surface.hidePopover();
            }
            surface.removeAttribute("data-citry-tooltip-exiting");
          };
          const animateEntry = (currentGeneration) => {
            const milliseconds = duration();
            if (milliseconds === 0) {
              return;
            }
            animation = surface.animate(
              [
                { opacity: 0, transform: "translateY(0.125rem) scale(0.98)" },
                { opacity: 1, transform: "none" },
              ],
              { duration: milliseconds, easing: easing() },
            );
            animation.finished.catch(() => {}).finally(() => {
              if (currentGeneration === generation) {
                animation = null;
              }
            });
          };
          const animateExit = (currentGeneration) => {
            const milliseconds = duration();
            if (milliseconds === 0 || !surface.matches(":popover-open")) {
              finishNativeClose(currentGeneration);
              return;
            }
            animation = surface.animate(
              [
                { opacity: 1, transform: "none" },
                { opacity: 0, transform: "translateY(0.125rem) scale(0.98)" },
              ],
              { duration: milliseconds, easing: easing() },
            );
            animation.finished.catch(() => {}).finally(() => {
              if (currentGeneration !== generation) {
                return;
              }
              animation = null;
              finishNativeClose(currentGeneration);
            });
          };
          const layer = {
            surface,
            trigger,
            isOpen: () => active && logicalOpen,
            requestDismiss: (reason, source) => {
              dismissedWhileActive = true;
              if (reason === "escape") {
                requestOpen(false, "escape", source);
              } else if (reason === "focus-outside") {
                requestOpen(false, "blur", source);
              } else {
                requestOpen(false, "pointer-leave", source);
              }
            },
            forceClose: (reason, source) => forceCloseLayer(reason, source),
          };
          const releaseTooltipWarmth = () => {
            if (layerCoordinator.tooltipLayer === layer) {
              layerCoordinator.tooltipLayer = null;
              layerCoordinator.tooltipWarmUntil = performance.now() + 300;
            }
          };
          const claimTooltipWarmth = () => {
            if (layerCoordinator.tooltipLayer && layerCoordinator.tooltipLayer !== layer) {
              layerCoordinator.tooltipLayer.requestPeerClose(surface);
            }
            layerCoordinator.tooltipLayer = layer;
            layerCoordinator.tooltipWarmUntil = Number.POSITIVE_INFINITY;
          };
          const applyOpen = (nextOpen, context = null) => {
            const visible = nextOpen && !configuration.disabled;
            if (visible === logicalOpen) {
              if (
                visible
                && !layerCoordinator.register(layer)
                && logicalOpen
              ) {
                forceCloseLayer(
                  layerCoordinator.blockedReason(layer) ?? "ancestor",
                  surface,
                );
              }
              return;
            }
            cancelAnimation();
            const currentGeneration = generation;
            if (visible) {
              if (!layerCoordinator.mayOpen(layer)) {
                if (!controlled) {
                  internalOpen = false;
                }
                return;
              }
              try {
                if (!surface.matches(":popover-open")) {
                  surface.showPopover();
                }
              } catch (error) {
                console.error("[citry-ui] CTooltip could not enter the top layer:", error, surface);
                logicalOpen = false;
                internalOpen = false;
                return;
              }
              logicalOpen = true;
              surface.removeAttribute("data-citry-tooltip-exiting");
              surface.setAttribute("data-open", "");
              if (!layerCoordinator.register(layer)) {
                logicalOpen = false;
                surface.hidePopover();
                surface.removeAttribute("data-open");
                return;
              }
              claimTooltipWarmth();
              animateEntry(currentGeneration);
              return;
            }
            logicalOpen = false;
            surface.removeAttribute("data-open");
            surface.setAttribute("data-citry-tooltip-exiting", "");
            layerCoordinator.unregister(layer);
            releaseTooltipWarmth();
            animateExit(currentGeneration);
          };
          const notify = (nextOpen, reason, source, forced = false) => {
            onOpenChange?.(nextOpen, {
              reason,
              controlled,
              forced,
              source,
            });
          };
          const requestOpen = (nextOpen, reason, source) => {
            if (configuration.disabled || nextOpen === logicalOpen) {
              return;
            }
            if (nextOpen) {
              layerCoordinator.clearSuppression(layer);
            }
            if (controlled) {
              pendingRequest = { nextOpen, reason, source };
              notify(nextOpen, reason, source);
              return;
            }
            internalOpen = nextOpen;
            applyOpen(nextOpen, { reason, source });
            notify(nextOpen, reason, source);
          };
          const forceCloseLayer = (reason, source) => {
            clearOpenTimer();
            clearCloseTimer();
            dismissedWhileActive = reason !== "ancestor";
            if (reason === "ancestor") {
              suppressedTouchFocus = false;
            }
            if (!logicalOpen) {
              internalOpen = false;
              pendingRequest = null;
              return;
            }
            pendingRequest = null;
            internalOpen = false;
            applyOpen(false, { reason, source });
            notify(false, reason, source, true);
          };
          layer.requestPeerClose = (source) => {
            dismissedWhileActive = true;
            requestOpen(false, "peer", source);
          };
          const maybeClearLatch = () => {
            if (!triggerHovered && !surfaceHovered && !triggerFocused) {
              dismissedWhileActive = false;
              suppressedTouchFocus = false;
            }
          };
          const scheduleOpen = (reason, source) => {
            clearCloseTimer();
            if (configuration.disabled || dismissedWhileActive) {
              return;
            }
            clearOpenTimer();
            const warmed = layerCoordinator.tooltipWarmUntil === Number.POSITIVE_INFINITY
              || performance.now() <= layerCoordinator.tooltipWarmUntil;
            const milliseconds = reason === "focus" || warmed ? 0 : configuration.delay;
            if (milliseconds === 0) {
              requestOpen(true, reason, source);
              return;
            }
            openTimer = setTimeout(() => {
              openTimer = null;
              if (active && triggerHovered && !dismissedWhileActive) {
                requestOpen(true, reason, source);
              }
            }, milliseconds);
          };
          const scheduleClose = (reason, source, options = {}) => {
            const { immediate = false } = options;
            clearOpenTimer();
            clearCloseTimer();
            if (triggerHovered || surfaceHovered || triggerFocused) {
              return;
            }
            const milliseconds = immediate ? 0 : configuration.closeDelay;
            if (milliseconds === 0) {
              requestOpen(false, reason, source);
              return;
            }
            closeTimer = setTimeout(() => {
              closeTimer = null;
              if (active && !triggerHovered && !surfaceHovered && !triggerFocused) {
                requestOpen(false, reason, source);
              }
            }, milliseconds);
          };
          const onTriggerPointerEnter = (event) => {
            if (event.pointerType === "touch") {
              return;
            }
            triggerHovered = true;
            scheduleOpen("hover", trigger);
          };
          const onTriggerPointerLeave = (event) => {
            if (event.pointerType === "touch") {
              return;
            }
            triggerHovered = false;
            maybeClearLatch();
            scheduleClose("pointer-leave", trigger);
          };
          const onSurfacePointerEnter = (event) => {
            if (event.pointerType === "touch") {
              return;
            }
            surfaceHovered = true;
            clearCloseTimer();
          };
          const onSurfacePointerLeave = (event) => {
            if (event.pointerType === "touch") {
              return;
            }
            surfaceHovered = false;
            maybeClearLatch();
            scheduleClose("pointer-leave", surface);
          };
          const onTriggerFocus = (event) => {
            triggerFocused = true;
            if (suppressedTouchFocus) {
              return;
            }
            scheduleOpen("focus", event.target);
          };
          const onTriggerBlur = (event) => {
            triggerFocused = false;
            if (layerCoordinator.isAncestorClosing(layer)) {
              return;
            }
            maybeClearLatch();
            scheduleClose("blur", event.target, { immediate: true });
          };
          const onTriggerPointerDown = (event) => {
            if (event.pointerType === "touch") {
              suppressedTouchFocus = true;
              dismissedWhileActive = true;
              clearOpenTimer();
              requestOpen(false, "press", event.target);
              return;
            }
            if (logicalOpen) {
              dismissedWhileActive = true;
              requestOpen(false, "press", event.target);
            }
          };
          const onToggle = (event) => {
            if (event.target !== surface) {
              return;
            }
            const nativeOpen = surface.matches(":popover-open");
            if (nativeOpen === logicalOpen || (!logicalOpen && animation)) {
              return;
            }
            cancelAnimation();
            if (nativeOpen) {
              if (!layerCoordinator.mayOpen(layer)) {
                surface.hidePopover();
                notify(
                  false,
                  layerCoordinator.blockedReason(layer) ?? "ancestor",
                  surface,
                  true,
                );
                return;
              }
              if (controlled || configuration.disabled) {
                surface.hidePopover();
                notify(true, "native", surface);
                return;
              }
              internalOpen = true;
              logicalOpen = true;
              surface.setAttribute("data-open", "");
              if (!layerCoordinator.register(layer)) {
                logicalOpen = false;
                internalOpen = false;
                surface.hidePopover();
                surface.removeAttribute("data-open");
                notify(
                  false,
                  layerCoordinator.blockedReason(layer) ?? "ancestor",
                  surface,
                  true,
                );
                return;
              }
              claimTooltipWarmth();
              notify(true, "native", surface);
              return;
            }
            if (controlled && !configuration.disabled) {
              if (!layerCoordinator.mayOpen(layer)) {
                forceCloseLayer(
                  layerCoordinator.blockedReason(layer) ?? "ancestor",
                  surface,
                );
                return;
              }
              try {
                surface.showPopover();
              } catch (error) {
                console.error(
                  "[citry-ui] CTooltip could not restore controlled native visibility:",
                  error,
                  surface,
                );
              }
              notify(false, "native", surface);
              return;
            }
            logicalOpen = false;
            internalOpen = false;
            surface.removeAttribute("data-open");
            surface.removeAttribute("data-citry-tooltip-exiting");
            layerCoordinator.unregister(layer);
            releaseTooltipWarmth();
            notify(false, "native", surface);
          };

          trigger.addEventListener("pointerenter", onTriggerPointerEnter);
          trigger.addEventListener("pointerleave", onTriggerPointerLeave);
          trigger.addEventListener("pointerdown", onTriggerPointerDown, true);
          trigger.addEventListener("focus", onTriggerFocus);
          trigger.addEventListener("blur", onTriggerBlur);
          surface.addEventListener("pointerenter", onSurfacePointerEnter);
          surface.addEventListener("pointerleave", onSurfacePointerLeave);
          surface.addEventListener("toggle", onToggle);
          effect(() => {
            const suppliedOpen = props.open;
            let nextOpen = internalOpen;
            if (suppliedOpen === undefined || suppliedOpen === null) {
              if (controlled) {
                internalOpen = logicalOpen;
              }
              controlled = false;
              pendingRequest = null;
              nextOpen = internalOpen;
              invalidEpisodes.delete("open");
            } else if (typeof suppliedOpen === "boolean") {
              controlled = true;
              nextOpen = suppliedOpen;
              invalidEpisodes.delete("open");
            } else {
              reportInvalid("open", suppliedOpen);
              if (controlled) {
                internalOpen = logicalOpen;
              }
              controlled = false;
              pendingRequest = null;
              nextOpen = internalOpen;
            }
            configuration = {
              disabled: resolveBoolean("disabled"),
              delay: resolveMilliseconds("delay"),
              closeDelay: resolveMilliseconds("closeDelay"),
              placement: resolvePlacement(),
            };
            onOpenChange = resolveCallback();
            resolveText();
            surface.dataset.placement = configuration.placement;
            if (configuration.disabled) {
              clearOpenTimer();
              clearCloseTimer();
            }
            if (!nextOpen) {
              layerCoordinator.clearSuppression(layer);
            }
            const context = pendingRequest?.nextOpen === nextOpen ? pendingRequest : null;
            applyOpen(nextOpen, context);
            if (context || nextOpen === logicalOpen) {
              pendingRequest = null;
            }
          });
          host.setAttribute("data-citry-tooltip-initialized", "");

          return () => {
            active = false;
            surface[handoffKey] = { open: logicalOpen };
            trigger.removeEventListener("pointerenter", onTriggerPointerEnter);
            trigger.removeEventListener("pointerleave", onTriggerPointerLeave);
            trigger.removeEventListener("pointerdown", onTriggerPointerDown, true);
            trigger.removeEventListener("focus", onTriggerFocus);
            trigger.removeEventListener("blur", onTriggerBlur);
            surface.removeEventListener("pointerenter", onSurfacePointerEnter);
            surface.removeEventListener("pointerleave", onSurfacePointerLeave);
            surface.removeEventListener("toggle", onToggle);
            clearOpenTimer();
            clearCloseTimer();
            cancelAnimation();
            layerCoordinator.unregister(layer);
            releaseTooltipWarmth();
            if (surface.matches(":popover-open")) {
              surface.hidePopover();
            }
            surface.removeAttribute("data-open");
            surface.removeAttribute("data-citry-tooltip-exiting");
            host.removeAttribute("data-citry-tooltip-initialized");
          };
        },
      });
    """
    )

    css = """
      @layer citry-ui.theme {
        :where(.cui-tooltip-host) {
          display: contents;
        }

        :where(.cui-tooltip) {
          --_cui-tooltip-background: var(
            --cui-tooltip-background,
            light-dark(#172033, #f4f7fb)
          );
          --_cui-tooltip-foreground: var(
            --cui-tooltip-foreground,
            light-dark(#ffffff, #172033)
          );
          --_cui-tooltip-border-color: var(
            --cui-tooltip-border-color,
            color-mix(in srgb, currentColor 18%, transparent)
          );
          --_cui-tooltip-border-width: var(--cui-tooltip-border-width, 1px);
          --_cui-tooltip-radius: var(--cui-tooltip-radius, 0.375rem);
          --_cui-tooltip-shadow: var(
            --cui-tooltip-shadow,
            0 0.5rem 1.25rem rgb(15 23 42 / 24%)
          );
          --_cui-tooltip-max-inline-size: var(--cui-tooltip-max-inline-size, 18rem);
          --_cui-tooltip-padding-block: var(--cui-tooltip-padding-block, 0.375rem);
          --_cui-tooltip-padding-inline: var(--cui-tooltip-padding-inline, 0.625rem);
          --_cui-tooltip-offset: var(--cui-tooltip-offset, 0.375rem);
          --_cui-tooltip-duration: var(--cui-tooltip-duration, 100ms);
          --_cui-tooltip-easing: var(
            --cui-tooltip-easing,
            cubic-bezier(0.2, 0.8, 0.2, 1)
          );

          box-sizing: border-box;
          position: fixed;
          position-anchor: var(--_cui-tooltip-anchor);
          position-try-fallbacks: flip-block, flip-inline, flip-block flip-inline;
          position-visibility: anchors-visible;
          display: block;
          inline-size: max-content;
          max-inline-size: min(
            var(--_cui-tooltip-max-inline-size),
            calc(100dvi - 1rem)
          );
          margin: 0;
          padding-block: var(--_cui-tooltip-padding-block);
          padding-inline: var(--_cui-tooltip-padding-inline);
          overflow-wrap: anywhere;
          border: var(--_cui-tooltip-border-width) solid var(--_cui-tooltip-border-color);
          border-radius: var(--_cui-tooltip-radius);
          background: var(--_cui-tooltip-background);
          color: var(--_cui-tooltip-foreground);
          box-shadow: var(--_cui-tooltip-shadow);
          font-family: ui-sans-serif, system-ui, sans-serif;
          font-size: 0.8125rem;
          font-weight: 500;
          line-height: 1.35;
          text-align: start;
          user-select: text;
        }

        :where(
          .cui-tooltip:not(:popover-open):not([data-open]):not(
            [data-citry-tooltip-exiting]
          )
        ) {
          display: none;
        }

        :where(.cui-tooltip[data-open]:not(:popover-open)) {
          position: static;
          display: block;
          inline-size: fit-content;
          margin-block: 0.25rem;
        }

        :where(.cui-tooltip[data-citry-tooltip-exiting]) {
          pointer-events: none;
          user-select: none;
        }

        :where(.cui-tooltip[data-placement="bottom-start"]) {
          position-area: block-end span-inline-end;
          margin-block-start: var(--_cui-tooltip-offset);
        }

        :where(.cui-tooltip[data-placement="bottom"]) {
          position-area: block-end;
          margin-block-start: var(--_cui-tooltip-offset);
        }

        :where(.cui-tooltip[data-placement="bottom-end"]) {
          position-area: block-end span-inline-start;
          margin-block-start: var(--_cui-tooltip-offset);
        }

        :where(.cui-tooltip[data-placement="top-start"]) {
          position-area: block-start span-inline-end;
          margin-block-end: var(--_cui-tooltip-offset);
        }

        :where(.cui-tooltip[data-placement="top"]) {
          position-area: block-start;
          margin-block-end: var(--_cui-tooltip-offset);
        }

        :where(.cui-tooltip[data-placement="top-end"]) {
          position-area: block-start span-inline-start;
          margin-block-end: var(--_cui-tooltip-offset);
        }

        @media (prefers-reduced-motion: reduce) {
          :where(.cui-tooltip) {
            --_cui-tooltip-duration: 0ms;
          }
        }

        @media (forced-colors: active) {
          :where(.cui-tooltip) {
            border-color: CanvasText;
            background: Canvas;
            color: CanvasText;
            box-shadow: none;
          }
        }

        @media print {
          :where(.cui-tooltip) {
            display: none;
          }
        }
      }
    """


__all__ = [
    "CTooltip",
    "CTooltipActivatorSlotData",
    "CTooltipDefaultSlotData",
    "CTooltipOpenChangeDetail",
    "CTooltipPlacement",
]
