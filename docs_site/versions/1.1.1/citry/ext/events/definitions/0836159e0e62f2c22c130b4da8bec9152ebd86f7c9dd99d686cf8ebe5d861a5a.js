try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledTooltip_1f73ef", "29b860e70a9bf37fb8052843708a482643c0dfcb1892e756eb0b424bbfe6beb5")({
  data() {
    return {
      open: false, locked: false, reason: 'none'
    };
  },
  methods: {
    // Show every request's reason, but change `open` only while
    // requests are not locked, so a declined request leaves the
    // Tooltip as is.
    applyOpenRequest(nextOpen, detail) {
      this.reason = detail.reason;
      if (!this.locked) this.open = nextOpen;
    },
  },
});

})();
__citryRuntime.finishScript("5a65920bb4eaca70a58d99f4d283c088ebab7e92885dd344ad5df2fcfb5c9b55");
} catch (error) {
__citryRuntime.finishScript("5a65920bb4eaca70a58d99f4d283c088ebab7e92885dd344ad5df2fcfb5c9b55", error);
}