try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TooltipPlacements_b31467", "94804b8020bc1fd27d9910268a971b7620f02dc67c35872cc0e2f5378396563c")({
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
__citryRuntime.finishScript("1c41123d4f1c41c4b1cfc1963c5dd01890fcbf3d8b17cb026a12a649bfbd1650");
} catch (error) {
__citryRuntime.finishScript("1c41123d4f1c41c4b1cfc1963c5dd01890fcbf3d8b17cb026a12a649bfbd1650", error);
}