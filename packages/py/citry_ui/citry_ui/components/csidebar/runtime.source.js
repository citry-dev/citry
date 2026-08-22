$component({
  props: {
    collapsed: {}, collapsible: {}, side: {}, variant: {}, size: {}, sticky: {}, onCollapsedChange: {},
  },
  init: ({els, data, props, effect}) => {
    const root = els[0];
    const toggle = root?.querySelector(':scope > [data-citry-ui-part="toggle"]');
    const panel = root?.querySelector(':scope > [data-citry-ui-part="panel"]');
    if (!(toggle instanceof HTMLButtonElement) || !(panel instanceof HTMLElement)) {
      console.error("[citry-ui] CSidebar could not resolve its owned anatomy.", root);
      return;
    }
    const invalid = new Set();
    let internalCollapsed = Boolean(data.collapsed);
    let collapsed = internalCollapsed;
    let initialized = false;
    let transitionTimer = 0;
    let controlled = false;
    let callback = null;
    let configuration = {
      collapsible: data.collapsible,
      side: data.side,
      variant: data.variant,
      size: data.size,
      sticky: data.sticky,
    };
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CSidebar ${name} received invalid client value`, value);
    };
    const choice = (name, fallback, allowed) => {
      const supplied = props[name];
      if (supplied === undefined) { invalid.delete(name); return fallback; }
      if (typeof supplied === "string" && allowed.includes(supplied)) {
        invalid.delete(name); return supplied;
      }
      report(name, supplied); return fallback;
    };
    const finishTransition = () => {
      clearTimeout(transitionTimer);
      transitionTimer = 0;
      root.removeAttribute("data-citry-sidebar-transitioning");
    };
    const beginTransition = (previous, next) => {
      if (!initialized || previous === next || configuration.collapsible !== "rail") return;
      root.setAttribute("data-citry-sidebar-transitioning", "");
      clearTimeout(transitionTimer);
      transitionTimer = setTimeout(finishTransition, 240);
    };
    const onTransitionEnd = event => {
      if (event.target === root && ["width", "inline-size"].includes(event.propertyName)) finishTransition();
    };
    const apply = (next) => {
      const resolved = configuration.collapsible === "none" ? false : Boolean(next);
      beginTransition(collapsed, resolved);
      collapsed = resolved;
      const offcanvasHidden = collapsed && configuration.collapsible === "offcanvas";
      if (offcanvasHidden && panel.contains(root.ownerDocument.activeElement)) {
        toggle.focus({preventScroll: true});
      }
      root.toggleAttribute("data-collapsed", collapsed);
      root.dataset.collapsible = configuration.collapsible;
      root.dataset.side = configuration.side;
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.toggleAttribute("data-sticky", configuration.sticky);
      toggle.hidden = configuration.collapsible === "none";
      toggle.setAttribute("aria-expanded", String(!collapsed));
      const labels = toggle.querySelectorAll('[data-citry-ui-part="toggle-label"]');
      if (labels.length === 2) {
        labels[0].hidden = !collapsed;
        labels[1].hidden = collapsed;
      }
      panel.hidden = offcanvasHidden;
      panel.inert = offcanvasHidden;
    };
    const reconcile = () => {
      configuration.collapsible = choice("collapsible", data.collapsible, ["rail", "offcanvas", "none"]);
      configuration.side = choice("side", data.side, ["inline-start", "inline-end"]);
      configuration.variant = choice("variant", data.variant, ["plain", "floating"]);
      configuration.size = choice("size", data.size, ["sm", "md", "lg"]);
      if (props.sticky === undefined) {
        invalid.delete("sticky"); configuration.sticky = data.sticky;
      } else if (typeof props.sticky === "boolean") {
        invalid.delete("sticky"); configuration.sticky = props.sticky;
      } else report("sticky", props.sticky);
      if (props.collapsed === undefined || props.collapsed === null) {
        invalid.delete("collapsed"); controlled = false;
      } else if (typeof props.collapsed === "boolean") {
        invalid.delete("collapsed"); controlled = true;
      } else {
        report("collapsed", props.collapsed); controlled = false;
      }
      if (props.onCollapsedChange === undefined || props.onCollapsedChange === null) {
        invalid.delete("onCollapsedChange"); callback = null;
      } else if (typeof props.onCollapsedChange === "function") {
        invalid.delete("onCollapsedChange"); callback = props.onCollapsedChange;
      } else report("onCollapsedChange", props.onCollapsedChange);
      apply(controlled ? props.collapsed : internalCollapsed);
    };
    const onClick = (event) => {
      if (configuration.collapsible === "none") return;
      const previousCollapsed = collapsed;
      const next = !collapsed;
      if (!controlled) {
        internalCollapsed = next;
        apply(next);
      }
      callback?.(next, {
        collapsed: next,
        previousCollapsed,
        controlled,
        source: "activation",
        sourceEvent: event,
      });
      if (controlled) queueMicrotask(reconcile);
    };
    toggle.addEventListener("click", onClick);
    root.addEventListener("transitionend", onTransitionEnd);
    const stop = effect(reconcile);
    initialized = true;
    root.setAttribute("data-citry-sidebar-initialized", "");
    return () => {
      stop?.();
      finishTransition();
      toggle.removeEventListener("click", onClick);
      root.removeEventListener("transitionend", onTransitionEnd);
      root.removeAttribute("data-citry-sidebar-initialized");
    };
  },
})
