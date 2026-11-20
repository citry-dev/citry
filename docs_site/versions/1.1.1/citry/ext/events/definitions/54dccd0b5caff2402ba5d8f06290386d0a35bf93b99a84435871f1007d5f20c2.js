try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsAlignmentAndOrientation_2353ef", "acec645729d9f3b61f941dc5b8558216e9bfb399b878e4e1ca87f8d587013b2f")({
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
__citryRuntime.finishScript("ae0e5c426b1a0b9a1a5d34b5df31e4a570390b57f7e69dbd22832cb08f6d3d57");
} catch (error) {
__citryRuntime.finishScript("ae0e5c426b1a0b9a1a5d34b5df31e4a570390b57f7e69dbd22832cb08f6d3d57", error);
}