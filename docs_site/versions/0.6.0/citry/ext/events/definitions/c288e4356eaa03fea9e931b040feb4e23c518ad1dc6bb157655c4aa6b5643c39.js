(function() {

__citryRuntime.registerTypeOptions.bind(null, "CNavigationMenu_3d3ab8", "04f9d305f5a60e1250f67d66fe8eb5646fee5fd824906a01ac67cb77a28a01d1")({
  props: {
    value: {},
    disabled: {},
    delay: {},
    closeDelay: {},
    loop: {},
    orientation: {},
    variant: {},
    size: {},
    onValueChange: {},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const list = root.querySelector(':scope > [data-citry-ui-part="list"]');
    if (!(root instanceof HTMLElement) || !(list instanceof HTMLUListElement)) {
      throw new Error("[citry-ui] CNavigationMenu requires its owned nav/list anatomy.");
    }
    const handoffKey = Symbol.for("citry-ui:navigation-menu-handoff");
    const previous = root[handoffKey];
    delete root[handoffKey];
    let active = true;
    let controlled = false;
    let internalValue = previous?.serverValue === data.value ? previous.value : data.value;
    let effectiveValue = null;
    let onValueChange = null;
    let entries = [];
    let invalidStructure = false;
    let openTimer = null;
    let closeTimer = null;
    let reconcileFrame = null;
    let geometryFrame = null;
    let geometryListening = false;
    let outsideListening = false;
    const invalidEpisodes = new Set();
    let configuration = {
      disabled: data.disabled,
      delay: data.delay,
      closeDelay: data.closeDelay,
      loop: data.loop,
      orientation: data.orientation,
      variant: data.variant,
      size: data.size,
    };

    const reportInvalid = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CNavigationMenu ${name} received invalid client value.`, value, root);
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
    const resolveDelay = (name) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (Number.isInteger(value) && value >= 0 && value <= 60000) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return data[name];
    };
    const resolveChoice = (name, allowed) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (allowed.includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return data[name];
    };
    const resolveCallback = () => {
      const value = props.onValueChange;
      if (value === undefined || value === null || typeof value === "function") {
        invalidEpisodes.delete("onValueChange");
        return value ?? null;
      }
      reportInvalid("onValueChange", value);
      return null;
    };
    const clearTimers = () => {
      clearTimeout(openTimer);
      clearTimeout(closeTimer);
      openTimer = null;
      closeTimer = null;
    };
    const directChildren = () => [...list.children].filter((element) => (
      element.matches(':scope[data-citry-ui-part="link-item"], :scope[data-citry-ui-part="item"]')
    ));
    const collect = () => {
      const children = directChildren();
      const next = [];
      const values = new Set();
      let valid = children.length > 0 && children.length === list.children.length;
      for (const child of children) {
        const trigger = child.querySelector(':scope > [data-citry-navigation-menu-trigger]');
        if (!trigger) continue;
        const panel = child.querySelector(':scope > [data-citry-navigation-menu-panel]');
        const value = trigger.dataset.value;
        if (
          !(trigger instanceof HTMLButtonElement)
          || trigger.type !== "button"
          || !panel
          || !value
          || values.has(value)
        ) {
          valid = false;
          continue;
        }
        values.add(value);
        next.push({ item: child, trigger, panel, value });
      }
      entries = next;
      invalidStructure = !valid;
      if (!valid) reportInvalid("structure", children.length);
      else invalidEpisodes.delete("structure");
    };
    const entryFor = (value) => entries.find((entry) => entry.value === value) ?? null;
    const deepActive = () => {
      let current = root.ownerDocument.activeElement;
      while (current?.shadowRoot?.activeElement) current = current.shadowRoot.activeElement;
      return current;
    };
    const composedContains = (container, target) => {
      let current = target;
      while (current) {
        if (current === container) return true;
        current = current.parentNode ?? current.getRootNode?.()?.host ?? null;
      }
      return false;
    };
    const focusTargets = () => [...list.querySelectorAll(
      ':scope > li > a[href], :scope > li > button:not(:disabled)',
    )].filter((element) => element.offsetParent !== null);
    const panelFocusTarget = (panel) => panel.querySelector(
      'a[href], button:not(:disabled), input:not(:disabled), '
        + 'select:not(:disabled), textarea:not(:disabled), '
        + '[tabindex]:not([tabindex="-1"])',
    );
    const alignOpenPanel = () => {
      geometryFrame = null;
      for (const entry of entries) {
        entry.panel.removeAttribute("data-cui-navigation-menu-align-end");
        entry.panel.style.removeProperty("--_cui-navigation-menu-panel-shift");
      }
      if (configuration.orientation !== "horizontal") return;
      const entry = entryFor(effectiveValue);
      if (!entry || entry.panel.hidden) return;
      const view = root.ownerDocument.defaultView;
      const viewportWidth = view?.visualViewport?.width ?? view?.innerWidth ?? 0;
      if (!viewportWidth) return;
      const margin = 16;
      let rect = entry.panel.getBoundingClientRect();
      const rtl = getComputedStyle(root).direction === "rtl";
      const overInlineEnd = rtl ? rect.left < margin : rect.right > viewportWidth - margin;
      entry.panel.toggleAttribute("data-cui-navigation-menu-align-end", overInlineEnd);
      rect = entry.panel.getBoundingClientRect();
      let shift = 0;
      if (rect.right > viewportWidth - margin) shift -= rect.right - (viewportWidth - margin);
      if (rect.left + shift < margin) shift += margin - (rect.left + shift);
      if (Math.abs(shift) > 0.5) {
        entry.panel.style.setProperty("--_cui-navigation-menu-panel-shift", `${shift}px`);
      }
    };
    const scheduleGeometry = () => {
      if (geometryFrame !== null) return;
      geometryFrame = requestAnimationFrame(alignOpenPanel);
    };
    const startGeometry = () => {
      if (!geometryListening) {
        geometryListening = true;
        root.ownerDocument.defaultView?.addEventListener("resize", scheduleGeometry);
        root.ownerDocument.addEventListener("scroll", scheduleGeometry, true);
      }
      scheduleGeometry();
    };
    const stopGeometry = () => {
      if (geometryListening) {
        geometryListening = false;
        root.ownerDocument.defaultView?.removeEventListener("resize", scheduleGeometry);
        root.ownerDocument.removeEventListener("scroll", scheduleGeometry, true);
      }
      cancelAnimationFrame(geometryFrame);
      geometryFrame = null;
    };
    const startOutside = () => {
      if (outsideListening || effectiveValue === null) return;
      outsideListening = true;
      root.ownerDocument.addEventListener("pointerdown", onDocumentPointerDown, true);
      root.ownerDocument.addEventListener("focusin", onDocumentFocusIn, true);
    };
    const stopOutside = () => {
      if (!outsideListening) return;
      outsideListening = false;
      root.ownerDocument.removeEventListener("pointerdown", onDocumentPointerDown, true);
      root.ownerDocument.removeEventListener("focusin", onDocumentFocusIn, true);
    };
    const apply = (value) => {
      const next = configuration.disabled || invalidStructure || !entryFor(value) ? null : value;
      effectiveValue = next;
      root.toggleAttribute("data-disabled", configuration.disabled);
      root.dataset.orientation = configuration.orientation;
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.toggleAttribute("data-loop", configuration.loop);
      if (next === null) delete root.dataset.value;
      else root.dataset.value = next;
      for (const entry of entries) {
        const open = entry.value === next;
        const disabled = configuration.disabled || entry.trigger.disabled;
        entry.item.toggleAttribute("data-open", open);
        entry.item.toggleAttribute("data-disabled", disabled);
        entry.trigger.toggleAttribute("data-open", open);
        entry.trigger.toggleAttribute("data-disabled", disabled);
        entry.trigger.setAttribute("aria-expanded", String(open));
        entry.panel.toggleAttribute("data-open", open);
        entry.panel.hidden = !open;
        entry.panel.inert = !open;
      }
      if (next === null) {
        stopOutside();
        stopGeometry();
      } else {
        startOutside();
        startGeometry();
      }
    };
    const notify = (next, previousValue, reason, source, forced = false) => {
      onValueChange?.(next, {
        value: next,
        previousValue,
        reason,
        controlled,
        forced,
        source,
      });
    };
    const request = (next, reason, source, forced = false) => {
      clearTimers();
      const previousValue = effectiveValue;
      if (forced) {
        internalValue = null;
        apply(null);
        if (previousValue !== null) notify(null, previousValue, reason, source, true);
        return;
      }
      if (!controlled) {
        internalValue = next;
        apply(next);
      }
      if (next !== previousValue) notify(next, previousValue, reason, source, false);
    };
    function onDocumentPointerDown(event) {
      if (!event.composedPath().includes(root)) request(null, "outside", event.target);
    }
    function onDocumentFocusIn(event) {
      if (!event.composedPath().includes(root)) request(null, "focus-outside", event.target);
    }
    const onClick = (event) => {
      const path = event.composedPath();
      const trigger = path.find((element) => element?.matches?.("[data-citry-navigation-menu-trigger]"));
      if (trigger && root.contains(trigger)) {
        const entry = entries.find((candidate) => candidate.trigger === trigger);
        if (entry && !configuration.disabled && !trigger.disabled) {
          request(effectiveValue === entry.value ? null : entry.value, "trigger", trigger);
        }
        return;
      }
      const link = path.find((element) => element?.matches?.("a[href]"));
      if (link && root.contains(link) && effectiveValue !== null) request(null, "link", link);
    };
    const onKeyDown = (event) => {
      const target = event.target;
      const controls = focusTargets();
      const index = controls.indexOf(target);
      if (event.key === "Escape" && effectiveValue !== null) {
        const entry = entryFor(effectiveValue);
        request(null, "escape", target);
        entry?.trigger.focus();
        event.preventDefault();
        return;
      }
      if (index < 0) return;
      const rtl = getComputedStyle(root).direction === "rtl";
      let delta = 0;
      if (configuration.orientation === "horizontal") {
        if (event.key === (rtl ? "ArrowLeft" : "ArrowRight")) delta = 1;
        if (event.key === (rtl ? "ArrowRight" : "ArrowLeft")) delta = -1;
        if (event.key === "ArrowDown") {
          const entry = entries.find((candidate) => (
            candidate.trigger === target && candidate.value === effectiveValue
          ));
          const focusTarget = entry && panelFocusTarget(entry.panel);
          if (focusTarget) {
            focusTarget.focus();
            event.preventDefault();
            return;
          }
        }
      } else {
        if (event.key === "ArrowDown") delta = 1;
        if (event.key === "ArrowUp") delta = -1;
      }
      if (event.key === "Home") {
        controls[0]?.focus();
        event.preventDefault();
        return;
      }
      if (event.key === "End") {
        controls.at(-1)?.focus();
        event.preventDefault();
        return;
      }
      if (!delta) return;
      let next = index + delta;
      if (configuration.loop) next = (next + controls.length) % controls.length;
      if (next >= 0 && next < controls.length) controls[next].focus();
      event.preventDefault();
    };
    const hoverEligible = (event) => event.pointerType === "mouse" || (
      event.pointerType === "pen" && event.buttons === 0 && event.pressure === 0
    );
    const onPointerOver = (event) => {
      if (!hoverEligible(event) || configuration.disabled) return;
      const trigger = event.target.closest?.("[data-citry-navigation-menu-trigger]");
      if (!trigger || !root.contains(trigger) || trigger.disabled) return;
      const entry = entries.find((candidate) => candidate.trigger === trigger);
      if (!entry || trigger.contains(event.relatedTarget)) return;
      clearTimeout(closeTimer);
      clearTimeout(openTimer);
      openTimer = setTimeout(() => request(entry.value, "hover", trigger), configuration.delay);
    };
    const onPointerOut = (event) => {
      if (!hoverEligible(event) || root.contains(event.relatedTarget)) return;
      clearTimeout(openTimer);
      clearTimeout(closeTimer);
      closeTimer = setTimeout(() => request(null, "hover", event.target), configuration.closeDelay);
    };
    const reconcile = () => {
      reconcileFrame = null;
      const previousValue = effectiveValue;
      collect();
      if (invalidStructure) {
        apply(null);
        if (previousValue !== null) notify(null, previousValue, "structure", root, true);
        return;
      }
      if (previousValue !== null && !entryFor(previousValue)) {
        internalValue = null;
        apply(null);
        notify(null, previousValue, "structure", root, true);
        return;
      }
      apply(controlled ? effectiveValue : internalValue);
    };
    const scheduleReconcile = () => {
      if (reconcileFrame !== null) return;
      reconcileFrame = requestAnimationFrame(reconcile);
    };
    const observer = new MutationObserver(scheduleReconcile);
    observer.observe(list, { childList: true, subtree: true, attributes: true, attributeFilter: ["disabled"] });
    root.addEventListener("click", onClick, true);
    root.addEventListener("keydown", onKeyDown, true);
    root.addEventListener("pointerover", onPointerOver);
    root.addEventListener("pointerout", onPointerOut);
    collect();

    effect(() => {
      configuration = {
        disabled: resolveBoolean("disabled"),
        delay: resolveDelay("delay"),
        closeDelay: resolveDelay("closeDelay"),
        loop: resolveBoolean("loop"),
        orientation: resolveChoice("orientation", ["horizontal", "vertical"]),
        variant: resolveChoice("variant", ["plain", "surface"]),
        size: resolveChoice("size", ["sm", "md", "lg"]),
      };
      onValueChange = resolveCallback();
      const supplied = props.value !== undefined;
      let next = internalValue;
      if (supplied) {
        if (props.value === null || (typeof props.value === "string" && entryFor(props.value))) {
          controlled = true;
          invalidEpisodes.delete("value");
          next = props.value;
          internalValue = props.value;
        } else {
          controlled = false;
          reportInvalid("value", props.value);
          next = internalValue;
        }
      } else {
        controlled = false;
        invalidEpisodes.delete("value");
      }
      if (configuration.disabled && effectiveValue !== null) {
        request(null, "disabled", root, true);
      } else {
        apply(next);
      }
      root.setAttribute("data-citry-navigation-menu-initialized", "");
    });

    return () => {
      active = false;
      clearTimers();
      cancelAnimationFrame(reconcileFrame);
      stopGeometry();
      observer.disconnect();
      stopOutside();
      root.removeEventListener("click", onClick, true);
      root.removeEventListener("keydown", onKeyDown, true);
      root.removeEventListener("pointerover", onPointerOver);
      root.removeEventListener("pointerout", onPointerOut);
      root[handoffKey] = { value: internalValue, serverValue: data.value };
      root.removeAttribute("data-citry-navigation-menu-initialized");
    };
  },
});

})();