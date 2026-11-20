try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormThemeCustomization_31b291", "71aad7878da7b876dde9a2f6baa786b57d59c97b038dc6baab607f7d1ed72250")({
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
__citryRuntime.finishScript("21133ee4807b204605e2d00f0d284b1f8c9d7f094ac01468d091f697912d0aa9");
} catch (error) {
__citryRuntime.finishScript("21133ee4807b204605e2d00f0d284b1f8c9d7f094ac01468d091f697912d0aa9", error);
}