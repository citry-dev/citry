try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDensityAndGrowth_7cef49", "83cf760dc1929bf4d537c1644c4698623740b51f23056d87ab490c9a5f17a46b")({
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
__citryRuntime.finishScript("2dfe6ed6f9e1dcfe01e450572f2df22a4e794709e4a87306e8c06c5b87b69327");
} catch (error) {
__citryRuntime.finishScript("2dfe6ed6f9e1dcfe01e450572f2df22a4e794709e4a87306e8c06c5b87b69327", error);
}