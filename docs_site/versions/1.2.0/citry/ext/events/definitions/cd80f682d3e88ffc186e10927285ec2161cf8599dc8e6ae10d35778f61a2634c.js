try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledSplitButtonMenu_9af6ec", "826c5ace4d7e6bb593117196ed460b099196b62423c6f86c31d7eebfd1440934")({
  data(){return {
    open:false,
    controlled:true,
    accept:true,
    lastReason:'none'
  };},
  methods: {
    // Show every request's reason. Change `open` only while this owner controls
    // the Menu and accepts requests; after release the Menu applies
    // requests itself.
    applyOpenRequest(nextOpen, detail) {
      this.lastReason = detail.reason;
      if (this.controlled && this.accept) this.open = nextOpen;
    },
  },
});

})();
__citryRuntime.finishScript("fe7b7d1024658366ebb0307f3245799a18789ff1079c99b2ddbc962f1fa80bc9");
} catch (error) {
__citryRuntime.finishScript("fe7b7d1024658366ebb0307f3245799a18789ff1079c99b2ddbc962f1fa80bc9", error);
}