try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDialog_a57809", "2d1625bfd61f128cea04ae6c8eae839b7d3918f0969262ea8a0692d5ee26375c")({
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
__citryRuntime.finishScript("956239372a56caaaf12018c63874a84ebc0f99fa8c0a9d02b108bde51fb72b15");
} catch (error) {
__citryRuntime.finishScript("956239372a56caaaf12018c63874a84ebc0f99fa8c0a9d02b108bde51fb72b15", error);
}