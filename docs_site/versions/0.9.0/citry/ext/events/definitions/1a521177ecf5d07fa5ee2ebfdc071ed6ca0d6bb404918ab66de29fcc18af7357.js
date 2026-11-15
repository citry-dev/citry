try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsControlledSelection_ea0b8a", "061a7570e4794d7b6ec27fc47604cb66ab440447841b86d8b5eea0ed58ed74ed")({
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
__citryRuntime.finishScript("08a4bc2138fd2d25d86479cd9bab129e6298750e8a5e6e6c9d7506815bd4a39a");
} catch (error) {
__citryRuntime.finishScript("08a4bc2138fd2d25d86479cd9bab129e6298750e8a5e6e6c9d7506815bd4a39a", error);
}