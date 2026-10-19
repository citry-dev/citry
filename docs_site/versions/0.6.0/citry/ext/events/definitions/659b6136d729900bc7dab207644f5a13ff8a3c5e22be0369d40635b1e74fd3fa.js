(function() {

__citryRuntime.registerTypeOptions.bind(null, "CToolbar_f29302", "6132d8b946476f455eb4ab840ccbade85118e8bfa1a1b3ab7138e3737f0feddb")({
  props: {orientation: {}, loop: {}, variant: {}, size: {}},
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const invalidEpisodes = new Set();
    const originalTabindex = new Map();
    const excludedComposite = '[role="menu"], [role="listbox"], [role="tree"], '
      + '[role="grid"], [role="tablist"], dialog, [popover]';
    let controls = [];
    let current = null;
    let currentIndex = 0;
    let configuration = {
      orientation: data.orientation,
      loop: data.loop,
      variant: data.variant,
      size: data.size,
    };
    let generation = 0;
    let reconciliationTask = null;
    let structureValid = false;

    const report = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CToolbar ${name} received invalid value`, value);
    };
    const resolveChoice = (name, fallback, allowed) => {
      const supplied = props[name];
      if (supplied === undefined) {
        invalidEpisodes.delete(name);
        return fallback;
      }
      if (typeof supplied === "string" && allowed.includes(supplied)) {
        invalidEpisodes.delete(name);
        return supplied;
      }
      report(name, supplied);
      return fallback;
    };
    const resolveBoolean = (name, fallback) => {
      const supplied = props[name];
      if (supplied === undefined) {
        invalidEpisodes.delete(name);
        return fallback;
      }
      if (typeof supplied === "boolean") {
        invalidEpisodes.delete(name);
        return supplied;
      }
      report(name, supplied);
      return fallback;
    };
    const ownedRegion = (element) => {
      if (!(element instanceof Element)) return false;
      if (element.closest('[data-citry-ui-part="toolbar"]') !== root) return false;
      const composite = element.closest(excludedComposite);
      return composite === null || !root.contains(composite);
    };
    const candidateControls = () => [...root.querySelectorAll('button, a[href]')]
      .filter(ownedRegion);
    const unavailable = (element) => {
      if (!element.isConnected) return true;
      if (element instanceof HTMLButtonElement && element.matches(':disabled')) return true;
      if (element.getAttribute("aria-disabled") === "true") return true;
      for (let node = element; node && node !== root; node = node.parentElement) {
        if (node.hidden || node.inert) return true;
      }
      return false;
    };
    const enabledControls = () => controls.filter((element) => !unavailable(element));
    const restoreTabindex = () => {
      originalTabindex.forEach((value, element) => {
        if (!element.isConnected) return;
        if (value === null) element.removeAttribute("tabindex");
        else element.setAttribute("tabindex", value);
      });
    };
    const invalidStructure = () => {
      if (root.querySelector('[role="toolbar"]')) return "nested Toolbar";
      const unsupported = [...root.querySelectorAll(
        'input, select, textarea, [contenteditable]:not([contenteditable="false"]), [tabindex]'
      )].find((element) => {
        if (!ownedRegion(element)) return false;
        if (element.matches('button, a[href]') && originalTabindex.has(element)) {
          if (originalTabindex.get(element) !== null) return true;
          const expected = element === current ? "0" : "-1";
          return element.getAttribute("tabindex") !== expected;
        }
        return true;
      });
      if (unsupported) return unsupported.outerHTML;
      return null;
    };
    const syncTabStops = (focusReplacement = false) => {
      const enabled = enabledControls();
      if (!enabled.includes(current)) {
        const bounded = Math.min(currentIndex, Math.max(0, enabled.length - 1));
        current = enabled[bounded] ?? enabled[0] ?? null;
      }
      controls.forEach((element) => {
        element.tabIndex = element === current && !unavailable(element) ? 0 : -1;
      });
      currentIndex = current ? enabled.indexOf(current) : 0;
      if (focusReplacement && current) current.focus();
    };
    const reconcileStructure = () => {
      reconciliationTask = null;
      const active = root.ownerDocument.activeElement;
      const priorControls = controls;
      const priorCurrent = current;
      const priorIndex = Math.max(0, priorControls.indexOf(current));
      const focusWasInside = active instanceof Element && root.contains(active);
      controls = candidateControls();
      controls.forEach((element) => {
        if (!originalTabindex.has(element)) {
          originalTabindex.set(element, element.getAttribute("tabindex"));
        }
      });
      currentIndex = priorIndex;
      const problem = invalidStructure();
      if (problem || controls.length < 3) {
        structureValid = false;
        report("structure", problem ?? `expected at least three controls, got ${controls.length}`);
        restoreTabindex();
        root.removeAttribute("data-citry-toolbar-initialized");
        return;
      }
      invalidEpisodes.delete("structure");
      structureValid = true;
      if (!controls.includes(current)) current = controls[Math.min(priorIndex, controls.length - 1)];
      const nativeDisabledFocusFallback = active === root.ownerDocument.body
        && priorControls.includes(priorCurrent)
        && unavailable(priorCurrent);
      syncTabStops(
        (focusWasInside
          && priorControls.includes(active)
          && (!controls.includes(active) || unavailable(active)))
          || nativeDisabledFocusFallback
      );
      root.setAttribute("data-citry-toolbar-initialized", "");
    };
    const scheduleReconcile = () => {
      if (reconciliationTask !== null) return;
      const scheduledGeneration = generation;
      reconciliationTask = setTimeout(() => {
        if (scheduledGeneration !== generation) return;
        reconcileStructure();
      }, 0);
    };
    const move = (direction) => {
      const enabled = enabledControls();
      if (!enabled.length) return;
      let index = enabled.indexOf(current);
      if (index < 0) index = 0;
      let next = index + direction;
      if (configuration.loop) next = (next + enabled.length) % enabled.length;
      else next = Math.max(0, Math.min(enabled.length - 1, next));
      current = enabled[next];
      syncTabStops();
      current.focus();
    };
    const edge = (last) => {
      const enabled = enabledControls();
      if (!enabled.length) return;
      current = enabled[last ? enabled.length - 1 : 0];
      syncTabStops();
      current.focus();
    };
    const controlForEvent = (event) => event.composedPath()
      .find((node) => controls.includes(node));
    const onFocusIn = (event) => {
      const control = controlForEvent(event);
      if (!(control instanceof Element) || unavailable(control)) return;
      current = control;
      syncTabStops();
    };
    const onKeyDown = (event) => {
      if (!structureValid || event.isComposing || event.ctrlKey || event.metaKey || event.altKey) return;
      const control = controlForEvent(event);
      if (!(control instanceof Element) || unavailable(control)) return;
      let direction = 0;
      if (configuration.orientation === "horizontal") {
        const rtl = getComputedStyle(root).direction === "rtl";
        if (event.key === "ArrowRight") direction = rtl ? -1 : 1;
        if (event.key === "ArrowLeft") direction = rtl ? 1 : -1;
      } else {
        if (event.key === "ArrowDown") direction = 1;
        if (event.key === "ArrowUp") direction = -1;
      }
      if (direction) {
        event.preventDefault();
        move(direction);
      } else if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        edge(event.key === "End");
      }
    };
    const observer = new MutationObserver((records) => {
      const meaningful = records.some((record) => {
        if (record.attributeName !== "tabindex") return true;
        // Only a `tabindex` attribute change gets here, and an attribute's target is always an element.
        const target = /** @type {Element} */ (record.target);
        if (!controls.includes(target)) return true;
        const expected = target === current && !unavailable(target) ? "0" : "-1";
        return target.getAttribute("tabindex") !== expected;
      });
      if (meaningful) scheduleReconcile();
    });
    observer.observe(root, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: [
        "aria-disabled", "class", "contenteditable", "disabled", "hidden",
        "href", "inert", "style", "tabindex"
      ],
    });
    const fieldsetObservers = [];
    for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (!(ancestor instanceof HTMLFieldSetElement)) continue;
      const fieldsetObserver = new MutationObserver(scheduleReconcile);
      fieldsetObserver.observe(ancestor, {
        childList: true,
        attributes: true,
        attributeFilter: ["disabled"],
      });
      fieldsetObservers.push(fieldsetObserver);
    }
    root.addEventListener("focusin", onFocusIn, true);
    root.addEventListener("keydown", onKeyDown, true);
    const stop = effect(() => {
      configuration = {
        orientation: resolveChoice("orientation", data.orientation, ["horizontal", "vertical"]),
        loop: resolveBoolean("loop", data.loop),
        variant: resolveChoice("variant", data.variant, ["plain", "soft", "outline"]),
        size: resolveChoice("size", data.size, ["sm", "md", "lg"]),
      };
      root.dataset.orientation = configuration.orientation;
      root.setAttribute("aria-orientation", configuration.orientation);
      root.toggleAttribute("data-loop", configuration.loop);
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      scheduleReconcile();
    });

    return () => {
      generation += 1;
      if (reconciliationTask !== null) clearTimeout(reconciliationTask);
      stop?.();
      observer.disconnect();
      fieldsetObservers.forEach((item) => item.disconnect());
      root.removeEventListener("focusin", onFocusIn, true);
      root.removeEventListener("keydown", onKeyDown, true);
      restoreTabindex();
      root.removeAttribute("data-citry-toolbar-initialized");
    };
  },
})

})();