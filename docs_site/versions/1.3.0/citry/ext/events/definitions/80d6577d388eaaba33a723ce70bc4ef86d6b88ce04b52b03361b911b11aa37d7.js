try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDensityAndGrowth_302702", "83cf760dc1929bf4d537c1644c4698623740b51f23056d87ab490c9a5f17a46b")({
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
__citryRuntime.finishScript("5c3d6c75c9bf58ea8218dc02b88a85d7ab820e00185fa58dee256802b3cb4ef3");
} catch (error) {
__citryRuntime.finishScript("5c3d6c75c9bf58ea8218dc02b88a85d7ab820e00185fa58dee256802b3cb4ef3", error);
}