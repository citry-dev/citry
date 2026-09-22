$component({
  props: {
    collapsed: {default: undefined}, collapsible: {default: undefined}, side: {default: undefined},
    variant: {default: undefined}, size: {default: undefined}, sticky: {default: undefined},
    onCollapsedChange: {default: undefined},
  },
  data() { return {internalCollapsed: undefined, collapsedBaseline: undefined}; },
  onServerRender: ({component}) => {
    const root = component.$refs.root;
    const defaults = component.serverDefaults;
    const toggle = root?.querySelector(':scope > [data-citry-ui-part="toggle"]');
    const panel = root?.querySelector(':scope > [data-citry-ui-part="panel"]');
    if (!(toggle instanceof HTMLButtonElement) || !(panel instanceof HTMLElement)) {
      console.error("[citry-ui] CSidebar could not resolve its owned anatomy.", root);
      return;
    }
    const invalid = new Set();
    if (component.internalCollapsed === undefined) component.internalCollapsed = Boolean(defaults.collapsed);
    let collapsed = component.internalCollapsed;
    let initialized = false;
    let transitionTimer = 0;
    let controlled = false;
    let callback = null;
    let configuration = {
      collapsible: defaults.collapsible,
      side: defaults.side,
      variant: defaults.variant,
      size: defaults.size,
      sticky: defaults.sticky,
    };
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CSidebar ${name} received invalid client value`, value);
    };
    const choice = (name, fallback, allowed) => {
      const supplied = component[name];
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
      if (collapsed) root.setAttribute("data-collapsed", "");
      else root.removeAttribute("data-collapsed");
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
      const serverCollapsed = Boolean(defaults.collapsed);
      if (component.collapsedBaseline === undefined || component.collapsedBaseline !== serverCollapsed) {
        component.internalCollapsed = serverCollapsed;
        component.collapsedBaseline = serverCollapsed;
      }
      configuration.collapsible = choice("collapsible", defaults.collapsible, ["rail", "offcanvas", "none"]);
      configuration.side = choice("side", defaults.side, ["inline-start", "inline-end"]);
      configuration.variant = choice("variant", defaults.variant, ["plain", "floating"]);
      configuration.size = choice("size", defaults.size, ["sm", "md", "lg"]);
      if (component.sticky === undefined) {
        invalid.delete("sticky"); configuration.sticky = defaults.sticky;
      } else if (typeof component.sticky === "boolean") {
        invalid.delete("sticky"); configuration.sticky = component.sticky;
      } else report("sticky", component.sticky);
      if (component.collapsed === undefined || component.collapsed === null) {
        invalid.delete("collapsed"); controlled = false;
      } else if (typeof component.collapsed === "boolean") {
        invalid.delete("collapsed"); controlled = true;
        component.internalCollapsed = component.collapsed;
      } else {
        report("collapsed", component.collapsed); controlled = false;
      }
      if (component.onCollapsedChange === undefined || component.onCollapsedChange === null) {
        invalid.delete("onCollapsedChange"); callback = null;
      } else if (typeof component.onCollapsedChange === "function") {
        invalid.delete("onCollapsedChange"); callback = component.onCollapsedChange;
      } else report("onCollapsedChange", component.onCollapsedChange);
      apply(controlled ? component.collapsed : component.internalCollapsed);
    };
    const onClick = (event) => {
      if (configuration.collapsible === "none") return;
      const previousCollapsed = collapsed;
      const next = !collapsed;
      if (!controlled) {
        component.internalCollapsed = next;
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
    const stop = Citry.vue.watchEffect(reconcile);
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
