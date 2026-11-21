try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureAlert_6a5b7f", "0783867deefad4dea1bca638f2c6892d91fad1f06ffb71ccbcd6b2688540bc48")({
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
__citryRuntime.finishScript("eef7492fa88150a4b790029a9272ab53867866e0b973255d11c593eff0f4f072");
} catch (error) {
__citryRuntime.finishScript("eef7492fa88150a4b790029a9272ab53867866e0b973255d11c593eff0f4f072", error);
}