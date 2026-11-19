try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledTooltip_48a8ef", "29b860e70a9bf37fb8052843708a482643c0dfcb1892e756eb0b424bbfe6beb5")({
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
__citryRuntime.finishScript("249a87c4d8b60e594968270a816db4727ce7693bcb2a3acac5da321990561d9f");
} catch (error) {
__citryRuntime.finishScript("249a87c4d8b60e594968270a816db4727ce7693bcb2a3acac5da321990561d9f", error);
}