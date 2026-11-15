try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ExternalControls_c2743d", "6987def9e1f9193e8bcf5b35eed7bc5ad6d26bb4671fb7e0b95973ae41fc76f0")({
  data() {
    return {
      disabled: false, result: ''
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
__citryRuntime.finishScript("6a7a53fdc40a568f86f05878ae07264f8380cbbf8045f51f13f3f698624cad59");
} catch (error) {
__citryRuntime.finishScript("6a7a53fdc40a568f86f05878ae07264f8380cbbf8045f51f13f3f698624cad59", error);
}