"""Private native Dialog lifecycle shared by Citry UI modal families."""

from citry.ext.dependencies import Script

DIALOG_CONTROLLER_RUNTIME_KEY = "citry-ui:dialog-controller-runtime"
DIALOG_CONTROLLER_RUNTIME_GENERATION = 1

DIALOG_CONTROLLER_RUNTIME_JS = r"""
  (() => {
    const key = Symbol.for("citry-ui:dialog-controller-runtime");
    const installed = globalThis[key];
    if (installed !== undefined) {
      if (installed.generation !== 1) {
        throw new Error(
          "[citry-ui] cannot replace an incompatible Dialog controller; "
            + "a full page reload is required.",
        );
      }
      return;
    }

    const modalRecords = [];
    /* citry-ui:command-palette-attribution:dialog-document-lock-state:begin */
    const documentLocks = new WeakMap();
    /* citry-ui:command-palette-attribution:dialog-document-lock-state:end */
    /* citry-ui:command-palette-attribution:dialog-handoff-keys:begin */
    const handoffKey = Symbol.for("citry-ui:dialog-controller-handoff");
    const ownerKey = Symbol.for("citry-ui:dialog-controller-owner");
    /* citry-ui:command-palette-attribution:dialog-handoff-keys:end */
    /* citry-ui:command-palette-attribution:dialog-root-scope-state:begin */
    const scopeManagers = new WeakMap();

    const deepActive = (documentOwner) => {
      let active = documentOwner.activeElement;
      while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
      return active;
    };
    const supportedRoot = (element, documentOwner) => {
      const root = element.getRootNode();
      return root === documentOwner
        || (root instanceof ShadowRoot
          && root.mode === "open"
          && root.host.ownerDocument === documentOwner
          && root.host.shadowRoot === root);
    };
    /* citry-ui:command-palette-attribution:dialog-root-scope-state:end */
    const isFocusable = (element) => element instanceof HTMLElement
      && element.isConnected
      && !element.hidden
      && !element.matches(":disabled,[inert]")
      && !element.closest("[inert]")
      && element.getClientRects().length > 0
      && getComputedStyle(element).visibility !== "hidden";
    /* citry-ui:command-palette-attribution:dialog-document-lock:begin */
    const lock = (documentOwner, dialog) => {
      let state = documentLocks.get(documentOwner);
      if (!state) {
        state = { dialogs: [], overflow: "", paddingInlineEnd: "" };
        documentLocks.set(documentOwner, state);
      }
      if (state.dialogs.includes(dialog)) return;
      if (state.dialogs.length === 0) {
        const root = documentOwner.documentElement;
        state.overflow = root.style.overflow;
        state.paddingInlineEnd = root.style.paddingInlineEnd;
        const view = documentOwner.defaultView;
        const scrollbarWidth = Math.max(0, (view?.innerWidth ?? root.clientWidth) - root.clientWidth);
        const currentPadding = Number.parseFloat(view?.getComputedStyle(root).paddingInlineEnd) || 0;
        root.style.overflow = "hidden";
        if (scrollbarWidth > 0) root.style.paddingInlineEnd = `${currentPadding + scrollbarWidth}px`;
      }
      state.dialogs.push(dialog);
    };
    const unlock = (documentOwner, dialog) => {
      const state = documentLocks.get(documentOwner);
      if (!state) return;
      const index = state.dialogs.indexOf(dialog);
      if (index < 0) return;
      state.dialogs.splice(index, 1);
      if (state.dialogs.length === 0) {
        const root = documentOwner.documentElement;
        root.style.overflow = state.overflow;
        root.style.paddingInlineEnd = state.paddingInlineEnd;
        documentLocks.delete(documentOwner);
      }
    };
    /* citry-ui:command-palette-attribution:dialog-document-lock:end */
    const register = (record) => {
      if (!modalRecords.includes(record)) modalRecords.push(record);
    };
    const unregister = (record) => {
      const index = modalRecords.indexOf(record);
      if (index >= 0) modalRecords.splice(index, 1);
    };
    /* citry-ui:command-palette-attribution:dialog-root-scope-manager:begin */
    const watchScope = (scope, owner) => {
      let manager = scopeManagers.get(scope);
      if (!manager) {
        const owners = new Set();
        const observer = new MutationObserver(() => {
          for (const candidate of [...owners]) candidate.validate();
        });
        observer.observe(scope instanceof Document ? scope.documentElement : scope, {
          subtree: true,
          childList: true,
        });
        manager = { owners, observer };
        scopeManagers.set(scope, manager);
      }
      manager.owners.add(owner);
      return () => {
        manager.owners.delete(owner);
        if (manager.owners.size === 0) {
          manager.observer.disconnect();
          scopeManagers.delete(scope);
        }
      };
    };
    /* citry-ui:command-palette-attribution:dialog-root-scope-manager:end */

    const create = ({
      host,
      dialog,
      surface,
      title,
      closeButton,
      signature,
      policy,
      initialFocus,
      containmentFallback,
      escapeBlocked,
      interceptDialogSubmit,
      requestClose,
      nativeClosed,
      forceClose,
      failed,
      handoffAborted,
    }) => {
      if (
        !(host instanceof HTMLElement)
        || !(dialog instanceof HTMLDialogElement)
        || !(surface instanceof HTMLElement)
        || !(title instanceof HTMLElement)
        || !(closeButton instanceof HTMLButtonElement)
        || dialog.parentElement !== host
        || surface.parentElement !== dialog
      ) {
        throw new TypeError("[citry-ui] Dialog controller received invalid owned anatomy.");
      }
      const documentOwner = host.ownerDocument;
      if (!supportedRoot(host, documentOwner)) {
        throw new TypeError("[citry-ui] Dialog controller requires a Document or open ShadowRoot.");
      }
      let active = true;
      let appliedOpen = false;
      let expectedNativeClose = false;
      let pointerStartedOutside = false;
      let previousFocus = null;
      let focusGeneration = 0;
      let handedOff = false;
      /* citry-ui:command-palette-attribution:dialog-handoff-close-state:begin */
      let handoffCloseGuard = false;
      let handoffCloseIntent = false;
      let handoffFrame = null;
      /* citry-ui:command-palette-attribution:dialog-handoff-close-state:end */
      let actualRoot = host.getRootNode();
      const liveOwner = dialog[ownerKey] ?? null;
      liveOwner?.transfer?.();
      const owner = {
        active: true,
        transfer: null,
        validate: null,
      };
      /* citry-ui:command-palette-attribution:dialog-focus-target:begin */
      const initialFocusTarget = initialFocus?.() ?? null;
      /* citry-ui:command-palette-attribution:dialog-focus-target:end */

      /* citry-ui:command-palette-attribution:dialog-handoff-consume:begin */
      const previous = dialog[handoffKey] ?? null;
      const abortPrevious = () => {
        if (!previous) return;
        if (previous.timer !== null) clearTimeout(previous.timer);
        previous.abort();
        if (dialog[handoffKey] === previous) delete dialog[handoffKey];
      };
      const retained = Boolean(previous
        && previous.host === host
        && previous.dialog === dialog
        && previous.surface === surface
        && previous.title === title
        && previous.closeButton === closeButton
        && previous.documentOwner === documentOwner
        && previous.actualRoot === actualRoot
        && previous.signature === signature
        && previous.initialFocusTarget === initialFocusTarget);
      if (previous && !retained) abortPrevious();
      if (retained) {
        if (previous.timer !== null) clearTimeout(previous.timer);
        appliedOpen = previous.appliedOpen && dialog.open;
        previousFocus = previous.previousFocus;
        handoffCloseGuard = true;
        handoffFrame = requestAnimationFrame(() => {
          handoffFrame = requestAnimationFrame(() => {
            handoffFrame = null;
            handoffCloseGuard = false;
            handoffCloseIntent = false;
          });
        });
        delete dialog[handoffKey];
      }
      /* citry-ui:command-palette-attribution:dialog-handoff-consume:end */

      const currentPolicy = () => policy?.() ?? {};
      const ownedFocusables = () => {
        const elements = [...dialog.querySelectorAll(
          'a[href], area[href], button:not(:disabled), input:not(:disabled):not([type="hidden"]), '
            + 'select:not(:disabled), textarea:not(:disabled), iframe, object, embed, '
            + 'audio[controls], video[controls], summary, '
            + '[contenteditable]:not([contenteditable="false"]), '
            + '[tabindex]:not([tabindex="-1"]):not([inert])',
        )].filter((element) => isFocusable(element) && element.closest("dialog") === dialog);
        return elements
          .map((element, index) => ({ element, index, tabIndex: element.tabIndex }))
          .filter(({ tabIndex }) => tabIndex >= 0)
          .sort((left, right) => {
            if (left.tabIndex > 0 && right.tabIndex === 0) return -1;
            if (left.tabIndex === 0 && right.tabIndex > 0) return 1;
            if (left.tabIndex > 0 && right.tabIndex > 0 && left.tabIndex !== right.tabIndex) {
              return left.tabIndex - right.tabIndex;
            }
            return left.index - right.index;
          })
          .map(({ element }) => element);
      };
      /* citry-ui:command-palette-attribution:dialog-focus-hooks:begin */
      const focusInitial = () => {
        const generation = ++focusGeneration;
        queueMicrotask(() => {
          if (!active || generation !== focusGeneration || !appliedOpen || !dialog.open) return;
          const target = initialFocus?.() ?? null;
          if (isFocusable(target)) target.focus({ preventScroll: true });
        });
      };
      /* citry-ui:command-palette-attribution:dialog-focus-hooks:end */
      /* citry-ui:command-palette-attribution:dialog-focus-restore:begin */
      const restoreFocus = (browserFocus = null) => {
        const generation = ++focusGeneration;
        queueMicrotask(() => {
          if (!active || generation !== focusGeneration || appliedOpen) return;
          const current = deepActive(documentOwner);
          const browserNeedsHelp = current === null
            || current === documentOwner.body
            || current === documentOwner.documentElement
            || current === dialog
            || dialog.contains(current)
            || current === browserFocus;
          if (browserNeedsHelp && isFocusable(previousFocus)) {
            previousFocus.focus({ preventScroll: true });
          }
        });
      };
      /* citry-ui:command-palette-attribution:dialog-focus-restore:end */
      const eventIsOutside = (event) => {
        if (event.target !== dialog) return false;
        const rect = surface.getBoundingClientRect();
        return event.clientX < rect.left
          || event.clientX > rect.right
          || event.clientY < rect.top
          || event.clientY > rect.bottom;
      };
      const closeDescendants = (reason = "ancestor") => {
        for (const candidate of [...modalRecords].reverse()) {
          if (candidate !== record && dialog.contains(candidate.dialog) && candidate.dialog.open) {
            candidate.force(reason, dialog);
          }
        }
      };
      const setOpen = (nextOpen, source = null, returnValue = "") => {
        if (!active) return false;
        const next = Boolean(nextOpen);
        if (!next) closeDescendants();
        if (next === appliedOpen && dialog.open === next) return true;
        if (next) {
          if (!supportedRoot(host, documentOwner)) return false;
          previousFocus = source instanceof Element ? source : deepActive(documentOwner);
          dialog.returnValue = "";
          if (dialog.open) dialog.removeAttribute("open");
          try {
            const anchoredRuntime = globalThis[Symbol.for("citry-ui:anchored-layer-runtime")];
            anchoredRuntime?.coordinatorFor?.(dialog)?.prepareModal?.(dialog, source ?? dialog);
            dialog.showModal();
          } catch {
            appliedOpen = false;
            failed?.();
            return false;
          }
          appliedOpen = true;
          register(record);
          lock(documentOwner, dialog);
          focusInitial();
          return true;
        }
        expectedNativeClose = dialog.open;
        if (dialog.open) dialog.close(returnValue);
        const browserFocus = deepActive(documentOwner);
        appliedOpen = false;
        unregister(record);
        unlock(documentOwner, dialog);
        restoreFocus(browserFocus);
        return true;
      };
      const onCancel = (event) => {
        event.preventDefault();
        if (escapeBlocked?.()) return;
        const configuration = currentPolicy();
        if (configuration.dismissible !== false && configuration.closeOnEscape !== false) {
          requestClose?.("escape", dialog, "");
        }
      };
      const onKeyDown = (event) => {
        if (event.key !== "Tab" || event.target.closest?.("dialog") !== dialog) return;
        const focusable = ownedFocusables();
        if (!focusable.length) {
          event.preventDefault();
          const target = initialFocus?.() ?? containmentFallback?.() ?? dialog;
          if (isFocusable(target)) target.focus({ preventScroll: true });
          return;
        }
        const first = focusable[0];
        const last = focusable.at(-1);
        const current = deepActive(documentOwner);
        if (event.shiftKey && (current === first || current === dialog || current === title)) {
          event.preventDefault();
          last.focus({ preventScroll: true });
        } else if (!event.shiftKey && current === last) {
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
      const onClick = (event) => {
        const shouldClose = pointerStartedOutside && eventIsOutside(event);
        pointerStartedOutside = false;
        const configuration = currentPolicy();
        if (
          shouldClose
          && configuration.dismissible !== false
          && configuration.closeOnOutside !== false
        ) requestClose?.("outside", dialog, "");
      };
      const onSubmit = (event) => {
        if (!interceptDialogSubmit?.()) return;
        const form = event.target;
        if (event.defaultPrevented || !(form instanceof HTMLFormElement)) return;
        if (form.closest("dialog") !== dialog) return;
        const submitter = event.submitter;
        const override = (submitter instanceof HTMLButtonElement
          || submitter instanceof HTMLInputElement) && submitter.hasAttribute("formmethod");
        const method = override ? submitter.formMethod : form.method;
        if (method.toLowerCase() !== "dialog") return;
        event.preventDefault();
        const returnValue = submitter instanceof HTMLButtonElement
          || submitter instanceof HTMLInputElement ? submitter.value : "";
        requestClose?.("native", submitter ?? form, returnValue);
      };
      /* citry-ui:command-palette-attribution:dialog-handoff-close-intent:begin */
      const onBeforeToggle = (event) => {
        if (handoffCloseGuard && event.newState === "closed") handoffCloseIntent = true;
      };
      /* citry-ui:command-palette-attribution:dialog-handoff-close-intent:end */
      const onNativeClose = () => {
        if (expectedNativeClose) {
          expectedNativeClose = false;
          /* citry-ui:command-palette-attribution:dialog-handoff-close-expected:begin */
          handoffCloseIntent = false;
          /* citry-ui:command-palette-attribution:dialog-handoff-close-expected:end */
          return;
        }
        /* citry-ui:command-palette-attribution:dialog-handoff-close-reclaim:begin */
        if (
          handoffCloseGuard
          && !handoffCloseIntent
          && active
          && dialog[ownerKey] === owner
          && appliedOpen
        ) {
          try {
            dialog.showModal();
          } catch {
            appliedOpen = false;
            failed?.();
            return;
          }
          register(record);
          lock(documentOwner, dialog);
          focusInitial();
          return;
        }
        /* citry-ui:command-palette-attribution:dialog-handoff-close-reclaim:end */
        /* citry-ui:command-palette-attribution:dialog-handoff-close-retire:begin */
        handoffCloseIntent = false;
        /* citry-ui:command-palette-attribution:dialog-handoff-close-retire:end */
        closeDescendants();
        appliedOpen = false;
        unregister(record);
        unlock(documentOwner, dialog);
        const browserFocus = deepActive(documentOwner);
        nativeClosed?.("native", dialog, dialog.returnValue);
        restoreFocus(browserFocus);
      };
      const force = (reason = "ancestor", source = dialog) => {
        forceClose?.(reason, source);
        if (dialog.open || appliedOpen) setOpen(false, source);
      };

      const record = { dialog, force };
      /* citry-ui:command-palette-attribution:dialog-root-scope-refresh:begin */
      let unwatchScope = watchScope(actualRoot, owner);
      const refreshRoot = () => {
        const nextRoot = host.getRootNode();
        if (nextRoot === actualRoot) return true;
        if (
          !supportedRoot(host, documentOwner)
          || dialog.getRootNode() !== nextRoot
          || surface.getRootNode() !== nextRoot
          || title.getRootNode() !== nextRoot
          || closeButton.getRootNode() !== nextRoot
        ) return false;
        if (dialog.open || appliedOpen) force("ancestor", host);
        unwatchScope();
        actualRoot = nextRoot;
        unwatchScope = watchScope(actualRoot, owner);
        return true;
      };
      owner.validate = () => {
        if (!active || dialog[ownerKey] !== owner) return;
        if (
          !host.isConnected
          || host.ownerDocument !== documentOwner
          || !supportedRoot(host, documentOwner)
          || !refreshRoot()
        ) force("ancestor", host);
      };
      /* citry-ui:command-palette-attribution:dialog-root-scope-refresh:end */
      dialog.addEventListener("cancel", onCancel);
      dialog.addEventListener("keydown", onKeyDown);
      dialog.addEventListener("pointerdown", onPointerDown);
      dialog.addEventListener("pointercancel", onPointerCancel);
      dialog.addEventListener("click", onClick);
      dialog.addEventListener("submit", onSubmit);
      /* citry-ui:command-palette-attribution:dialog-handoff-close-listener:begin */
      dialog.addEventListener("beforetoggle", onBeforeToggle);
      /* citry-ui:command-palette-attribution:dialog-handoff-close-listener:end */
      dialog.addEventListener("close", onNativeClose);
      if (retained && appliedOpen) register(record);

      const cleanup = ({ handoff = false } = {}) => {
        if (!active) return false;
        active = false;
        owner.active = false;
        focusGeneration += 1;
        /* citry-ui:command-palette-attribution:dialog-handoff-close-cleanup:begin */
        if (handoffFrame !== null) cancelAnimationFrame(handoffFrame);
        handoffFrame = null;
        handoffCloseGuard = false;
        handoffCloseIntent = false;
        /* citry-ui:command-palette-attribution:dialog-handoff-close-cleanup:end */
        dialog.removeEventListener("cancel", onCancel);
        dialog.removeEventListener("keydown", onKeyDown);
        dialog.removeEventListener("pointerdown", onPointerDown);
        dialog.removeEventListener("pointercancel", onPointerCancel);
        dialog.removeEventListener("click", onClick);
        dialog.removeEventListener("submit", onSubmit);
        /* citry-ui:command-palette-attribution:dialog-handoff-close-unlisten:begin */
        dialog.removeEventListener("beforetoggle", onBeforeToggle);
        /* citry-ui:command-palette-attribution:dialog-handoff-close-unlisten:end */
        dialog.removeEventListener("close", onNativeClose);
        unwatchScope();
        if (dialog[ownerKey] === owner) delete dialog[ownerKey];
        const canHandoff = handoff
          && host.isConnected
          && dialog.isConnected
          && supportedRoot(host, documentOwner);
        /* citry-ui:command-palette-attribution:dialog-handoff-produce:begin */
        if (canHandoff) {
          handedOff = true;
          unregister(record);
          const handoffRecord = {
            host,
            dialog,
            surface,
            title,
            closeButton,
            documentOwner,
            actualRoot: host.getRootNode(),
            signature,
            initialFocusTarget,
            appliedOpen,
            previousFocus,
            timer: null,
            abort() {
              closeDescendants();
              expectedNativeClose = dialog.open;
              if (dialog.open) dialog.close();
              appliedOpen = false;
              unlock(documentOwner, dialog);
              handoffAborted?.();
            },
          };
          dialog[handoffKey] = handoffRecord;
          handoffRecord.timer = setTimeout(() => {
            if (dialog[handoffKey] !== handoffRecord) return;
            handoffRecord.abort();
            delete dialog[handoffKey];
          }, 1000);
          return true;
        }
        /* citry-ui:command-palette-attribution:dialog-handoff-produce:end */
        closeDescendants();
        expectedNativeClose = dialog.open;
        if (dialog.open) dialog.close();
        appliedOpen = false;
        unregister(record);
        unlock(documentOwner, dialog);
        restoreFocus();
        return false;
      };
      owner.transfer = () => cleanup({ handoff: true });
      dialog[ownerKey] = owner;

      return {
        setOpen,
        isOpen: () => appliedOpen && dialog.open,
        focusInitial,
        refreshRoot,
        force,
        cleanup,
        retained,
        handedOff: () => handedOff,
      };
    };

    /* citry-ui:command-palette-attribution:dialog-handoff-abort:begin */
    const abortHandoff = (dialog) => {
      const record = dialog?.[handoffKey] ?? null;
      if (!record) return false;
      if (record.timer !== null) clearTimeout(record.timer);
      record.abort();
      if (dialog[handoffKey] === record) delete dialog[handoffKey];
      return true;
    };
    /* citry-ui:command-palette-attribution:dialog-handoff-abort:end */

    globalThis[key] = {
      generation: 1,
      create,
      abortHandoff,
      deepActive,
      isFocusable,
      counts: () => ({ modals: modalRecords.length }),
    };
  })();
"""

DIALOG_CONTROLLER_RUNTIME_DEPENDENCY = Script(content=DIALOG_CONTROLLER_RUNTIME_JS)


__all__: list[str] = []
