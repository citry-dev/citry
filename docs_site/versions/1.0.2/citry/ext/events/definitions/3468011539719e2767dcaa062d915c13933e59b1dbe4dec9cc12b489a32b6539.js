try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsControlledSelection_4c85f6", "061a7570e4794d7b6ec27fc47604cb66ab440447841b86d8b5eea0ed58ed74ed")({
  data() {
    return {
      current: 'mercury',
      requested: 'none',
      requestSource: 'none',
      applyRequests: true,
    };
  },
  methods: {
    // Tabs only ask for a new selection. Record each request,
    // and apply it only while "Apply requests from Tabs" is
    // checked.
    applySelectionRequest(value, detail) {
      this.requested = value;
      this.requestSource = detail.source;
      if (this.applyRequests) {
        this.current = value;
      }
    },
  },
});

})();
__citryRuntime.finishScript("3082f4faff792a92144ac2c581fc5baae9d1e9f6b9ce5d9e71876be587ea8171");
} catch (error) {
__citryRuntime.finishScript("3082f4faff792a92144ac2c581fc5baae9d1e9f6b9ce5d9e71876be587ea8171", error);
}