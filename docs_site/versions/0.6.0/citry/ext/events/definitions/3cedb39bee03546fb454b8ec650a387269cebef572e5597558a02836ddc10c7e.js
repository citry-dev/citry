(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDensityAndGrowth_c62b0c", "83cf760dc1929bf4d537c1644c4698623740b51f23056d87ab490c9a5f17a46b")({
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