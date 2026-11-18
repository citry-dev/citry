try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsControlledSelection_d70bf7", "061a7570e4794d7b6ec27fc47604cb66ab440447841b86d8b5eea0ed58ed74ed")({
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
__citryRuntime.finishScript("dc21841bb5ba3c3c110dacaf1c3150a65c9e6204d4d938858c079879ac7db965");
} catch (error) {
__citryRuntime.finishScript("dc21841bb5ba3c3c110dacaf1c3150a65c9e6204d4d938858c079879ac7db965", error);
}