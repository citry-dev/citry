try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormThemeCustomization_fcca65", "71aad7878da7b876dde9a2f6baa786b57d59c97b038dc6baab607f7d1ed72250")({
  data() {
    return {
      gap: '0.75rem', scheme: 'light', compact: false
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
__citryRuntime.finishScript("6100fd242ffc1c6b33a62c972779156d1518d8f747111f493260a4d8c0744213");
} catch (error) {
__citryRuntime.finishScript("6100fd242ffc1c6b33a62c972779156d1518d8f747111f493260a4d8c0744213", error);
}