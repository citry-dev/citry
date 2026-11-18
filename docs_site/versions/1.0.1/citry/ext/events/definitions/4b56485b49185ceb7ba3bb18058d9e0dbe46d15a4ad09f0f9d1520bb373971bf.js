try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledPopover_7ceea1", "6ced216940fd74aa82af40e75b20d2887570331febbb455314f1d42ab607e01d")({
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
__citryRuntime.finishScript("a0e2f1d9d18412afec61584fcfb22c3ed77190ea0a0ec83857641fd4b6ecb305");
} catch (error) {
__citryRuntime.finishScript("a0e2f1d9d18412afec61584fcfb22c3ed77190ea0a0ec83857641fd4b6ecb305", error);
}