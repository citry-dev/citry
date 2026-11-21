try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledPopover_f652a9", "6ced216940fd74aa82af40e75b20d2887570331febbb455314f1d42ab607e01d")({
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
__citryRuntime.finishScript("91a21b3c9a7a7aecce585620216ab39a199ba9676056a5535687f4446ae8f3f7");
} catch (error) {
__citryRuntime.finishScript("91a21b3c9a7a7aecce585620216ab39a199ba9676056a5535687f4446ae8f3f7", error);
}