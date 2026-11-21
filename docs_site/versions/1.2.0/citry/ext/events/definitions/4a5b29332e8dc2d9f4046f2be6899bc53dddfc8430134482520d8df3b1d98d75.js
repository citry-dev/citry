try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsControlledSelection_a743cd", "061a7570e4794d7b6ec27fc47604cb66ab440447841b86d8b5eea0ed58ed74ed")({
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
__citryRuntime.finishScript("34e73a74fba78ba71214e1d547675ec5cfc59b3ddb21c5f34f481e228e99e35d");
} catch (error) {
__citryRuntime.finishScript("34e73a74fba78ba71214e1d547675ec5cfc59b3ddb21c5f34f481e228e99e35d", error);
}