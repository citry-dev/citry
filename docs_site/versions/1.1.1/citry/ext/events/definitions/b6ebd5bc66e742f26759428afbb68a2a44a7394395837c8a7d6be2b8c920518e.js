try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureAlert_047dc2", "0783867deefad4dea1bca638f2c6892d91fad1f06ffb71ccbcd6b2688540bc48")({
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
__citryRuntime.finishScript("bde35c76452b03d71fcf29d05d49fcdb2a036b6b0d6e1e3f11e5ced3ba283e8f");
} catch (error) {
__citryRuntime.finishScript("bde35c76452b03d71fcf29d05d49fcdb2a036b6b0d6e1e3f11e5ced3ba283e8f", error);
}