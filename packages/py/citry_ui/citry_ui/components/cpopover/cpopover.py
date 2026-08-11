"""Styled non-modal Popover component family."""

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

CPopoverPlacement = Literal[
    "top-start",
    "top",
    "top-end",
    "bottom-start",
    "bottom",
    "bottom-end",
]


class CPopoverOpenChangeDetail(TypedDict):
    reason: Literal[
        "trigger",
        "action",
        "escape",
        "outside",
        "focus-outside",
        "native",
        "ancestor",
        "modal",
    ]
    controlled: bool
    forced: bool
    source: object | None


class CPopoverActivatorSlotData:
    activator_attrs: dict[str, object]


class CPopoverTitleSlotData:
    pass


class CPopoverDescriptionSlotData:
    pass


class CPopoverDefaultSlotData:
    pass


class CPopoverActionsSlotData:
    close_attrs: dict[str, object]


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
        "aria-describedby",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-modal",
        "aria-roledescription",
        "autofocus",
        "contenteditable",
        "data-citry-popover-exiting",
        "data-citry-popover-initialized",
        "data-citry-ui-part",
        "data-match-width",
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
        msg = f"CPopover {input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CPopover could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain


def _plain_html_id(value: object) -> str | None:
    plain = _plain_optional_string("id", value)
    if plain is None:
        return None
    if not plain or any(character in "\t\n\f\r " for character in plain):
        msg = "CPopover id must be non-empty and cannot contain ASCII whitespace."
        raise ValueError(msg)
    if "\0" in plain:
        msg = "CPopover id cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _plain_placement(value: object) -> str:
    plain = _plain_optional_string("placement", value)
    if plain is None or plain not in _PLACEMENTS:
        expected = ", ".join(repr(item) for item in _PLACEMENTS)
        msg = f"CPopover placement must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _copy_attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        msg = f"CPopover attrs must be a mapping or None, got {attrs!r}."
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
    reject_owned_attrs(attrs, _SURFACE_OWNED_ATTRS, "CPopover")
    for key in attrs:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CPopover attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CPopover attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in _SURFACE_OWNED_ATTRS:
            msg = f"CPopover attrs cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)


