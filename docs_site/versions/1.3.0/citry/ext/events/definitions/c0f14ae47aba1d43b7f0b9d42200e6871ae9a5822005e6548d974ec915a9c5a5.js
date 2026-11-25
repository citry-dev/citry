try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PopoverPlacements_2438eb", "c800100a6589b762947431f72eb7dc59372662003e8631691c6017673281f42b")({
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
__citryRuntime.finishScript("2d3adcac64437018d9a7ed0255cd19e49a911caeb9cb562d388668dbfe08f0be");
} catch (error) {
__citryRuntime.finishScript("2d3adcac64437018d9a7ed0255cd19e49a911caeb9cb562d388668dbfe08f0be", error);
}