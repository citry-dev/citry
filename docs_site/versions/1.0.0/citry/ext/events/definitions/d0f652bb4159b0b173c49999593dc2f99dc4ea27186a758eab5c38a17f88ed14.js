try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormConfiguration_091351", "15f209712e42d54b702e92057ac78aeaa37ccf9c09cedff9c84a539a199716b7")({
  data() {
    return {
      disabled: false,
      readonly: false,
      submitting: false,
      gap: '1rem',
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
__citryRuntime.finishScript("147b874eeed2c0a8aabe3f9ca6f4196f0ab25fd17b4095f1474d0e9b51cda9c7");
} catch (error) {
__citryRuntime.finishScript("147b874eeed2c0a8aabe3f9ca6f4196f0ab25fd17b4095f1474d0e9b51cda9c7", error);
}