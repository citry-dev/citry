try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ExternalControls_a583cd", "6987def9e1f9193e8bcf5b35eed7bc5ad6d26bb4671fb7e0b95973ae41fc76f0")({
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
__citryRuntime.finishScript("0d3e5303b525663db032ed398fe9de4177490cc484ec9838b1469d888ca7aec8");
} catch (error) {
__citryRuntime.finishScript("0d3e5303b525663db032ed398fe9de4177490cc484ec9838b1469d888ca7aec8", error);
}