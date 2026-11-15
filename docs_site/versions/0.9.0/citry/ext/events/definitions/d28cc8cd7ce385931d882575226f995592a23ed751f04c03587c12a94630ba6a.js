try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDialog_f4eecb", "2d1625bfd61f128cea04ae6c8eae839b7d3918f0969262ea8a0692d5ee26375c")({
  data() {
    return {
      open: false, accept: false, lastReason: 'none'
    };
  },
  methods: {
    // Show every request's reason, but change `open` only while the
    // owner accepts requests, so a declined request leaves the Dialog
    // as is.
    applyOpenRequest(nextOpen, detail) {
      this.lastReason = detail.reason;
      if (this.accept) this.open = nextOpen;
    },
  },
});

})();
__citryRuntime.finishScript("748ad039945e84c7d37c80efd3d33947caa741c4b35dfb77e2284d8f3cead198");
} catch (error) {
__citryRuntime.finishScript("748ad039945e84c7d37c80efd3d33947caa741c4b35dfb77e2284d8f3cead198", error);
}