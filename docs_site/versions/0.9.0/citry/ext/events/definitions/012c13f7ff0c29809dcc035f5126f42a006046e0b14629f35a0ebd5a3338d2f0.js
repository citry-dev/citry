try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PopoverPlacements_f08d3b", "c800100a6589b762947431f72eb7dc59372662003e8631691c6017673281f42b")({
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
__citryRuntime.finishScript("37818c6a50d64af0046263e0fedaa2c788e61764ead6f1b24fcb9ca2958def0b");
} catch (error) {
__citryRuntime.finishScript("37818c6a50d64af0046263e0fedaa2c788e61764ead6f1b24fcb9ca2958def0b", error);
}