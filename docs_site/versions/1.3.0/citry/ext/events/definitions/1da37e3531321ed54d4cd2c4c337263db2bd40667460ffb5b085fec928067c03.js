try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ButtonConfiguration_4b1e44", "31a922ae0cbbfec64a9e9c8e3bb117011480d22169d2c2c15c211010764be2a7")({
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
__citryRuntime.finishScript("699e6cc3bdb397069fda196f43b0a8a6e946feaaebf8dcc4d378108fd005fb53");
} catch (error) {
__citryRuntime.finishScript("699e6cc3bdb397069fda196f43b0a8a6e946feaaebf8dcc4d378108fd005fb53", error);
}