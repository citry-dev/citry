try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDialog_1513c7", "201b2aa9efe9c967091bd3c6fbe3325be37aeb5ac8481a477fafc6687d667b72")({
  data() {
    return {
      size: 'md',
      scroll: 'body',
      dismissible: true,
      close_on_escape: true,
      close_on_outside: true,
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
__citryRuntime.finishScript("228b9554f19c3a07a797789a707a273b5626b87efedcfe2ce2896466229fc424");
} catch (error) {
__citryRuntime.finishScript("228b9554f19c3a07a797789a707a273b5626b87efedcfe2ce2896466229fc424", error);
}