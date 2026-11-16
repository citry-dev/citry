try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureAlert_e6e7d3", "0783867deefad4dea1bca638f2c6892d91fad1f06ffb71ccbcd6b2688540bc48")({
  data() {
    return {
      intent: 'info',
      variant: 'soft',
      size: 'md',
      announce: 'off',
      icon: true,
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
__citryRuntime.finishScript("5b2dbc0d5a409d52aa042d51d976c4110269aea913867a166a7af8cef95e8043");
} catch (error) {
__citryRuntime.finishScript("5b2dbc0d5a409d52aa042d51d976c4110269aea913867a166a7af8cef95e8043", error);
}