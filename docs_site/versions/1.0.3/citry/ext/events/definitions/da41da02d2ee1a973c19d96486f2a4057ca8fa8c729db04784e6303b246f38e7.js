try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDensityAndGrowth_163337", "83cf760dc1929bf4d537c1644c4698623740b51f23056d87ab490c9a5f17a46b")({
  data() {
    return {
      grow: false
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
__citryRuntime.finishScript("91036c4ebf8e500ff5674f9bcfad811ca27731d118bbbc0764ca0dd0a86ecd9c");
} catch (error) {
__citryRuntime.finishScript("91036c4ebf8e500ff5674f9bcfad811ca27731d118bbbc0764ca0dd0a86ecd9c", error);
}