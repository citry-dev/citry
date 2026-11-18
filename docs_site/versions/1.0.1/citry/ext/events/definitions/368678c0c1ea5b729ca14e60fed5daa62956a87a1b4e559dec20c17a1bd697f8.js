try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDialog_ffbfe0", "201b2aa9efe9c967091bd3c6fbe3325be37aeb5ac8481a477fafc6687d667b72")({
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
__citryRuntime.finishScript("c4cee326dd11cbc3ce1405293fd71525c6a9c05207fa4b83faa8691c8f9eed62");
} catch (error) {
__citryRuntime.finishScript("c4cee326dd11cbc3ce1405293fd71525c6a9c05207fa4b83faa8691c8f9eed62", error);
}