try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ExternalControls_cb9946", "6987def9e1f9193e8bcf5b35eed7bc5ad6d26bb4671fb7e0b95973ae41fc76f0")({
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
__citryRuntime.finishScript("08156b3812954d0a4ad49093c5f5e02f9450e8a12afe39b18f1512d08ef792d8");
} catch (error) {
__citryRuntime.finishScript("08156b3812954d0a4ad49093c5f5e02f9450e8a12afe39b18f1512d08ef792d8", error);
}