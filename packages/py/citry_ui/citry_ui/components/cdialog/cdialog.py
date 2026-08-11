"""Styled native modal Dialog component family."""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
)

CDialogInitialFocus = Literal["auto", "title"]
CDialogScroll = Literal["body", "dialog"]
CDialogSize = Literal["sm", "md", "lg", "full"]


class CDialogActivatorSlotData:
    activator_attrs: dict[str, object]


class CDialogTitleSlotData:
    pass


class CDialogDescriptionSlotData:
    pass


class CDialogDefaultSlotData:
    pass


class CDialogActionsSlotData:
    close_attrs: dict[str, object]


class CDialogCloseSlotData:
    pass


class CDialog(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        open: bool = False
        dismissible: bool = True
        close_on_escape: bool = True
        close_on_outside: bool = True
        initial_focus: CDialogInitialFocus = "auto"
        size: CDialogSize = "md"
        scroll: CDialogScroll = "body"
        close_label: str = "Close"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        title: SlotInput[CDialogTitleSlotData]
        default: SlotInput[CDialogDefaultSlotData]
        activator: SlotInput[CDialogActivatorSlotData] | None = None
        description: SlotInput[CDialogDescriptionSlotData] | None = None
        actions: SlotInput[CDialogActionsSlotData] | None = None
        close: SlotInput[CDialogCloseSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        validate_html_id("CDialog", kwargs.id)
        validate_boolean("CDialog", "open", kwargs.open)
        validate_boolean("CDialog", "dismissible", kwargs.dismissible)
        validate_boolean("CDialog", "close_on_escape", kwargs.close_on_escape)
        validate_boolean("CDialog", "close_on_outside", kwargs.close_on_outside)
        validate_choice("CDialog", "initial_focus", kwargs.initial_focus, ("auto", "title"))
        validate_choice("CDialog", "size", kwargs.size, ("sm", "md", "lg", "full"))
        validate_choice("CDialog", "scroll", kwargs.scroll, ("body", "dialog"))
        validate_non_empty_string("CDialog", "close_label", kwargs.close_label)
        reject_owned_attrs(
            kwargs.attrs,
            {
                "aria-label",
                "aria-describedby",
                "aria-labelledby",
                "aria-modal",
                "closedby",
                "data-citry-dialog-built-in-close",
                "data-citry-dialog-close",
                "data-citry-dialog-host",
                "data-citry-dialog-initialized",
                "data-citry-dialog-trigger",
                "data-citry-ui-part",
                "data-open",
                "data-scroll",
                "data-size",
                "id",
                "open",
                "popover",
                "role",
                "tabindex",
            },
            "CDialog",
        )

        dialog_id = kwargs.id or f"cui-dialog-{self.id}"
        title_id = f"{dialog_id}-title"
        description_id = f"{dialog_id}-description"
        has_description = "description" in self.raw_slots
        return {
            "dialog_id": dialog_id,
            "title_id": title_id,
            "description_id": description_id,
            "described_by": description_id if has_description else None,
            "open": kwargs.open,
            "dismissible": kwargs.dismissible,
            "initial_focus": kwargs.initial_focus,
            "title_tabindex": -1 if kwargs.initial_focus == "title" else None,
            "size": kwargs.size,
            "scroll": kwargs.scroll,
            "close_label": kwargs.close_label,
            "has_activator": "activator" in self.raw_slots,
            "has_description": has_description,
            "has_actions": "actions" in self.raw_slots,
            "has_close": "close" in self.raw_slots,
            "activator_attrs": {
                "aria-haspopup": "dialog",
                "aria-controls": dialog_id,
                "aria-expanded": "true" if kwargs.open else "false",
                "data-citry-dialog-trigger": "",
            },
            "close_attrs": {
                "data-citry-dialog-close": "",
            },
            "attrs": merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style),
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "open": kwargs.open,
            "dismissible": kwargs.dismissible,
            "closeOnEscape": kwargs.close_on_escape,
            "closeOnOutside": kwargs.close_on_outside,
            "initialFocus": kwargs.initial_focus,
            "size": kwargs.size,
            "scroll": kwargs.scroll,
        }

    template = """
      <div
        class="cui-dialog-host"
        data-citry-dialog-host
      >
        <c-if cond="has_activator">
          <c-slot
            name="activator"
            c-activator_attrs="activator_attrs"
          />
        </c-if>
        <dialog
          class="cui-dialog"
          data-citry-dialog-surface
          c-id="dialog_id"
          c-open="open"
          c-aria-labelledby="title_id"
          c-aria-describedby="described_by"
          aria-modal="true"
          c-data-open="open"
          c-data-size="size"
          c-data-scroll="scroll"
          c-bind="attrs"
          data-citry-ui-part="dialog"
        >
          <div
            class="cui-dialog__surface"
            data-citry-ui-part="surface"
          >
            <header
              class="cui-dialog__header"
              data-citry-ui-part="header"
            >
              <h2
                class="cui-dialog__title"
                c-id="title_id"
                c-tabindex="title_tabindex"
                data-citry-ui-part="title"
              >
                <c-slot name="title" required />
              </h2>
              <button
                class="cui-dialog__close"
                type="button"
                c-aria-label="close_label"
                c-hidden="not dismissible"
                data-citry-dialog-close
                data-citry-dialog-built-in-close
                data-citry-ui-part="close"
              >
                <c-if cond="has_close">
                  <c-slot name="close" />
                </c-if>
                <c-else>
                  <span aria-hidden="true">
                    &times;
                  </span>
                </c-else>
              </button>
            </header>
            <c-if cond="has_description">
              <div
                class="cui-dialog__description"
                c-id="description_id"
                data-citry-ui-part="description"
              >
                <c-slot name="description" />
              </div>
            </c-if>
            <div
              class="cui-dialog__body"
              data-citry-ui-part="body"
            >
              <c-slot required />
            </div>
            <c-if cond="has_actions">
              <footer
                class="cui-dialog__actions"
                data-citry-ui-part="actions"
              >
                <c-slot
                  name="actions"
                  c-close_attrs="close_attrs"
                />
              </footer>
            </c-if>
          </div>
        </dialog>
      </div>
    """

    js = """
      const runtimeKey = Symbol.for("citry-ui:dialog-runtime");
      const runtime = globalThis[runtimeKey] ?? {
        dialogs: [],
        overflow: "",
        paddingInlineEnd: "",
      };
      globalThis[runtimeKey] = runtime;

      $component({
        props: {
          open: {},
          dismissible: {},
          closeOnEscape: {},
          closeOnOutside: {},
          initialFocus: {},
          size: {},
          scroll: {},
          onOpenChange: {},
        },
        init: ({ els, data, props, effect }) => {
          const host = els[0];
          const nearestHost = (element) => element?.closest?.("[data-citry-dialog-host]") ?? null;
          const dialog = [...host.querySelectorAll('[data-citry-dialog-surface]')]
            .find((candidate) => nearestHost(candidate) === host);
          const surface = dialog.querySelector(':scope > [data-citry-ui-part="surface"]');
          const title = surface.querySelector('[data-citry-ui-part="title"]');
          const closeButton = surface.querySelector('[data-citry-dialog-built-in-close]');
          const allowedValues = {
            initialFocus: ["auto", "title"],
            size: ["sm", "md", "lg", "full"],
            scroll: ["body", "dialog"],
          };
          const invalidEpisodes = new Map();
          let internalOpen = data.open;
          let controlled = false;
          let appliedOpen = false;
          let suppressStaleControlledOpen = false;
          let pendingControlledReturnValue = "";
          let expectedNativeClose = false;
          let pointerStartedOutside = false;
          let previousFocus = null;
          let onOpenChange = null;
          let configuration = {
            dismissible: data.dismissible,
            closeOnEscape: data.closeOnEscape,
            closeOnOutside: data.closeOnOutside,
            initialFocus: data.initialFocus,
            size: data.size,
            scroll: data.scroll,
          };

          const ownedElements = (selector) => [...host.querySelectorAll(selector)]
            .filter((element) => nearestHost(element) === host);
          const ownedActivators = () => ownedElements("[data-citry-dialog-trigger]");
          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value) => {
            const describedValue = describeValue(value);
            const fingerprint = `${typeof value}:${describedValue}`;
            if (invalidEpisodes.get(name) === fingerprint) {
              return;
            }
            invalidEpisodes.set(name, fingerprint);
            console.error(
              `[citry-ui] CDialog ${name} received invalid client value ${describedValue}; `
                + "using the current or server-rendered fallback.",
              dialog,
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
          const resolveEnum = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (allowedValues[name].includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
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
          const updateActivators = (open) => {
            for (const activator of ownedActivators()) {
              activator.setAttribute("aria-expanded", open ? "true" : "false");
            }
          };
          const lockScroll = () => {
            if (runtime.dialogs.includes(dialog)) {
              return;
            }
            if (runtime.dialogs.length === 0) {
              const root = document.documentElement;
              runtime.overflow = root.style.overflow;
              runtime.paddingInlineEnd = root.style.paddingInlineEnd;
              const scrollbarWidth = Math.max(0, window.innerWidth - root.clientWidth);
              const currentPadding = Number.parseFloat(getComputedStyle(root).paddingInlineEnd) || 0;
              root.style.overflow = "hidden";
              if (scrollbarWidth > 0) {
                root.style.paddingInlineEnd = `${currentPadding + scrollbarWidth}px`;
              }
            }
            runtime.dialogs.push(dialog);
          };
          const unlockScroll = () => {
            const index = runtime.dialogs.indexOf(dialog);
            if (index === -1) {
              return;
            }
            runtime.dialogs.splice(index, 1);
            if (runtime.dialogs.length === 0) {
              const root = document.documentElement;
              root.style.overflow = runtime.overflow;
              root.style.paddingInlineEnd = runtime.paddingInlineEnd;
            }
          };
          const isFocusable = (element) => element instanceof HTMLElement
            && !element.hidden
            && !element.matches(":disabled,[inert]")
            && !element.closest("[inert]")
            && element.getClientRects().length > 0
            && getComputedStyle(element).visibility !== "hidden";
          const radioIsTabStop = (element) => {
            if (!(element instanceof HTMLInputElement) || element.type !== "radio" || !element.name) {
              return true;
            }
            const group = [...dialog.querySelectorAll('input[type="radio"]')]
              .filter((radio) => radio.name === element.name
                && radio.form === element.form
                && radio.closest("dialog") === dialog
                && isFocusable(radio));
            const checked = group.find((radio) => radio.checked);
            return checked ? element === checked : element === group[0];
          };
          const focusableElements = () => {
            const elements = [...dialog.querySelectorAll(
              'a[href], area[href], button:not(:disabled), input:not(:disabled):not([type="hidden"]), '
                + 'select:not(:disabled), textarea:not(:disabled), iframe, object, embed, '
                + 'audio[controls], video[controls], summary, [contenteditable]:not([contenteditable="false"]), '
                + '[tabindex]:not([tabindex="-1"]):not([inert])',
            )].filter((element) => isFocusable(element)
              && element.closest("dialog") === dialog
              && radioIsTabStop(element));
            return elements
              .map((element, index) => ({ element, index, tabIndex: element.tabIndex }))
              .filter(({ tabIndex }) => tabIndex >= 0)
              .sort((left, right) => {
                if (left.tabIndex > 0 && right.tabIndex === 0) {
                  return -1;
                }
                if (left.tabIndex === 0 && right.tabIndex > 0) {
                  return 1;
                }
                if (left.tabIndex > 0 && right.tabIndex > 0 && left.tabIndex !== right.tabIndex) {
                  return left.tabIndex - right.tabIndex;
                }
                return left.index - right.index;
              })
              .map(({ element }) => element);
          };
          const focusTitle = () => {
            if (configuration.initialFocus === "title" && isFocusable(title)) {
              title.focus({ preventScroll: true });
            }
          };
          const ensureFocusRestored = () => {
            // The HTML close algorithm owns the destination. WebKit does not
            // consistently perform that restoration, so repeat the same target
            // only when the browser did not restore it itself.
            if (
              previousFocus?.isConnected
              && document.activeElement !== previousFocus
              && isFocusable(previousFocus)
            ) {
              previousFocus.focus({ preventScroll: true });
            }
          };
          const closeDescendants = () => {
            // Native Dialog does not close a nested top-layer Dialog when its
            // ancestor closes. Close deepest descendants first so no invisible
            // modal can retain inertness or the shared scroll lock.
            for (const candidate of [...runtime.dialogs].reverse()) {
              if (candidate !== dialog && dialog.contains(candidate) && candidate.open) {
                candidate.close();
              }
            }
          };
          const applyOpen = (nextOpen, source = null, returnValue = "") => {
            if (!nextOpen) {
              closeDescendants();
            }
            if (nextOpen === appliedOpen && dialog.open === nextOpen) {
              return;
            }
            if (nextOpen) {
              previousFocus = source instanceof HTMLElement ? source : document.activeElement;
              dialog.returnValue = "";
              if (dialog.open) {
                dialog.removeAttribute("open");
              }
              try {
                dialog.showModal();
              } catch (error) {
                console.error("[citry-ui] CDialog could not enter modal state:", error, dialog);
                appliedOpen = false;
                updateActivators(false);
                return;
              }
              appliedOpen = true;
              dialog.setAttribute("data-open", "");
              updateActivators(true);
              lockScroll();
              queueMicrotask(focusTitle);
              return;
            }
            expectedNativeClose = dialog.open;
            if (dialog.open) {
              dialog.close(returnValue);
            }
            appliedOpen = false;
            dialog.removeAttribute("data-open");
            updateActivators(false);
            unlockScroll();
            queueMicrotask(ensureFocusRestored);
          };
          const notify = (nextOpen, reason, source, returnValue = "") => {
            onOpenChange?.(nextOpen, {
              reason,
              controlled,
              source,
              returnValue,
            });
          };
          const requestOpen = (nextOpen, reason, source, returnValue = "") => {
            if (nextOpen === appliedOpen) {
              return;
            }
            if (
              nextOpen
              && controlled
              && suppressStaleControlledOpen
              && props.open === true
            ) {
              suppressStaleControlledOpen = false;
              applyOpen(true, source);
              notify(true, reason, source, returnValue);
              return;
            }
            if (controlled) {
              pendingControlledReturnValue = nextOpen ? "" : returnValue;
              notify(nextOpen, reason, source, returnValue);
              return;
            }
            internalOpen = nextOpen;
            applyOpen(nextOpen, source, returnValue);
            notify(nextOpen, reason, source, returnValue);
          };
          const eventIsOutside = (event) => {
            if (event.target !== dialog) {
              return false;
            }
            const rect = surface.getBoundingClientRect();
            return event.clientX < rect.left
              || event.clientX > rect.right
              || event.clientY < rect.top
              || event.clientY > rect.bottom;
          };
          const onHostClick = (event) => {
            const trigger = event.target.closest?.("[data-citry-dialog-trigger]");
            if (trigger && nearestHost(trigger) === host) {
              requestOpen(true, "trigger", trigger);
              return;
            }
            const close = event.target.closest?.("[data-citry-dialog-close]");
            if (!close || nearestHost(close) !== host || !dialog.contains(close)) {
              return;
            }
            const builtIn = close.hasAttribute("data-citry-dialog-built-in-close");
            if (builtIn && !configuration.dismissible) {
              return;
            }
            const returnValue = close instanceof HTMLButtonElement ? close.value : "";
            requestOpen(false, builtIn ? "close-button" : "action", close, returnValue);
          };
          const onCancel = (event) => {
            event.preventDefault();
            if (configuration.dismissible && configuration.closeOnEscape) {
              requestOpen(false, "escape", dialog);
            }
          };
          const onKeyDown = (event) => {
            // Parent Dialogs receive bubbled key events from nested Dialogs. Only the
            // nearest native Dialog may apply its focus loop.
            if (event.key !== "Tab" || event.target.closest?.("dialog") !== dialog) {
              return;
            }
            const focusable = focusableElements();
            if (focusable.length === 0) {
              event.preventDefault();
              if (configuration.initialFocus === "title") {
                title.focus({ preventScroll: true });
              } else {
                dialog.focus({ preventScroll: true });
              }
              return;
            }
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (
              event.shiftKey
              && (
                document.activeElement === first
                || document.activeElement === dialog
                || document.activeElement === title
              )
            ) {
              event.preventDefault();
              last.focus({ preventScroll: true });
            } else if (!event.shiftKey && document.activeElement === last) {
              event.preventDefault();
              first.focus({ preventScroll: true });
            }
          };
          const onPointerDown = (event) => {
            pointerStartedOutside = eventIsOutside(event);
          };
          const onPointerCancel = () => {
            pointerStartedOutside = false;
          };
          const onDialogClick = (event) => {
            const shouldClose = pointerStartedOutside && eventIsOutside(event);
            pointerStartedOutside = false;
            if (shouldClose && configuration.dismissible && configuration.closeOnOutside) {
              requestOpen(false, "outside", dialog);
            }
          };
          const onSubmit = (event) => {
            const form = event.target;
            if (
              event.defaultPrevented
              || !(form instanceof HTMLFormElement)
              || form.closest("dialog") !== dialog
              || !controlled
            ) {
              return;
            }
            const submitter = event.submitter;
            const submitterOverridesMethod = (
              submitter instanceof HTMLButtonElement
              || submitter instanceof HTMLInputElement
            ) && submitter.hasAttribute("formmethod");
            const method = submitterOverridesMethod
              ? submitter.formMethod
              : form.method;
            if (method.toLowerCase() !== "dialog") {
              return;
            }

            // Native method=dialog closure cannot be undone. In controlled mode,
            // intercept only that final close so the owner can accept or decline
            // it like every other user-authored visibility request. Validation
            // and the native submit event have already completed at this point.
            event.preventDefault();
            const returnValue = (
              submitter instanceof HTMLButtonElement
              || submitter instanceof HTMLInputElement
            ) ? submitter.value : "";
            requestOpen(false, "native", submitter ?? form, returnValue);
          };
          const onNativeClose = () => {
            if (expectedNativeClose) {
              expectedNativeClose = false;
              return;
            }
            closeDescendants();
            suppressStaleControlledOpen = controlled && props.open === true;
            appliedOpen = false;
            internalOpen = false;
            dialog.removeAttribute("data-open");
            updateActivators(false);
            unlockScroll();
            notify(false, "native", dialog, dialog.returnValue);
            queueMicrotask(ensureFocusRestored);
          };

          host.addEventListener("click", onHostClick);
          dialog.addEventListener("cancel", onCancel);
          dialog.addEventListener("keydown", onKeyDown);
          dialog.addEventListener("pointerdown", onPointerDown);
          dialog.addEventListener("pointercancel", onPointerCancel);
          dialog.addEventListener("click", onDialogClick);
          dialog.addEventListener("submit", onSubmit);
          dialog.addEventListener("close", onNativeClose);
          effect(() => {
            const suppliedOpen = props.open;
            let nextOpen = internalOpen;
            if (suppliedOpen === undefined || suppliedOpen === null) {
              suppressStaleControlledOpen = false;
              pendingControlledReturnValue = "";
              if (controlled) {
                internalOpen = appliedOpen;
              }
              controlled = false;
              nextOpen = internalOpen;
              invalidEpisodes.delete("open");
            } else if (typeof suppliedOpen === "boolean") {
              controlled = true;
              if (!suppliedOpen) {
                suppressStaleControlledOpen = false;
              }
              nextOpen = suppressStaleControlledOpen ? false : suppliedOpen;
              invalidEpisodes.delete("open");
            } else {
              suppressStaleControlledOpen = false;
              pendingControlledReturnValue = "";
              reportInvalid("open", suppliedOpen);
              if (controlled) {
                internalOpen = appliedOpen;
              }
              controlled = false;
              nextOpen = internalOpen;
            }
            configuration = {
              dismissible: resolveBoolean("dismissible"),
              closeOnEscape: resolveBoolean("closeOnEscape"),
              closeOnOutside: resolveBoolean("closeOnOutside"),
              initialFocus: resolveEnum("initialFocus"),
              size: resolveEnum("size"),
              scroll: resolveEnum("scroll"),
            };
            onOpenChange = resolveCallback();
            if (closeButton) {
              closeButton.hidden = !configuration.dismissible;
            }
            if (configuration.initialFocus === "title") {
              title.setAttribute("tabindex", "-1");
            } else {
              title.removeAttribute("tabindex");
            }
            dialog.dataset.size = configuration.size;
            dialog.dataset.scroll = configuration.scroll;
            applyOpen(nextOpen, null, nextOpen ? "" : pendingControlledReturnValue);
            if ((nextOpen && appliedOpen) || (!nextOpen && !appliedOpen)) {
              pendingControlledReturnValue = "";
            }
          });
          host.setAttribute("data-citry-dialog-initialized", "");
          if (dialog.getAttribute("role") === "alertdialog") {
            host.setAttribute("data-citry-alert-dialog-initialized", "");
          }

          return () => {
            host.removeEventListener("click", onHostClick);
            dialog.removeEventListener("cancel", onCancel);
            dialog.removeEventListener("keydown", onKeyDown);
            dialog.removeEventListener("pointerdown", onPointerDown);
            dialog.removeEventListener("pointercancel", onPointerCancel);
            dialog.removeEventListener("click", onDialogClick);
            dialog.removeEventListener("submit", onSubmit);
            dialog.removeEventListener("close", onNativeClose);
            closeDescendants();
            expectedNativeClose = dialog.open;
            if (dialog.open) {
              dialog.close();
            }
            appliedOpen = false;
            updateActivators(false);
            unlockScroll();
            queueMicrotask(ensureFocusRestored);
            host.removeAttribute("data-citry-dialog-initialized");
            host.removeAttribute("data-citry-alert-dialog-initialized");
          };
        },
      });
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-dialog-host) {
          display: contents;
          color: CanvasText;
          font-family: ui-sans-serif, system-ui, sans-serif;
        }

        :where(.cui-dialog) {
          --_cui-dialog-backdrop: var(--cui-dialog-backdrop, rgb(15 23 42 / 58%));
          --_cui-dialog-background: var(--cui-dialog-background, Canvas);
          --_cui-dialog-foreground: var(--cui-dialog-foreground, CanvasText);
          --_cui-dialog-border-color: var(
            --cui-dialog-border-color,
            color-mix(in srgb, CanvasText 16%, transparent)
          );
          --_cui-dialog-radius: var(--cui-dialog-radius, 0.875rem);
          --_cui-dialog-shadow: var(
            --cui-dialog-shadow,
            0 1.5rem 4rem rgb(15 23 42 / 28%)
          );
          --_cui-dialog-inline-size: var(--cui-dialog-inline-size, 36rem);
          --_cui-dialog-max-block-size: var(
            --cui-dialog-max-block-size,
            calc(100dvb - 2rem)
          );
          --_cui-dialog-padding: var(--cui-dialog-padding, 1.25rem);
          --_cui-dialog-gap: var(--cui-dialog-gap, 1rem);
          --_cui-dialog-close-size: var(--cui-dialog-close-size, 2.5rem);
          --_cui-dialog-close-radius: var(--cui-dialog-close-radius, 0.5rem);

          box-sizing: border-box;
          inline-size: min(var(--_cui-dialog-inline-size), calc(100dvi - 2rem));
          max-inline-size: none;
          max-block-size: var(--_cui-dialog-max-block-size);
          margin: auto;
          padding: 0;
          overflow: hidden;
          border: 1px solid var(--_cui-dialog-border-color);
          border-radius: var(--_cui-dialog-radius);
          background: var(--_cui-dialog-background);
          color: var(--_cui-dialog-foreground);
          box-shadow: var(--_cui-dialog-shadow);
        }

        :where(.cui-dialog::backdrop) {
          background: var(--_cui-dialog-backdrop);
        }

        :where(.cui-dialog[data-size="sm"]) {
          --_cui-dialog-inline-size: var(--cui-dialog-inline-size, 26rem);
        }

        :where(.cui-dialog[data-size="lg"]) {
          --_cui-dialog-inline-size: var(--cui-dialog-inline-size, 52rem);
        }

        :where(.cui-dialog[data-size="full"]) {
          --_cui-dialog-inline-size: var(--cui-dialog-inline-size, 100dvi);
          --_cui-dialog-max-block-size: var(--cui-dialog-max-block-size, 100dvb);
          --_cui-dialog-radius: var(--cui-dialog-radius, 0);
          --_cui-dialog-shadow: var(--cui-dialog-shadow, none);

          inline-size: var(--_cui-dialog-inline-size);
          block-size: var(--_cui-dialog-max-block-size);
          margin: 0;
          border-width: 0;
        }

        :where(.cui-dialog__surface) {
          box-sizing: border-box;
          display: flex;
          flex-direction: column;
          gap: var(--_cui-dialog-gap);
          max-block-size: inherit;
          padding: var(--_cui-dialog-padding);
        }

        :where(.cui-dialog[data-size="full"] .cui-dialog__surface) {
          min-block-size: 100%;
        }

        :where(.cui-dialog[data-scroll="dialog"]) {
          overflow: auto;
          overscroll-behavior: contain;
        }

        :where(.cui-dialog[data-scroll="dialog"] .cui-dialog__surface) {
          max-block-size: none;
        }

        :where(.cui-dialog__header) {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: var(--_cui-dialog-gap);
          align-items: start;
        }

        :where(.cui-dialog__title) {
          margin: 0;
          font-size: 1.25rem;
          font-weight: 700;
          line-height: 1.3;
        }

        :where(.cui-dialog__description) {
          color: color-mix(in srgb, currentColor 72%, transparent);
          line-height: 1.5;
        }

        :where(.cui-dialog__body) {
          flex: 1 1 auto;
          min-block-size: 0;
          line-height: 1.5;
        }

        :where(.cui-dialog[data-scroll="body"] .cui-dialog__body) {
          overflow: auto;
          overscroll-behavior: contain;
        }

        :where(.cui-dialog__actions) {
          display: flex;
          flex-wrap: wrap;
          gap: 0.75rem;
          justify-content: end;
        }

        :where(.cui-dialog__close) {
          display: inline-grid;
          place-items: center;
          inline-size: var(--_cui-dialog-close-size);
          block-size: var(--_cui-dialog-close-size);
          padding: 0;
          border: 0;
          border-radius: var(--_cui-dialog-close-radius);
          background: transparent;
          color: inherit;
          font: inherit;
          font-size: 1.5rem;
          line-height: 1;
          cursor: pointer;
        }

        :where(.cui-dialog__close[hidden]) {
          display: none;
        }

        @media (hover: hover) {
          :where(.cui-dialog__close:hover) {
            background: color-mix(in srgb, currentColor 10%, transparent);
          }
        }

        :where(.cui-dialog__close:focus-visible) {
          outline: 0.1875rem solid Highlight;
          outline-offset: 0.125rem;
        }

        @media (forced-colors: active) {
          :where(.cui-dialog) {
            border-color: CanvasText;
          }

          :where(.cui-dialog__close) {
            border: 1px solid ButtonText;
          }
        }
      }
    """


__all__ = [
    "CDialog",
    "CDialogActionsSlotData",
    "CDialogActivatorSlotData",
    "CDialogCloseSlotData",
    "CDialogDefaultSlotData",
    "CDialogDescriptionSlotData",
    "CDialogInitialFocus",
    "CDialogScroll",
    "CDialogSize",
    "CDialogTitleSlotData",
]
