try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FieldInputConfiguration_049bfc", "06a4752c27a29092e5046b6e36537be80f9b6f6890d7c1ef203b8870e38b245c")({
  data() {
    return {
      orientation: 'vertical',
      density: 'default',
      variant: 'outline',
      size: 'md',
      required: true,
      disabled: false,
      readonly: false,
      invalid: false,
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
__citryRuntime.finishScript("0c893d6a3c51832fa27378b7732da2d5e4149c34956b503619f4c90c44e8548f");
} catch (error) {
__citryRuntime.finishScript("0c893d6a3c51832fa27378b7732da2d5e4149c34956b503619f4c90c44e8548f", error);
}