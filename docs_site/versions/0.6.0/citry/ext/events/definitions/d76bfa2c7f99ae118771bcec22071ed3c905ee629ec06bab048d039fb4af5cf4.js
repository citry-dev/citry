(function() {

__citryRuntime.registerTypeOptions.bind(null, "CAccordionItem_f4da52", "369b104ac75663192356b92c43205fad176720da944976886750ab140e8078d3")({
  props: {
    disabled: {},
  },
  inject: {
    accordionService: {from: Symbol.for("citry-ui:accordion"), default: null},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const defaults = data.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const context = component.accordionService;
    if (!context) {
      console.error(
        "[citry-ui] CAccordionItem requires the nearest CAccordion client context.",
        root,
      );
      return;
    }
    const direct = (selector) => root.querySelector(`:scope > ${selector}`);
    const header = direct('[data-citry-ui-part="accordion-header"]');
    const trigger = header?.querySelector(
      ':scope > [data-citry-ui-part="accordion-heading"] '
        + '> [data-citry-accordion-trigger]',
    );
    const panel = direct("[data-citry-accordion-panel]");
    const indicator = trigger?.querySelector(':scope > [data-citry-ui-part="accordion-indicator"]');
    if (!trigger || !panel || !indicator) {
      console.error("[citry-ui] CAccordionItem could not resolve its owned anatomy.", root);
      return;
    }
    const invalidEpisodes = new Set();
    const item = {
      root,
      trigger,
      panel,
      indicator,
      value: data.value,
      ownDisabled: defaults.disabled,
      effectiveDisabled: trigger.matches(":disabled"),
    };
    const unregister = context.registerItem(item);
    const describeValue = (value) => {
      try {
        return JSON.stringify(value) ?? String(value);
      } catch {
        return String(value);
      }
    };
    effect(() => {
      const value = props.disabled === undefined ? defaults.disabled : props.disabled;
      if (typeof value === "boolean") {
        invalidEpisodes.delete("disabled");
        context.updateItem(item, value);
        return;
      }
      if (!invalidEpisodes.has("disabled")) {
        invalidEpisodes.add("disabled");
        console.error(
          `[citry-ui] CAccordionItem disabled received invalid client value `
            + `${describeValue(value)}; using the server-rendered fallback.`,
          root,
        );
      }
      context.updateItem(item, defaults.disabled);
    });
    root.setAttribute("data-citry-accordion-item-initialized", "");
    return () => {
      unregister();
      root.removeAttribute("data-citry-accordion-item-initialized");
    };
  },
});

})();