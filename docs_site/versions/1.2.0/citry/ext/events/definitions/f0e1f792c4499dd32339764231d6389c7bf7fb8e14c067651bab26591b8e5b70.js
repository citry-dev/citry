try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledTooltip_d38b8f", "29b860e70a9bf37fb8052843708a482643c0dfcb1892e756eb0b424bbfe6beb5")({
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
__citryRuntime.finishScript("70da72546998e12fedccd703333ba92a0d78925c32a6a773b76c34405f7b97fc");
} catch (error) {
__citryRuntime.finishScript("70da72546998e12fedccd703333ba92a0d78925c32a6a773b76c34405f7b97fc", error);
}