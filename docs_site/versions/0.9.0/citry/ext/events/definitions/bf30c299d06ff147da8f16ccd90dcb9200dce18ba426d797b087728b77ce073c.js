try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormConfiguration_351fda", "15f209712e42d54b702e92057ac78aeaa37ccf9c09cedff9c84a539a199716b7")({
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
__citryRuntime.finishScript("d4498b4addd7f4c83905351fe9e6e9a3e29437a3507d14880eb204a2a13ca2e5");
} catch (error) {
__citryRuntime.finishScript("d4498b4addd7f4c83905351fe9e6e9a3e29437a3507d14880eb204a2a13ca2e5", error);
}