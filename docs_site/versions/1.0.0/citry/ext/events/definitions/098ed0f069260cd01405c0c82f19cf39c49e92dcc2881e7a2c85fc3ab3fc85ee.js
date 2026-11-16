try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormThemeCustomization_92547b", "71aad7878da7b876dde9a2f6baa786b57d59c97b038dc6baab607f7d1ed72250")({
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
__citryRuntime.finishScript("1d70e80d31f7cfbd0d1641008fe3478472d4f38f481ff106c1987c77d1cf73c6");
} catch (error) {
__citryRuntime.finishScript("1d70e80d31f7cfbd0d1641008fe3478472d4f38f481ff106c1987c77d1cf73c6", error);
}