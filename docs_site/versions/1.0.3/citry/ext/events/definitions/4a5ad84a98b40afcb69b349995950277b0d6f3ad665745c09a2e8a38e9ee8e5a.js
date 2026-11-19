try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsControlledSelection_450d72", "061a7570e4794d7b6ec27fc47604cb66ab440447841b86d8b5eea0ed58ed74ed")({
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
__citryRuntime.finishScript("328cf133583b6f014074b2dc8709fa6db8f7f9ba5707be2bdeb179e3b9fa6429");
} catch (error) {
__citryRuntime.finishScript("328cf133583b6f014074b2dc8709fa6db8f7f9ba5707be2bdeb179e3b9fa6429", error);
}