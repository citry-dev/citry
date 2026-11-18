try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormThemeCustomization_c298c6", "71aad7878da7b876dde9a2f6baa786b57d59c97b038dc6baab607f7d1ed72250")({
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
__citryRuntime.finishScript("020a11265db6aa6f5254ccd2b4a429c88b400d837f4ceb8adaa8bbab7923f853");
} catch (error) {
__citryRuntime.finishScript("020a11265db6aa6f5254ccd2b4a429c88b400d837f4ceb8adaa8bbab7923f853", error);
}