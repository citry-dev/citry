try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledTooltip_86581e", "29b860e70a9bf37fb8052843708a482643c0dfcb1892e756eb0b424bbfe6beb5")({
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
__citryRuntime.finishScript("e897c6c5849efc6fec18b5165fbfbee3c1a32d2cafc99644d0f7fb2a1c7f752a");
} catch (error) {
__citryRuntime.finishScript("e897c6c5849efc6fec18b5165fbfbee3c1a32d2cafc99644d0f7fb2a1c7f752a", error);
}