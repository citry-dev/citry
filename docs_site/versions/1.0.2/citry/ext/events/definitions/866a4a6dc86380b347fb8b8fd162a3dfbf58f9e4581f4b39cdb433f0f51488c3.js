try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDensityAndGrowth_1790d3", "83cf760dc1929bf4d537c1644c4698623740b51f23056d87ab490c9a5f17a46b")({
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
__citryRuntime.finishScript("35e4e6e513a17120703f687d8f607e7fa373e868b1212a6185c0ae70c34f631a");
} catch (error) {
__citryRuntime.finishScript("35e4e6e513a17120703f687d8f607e7fa373e868b1212a6185c0ae70c34f631a", error);
}