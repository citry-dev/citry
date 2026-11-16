try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledSplitButtonMenu_c5d23f", "826c5ace4d7e6bb593117196ed460b099196b62423c6f86c31d7eebfd1440934")({
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
__citryRuntime.finishScript("f5b1f4aaa0860f236eac0da1f33335e2d734b43a09d7702fa61eea254edf3bbf");
} catch (error) {
__citryRuntime.finishScript("f5b1f4aaa0860f236eac0da1f33335e2d734b43a09d7702fa61eea254edf3bbf", error);
}