try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TooltipPlacements_288b7a", "94804b8020bc1fd27d9910268a971b7620f02dc67c35872cc0e2f5378396563c")({
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
__citryRuntime.finishScript("cffe4f2246f719dbf34f88f325033ab6e4faa239d5e4e1432fec20dbfcd383b9");
} catch (error) {
__citryRuntime.finishScript("cffe4f2246f719dbf34f88f325033ab6e4faa239d5e4e1432fec20dbfcd383b9", error);
}