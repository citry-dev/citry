try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ExternalControls_882905", "6987def9e1f9193e8bcf5b35eed7bc5ad6d26bb4671fb7e0b95973ae41fc76f0")({
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
__citryRuntime.finishScript("d3a0fd0fa556ef590653cc4961357c1ae104a516d5af4a5a4790e9e856003a10");
} catch (error) {
__citryRuntime.finishScript("d3a0fd0fa556ef590653cc4961357c1ae104a516d5af4a5a4790e9e856003a10", error);
}