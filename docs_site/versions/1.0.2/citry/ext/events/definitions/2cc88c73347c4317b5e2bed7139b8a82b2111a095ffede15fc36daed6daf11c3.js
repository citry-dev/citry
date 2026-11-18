try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDialog_461a21", "2d1625bfd61f128cea04ae6c8eae839b7d3918f0969262ea8a0692d5ee26375c")({
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
__citryRuntime.finishScript("0e6f84975f5a54de683d88d5cae63a5571f26b18086e2ae3424a509ac79aaa28");
} catch (error) {
__citryRuntime.finishScript("0e6f84975f5a54de683d88d5cae63a5571f26b18086e2ae3424a509ac79aaa28", error);
}