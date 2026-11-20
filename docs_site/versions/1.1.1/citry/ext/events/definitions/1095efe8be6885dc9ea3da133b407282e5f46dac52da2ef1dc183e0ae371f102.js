try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormConfiguration_80b8ce", "15f209712e42d54b702e92057ac78aeaa37ccf9c09cedff9c84a539a199716b7")({
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
__citryRuntime.finishScript("78580df204d83a9295898838905c95ea7b93b8b22b0d9c59046c1c89a33689b5");
} catch (error) {
__citryRuntime.finishScript("78580df204d83a9295898838905c95ea7b93b8b22b0d9c59046c1c89a33689b5", error);
}