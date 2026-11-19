try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ButtonConfiguration_15a05a", "31a922ae0cbbfec64a9e9c8e3bb117011480d22169d2c2c15c211010764be2a7")({
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
__citryRuntime.finishScript("e334f7ff2e6d2e3cb8230ee907bd953d5877779d22e716df750cb84636142e3f");
} catch (error) {
__citryRuntime.finishScript("e334f7ff2e6d2e3cb8230ee907bd953d5877779d22e716df750cb84636142e3f", error);
}