try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TooltipPlacements_9e35d1", "94804b8020bc1fd27d9910268a971b7620f02dc67c35872cc0e2f5378396563c")({
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
__citryRuntime.finishScript("1a2df8ce641b7ee4f6e7be1dd8acdca9c0d69afddce2241373aa34a5723286b2");
} catch (error) {
__citryRuntime.finishScript("1a2df8ce641b7ee4f6e7be1dd8acdca9c0d69afddce2241373aa34a5723286b2", error);
}