try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsControlledSelection_8060a7", "061a7570e4794d7b6ec27fc47604cb66ab440447841b86d8b5eea0ed58ed74ed")({
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
__citryRuntime.finishScript("5b88647fabc27d1ebe895d89869a95093d2b03b01a237bb96b2f9a814beea923");
} catch (error) {
__citryRuntime.finishScript("5b88647fabc27d1ebe895d89869a95093d2b03b01a237bb96b2f9a814beea923", error);
}