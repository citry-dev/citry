(function() {

__citryRuntime.registerTypeOptions.bind(null, "TooltipPlacements_503c12", "94804b8020bc1fd27d9910268a971b7620f02dc67c35872cc0e2f5378396563c")({
  data() {
    return {
      placement: 'top'
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