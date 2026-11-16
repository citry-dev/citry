try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledPopover_27bcba", "6ced216940fd74aa82af40e75b20d2887570331febbb455314f1d42ab607e01d")({
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
__citryRuntime.finishScript("92e56dee6518530a95423b76823cdfcb4dc747374f79bbfb2ec31a5ee3a9591a");
} catch (error) {
__citryRuntime.finishScript("92e56dee6518530a95423b76823cdfcb4dc747374f79bbfb2ec31a5ee3a9591a", error);
}