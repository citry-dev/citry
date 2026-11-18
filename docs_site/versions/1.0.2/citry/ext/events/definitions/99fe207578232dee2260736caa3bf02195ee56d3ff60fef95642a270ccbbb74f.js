try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormConfiguration_c2a676", "15f209712e42d54b702e92057ac78aeaa37ccf9c09cedff9c84a539a199716b7")({
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
__citryRuntime.finishScript("c931b889cea479a5675e8f5c548bccfb9c5e67d226c0d3bf46aac4ce32af8f3d");
} catch (error) {
__citryRuntime.finishScript("c931b889cea479a5675e8f5c548bccfb9c5e67d226c0d3bf46aac4ce32af8f3d", error);
}