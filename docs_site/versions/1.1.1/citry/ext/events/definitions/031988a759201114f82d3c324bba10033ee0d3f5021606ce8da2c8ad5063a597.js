try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PopoverPlacements_9c61a5", "c800100a6589b762947431f72eb7dc59372662003e8631691c6017673281f42b")({
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
__citryRuntime.finishScript("55bb640ab1273abf8bffaae62eb75768614bfbe889f4f9dd94ad8c8a01052861");
} catch (error) {
__citryRuntime.finishScript("55bb640ab1273abf8bffaae62eb75768614bfbe889f4f9dd94ad8c8a01052861", error);
}