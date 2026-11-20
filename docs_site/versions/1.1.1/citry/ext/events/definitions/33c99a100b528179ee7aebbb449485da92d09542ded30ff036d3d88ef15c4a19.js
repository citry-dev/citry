try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ExternalControls_80450c", "6987def9e1f9193e8bcf5b35eed7bc5ad6d26bb4671fb7e0b95973ae41fc76f0")({
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
__citryRuntime.finishScript("2f4856c4b41d420cbbd09183937bdd52982c53e115a193cba07493298bd78660");
} catch (error) {
__citryRuntime.finishScript("2f4856c4b41d420cbbd09183937bdd52982c53e115a193cba07493298bd78660", error);
}