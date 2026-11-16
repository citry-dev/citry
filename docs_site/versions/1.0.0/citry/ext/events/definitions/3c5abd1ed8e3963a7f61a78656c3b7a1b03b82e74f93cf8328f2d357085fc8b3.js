try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ExternalControls_7aaa59", "6987def9e1f9193e8bcf5b35eed7bc5ad6d26bb4671fb7e0b95973ae41fc76f0")({
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
__citryRuntime.finishScript("22a790692e32d7f6f4363923e1eed0b2adef4aeaa07cab0901118cc17337d98a");
} catch (error) {
__citryRuntime.finishScript("22a790692e32d7f6f4363923e1eed0b2adef4aeaa07cab0901118cc17337d98a", error);
}