class CPopover(LibraryComponent):
    class Dependencies:
        js = (ANCHORED_LAYER_RUNTIME_DEPENDENCY,)

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        open: bool = False
        dismissible: bool = True
        placement: CPopoverPlacement = "bottom-start"
        match_width: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        activator: SlotInput[CPopoverActivatorSlotData]
        title: SlotInput[CPopoverTitleSlotData]
        default: SlotInput[CPopoverDefaultSlotData]
        description: SlotInput[CPopoverDescriptionSlotData] | None = None
        actions: SlotInput[CPopoverActionsSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_popover_snapshot", None)
        if cached is not None:
            return cached

        popover_id = _plain_html_id(kwargs.id) or f"cui-popover-{self.id}"
        validate_boolean("CPopover", "open", kwargs.open)
        validate_boolean("CPopover", "dismissible", kwargs.dismissible)
        validate_boolean("CPopover", "match_width", kwargs.match_width)
        placement = _plain_placement(kwargs.placement)
        attrs = _copy_attrs(kwargs.attrs)
        _validate_attrs(attrs)
        anchor_name = f"--_cui-popover-anchor-ref-{self.id}"
        generated_anchor_style = {"--_cui-popover-anchor": anchor_name}
        surface_style: CStyleValue = (
            generated_anchor_style if kwargs.style is None else (kwargs.style, generated_anchor_style)
        )
        snapshot: dict[str, object] = {
            "popover_id": popover_id,
            "title_id": f"{popover_id}-title",
            "description_id": f"{popover_id}-description",
            "described_by": (f"{popover_id}-description" if "description" in self.raw_slots else None),
            "open": bool(kwargs.open),
            "dismissible": bool(kwargs.dismissible),
            "placement": placement,
            "match_width": bool(kwargs.match_width),
            "has_description": "description" in self.raw_slots,
            "has_actions": "actions" in self.raw_slots,
            "activator_attrs": {
                "aria-haspopup": "dialog",
                "aria-controls": popover_id,
                "aria-expanded": "true" if kwargs.open else "false",
                "data-citry-popover-trigger": "",
                "style": {"anchor-name": anchor_name},
            },
            "close_attrs": {"data-citry-popover-close": ""},
            "attrs": merge_root_attrs(attrs, kwargs.class_, surface_style),
        }
        self._cui_popover_snapshot = snapshot
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
            "open": snapshot["open"],
            "dismissible": snapshot["dismissible"],
            "placement": snapshot["placement"],
            "matchWidth": snapshot["match_width"],
        }

    template = """
      <div
        class="cui-popover-host"
        data-citry-popover-host
      >
        <c-slot
          name="activator"
          c-activator_attrs="activator_attrs"
          required
        />
        <div
          class="cui-popover"
          c-id="popover_id"
          c-aria-labelledby="title_id"
          c-aria-describedby="described_by"
          c-inert="not open"
          c-data-open="open"
          c-data-placement="placement"
          c-data-match-width="match_width"
          c-bind="attrs"
          popover="manual"
          role="dialog"
          tabindex="-1"
          data-citry-ui-part="popover"
        >
          <header
            class="cui-popover__header"
            data-citry-ui-part="header"
          >
            <h2
              class="cui-popover__title"
              c-id="title_id"
              data-citry-ui-part="title"
            >
              <c-slot name="title" required />
            </h2>
            <c-if cond="has_description">
              <div
                class="cui-popover__description"
                c-id="description_id"
                data-citry-ui-part="description"
              >
                <c-slot name="description" />
              </div>
            </c-if>
          </header>
          <div
            class="cui-popover__body"
            data-citry-ui-part="body"
          >
            <c-slot required />
          </div>
          <c-if cond="has_actions">
            <footer
              class="cui-popover__actions"
              data-citry-ui-part="actions"
            >
              <c-slot
                name="actions"
                c-close_attrs="close_attrs"
              />
            </footer>
          </c-if>
        </div>
      </div>
    """

    js = (
        ANCHORED_LAYER_RUNTIME_JS
        + r"""
      const handoffKey = Symbol.for("citry-ui:popover-handoff");

      $component({
        props: {
          open: {},
          dismissible: {},
          placement: {},
          matchWidth: {},
          onOpenChange: {},
        },
        init: ({ els, data, props, effect }) => {
          const host = els[0];
          const nearestHost = (element) => (
            element?.closest?.("[data-citry-popover-host]") ?? null
          );
          const surface = [...host.querySelectorAll('[data-citry-ui-part="popover"]')]
            .find((candidate) => nearestHost(candidate) === host);
          const triggers = [...host.querySelectorAll("[data-citry-popover-trigger]")]
            .filter((candidate) => nearestHost(candidate) === host);
          if (!surface || triggers.length !== 1 || !(triggers[0] instanceof HTMLButtonElement)) {
            throw new Error(
              "[citry-ui] CPopover activator must spread activator_attrs onto exactly one native Button.",
            );
          }
          const trigger = triggers[0];
          const layerCoordinator = anchoredLayerRuntime.coordinatorFor(surface);
          // Both declarations exist in server HTML for the no-JavaScript
          // fallback. Reassert them after all authored Button/surface styles
          // have initialized so the component keeps its private anchor owner.
          const anchorName = getComputedStyle(surface)
            .getPropertyValue("--_cui-popover-anchor")
            .trim();
          if (!anchorName.startsWith("--")) {
            throw new Error("[citry-ui] CPopover could not resolve its CSS anchor name.");
          }
          trigger.style.setProperty("anchor-name", anchorName);
          surface.style.setProperty("position-anchor", anchorName);
          const allowedPlacements = [
            "top-start",
            "top",
            "top-end",
            "bottom-start",
            "bottom",
            "bottom-end",
          ];
          const invalidEpisodes = new Set();
          const scheduledTasks = new Set();
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
          let configuration = {
            dismissible: data.dismissible,
            placement: data.placement,
            matchWidth: data.matchWidth,
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
              `[citry-ui] CPopover ${name} received invalid client value `
                + `${describeValue(value)}; using the current or server-rendered fallback.`,
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
          const scheduleTask = (callback) => {
            const task = setTimeout(() => {
              scheduledTasks.delete(task);
              if (active) {
                callback();
              }
            }, 0);
            scheduledTasks.add(task);
          };
          const cancelAnimation = () => {
            generation += 1;
            animation?.cancel();
            animation = null;
          };
          const duration = () => {
            const raw = getComputedStyle(surface)
              .getPropertyValue("--_cui-popover-duration")
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
            .getPropertyValue("--_cui-popover-easing")
            .trim() || "ease";
          const updateTrigger = () => {
            trigger.setAttribute("aria-expanded", logicalOpen ? "true" : "false");
          };
          const focusable = () => [...surface.querySelectorAll(
            'a[href], area[href], button:not(:disabled), input:not(:disabled):not([type="hidden"]), '
              + 'select:not(:disabled), textarea:not(:disabled), iframe, object, embed, '
              + 'audio[controls], video[controls], summary, '
              + '[contenteditable]:not([contenteditable="false"]), '
              + '[tabindex]:not([tabindex="-1"]):not([inert])',
          )].filter((element) => (
            element instanceof HTMLElement
            && element.closest("[popover]") === surface
            && !element.hidden
            && !element.closest("[inert]")
            && element.getClientRects().length > 0
            && getComputedStyle(element).visibility !== "hidden"
          ));
          const placeInitialFocus = (currentGeneration) => {
            queueMicrotask(() => {
              if (!active || !logicalOpen || currentGeneration !== generation) {
                return;
              }
              const autofocus = [...surface.querySelectorAll("[autofocus]")]
                .find((element) => element instanceof HTMLElement
                  && element.closest("[popover]") === surface);
              const target = autofocus ?? focusable()[0] ?? surface;
              target.focus({ preventScroll: true });
            });
          };
          const finishNativeClose = (currentGeneration) => {
            if (!active || logicalOpen || currentGeneration !== generation) {
              return;
            }
            if (surface.matches(":popover-open")) {
              surface.hidePopover();
            }
            surface.removeAttribute("data-citry-popover-exiting");
          };
          const animateEntry = (currentGeneration) => {
            const milliseconds = duration();
            if (milliseconds === 0) {
              return;
            }
            animation = surface.animate(
              [
                { opacity: 0, transform: "translateY(-0.25rem) scale(0.98)" },
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
                { opacity: 0, transform: "translateY(-0.25rem) scale(0.98)" },
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
          const restoreFocus = (reason) => {
            if (
              reason === "outside"
              || reason === "focus-outside"
              || reason === "ancestor"
              || reason === "modal"
              || !anchoredLayerRuntime.composedContains(
                surface,
                layerCoordinator.deepActiveElement(),
              )
              || trigger.disabled
              || !trigger.isConnected
            ) {
              return;
            }
            trigger.focus({ preventScroll: true });
          };
          const layer = {
            surface,
            trigger,
            isOpen: () => active && logicalOpen,
            requestDismiss: (reason, source) => {
              if (configuration.dismissible) {
                requestOpen(false, reason, source);
              }
            },
            forceClose: (reason, source) => forceCloseLayer(reason, source),
          };
          const applyOpen = (nextOpen, context = null) => {
            if (nextOpen === logicalOpen) {
              if (
                nextOpen
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
            if (nextOpen) {
              if (!layerCoordinator.mayOpen(layer)) {
                if (!controlled) {
                  internalOpen = false;
                }
                updateTrigger();
                return;
              }
              try {
                if (!surface.matches(":popover-open")) {
                  surface.showPopover();
                }
              } catch (error) {
                console.error("[citry-ui] CPopover could not enter the top layer:", error, surface);
                logicalOpen = false;
                internalOpen = false;
                updateTrigger();
                return;
              }
              logicalOpen = true;
              surface.inert = false;
              surface.removeAttribute("data-citry-popover-exiting");
              surface.setAttribute("data-open", "");
              if (!layerCoordinator.register(layer)) {
                logicalOpen = false;
                surface.hidePopover();
                surface.inert = true;
                surface.removeAttribute("data-open");
                updateTrigger();
                return;
              }
              updateTrigger();
              animateEntry(currentGeneration);
              placeInitialFocus(currentGeneration);
              return;
            }
            logicalOpen = false;
            surface.removeAttribute("data-open");
            surface.setAttribute("data-citry-popover-exiting", "");
            surface.inert = true;
            layerCoordinator.unregister(layer);
            updateTrigger();
            restoreFocus(context?.reason ?? null);
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
            if (nextOpen === logicalOpen) {
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
          const onHostClick = (event) => {
            const source = event.target?.closest?.(
              "[data-citry-popover-trigger], [data-citry-popover-close]",
            );
            if (!source || nearestHost(source) !== host) {
              return;
            }
            scheduleTask(() => {
              if (event.defaultPrevented) {
                return;
              }
              if (source.hasAttribute("data-citry-popover-trigger")) {
                if (source.disabled || source.matches('[aria-disabled="true"]')) {
                  return;
                }
                requestOpen(!logicalOpen, "trigger", source);
                return;
              }
              requestOpen(false, "action", source);
            });
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
              if (controlled) {
                surface.hidePopover();
                notify(true, "native", surface);
                return;
              }
              internalOpen = true;
              logicalOpen = true;
              surface.inert = false;
              surface.setAttribute("data-open", "");
              if (!layerCoordinator.register(layer)) {
                logicalOpen = false;
                internalOpen = false;
                surface.hidePopover();
                surface.inert = true;
                surface.removeAttribute("data-open");
                notify(
                  false,
                  layerCoordinator.blockedReason(layer) ?? "ancestor",
                  surface,
                  true,
                );
                return;
              }
              updateTrigger();
              notify(true, "native", surface);
              return;
            }
            if (controlled) {
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
                  "[citry-ui] CPopover could not restore controlled native visibility:",
                  error,
                  surface,
                );
              }
              notify(false, "native", surface);
              return;
            }
            logicalOpen = false;
            internalOpen = false;
            surface.inert = true;
            surface.removeAttribute("data-open");
            surface.removeAttribute("data-citry-popover-exiting");
            layerCoordinator.unregister(layer);
            updateTrigger();
            notify(false, "native", surface);
          };

          host.addEventListener("click", onHostClick, true);
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
              dismissible: resolveBoolean("dismissible"),
              placement: resolvePlacement(),
              matchWidth: resolveBoolean("matchWidth"),
            };
            onOpenChange = resolveCallback();
            surface.dataset.placement = configuration.placement;
            surface.toggleAttribute("data-match-width", configuration.matchWidth);
            if (!nextOpen) {
              layerCoordinator.clearSuppression(layer);
            }
            const context = pendingRequest?.nextOpen === nextOpen ? pendingRequest : null;
            applyOpen(nextOpen, context);
            if (context || nextOpen === logicalOpen) {
              pendingRequest = null;
            }
          });
          host.setAttribute("data-citry-popover-initialized", "");

          return () => {
            active = false;
            surface[handoffKey] = { open: logicalOpen };
            host.removeEventListener("click", onHostClick, true);
            surface.removeEventListener("toggle", onToggle);
            for (const task of scheduledTasks) {
              clearTimeout(task);
            }
            scheduledTasks.clear();
            cancelAnimation();
            layerCoordinator.unregister(layer);
            if (surface.matches(":popover-open")) {
              surface.hidePopover();
            }
            surface.inert = true;
            surface.removeAttribute("data-open");
            surface.removeAttribute("data-citry-popover-exiting");
            trigger.setAttribute("aria-expanded", "false");
            host.removeAttribute("data-citry-popover-initialized");
          };
        },
      });
    """
    )

    css = """
      @layer citry-ui.theme {
        :where(.cui-popover-host) {
          display: contents;
        }

        :where(.cui-popover) {
          --_cui-popover-background: var(--cui-popover-background, Canvas);
          --_cui-popover-foreground: var(--cui-popover-foreground, CanvasText);
          --_cui-popover-border-color: var(
            --cui-popover-border-color,
            color-mix(in srgb, CanvasText 16%, transparent)
          );
          --_cui-popover-border-width: var(--cui-popover-border-width, 1px);
          --_cui-popover-radius: var(--cui-popover-radius, 0.75rem);
          --_cui-popover-shadow: var(
            --cui-popover-shadow,
            0 1rem 3rem rgb(15 23 42 / 22%)
          );
          --_cui-popover-inline-size: var(--cui-popover-inline-size, 20rem);
          --_cui-popover-max-inline-size: var(
            --cui-popover-max-inline-size,
            calc(100dvi - 1rem)
          );
          --_cui-popover-max-block-size: var(
            --cui-popover-max-block-size,
            calc(100dvb - 1rem)
          );
          --_cui-popover-padding: var(--cui-popover-padding, 1rem);
          --_cui-popover-gap: var(--cui-popover-gap, 0.75rem);
          --_cui-popover-offset: var(--cui-popover-offset, 0.5rem);
          --_cui-popover-duration: var(--cui-popover-duration, 140ms);
          --_cui-popover-easing: var(
            --cui-popover-easing,
            cubic-bezier(0.2, 0.8, 0.2, 1)
          );
          --_cui-popover-focus-color: var(--cui-popover-focus-color, Highlight);

          box-sizing: border-box;
          position: fixed;
          position-anchor: var(--_cui-popover-anchor);
          position-try-fallbacks: flip-block, flip-inline, flip-block flip-inline;
          position-visibility: anchors-visible;
          display: grid;
          grid-template-rows: auto minmax(0, 1fr) auto;
          inline-size: min(
            var(--_cui-popover-inline-size),
            var(--_cui-popover-max-inline-size)
          );
          max-inline-size: var(--_cui-popover-max-inline-size);
          max-block-size: var(--_cui-popover-max-block-size);
          margin: 0;
          padding: 0;
          overflow: hidden;
          border: var(--_cui-popover-border-width) solid var(--_cui-popover-border-color);
          border-radius: var(--_cui-popover-radius);
          background: var(--_cui-popover-background);
          color: var(--_cui-popover-foreground);
          box-shadow: var(--_cui-popover-shadow);
          font-family: ui-sans-serif, system-ui, sans-serif;
          line-height: 1.5;
          overscroll-behavior: contain;
        }

        :where(
          .cui-popover:not(:popover-open):not([data-open]):not(
            [data-citry-popover-exiting]
          )
        ) {
          display: none;
        }

        :where(.cui-popover[data-open]:not(:popover-open)) {
          position: static;
          display: grid;
          inline-size: min(100%, var(--_cui-popover-max-inline-size));
          margin-block: 0.5rem;
        }

        :where(.cui-popover[data-citry-popover-exiting]) {
          pointer-events: none;
          user-select: none;
        }

        :where(.cui-popover[data-placement="bottom-start"]) {
          position-area: block-end span-inline-end;
          margin-block-start: var(--_cui-popover-offset);
        }

        :where(.cui-popover[data-placement="bottom"]) {
          position-area: block-end;
          margin-block-start: var(--_cui-popover-offset);
        }

        :where(.cui-popover[data-placement="bottom-end"]) {
          position-area: block-end span-inline-start;
          margin-block-start: var(--_cui-popover-offset);
        }

        :where(.cui-popover[data-placement="top-start"]) {
          position-area: block-start span-inline-end;
          margin-block-end: var(--_cui-popover-offset);
        }

        :where(.cui-popover[data-placement="top"]) {
          position-area: block-start;
          margin-block-end: var(--_cui-popover-offset);
        }

        :where(.cui-popover[data-placement="top-end"]) {
          position-area: block-start span-inline-start;
          margin-block-end: var(--_cui-popover-offset);
        }

        :where(.cui-popover[data-match-width]) {
          min-inline-size: anchor-size(width);
        }

        :where(.cui-popover__header),
        :where(.cui-popover__body),
        :where(.cui-popover__actions) {
          box-sizing: border-box;
          min-inline-size: 0;
          padding-inline: var(--_cui-popover-padding);
          overflow-wrap: anywhere;
        }

        :where(.cui-popover__header) {
          display: grid;
          gap: 0.25rem;
          padding-block-start: var(--_cui-popover-padding);
        }

        :where(.cui-popover__title) {
          margin: 0;
          font-size: 1rem;
          font-weight: 700;
          line-height: 1.3;
        }

        :where(.cui-popover__description) {
          color: color-mix(in srgb, currentColor 72%, transparent);
          font-size: 0.875rem;
        }

        :where(.cui-popover__body) {
          min-block-size: 0;
          padding-block: var(--_cui-popover-gap);
          overflow: auto;
        }

        :where(.cui-popover__body > :first-child) {
          margin-block-start: 0;
        }

        :where(.cui-popover__body > :last-child) {
          margin-block-end: 0;
        }

        :where(.cui-popover__actions) {
          display: flex;
          flex-wrap: wrap;
          justify-content: end;
          gap: 0.5rem;
          padding-block-end: var(--_cui-popover-padding);
        }

        :where(.cui-popover__actions > *) {
          min-inline-size: 0;
          max-inline-size: 100%;
        }

        :where(.cui-popover:focus-visible) {
          outline: 0.1875rem solid var(--_cui-popover-focus-color);
          outline-offset: 0.125rem;
        }

        @media (prefers-reduced-motion: reduce) {
          :where(.cui-popover) {
            --_cui-popover-duration: 0ms;
          }
        }

        @media (forced-colors: active) {
          :where(.cui-popover) {
            border-color: CanvasText;
            background: Canvas;
            color: CanvasText;
            box-shadow: none;
          }
        }

        @media print {
          :where(.cui-popover) {
            position: static;
            display: none;
            inline-size: auto;
            max-inline-size: none;
            max-block-size: none;
            margin-block: 1rem;
            border-color: currentColor;
            background: transparent;
            color: #000000;
            box-shadow: none;
          }

          :where(.cui-popover[data-open]) {
            display: grid;
          }
        }
      }
    """


__all__ = [
    "CPopover",
    "CPopoverActionsSlotData",
    "CPopoverActivatorSlotData",
    "CPopoverDefaultSlotData",
    "CPopoverDescriptionSlotData",
    "CPopoverOpenChangeDetail",
    "CPopoverPlacement",
    "CPopoverTitleSlotData",
]
