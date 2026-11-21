try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PopoverPlacements_7a26b6", "c800100a6589b762947431f72eb7dc59372662003e8631691c6017673281f42b")({
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
__citryRuntime.finishScript("137cde5c293b22b7a542022084701653e9bdb7f74b0dd8534b8a9bba6c852433");
} catch (error) {
__citryRuntime.finishScript("137cde5c293b22b7a542022084701653e9bdb7f74b0dd8534b8a9bba6c852433", error);
}