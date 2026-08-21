$component({
  props: {
    open: {}, active: {}, dismissible: {}, closeOnEscape: {}, closeOnOutside: {},
    skippable: {}, scroll: {}, missingTarget: {}, size: {}, onOpenChange: {}, onActiveChange: {},
  },
  init: ({els, data, props, effect}) => {
    const host = els[0];
    const dialog = host?.querySelector(':scope > [data-citry-tour-dialog]');
    const surface = dialog?.querySelector(':scope > [data-citry-ui-part="surface"]');
    const spotlight = dialog?.querySelector(':scope > [data-citry-ui-part="spotlight"]');
    const panels = [...(surface?.querySelectorAll(':scope > [data-citry-tour-panel]') ?? [])];
    const controllerRuntime = globalThis[Symbol.for("citry-ui:dialog-controller-runtime")];
    if (!(host instanceof HTMLElement) || !(dialog instanceof HTMLDialogElement)
        || !(surface instanceof HTMLElement) || !(spotlight instanceof HTMLElement)
        || panels.length === 0 || controllerRuntime?.generation !== 1) {
      throw new Error("[citry-ui] CTour requires its owned anatomy and Dialog controller runtime.");
    }
    const invalid = new Map();
    let internalOpen = Boolean(data.open);
    let internalActive = data.active;
    let controlledOpen = false;
    let controlledActive = false;
    let appliedOpen = false;
    let active = data.active;
    let onOpenChange = null;
    let onActiveChange = null;
    let target = null;
    let resizeObserver = null;
    let mutationObserver = null;
    let frame = null;
    let listening = false;
    let configuration = {
      dismissible: data.dismissible,
      closeOnEscape: data.closeOnEscape,
      closeOnOutside: data.closeOnOutside,
      skippable: data.skippable,
      scroll: data.scroll,
      missingTarget: data.missingTarget,
      size: data.size,
    };
    const report = (name, value) => {
      let shown;
      try { shown = JSON.stringify(value) ?? String(value); } catch { shown = String(value); }
      const fingerprint = `${typeof value}:${shown}`;
      if (invalid.get(name) === fingerprint) return;
      invalid.set(name, fingerprint);
      console.error(`[citry-ui] CTour ${name} received invalid client value ${shown}.`, host);
    };
    const boolean = (name) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (typeof value === "boolean") { invalid.delete(name); return value; }
      report(name, value); return data[name];
    };
    const choice = (name, allowed) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (allowed.includes(value)) { invalid.delete(name); return value; }
      report(name, value); return data[name];
    };
    const callback = (name) => {
      const value = props[name];
      if (value === undefined || value === null || typeof value === "function") {
        invalid.delete(name); return value ?? null;
      }
      report(name, value); return null;
    };
    const activators = () => [...host.querySelectorAll('[data-citry-tour-trigger]')]
      .filter((element) => element.closest('[data-citry-tour-host]') === host);
    const panelTarget = (index) => {
      const id = panels[index]?.dataset.targetId;
      return id ? host.ownerDocument.getElementById(id) : null;
    };
    const targetExists = (index) => !panels[index]?.dataset.targetId || panelTarget(index)?.isConnected;
    const resolveIndex = (requested, direction = 1) => {
      if (!Number.isInteger(requested) || requested < 0 || requested >= panels.length) return null;
      if (targetExists(requested)) return requested;
      if (configuration.missingTarget === "close") return null;
      for (let index = requested + direction; index >= 0 && index < panels.length; index += direction) {
        if (targetExists(index)) return index;
      }
      return null;
    };
    const stopGeometry = () => {
      if (!listening) return;
      listening = false;
      globalThis.removeEventListener("resize", queueGeometry);
      host.ownerDocument.removeEventListener("scroll", queueGeometry, true);
      resizeObserver?.disconnect();
      mutationObserver?.disconnect();
      resizeObserver = null;
      mutationObserver = null;
      if (frame !== null) cancelAnimationFrame(frame);
      frame = null;
    };
    const place = () => {
      frame = null;
      if (!appliedOpen) return;
      const panel = panels[active];
      target = panelTarget(active);
      const targeted = Boolean(panel.dataset.targetId && target?.isConnected);
      host.toggleAttribute("data-targeted", targeted);
      spotlight.hidden = !targeted;
      if (!targeted) {
        surface.style.removeProperty("inset-inline-start");
        surface.style.removeProperty("inset-block-start");
        surface.dataset.placement = "center";
        return;
      }
      const rect = target.getBoundingClientRect();
      const pad = Number.parseFloat(
        getComputedStyle(host).getPropertyValue("--_cui-tour-spotlight-padding"),
      ) || 8;
      spotlight.style.insetInlineStart = `${rect.left - pad}px`;
      spotlight.style.insetBlockStart = `${rect.top - pad}px`;
      spotlight.style.inlineSize = `${rect.width + 2 * pad}px`;
      spotlight.style.blockSize = `${rect.height + 2 * pad}px`;
      const box = surface.getBoundingClientRect();
      const gap = Number.parseFloat(getComputedStyle(host).getPropertyValue("--_cui-tour-offset")) || 12;
      const margin = 8;
      const rtl = getComputedStyle(host).direction === "rtl";
      const requested = panel.dataset.placement;
      let physical = requested === "inline-start" ? (rtl ? "right" : "left")
        : requested === "inline-end" ? (rtl ? "left" : "right") : requested;
      let x = rect.left + (rect.width - box.width) / 2;
      let y = rect.bottom + gap;
      if (physical.startsWith("top")) y = rect.top - box.height - gap;
      if (physical === "left") {
        x = rect.left - box.width - gap;
        y = rect.top + (rect.height - box.height) / 2;
      }
      if (physical === "right") {
        x = rect.right + gap;
        y = rect.top + (rect.height - box.height) / 2;
      }
      if (physical.endsWith("-start")) x = rtl ? rect.right - box.width : rect.left;
      if (physical.endsWith("-end")) x = rtl ? rect.left : rect.right - box.width;
      if (physical.startsWith("top") && y < margin) {
        physical = physical.replace("top", "bottom");
        y = rect.bottom + gap;
      }
      else if (physical.startsWith("bottom") && y + box.height > innerHeight - margin) {
        physical = physical.replace("bottom", "top"); y = rect.top - box.height - gap;
      } else if (physical === "left" && x < margin) { physical = "right"; x = rect.right + gap; }
      else if (physical === "right" && x + box.width > innerWidth - margin) {
        physical = "left";
        x = rect.left - box.width - gap;
      }
      x = Math.max(margin, Math.min(x, innerWidth - box.width - margin));
      y = Math.max(margin, Math.min(y, innerHeight - box.height - margin));
      surface.style.insetInlineStart = `${x}px`;
      surface.style.insetBlockStart = `${y}px`;
      surface.dataset.placement = physical;
    };
    function queueGeometry() {
      if (frame === null) frame = requestAnimationFrame(place);
    }
    const startGeometry = () => {
      stopGeometry();
      if (!appliedOpen) return;
      listening = true;
      globalThis.addEventListener("resize", queueGeometry);
      host.ownerDocument.addEventListener("scroll", queueGeometry, true);
      target = panelTarget(active);
      if (target && "ResizeObserver" in globalThis) {
        resizeObserver = new ResizeObserver(queueGeometry);
        resizeObserver.observe(target);
      }
      mutationObserver = new MutationObserver(() => {
        if (panels[active].dataset.targetId && !panelTarget(active)?.isConnected) {
          const next = resolveIndex(active + 1, 1) ?? resolveIndex(active - 1, -1);
          if (next === null) requestOpen(false, "missing-target", target);
          else requestActive(next, "missing-target", target);
        }
      });
      mutationObserver.observe(host.ownerDocument.documentElement, {subtree: true, childList: true});
      queueGeometry();
    };
    const showPanel = (index, source = null) => {
      const previous = active;
      active = index;
      const panel = panels[index];
      panels.forEach((candidate, candidateIndex) => {
        const current = candidateIndex === index;
        candidate.hidden = !current;
        candidate.toggleAttribute("data-current", current);
        candidate.inert = !current;
      });
      host.dataset.active = String(index);
      host.dataset.value = panel.dataset.value;
      dialog.setAttribute("aria-labelledby", panel.dataset.titleId);
      if (panel.dataset.describe === "true") {
        dialog.setAttribute("aria-describedby", panel.dataset.descriptionId);
      }
      else dialog.removeAttribute("aria-describedby");
      if (appliedOpen && configuration.scroll !== "none") {
        panelTarget(index)?.scrollIntoView({
          behavior: configuration.scroll,
          block: "nearest",
          inline: "nearest",
        });
      }
      if (appliedOpen) {
        startGeometry();
        queueMicrotask(() => {
          if (active !== index || !appliedOpen) return;
          panel.querySelector('[data-citry-ui-part="title"]')?.focus({preventScroll: true});
        });
      }
      return previous;
    };
    const updateActivators = (open) => {
      for (const activator of activators()) activator.setAttribute("aria-expanded", String(open));
    };
    const notifyOpen = (open, reason, source) => onOpenChange?.(open, {
      reason, active, value: panels[active].dataset.value, controlled: controlledOpen, source,
    });
    const notifyActive = (next, previous, reason, source) => onActiveChange?.(next, {
      previousActive: previous,
      value: panels[next].dataset.value,
      previousValue: panels[previous].dataset.value,
      reason,
      controlled: controlledActive,
      source,
    });
    let controller;
    const applyOpen = (next, source = null) => {
      if (next === appliedOpen && dialog.open === next) return;
      controller.setOpen(next, source, "");
      appliedOpen = controller.isOpen();
      host.toggleAttribute("data-open", appliedOpen);
      dialog.toggleAttribute("data-open", appliedOpen);
      updateActivators(appliedOpen);
      if (appliedOpen) {
        if (configuration.scroll !== "none") {
          panelTarget(active)?.scrollIntoView({
            behavior: configuration.scroll,
            block: "nearest",
            inline: "nearest",
          });
        }
        startGeometry();
      } else stopGeometry();
    };
    const requestOpen = (next, reason, source) => {
      if (next === appliedOpen) return;
      if (next) {
        const resolved = resolveIndex(active, 1);
        if (resolved === null) { notifyOpen(false, "missing-target", source); return; }
        if (resolved !== active) showPanel(resolved, source);
      }
      if (controlledOpen) notifyOpen(next, reason, source);
      else { internalOpen = next; applyOpen(next, source); notifyOpen(next, reason, source); }
    };
    const requestActive = (next, reason, source) => {
      const direction = next >= active ? 1 : -1;
      const resolved = resolveIndex(next, direction);
      if (resolved === null) { requestOpen(false, "missing-target", source); return; }
      if (resolved === active) return;
      const previous = active;
      if (controlledActive) notifyActive(resolved, previous, reason, source);
      else {
        internalActive = resolved;
        showPanel(resolved, source);
        notifyActive(resolved, previous, reason, source);
      }
    };
    const onClick = (event) => {
      const trigger = event.target.closest?.("[data-citry-tour-trigger]");
      if (trigger && trigger.closest("[data-citry-tour-host]") === host) {
        requestOpen(true, "activator", trigger);
        return;
      }
      const action = event.target.closest?.("[data-citry-tour-action]");
      if (!action || !dialog.contains(action)) return;
      const kind = action.dataset.citryTourAction;
      if (kind === "previous") requestActive(active - 1, "previous", action);
      else if (kind === "next") requestActive(active + 1, "next", action);
      else if (kind === "finish") requestOpen(false, "finish", action);
      else if (kind === "skip" && configuration.skippable) requestOpen(false, "skip", action);
      else if (kind === "close" && configuration.dismissible) requestOpen(false, "close", action);
    };
    const onKeyDown = (event) => {
      if (event.defaultPrevented || event.key !== "Tab" || !event.shiftKey) return;
      const title = panels[active].querySelector('[data-citry-ui-part="title"]');
      if (event.target !== title) return;
      const focusable = [...panels[active].querySelectorAll('button:not(:disabled):not([hidden]), a[href]')]
        .filter((element) => element.getClientRects().length > 0);
      const last = focusable.at(-1);
      if (last instanceof HTMLElement) {
        event.preventDefault();
        last.focus({preventScroll: true});
      }
    };
    controller = controllerRuntime.create({
      host, dialog, surface,
      title: panels[active].querySelector('[data-citry-ui-part="title"]'),
      closeButton: surface.querySelector('[data-citry-tour-action="close"]'),
      signature: "CTour:modal-v1",
      policy: () => configuration,
      initialFocus: () => panels[active].querySelector('[data-citry-ui-part="title"]'),
      containmentFallback: () => panels[active].querySelector('[data-citry-ui-part="title"]'),
      escapeBlocked: () => false,
      interceptDialogSubmit: () => controlledOpen,
      requestClose: (reason, source) => requestOpen(false, reason, source),
      nativeClosed: (reason, source) => {
        appliedOpen = false; internalOpen = false; host.removeAttribute("data-open");
        dialog.removeAttribute("data-open");
        updateActivators(false);
        stopGeometry();
        notifyOpen(false, reason, source);
      },
      forceClose: (_reason, source) => {
        appliedOpen = false; internalOpen = false; host.removeAttribute("data-open");
        dialog.removeAttribute("data-open");
        updateActivators(false);
        stopGeometry();
        notifyOpen(false, "native", source);
      },
      failed: () => {
        appliedOpen = false;
        stopGeometry();
        console.error("[citry-ui] CTour could not enter modal state.");
      },
      handoffAborted: () => { appliedOpen = false; stopGeometry(); },
    });
    if (controller.retained) appliedOpen = controller.isOpen();
    host.addEventListener("click", onClick);
    dialog.addEventListener("keydown", onKeyDown);
    effect(() => {
      configuration = {
        dismissible: boolean("dismissible"),
        closeOnEscape: boolean("closeOnEscape"),
        closeOnOutside: boolean("closeOnOutside"),
        skippable: boolean("skippable"),
        scroll: choice("scroll", ["auto", "smooth", "none"]),
        missingTarget: choice("missingTarget", ["skip", "close"]),
        size: choice("size", ["sm", "md", "lg"]),
      };
      onOpenChange = callback("onOpenChange");
      onActiveChange = callback("onActiveChange");
      const suppliedActive = props.active;
      let nextActive = internalActive;
      if (suppliedActive === undefined || suppliedActive === null) {
        controlledActive = false;
        invalid.delete("active");
      }
      else if (Number.isInteger(suppliedActive) && suppliedActive >= 0 && suppliedActive < panels.length) {
        controlledActive = true; nextActive = suppliedActive; invalid.delete("active");
      } else { controlledActive = false; report("active", suppliedActive); }
      const resolved = resolveIndex(nextActive, nextActive >= active ? 1 : -1);
      if (resolved !== null && resolved !== active) showPanel(resolved);
      const suppliedOpen = props.open;
      let nextOpen = internalOpen;
      if (suppliedOpen === undefined || suppliedOpen === null) {
        controlledOpen = false;
        invalid.delete("open");
      }
      else if (typeof suppliedOpen === "boolean") {
        controlledOpen = true;
        nextOpen = suppliedOpen;
        invalid.delete("open");
      }
      else { controlledOpen = false; report("open", suppliedOpen); }
      host.dataset.size = configuration.size;
      surface.dataset.size = configuration.size;
      surface.querySelector('[data-citry-tour-action="close"]').hidden = !configuration.dismissible;
      for (const panel of panels) {
        const skip = panel.querySelector('[data-citry-tour-action="skip"]');
        if (skip) skip.hidden = !configuration.skippable;
      }
      if (nextOpen && resolveIndex(active, 1) === null) {
        if (appliedOpen) requestOpen(false, "missing-target", null);
      } else applyOpen(nextOpen);
    });
    host.setAttribute("data-citry-tour-initialized", "");
    return () => {
      host.removeEventListener("click", onClick);
      dialog.removeEventListener("keydown", onKeyDown);
      stopGeometry();
      const handedOff = controller.cleanup({handoff: true});
      if (!handedOff) host.removeAttribute("data-citry-tour-initialized");
    };
  },
});
