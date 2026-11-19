try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledSplitButtonMenu_5bdcac", "826c5ace4d7e6bb593117196ed460b099196b62423c6f86c31d7eebfd1440934")({
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
__citryRuntime.finishScript("f1c3d7de9ccc383693d4870abe2c854a777e06c3b2f2ac60dc553f0e36516eaf");
} catch (error) {
__citryRuntime.finishScript("f1c3d7de9ccc383693d4870abe2c854a777e06c3b2f2ac60dc553f0e36516eaf", error);
}