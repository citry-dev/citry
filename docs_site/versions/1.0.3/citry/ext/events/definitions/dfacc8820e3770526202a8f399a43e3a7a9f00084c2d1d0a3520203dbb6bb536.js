try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PopoverPlacements_c04486", "c800100a6589b762947431f72eb7dc59372662003e8631691c6017673281f42b")({
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
__citryRuntime.finishScript("e8e2fbebfe2d460a5b711d7dd79c236c8b756f0dba157acdbdc19fd82364eb39");
} catch (error) {
__citryRuntime.finishScript("e8e2fbebfe2d460a5b711d7dd79c236c8b756f0dba157acdbdc19fd82364eb39", error);
}