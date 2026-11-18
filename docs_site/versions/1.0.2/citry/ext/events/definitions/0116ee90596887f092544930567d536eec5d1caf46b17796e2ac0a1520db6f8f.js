try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledPopover_9dd225", "6ced216940fd74aa82af40e75b20d2887570331febbb455314f1d42ab607e01d")({
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
__citryRuntime.finishScript("bea4dbf5b3d310ddce2ba439b836c5b8113ee348c0bbf474ac36649a15c5402f");
} catch (error) {
__citryRuntime.finishScript("bea4dbf5b3d310ddce2ba439b836c5b8113ee348c0bbf474ac36649a15c5402f", error);
}