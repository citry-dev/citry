try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledPopover_6f264f", "6ced216940fd74aa82af40e75b20d2887570331febbb455314f1d42ab607e01d")({
  data() {
    return {
      open: false, locked: false, lastReason: 'none'
    };
  },
  methods: {
    // Show every request's reason, but change `open` only while
    // requests are not locked, so a declined request leaves the
    // Popover as is.
    applyOpenRequest(nextOpen, detail) {
      this.lastReason = detail.reason;
      if (!this.locked) this.open = nextOpen;
    },
  },
});

})();
__citryRuntime.finishScript("d678823765673ce3f59e9cc3d22fbd59bb0b3537eb196acd4a431952fa3c6359");
} catch (error) {
__citryRuntime.finishScript("d678823765673ce3f59e9cc3d22fbd59bb0b3537eb196acd4a431952fa3c6359", error);
}