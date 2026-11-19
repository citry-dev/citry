try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormConfiguration_693a4a", "15f209712e42d54b702e92057ac78aeaa37ccf9c09cedff9c84a539a199716b7")({
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
__citryRuntime.finishScript("2373041b086bc426996bf2906606b11be9d43b2364d15417b3917e572d90e5eb");
} catch (error) {
__citryRuntime.finishScript("2373041b086bc426996bf2906606b11be9d43b2364d15417b3917e572d90e5eb", error);
}