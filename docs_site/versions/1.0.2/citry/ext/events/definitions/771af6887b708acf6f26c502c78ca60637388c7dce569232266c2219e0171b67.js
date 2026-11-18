try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledTooltip_95b31e", "29b860e70a9bf37fb8052843708a482643c0dfcb1892e756eb0b424bbfe6beb5")({
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
__citryRuntime.finishScript("35494743a03e6cb22b2c027c0f449f75af1fed4b7744b5ef3226e74c9642ec45");
} catch (error) {
__citryRuntime.finishScript("35494743a03e6cb22b2c027c0f449f75af1fed4b7744b5ef3226e74c9642ec45", error);
}