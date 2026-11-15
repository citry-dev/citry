try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CMenuSeparator_6a9865", "a1abb03b6ac4ecd8fcc802940fbb9595342cceaf6a6aa0ba78982d788ef8b5f2")({
  inject: {menuContext: {from: Symbol.for("citry-ui:menu"), default: null}},
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component;
    const context = component.menuContext;
    if (!context) {
      console.error(
        "[citry-ui] CMenuSeparator requires the nearest CMenu client context.",
        root,
      );
      return;
    }
    const unregister = context.register({
      root,
      key: data.key,
      kind: "separator",
      value: null,
      surface: context.surface,
      container: context.container,
    });
    return () => unregister();
  },
});

})();
__citryRuntime.finishScript("77d81907526d683341146aa2f460057dbedd540060113a936872840aececca93");
} catch (error) {
__citryRuntime.finishScript("77d81907526d683341146aa2f460057dbedd540060113a936872840aececca93", error);
}