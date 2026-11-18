try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PopoverPlacements_73c20a", "c800100a6589b762947431f72eb7dc59372662003e8631691c6017673281f42b")({
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
__citryRuntime.finishScript("652c97858d28432486ebd448e244d57b18b5591e9a44c45ad7142902c1af05c3");
} catch (error) {
__citryRuntime.finishScript("652c97858d28432486ebd448e244d57b18b5591e9a44c45ad7142902c1af05c3", error);
}