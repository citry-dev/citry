try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TooltipPlacements_3e6a2a", "94804b8020bc1fd27d9910268a971b7620f02dc67c35872cc0e2f5378396563c")({
  data() {
    return {
      placement: 'top'
    };
  },
  methods: {
    applyPreviewControls(event) {
      Object.assign(this, event.detail);
    },
  },
  mounted() {
    window.addEventListener("citry-ui-preview-controls", this.applyPreviewControls);
  },
  beforeUnmount() {
    window.removeEventListener("citry-ui-preview-controls", this.applyPreviewControls);
  },
});

})();
__citryRuntime.finishScript("71c26728ccfed4b8641aea525dbe13247914a42ca596b17f46fb10a69fd30759");
} catch (error) {
__citryRuntime.finishScript("71c26728ccfed4b8641aea525dbe13247914a42ca596b17f46fb10a69fd30759", error);
}