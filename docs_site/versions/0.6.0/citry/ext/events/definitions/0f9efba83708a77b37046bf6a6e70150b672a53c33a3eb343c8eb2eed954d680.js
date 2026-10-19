(function() {

__citryRuntime.registerTypeOptions.bind(null, "CPagination_d32cfc", "858df6eee299e6b8e58b186014a02e50fb2c8ff83935422049900479dfbebb4f")({
  props: {page: {}, disabled: {}, variant: {}, size: {}, onPageChange: {}},
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const defaults = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const i18n = component.$i18n;
    const list = root.querySelector('[data-citry-ui-part="list"]');
    let current = defaults.page;
    let callback = null;
    let effectiveDisabled = defaults.disabled;
    let effectiveVariant = defaults.variant;
    let effectiveSize = defaults.size;
    let translationBindings = [];
    const invalid = new Set();
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CPagination ${name} received invalid client value`, value);
    };
    const resolveBoolean = (name, fallback) => {
      const supplied = props[name];
      if (supplied === undefined) { invalid.delete(name); return fallback; }
      if (typeof supplied === "boolean") { invalid.delete(name); return supplied; }
      report(name, supplied);
      return fallback;
    };
    const resolveChoice = (name, fallback, allowed) => {
      const supplied = props[name];
      if (supplied === undefined) { invalid.delete(name); return fallback; }
      if (typeof supplied === "string" && allowed.includes(supplied)) {
        invalid.delete(name);
        return supplied;
      }
      report(name, supplied);
      return fallback;
    };
    const range = (page) => {
      const values = new Set();
      for (let n = 1; n <= Math.min(data.boundaries, data.pages); n += 1) values.add(n);
      for (let n = Math.max(1, data.pages - data.boundaries + 1); n <= data.pages; n += 1) values.add(n);
      for (let n = Math.max(1, page - data.siblings);
          n <= Math.min(data.pages, page + data.siblings); n += 1) values.add(n);
      const ordered = [...values].sort((a, b) => a - b);
      const result = [];
      ordered.forEach((value) => {
        const previous = result[result.length - 1];
        if (typeof previous === "number" && value - previous === 2) result.push(value - 1);
        else if (typeof previous === "number" && value - previous > 2) result.push("ellipsis");
        result.push(value);
      });
      return result;
    };
    const label = (kind, page) => kind === "page"
      ? data.page_label.replace("{page}", String(page))
      : data[`${kind}_label`];
    const bindLabel = (kind, page, control) => {
      if (!i18n) return;
      let binding = null;
      if (kind === "page" && data.catalog_page_label) {
        binding = i18n.bind({
          message: "citry-ui-pagination-page",
          values: () => ({
            page: i18n.format.number(page, {format: "citry-ui-pagination-page"}),
          }),
          onChange: (text) => control.setAttribute("aria-label", text),
        });
      } else if (kind === "previous" && data.catalog_previous_label) {
        binding = i18n.bind({
          message: "citry-ui-pagination-previous",
          onChange: (text) => control.setAttribute("aria-label", text),
        });
      } else if (kind === "next" && data.catalog_next_label) {
        binding = i18n.bind({
          message: "citry-ui-pagination-next",
          onChange: (text) => control.setAttribute("aria-label", text),
        });
      } else if (kind === "first" && data.catalog_first_label) {
        binding = i18n.bind({
          message: "citry-ui-pagination-first",
          onChange: (text) => control.setAttribute("aria-label", text),
        });
      } else if (kind === "last" && data.catalog_last_label) {
        binding = i18n.bind({
          message: "citry-ui-pagination-last",
          onChange: (text) => control.setAttribute("aria-label", text),
        });
      }
      if (binding) translationBindings.push(binding);
    };
    const render = () => {
      translationBindings.forEach((binding) => binding.dispose());
      translationBindings = [];
      const items = [];
      if (data.showEdges) items.push(["first", 1]);
      if (data.showControls) items.push(["previous", Math.max(1, current - 1)]);
      range(current).forEach((value) => items.push(value === "ellipsis" ? ["ellipsis", null] : ["page", value]));
      if (data.showControls) items.push(["next", Math.min(data.pages, current + 1)]);
      if (data.showEdges) items.push(["last", data.pages]);
      list.replaceChildren(...items.map(([kind, page]) => {
        const li = document.createElement("li");
        if (kind === "ellipsis") {
          const span = document.createElement("span");
          span.dataset.citryUiPart = "ellipsis";
          span.setAttribute("aria-hidden", "true");
          span.textContent = "…";
          li.append(span);
          return li;
        }
        const unavailable = effectiveDisabled
          || (["first", "previous"].includes(kind) && current === 1)
          || (["next", "last"].includes(kind) && current === data.pages);
        const href = data.href && !unavailable ? data.href.replace("{page}", String(page)) : null;
        // A control with a URL is a link; any other control is a button, disabled when its page is unavailable.
        let control;
        if (href) {
          const link = document.createElement("a");
          link.href = href;
          control = link;
        } else {
          const button = document.createElement("button");
          button.type = "button";
          button.disabled = unavailable;
          control = button;
        }
        control.dataset.citryUiPart = "control";
        control.dataset.page = String(page);
        control.dataset.kind = kind;
        control.setAttribute("aria-label", label(kind, page));
        bindLabel(kind, page, control);
        control.textContent = kind === "page" ? String(page)
          : ({first: "«", previous: "\u2039", next: "\u203a", last: "»"})[kind];
        if (kind === "page" && page === current) {
          control.setAttribute("aria-current", "page");
          control.setAttribute("data-current", "");
        }
        li.append(control);
        return li;
      }));
      root.toggleAttribute("data-disabled", effectiveDisabled);
    };
    const reconcile = () => {
      callback = typeof props.onPageChange === "function" ? props.onPageChange : null;
      if (props.page === undefined) invalid.delete("page");
      else if (Number.isInteger(props.page) && props.page >= 1 && props.page <= data.pages) {
        invalid.delete("page");
        current = props.page;
      } else report("page", props.page);
      effectiveDisabled = resolveBoolean("disabled", defaults.disabled);
      effectiveVariant = resolveChoice("variant", defaults.variant, ["soft", "outline", "plain"]);
      effectiveSize = resolveChoice("size", defaults.size, ["sm", "md", "lg"]);
      root.dataset.variant = effectiveVariant;
      root.dataset.size = effectiveSize;
      render();
    };
    const onClick = (event) => {
      const control = event.target.closest?.('[data-citry-ui-part="control"]');
      if (!control || control.closest('[data-citry-ui-part="pagination"]') !== root || control.disabled) return;
      const page = Number(control.dataset.page);
      if (page === current) return;
      const previousPage = current;
      callback?.(page, {page, previousPage, kind: control.dataset.kind, sourceEvent: event});
      if (!control.href) event.preventDefault();
      if (props.page === undefined && (!control.href || event.defaultPrevented)) { current = page; render(); }
      else if (props.page !== undefined) setTimeout(reconcile, 0);
    };
    root.addEventListener("click", onClick);
    const stop = effect(reconcile);
    root.setAttribute("data-citry-pagination-initialized", "");
    return () => {
      stop?.();
      translationBindings.forEach((binding) => binding.dispose());
      root.removeEventListener("click", onClick);
      root.removeAttribute("data-citry-pagination-initialized");
    };
  },
})

})();