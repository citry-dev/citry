try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDialog_b76e1a", "2d1625bfd61f128cea04ae6c8eae839b7d3918f0969262ea8a0692d5ee26375c")({
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
__citryRuntime.finishScript("b58d734070c110e5f4c867b2efcf4cb5baef1cf30f962318cad30c045e1dcafc");
} catch (error) {
__citryRuntime.finishScript("b58d734070c110e5f4c867b2efcf4cb5baef1cf30f962318cad30c045e1dcafc", error);
}