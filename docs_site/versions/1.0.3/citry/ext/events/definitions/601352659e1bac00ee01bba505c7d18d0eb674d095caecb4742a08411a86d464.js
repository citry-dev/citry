try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormReset_320188", "34cc8131b3362bb8b970d8a13823023b1faa3b35c1a1ed5f777aab3cfc8e6879")({
  data() {
    return {
      cancel_reset: false, status: 'Edit either value, then reset.'
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
__citryRuntime.finishScript("9449b2d60a89dc7830da439e87ba6c2330a3417a83e1871bf972fbf493a3d28b");
} catch (error) {
__citryRuntime.finishScript("9449b2d60a89dc7830da439e87ba6c2330a3417a83e1871bf972fbf493a3d28b", error);
}