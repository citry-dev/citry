try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormThemeCustomization_94569a", "71aad7878da7b876dde9a2f6baa786b57d59c97b038dc6baab607f7d1ed72250")({
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
__citryRuntime.finishScript("43d3af75666a2b8b606676f76a687b0e6706b4fa25bb9b1c76bbbe693e765842");
} catch (error) {
__citryRuntime.finishScript("43d3af75666a2b8b606676f76a687b0e6706b4fa25bb9b1c76bbbe693e765842", error);
}