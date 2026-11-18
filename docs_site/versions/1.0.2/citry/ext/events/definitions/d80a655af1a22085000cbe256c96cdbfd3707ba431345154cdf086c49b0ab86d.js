try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledSplitButtonMenu_6f6520", "826c5ace4d7e6bb593117196ed460b099196b62423c6f86c31d7eebfd1440934")({
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
__citryRuntime.finishScript("630dbf2f58b461765daace0d34ce5c417cef7f24fc3c33490b3b348eae6f6cd0");
} catch (error) {
__citryRuntime.finishScript("630dbf2f58b461765daace0d34ce5c417cef7f24fc3c33490b3b348eae6f6cd0", error);
}