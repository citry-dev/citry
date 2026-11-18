try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CustomizeAccordion_ae2c57", "a17e4b7ed465b184d103dd467449d89ab26d67189fd3720c8ba3ce7f46fe35f8")({
  data() {
    return {
      variant: 'separated',
      size: 'md',
      indicator: true,
      indicator_position: 'end',
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
__citryRuntime.finishScript("1ed4e68d3e6977b4285e691544b04107fcc34b1134d5cba57bbded2aceac1a12");
} catch (error) {
__citryRuntime.finishScript("1ed4e68d3e6977b4285e691544b04107fcc34b1134d5cba57bbded2aceac1a12", error);
}