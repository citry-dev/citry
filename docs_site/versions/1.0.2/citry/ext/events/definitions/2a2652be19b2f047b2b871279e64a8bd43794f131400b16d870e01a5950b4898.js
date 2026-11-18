try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureAlert_c7b4d1", "0783867deefad4dea1bca638f2c6892d91fad1f06ffb71ccbcd6b2688540bc48")({
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
__citryRuntime.finishScript("816886780e5091cb410d5a2967d5147768afac1a2eac85fb15d7a1f47f6c4c94");
} catch (error) {
__citryRuntime.finishScript("816886780e5091cb410d5a2967d5147768afac1a2eac85fb15d7a1f47f6c4c94", error);
}