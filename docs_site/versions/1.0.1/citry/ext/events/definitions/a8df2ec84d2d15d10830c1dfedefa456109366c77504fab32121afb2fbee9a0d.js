try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDialog_1b5e85", "2d1625bfd61f128cea04ae6c8eae839b7d3918f0969262ea8a0692d5ee26375c")({
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
__citryRuntime.finishScript("b677be477b6f5cd52c2936d4d011b749a426f98f9e91add2e0bf22e41331b035");
} catch (error) {
__citryRuntime.finishScript("b677be477b6f5cd52c2936d4d011b749a426f98f9e91add2e0bf22e41331b035", error);
}