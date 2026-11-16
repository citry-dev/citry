try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ButtonConfiguration_2303c8", "31a922ae0cbbfec64a9e9c8e3bb117011480d22169d2c2c15c211010764be2a7")({
  data() {
    return {
      variant: 'solid',
      intent: 'primary',
      size: 'md',
      loading_pos: 'center',
      loading: false,
      disabled: false,
      block: false,
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
__citryRuntime.finishScript("fc140a4eeda7df27b1eaf3b14df68851154bc51a51fc354d84815eefcf1f3d7f");
} catch (error) {
__citryRuntime.finishScript("fc140a4eeda7df27b1eaf3b14df68851154bc51a51fc354d84815eefcf1f3d7f", error);
}