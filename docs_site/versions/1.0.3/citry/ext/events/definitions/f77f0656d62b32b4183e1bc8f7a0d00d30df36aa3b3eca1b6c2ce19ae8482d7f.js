try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDialog_2b7f16", "201b2aa9efe9c967091bd3c6fbe3325be37aeb5ac8481a477fafc6687d667b72")({
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
__citryRuntime.finishScript("2579c8ffbf41b993ffadef0d5d128ce8b3867ceb68242bb65ea7afda959b3c69");
} catch (error) {
__citryRuntime.finishScript("2579c8ffbf41b993ffadef0d5d128ce8b3867ceb68242bb65ea7afda959b3c69", error);
}