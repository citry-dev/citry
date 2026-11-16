try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDialog_eebe34", "201b2aa9efe9c967091bd3c6fbe3325be37aeb5ac8481a477fafc6687d667b72")({
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
__citryRuntime.finishScript("6b0ad68de8bb2982074deb86494c5c2598053afe5143b6ec5b83a5c090677610");
} catch (error) {
__citryRuntime.finishScript("6b0ad68de8bb2982074deb86494c5c2598053afe5143b6ec5b83a5c090677610", error);
}