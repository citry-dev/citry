try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledTooltip_456c4c", "29b860e70a9bf37fb8052843708a482643c0dfcb1892e756eb0b424bbfe6beb5")({
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
__citryRuntime.finishScript("90b4fc6db17cbc2f76ba3339f854e0ebce09955d2b715b90a0909cfd38e4bd98");
} catch (error) {
__citryRuntime.finishScript("90b4fc6db17cbc2f76ba3339f854e0ebce09955d2b715b90a0909cfd38e4bd98", error);
}