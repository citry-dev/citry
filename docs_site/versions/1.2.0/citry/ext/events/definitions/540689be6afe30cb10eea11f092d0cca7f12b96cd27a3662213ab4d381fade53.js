try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDialog_a5d42f", "201b2aa9efe9c967091bd3c6fbe3325be37aeb5ac8481a477fafc6687d667b72")({
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
__citryRuntime.finishScript("1288a8d2c4fd2e5c9faec530d91d98d77934c5155e6d2061d1cefbd4bfdd214d");
} catch (error) {
__citryRuntime.finishScript("1288a8d2c4fd2e5c9faec530d91d98d77934c5155e6d2061d1cefbd4bfdd214d", error);
}