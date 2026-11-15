try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TooltipPlacements_65d353", "94804b8020bc1fd27d9910268a971b7620f02dc67c35872cc0e2f5378396563c")({
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
__citryRuntime.finishScript("cf550db7bb60f332b157bd028c4769d2458ed510a86c814aef876094d2e971a9");
} catch (error) {
__citryRuntime.finishScript("cf550db7bb60f332b157bd028c4769d2458ed510a86c814aef876094d2e971a9", error);
}