try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsAlignmentAndOrientation_96f545", "acec645729d9f3b61f941dc5b8558216e9bfb399b878e4e1ca87f8d587013b2f")({
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
__citryRuntime.finishScript("bf23a7afec3f8b2dab8311e54f9f1c98aa11a87cf58af7a60c7a457054571c5e");
} catch (error) {
__citryRuntime.finishScript("bf23a7afec3f8b2dab8311e54f9f1c98aa11a87cf58af7a60c7a457054571c5e", error);
}