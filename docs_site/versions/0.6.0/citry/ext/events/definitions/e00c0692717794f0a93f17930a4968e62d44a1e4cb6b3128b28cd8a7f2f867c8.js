(function() {

__citryRuntime.registerTypeOptions.bind(null, "CMenuGroup_74a097", "91b4e41e572c4b95256ac4e14a712e0824c0538dfb151710ec326144ee23e737")({
  inject: {menuContext: {from: Symbol.for("citry-ui:menu"), default: null}},
  setup() {
    const parent = Citry.vue.inject(Symbol.for("citry-ui:menu"), null);
    return {groupService: Citry.vue.markRaw(parent?.child({container: null}) ?? {})};
  },
  provide() { return {[Symbol.for("citry-ui:menu")]: this.groupService}; },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const context = component.menuContext;
    if (!context) {
      console.error(
        "[citry-ui] CMenuGroup requires the nearest CMenu client context.",
        root,
      );
      return;
    }
    const label = root.querySelector(':scope > [data-citry-ui-part="menu-group-label"]');
    const entry = {
      root,
      key: data.key,
      kind: "group",
      value: null,
      surface: context.surface,
      container: context.container,
      validate() {
        const forbidden = label?.querySelector(
          "a[href], button, input, select, textarea, [contenteditable], [tabindex]",
        );
        if (forbidden) {
          console.error("[citry-ui] CMenuGroup label must remain noninteractive.", root);
          return false;
        }
        return context.entries(root).length > 0;
      },
    };
    const unregister = context.register(entry);
    component.groupService.setOptions({container: root});
    return () => unregister();
  },
});

})();