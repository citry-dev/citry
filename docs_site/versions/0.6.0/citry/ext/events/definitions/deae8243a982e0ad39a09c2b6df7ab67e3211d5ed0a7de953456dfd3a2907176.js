(function() {

const anchoredLayerRuntimeCompatible = globalThis[
  Symbol.for("citry-ui:anchored-layer-runtime-compatible")
] === true;
const anchoredLayerRuntime = globalThis[
  Symbol.for("citry-ui:anchored-layer-runtime")
];

const handoffKey = Symbol.for("citry-ui:popover-handoff");

__citryRuntime.registerTypeOptions.bind(null, "CPopover_d4bf44", "0b46aaa3a04c2221ea747165c71d22836351cc3f45ad02aab776680a8c890554")({
  props: {
    open: {},
    dismissible: {},
    placement: {},
    matchWidth: {},
    onOpenChange: {},
  },
  onServerRender: ({component}) => {
    if (!anchoredLayerRuntimeCompatible) return;
    const host = component.$el;
    const data = component;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const defaults = data.serverDefaults;
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
    // A server re-render hands the previous run's open state to this one, so
    // a popover that was open before the re-render is still open after it.
    // When the server's `open` input changed, the popover follows the server
    // instead.
    let internalOpen = initialHandoff && initialHandoff.serverOpen === defaults.open
      ? initialHandoff.open
      : defaults.open;
    let onOpenChange = null;
    let animation = null;
    let generation = 0;
    let pendingRequest = null;
    let configuration = {
      dismissible: defaults.dismissible,
      placement: defaults.placement,
      matchWidth: defaults.matchWidth,
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
      const value = props[name] === undefined ? defaults[name] : props[name];
      if (typeof value === "boolean") {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return defaults[name];
    };
    const resolvePlacement = () => {
      const value = props.placement === undefined ? defaults.placement : props.placement;
      if (allowedPlacements.includes(value)) {
        invalidEpisodes.delete("placement");
        return value;
      }
      reportInvalid("placement", value);
      return defaults.placement;
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
      surface[handoffKey] = { open: logicalOpen, serverOpen: defaults.open };
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

})();