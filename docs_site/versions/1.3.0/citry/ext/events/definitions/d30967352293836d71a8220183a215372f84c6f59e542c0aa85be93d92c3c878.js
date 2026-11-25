try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDialog_78681b", "2d1625bfd61f128cea04ae6c8eae839b7d3918f0969262ea8a0692d5ee26375c")({
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
__citryRuntime.finishScript("0f6aaaa372c395e1aeaa7c8e8372e4d0359f62ba5a49fcd4c3df03349c6a8ce7");
} catch (error) {
__citryRuntime.finishScript("0f6aaaa372c395e1aeaa7c8e8372e4d0359f62ba5a49fcd4c3df03349c6a8ce7", error);
}