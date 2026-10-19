(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureAlert_a656a8", "0783867deefad4dea1bca638f2c6892d91fad1f06ffb71ccbcd6b2688540bc48")({
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