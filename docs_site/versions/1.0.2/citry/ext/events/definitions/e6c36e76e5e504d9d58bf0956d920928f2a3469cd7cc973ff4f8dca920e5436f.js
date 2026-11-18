try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsAlignmentAndOrientation_6a400e", "acec645729d9f3b61f941dc5b8558216e9bfb399b878e4e1ca87f8d587013b2f")({
  data() {
    return {
      align: 'start', orientation: 'horizontal'
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
__citryRuntime.finishScript("bc07a4569d61044aa63d4dbea832b1ca9becc41dce1246974f926ed8993e6f48");
} catch (error) {
__citryRuntime.finishScript("bc07a4569d61044aa63d4dbea832b1ca9becc41dce1246974f926ed8993e6f48", error);
}