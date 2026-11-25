try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ExternalControls_ae2fe1", "6987def9e1f9193e8bcf5b35eed7bc5ad6d26bb4671fb7e0b95973ae41fc76f0")({
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
__citryRuntime.finishScript("b7c4695438623fc3d9d3fa69dc099e45c355bda1706ab321f96cff1d1ac59606");
} catch (error) {
__citryRuntime.finishScript("b7c4695438623fc3d9d3fa69dc099e45c355bda1706ab321f96cff1d1ac59606", error);
}