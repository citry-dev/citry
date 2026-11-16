try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDialog_603ae9", "2d1625bfd61f128cea04ae6c8eae839b7d3918f0969262ea8a0692d5ee26375c")({
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
__citryRuntime.finishScript("103402831c53e3369afdd988d806081f8fd4c3f6c579eb215615bc6df13d07f2");
} catch (error) {
__citryRuntime.finishScript("103402831c53e3369afdd988d806081f8fd4c3f6c579eb215615bc6df13d07f2", error);
}