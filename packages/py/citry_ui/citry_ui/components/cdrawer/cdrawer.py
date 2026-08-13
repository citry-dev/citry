"""Styled native modal Drawer and Sheet component family."""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput
from citry_ui.components._attrs import (
    CClassValue,
    CStyleValue,
    merge_root_attrs,
    reject_html_attr_bindings,
)
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
)

CDrawerInitialFocus = Literal["auto", "title"]
CDrawerPlacement = Literal["inline-start", "inline-end", "block-start", "block-end"]
CDrawerScroll = Literal["body", "drawer"]
CDrawerSize = Literal["sm", "md", "lg", "full"]


class CDrawerActivatorSlotData:
    activator_attrs: dict[str, object]


class CDrawerTitleSlotData:
    pass


class CDrawerDescriptionSlotData:
    pass


class CDrawerDefaultSlotData:
    pass


class CDrawerActionsSlotData:
    close_attrs: dict[str, object]


class CDrawerCloseSlotData:
    pass


class CDrawer(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        open: bool = False
        dismissible: bool = True
        close_on_escape: bool = True
        close_on_outside: bool = True
        initial_focus: CDrawerInitialFocus = "auto"
        placement: CDrawerPlacement = "inline-end"
        size: CDrawerSize = "md"
        scroll: CDrawerScroll = "body"
        close_label: str = "Close"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        title: SlotInput[CDrawerTitleSlotData]
        default: SlotInput[CDrawerDefaultSlotData]
        activator: SlotInput[CDrawerActivatorSlotData] | None = None
        description: SlotInput[CDrawerDescriptionSlotData] | None = None
        actions: SlotInput[CDrawerActionsSlotData] | None = None
        close: SlotInput[CDrawerCloseSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        validate_html_id("CDrawer", kwargs.id)
        if kwargs.id is not None and "\0" in kwargs.id:
            msg = "CDrawer id cannot contain U+0000."
            raise ValueError(msg)
        validate_boolean("CDrawer", "open", kwargs.open)
        validate_boolean("CDrawer", "dismissible", kwargs.dismissible)
        validate_boolean("CDrawer", "close_on_escape", kwargs.close_on_escape)
        validate_boolean("CDrawer", "close_on_outside", kwargs.close_on_outside)
        validate_choice("CDrawer", "initial_focus", kwargs.initial_focus, ("auto", "title"))
        validate_choice(
            "CDrawer",
            "placement",
            kwargs.placement,
            ("inline-start", "inline-end", "block-start", "block-end"),
        )
        validate_choice("CDrawer", "size", kwargs.size, ("sm", "md", "lg", "full"))
        validate_choice("CDrawer", "scroll", kwargs.scroll, ("body", "drawer"))
        close_label = kwargs.close_label if "close_label" in self.raw_kwargs else self.i18n.tr("citry-ui-drawer-close")
        validate_non_empty_string("CDrawer", "close_label", close_label)
        reject_owned_attrs(
            kwargs.attrs,
            {
                "aria-describedby",
                "aria-hidden",
                "aria-label",
                "aria-labelledby",
                "aria-modal",
                "closedby",
                "data-citry-drawer-built-in-close",
                "data-citry-drawer-close",
                "data-citry-drawer-host",
                "data-citry-drawer-initialized",
                "data-citry-drawer-trigger",
                "data-citry-ui-part",
                "data-open",
                "data-placement",
                "data-scroll",
                "data-size",
                "hidden",
                "id",
                "inert",
                "open",
                "popover",
                "role",
                "tabindex",
                "x-for",
                "x-html",
                "x-if",
                "x-ignore",
                "x-model",
                "x-modelable",
                "x-teleport",
                "x-text",
            },
            "CDrawer",
        )
        reject_html_attr_bindings(
            kwargs.attrs,
            {
                "aria-describedby",
                "aria-hidden",
                "aria-label",
                "aria-labelledby",
                "aria-modal",
                "closedby",
                "data-citry-ui-part",
                "data-open",
                "data-placement",
                "data-scroll",
                "data-size",
                "hidden",
                "id",
                "inert",
                "open",
                "popover",
                "role",
                "tabindex",
            },
            "CDrawer",
        )

        drawer_id = kwargs.id or f"cui-drawer-{self.id}"
        title_id = f"{drawer_id}-title"
        description_id = f"{drawer_id}-description"
        has_description = "description" in self.raw_slots
        return {
            "drawer_id": drawer_id,
            "title_id": title_id,
            "description_id": description_id,
            "described_by": description_id if has_description else None,
            "open": kwargs.open,
            "dismissible": kwargs.dismissible,
            "initial_focus": kwargs.initial_focus,
            "title_tabindex": -1 if kwargs.initial_focus == "title" else None,
            "placement": kwargs.placement,
            "size": kwargs.size,
            "scroll": kwargs.scroll,
            "close_label": close_label,
            "catalog_close_label": uses_catalog_default(self, "close_label"),
            "has_activator": "activator" in self.raw_slots,
            "has_description": has_description,
            "has_actions": "actions" in self.raw_slots,
            "has_close": "close" in self.raw_slots,
            "activator_attrs": {
                "aria-haspopup": "dialog",
                "aria-controls": drawer_id,
                "aria-expanded": "true" if kwargs.open else "false",
                "data-citry-drawer-trigger": "",
            },
            "close_attrs": {"data-citry-drawer-close": ""},
            "attrs": merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "open": kwargs.open,
            "dismissible": kwargs.dismissible,
            "closeOnEscape": kwargs.close_on_escape,
            "closeOnOutside": kwargs.close_on_outside,
            "initialFocus": kwargs.initial_focus,
            "placement": kwargs.placement,
            "size": kwargs.size,
            "scroll": kwargs.scroll,
            "hasActivator": "activator" in self.raw_slots,
        }

    template = """
      <div class="cui-drawer-host" data-citry-drawer-host>
        <c-if cond="has_activator">
          <c-slot name="activator" c-activator_attrs="activator_attrs" />
        </c-if>
        <dialog
          class="cui-drawer"
          c-id="drawer_id"
          c-open="open"
          c-aria-labelledby="title_id"
          c-aria-describedby="described_by"
          aria-modal="true"
          c-data-open="open"
          c-data-placement="placement"
          c-data-size="size"
          c-data-scroll="scroll"
          c-bind="attrs"
          data-citry-ui-part="drawer"
        >
          <div class="cui-drawer__surface" data-citry-ui-part="surface">
            <header class="cui-drawer__header" data-citry-ui-part="header">
              <h2
                class="cui-drawer__title"
                c-id="title_id"
                c-tabindex="title_tabindex"
                data-citry-ui-part="title"
              >
                <c-slot name="title" required />
              </h2>
              <button
                class="cui-drawer__close"
                type="button"
                c-aria-label="tr('citry-ui-drawer-close') if catalog_close_label else close_label"
                c-$c-tr:citry-ui-drawer-close[aria-label]="True if catalog_close_label else None"
                c-hidden="not dismissible"
                data-citry-drawer-close
                data-citry-drawer-built-in-close
                data-citry-ui-part="close"
              >
                <c-if cond="has_close"><c-slot name="close" /></c-if>
                <c-else><span aria-hidden="true">&times;</span></c-else>
              </button>
            </header>
            <c-if cond="has_description">
              <div
                class="cui-drawer__description"
                c-id="description_id"
                data-citry-ui-part="description"
              >
                <c-slot name="description" />
              </div>
            </c-if>
            <div class="cui-drawer__body" data-citry-ui-part="body">
              <c-slot required />
            </div>
            <c-if cond="has_actions">
              <footer class="cui-drawer__actions" data-citry-ui-part="actions">
                <c-slot name="actions" c-close_attrs="close_attrs" />
              </footer>
            </c-if>
          </div>
        </dialog>
      </div>
    """

    js = r"""
      const modalRuntimeKey = Symbol.for("citry-ui:dialog-runtime");
      const modalRuntime = globalThis[modalRuntimeKey] ?? {
        dialogs: [], overflow: "", paddingInlineEnd: "",
      };
      globalThis[modalRuntimeKey] = modalRuntime;
      modalRuntime.drawerControllers ??= new WeakMap();

      $component({
        props: {
          open: {}, dismissible: {}, closeOnEscape: {}, closeOnOutside: {},
          initialFocus: {}, placement: {}, size: {}, scroll: {}, onOpenChange: {},
        },
        init: ({ els, data, props, effect }) => {
          const host = els[0];
          const nearestHost = (element) => element?.closest?.("[data-citry-drawer-host]") ?? null;
          const drawer = [...host.querySelectorAll('[data-citry-ui-part="drawer"]')]
            .find((candidate) => nearestHost(candidate) === host);
          const surface = drawer?.querySelector(':scope > [data-citry-ui-part="surface"]');
          const title = surface?.querySelector('[data-citry-ui-part="title"]');
          const closeButton = surface?.querySelector('[data-citry-drawer-built-in-close]');
          if (!(drawer instanceof HTMLDialogElement) || !surface || !title || !closeButton) {
            console.error("[citry-ui] CDrawer could not resolve its owned anatomy.", host);
            return;
          }

          const allowed = {
            initialFocus: ["auto", "title"],
            placement: ["inline-start", "inline-end", "block-start", "block-end"],
            size: ["sm", "md", "lg", "full"],
            scroll: ["body", "drawer"],
          };
          const invalidEpisodes = new Set();
          let internalOpen = data.open;
          let controlled = false;
          let appliedOpen = false;
          let suppressedControlledOpen = false;
          let pendingReturnValue = "";
          let pendingOpenSource = null;
          let expectedNativeClose = false;
          let pendingNativeUserClose = false;
          let pointerStartedOutside = false;
          let previousFocus = null;
          let onOpenChange = null;
          let structureValid = false;
          let structureEpisode = false;
          let disposed = false;
          let generation = 0;
          let eligibilitySource = null;
          let configuration = {
            dismissible: data.dismissible,
            closeOnEscape: data.closeOnEscape,
            closeOnOutside: data.closeOnOutside,
            initialFocus: data.initialFocus,
            placement: data.placement,
            size: data.size,
            scroll: data.scroll,
          };

          const deepActiveElement = () => {
            let active = drawer.ownerDocument.activeElement;
            while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
            return active;
          };
          const composedParent = (node) => {
            if (node?.parentNode) return node.parentNode;
            const root = node?.getRootNode?.();
            return root instanceof ShadowRoot ? root.host : null;
          };
          const composedContains = (ancestor, node) => {
            for (let current = node; current; current = composedParent(current)) {
              if (current === ancestor) return true;
            }
            return false;
          };
          const openRoots = () => {
            const roots = [drawer.ownerDocument];
            for (let index = 0; index < roots.length; index += 1) {
              const root = roots[index];
              for (const element of root.querySelectorAll("*")) {
                if (element.shadowRoot) roots.push(element.shadowRoot);
              }
            }
            return roots;
          };
          const mayOpen = () => {
            if (!host.isConnected || !drawer.isConnected || !structureValid) return false;
            if (drawer.hidden || drawer.inert) return false;
            if (drawer.open) {
              const drawerStyle = getComputedStyle(drawer);
              if (drawerStyle.display === "none" || drawerStyle.visibility === "hidden") return false;
            }
            for (let node = host; node; node = composedParent(node)) {
              if (node instanceof HTMLElement) {
                const style = getComputedStyle(node);
                if (node.hidden || node.inert || style.display === "none" || style.visibility === "hidden") {
                  return false;
                }
                if (node instanceof HTMLDialogElement && node !== drawer && !node.open) return false;
                if (node.hasAttribute("popover") && !node.matches(":popover-open")) return false;
              }
            }
            const modals = openRoots().flatMap((root) => [...root.querySelectorAll("dialog:modal")]);
            return modals.every((modal) => modal === drawer || composedContains(modal, host));
          };
          const isFocusable = (element) => element instanceof HTMLElement
            && element.isConnected
            && !element.hidden
            && !element.matches(":disabled,[inert]")
            && !element.closest("[inert]")
            && element.getClientRects().length > 0
            && getComputedStyle(element).visibility !== "hidden";
          const focusableElements = () => [...drawer.querySelectorAll(
            'a[href],area[href],button:not(:disabled),input:not(:disabled):not([type="hidden"]),'
              + 'select:not(:disabled),textarea:not(:disabled),iframe,object,embed,audio[controls],'
              + 'video[controls],summary,[contenteditable]:not([contenteditable="false"]),'
              + '[tabindex]:not([tabindex="-1"]):not([inert])',
          )].filter((element) => isFocusable(element) && element.closest("dialog") === drawer)
            .filter((element, _index, elements) => {
              if (!(element instanceof HTMLInputElement) || element.type !== "radio" || !element.name) {
                return true;
              }
              const group = elements.filter((candidate) => candidate instanceof HTMLInputElement
                && candidate.type === "radio" && candidate.name === element.name
                && candidate.form === element.form);
              const checked = group.find((candidate) => candidate.checked);
              return checked ? element === checked : element === group[0];
            })
            .map((element, index) => ({ element, index, tabIndex: element.tabIndex }))
            .filter(({ tabIndex }) => tabIndex >= 0)
            .sort((left, right) => {
              if (left.tabIndex > 0 && right.tabIndex === 0) return -1;
              if (left.tabIndex === 0 && right.tabIndex > 0) return 1;
              if (left.tabIndex > 0 && right.tabIndex > 0 && left.tabIndex !== right.tabIndex) {
                return left.tabIndex - right.tabIndex;
              }
              return left.index - right.index;
            }).map(({ element }) => element);
          const reportInvalid = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            let shown;
            try { shown = JSON.stringify(value) ?? String(value); } catch { shown = String(value); }
            console.error(
              `[citry-ui] CDrawer ${name} received invalid client value ${shown}; using its fallback.`,
              drawer,
            );
          };
          const resolveBoolean = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (typeof value === "boolean") { invalidEpisodes.delete(name); return value; }
            reportInvalid(name, value);
            return data[name];
          };
          const resolveEnum = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (allowed[name].includes(value)) { invalidEpisodes.delete(name); return value; }
            reportInvalid(name, value);
            return data[name];
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
          const ownedActivators = () => [...host.querySelectorAll("[data-citry-drawer-trigger]")]
            .filter((element) => nearestHost(element) === host && !drawer.contains(element));
          const updateActivators = (open) => {
            for (const activator of ownedActivators()) {
              activator.setAttribute("aria-expanded", open ? "true" : "false");
            }
          };
          const interactiveSelector = 'button,a[href],input,select,textarea,[tabindex],'
            + '[contenteditable]:not([contenteditable="false"])';
          const hasInteractiveDescendant = (element) => Boolean(element.querySelector(interactiveSelector));
          const validateStructure = () => {
            const activators = ownedActivators();
            const outsideInteractive = [...host.querySelectorAll(interactiveSelector)]
              .filter((element) => !drawer.contains(element));
            const activatorValid = !data.hasActivator || (
              activators.length === 1
              && activators[0] instanceof HTMLButtonElement
              && activators[0].type === "button"
              && outsideInteractive.length === 1
              && outsideInteractive[0] === activators[0]
            );
            const contentValid = !hasInteractiveDescendant(title)
              && ![...surface.querySelectorAll('[data-citry-ui-part="description"]')]
                .some(hasInteractiveDescendant)
              && ![...closeButton.children].some((child) => child.matches?.(interactiveSelector)
                || child.querySelector?.(interactiveSelector));
            const valid = activatorValid && contentValid;
            if (!valid && !structureEpisode) {
              structureEpisode = true;
              console.error("[citry-ui] CDrawer settled anatomy is invalid; failing closed.", host);
            } else if (valid) {
              structureEpisode = false;
            }
            structureValid = valid;
            return valid;
          };
          const lockScroll = () => {
            if (modalRuntime.dialogs.includes(drawer)) return;
            if (modalRuntime.dialogs.length === 0) {
              const root = drawer.ownerDocument.documentElement;
              modalRuntime.overflow = root.style.overflow;
              modalRuntime.paddingInlineEnd = root.style.paddingInlineEnd;
              const view = drawer.ownerDocument.defaultView;
              const scrollbarWidth = Math.max(0, view.innerWidth - root.clientWidth);
              const currentPadding = Number.parseFloat(view.getComputedStyle(root).paddingInlineEnd) || 0;
              root.style.overflow = "hidden";
              if (scrollbarWidth > 0) root.style.paddingInlineEnd = `${currentPadding + scrollbarWidth}px`;
            }
            modalRuntime.dialogs.push(drawer);
          };
          const unlockScroll = () => {
            const index = modalRuntime.dialogs.indexOf(drawer);
            if (index === -1) return;
            modalRuntime.dialogs.splice(index, 1);
            if (modalRuntime.dialogs.length === 0) {
              const root = drawer.ownerDocument.documentElement;
              root.style.overflow = modalRuntime.overflow;
              root.style.paddingInlineEnd = modalRuntime.paddingInlineEnd;
            }
          };
          const closeDescendants = () => {
            for (const candidate of [...modalRuntime.dialogs].reverse()) {
              if (candidate === drawer || !drawer.contains(candidate) || !candidate.open) continue;
              const controller = modalRuntime.drawerControllers.get(candidate);
              if (controller) controller.forceClose("ancestor", drawer);
              else candidate.close();
            }
          };
          const stopEligibilityWatch = () => eligibilityObserver.disconnect();
          const forceClose = (reason, source) => {
            const wasOpen = appliedOpen || drawer.open;
            suppressedControlledOpen = controlled && props.open === true;
            internalOpen = false;
            normalizeClosed();
            if (wasOpen) notify(false, reason, source, "", true);
            restoreFocus();
          };
          modalRuntime.drawerControllers.set(drawer, { forceClose });
          const reconcileEligibility = (records) => {
            if (!appliedOpen) return;
            if (!drawer.open) { onNativeClose(); return; }
            if (mayOpen()) return;
            eligibilitySource = records.find((record) => record.target instanceof Element)?.target ?? host;
            forceClose("ancestor", eligibilitySource);
          };
          const eligibilityObserver = new MutationObserver(reconcileEligibility);
          const startEligibilityWatch = () => {
            eligibilityObserver.disconnect();
            const observed = new Set();
            for (let node = host; node; node = composedParent(node)) {
              if (node instanceof Element && !observed.has(node)) {
                observed.add(node);
                eligibilityObserver.observe(node, {
                  attributes: true,
                  attributeFilter: ["class", "hidden", "inert", "open", "style"],
                });
              }
              if (node?.parentNode && !observed.has(node.parentNode)) {
                observed.add(node.parentNode);
                eligibilityObserver.observe(node.parentNode, { childList: true });
              }
            }
            eligibilityObserver.observe(drawer, {
              attributes: true,
              attributeFilter: ["class", "hidden", "inert", "open", "style"],
            });
          };
          const normalizeClosed = () => {
            stopEligibilityWatch();
            closeDescendants();
            expectedNativeClose = drawer.open;
            if (drawer.open) drawer.close();
            drawer.removeAttribute("data-open");
            appliedOpen = false;
            updateActivators(false);
            unlockScroll();
          };
          const restoreFocus = (immediate = false) => {
            const token = generation;
            const restore = () => {
              if ((!immediate && disposed) || token !== generation) return;
              const active = deepActiveElement();
              const browserNeedsTarget = active === drawer.ownerDocument.body
                || active === drawer
                || composedContains(drawer, active);
              if (
                browserNeedsTarget
                && previousFocus?.isConnected
                && active !== previousFocus
                && isFocusable(previousFocus)
              ) {
                previousFocus.focus({ preventScroll: true });
              }
            };
            if (immediate) restore();
            else queueMicrotask(restore);
          };
          const applyOpen = (nextOpen, source = null, returnValue = "") => {
            if (!nextOpen) closeDescendants();
            if (nextOpen === appliedOpen && drawer.open === nextOpen) return;
            generation += 1;
            if (nextOpen) {
              if (!mayOpen()) {
                if (controlled) suppressedControlledOpen = props.open === true;
                else internalOpen = false;
                normalizeClosed();
                return;
              }
              previousFocus = source instanceof HTMLElement ? source : deepActiveElement();
              drawer.returnValue = "";
              if (drawer.open) drawer.removeAttribute("open");
              try { drawer.showModal(); } catch (error) {
                console.error("[citry-ui] CDrawer could not enter modal state:", error, drawer);
                normalizeClosed();
                return;
              }
              appliedOpen = true;
              drawer.setAttribute("data-open", "");
              updateActivators(true);
              lockScroll();
              startEligibilityWatch();
              const token = generation;
              queueMicrotask(() => {
                if (
                  !disposed && token === generation
                  && configuration.initialFocus === "title" && isFocusable(title)
                ) {
                  title.focus({ preventScroll: true });
                }
              });
              return;
            }
            expectedNativeClose = drawer.open;
            stopEligibilityWatch();
            if (drawer.open) drawer.close(returnValue);
            drawer.removeAttribute("data-open");
            appliedOpen = false;
            updateActivators(false);
            unlockScroll();
            restoreFocus();
          };
          const notify = (nextOpen, reason, source, returnValue = "", forced = false) => onOpenChange?.(nextOpen, {
            reason, controlled, forced, source, returnValue,
          });
          const requestOpen = (nextOpen, reason, source, returnValue = "") => {
            if (nextOpen === appliedOpen) return;
            if (controlled) {
              pendingReturnValue = nextOpen ? "" : returnValue;
              if (nextOpen && source instanceof HTMLElement) pendingOpenSource = source;
              notify(nextOpen, reason, source, returnValue);
              return;
            }
            internalOpen = nextOpen;
            applyOpen(nextOpen, source, returnValue);
            if (appliedOpen === nextOpen) notify(nextOpen, reason, source, returnValue);
          };
          const eventIsOutside = (event) => {
            if (event.target !== drawer) return false;
            const rect = surface.getBoundingClientRect();
            return event.clientX < rect.left || event.clientX > rect.right
              || event.clientY < rect.top || event.clientY > rect.bottom;
          };
          const onHostClick = (event) => {
            const trigger = event.target.closest?.("[data-citry-drawer-trigger]");
            if (trigger && nearestHost(trigger) === host) { requestOpen(true, "trigger", trigger); return; }
            const close = event.target.closest?.("[data-citry-drawer-close]");
            if (!close || nearestHost(close) !== host || !drawer.contains(close)) return;
            const builtIn = close.hasAttribute("data-citry-drawer-built-in-close");
            if (builtIn && !configuration.dismissible) return;
            requestOpen(false, builtIn ? "close-button" : "action", close,
              close instanceof HTMLButtonElement ? close.value : "");
          };
          const onCancel = (event) => {
            event.preventDefault();
            if (configuration.dismissible && configuration.closeOnEscape) requestOpen(false, "escape", drawer);
          };
          const onKeyDown = (event) => {
            if (event.key !== "Tab" || event.target.closest?.("dialog") !== drawer) return;
            const focusable = focusableElements();
            if (focusable.length === 0) {
              event.preventDefault();
              (configuration.initialFocus === "title" ? title : drawer).focus({ preventScroll: true });
              return;
            }
            const active = deepActiveElement();
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && (active === first || active === drawer || active === title)) {
              event.preventDefault(); last.focus({ preventScroll: true });
            } else if (!event.shiftKey && active === last) {
              event.preventDefault(); first.focus({ preventScroll: true });
            }
          };
          const rememberNativeDialogSubmission = (target) => {
            if (controlled || target.closest?.("[data-citry-drawer-close]")) return;
            const submitter = target.closest?.("button,input");
            if (!(submitter instanceof HTMLButtonElement || submitter instanceof HTMLInputElement)
              || submitter.form?.closest("dialog") !== drawer) return;
            const isSubmit = submitter instanceof HTMLButtonElement
              ? submitter.type === "submit"
              : submitter.type === "submit" || submitter.type === "image";
            const method = submitter.hasAttribute("formmethod")
              ? submitter.getAttribute("formmethod")
              : submitter.form.getAttribute("method") ?? "get";
            if (isSubmit && method.toLowerCase() === "dialog") pendingNativeUserClose = true;
          };
          const onPointerDown = (event) => {
            pointerStartedOutside = eventIsOutside(event);
            rememberNativeDialogSubmission(event.target);
          };
          const onPointerCancel = () => { pointerStartedOutside = false; };
          const onDrawerClick = (event) => {
            rememberNativeDialogSubmission(event.target);
            const close = pointerStartedOutside && eventIsOutside(event);
            pointerStartedOutside = false;
            if (close && configuration.dismissible && configuration.closeOnOutside) {
              requestOpen(false, "outside", drawer);
            }
          };
          const onSubmit = (event) => {
            const form = event.target;
            if (event.defaultPrevented || !(form instanceof HTMLFormElement)
              || form.closest("dialog") !== drawer) return;
            const submitter = event.submitter;
            const overridden = (submitter instanceof HTMLButtonElement || submitter instanceof HTMLInputElement)
              && submitter.hasAttribute("formmethod");
            if ((overridden ? submitter.formMethod : form.method).toLowerCase() !== "dialog") return;
            if (!controlled) {
              pendingNativeUserClose = true;
              return;
            }
            event.preventDefault();
            requestOpen(false, "native", submitter ?? form,
              submitter instanceof HTMLButtonElement || submitter instanceof HTMLInputElement
                ? submitter.value : "");
          };
          const onNativeClose = () => {
            if (expectedNativeClose) { expectedNativeClose = false; return; }
            if (!appliedOpen) return;
            closeDescendants();
            suppressedControlledOpen = controlled && props.open === true;
            appliedOpen = false;
            internalOpen = false;
            drawer.removeAttribute("data-open");
            updateActivators(false);
            unlockScroll();
            stopEligibilityWatch();
            let closedAncestor = null;
            for (let node = composedParent(host); node; node = composedParent(node)) {
              if (node instanceof HTMLDialogElement && !node.open) { closedAncestor = node; break; }
            }
            const forced = closedAncestor !== null || !pendingNativeUserClose;
            pendingNativeUserClose = false;
            notify(false, closedAncestor ? "ancestor" : "native", closedAncestor ?? drawer,
              drawer.returnValue, forced);
            restoreFocus();
          };
          const reconcileStructure = () => {
            if (validateStructure()) {
              host.setAttribute("data-citry-drawer-initialized", "");
            } else {
              host.removeAttribute("data-citry-drawer-initialized");
              if (appliedOpen || drawer.open) {
                forceClose("ancestor", host);
              }
            }
          };

          host.addEventListener("click", onHostClick);
          drawer.addEventListener("cancel", onCancel);
          drawer.addEventListener("keydown", onKeyDown);
          drawer.addEventListener("pointerdown", onPointerDown, true);
          drawer.addEventListener("pointercancel", onPointerCancel);
          drawer.addEventListener("click", onDrawerClick);
          drawer.addEventListener("submit", onSubmit);
          drawer.addEventListener("close", onNativeClose);
          const structureObserver = new MutationObserver(reconcileStructure);
          structureObserver.observe(host, {
            subtree: true, childList: true, attributes: true,
            attributeFilter: ["contenteditable", "href", "role", "tabindex", "type"],
          });
          validateStructure();

          effect(() => {
            const suppliedOpen = props.open;
            let nextOpen = internalOpen;
            if (suppliedOpen === undefined || suppliedOpen === null) {
              suppressedControlledOpen = false;
              pendingReturnValue = "";
              if (controlled) internalOpen = appliedOpen;
              controlled = false;
              nextOpen = internalOpen;
              invalidEpisodes.delete("open");
            } else if (typeof suppliedOpen === "boolean") {
              controlled = true;
              if (!suppliedOpen) suppressedControlledOpen = false;
              nextOpen = suppressedControlledOpen ? false : suppliedOpen;
              invalidEpisodes.delete("open");
            } else {
              suppressedControlledOpen = false;
              pendingReturnValue = "";
              reportInvalid("open", suppliedOpen);
              if (controlled) internalOpen = appliedOpen;
              controlled = false;
              nextOpen = internalOpen;
            }
            configuration = {
              dismissible: resolveBoolean("dismissible"),
              closeOnEscape: resolveBoolean("closeOnEscape"),
              closeOnOutside: resolveBoolean("closeOnOutside"),
              initialFocus: resolveEnum("initialFocus"),
              placement: resolveEnum("placement"),
              size: resolveEnum("size"),
              scroll: resolveEnum("scroll"),
            };
            onOpenChange = resolveCallback();
            closeButton.hidden = !configuration.dismissible;
            if (configuration.initialFocus === "title") title.setAttribute("tabindex", "-1");
            else title.removeAttribute("tabindex");
            drawer.dataset.placement = configuration.placement;
            drawer.dataset.size = configuration.size;
            drawer.dataset.scroll = configuration.scroll;
            applyOpen(nextOpen, nextOpen ? pendingOpenSource : null, nextOpen ? "" : pendingReturnValue);
            if (appliedOpen === nextOpen) {
              pendingReturnValue = "";
              if (nextOpen) pendingOpenSource = null;
            }
          });
          if (structureValid) host.setAttribute("data-citry-drawer-initialized", "");

          return () => {
            generation += 1;
            structureObserver.disconnect();
            eligibilityObserver.disconnect();
            host.removeEventListener("click", onHostClick);
            drawer.removeEventListener("cancel", onCancel);
            drawer.removeEventListener("keydown", onKeyDown);
            drawer.removeEventListener("pointerdown", onPointerDown, true);
            drawer.removeEventListener("pointercancel", onPointerCancel);
            drawer.removeEventListener("click", onDrawerClick);
            drawer.removeEventListener("submit", onSubmit);
            drawer.removeEventListener("close", onNativeClose);
            modalRuntime.drawerControllers.delete(drawer);
            closeDescendants();
            expectedNativeClose = drawer.open;
            if (drawer.open) drawer.close();
            appliedOpen = false;
            updateActivators(false);
            unlockScroll();
            restoreFocus(true);
            disposed = true;
            host.removeAttribute("data-citry-drawer-initialized");
          };
        },
      });
    """

    css = r"""
      @layer citry-ui.theme {
        :where(.cui-drawer-host) {
          display: contents;
          color: CanvasText;
          font-family: ui-sans-serif, system-ui, sans-serif;
        }

        :where(.cui-drawer) {
          --_cui-drawer-backdrop: var(--cui-drawer-backdrop, rgb(15 23 42 / 58%));
          --_cui-drawer-background: var(--cui-drawer-background, Canvas);
          --_cui-drawer-foreground: var(--cui-drawer-foreground, CanvasText);
          --_cui-drawer-border-color: var(
            --cui-drawer-border-color,
            color-mix(in srgb, CanvasText 16%, transparent)
          );
          --_cui-drawer-shadow: var(--cui-drawer-shadow, 0 1.5rem 4rem rgb(15 23 42 / 28%));
          --_cui-drawer-extent: var(--cui-drawer-extent, 28rem);
          --_cui-drawer-padding: var(--cui-drawer-padding, 1.25rem);
          --_cui-drawer-gap: var(--cui-drawer-gap, 1rem);
          --_cui-drawer-radius: var(--cui-drawer-radius, 0.875rem);
          --_cui-drawer-close-size: var(--cui-drawer-close-size, 2.5rem);
          --_cui-drawer-close-radius: var(--cui-drawer-close-radius, 0.5rem);

          position: fixed;
          box-sizing: border-box;
          max-inline-size: none;
          max-block-size: none;
          margin: 0;
          padding: 0;
          overflow: hidden;
          border: 0;
          background: var(--_cui-drawer-background);
          color: var(--_cui-drawer-foreground);
          box-shadow: var(--_cui-drawer-shadow);
        }

        :where(.cui-drawer::backdrop) { background: var(--_cui-drawer-backdrop); }
        :where(.cui-drawer[data-size="sm"]) { --_cui-drawer-extent: var(--cui-drawer-extent, 20rem); }
        :where(.cui-drawer[data-size="lg"]) { --_cui-drawer-extent: var(--cui-drawer-extent, 40rem); }

        :where(.cui-drawer[data-placement^="inline-"]) {
          inset-block: 0;
          inline-size: min(var(--_cui-drawer-extent), 100dvi);
          block-size: 100dvb;
          border-block: 0;
        }
        :where(.cui-drawer[data-placement="inline-start"]) {
          inset-inline-start: 0;
          inset-inline-end: auto;
          border-inline-end: 1px solid var(--_cui-drawer-border-color);
          border-start-end-radius: var(--_cui-drawer-radius);
          border-end-end-radius: var(--_cui-drawer-radius);
        }
        :where(.cui-drawer[data-placement="inline-end"]) {
          inset-inline-start: auto;
          inset-inline-end: 0;
          border-inline-start: 1px solid var(--_cui-drawer-border-color);
          border-start-start-radius: var(--_cui-drawer-radius);
          border-end-start-radius: var(--_cui-drawer-radius);
        }
        :where(.cui-drawer[data-placement^="block-"]) {
          inset-inline: 0;
          inline-size: 100dvi;
          block-size: min(var(--_cui-drawer-extent), 100dvb);
          border-inline: 0;
        }
        :where(.cui-drawer[data-placement="block-start"]) {
          inset-block-start: 0;
          inset-block-end: auto;
          border-block-end: 1px solid var(--_cui-drawer-border-color);
          border-end-start-radius: var(--_cui-drawer-radius);
          border-end-end-radius: var(--_cui-drawer-radius);
        }
        :where(.cui-drawer[data-placement="block-end"]) {
          inset-block-start: auto;
          inset-block-end: 0;
          border-block-start: 1px solid var(--_cui-drawer-border-color);
          border-start-start-radius: var(--_cui-drawer-radius);
          border-start-end-radius: var(--_cui-drawer-radius);
        }
        :where(.cui-drawer[data-size="full"]) {
          --_cui-drawer-extent: var(--cui-drawer-extent, 100%);
          border-width: 0;
          border-radius: 0;
        }

        :where(.cui-drawer__surface) {
          box-sizing: border-box;
          display: flex;
          flex-direction: column;
          gap: var(--_cui-drawer-gap);
          min-inline-size: 0;
          min-block-size: 0;
          inline-size: 100%;
          block-size: 100%;
          padding-top: max(var(--_cui-drawer-padding), env(safe-area-inset-top));
          padding-right: max(var(--_cui-drawer-padding), env(safe-area-inset-right));
          padding-bottom: max(var(--_cui-drawer-padding), env(safe-area-inset-bottom));
          padding-left: max(var(--_cui-drawer-padding), env(safe-area-inset-left));
        }
        :where(.cui-drawer[data-scroll="drawer"]) { overflow: auto; overscroll-behavior: contain; }
        :where(.cui-drawer[data-scroll="drawer"] .cui-drawer__surface) { block-size: auto; min-block-size: 100%; }
        :where(.cui-drawer__header) {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: var(--_cui-drawer-gap);
          align-items: start;
        }
        :where(.cui-drawer__title) {
          min-inline-size: 0;
          margin: 0;
          overflow-wrap: anywhere;
          font-size: 1.25rem;
          font-weight: 700;
          line-height: 1.3;
        }
        :where(.cui-drawer__description) {
          min-inline-size: 0;
          overflow-wrap: anywhere;
          color: color-mix(in srgb, currentColor 72%, transparent);
          line-height: 1.5;
        }
        :where(.cui-drawer__body) {
          flex: 1 1 auto;
          min-inline-size: 0;
          min-block-size: 0;
          overflow-wrap: anywhere;
          line-height: 1.5;
        }
        :where(.cui-drawer[data-scroll="body"] .cui-drawer__body) {
          overflow: auto;
          overscroll-behavior: contain;
        }
        :where(.cui-drawer__actions) {
          display: flex;
          flex-wrap: wrap;
          gap: 0.75rem;
          justify-content: end;
          min-inline-size: 0;
          overflow-wrap: anywhere;
        }
        :where(.cui-drawer__close) {
          display: inline-grid;
          place-items: center;
          inline-size: var(--_cui-drawer-close-size);
          block-size: var(--_cui-drawer-close-size);
          padding: 0;
          border: 0;
          border-radius: var(--_cui-drawer-close-radius);
          background: transparent;
          color: inherit;
          font: inherit;
          font-size: 1.5rem;
          line-height: 1;
          cursor: pointer;
        }
        :where(.cui-drawer__close[hidden]) { display: none; }
        @media (hover: hover) {
          :where(.cui-drawer__close:hover) { background: color-mix(in srgb, currentColor 10%, transparent); }
        }
        :where(.cui-drawer__close:focus-visible) {
          outline: 0.1875rem solid Highlight;
          outline-offset: 0.125rem;
        }
        @media (forced-colors: active) {
          :where(.cui-drawer) { border-color: CanvasText; }
          :where(.cui-drawer__close) { border: 1px solid ButtonText; }
        }
        @media print {
          :where(.cui-drawer:not([open])) { display: none; }
        }
      }
    """

    messages = """
      citry-ui-drawer-close = Close
    """


__all__ = [
    "CDrawer",
    "CDrawerActionsSlotData",
    "CDrawerActivatorSlotData",
    "CDrawerCloseSlotData",
    "CDrawerDefaultSlotData",
    "CDrawerDescriptionSlotData",
    "CDrawerInitialFocus",
    "CDrawerPlacement",
    "CDrawerScroll",
    "CDrawerSize",
    "CDrawerTitleSlotData",
]
