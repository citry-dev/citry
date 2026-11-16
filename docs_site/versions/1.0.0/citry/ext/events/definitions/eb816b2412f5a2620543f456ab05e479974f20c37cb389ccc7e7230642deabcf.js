try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDensityAndGrowth_ac276a", "83cf760dc1929bf4d537c1644c4698623740b51f23056d87ab490c9a5f17a46b")({
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
__citryRuntime.finishScript("99e5a528c2330aab8548838e78f672f1eacf210d9d34106023781b2f560c87d5");
} catch (error) {
__citryRuntime.finishScript("99e5a528c2330aab8548838e78f672f1eacf210d9d34106023781b2f560c87d5", error);
}