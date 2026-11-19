try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDialog_e94ce1", "2d1625bfd61f128cea04ae6c8eae839b7d3918f0969262ea8a0692d5ee26375c")({
  data() {
    return {
      open: false, accept: false, lastReason: 'none'
    };
  },
  methods: {
    // Show every request's reason, but change `open` only while the
    // owner accepts requests, so a declined request leaves the Dialog
    // as is.
    applyOpenRequest(nextOpen, detail) {
      this.lastReason = detail.reason;
      if (this.accept) this.open = nextOpen;
    },
  },
});

})();
__citryRuntime.finishScript("4d559905ce45019db4b786f42652abc7f0c733b59673bee8211edbf4a0055a6b");
} catch (error) {
__citryRuntime.finishScript("4d559905ce45019db4b786f42652abc7f0c733b59673bee8211edbf4a0055a6b", error);
}