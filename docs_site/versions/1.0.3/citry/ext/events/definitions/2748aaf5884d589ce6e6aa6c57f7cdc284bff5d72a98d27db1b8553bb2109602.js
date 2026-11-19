try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledPopover_099e6f", "6ced216940fd74aa82af40e75b20d2887570331febbb455314f1d42ab607e01d")({
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
__citryRuntime.finishScript("15fa8491854e0b7aec0d5eff5071a92c9d451e816ca3e8911090c3ddb72b11ae");
} catch (error) {
__citryRuntime.finishScript("15fa8491854e0b7aec0d5eff5071a92c9d451e816ca3e8911090c3ddb72b11ae", error);
}