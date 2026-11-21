try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormThemeCustomization_9cb77d", "71aad7878da7b876dde9a2f6baa786b57d59c97b038dc6baab607f7d1ed72250")({
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
__citryRuntime.finishScript("75becda2c4f122ae944a6e2ec02a771e667e2fe3ecb4cbefb3293070bba92452");
} catch (error) {
__citryRuntime.finishScript("75becda2c4f122ae944a6e2ec02a771e667e2fe3ecb4cbefb3293070bba92452", error);
}