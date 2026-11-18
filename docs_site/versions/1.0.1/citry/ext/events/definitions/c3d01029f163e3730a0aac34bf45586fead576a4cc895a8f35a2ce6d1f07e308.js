try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsAlignmentAndOrientation_f249f8", "acec645729d9f3b61f941dc5b8558216e9bfb399b878e4e1ca87f8d587013b2f")({
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
__citryRuntime.finishScript("0ad72cb5285ffb06ff1176841aba6a1af3754d0aeec2f70507d63746b0b85832");
} catch (error) {
__citryRuntime.finishScript("0ad72cb5285ffb06ff1176841aba6a1af3754d0aeec2f70507d63746b0b85832", error);
}