try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledPopover_2a1646", "6ced216940fd74aa82af40e75b20d2887570331febbb455314f1d42ab607e01d")({
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
__citryRuntime.finishScript("4c7b4bf10d00bf3539254f0ab40d6028a99d07eafb7f43faadde4bb0c97e555d");
} catch (error) {
__citryRuntime.finishScript("4c7b4bf10d00bf3539254f0ab40d6028a99d07eafb7f43faadde4bb0c97e555d", error);
}