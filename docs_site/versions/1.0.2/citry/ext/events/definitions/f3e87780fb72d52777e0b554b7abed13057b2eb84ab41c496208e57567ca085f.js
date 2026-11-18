try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDialog_767d8a", "201b2aa9efe9c967091bd3c6fbe3325be37aeb5ac8481a477fafc6687d667b72")({
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
__citryRuntime.finishScript("08bd62f8659d9832b6fcb177844ad469313308b1300babfe29f16568f16d0345");
} catch (error) {
__citryRuntime.finishScript("08bd62f8659d9832b6fcb177844ad469313308b1300babfe29f16568f16d0345", error);
}