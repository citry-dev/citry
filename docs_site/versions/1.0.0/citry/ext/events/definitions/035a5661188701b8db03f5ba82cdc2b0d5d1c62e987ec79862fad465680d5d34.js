try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsAlignmentAndOrientation_4124e9", "acec645729d9f3b61f941dc5b8558216e9bfb399b878e4e1ca87f8d587013b2f")({
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
__citryRuntime.finishScript("52f508f29c7455a7ef3b862f1dee28e8587d4efa4ae76caaca4be9abbe81ebb8");
} catch (error) {
__citryRuntime.finishScript("52f508f29c7455a7ef3b862f1dee28e8587d4efa4ae76caaca4be9abbe81ebb8", error);
}