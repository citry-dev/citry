try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ExternalControls_3fd4e5", "6987def9e1f9193e8bcf5b35eed7bc5ad6d26bb4671fb7e0b95973ae41fc76f0")({
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
__citryRuntime.finishScript("34bf149d5ab7f52a1b1e3bf9f8066b6c96700474c1b4e4989d98c52c03d0199e");
} catch (error) {
__citryRuntime.finishScript("34bf149d5ab7f52a1b1e3bf9f8066b6c96700474c1b4e4989d98c52c03d0199e", error);
}