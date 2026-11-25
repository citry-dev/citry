try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDialog_55fe6b", "201b2aa9efe9c967091bd3c6fbe3325be37aeb5ac8481a477fafc6687d667b72")({
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
__citryRuntime.finishScript("fdaf6eef78fa8a0b935c442383217328279c4a5b6e1c873982a7e98fc1a2d28e");
} catch (error) {
__citryRuntime.finishScript("fdaf6eef78fa8a0b935c442383217328279c4a5b6e1c873982a7e98fc1a2d28e", error);
}