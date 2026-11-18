try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDensityAndGrowth_412a6c", "83cf760dc1929bf4d537c1644c4698623740b51f23056d87ab490c9a5f17a46b")({
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
__citryRuntime.finishScript("17b5274ee93c15f3f5ad6a1ea39d2222d9151d84debefde24460241d8613e090");
} catch (error) {
__citryRuntime.finishScript("17b5274ee93c15f3f5ad6a1ea39d2222d9151d84debefde24460241d8613e090", error);
}