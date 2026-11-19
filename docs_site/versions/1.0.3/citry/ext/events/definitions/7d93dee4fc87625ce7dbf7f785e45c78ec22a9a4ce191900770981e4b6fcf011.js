try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsAlignmentAndOrientation_88c817", "acec645729d9f3b61f941dc5b8558216e9bfb399b878e4e1ca87f8d587013b2f")({
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
__citryRuntime.finishScript("d96a73f654ab8b190feffc3b21c7239341e110c9d2b99d1763013b3bbd9882b4");
} catch (error) {
__citryRuntime.finishScript("d96a73f654ab8b190feffc3b21c7239341e110c9d2b99d1763013b3bbd9882b4", error);
}