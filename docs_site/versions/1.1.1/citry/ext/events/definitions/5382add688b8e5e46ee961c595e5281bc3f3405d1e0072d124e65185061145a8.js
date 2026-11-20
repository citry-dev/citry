try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDialog_410dd5", "201b2aa9efe9c967091bd3c6fbe3325be37aeb5ac8481a477fafc6687d667b72")({
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
__citryRuntime.finishScript("5995b2bfcebd26804deef5e915c5528c429f39a12b5789d1530bb6f589689b85");
} catch (error) {
__citryRuntime.finishScript("5995b2bfcebd26804deef5e915c5528c429f39a12b5789d1530bb6f589689b85", error);
}