try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PopoverPlacements_2395d6", "c800100a6589b762947431f72eb7dc59372662003e8631691c6017673281f42b")({
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
__citryRuntime.finishScript("3d11116fa3251b6805781826246ee7627be7c0e759d9f9ac5dc2c3f77252d65c");
} catch (error) {
__citryRuntime.finishScript("3d11116fa3251b6805781826246ee7627be7c0e759d9f9ac5dc2c3f77252d65c", error);
}