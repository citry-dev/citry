try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PopoverPlacements_11b1d3", "c800100a6589b762947431f72eb7dc59372662003e8631691c6017673281f42b")({
  data() {
    return {
      placement: 'bottom-start', match_width: false
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
__citryRuntime.finishScript("736e53af623a83fee8ebf89f012b71e1fee9def15e58ef7903a1268681689854");
} catch (error) {
__citryRuntime.finishScript("736e53af623a83fee8ebf89f012b71e1fee9def15e58ef7903a1268681689854", error);
}