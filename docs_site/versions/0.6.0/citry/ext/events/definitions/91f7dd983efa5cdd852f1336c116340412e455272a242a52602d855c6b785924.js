(function() {

const anchoredLayerRuntimeCompatible = globalThis[
  Symbol.for("citry-ui:anchored-layer-runtime-compatible")
] === true;
const anchoredLayerRuntime = globalThis[
  Symbol.for("citry-ui:anchored-layer-runtime")
];

const handoffKey = Symbol.for("citry-ui:hover-card-handoff");

__citryRuntime.registerTypeOptions.bind(null, "CHoverCard_27dc84", "f7c65ba75a7c7f14abda8acedd156cf69eede832ddd5673a06ebd0d88860898a")({
  props: {
    open: {},
    disabled: {},
    delay: {},
    closeDelay: {},
    placement: {},
    arrow: {},
    size: {},
    onOpenChange: {},
  },
  onServerRender: ({component}) => {
    if (!anchoredLayerRuntimeCompatible) return;
    const host = component.$el;
    const data = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const nearestHost = (element) => (
      element?.closest?.("[data-citry-hover-card-host]") ?? null
    );
    const surface = [...host.querySelectorAll('[data-citry-ui-part="hover-card"]')]
      .find((candidate) => nearestHost(candidate) === host);
    const triggers = [...host.querySelectorAll("[data-citry-hover-card-trigger]")]
      .filter((candidate) => nearestHost(candidate) === host);
    if (
      !surface
      || triggers.length !== 1
      || !(triggers[0] instanceof HTMLElement)
      || triggers[0].parentElement !== host
    ) {
      throw new Error(
        "[citry-ui] CHoverCard activator must spread activator_attrs onto exactly one HTMLElement.",
      );
    }
    const trigger = triggers[0];
    const layerCoordinator = anchoredLayerRuntime.coordinatorFor(surface);
    if (
      trigger.matches(":disabled")
      || trigger.matches('[aria-disabled="true"]')
      || trigger.tabIndex < 0
    ) {
      throw new Error("[citry-ui] CHoverCard activator must be enabled and focusable.");
    }
    const anchorName = getComputedStyle(surface)
      .getPropertyValue("--_cui-hover-card-anchor")
      .trim();
    if (!anchorName.startsWith("--")) {
      throw new Error("[citry-ui] CHoverCard could not resolve its CSS anchor name.");
    }
    // Reassert private CSS-anchor ownership after authored trigger and
    // surface styles have initialized.
    trigger.style.setProperty("anchor-name", anchorName);
    surface.style.setProperty("position-anchor", anchorName);

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
      "[data-citry-hover-card-host]",
    ].join(",");
    if (surface.querySelector(interactiveSelector)) {
      throw new Error("[citry-ui] CHoverCard content must be noninteractive.");
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
    // A server re-render hands the previous run's open state to this one, so
    // a card that was open before the re-render is still open after it. When
    // the server's `open` input changed, the card follows the server instead.
    const sameServerOpen = Boolean(initialHandoff) && initialHandoff.serverOpen === data.open;
    let internalOpen = sameServerOpen ? initialHandoff.open : data.open;
    let updated = false;
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
    let geometryFrame = null;
    let geometryListening = false;
    let configuration = {
      disabled: data.disabled,
      delay: data.delay,
      closeDelay: data.closeDelay,
      placement: data.placement,
      arrow: data.arrow,
      size: data.size,
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
        `[citry-ui] CHoverCard ${name} received invalid client value `
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
        .getPropertyValue("--_cui-hover-card-duration")
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
      .getPropertyValue("--_cui-hover-card-easing")
      .trim() || "ease";
    const syncGeometry = () => {
      geometryFrame = null;
      if (!active || !logicalOpen || !surface.matches(":popover-open")) return;
      const triggerRect = trigger.getBoundingClientRect();
      const surfaceRect = surface.getBoundingClientRect();
      surface.dataset.side = surfaceRect.bottom <= triggerRect.top ? "top" : "bottom";
    };
    const scheduleGeometry = () => {
      if (geometryFrame !== null) return;
      geometryFrame = requestAnimationFrame(syncGeometry);
    };
    const startGeometry = () => {
      if (!geometryListening) {
        geometryListening = true;
        surface.ownerDocument.defaultView?.addEventListener("resize", scheduleGeometry);
        surface.ownerDocument.addEventListener("scroll", scheduleGeometry, true);
        surface.ownerDocument.defaultView?.visualViewport?.addEventListener("resize", scheduleGeometry);
        surface.ownerDocument.defaultView?.visualViewport?.addEventListener("scroll", scheduleGeometry);
      }
      scheduleGeometry();
    };
    const stopGeometry = () => {
      if (geometryFrame !== null) cancelAnimationFrame(geometryFrame);
      geometryFrame = null;
      if (!geometryListening) return;
      geometryListening = false;
      surface.ownerDocument.defaultView?.removeEventListener("resize", scheduleGeometry);
      surface.ownerDocument.removeEventListener("scroll", scheduleGeometry, true);
      surface.ownerDocument.defaultView?.visualViewport?.removeEventListener("resize", scheduleGeometry);
      surface.ownerDocument.defaultView?.visualViewport?.removeEventListener("scroll", scheduleGeometry);
    };
    const finishNativeClose = (currentGeneration) => {
      if (!active || logicalOpen || currentGeneration !== generation) {
        return;
      }
      if (surface.matches(":popover-open")) {
        surface.hidePopover();
      }
      surface.removeAttribute("data-citry-hover-card-exiting");
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
    const releaseHoverCardWarmth = () => {
      if (layerCoordinator.hoverCardLayer === layer) {
        layerCoordinator.hoverCardLayer = null;
        layerCoordinator.hoverCardWarmUntil = performance.now() + 300;
      }
    };
    const claimHoverCardWarmth = () => {
      if (layerCoordinator.hoverCardLayer && layerCoordinator.hoverCardLayer !== layer) {
        layerCoordinator.hoverCardLayer.requestPeerClose(surface);
      }
      layerCoordinator.hoverCardLayer = layer;
      layerCoordinator.hoverCardWarmUntil = Number.POSITIVE_INFINITY;
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
          console.error("[citry-ui] CHoverCard could not enter the top layer:", error, surface);
          logicalOpen = false;
          internalOpen = false;
          return;
        }
        logicalOpen = true;
        surface.removeAttribute("data-citry-hover-card-exiting");
        surface.setAttribute("data-open", "");
        if (!layerCoordinator.register(layer)) {
          logicalOpen = false;
          surface.hidePopover();
          surface.removeAttribute("data-open");
          return;
        }
        claimHoverCardWarmth();
        startGeometry();
        animateEntry(currentGeneration);
        return;
      }
      logicalOpen = false;
      surface.removeAttribute("data-open");
      surface.setAttribute("data-citry-hover-card-exiting", "");
      layerCoordinator.unregister(layer);
      releaseHoverCardWarmth();
      stopGeometry();
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
      dismissedWhileActive = true;
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
      const warmed = layerCoordinator.hoverCardWarmUntil === Number.POSITIVE_INFINITY
        || performance.now() <= layerCoordinator.hoverCardWarmUntil;
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
        claimHoverCardWarmth();
        startGeometry();
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
            "[citry-ui] CHoverCard could not restore controlled native visibility:",
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
      surface.removeAttribute("data-citry-hover-card-exiting");
      layerCoordinator.unregister(layer);
      releaseHoverCardWarmth();
      stopGeometry();
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
    // The stylesheet hides the card until this mark is present. A server
    // re-render hands an open card to this run and the effect below reopens
    // it at once, so the mark must already be back or the reopen measures a
    // hidden card, fails, and closes it without telling the owner.
    host.setAttribute("data-citry-hover-card-initialized", "");
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
        arrow: resolveBoolean("arrow"),
        size: (() => {
          const value = props.size === undefined ? data.size : props.size;
          if (["sm", "md", "lg"].includes(value)) {
            invalidEpisodes.delete("size");
            return value;
          }
          reportInvalid("size", value);
          return data.size;
        })(),
      };
      onOpenChange = resolveCallback();
      surface.dataset.placement = configuration.placement;
      surface.dataset.size = configuration.size;
      surface.toggleAttribute("data-arrow", configuration.arrow);
      if (configuration.disabled) {
        clearOpenTimer();
        clearCloseTimer();
      }
      if (!nextOpen) {
        layerCoordinator.clearSuppression(layer);
      }
      // On this run's first update the card was showing only if the previous
      // run left it open. A render that disables a showing card closes it
      // because of the disable, even when it also changes the server's
      // `open` input, so that first update reports the close either way.
      const firstUpdate = !updated;
      const wasShowing = firstUpdate ? Boolean(initialHandoff?.open) : logicalOpen;
      updated = true;
      if (configuration.disabled && wasShowing && (nextOpen || firstUpdate)) {
        // Disabling an open card hides it, as CMenu does. The owner did not
        // ask for that close, so tell it once, and stop an uncontrolled card
        // from coming back on its own when it is enabled again.
        if (!controlled) {
          internalOpen = false;
        }
        applyOpen(false, null);
        notify(false, "disabled", null, true);
        pendingRequest = null;
        return;
      }
      const context = pendingRequest?.nextOpen === nextOpen ? pendingRequest : null;
      applyOpen(nextOpen, context);
      if (context || nextOpen === logicalOpen) {
        pendingRequest = null;
      }
    });

    return () => {
      active = false;
      surface[handoffKey] = { open: logicalOpen, serverOpen: data.open };
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
      stopGeometry();
      layerCoordinator.unregister(layer);
      releaseHoverCardWarmth();
      if (surface.matches(":popover-open")) {
        surface.hidePopover();
      }
      surface.removeAttribute("data-open");
      surface.removeAttribute("data-citry-hover-card-exiting");
      host.removeAttribute("data-citry-hover-card-initialized");
    };
  },
});

})();