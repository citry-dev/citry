try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsControlledSelection_41c70c", "061a7570e4794d7b6ec27fc47604cb66ab440447841b86d8b5eea0ed58ed74ed")({
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
__citryRuntime.finishScript("383f1bc1dcdf5b0891cc3cba30c5c25214a7e37b0e44068a7edc182e2c3217c1");
} catch (error) {
__citryRuntime.finishScript("383f1bc1dcdf5b0891cc3cba30c5c25214a7e37b0e44068a7edc182e2c3217c1", error);
}