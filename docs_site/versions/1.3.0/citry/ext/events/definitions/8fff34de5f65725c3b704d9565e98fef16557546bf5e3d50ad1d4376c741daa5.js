try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledTooltip_05d1cf", "29b860e70a9bf37fb8052843708a482643c0dfcb1892e756eb0b424bbfe6beb5")({
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
__citryRuntime.finishScript("af2f9103c6b222e965c30bb90a6b4918549394c1548a70a7e4c74e868e9dc120");
} catch (error) {
__citryRuntime.finishScript("af2f9103c6b222e965c30bb90a6b4918549394c1548a70a7e4c74e868e9dc120", error);
}