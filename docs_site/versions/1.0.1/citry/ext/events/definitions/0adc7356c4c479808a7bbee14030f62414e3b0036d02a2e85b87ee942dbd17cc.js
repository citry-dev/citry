try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledTooltip_7e06d4", "29b860e70a9bf37fb8052843708a482643c0dfcb1892e756eb0b424bbfe6beb5")({
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
__citryRuntime.finishScript("ccaa803715429c379d506881ae6641498ac7d2ccd88a8053819dd85094389d43");
} catch (error) {
__citryRuntime.finishScript("ccaa803715429c379d506881ae6641498ac7d2ccd88a8053819dd85094389d43", error);
}