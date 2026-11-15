try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormThemeCustomization_fd5429", "71aad7878da7b876dde9a2f6baa786b57d59c97b038dc6baab607f7d1ed72250")({
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
__citryRuntime.finishScript("62d7cfeb856c584ec91f994eb79b3dce233d9044a68915f0718e83732615c03c");
} catch (error) {
__citryRuntime.finishScript("62d7cfeb856c584ec91f994eb79b3dce233d9044a68915f0718e83732615c03c", error);
}