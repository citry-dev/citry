try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureAlert_c39520", "0783867deefad4dea1bca638f2c6892d91fad1f06ffb71ccbcd6b2688540bc48")({
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
__citryRuntime.finishScript("93c9b573af87a1b39682ea9d14f1d9bb7ee06b7d7d8cf0a4c238560e50d21690");
} catch (error) {
__citryRuntime.finishScript("93c9b573af87a1b39682ea9d14f1d9bb7ee06b7d7d8cf0a4c238560e50d21690", error);
}