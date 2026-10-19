(function() {

const runtimeKey = Symbol.for("citry-ui:dialog-runtime");
const runtime = globalThis[runtimeKey] ?? {
  dialogs: [],
  overflow: "",
  paddingInlineEnd: "",
};
globalThis[runtimeKey] = runtime;

__citryRuntime.registerTypeOptions.bind(null, "CDialog_e133eb", "9ec2d09f8b2f2a1468264a5bc0be35aae3d75971489da6628685df1d69fd251f")({
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
  onServerRender: ({component}) => {
    const host = component.$el;
    const data = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const nearestHost = (element) => element?.closest?.("[data-citry-dialog-host]") ?? null;
    const dialog = [...host.querySelectorAll('[data-citry-dialog-surface]')]
      .find((candidate) => nearestHost(candidate) === host);
    const surface = dialog.querySelector(':scope > [data-citry-ui-part="surface"]');
    const title = surface.querySelector('[data-citry-ui-part="title"]');
    const closeButton = surface.querySelector('[data-citry-dialog-built-in-close]')
      ?? surface.querySelector('[data-citry-dialog-close]');
    const controllerRuntime = globalThis[Symbol.for("citry-ui:dialog-controller-runtime")];
    if (controllerRuntime?.generation !== 1) {
      throw new Error("[citry-ui] CDialog controller runtime dependency did not load.");
    }
    const allowedValues = {
      initialFocus: ["auto", "title"],
      size: ["sm", "md", "lg", "full"],
      scroll: ["body", "dialog"],
    };
    const invalidEpisodes = new Map();
    let internalOpen = data.open;
    // The server's `open` input from the previous run, which the cleanup
    // stores on the dialog. A kept dialog keeps its own open state only while
    // this input is unchanged; otherwise it follows the server.
    const serverOpenKey = Symbol.for("citry-ui:dialog-server-open");
    const previousServerOpen = dialog[serverOpenKey];
    delete dialog[serverOpenKey];
    let controlled = false;
    let appliedOpen = false;
    let suppressStaleControlledOpen = false;
    let pendingControlledReturnValue = "";
    let onOpenChange = null;
    let configuration = {
      dismissible: data.dismissible,
      closeOnEscape: data.closeOnEscape,
      closeOnOutside: data.closeOnOutside,
      initialFocus: data.initialFocus,
      size: data.size,
      scroll: data.scroll,
    };
    const syncRuntimeDialog = (open) => {
      const index = runtime.dialogs.indexOf(dialog);
      if (open && index < 0) runtime.dialogs.push(dialog);
      if (!open && index >= 0) runtime.dialogs.splice(index, 1);
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
    let controller;
    const applyOpen = (nextOpen, source = null, returnValue = "") => {
      if (nextOpen === appliedOpen && dialog.open === nextOpen) {
        return;
      }
      controller.setOpen(nextOpen, source, returnValue);
      appliedOpen = controller.isOpen();
      dialog.toggleAttribute("data-open", appliedOpen);
      updateActivators(appliedOpen);
      syncRuntimeDialog(appliedOpen);
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
    controller = controllerRuntime.create({
      host,
      dialog,
      surface,
      title,
      closeButton,
      signature: `CDialog:${data.initialFocus}`,
      policy: () => configuration,
      initialFocus: () => configuration.initialFocus === "title" ? title : null,
      containmentFallback: () => configuration.initialFocus === "title" ? title : dialog,
      escapeBlocked: () => false,
      interceptDialogSubmit: () => controlled,
      requestClose: (reason, source, returnValue) => {
        requestOpen(false, reason, source, returnValue);
      },
      nativeClosed: (reason, source, returnValue) => {
        suppressStaleControlledOpen = controlled && props.open === true;
        appliedOpen = false;
        internalOpen = false;
        dialog.removeAttribute("data-open");
        updateActivators(false);
        syncRuntimeDialog(false);
        notify(false, reason, source, returnValue);
      },
      forceClose: (reason, source) => {
        suppressStaleControlledOpen = false;
        appliedOpen = false;
        internalOpen = false;
        dialog.removeAttribute("data-open");
        updateActivators(false);
        syncRuntimeDialog(false);
        // An enclosing dialog that closes this one passes itself as the
        // source; that close is reported as "ancestor". The controller's
        // other forced closes (the dialog left its root) stay "native".
        const fromAncestor = reason === "ancestor"
          && source instanceof HTMLDialogElement
          && source !== dialog;
        notify(false, fromAncestor ? "ancestor" : "native", source, "");
      },
      failed: () => {
        appliedOpen = false;
        updateActivators(false);
        syncRuntimeDialog(false);
        console.error("[citry-ui] CDialog could not enter modal state.");
      },
      handoffAborted: () => {
        // No later run kept the dialog, so the page removed it. The owner
        // removed it, so the close is not reported to `onOpenChange`.
        appliedOpen = false;
        updateActivators(false);
        syncRuntimeDialog(false);
      },
    });

    // The controller closed a dialog this run would have taken over open,
    // because an enclosing dialog closed first. Tell the owner once the
    // callback below is known, and keep a stale controlled `open` from
    // showing it again inside the closed ancestor.
    const ancestorClose = controller.closedByAncestor;
    if (ancestorClose) {
      internalOpen = false;
      suppressStaleControlledOpen = props.open === true;
    }
    if (controller.retained) {
      appliedOpen = controller.isOpen();
      // A server re-render that keeps the dialog and its `open` input keeps
      // its open state too, so the effect below does not close it back to the
      // server's default. A changed `open` input wins instead.
      if (previousServerOpen === data.open) {
        internalOpen = appliedOpen;
      }
      dialog.toggleAttribute("data-open", appliedOpen);
      updateActivators(appliedOpen);
      syncRuntimeDialog(appliedOpen);
    }

    host.addEventListener("click", onHostClick);
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
    if (ancestorClose) notify(false, "ancestor", ancestorClose, "");
    host.setAttribute("data-citry-dialog-initialized", "");
    if (dialog.getAttribute("role") === "alertdialog") {
      host.setAttribute("data-citry-alert-dialog-initialized", "");
    }

    return () => {
      host.removeEventListener("click", onHostClick);
      dialog[serverOpenKey] = data.open;
      // A server revision runs this cleanup and then the callback again on the
      // same dialog, so an open dialog is handed to the next callback run.
      const handedOff = controller.cleanup({ handoff: true });
      if (handedOff) {
        // Citry runs this cleanup before Vue updates the page, and Vue updates
        // it in a later microtask, so by the next task a removed dialog is
        // disconnected, and the check below releases its modal state, scroll
        // lock, and focus. A kept dialog is still connected, so the check
        // leaves its handoff for the next run.
        setTimeout(() => {
          if (!dialog.isConnected) controllerRuntime.abortHandoff(dialog);
        }, 0);
      }
      appliedOpen = false;
      updateActivators(false);
      syncRuntimeDialog(false);
      if (!handedOff) {
        host.removeAttribute("data-citry-dialog-initialized");
        host.removeAttribute("data-citry-alert-dialog-initialized");
      }
    };
  },
});

})();