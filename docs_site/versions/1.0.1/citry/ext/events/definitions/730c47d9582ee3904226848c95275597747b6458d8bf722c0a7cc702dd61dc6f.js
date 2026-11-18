try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TooltipPlacements_1b2b71", "94804b8020bc1fd27d9910268a971b7620f02dc67c35872cc0e2f5378396563c")({
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
__citryRuntime.finishScript("f907466f8f7b95c94efe8ce596181e299bfe12db54a7362b90cbb7896406e86d");
} catch (error) {
__citryRuntime.finishScript("f907466f8f7b95c94efe8ce596181e299bfe12db54a7362b90cbb7896406e86d", error);
}