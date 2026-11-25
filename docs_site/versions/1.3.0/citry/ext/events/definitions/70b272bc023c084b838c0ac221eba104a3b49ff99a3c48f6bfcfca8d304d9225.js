try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledSplitButtonMenu_91ae08", "826c5ace4d7e6bb593117196ed460b099196b62423c6f86c31d7eebfd1440934")({
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
__citryRuntime.finishScript("823cedf5c25ed1607f90c47d33654890c02a0e04692d24bd533c730d22d29d34");
} catch (error) {
__citryRuntime.finishScript("823cedf5c25ed1607f90c47d33654890c02a0e04692d24bd533c730d22d29d34", error);
}